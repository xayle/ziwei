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
    from cachetools import TTLCache
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
    # 以下供内部调试/日志使用
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

    wuxing_score_raw, _ = compute_wuxing(rp)
    strength_raw = compute_strength(rp.day.stem, wuxing_score_raw)
    yongshen_raw = compute_yongshen(wuxing_score_raw, strength_raw)
    ten_gods_map = build_ten_gods(rp.day.stem, rp)
    ten_gods = TenGodsModel(**ten_gods_map)

    wuxing_score = WuXingScoreModel.model_validate(
        wuxing_score_raw.model_dump() if hasattr(wuxing_score_raw, "model_dump")
        else getattr(wuxing_score_raw, "__dict__", wuxing_score_raw)
    )
    strength = DayMasterStrengthModel.model_validate(
        strength_raw.model_dump() if hasattr(strength_raw, "model_dump")
        else getattr(strength_raw, "__dict__", strength_raw)
    )
    yongshen = YongShenModel.model_validate(
        yongshen_raw.model_dump() if hasattr(yongshen_raw, "model_dump")
        else getattr(yongshen_raw, "__dict__", yongshen_raw)
    )
    wealth = WealthModel(
        wealth_score=round(strength.score, 2),
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
    dayun_model_raw, _ = build_dayun(dt_effective, rp, methods)
    dayun_model = DaYunModel.model_validate(
        dayun_model_raw.model_dump() if hasattr(dayun_model_raw, "model_dump")
        else getattr(dayun_model_raw, "__dict__", dayun_model_raw)
    )
    _WX_CN_MAP = {"wood": "木", "fire": "火", "earth": "土", "metal": "金", "water": "水"}
    for item in dayun_model.items:
        if item.stem:
            item.ten_god = ten_god(rp.day.stem, item.stem)
        if yongshen.favor:
            item.wealth_hint = f"用神倾向: {', '.join(_WX_CN_MAP.get(f, f) for f in yongshen.favor)}"
        if yongshen.avoid:
            item.health_hint = f"忌神: {', '.join(_WX_CN_MAP.get(a, a) for a in yongshen.avoid)}"

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
    return PillarsModel.model_validate(p.__dict__)


# ──────────────────────────────────────────────────────────────────────────────
# 新引擎路径（ENGINE_V2=true）— M1 完成后启用
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
) -> CalculateResult:
    """
    新引擎路径（M1 完成后激活）.
    目前 fallback 到 v1，等待各子模块集成完成后替换。
    """
    logger.info("[BaziEngineService] ENGINE_V2=true path called (stub→v1 for now)")
    return _calculate_v1(
        dt=dt, lon=lon, tz=tz, use_solar=use_solar,
        mode=mode, gender=gender, request_id=request_id,
        extra_warnings=extra_warnings,
    )


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
        )
    else:
        result = _calculate_v1(
            dt=dt, lon=lon, tz=tz, use_solar=use_solar,
            mode=mode, gender=gender, request_id=request_id,
            extra_warnings=_extra,
        )

    # ── 存入缓存 ──────────────────────────────────────────────────────────────
    if _CACHETOOLS_AVAILABLE:
        _RESULT_CACHE[cache_key] = result
        logger.debug("[Cache] STORE key=%s...", cache_key[:8])

    return result


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

    # ── 十神得分 ──────────────────────────────────────────────────────
    shishen_scores = compute_shishen_scores(
        day_stem=ds_st,
        year_stem=ys_st, month_stem=ms_st, hour_stem=hs_st,
        year_branch=ys_br, month_branch=ms_br,
        day_branch=ds_br, hour_branch=hs_br,
    )

    # ── 格局 ─────────────────────────────────────────────────────────
    try:
        geju_raw = compute_geju(
            year_stem=ys_st, month_stem=ms_st, month_branch=ms_br,
            day_stem=ds_st, hour_stem=hs_st, wuxing_scores=wx_scores,
        )
        geju_name = geju_raw.get("name", "普通格")
        is_broken = not geju_raw.get("confident", True)
        from typing import cast as _cast
        verify_response.geju = GejuModel(
            geju_name=geju_name,
            geju_level=_geju_level(geju_name),  # type: ignore[arg-type]
            month_stem_shishen=geju_raw.get("ten_god", ""),
            is_broken=is_broken,
            inference_tags=[geju_name],
            interpretation_text=geju_raw.get("note", ""),
            classic_ref="",
        )
    except Exception as exc:
        logger.debug("[M2 geju] %s", exc)
        geju_name = "普通格"

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
        verify_response.shensha = [
            ShenshaModel(
                name=s.get("name", ""),
                dizhi=s.get("pillar", ""),
                pillar=s.get("pillar", ""),
                is_beneficial=(s.get("polarity", "") == "positive"),
                is_star=s.get("priority", "") == "high",
                meaning=s.get("note", ""),
                classic_source="",
            )
            for s in shensha_items_raw
        ]
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
    try:
        verify_response.wealth_analysis = compute_wealth(
            yongshen_favor=favor, yongshen_avoid=avoid,
            wuxing_scores=wx_scores, shishen_scores=shishen_scores,
            strength_score=strength_score, dayun_list=dayun_list,
            day_branch=ds_br,
        )
    except Exception as exc:
        logger.debug("[M2 wealth] %s", exc)

    try:
        verify_response.career = compute_career(
            geju_name=geju_name, yongshen_favor=favor, yongshen_avoid=avoid,
            shishen_scores=shishen_scores, strength_score=strength_score,
            dayun_list=dayun_list, day_branch=ds_br,
        )
    except Exception as exc:
        logger.debug("[M2 career] %s", exc)

    try:
        verify_response.marriage_analysis = compute_marriage(
            all_branches=all_branches, day_branch=ds_br,
            shishen_scores=shishen_scores, shensha_items=shensha_items_raw,
            gender=gender or "male", yongshen_favor=favor, yongshen_avoid=avoid,
            dayun_list=dayun_list, strength_score=strength_score,
        )
    except Exception as exc:
        logger.debug("[M2 marriage] %s", exc)

    try:
        verify_response.health = compute_health(
            wuxing_scores=wx_scores, yongshen_favor=favor,
            yongshen_avoid=avoid, day_stem=ds_st,
        )
    except Exception as exc:
        logger.debug("[M2 health] %s", exc)

    try:
        verify_response.relationship = compute_relationship(
            shishen_scores=shishen_scores, shensha_items=shensha_items_raw,
            gender=gender or "male", day_stem=ds_st, dayun_list=dayun_list,
        )
    except Exception as exc:
        logger.debug("[M2 relationship] %s", exc)

    try:
        verify_response.personality = compute_personality(
            day_stem=ds_st, strength_tier=strength_tier,
            strength_score=strength_score, geju_name=geju_name,
        )
    except Exception as exc:
        logger.debug("[M2 personality] %s", exc)

    try:
        verify_response.monthly_fortune = compute_monthly(
            day_branch=ds_br, yongshen_favor=favor, yongshen_avoid=avoid,
            year_branch=ys_br, mode=mode,
        )
    except Exception as exc:
        logger.debug("[M2 monthly] %s", exc)

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
                for i in range(10):
                    yr = birth_year + start_age + i
                    liunian_items.append({
                        "year": yr,
                        "ganzhi": f"流年{yr}",
                        "branch": dy_branch,
                        "stem": "",
                    })
        verify_response.milestones = compute_milestones(
            birth_year=birth_year, day_branch=ds_br, year_branch=ys_br,
            dayun_list=dayun_list, liunian_list=liunian_items,
            yongshen_favor=favor, yongshen_avoid=avoid,
        )
    except Exception as exc:
        logger.debug("[M2.5 milestones] %s", exc)

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
    # M3 新增: interpret.py 解读文本
    # ────────────────────────────────────────────────────────────────────────
    try:
        from services.bazi_engine.interpret import interpret_bazi, InterpretInput
        interp_inp = InterpretInput(
            day_stem=ds_st,
            wuxing_scores=wx_scores,
            yongshen_favor=favor,
            yongshen_avoid=avoid,
            strength_tier=strength_tier,
            geju_name=geju_name,
            shensha_items=shensha_items_raw,
            dizhi_relations=[],   # 地支关系（简化，后续接）
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
        from app.schemas.analysis import LiuNianDetailModel

        # 取近5年流年构建 liunian_detail
        current_year = dt.year
        birth_year   = dt.year
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
                tai_sui_relations=[],
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
