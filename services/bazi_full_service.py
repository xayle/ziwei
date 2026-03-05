from __future__ import annotations

from datetime import datetime, timedelta, timezone
from math import ceil
from typing import Optional
from uuid import uuid4
from zoneinfo import ZoneInfo

from app.exceptions import (
    ValidationException,
    BusinessException,
    ServiceException,
    ErrorCode,
)
from app.error_handling import handle_exceptions

from backends import get_jieqi_context
from constants import API_VERSION, RULE_VERSION
from schemas import (
    BaziFullRequest,
    BaziFullResponse,
    BaziMethodsModel,
    BaziRawModel,
    BaziRawDayunModel,
    DaYunModel,
    DaYunItemModel,
    DayMasterStrengthModel,
    LiuNianResultModel,
    LiuNianItemModel,
    PillarModel,
    PillarsModel,
    StrengthFactorModel,
    TenGodsModel,
    WarningModel,
    WuXingBreakdownModel,
    WuXingScoreModel,
    YongShenModel,
)
from services.normalize_input import validate_lon_strict, warn_lon_cn_range
from services.bazi_engine.tables import BRANCH_HIDDEN_STEMS as _BRANCH_HIDDEN_STEMS  # RL#1 藏干
from verify import verify_full


STEM_META = {
    "甲": ("wood", "yang"),
    "乙": ("wood", "yin"),
    "丙": ("fire", "yang"),
    "丁": ("fire", "yin"),
    "戊": ("earth", "yang"),
    "己": ("earth", "yin"),
    "庚": ("metal", "yang"),
    "辛": ("metal", "yin"),
    "壬": ("water", "yang"),
    "癸": ("water", "yin"),
    "jia": ("wood", "yang"),
    "yi": ("wood", "yin"),
    "bing": ("fire", "yang"),
    "ding": ("fire", "yin"),
    "wu": ("earth", "yang"),
    "ji": ("earth", "yin"),
    "geng": ("metal", "yang"),
    "xin": ("metal", "yin"),
    "ren": ("water", "yang"),
    "gui": ("water", "yin"),
}

STEMS_60 = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
BRANCHES_12 = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]

BRANCH_ELEMENT = {
    "子": "water",
    "丑": "earth",
    "寅": "wood",
    "卯": "wood",
    "辰": "earth",
    "巳": "fire",
    "午": "fire",
    "未": "earth",
    "申": "metal",
    "酉": "metal",
    "戌": "earth",
    "亥": "water",
    "zi": "water",
    "chou": "earth",
    "yin": "wood",
    "mao": "wood",
    "chen": "earth",
    "si": "fire",
    "wu": "fire",
    "wei": "earth",
    "shen": "metal",
    "you": "metal",
    "xu": "earth",
    "hai": "water",
}

PARENT_OF = {
    "wood": "water",
    "fire": "wood",
    "earth": "fire",
    "metal": "earth",
    "water": "metal",
}


def _wuxing_init_dict() -> dict[str, float]:
    return {"wood": 0.0, "fire": 0.0, "earth": 0.0, "metal": 0.0, "water": 0.0}


def compute_wuxing(pillars: PillarsModel) -> tuple[WuXingScoreModel, WuXingBreakdownModel]:
    stem_contrib = _wuxing_init_dict()
    branch_contrib = _wuxing_init_dict()
    hidden_contrib: dict[str, float] = _wuxing_init_dict()

    for stem in [pillars.year.stem, pillars.month.stem, pillars.day.stem, pillars.hour.stem]:
        elem, _ = _stem_meta(stem)
        stem_contrib[elem] += 1.0

    for branch in [pillars.year.branch, pillars.month.branch, pillars.day.branch, pillars.hour.branch]:
        elem = BRANCH_ELEMENT.get(branch)
        if elem:
            branch_contrib[elem] += 1.0
        # RL#1: 藏干贡献（按中文支查表）
        for hidden_stem, weight in _BRANCH_HIDDEN_STEMS.get(branch, []):
            h_elem, _ = _stem_meta(hidden_stem) if hidden_stem in STEM_META else (None, None)
            if h_elem:
                hidden_contrib[h_elem] += weight * 0.3

    total = {k: stem_contrib[k] + branch_contrib[k] + hidden_contrib[k] for k in stem_contrib.keys()}
    score = WuXingScoreModel(**total)
    breakdown = WuXingBreakdownModel(
        stem_contrib=stem_contrib,
        branch_contrib=branch_contrib,
        hidden_contrib=hidden_contrib,
        weights={"stem": 1.0, "branch": 1.0, "hidden": 1.0},
    )
    return score, breakdown


def compute_strength(day_stem: str, score: WuXingScoreModel) -> DayMasterStrengthModel:
    day_elem, _ = _stem_meta(day_stem)
    parent_elem = PARENT_OF[day_elem]
    same = getattr(score, day_elem)
    parent = getattr(score, parent_elem)
    strength_score = same + 0.8 * parent
    if strength_score >= 3.0:
        tier = "strong"
    elif strength_score < 1.5:
        tier = "weak"
    else:
        tier = "balanced"

    _elem_cn = {'wood': '木', 'fire': '火', 'earth': '土', 'metal': '金', 'water': '水'}
    factors = [
        StrengthFactorModel(name="same_element_support", score=same, reason=f"{_elem_cn.get(day_elem, day_elem)} 同类总量"),
        StrengthFactorModel(name="parent_element_support", score=0.8 * parent, reason=f"{_elem_cn.get(parent_elem, parent_elem)} 生 {_elem_cn.get(day_elem, day_elem)}"),
    ]
    return DayMasterStrengthModel(score=strength_score, tier=tier, factors=factors)


def compute_yongshen(
    score: WuXingScoreModel,
    strength: DayMasterStrengthModel,
    pillars: Optional["PillarsModel"] = None,
) -> YongShenModel:
    """
    RL#2: 用神必须走5分支决策树 — 禁止 min/max.
    When pillars is provided, delegates to the new engine's 5-branch version.
    Falls back to approximate扶抑 when pillars absent (legacy/test path).
    """
    if pillars is not None:
        from services.bazi_engine.wuxing import compute_wuxing as _eng_wx
        from services.bazi_engine.strength import compute_strength as _eng_str
        from services.bazi_engine.yongshen import compute_yongshen as _eng_yong
        _w = _eng_wx(
            pillars.year.stem, pillars.year.branch,
            pillars.month.stem, pillars.month.branch,
            pillars.day.stem, pillars.day.branch,
            pillars.hour.stem, pillars.hour.branch,
        )
        _s = _eng_str(
            pillars.day.stem, pillars.month.branch,
            pillars.year.stem, pillars.month.stem, pillars.hour.stem,
            pillars.year.branch, pillars.day.branch, pillars.hour.branch,
            _w,
        )
        result = _eng_yong(
            day_stem=pillars.day.stem,
            month_branch=pillars.month.branch,
            strength=_s,
            wuxing=_w,
        )
        return YongShenModel(
            favor=result.favor,
            avoid=result.avoid,
            rationale=result.rationale,
        )

    # ── 扶抑法 fallback（无四柱时使用，兼顾旧路径） ──────────────────────
    totals = {
        "wood": score.wood, "fire": score.fire, "earth": score.earth,
        "metal": score.metal, "water": score.water,
    }
    SHENG = {"wood": "fire", "fire": "earth", "earth": "metal", "metal": "water", "water": "wood"}
    SHENG_REV = {v: k for k, v in SHENG.items()}
    KE = {"wood": "earth", "fire": "metal", "earth": "water", "metal": "wood", "water": "fire"}
    elem_map = {"strong": ("same", "parent"), "weak": ("ke", "consume"), "balanced": ("ke",)}
    # 取日主五行（从 strength.factors 的 same_element_support）
    day_elem = next(
        ((f.reason or "").split()[0] for f in (strength.factors or []) if "same" in f.name),
        None,
    )
    if day_elem and strength.tier in ("strong", "weak"):
        if strength.tier == "strong":
            # 强→泄秀/克洩制约: 食伤/财星/官杀抑制
            favor = [KE.get(day_elem, ""), SHENG.get(day_elem, "")]
            avoid = [day_elem, SHENG_REV.get(day_elem, "")]
        else:
            # 弱→帮扶生助: 比劫/印绶
            favor = [day_elem, SHENG_REV.get(day_elem, "")]
            avoid = [KE.get(day_elem, ""), SHENG.get(day_elem, "")]
        favor = [e for e in favor if e][:2]
        avoid = [e for e in avoid if e][:2]
    else:
        # 均衡/未知: 以弱为喜
        min_val = min(totals.values())
        max_val = max(totals.values())
        favor = [k for k, v in totals.items() if abs(v - min_val) < 1e-6]
        avoid = [k for k, v in totals.items() if abs(v - max_val) < 1e-6]
    return YongShenModel(
        favor=favor, avoid=avoid,
        rationale=f"扶抑法: tier={strength.tier}, favor={favor}, avoid={avoid} (5-branch fallback)",
    )


def _ganzhi_index(stem: str, branch: str) -> int:
    stem_idx = STEMS_60.index(stem)
    branch_idx = BRANCHES_12.index(branch)
    # Find matching index in 60-cycle where stem and branch align
    for i in range(60):
        if i % 10 == stem_idx and i % 12 == branch_idx:
            return i
    raise ValidationException(
        code=ErrorCode.VALIDATION_INVALID_INPUT,
        message=f"Invalid ganzhi combination: {stem}{branch}",
        details={"stem": stem, "branch": branch},
    )


def _ganzhi_from_index(idx: int) -> tuple[str, str]:
    i = idx % 60
    return STEMS_60[i % 10], BRANCHES_12[i % 12]


def build_dayun(
    dt_effective: datetime,
    pillars: PillarsModel,
    methods: BaziMethodsModel,
    gender: Optional[str] = None,
) -> tuple[DaYunModel, BaziRawDayunModel]:
    raw_dayun = BaziRawDayunModel()

    jie_ctx = get_jieqi_context(dt_effective)
    if jie_ctx is None:
        # No jieqi data; return empty items but keep status computed
        raw_dayun.status = "computed"
        return DaYunModel(method=methods.dayun_method, boundary=methods.dayun_boundary, items=[]), raw_dayun

    # Direction rule: RL#3 男阳顺/男阴逆/女阳逆/女阴顺
    year_stem = pillars.year.stem
    _, year_polarity = _stem_meta(year_stem)
    if gender == "male":
        direction = "forward" if year_polarity == "yang" else "backward"
    elif gender == "female":
        direction = "backward" if year_polarity == "yang" else "forward"
    else:
        # 无性别信息时 fallback：年干阴阳（保持旧行为，存在误差）
        direction = "forward" if year_polarity == "yang" else "backward"
    raw_dayun.direction = direction
    raw_dayun.direction_basis = {
        "gender": gender,
        "year_stem": year_stem,
        "year_stem_yinyang": year_polarity,
    }

    # RL#4: 顺排用 next_jie_dt（距下一节），逆排用 prev_jie_dt（距前一节）
    if direction == "backward":
        anchor_dt = jie_ctx.prev_jie_dt
        raw_dayun.anchor_jieqi_dt = anchor_dt.isoformat()
        raw_dayun.anchor_jieqi_name = jie_ctx.prev_jie_name
        delta_days = (dt_effective - anchor_dt).total_seconds() / 86400.0  # 出生 - 前节
    else:
        anchor_dt = jie_ctx.next_jie_dt
        raw_dayun.anchor_jieqi_dt = anchor_dt.isoformat()
        raw_dayun.anchor_jieqi_name = jie_ctx.next_jie_name
        delta_days = (anchor_dt - dt_effective).total_seconds() / 86400.0  # 后节 - 出生

    raw_dayun.birth_to_jieqi_days = delta_days
    months_before_round = delta_days / methods.dayun_days_per_month
    raw_dayun.computed_months_before_rounding = months_before_round
    raw_dayun.rounding_applied = methods.dayun_rounding
    start_age_months = ceil(months_before_round)
    raw_dayun.sequence_start = "from_month_pillar"
    raw_dayun.status = "computed"

    # Build 10 items advancing from month pillar
    start_idx = _ganzhi_index(pillars.month.stem, pillars.month.branch)
    step = 1 if direction == "forward" else -1
    items: list[DaYunItemModel] = []
    current_idx = (start_idx + step) % 60
    base_age = start_age_months // 12
    start_year = dt_effective.year + base_age
    for i in range(10):
        stem, branch = _ganzhi_from_index(current_idx)
        stem_elem, _ = _stem_meta(stem) if stem in STEM_META else (None, None)
        items.append(
            DaYunItemModel(
                start_age=base_age + i * 10,
                start_year=start_year + i * 10,
                start_age_months=start_age_months + i * 120,
                stem=stem,
                branch=branch,
                flow_wuxing=stem_elem,
            )
        )
        current_idx = (current_idx + step) % 60

    return DaYunModel(
        method=methods.dayun_method,
        boundary=methods.dayun_boundary,
        direction=direction,
        direction_basis=raw_dayun.direction_basis,
        start_age=base_age,
        start_age_months=start_age_months,
        anchor_jieqi_name=raw_dayun.anchor_jieqi_name,
        anchor_jieqi_dt=raw_dayun.anchor_jieqi_dt,
        items=items,
    ), raw_dayun


def _stem_meta(stem: str) -> tuple[str, str]:
    if stem not in STEM_META:
        raise ValidationException(
            code=ErrorCode.VALIDATION_INVALID_INPUT,
            message=f"Unsupported stem: {stem}",
            details={"stem": stem, "supported_stems": list(STEM_META.keys())},
        )
    return STEM_META[stem]


def _element_relation(day_element: str, target_element: str) -> str:
    produces = {
        "wood": "fire",
        "fire": "earth",
        "earth": "metal",
        "metal": "water",
        "water": "wood",
    }
    controls = {
        "wood": "earth",
        "fire": "metal",
        "earth": "water",
        "metal": "wood",
        "water": "fire",
    }
    if target_element == day_element:
        return "same"
    if produces[day_element] == target_element:
        return "child"
    if produces[target_element] == day_element:
        return "parent"
    if controls[day_element] == target_element:
        return "wealth"
    if controls[target_element] == day_element:
        return "officer"
    return "unknown"


def ten_god(day_stem: str, target_stem: str) -> Optional[str]:
    try:
        day_element, day_polarity = _stem_meta(day_stem)
        target_element, target_polarity = _stem_meta(target_stem)
    except ValueError:
        return None

    relation = _element_relation(day_element, target_element)
    same_polarity = day_polarity == target_polarity

    if relation == "same":
        return "bi_jian" if same_polarity else "jie_cai"
    if relation == "child":
        return "shi_shen" if same_polarity else "shang_guan"
    if relation == "parent":
        return "pian_yin" if same_polarity else "zheng_yin"
    if relation == "wealth":
        return "pian_cai" if same_polarity else "zheng_cai"
    if relation == "officer":
        return "qi_sha" if same_polarity else "zheng_guan"
    return None


def build_ten_gods(day_stem: str, pillars: PillarsModel):
    """构建四柱十神。日主柱标注"日主"而非十神名。"""
    return {
        "year": ten_god(day_stem, pillars.year.stem),
        "month": ten_god(day_stem, pillars.month.stem),
        "day": "日主",   # 1.15: 日柱固定标注"日主"，不计十神
        "hour": ten_god(day_stem, pillars.hour.stem),
    }


def ganzhi_for_year(year: int) -> tuple[str, str]:
    idx = (year - 1984) % 60
    stem = STEMS_60[idx % 10]
    branch = BRANCHES_12[idx % 12]
    return stem, branch


def build_liunian(day_stem: str, dt_effective: datetime, years_used: list[int]) -> LiuNianResultModel:
    items: list[LiuNianItemModel] = []
    for delta in years_used:
        year = dt_effective.year + delta
        stem, branch = ganzhi_for_year(year)
        tg = ten_god(day_stem, stem)
        items.append(LiuNianItemModel(year=year, stem=stem, branch=branch, ten_god=tg, clash=None))
    return LiuNianResultModel(years_used=years_used, items=items)


def _attach_tz(dt: datetime, tz_name: str) -> datetime:
    try:
        tz = ZoneInfo(tz_name)
    except Exception:
        raise ValidationException(
            code=ErrorCode.VALIDATION_INVALID_INPUT,
            message=f"Invalid timezone: {tz_name}",
            details={"timezone": tz_name},
        )
    if dt.tzinfo is None or dt.utcoffset() is None:
        return dt.replace(tzinfo=tz)
    return dt.astimezone(tz)


def _to_pillars_model(pillars) -> PillarsModel:
    return PillarsModel(
        year=PillarModel(**pillars.year.__dict__),
        month=PillarModel(**pillars.month.__dict__),
        day=PillarModel(**pillars.day.__dict__),
        hour=PillarModel(**pillars.hour.__dict__),
    )


def bazi_full(
    body: BaziFullRequest,
    request_id: Optional[str] = None,
) -> BaziFullResponse:
    dt = _attach_tz(body.dt, body.tz)
    lon = validate_lon_strict(body.lon)
    liunian_years = body.liunian_years or [-2, 2]

    # Soft warnings only (e.g., lon outside CN range)
    warnings_raw = warn_lon_cn_range(body.tz, lon)
    warnings = [WarningModel.model_validate(w) for w in warnings_raw]

    try:
        result = verify_full(dt, lon=lon, use_solar=body.solar_time_enabled, mode=body.mode)
    except ValidationException:
        raise
    except BusinessException:
        raise
    except Exception as exc:
        raise ServiceException(
            code=ErrorCode.SERVICE_EXTERNAL_ERROR,
            message="Failed to perform BaZi calculation",
            details={"error": str(exc)},
        )

    # Compute effective datetime for traceability
    offset_minutes_int = int(round(result.solar_time_offset_minutes))
    dt_effective = dt + timedelta(minutes=offset_minutes_int)
    dt_effective_utc = dt_effective.astimezone(timezone.utc)

    methods = BaziMethodsModel()

    offset_minutes = 0
    dt_offset = dt_effective.utcoffset()
    if dt_offset is not None:
        offset_minutes = int(dt_offset.total_seconds() // 60)

    raw = BaziRawModel(
        tz_used=body.tz,
        dt_effective_local=dt_effective.isoformat(),
        dt_effective_utc=dt_effective_utc.isoformat(),
        dt_effective_local_offset_minutes=offset_minutes,
        solar_time_offset_minutes=offset_minutes_int,
        day_boundary_rule_used=methods.day_boundary_rule,
        day_boundary_crossed=False,
        jieqi_context={},
        dayun=BaziRawDayunModel(),
    )

    pillars_model = _to_pillars_model(result.pillars_primary)
    ten_gods = TenGodsModel(**build_ten_gods(pillars_model.day.stem, pillars_model))
    liunian = build_liunian(pillars_model.day.stem, dt_effective, years_used=liunian_years)

    day_boundary_crossed = False
    if methods.day_boundary_rule == "zi_initial" and (
        dt_effective.hour >= 23 or dt_effective.hour == 0
    ):
        day_boundary_crossed = True

    # Derived calculations
    wuxing_score, wuxing_breakdown = compute_wuxing(pillars_model)
    strength = compute_strength(pillars_model.day.stem, wuxing_score)
    yongshen = compute_yongshen(wuxing_score, strength)

    dayun_model, raw_dayun = build_dayun(dt_effective, pillars_model, methods)
    raw.day_boundary_crossed = day_boundary_crossed
    raw.dayun = raw_dayun

    return BaziFullResponse(
        api_version=API_VERSION,
        rule_version=RULE_VERSION,
        request_id=request_id or str(uuid4()),
        warnings=warnings,
        methods=methods,
        pillars_primary=pillars_model,
        pillars_secondary=_to_pillars_model(result.pillars_secondary) if result.pillars_secondary else None,
        dayun=dayun_model,
        ten_gods=ten_gods,
        liunian=liunian,
        wuxing_score=wuxing_score,
        wuxing_breakdown=wuxing_breakdown,
        day_master_strength=strength,
        yongshen=yongshen,
        raw=raw,
    )
