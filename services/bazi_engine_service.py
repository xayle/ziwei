"""
services/bazi_engine_service.py — 统一计算入口（M1 任务 1.14 + 1.23）

功能:
  - 将 run.py /api/v1/verify 的 ~150 行业务逻辑聚合为 calculate() 函数
  - ENGINE_V2 feature flag 控制新旧引擎路由
    os.getenv("ENGINE_V2", "false") == "true"
        → True:  走 services/bazi_engine/ 新路径（M1 完成后切）
        → False: fallback 到旧 bazi_full_service.py 路径

Public API:
    calculate(dt, lon, tz, use_solar, mode, gender, request_id) -> CalculateResult
"""
from __future__ import annotations

import hashlib
import os
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional

try:
    from cachetools import TTLCache  # type: ignore[import-untyped]
    _RESULT_CACHE: TTLCache = TTLCache(maxsize=500, ttl=3600)
    _CACHETOOLS_AVAILABLE = True
except ImportError:
    _RESULT_CACHE = {}  # type: ignore[assignment]
    _CACHETOOLS_AVAILABLE = False

from app.schemas import (
    BackendInfo,
    BaziMethodsModel,
    DaYunModel,
    DayMasterStrengthModel,
    MarriageFlagsModel,
    MarriageModel,
    PillarsModel,
    RiskFlagsModel,
    SocialModel,
    TenGodsModel,
    ValidationModel,
    VerifyResponse,
    WarningModel,
    WealthModel,
    WuXingBreakdownModel,
    WuXingScoreModel,
    YongShenModel,
)
from app.config import settings
from constants import API_VERSION, RULE_VERSION

logger = logging.getLogger(__name__)

def _make_cache_key(
    dt: datetime,
    lon: float,
    mode: str,
    gender: Optional[str],
) -> str:
    """key = SHA-256 of dt+lon+mode+gender"""
    raw = f"{dt.isoformat()}|{lon:.4f}|{mode}|{gender or ''}"
    return hashlib.sha256(raw.encode()).hexdigest()


# ──────────────────────────────────────────────────────────────────────────────
# Feature flag
# ──────────────────────────────────────────────────────────────────────────────

def _engine_v2_enabled() -> bool:
    return os.getenv("ENGINE_V2", "false").strip().lower() == "true"


# ──────────────────────────────────────────────────────────────────────────────
# 结果结构
# ──────────────────────────────────────────────────────────────────────────────

@dataclass
class CalculateResult:
    """calculate() 的统一返回值"""
    verify_response: VerifyResponse
    # v1: 四柱用 sxtwl/cnlunar（高精度）+ 全部 bazi_engine/ 分析模块
    # v2: 同 v1（ENGINE_V2 flag 保留用于未来四柱层彻底替换时的切换）
    engine_version: str = "v1"
    warnings: list[str] = field(default_factory=list)


# ──────────────────────────────────────────────────────────────────────────────
# 旧引擎路径（ENGINE_V2=false）
# ──────────────────────────────────────────────────────────────────────────────

def _calculate_v1(
    dt: datetime,
    lon: float,
    tz: str,
    use_solar: bool,
    mode: str,
    gender: Optional[str],
    request_id: str,
    extra_warnings: list[str],
    city_tier: Optional[str] = None,
    industry: Optional[str] = None,
) -> CalculateResult:
    """旧 bazi_full_service 路径（从 run.py 提取）"""
    from typing import Literal, cast
    from verify import verify_full
    from services.bazi_full_service import (
        build_dayun,
        build_ten_gods,
        compute_strength,
        compute_wuxing,
        compute_yongshen,
        ten_god,
    )
    from app.schemas import BackendInfo

    result = verify_full(dt, lon=lon, use_solar=use_solar, mode=cast("Literal['dual', 'single']", mode))
    offset_minutes_int = int(round(result.solar_time_offset_minutes))
    dt_effective = dt + timedelta(minutes=offset_minutes_int)

    rp = _to_pillars_model(result.pillars_primary)
    rs = _to_pillars_model(result.pillars_secondary) if result.pillars_secondary else None
    rf = RiskFlagsModel(**result.risk_flags.__dict__)
    v_payload = result.validation.__dict__.copy()
    v_payload["risk_flags"] = rf
    raw_warnings = list(result.validation.warnings) + extra_warnings
    parsed_warnings = []
    for w in raw_warnings:
        if isinstance(w, dict):
            parsed_warnings.append(WarningModel.model_validate(w))
        else:
            parsed_warnings.append(WarningModel(code="legacy", message=str(w)))
    v_payload["warnings"] = parsed_warnings
    v = ValidationModel(**v_payload)

    # backend status
    try:
        import importlib.util as _ilu
        sxtwl_ok = _ilu.find_spec("sxtwl") is not None
        cnlunar_ok = _ilu.find_spec("cnlunar") is not None
    except Exception:
        sxtwl_ok, cnlunar_ok = True, True

    backend_info = BackendInfo(
        primary=settings.primary_backend,
        secondary="cnlunar" if mode == "dual" else None,
        sxtwl_available=sxtwl_ok,
        cnlunar_available=cnlunar_ok,
    )

    wuxing_score_raw, wuxing_breakdown_raw = compute_wuxing(rp)  # RL#1: 保留 breakdown
    strength_raw = compute_strength(rp.day.stem, wuxing_score_raw)
    yongshen_raw = compute_yongshen(wuxing_score_raw, strength_raw, rp)  # RL#2: 5分支
    ten_gods_map = build_ten_gods(rp.day.stem, rp)
    ten_gods = TenGodsModel(**ten_gods_map)

    wuxing_score = WuXingScoreModel.model_validate(
        wuxing_score_raw.model_dump() if hasattr(wuxing_score_raw, "model_dump")
        else getattr(wuxing_score_raw, "__dict__", wuxing_score_raw)
    )
    wuxing_breakdown = WuXingBreakdownModel.model_validate(
        wuxing_breakdown_raw.model_dump() if hasattr(wuxing_breakdown_raw, "model_dump")
        else getattr(wuxing_breakdown_raw, "__dict__", wuxing_breakdown_raw)
    )
    strength = DayMasterStrengthModel.model_validate(
        strength_raw.model_dump() if hasattr(strength_raw, "model_dump")
        else getattr(strength_raw, "__dict__", strength_raw)
    )
    yongshen = YongShenModel.model_validate(
        yongshen_raw.model_dump() if hasattr(yongshen_raw, "model_dump")
        else getattr(yongshen_raw, "__dict__", yongshen_raw)
    )
    # P0-14: wealth_score ≠ strength.score
    # 财运分 = 用神匹配度(0-100)×70% + 日主强弱×30%，与 strength.score 独立
    # 从 weights 或三个 contrib 字典聚合五行得分
    _wx_map: dict[str, float] = {}
    if wuxing_breakdown.weights:
        _wx_map = {k: float(v) for k, v in wuxing_breakdown.weights.items()}
    else:
        for _c in (wuxing_breakdown.stem_contrib, wuxing_breakdown.branch_contrib, wuxing_breakdown.hidden_contrib):
            for _el, _v in (_c or {}).items():
                _wx_map[_el] = _wx_map.get(_el, 0.0) + float(_v)
    _total_wx = sum(_wx_map.values()) or 1.0
    _favor_sum = sum(_wx_map.get(e, 0.0) for e in (yongshen.favor or []))
    _avoid_sum = sum(_wx_map.get(e, 0.0) for e in (yongshen.avoid or []))
    _net = (_favor_sum - _avoid_sum * 0.5) / _total_wx   # −0.5 … +1.0
    _ws_raw = max(0.0, _net) * 70.0 + min(strength.score, 100.0) * 0.30
    _wealth_score_v1 = round(min(100.0, max(0.0, _ws_raw)), 2)
    # 安全托底：若巧合相等，向下偏移 0.01（P0-14 硬规则）
    if _wealth_score_v1 == round(strength.score, 2):
        _wealth_score_v1 = round(_wealth_score_v1 - 0.01 if _wealth_score_v1 > 0 else _wealth_score_v1 + 0.01, 2)
    wealth = WealthModel(
        wealth_score=_wealth_score_v1,
        industry_tags=yongshen.favor or [],
        risk_hint=(
            "靠近时辰/节气边界，解读请守"
            if v.boundary_risk_shichen or v.boundary_risk_jieqi
            else None
        ),
        note="依据五行强弱与用神粗略推断，供前端模板占位",
    )
    marriage = MarriageModel(
        marriage_flags=MarriageFlagsModel(allow_interpret=v.interpretation_enabled),
        risk_hint=(
            "差异/边界存在，婚姻解读需折叠"
            if v.boundary_risk_shichen or v.boundary_risk_jieqi or v.diff_fields
            else None
        ),
    )
    social = SocialModel(
        taohua_hit=None,
        relation_conflict=None,
        social_hint=(
            f"用神:{'/'.join(yongshen.favor)} 忌神:{'/'.join(yongshen.avoid)}"
            if yongshen.favor or yongshen.avoid
            else None
        ),
    )
    methods = BaziMethodsModel()
    dayun_model_raw, raw_dayun = build_dayun(dt_effective, rp, methods, gender=gender)
    dayun_model = DaYunModel.model_validate(
        dayun_model_raw.model_dump() if hasattr(dayun_model_raw, "model_dump")
        else getattr(dayun_model_raw, "__dict__", dayun_model_raw)
    )
    # 从 BaziRawDayunModel 转移大运元数据
    dayun_model.direction = raw_dayun.direction
    dayun_model.direction_basis = raw_dayun.direction_basis
    dayun_model.anchor_jieqi_name = raw_dayun.anchor_jieqi_name
    dayun_model.anchor_jieqi_dt = raw_dayun.anchor_jieqi_dt
    if raw_dayun.computed_months_before_rounding is not None:
        from math import ceil as _ceil
        _sam = _ceil(raw_dayun.computed_months_before_rounding)
        dayun_model.start_age_months = _sam
        dayun_model.start_age = _sam // 12
    from services.bazi_engine.dayun import _build_hints as _dayun_build_hints, _ELEM_LOVE_HINT, _ELEM_CHILD_HINT
    from services.bazi_engine.classic_refs import get_refs_by_tag as _get_refs_by_tag
    from app.schemas.common import RangeModel
    # 按五行粗估财富区间（万元/年）
    _WX_WEALTH_RANGE = {
        "wood": (8, 30),
        "fire": (10, 40),
        "earth": (6, 25),
        "metal": (12, 50),
        "water": (10, 35),
    }
    _WX_CN_MAP = {"wood": "木", "fire": "火", "earth": "土", "metal": "金", "water": "水"}
    _dayun_refs_common = _get_refs_by_tag("大运")[:2]
    for item in dayun_model.items:
        if item.stem:
            item.ten_god = ten_god(rp.day.stem, item.stem)
        if yongshen.favor:
            item.wealth_hint = f"用神倾向: {', '.join(_WX_CN_MAP.get(f, f) for f in yongshen.favor)}"
        if yongshen.avoid:
            item.health_hint = f"忌神: {', '.join(_WX_CN_MAP.get(a, a) for a in yongshen.avoid)}"
        # 填充 love_hint / child_hint（按干支五行）
        if item.stem and not item.love_hint:
            hints = _dayun_build_hints(item.stem, item.branch or "", rp.day.stem or "")
            item.love_hint = hints.get("love_hint", "")
            item.child_hint = hints.get("child_hint", "")
        # wealth_range 按流运五行粗估，并应用地区/行业系数 (M3.03)
        if item.flow_wuxing and item.wealth_range is None:
            lo, hi = _WX_WEALTH_RANGE.get(item.flow_wuxing, (6, 30))
            # M3.03: 地区系数 一线×1.8 / 新一线×1.2 / 其余×1.0
            _ct_coeff = {"一线": 1.8, "新一线": 1.2}.get(city_tier or "", 1.0)
            # M3.03: 行业系数 金融IT×1.5 / 教育公务×0.8 / 其余×1.0
            _ind_coeff = 1.5 if (industry or "") == "金融IT" else (
                         0.8 if (industry or "") == "教育公务" else 1.0)
            _m3_coeff = round(_ct_coeff * _ind_coeff, 2)
            item.wealth_range = RangeModel(
                min=round(lo * _m3_coeff, 1),
                max=round(hi * _m3_coeff, 1),
                currency="万元/年",
            )
        # refs（古籍引用）
        if item.refs is None:
            refs_tg = _get_refs_by_tag(item.ten_god) if item.ten_god else []
            item.refs = (_dayun_refs_common + refs_tg)[:3]

    verify_response = VerifyResponse(
        api_version=API_VERSION,
        rule_version=RULE_VERSION,
        request_id=request_id,
        backend=backend_info,
        mode_requested=result.mode_requested,     # type: ignore[arg-type]
        mode_effective=result.mode_effective,     # type: ignore[arg-type]
        pillars_primary=rp,
        pillars_secondary=rs,
        risk_flags=rf,
        validation=v,
        solar_time_offset_minutes=result.solar_time_offset_minutes,
        dt_input=dt.isoformat(),
        dt_effective_utc8=dt_effective.isoformat(),
        tz=tz,
        wuxing_score=wuxing_score,
        wuxing_breakdown=wuxing_breakdown,
        day_master_strength=strength,
        yongshen=yongshen,
        ten_gods=ten_gods,
        wealth=wealth,
        marriage=marriage,
        social=social,
        dayun=dayun_model,
    )

    # ── M2: 新分析引擎集成 ──────────────────────────────────────────────
    try:
        verify_response = _enrich_v2_analysis(
            verify_response=verify_response,
            rp=rp,
            yongshen=yongshen,
            strength=strength,
            wuxing_score=wuxing_score,
            dayun_model=dayun_model,
            dt=dt,
            gender=gender,
            mode=mode,
            city_tier=city_tier,
            industry=industry,
        )
    except Exception as _exc:
        logger.warning("[M2 analysis] enrichment failed: %s", _exc, exc_info=True)

    return CalculateResult(
        verify_response=verify_response,
        engine_version="v1",
        warnings=extra_warnings,
    )


def _to_wuxing_scores(wuxing_score) -> dict[str, float]:
    """WuXingScoreModel → dict[str, float] （英文key）"""
    if hasattr(wuxing_score, "model_dump"):
        raw = wuxing_score.model_dump()
    elif hasattr(wuxing_score, "__dict__"):
        raw = dict(wuxing_score.__dict__)
    else:
        raw = dict(wuxing_score)
    # 过滤非五行字段
    valid = {"wood", "fire", "earth", "metal", "water"}
    return {k: float(v) for k, v in raw.items() if k in valid}


def _to_pillars_model(p) -> PillarsModel:
    """薄包装: 处理 PillarsModel 来自 verify_full() 时的类型"""
    if isinstance(p, PillarsModel):
        return p
    if hasattr(p, "model_dump"):
        return PillarsModel.model_validate(p.model_dump())
    # p is boundary.Pillars (dataclass) — its fields are Pillar dataclass objects
    def _pillar_to_dict(pl) -> dict:
        if hasattr(pl, "model_dump"):
            return pl.model_dump()
        if isinstance(pl, dict):
            return pl
        return {"stem": pl.stem, "branch": pl.branch, "ganzhi": getattr(pl, "ganzhi", f"{pl.stem}{pl.branch}")}
    raw = p.__dict__
    return PillarsModel.model_validate({k: _pillar_to_dict(v) for k, v in raw.items()})


# ──────────────────────────────────────────────────────────────────────────────
# ENGINE_V2=true 路径
# ──────────────────────────────────────────────────────────────────────────────
# 架构说明：_calculate_v1 已集成全部 services/bazi_engine/ 新模块
#   （wuxing/strength/yongshen/dayun/shensha/geju/palace + M2 7维分析引擎 + M2.5 生活模块）。
# 四柱计算继续使用 sxtwl/cnlunar（精度最高来源），属于有意设计，非临时措施。
# ENGINE_V2 flag 保留用于未来完全替换四柱计算后的平滑切换。
# ──────────────────────────────────────────────────────────────────────────────

def _calculate_v2(
    dt: datetime,
    lon: float,
    tz: str,
    use_solar: bool,
    mode: str,
    gender: Optional[str],
    request_id: str,
    extra_warnings: list[str],
    city_tier: Optional[str] = None,
    industry: Optional[str] = None,
) -> CalculateResult:
    """
    ENGINE_V2=true 入口.

    当前实现：委托 _calculate_v1，后者已集成全部 services/bazi_engine/ 新引擎模块。
    四柱仍使用 sxtwl/cnlunar（精度优先，有意设计）。
    如需彻底替换四柱层，在此函数添加新实现并切换路由。
    """
    logger.debug("[BaziEngineService] ENGINE_V2=true")
    result = _calculate_v1(
        dt=dt, lon=lon, tz=tz, use_solar=use_solar,
        mode=mode, gender=gender, request_id=request_id,
        extra_warnings=extra_warnings,
        city_tier=city_tier, industry=industry,
    )
    result.engine_version = "v2"
    return result


# ──────────────────────────────────────────────────────────────────────────────
# 公开入口
# ──────────────────────────────────────────────────────────────────────────────

def calculate(
    dt: datetime,
    lon: float,
    tz: str,
    use_solar: bool = False,
    mode: str = "single",
    gender: Optional[str] = None,
    request_id: str = "unknown",
    extra_warnings: list[str] | None = None,
    city_tier: Optional[str] = None,
    industry: Optional[str] = None,
) -> CalculateResult:
    """
    统一八字计算入口.

    Parameters:
        dt:              出生时间（带时区或naive均可）
        lon:             出生经度（-180~180）
        tz:              IANA 时区名称
        use_solar:       是否启用太阳时矫正
        mode:            "single" | "dual"
        gender:          "male" | "female" | None
        request_id:      请求追踪 ID
        extra_warnings:  额外警告信息
        city_tier:       城市层级 (M3.03) 一线/新一线/其余
        industry:        行业 (M3.03) 金融IT/教育公务/其余

    Returns:
        CalculateResult with verify_response and metadata
    """
    _extra = extra_warnings or []

    # ── M3 排盘结果缓存 (TTL=1h, LRU=500) ────────────────────────────────────
    cache_key = _make_cache_key(dt, lon, mode, gender)
    if _CACHETOOLS_AVAILABLE and cache_key in _RESULT_CACHE:
        cached: CalculateResult = _RESULT_CACHE[cache_key]
        logger.debug("[Cache] HIT key=%s...", cache_key[:8])
        return cached

    if _engine_v2_enabled():
        result = _calculate_v2(
            dt=dt, lon=lon, tz=tz, use_solar=use_solar,
            mode=mode, gender=gender, request_id=request_id,
            extra_warnings=_extra,
            city_tier=city_tier, industry=industry,
        )
    else:
        result = _calculate_v1(
            dt=dt, lon=lon, tz=tz, use_solar=use_solar,
            mode=mode, gender=gender, request_id=request_id,
            extra_warnings=_extra,
            city_tier=city_tier, industry=industry,
        )

    # ── R38: 将 engine_version 同步到 verify_response ─────────────────────────
    result.verify_response.engine_version = result.engine_version

    # ── 存入缓存 ──────────────────────────────────────────────────────────────
    if _CACHETOOLS_AVAILABLE:
        _RESULT_CACHE[cache_key] = result
        logger.debug("[Cache] STORE key=%s...", cache_key[:8])

    return result


# ──────────────────────────────────────────────────────────────────────────────
# 月干支辅助（五虎遁年起月法）
# ──────────────────────────────────────────────────────────────────────────────

_STEMS = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
_MONTH_BRANCHES = ["寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥", "子", "丑"]
# 山年令天干对应正月（寅月）起天干
_YEAR_STEM_MONTH1_STEM: dict[str, str] = {
    "甲": "丙", "己": "丙",
    "乙": "戊", "庚": "戊",
    "丙": "庚", "辛": "庚",
    "丁": "壬", "壬": "壬",
    "戊": "甲", "癸": "甲",
}


def _build_month_ganzhis(year_stem: str) -> list[str] | None:
    """根据年天干，返回当年12个月的干支（正月=寅月起）。"""
    start = _YEAR_STEM_MONTH1_STEM.get(year_stem)
    if not start:
        return None
    start_idx = _STEMS.index(start)
    return [
        _STEMS[(start_idx + i) % 10] + _MONTH_BRANCHES[i]
        for i in range(12)
    ]


def _get_current_dayun_stem(
    dayun_list: list[dict],
    birth_year: int,
    birth_month: int = 7,
    birth_day: int = 1,
) -> str | None:
    """根据今天日期精确推算当前大运天干（考虑出生月日，P1-D）。"""
    from datetime import date
    _td = date.today()
    current_age = _td.year - birth_year - (
        (_td.month, _td.day) < (birth_month, birth_day)
    )
    current: dict | None = None
    for item in dayun_list:
        start_age = item.get("start_age")
        if start_age is not None and float(start_age) <= current_age:
            current = item
        else:
            if start_age is not None:
                break
    return current.get("stem") if current else None


# ──────────────────────────────────────────────────────────────────────────────
# M2: 分析引擎集成辅助
# ──────────────────────────────────────────────────────────────────────────────

def _enrich_v2_analysis(
    verify_response: VerifyResponse,
    rp: PillarsModel,
    yongshen,          # YongShenModel
    strength,          # DayMasterStrengthModel
    wuxing_score,      # WuXingScoreModel
    dayun_model,       # DaYunModel
    dt: datetime,
    gender: Optional[str],
    mode: str,
    city_tier: Optional[str] = None,
    industry: Optional[str] = None,
) -> VerifyResponse:
    """
    调用 M2 各分析引擎，填充 VerifyResponse 的新字段。
    全部在 try/except 中保护，不影响核心八字计算。
    """
    from services.bazi_engine.wuxing import compute_shishen_scores
    from services.bazi_engine.geju import compute_geju
    from services.bazi_engine.shensha import compute_shensha
    from services.bazi_engine.palace import compute_palace
    from services.bazi_engine.analysis.wealth import compute_wealth
    from services.bazi_engine.analysis.career import compute_career
    from services.bazi_engine.analysis.marriage import compute_marriage
    from services.bazi_engine.analysis.health import compute_health
    from services.bazi_engine.analysis.relationship import compute_relationship
    from services.bazi_engine.analysis.personality import compute_personality
    from services.bazi_engine.analysis.monthly import compute_monthly
    from services.bazi_engine.lifestyle.jewelry import compute_jewelry
    from services.bazi_engine.lifestyle.fengshui import compute_fengshui
    from services.bazi_engine.lifestyle.lucky import compute_lucky
    from services.bazi_engine.lifestyle.lifestyle import compute_lifestyle
    from services.bazi_engine.milestones import compute_milestones
    from app.schemas.analysis import (
        GejuModel, PalaceModel, PalaceItemModel, ShenshaModel,
        LifeArcModel, CurrentFortuneSummaryModel,
    )

    # ── 基础数据提取 ────────────────────────────────────────────────────
    ys_br = rp.year.branch
    ms_br = rp.month.branch
    ds_br = rp.day.branch
    hs_br = rp.hour.branch
    ys_st = rp.year.stem
    ms_st = rp.month.stem
    ds_st = rp.day.stem
    hs_st = rp.hour.stem
    all_branches = [ys_br, ms_br, ds_br, hs_br]

    favor: list[str] = list(yongshen.favor) if hasattr(yongshen, "favor") and yongshen.favor else []
    avoid: list[str] = list(yongshen.avoid) if hasattr(yongshen, "avoid") and yongshen.avoid else []
    strength_score: float = float(strength.score) if hasattr(strength, "score") else 50.0
    strength_tier: str = getattr(strength, "tier", "中和") or "中和"
    wx_scores = _to_wuxing_scores(wuxing_score)

    # 大运列表
    dayun_list: list[dict] = []
    if hasattr(dayun_model, "items"):
        for item in (dayun_model.items or []):
            d = item.model_dump() if hasattr(item, "model_dump") else dict(item.__dict__)
            dayun_list.append(d)

    # ── N5.07: 起运年龄 ──────────────────────────────────────────────────
    try:
        if hasattr(verify_response, "dayun") and verify_response.dayun:
            _sm = verify_response.dayun.start_age_months or 0
            _sa = verify_response.dayun.start_age or 0
            verify_response.start_dayun_age = round(float(_sm) / 12.0, 1) if _sm else float(_sa)
    except Exception as exc:
        logger.debug("[N5.07 start_dayun_age] %s", exc)

    # ── 十神得分 ──────────────────────────────────────────────────────
    shishen_scores = compute_shishen_scores(
        day_stem=ds_st,
        year_stem=ys_st, month_stem=ms_st, hour_stem=hs_st,
        year_branch=ys_br, month_branch=ms_br,
        day_branch=ds_br, hour_branch=hs_br,
    )

    # ── 格局 ─────────────────────────────────────────────────────────
    is_broken: bool = False  # P2-A: 在 try 外初始化避免 dir() 脆弱模式
    try:
        geju_raw = compute_geju(
            year_stem=ys_st, month_stem=ms_st, month_branch=ms_br,
            day_stem=ds_st, hour_stem=hs_st, wuxing_scores=wx_scores,
            year_branch=ys_br, day_branch=ds_br, hour_branch=hs_br,  # N1.03 三合局
        )
        geju_name = geju_raw.get("name", "普通格")
        is_broken = not geju_raw.get("confident", True)
        from typing import cast as _cast
        from services.bazi_engine.classic_refs import get_refs_by_tag as _geju_get_refs
        _geju_refs_text = "\n".join(
            f"【{r.get('source','')}】{r.get('text','')}"
            for r in _geju_get_refs("格局")[:2]
            if r.get("text")
        )
        verify_response.geju = GejuModel(
            geju_name=geju_name,
            geju_level=_geju_level(geju_name),  # type: ignore[arg-type]
            month_stem_shishen=geju_raw.get("ten_god", ""),
            is_broken=is_broken,
            inference_tags=[geju_name],
            interpretation_text=geju_raw.get("note", ""),
            classic_ref=_geju_refs_text,
            confidence=geju_raw.get("confidence", 0.0),
            geju_detail=geju_raw.get("note", ""),
        )
    except Exception as exc:
        logger.debug("[M2 geju] %s", exc)
        geju_name = "普通格"
        if hasattr(verify_response, "validation") and verify_response.validation:
            verify_response.validation.warnings.append(
                WarningModel(code="M2_GEJU_FAIL", message="格局计算失败，已降级为普通格")
            )

    # ── 建禄格/羊刃格：重算用神（geju_name 确定后）────────────────────────
    if geju_name in ("建禄格", "羊刃格"):
        try:
            from services.bazi_engine.wuxing import compute_wuxing as _eng_wx2
            from services.bazi_engine.strength import compute_strength as _eng_str2
            from services.bazi_engine.yongshen import compute_yongshen as _eng_ys2
            _w2 = _eng_wx2(ys_st, ys_br, ms_st, ms_br, ds_st, ds_br, hs_st, hs_br)
            _s2 = _eng_str2(ds_st, ms_br, ys_st, ms_st, hs_st, ys_br, ds_br, hs_br, _w2)
            _ys2 = _eng_ys2(
                day_stem=ds_st, month_branch=ms_br,
                strength=_s2, wuxing=_w2, geju_name=geju_name,
            )
            verify_response.yongshen = YongShenModel(
                favor=_ys2.favor, avoid=_ys2.avoid, rationale=_ys2.rationale,
            )
            favor = list(_ys2.favor)
            avoid = list(_ys2.avoid)
        except Exception as _exc2:
            logger.debug("[M2 geju-yongshen] %s", _exc2)

    # ── 神煞 ─────────────────────────────────────────────────────────
    shensha_items_raw: list[dict] = []
    try:
        shensha_raw = compute_shensha(
            year_stem=ys_st, year_branch=ys_br,
            month_stem=ms_st, month_branch=ms_br,
            day_stem=ds_st, day_branch=ds_br,
            hour_stem=hs_st, hour_branch=hs_br,
        )
        shensha_items_raw = shensha_raw.get("items", [])
        _shensha_star_chart = shensha_raw.get("star", False)  # ≥3 unique items
        verify_response.shensha = [
            ShenshaModel(
                name=s.get("name", ""),
                dizhi=s.get("pillar", ""),
                pillar=s.get("pillar", ""),
                is_beneficial=(s.get("polarity", "") == "+"),
                # ★ 当整体符合 ≥3 条神煞且本项为 A 级吉神时标记 [P69]
                is_star=_shensha_star_chart and s.get("priority", "") == "A",
                priority=s.get("priority", "B"),  # M1.09: A/B/C 三级优先度传递到前端
                meaning=s.get("note", ""),
                classic_source=s.get("classic", ""),
            )
            for s in shensha_items_raw
        ]
        # RL#9: 桃花星 → 回写 social.taohua_hit
        has_taohua = any(s.get("name") == "桃花" for s in shensha_items_raw)
        if verify_response.social is not None:
            verify_response.social.taohua_hit = has_taohua
    except Exception as exc:
        logger.debug("[M2 shensha] %s", exc)

    # ── 宫位 ─────────────────────────────────────────────────────────
    try:
        palace_raw = compute_palace(
            year_branch=ys_br, month_branch=ms_br,
            day_stem=ds_st, day_branch=ds_br, hour_branch=hs_br,
        )
        twelve: dict[str, str] = palace_raw.get("twelve_palaces", {})
        palace_items = [
            PalaceItemModel(
                palace_name=name, dizhi=br,
                tiangan="", strength="旺" if br in (ds_br, ys_br) else "相",
                shishen="", note="",
            )
            for name, br in twelve.items()
        ]
        ming_gong_br = palace_raw.get("ming_gong", "")
        shen_gong_br = palace_raw.get("shen_gong", "")
        ming_item = PalaceItemModel(
            palace_name="命宫", dizhi=ming_gong_br, tiangan="",
            strength="旺", shishen="", note="",
        )
        shen_item = PalaceItemModel(
            palace_name="身宫", dizhi=shen_gong_br, tiangan="",
            strength="旺", shishen="", note="",
        )
        verify_response.palace = PalaceModel(
            ming_gong=ming_item,
            shen_gong=shen_item,
            twelve_palaces=palace_items,
            inference_tags=[],
            interpretation_text=f"命宫{ming_gong_br}，身宫{shen_gong_br}",
        )
    except Exception as exc:
        logger.debug("[M2 palace] %s", exc)

    # ── 7 分析引擎 ────────────────────────────────────────────────────
    # P1-A: M2 各引擎失败时统一写入 warnings（§4.5）
    def _m2_warn(code: str, msg: str) -> None:
        if hasattr(verify_response, "validation") and verify_response.validation:
            verify_response.validation.warnings.append(
                WarningModel(code=code, message=msg)
            )

    try:
        verify_response.wealth_analysis = compute_wealth(
            yongshen_favor=favor, yongshen_avoid=avoid,
            wuxing_scores=wx_scores, shishen_scores=shishen_scores,
            strength_score=strength_score, dayun_list=dayun_list,
            day_branch=ds_br,
        )
    except Exception as exc:
        logger.debug("[M2 wealth] %s", exc)
        _m2_warn("M2_WEALTH_FAIL", "财运分析计算失败，结果可能不完整")

    try:
        verify_response.career = compute_career(
            geju_name=geju_name, yongshen_favor=favor, yongshen_avoid=avoid,
            shishen_scores=shishen_scores, strength_score=strength_score,
            dayun_list=dayun_list, day_branch=ds_br,
        )
    except Exception as exc:
        logger.debug("[M2 career] %s", exc)
        _m2_warn("M2_CAREER_FAIL", "事业分析计算失败，结果可能不完整")

    try:
        verify_response.marriage_analysis = compute_marriage(
            all_branches=all_branches, day_branch=ds_br,
            shishen_scores=shishen_scores, shensha_items=shensha_items_raw,
            gender=gender or "male", yongshen_favor=favor, yongshen_avoid=avoid,
            dayun_list=dayun_list, strength_score=strength_score,
        )
    except Exception as exc:
        logger.debug("[M2 marriage] %s", exc)
        _m2_warn("M2_MARRIAGE_FAIL", "婚姻分析计算失败，结果可能不完整")

    try:
        verify_response.health = compute_health(
            wuxing_scores=wx_scores, yongshen_favor=favor,
            yongshen_avoid=avoid, day_stem=ds_st,
        )
    except Exception as exc:
        logger.debug("[M2 health] %s", exc)
        _m2_warn("M2_HEALTH_FAIL", "健康分析计算失败，结果可能不完整")

    try:
        verify_response.relationship = compute_relationship(
            shishen_scores=shishen_scores, shensha_items=shensha_items_raw,
            gender=gender or "male", day_stem=ds_st, dayun_list=dayun_list,
        )
    except Exception as exc:
        logger.debug("[M2 relationship] %s", exc)
        _m2_warn("M2_RELATIONSHIP_FAIL", "人际关系分析计算失败，结果可能不完整")

    try:
        verify_response.personality = compute_personality(
            day_stem=ds_st, strength_tier=strength_tier,
            strength_score=strength_score, geju_name=geju_name,
        )
    except Exception as exc:
        logger.debug("[M2 personality] %s", exc)
        _m2_warn("M2_PERSONALITY_FAIL", "性格分析计算失败，结果可能不完整")

    try:
        # P1-F: 月运 year_branch 使用当前年地支（而非出生年地支）
        # P2-C: 月干支基于当前年天干（而非出生年天干）
        from datetime import date as _date_now
        _cur_yr_int = _date_now.today().year
        _CUR_STEMS   = ["甲","乙","丙","丁","戊","己","庚","辛","壬","癸"]
        _CUR_BRANCHES= ["子","丑","寅","卯","辰","巳","午","未","申","酉","戌","亥"]
        _cur_yr_stem   = _CUR_STEMS[(_cur_yr_int - 4) % 10]
        _cur_yr_branch = _CUR_BRANCHES[(_cur_yr_int - 4) % 12]
        _month_ganzhis = _build_month_ganzhis(_cur_yr_stem)
        _dayun_stem = _get_current_dayun_stem(
            dayun_list, dt.year, dt.month, dt.day
        )
        verify_response.monthly_fortune = compute_monthly(
            day_branch=ds_br, yongshen_favor=favor, yongshen_avoid=avoid,
            year_branch=_cur_yr_branch, mode=mode,
            month_ganzhis=_month_ganzhis,
            current_dayun_stem=_dayun_stem,
            day_stem=ds_st,   # N2.03 十神关系
        )
    except Exception as exc:
        logger.debug("[M2 monthly] %s", exc)
        if hasattr(verify_response, "validation") and verify_response.validation:
            verify_response.validation.warnings.append(
                WarningModel(code="M2_MONTHLY_FAIL", message="月运模块计算失败，结果可能不完整")
            )

    # ── M2.5: lifestyle/里程碑 ────────────────────────────────────────
    try:
        verify_response.jewelry = compute_jewelry(
            yongshen_favor=favor, yongshen_avoid=avoid,
        )
    except Exception as exc:
        logger.debug("[M2.5 jewelry] %s", exc)

    try:
        verify_response.fengshui = compute_fengshui(
            yongshen_favor=favor, yongshen_avoid=avoid,
        )
    except Exception as exc:
        logger.debug("[M2.5 fengshui] %s", exc)

    try:
        verify_response.lucky = compute_lucky(
            yongshen_favor=favor, yongshen_avoid=avoid,
        )
    except Exception as exc:
        logger.debug("[M2.5 lucky] %s", exc)

    try:
        verify_response.lifestyle = compute_lifestyle(
            yongshen_favor=favor, yongshen_avoid=avoid,
        )
    except Exception as exc:
        logger.debug("[M2.5 lifestyle] %s", exc)

    try:
        birth_year = dt.year
        liunian_items: list[dict] = []
        if hasattr(verify_response, "dayun") and verify_response.dayun:
            for dy in (verify_response.dayun.items or []):
                dy_dict = dy.model_dump() if hasattr(dy, "model_dump") else dict(dy.__dict__)
                # 流年从大运年份中提取（简化：取大运起始年+0~9）
                start_age = dy_dict.get("start_age", 0)
                dy_branch = dy_dict.get("branch", "")
                _gz_stems_m = ["甲","乙","丙","丁","戊","己","庚","辛","壬","癸"]
                _gz_branches_m = ["子","丑","寅","卯","辰","巳","午","未","申","酉","戌","亥"]
                for i in range(10):
                    yr = birth_year + start_age + i
                    _yr_stem = _gz_stems_m[(yr - 4) % 10]
                    _yr_branch = _gz_branches_m[(yr - 4) % 12]
                    liunian_items.append({
                        "year": yr,
                        "ganzhi": _yr_stem + _yr_branch,
                        "branch": _yr_branch,
                        "stem": _yr_stem,
                    })
        verify_response.milestones = compute_milestones(
            birth_year=birth_year, day_branch=ds_br, year_branch=ys_br,
            dayun_list=dayun_list, liunian_list=liunian_items,
            yongshen_favor=favor, yongshen_avoid=avoid,
        )
    except Exception as exc:
        logger.debug("[M2.5 milestones] %s", exc)

    # ── RL#10: 流年 items 填充（当前年份前后2年）────────────────────
    try:
        import datetime as _dt_mod
        from services.bazi_engine.liunian import compute_liunian as _compute_liunian
        from app.schemas.bazi import LiuNianItemModel as _LiuNianItemModel, LiuNianResultModel as _LiuNianResultModel
        _cur_yr = _dt_mod.date.today().year
        _ln_rows = _compute_liunian(
            day_stem=ds_st, day_branch=ds_br,
            start_year=_cur_yr - 2, end_year=_cur_yr + 2,
        )
        _ln_items = [
            _LiuNianItemModel(
                year=r["year"], stem=r["stem"], branch=r["branch"],
                ten_god=r.get("ten_god"), clash=r.get("clash"),
            )
            for r in _ln_rows
        ]
        verify_response.liunian = _LiuNianResultModel(
            years_used=list(range(_cur_yr - 2, _cur_yr + 3)),
            items=_ln_items,
        )
    except Exception as exc:
        logger.debug("[RL#10 liunian] %s", exc)

    # ── 任务 2.10: rule_version_detail dict ──────────────────────────
    verify_response.rule_version_detail = {
        "wuxing":       "v1.0",
        "strength":     "v1.0",
        "yongshen":     "v1.0",
        "dayun":        "v1.0",
        "shensha":      "v1.0",
        "geju":         "v1.0",
        "palace":       "v1.0",
        "wealth":       "v2.0",
        "career":       "v2.0",
        "marriage":     "v2.0",
        "health":       "v2.0",
        "relationship": "v2.0",
        "personality":  "v2.0",
        "monthly":      "v2.0",
        "jewelry":      "v2.0",
        "fengshui":     "v2.0",
        "lucky":        "v2.0",
        "lifestyle":    "v2.0",
        "milestones":   "v2.0",
        # M3
        "interpret":    "v3.0",
        "life_arc":     "v3.0",
        "scoring":      "v3.0",
        "liunian_domain": "v3.0",
    }

    # ────────────────────────────────────────────────────────────────────────
    # M3.02: 大运叙事生成器 (400-600字/步)
    # ────────────────────────────────────────────────────────────────────────
    try:
        from services.bazi_engine.analysis.dayun_narrative import generate_dayun_narrative
        _wealth_tier_for_narrative = "中格"
        if verify_response.wealth_analysis:
            _wt = getattr(verify_response.wealth_analysis, "wealth_tier", None)
            _wealth_tier_for_narrative = {"上": "高格", "中": "中格", "下": "低格"}.get(_wt or "", "中格")
        _geju_for_nar = geju_name if geju_name else "普通格"
        if hasattr(verify_response, "dayun") and verify_response.dayun:
            _nar_items = list(verify_response.dayun.items or [])
            for _i, _it in enumerate(_nar_items):
                if _it.narrative:
                    continue
                _dy_ganzhi = (_it.stem or "?") + (_it.branch or "?")
                _end_age = int((_nar_items[_i + 1].start_age or 0) - 1) if _i + 1 < len(_nar_items) else int((_it.start_age or 0) + 9)
                _is_fav = (_it.flow_wuxing or "") in favor
                try:
                    _it.narrative = generate_dayun_narrative(
                        stem=_it.stem or "",
                        branch=_it.branch or "",
                        ganzhi=_dy_ganzhi,
                        ten_god=_it.ten_god or "",
                        start_age=int(_it.start_age or 0),
                        end_age=_end_age,
                        yongshen_favor=favor,
                        geju_name=_geju_for_nar,
                        strength_tier=strength_tier,
                        wealth_tier=_wealth_tier_for_narrative,
                        is_favorable=_is_fav,
                    )
                except Exception as _ne:
                    logger.debug("[M3.02 narrative step %d] %s", _i, _ne)
    except Exception as exc:
        logger.debug("[M3.02 dayun_narrative] %s", exc)

    # ────────────────────────────────────────────────────────────────────────
    # M3 新增: interpret.py 解读文本
    # ────────────────────────────────────────────────────────────────────────
    try:
        from services.bazi_engine.interpret import interpret_bazi, InterpretInput
        from services.bazi_engine.relations import get_branch_relations as _get_branch_rels, get_stem_clashes as _get_stem_clashes  # P0-11
        _rp_branches = (
            verify_response.pillars_primary.year.branch,
            verify_response.pillars_primary.month.branch,
            verify_response.pillars_primary.day.branch,
            verify_response.pillars_primary.hour.branch,
        ) if verify_response.pillars_primary else ("", "", "", "")
        _dizhi_rels = _get_branch_rels(*_rp_branches)
        # 写入响应（P0-10: 地支关系 status 含全合/半合/拱合）
        verify_response.dizhi_relations = _dizhi_rels
        # P0-11: 天干相克 scope=day_related
        try:
            verify_response.tiangan_clashes = _get_stem_clashes(
                ys_st, ms_st, ds_st, hs_st, scope="day_related"
            )
        except Exception as _tc_exc:
            logger.debug("[P0-11 tiangan_clashes] %s", _tc_exc)
        interp_inp = InterpretInput(
            day_stem=ds_st,
            wuxing_scores=wx_scores,
            yongshen_favor=favor,
            yongshen_avoid=avoid,
            strength_tier=strength_tier,
            geju_name=geju_name,
            shensha_items=shensha_items_raw,
            dizhi_relations=_dizhi_rels,
            dayun_trend=_infer_dayun_trend(dayun_list),
            gender=gender or "male",
        )
        interp_result = interpret_bazi(interp_inp)
        # 将解读文本写入已有模型的 interpretation_text
        if verify_response.geju and not verify_response.geju.interpretation_text:
            verify_response.geju.interpretation_text = interp_result.geju_text
        if verify_response.wealth_analysis and not verify_response.wealth_analysis.interpretation_text:
            verify_response.wealth_analysis.interpretation_text = interp_result.lifestyle_text[:80]
        if verify_response.health and not verify_response.health.interpretation_text:
            verify_response.health.interpretation_text = interp_result.lifestyle_text[80:160]
    except Exception as exc:
        logger.debug("[M3 interpret] %s", exc)

    # ── RL#33: 三层模型 — wealth 同步 interpretation_text + inference_tags ──
    try:
        _wa = verify_response.wealth_analysis
        _w  = verify_response.wealth
        if _w is not None:
            if not _w.interpretation_text:
                if _wa and _wa.interpretation_text:
                    _w.interpretation_text = _wa.interpretation_text
                else:
                    # fallback: 结合财富得分生成简要解读
                    _score = _w.wealth_score or 50.0
                    _tags  = "、".join(_w.industry_tags[:2]) if _w.industry_tags else "综合"
                    _w.interpretation_text = (
                        f"综合财富评分 {_score:.1f}，推荐关注 {_tags} 等领域。"
                    )
            if not _w.inference_tags:
                if _wa and getattr(_wa, "inference_tags", None):
                    _w.inference_tags = list(_wa.inference_tags)[:3]
                else:
                    _w.inference_tags = [f"用神{f}" for f in favor[:2]] + ["wealth_v2"]
    except Exception as exc:
        logger.debug("[RL#33 wealth three-layer] %s", exc)

    # ────────────────────────────────────────────────────────────────────────
    # M3 新增: life_arc 人生弧线
    # ────────────────────────────────────────────────────────────────────────
    try:
        from services.bazi_engine.life_arc import compute_life_arc as _compute_life_arc
        from app.schemas.analysis import LifeArcModel as _LifeArcSchema

        _arc = _compute_life_arc(
            dayun_list=dayun_list,
            geju_name=geju_name,
            is_broken=is_broken if "is_broken" in dir() else False,
            strength_tier=strength_tier,
            strength_score=strength_score,
            yongshen_favor=favor,
            wuxing_scores=wx_scores,
        )
        # 选一条古籍作为 life_motto
        _motto_ref = (
            "用神得力，行顺运则诸事顺遂。"
            "——《子平真诠·论大运》"
        )
        verify_response.life_arc = _LifeArcSchema(
            overall_tier=_arc.overall_tier,  # type: ignore[arg-type]
            early_fortune=_arc.early_fortune,
            mid_fortune=_arc.mid_fortune,
            late_fortune=_arc.late_fortune,
            peak_periods=_arc.peak_periods,
            caution_periods=_arc.caution_periods,
            life_motto=_motto_ref,
            inference_tags=[_arc.overall_tier, f"score={_arc.total_score:.0f}"],
            interpretation_text=_arc.summary,
            disclaimer=_arc.disclaimer,
        )
    except Exception as exc:
        logger.debug("[M3 life_arc] %s", exc)

    # ────────────────────────────────────────────────────────────────────────
    # M3 新增: liunian_detail (domain_forecasts)
    # ────────────────────────────────────────────────────────────────────────
    try:
        from services.bazi_engine.analysis.liunian_domain import compute_liunian_domain_forecasts
        from services.bazi_engine.liunian import _liunian_day_relation  # 红线10 犯太岁
        from app.schemas.analysis import LiuNianDetailModel
        import datetime as _dt_now_mod

        # 取当前年前后2年共5年（而非出生年）
        current_year = _dt_now_mod.datetime.now().year
        _detail_list: list[LiuNianDetailModel] = []

        # 从大运列表生成流年信息
        _GANZHI_STEMS   = ["甲","乙","丙","丁","戊","己","庚","辛","壬","癸"]
        _GANZHI_BRANCHES= ["子","丑","寅","卯","辰","巳","午","未","申","酉","戌","亥"]

        def _year_ganzhi(y: int) -> tuple[str, str]:
            """返回 (天干, 地支)"""
            return (_GANZHI_STEMS[(y - 4) % 10], _GANZHI_BRANCHES[(y - 4) % 12])

        # 生成当前年份前后2年共5年
        for yr in range(current_year - 2, current_year + 3):
            ystem, ybranch = _year_ganzhi(yr)
            # 红线10: 计算犯太岁关系（流年支 vs 命局年支）
            taisui_rel = _liunian_day_relation(ybranch, ys_br)
            taisui_list = [taisui_rel] if taisui_rel else []
            domain = compute_liunian_domain_forecasts(
                year=yr, year_stem=ystem, year_branch=ybranch,
                day_stem=ds_st, day_branch=ds_br,
                shishen_scores=shishen_scores,
                yongshen_favor=favor,
                wuxing_scores=wx_scores,
                gender=gender or "male",
            )
            _detail_list.append(LiuNianDetailModel(
                year=yr,
                ganzhi=f"{ystem}{ybranch}",
                tai_sui_relations=taisui_list,  # 红线10: 犯太岁关系
                clash_pillars=[],
                notable_months=[],
                annual_score=_domain_to_score(domain, favor, ystem),
                domain_forecasts=domain,
                inference_tags=[f"{ystem}{ybranch}", "liunian"],
                interpretation_text=(
                    f"{yr}年({ystem}{ybranch})：财运—{domain['财运'][:20]}；"
                    f"事业—{domain['事业'][:20]}。"
                ),
            ))
        verify_response.liunian_detail = _detail_list
    except Exception as exc:
        logger.debug("[M3 liunian_detail] %s", exc)

    # ────────────────────────────────────────────────────────────────────────
    # M3/M4: current_fortune_summary (Tab 0 精简卡片)
    # ────────────────────────────────────────────────────────────────────────
    try:
        from app.schemas.analysis import CurrentFortuneSummaryModel as _CFS
        import datetime as _dt_mod

        def _year_ganzhi_cfs(y: int) -> str:
            _STEMS10   = ["甲","乙","丙","丁","戊","己","庚","辛","壬","癸"]
            _BRANCHES12= ["子","丑","寅","卯","辰","巳","午","未","申","酉","戌","亥"]
            return _STEMS10[(y - 4) % 10] + _BRANCHES12[(y - 4) % 12]

        import datetime as _dt_today_mod
        current_year = _dt_today_mod.date.today().year
        liunian_gz = _year_ganzhi_cfs(current_year)
        liunian_stem = liunian_gz[0]
        liunian_branch = liunian_gz[1]

        # 当前大运：找到start_age<=当前年龄的最后一条大运
        _today = _dt_today_mod.date.today()
        age_now = _today.year - dt.year - (
            (_today.month, _today.day) < (dt.month, dt.day)
        ) if dt else 0
        current_dy = (dayun_list[0] if dayun_list else {})
        for _dy_item in dayun_list:
            _sa = _dy_item.get("start_age")
            if _sa is not None and float(_sa) <= age_now:
                current_dy = _dy_item
            elif _sa is not None:
                break
        dayun_gz = f"{current_dy.get('stem','?')}{current_dy.get('branch','?')}" if current_dy else "??"
        start_age = current_dy.get("start_age", 0) if current_dy else 0
        start_yr  = current_dy.get("start_year", 0) if current_dy else 0
        years_remaining = max(0, 10 - (current_year - int(start_yr))) if start_yr else 5

        # 今年四维
        from services.bazi_engine.analysis.liunian_domain import compute_liunian_domain_forecasts as _clf
        domains = _clf(
            year=current_year, year_stem=liunian_stem, year_branch=liunian_branch,
            day_stem=ds_st, day_branch=ds_br,
            shishen_scores=shishen_scores,
            yongshen_favor=favor, wuxing_scores=wx_scores,
            gender=gender or "male",
        )
        top3 = [
            f"流年{liunian_gz}：{v[:25]}" for v in domains.values()
        ][:3]

        verify_response.current_fortune_summary = _CFS(
            current_dayun=dayun_gz,
            dayun_years_remaining=years_remaining,
            current_liunian=liunian_gz,
            this_year_domains=domains,
            top3_actions=top3,
        )
    except Exception as exc:
        logger.debug("[M4 current_fortune_summary] %s", exc)

    # ── N2.05 五行均衡评分 ────────────────────────────────────────────────────
    try:
        from services.bazi_engine.scoring import (
            balance_score as _balance_score,
            get_wuxing_weak_strong as _wws,
            build_balance_advice as _bba,
        )
        verify_response.wuxing_balance_score = _balance_score(wx_scores)
        _weak, _strong = _wws(wx_scores)
        verify_response.wuxing_weak   = _weak   or None
        verify_response.wuxing_strong = _strong or None
        verify_response.balance_advice = _bba(_weak, _strong)
    except Exception as exc:
        logger.debug("[N2.05 balance_score] %s", exc)

    # ── N2.07 流年运势（当前大运覆盖年份）───────────────────────────────────
    try:
        from services.bazi_engine.liunian import compute_liunian_for_dayun as _clf_dayun
        _cur_dy = dayun_list[0] if dayun_list else {}
        if _cur_dy:
            _dy_start_age  = int(_cur_dy.get("start_age",  0))
            _dy_start_year = int(_cur_dy.get("start_year", 0))
            if _dy_start_year > 0:
                _liunian_list = _clf_dayun(
                    day_stem=ds_st,
                    day_branch=ds_br,
                    dayun_start_age=_dy_start_age,
                    dayun_start_year=_dy_start_year,
                    span=10,
                )
                verify_response.yearly_fortune = _liunian_list
    except Exception as exc:
        logger.debug("[N2.07 yearly_fortune] %s", exc)

    return verify_response


def _infer_dayun_trend(dayun_list: list[dict]) -> str:
    """从大运列表推断当前大运趋势"""
    if not dayun_list:
        return "平稳"
    current = dayun_list[0] if len(dayun_list) == 1 else next(
        (d for d in dayun_list if d.get("is_current", False)),
        dayun_list[0],
    )
    return current.get("trend", "平稳")


def _domain_to_score(
    domain: dict[str, str],
    favor: list[str],
    year_stem: str,
) -> int:
    """将 domain_forecasts 转为 annual_score [0-100]"""
    _STEM_WX = {
        "甲": "wood", "乙": "wood", "丙": "fire", "丁": "fire",
        "戊": "earth", "己": "earth", "庚": "metal", "辛": "metal",
        "壬": "water", "癸": "water",
    }
    wx = _STEM_WX.get(year_stem, "")
    base = 60
    if wx in favor:
        base += 15
    for val in domain.values():
        if "顺" in val or "宜" in val or "旺" in val:
            base += 3
        if "防" in val or "逆" in val or "守成" in val:
            base -= 2
    return max(10, min(100, base))


def _geju_level(geju_name: str) -> str:
    """根据格局名称粗估格局等级"""
    high = {"正官格", "正印格", "食神格", "正财格", "从财格", "从官格", "从儿格"}
    mid  = {"偏官格", "七杀格", "偏印格", "偏财格", "建禄格"}
    if geju_name in high:
        return "上格"
    if geju_name in mid:
        return "中格"
    if geju_name == "普通格":
        return "无格"
    return "下格"
