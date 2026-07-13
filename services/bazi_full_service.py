from __future__ import annotations

from datetime import UTC, datetime, timedelta
import logging
from math import ceil
from uuid import uuid4
from zoneinfo import ZoneInfo

from app.exceptions import (
    BusinessException,
    ErrorCode,
    ServiceException,
    ValidationException,
)
from app.schemas.bazi import (
    AdjustmentSummaryModel,
    BaziFullRequest,
    BaziFullResponse,
    BaziMethodsModel,
    BaziRawDayunModel,
    BaziRawModel,
    BaziStructuralSummaryModel,
    ConfidenceSummaryModel,
    DayMasterStrengthModel,
    DaYunItemModel,
    DaYunModel,
    EvidenceItemModel,
    HiddenStemDetailModel,
    LiuNianItemModel,
    LiuNianResultModel,
    PillarDetailModel,
    PillarModel,
    PillarShenshaDetailModel,
    PillarsModel,
    RelationItemModel,
    StrengthFactorModel,
    TimelinePointModel,
    WarningModel,
    WuXingBreakdownModel,
    WuXingScoreModel,
    YongShenModel,
)
from backends import get_jieqi_context
from constants import API_VERSION, RULE_VERSION
from services.bazi_provenance import build_bazi_provenance, day_boundary_crossed

logger = logging.getLogger(__name__)
from services.bazi_engine.liunian import _liunian_day_relation
from services.bazi_engine.shensha import SHENSHA_META as _SHENSHA_META
from services.bazi_engine.shensha import compute_flow_shensha_items
from services.bazi_engine.tables import BRANCH_HIDDEN_STEMS as _BRANCH_HIDDEN_STEMS  # RL#1 藏干
from services.bazi_engine.tables import MONTH_CLIMATE_RULES as _MONTH_CLIMATE_RULES
from services.bazi_engine.tables import NAYIN as _NAYIN_TABLE
from services.bazi_engine.tables import get_kongwang
from services.bazi_rule_engine import match_rules
from services.normalize_input import normalize_birth_datetime, validate_lon_strict, warn_lon_cn_range
from verify import verify_full as verify_full

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


def _shensha_meta_value(name: str, field: str) -> str:
    return str(_SHENSHA_META.get(name, {}).get(field) or "")


def _text_or_empty(value: object) -> str:
    return str(value).strip() if value else ""


STEMS_60 = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
BRANCHES_12 = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
STAGE_NAMES = ["长生", "沐浴", "冠带", "临官", "帝旺", "衰", "病", "死", "墓", "绝", "胎", "养"]
DAYUN_STAGE_START = {
    "甲": "亥",
    "乙": "午",
    "丙": "寅",
    "丁": "酉",
    "戊": "寅",
    "己": "酉",
    "庚": "巳",
    "辛": "子",
    "壬": "申",
    "癸": "卯",
}
DAYUN_STAGE_START_YIN = {
    "甲": "亥",
    "乙": "午",
    "丙": "寅",
    "丁": "酉",
    "戊": "寅",
    "己": "酉",
    "庚": "巳",
    "辛": "子",
    "壬": "申",
    "癸": "卯",
}


def _normalize_relation_type(raw_type: str) -> str:
    aliases = {
        "六合": "合",
        "六冲": "冲",
        "相冲": "冲",
        "相合": "合",
        "相害": "害",
        "相破": "破",
        "相刑": "刑",
        "三合半合": "合",
        "半合": "合",
        "三合": "合",
        "空亡": "空亡",
        "干支互动": "干支互动",
    }
    normalized = aliases.get(raw_type, raw_type)
    return normalized if normalized in {"刑", "冲", "合", "害", "破", "空亡", "干支互动"} else "干支互动"


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


def _branch_main_contrib(pillars: PillarsModel) -> dict[str, float]:
    """地支本气五行计数（用于 WuXingBreakdownModel.branch_contrib）。"""
    from services.bazi_engine.tables import BRANCH_HIDDEN_STEMS, STEM_ELEMENT

    contrib = _wuxing_init_dict()
    for branch in (pillars.year.branch, pillars.month.branch, pillars.day.branch, pillars.hour.branch):
        hidden = BRANCH_HIDDEN_STEMS.get(branch, [])
        if not hidden:
            continue
        main_stem, _ = hidden[0]
        elem = STEM_ELEMENT.get(main_stem, (None, None))[0]
        if elem:
            contrib[elem] += 1.0
    return contrib


def compute_core_metrics(
    pillars: PillarsModel,
    geju_name: str = "",
) -> tuple[WuXingScoreModel, WuXingBreakdownModel, DayMasterStrengthModel, YongShenModel]:
    """统一五行 / 强弱 / 用神计算（权威路径：services/bazi_engine/*）。"""
    from services.bazi_engine.strength import compute_strength as eng_strength
    from services.bazi_engine.wuxing import compute_wuxing as eng_wuxing
    from services.bazi_engine.yongshen import compute_yongshen as eng_yongshen

    wx = eng_wuxing(
        pillars.year.stem,
        pillars.year.branch,
        pillars.month.stem,
        pillars.month.branch,
        pillars.day.stem,
        pillars.day.branch,
        pillars.hour.stem,
        pillars.hour.branch,
    )
    st = eng_strength(
        pillars.day.stem,
        pillars.month.branch,
        pillars.year.stem,
        pillars.month.stem,
        pillars.hour.stem,
        pillars.year.branch,
        pillars.day.branch,
        pillars.hour.branch,
        wx,
    )
    ys = eng_yongshen(
        day_stem=pillars.day.stem,
        month_branch=pillars.month.branch,
        strength=st,
        wuxing=wx,
        geju_name=geju_name,
    )

    wuxing_score = WuXingScoreModel(**wx.scores_weighted)
    wuxing_breakdown = WuXingBreakdownModel(
        stem_contrib=wx.stem_contrib,
        branch_contrib=_branch_main_contrib(pillars),
        hidden_contrib=wx.branch_hidden_contrib,
        weights={"stem": 1.0, "branch": 1.0, "hidden": 0.3},
    )
    _factor_models = [
        StrengthFactorModel(
            name=f.name,
            score=f.score,
            weight=f.weight,
            weighted_score=f.weighted_score,
            reason=f.reason,
        )
        for f in st.factors
    ]
    strength = DayMasterStrengthModel(
        score=st.score,
        tier=st.tier,
        factors=_factor_models,
        strength_factors=_factor_models,
    )
    _WX2CN = {"wood": "木", "fire": "火", "earth": "土", "metal": "金", "water": "水"}
    rationale = ys.rationale
    for en, cn in _WX2CN.items():
        rationale = rationale.replace(en, cn)
    yongshen = YongShenModel(favor=ys.favor, avoid=ys.avoid, rationale=rationale)
    return wuxing_score, wuxing_breakdown, strength, yongshen


def compute_yongshen(
    score: WuXingScoreModel,
    strength: DayMasterStrengthModel,
    pillars: PillarsModel | None = None,
    geju_name: str = "",
) -> YongShenModel:
    """
    RL#2: 用神必须走5分支决策树 — 禁止 min/max.
    When pillars is provided, delegates to compute_core_metrics.
    Falls back to approximate扶抑 when pillars absent (legacy/test path).
    """
    if pillars is not None:
        _, _, _, yongshen = compute_core_metrics(pillars, geju_name=geju_name)
        return yongshen

    # ── 扶抑法 fallback（无四柱时使用，兼顾旧路径） ──────────────────────
    totals = {
        "wood": score.wood,
        "fire": score.fire,
        "earth": score.earth,
        "metal": score.metal,
        "water": score.water,
    }
    SHENG = {"wood": "fire", "fire": "earth", "earth": "metal", "metal": "water", "water": "wood"}
    SHENG_REV = {v: k for k, v in SHENG.items()}
    KE = {"wood": "earth", "fire": "metal", "earth": "water", "metal": "wood", "water": "fire"}
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
        favor=favor,
        avoid=avoid,
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
    gender: str | None = None,
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
        kongwang = list(get_kongwang(stem, branch))
        dy_self_seat, dy_self_seat_source = _pillar_self_seat(stem, branch)
        items.append(
            DaYunItemModel(
                start_age=base_age + i * 10,
                start_year=start_year + i * 10,
                start_age_months=start_age_months + i * 120,
                stem=stem,
                branch=branch,
                ten_god=ten_god(pillars.day.stem, stem),
                hidden_stems=_build_hidden_detail(branch, pillars.day.stem),
                xingyun=_pillar_xingyun(pillars.day.stem, branch),
                self_seat=dy_self_seat,
                self_seat_source=dy_self_seat_source,
                kongwang=kongwang,
                kongwang_source="services.bazi_engine.tables.get_kongwang",
                kongwang_hit=branch in kongwang,
                nayin=_NAYIN_TABLE.get(f"{stem}{branch}"),
                shensha=_build_flow_shensha_detail_items(
                    flow_label="dayun",
                    flow_stem=stem,
                    flow_branch=branch,
                    day_stem=pillars.day.stem,
                    day_branch=pillars.day.branch,
                    month_stem=pillars.month.stem,
                    month_branch=pillars.month.branch,
                    hour_stem=pillars.hour.stem,
                    hour_branch=pillars.hour.branch,
                ),
                wuxing=_element_cn(stem_elem),
                flow_wuxing=stem_elem,
                yin_yang=_stem_meta(stem)[1] if stem in STEM_META else None,
            )
        )
        current_idx = (current_idx + step) % 60

    start_age_days = int(round(max(delta_days, 0.0)))
    transition_hint = (
        f"出生距{raw_dayun.anchor_jieqi_name}约{start_age_days}天，"
        f"折合{start_age_months}个月起运；换运前后运势多有起伏，宜稳守过渡、忌重大决断。"
    )

    from datetime import date as _date

    from services.bazi_engine.dayun import compute_next_dayun_transition

    _next_trans = compute_next_dayun_transition(dt_effective.date(), items, _date.today())

    return DaYunModel(
        method=methods.dayun_method,
        boundary=methods.dayun_boundary,
        direction=direction,
        direction_basis=raw_dayun.direction_basis,
        start_age=base_age,
        start_age_months=start_age_months,
        start_age_days=start_age_days,
        transition_hint=transition_hint,
        days_to_next_transition=_next_trans.get("days_to_next_transition"),
        next_transition_age=_next_trans.get("next_transition_age"),
        next_transition_ganzhi=_next_trans.get("next_transition_ganzhi"),
        next_transition_hint=_next_trans.get("next_transition_hint"),
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


def _element_cn(element: str | None) -> str | None:
    return {"wood": "木", "fire": "火", "earth": "土", "metal": "金", "water": "水"}.get(element or "", None)


def _stem_element(stem: str | None) -> tuple[str | None, str | None]:
    if not stem:
        return None, None
    try:
        elem, yin_yang = _stem_meta(stem)
    except Exception:
        return None, None
    return _element_cn(elem), ("阳" if yin_yang == "yang" else "阴")


def _pillar_xingyun(day_stem: str, branch: str | None) -> str | None:
    if not day_stem or not branch:
        return None
    start_branch = DAYUN_STAGE_START.get(day_stem)
    if not start_branch:
        return None
    try:
        start_idx = BRANCHES_12.index(start_branch)
        branch_idx = BRANCHES_12.index(branch)
    except ValueError:
        return None
    is_yang = day_stem in {"甲", "丙", "戊", "庚", "壬"}
    offset = (branch_idx - start_idx + 12) % 12 if is_yang else (start_idx - branch_idx + 12) % 12
    return STAGE_NAMES[offset] if 0 <= offset < len(STAGE_NAMES) else None


def _pillar_self_seat(stem: str | None, branch: str | None) -> tuple[str | None, str | None]:
    """自坐：本柱天干 × 本柱地支 → 十二长生名（B-02）。"""
    if not stem or not branch:
        return None, None
    seat = _pillar_xingyun(stem, branch)
    if seat:
        return seat, f"{stem}坐{branch}十二长生"
    return None, None


def _build_hidden_detail(branch: str | None, day_stem: str | None) -> list[HiddenStemDetailModel]:
    if not branch:
        return []
    details: list[HiddenStemDetailModel] = []
    for hidden_stem, weight in _BRANCH_HIDDEN_STEMS.get(branch, []):
        elem_cn, _ = _stem_element(hidden_stem)
        ten_god_value = ten_god(day_stem, hidden_stem) if day_stem else None
        details.append(
            HiddenStemDetailModel(
                stem=hidden_stem,
                weight=weight,
                element=elem_cn,
                ten_god=ten_god_value,
                source="《三命通会》支藏干",
            )
        )
    return details


_PILLAR_LABEL_KEYS = {
    "年柱": "year",
    "月柱": "month",
    "日柱": "day",
    "时柱": "hour",
}


def _default_liunian_years(birth_year: int) -> list[int]:
    """Default offsets from birth year: ±2 plus offset to current calendar year."""
    from datetime import date

    today_year = date.today().year
    deltas = set(range(-2, 3))
    deltas.add(today_year - birth_year)
    return sorted(deltas)


def _shensha_for_pillar(label: str, shensha_items: list[dict]) -> list[PillarShenshaDetailModel]:
    pillar_key = _PILLAR_LABEL_KEYS.get(label, label.replace("柱", ""))
    allowed = {pillar_key, label, label.replace("柱", "")}
    seen: set[str] = set()
    models: list[PillarShenshaDetailModel] = []
    for item in shensha_items:
        item_pillar = str(item.get("pillar") or "")
        if item_pillar not in allowed:
            continue
        name = str(item.get("name") or "")
        if not name or name in seen:
            continue
        seen.add(name)
        models.append(
            PillarShenshaDetailModel(
                name=name,
                priority=str(item.get("priority") or _shensha_meta_value(name, "priority")),
                polarity=str(item.get("polarity") or _SHENSHA_META.get(name, {}).get("polarity", "unknown")),
                pillar=item_pillar,
                topic=str(item.get("topic") or _shensha_meta_value(name, "topic")),
                note=str(item.get("note") or _shensha_meta_value(name, "note")),
                classic=str(item.get("classic") or _SHENSHA_META.get(name, {}).get("classic", "")) or None,
                source=str(
                    item.get("classic") or _SHENSHA_META.get(name, {}).get("classic", "services.bazi_engine.shensha")
                ),
            )
        )
    return models


def _build_pillar_detail(
    label: str,
    stem: str | None,
    branch: str | None,
    day_stem: str,
    kongwang: list[str],
    shensha_items: list[dict],
) -> PillarDetailModel:
    element_cn, yin_yang = _stem_element(stem)
    hidden_stems = _build_hidden_detail(branch, day_stem)
    ten_god_value = ten_god(day_stem, stem) if stem else None
    if label == "日柱":
        ten_god_value = "日主"
    shensha = _shensha_for_pillar(label, shensha_items)
    pillar_kongwang = list(get_kongwang(stem, branch)) if stem and branch else list(kongwang)
    if pillar_kongwang == ["未知", "未知"]:
        pillar_kongwang = []
    kongwang_hit = bool(branch and branch in pillar_kongwang)
    kongwang_source = "services.bazi_engine.tables.get_kongwang" if stem and branch else ""
    self_seat, self_seat_source = _pillar_self_seat(stem, branch)
    return PillarDetailModel(
        label=label,
        stem=stem,
        branch=branch,
        ganzhi=f"{stem or ''}{branch or ''}" if stem or branch else None,
        ten_god=ten_god_value,
        hidden_stems=hidden_stems,
        xingyun=_pillar_xingyun(day_stem, branch),
        self_seat=self_seat,
        self_seat_source=self_seat_source,
        kongwang=list(pillar_kongwang),
        kongwang_source=kongwang_source,
        kongwang_hit=kongwang_hit,
        nayin=_NAYIN_TABLE.get(f"{stem or ''}{branch or ''}") if stem and branch else None,
        shensha=shensha,
        wuxing=element_cn,
        yin_yang=yin_yang,
    )


def _build_flow_shensha_detail_items(
    flow_label: str,
    flow_stem: str,
    flow_branch: str,
    day_stem: str,
    day_branch: str,
    month_stem: str | None = None,
    month_branch: str | None = None,
    hour_stem: str | None = None,
    hour_branch: str | None = None,
) -> list[PillarShenshaDetailModel]:
    raw_items = compute_flow_shensha_items(
        flow_label=flow_label,
        flow_stem=flow_stem,
        flow_branch=flow_branch,
        day_stem=day_stem,
        day_branch=day_branch,
        month_stem=month_stem,
        month_branch=month_branch,
        hour_stem=hour_stem,
        hour_branch=hour_branch,
    )
    return [
        PillarShenshaDetailModel(
            name=str(item.get("name") or ""),
            priority=str(item.get("priority") or _shensha_meta_value(str(item.get("name") or ""), "priority")),
            polarity=str(
                item.get("polarity") or _SHENSHA_META.get(str(item.get("name") or ""), {}).get("polarity", "unknown")
            ),
            pillar=str(item.get("pillar") or flow_label),
            topic=str(item.get("topic") or _shensha_meta_value(str(item.get("name") or ""), "topic")),
            note=str(item.get("note") or _shensha_meta_value(str(item.get("name") or ""), "note")),
            classic=str(item.get("classic") or _SHENSHA_META.get(str(item.get("name") or ""), {}).get("classic", ""))
            or None,
            source=str(
                item.get("classic")
                or _SHENSHA_META.get(str(item.get("name") or ""), {}).get("classic", "services.bazi_engine.shensha")
            ),
        )
        for item in raw_items
    ]


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


def ten_god(day_stem: str, target_stem: str) -> str | None:
    """返回中文十神名称（比肩/劫财/食神/伤官/正财/偏财/正官/七杀/正印/偏印）。"""
    try:
        day_element, day_polarity = _stem_meta(day_stem)
        target_element, target_polarity = _stem_meta(target_stem)
    except ValueError:
        return None

    relation = _element_relation(day_element, target_element)
    same_polarity = day_polarity == target_polarity

    if relation == "same":
        return "比肩" if same_polarity else "劫财"
    if relation == "child":
        return "食神" if same_polarity else "伤官"
    if relation == "parent":
        return "偏印" if same_polarity else "正印"
    if relation == "wealth":
        return "偏财" if same_polarity else "正财"
    if relation == "officer":
        return "七杀" if same_polarity else "正官"
    return None


def build_ten_gods(day_stem: str, pillars: PillarsModel):
    """构建四柱十神。日主柱标注"日主"而非十神名。"""
    return {
        "year": ten_god(day_stem, pillars.year.stem),
        "month": ten_god(day_stem, pillars.month.stem),
        "day": "日主",  # 1.15: 日柱固定标注"日主"，不计十神
        "hour": ten_god(day_stem, pillars.hour.stem),
    }


def ganzhi_for_year(year: int) -> tuple[str, str]:
    idx = (year - 1984) % 60
    stem = STEMS_60[idx % 10]
    branch = BRANCHES_12[idx % 12]
    return stem, branch


def build_liunian(
    pillars: PillarsModel,
    dt_effective: datetime,
    years_used: list[int],
) -> LiuNianResultModel:
    items: list[LiuNianItemModel] = []
    day_stem = pillars.day.stem
    for delta in years_used:
        year = dt_effective.year + delta
        stem, branch = ganzhi_for_year(year)
        tg = ten_god(day_stem, stem)
        kongwang = list(get_kongwang(stem, branch))
        ln_self_seat, ln_self_seat_source = _pillar_self_seat(stem, branch)
        items.append(
            LiuNianItemModel(
                year=year,
                stem=stem,
                branch=branch,
                ten_god=tg,
                hidden_stems=_build_hidden_detail(branch, day_stem),
                xingyun=_pillar_xingyun(day_stem, branch),
                self_seat=ln_self_seat,
                self_seat_source=ln_self_seat_source,
                kongwang=kongwang,
                kongwang_source="services.bazi_engine.tables.get_kongwang",
                kongwang_hit=branch in kongwang,
                nayin=_NAYIN_TABLE.get(f"{stem}{branch}"),
                shensha=_build_flow_shensha_detail_items(
                    flow_label="liunian",
                    flow_stem=stem,
                    flow_branch=branch,
                    day_stem=pillars.day.stem,
                    day_branch=pillars.day.branch,
                    month_stem=pillars.month.stem,
                    month_branch=pillars.month.branch,
                    hour_stem=pillars.hour.stem,
                    hour_branch=pillars.hour.branch,
                ),
                wuxing=_element_cn(_stem_meta(stem)[0]),
                yin_yang=_stem_meta(stem)[1] == "yang" and "阳" or "阴",
                clash=_text_or_empty(_liunian_day_relation(branch, pillars.day.branch)),
            )
        )
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


def build_liuri_liushi_enrichment(
    *,
    verify_response,
    birth_dt: datetime,
    target_date: datetime.date,
    target_hour: int,
) -> tuple[dict, dict | None]:
    """
    Build liuri_liushi payload and optional dayun transition patch.

    Returns (liuri_liushi model_dump, dayun transition dict or None).
    """
    from app.schemas.bazi import LiuriLiushiModel
    from services.bazi_engine.dayun import compute_next_dayun_transition, virtual_age
    from services.bazi_engine.liuri import get_liuri_liushi

    _birth_date = birth_dt.date()

    _dayun_tg: str | None = None
    _dayun_gz: str | None = None
    if verify_response.dayun and verify_response.dayun.items:
        _v_age = virtual_age(_birth_date, target_date)
        for _dy in verify_response.dayun.items:
            if _dy.start_age is not None and _dy.start_age <= _v_age < _dy.start_age + 10:
                _dayun_tg = _dy.ten_god
                _dayun_gz = f"{_dy.stem or ''}{_dy.branch or ''}"
                break

    _ln_tg: str | None = None
    _ln_gz: str | None = None
    if verify_response.liunian and verify_response.liunian.items:
        for _ln in verify_response.liunian.items:
            if _ln.year == target_date.year:
                _ln_tg = _ln.ten_god
                _ln_gz = f"{_ln.stem or ''}{_ln.branch or ''}"
                break

    if _ln_tg is None and verify_response.pillars_primary and verify_response.pillars_primary.day:
        from services.bazi_engine.liunian import compute_liunian as _compute_liunian_for_target

        _day = verify_response.pillars_primary.day
        _target_yr = target_date.year
        _ln_rows = _compute_liunian_for_target(
            day_stem=_day.stem,
            day_branch=_day.branch,
            start_year=_target_yr,
            end_year=_target_yr,
        )
        if _ln_rows:
            _ln_tg = _ln_rows[0].get("ten_god")
            _ln_gz = f"{_ln_rows[0]['stem']}{_ln_rows[0]['branch']}"

    _favor = list(verify_response.yongshen.favor or []) if verify_response.yongshen else None
    _avoid = list(verify_response.yongshen.avoid or []) if verify_response.yongshen else None
    _geju_broken = bool(getattr(getattr(verify_response, "geju", None), "is_broken", False))

    dayun_patch: dict | None = None
    _trans: dict = {}
    if verify_response.dayun and verify_response.dayun.items:
        _trans = compute_next_dayun_transition(_birth_date, verify_response.dayun.items, target_date)
        dayun_patch = {
            "days_to_next_transition": _trans.get("days_to_next_transition"),
            "next_transition_age": _trans.get("next_transition_age"),
            "next_transition_ganzhi": _trans.get("next_transition_ganzhi"),
            "next_transition_hint": _trans.get("next_transition_hint"),
        }

    _zi_day_rule = getattr(verify_response, "zi_day_rule", None) or "sxtwl"

    _raw_liuri = get_liuri_liushi(
        birth_dt.year,
        birth_dt.month,
        birth_dt.day,
        birth_dt.hour,
        day_stem=verify_response.pillars_primary.day.stem if verify_response.pillars_primary else None,
        target_date=target_date,
        target_hour=target_hour,
        dayun_ten_god=_dayun_tg,
        dayun_ganzhi=_dayun_gz,
        liunian_ten_god=_ln_tg,
        liunian_ganzhi=_ln_gz,
        yongshen_favor=_favor,
        yongshen_avoid=_avoid,
        geju_broken=_geju_broken,
        days_to_next_transition=_trans.get("days_to_next_transition"),
        next_transition_ganzhi=_trans.get("next_transition_ganzhi"),
        next_transition_age=_trans.get("next_transition_age"),
        next_transition_hint=_trans.get("next_transition_hint"),
        zi_day_rule=_zi_day_rule,
    )
    liuri_payload = LiuriLiushiModel(
        date=_raw_liuri["date"],
        day_ganzhi=_raw_liuri["day_ganzhi"],
        day_stem=_raw_liuri["day_stem"],
        day_branch=_raw_liuri["day_branch"],
        hour_ganzhi=_raw_liuri["hour_ganzhi"],
        hour_stem=_raw_liuri["hour_stem"],
        hour_branch=_raw_liuri["hour_branch"],
        hour_branch_idx=_raw_liuri.get("hour_branch_idx", 0),
        hour_label=_raw_liuri.get("hour_label", ""),
        day_ten_god=_raw_liuri.get("day_ten_god"),
        hour_ten_god=_raw_liuri.get("hour_ten_god"),
        method=_raw_liuri.get("method", "ganzhi_day_pillar"),
        missing_fields=_raw_liuri.get("missing_fields", []),
        flow_score=_raw_liuri.get("flow_score"),
        flow_score_dayun=_raw_liuri.get("flow_score_dayun"),
        flow_score_liunian=_raw_liuri.get("flow_score_liunian"),
        flow_score_geju=_raw_liuri.get("flow_score_geju"),
        flow_tone=_raw_liuri.get("flow_tone"),
        transition_hint=_raw_liuri.get("transition_hint"),
        dayun_link=_raw_liuri.get("dayun_link"),
        liunian_link=_raw_liuri.get("liunian_link"),
        current_dayun_ganzhi=_raw_liuri.get("current_dayun_ganzhi"),
        current_liunian_ganzhi=_raw_liuri.get("current_liunian_ganzhi"),
        flow_summary=_raw_liuri.get("flow_summary"),
        warnings=_raw_liuri.get("warnings") or [],
    ).model_dump()

    if dayun_patch and _raw_liuri.get("transition_hint"):
        dayun_patch["next_transition_hint"] = _raw_liuri["transition_hint"]

    return liuri_payload, dayun_patch


def compute_liuri_liushi(
    body,
    request_id: str | None = None,
):
    """Standalone liuri/liushi computation for POST /bazi/liuri-liushi."""
    from datetime import date as _date
    from uuid import uuid4

    from app.schemas.bazi import DayunTransitionModel, LiuriLiushiEndpointResponse, LiuriLiushiModel
    from services.bazi_engine_service import calculate

    dt = _attach_tz(body.dt, body.tz)
    lon = validate_lon_strict(body.lon)
    normalized_birth = normalize_birth_datetime(dt, body.tz, auto_dst=True)
    solar_offset_minutes = 0

    try:
        calc_result = calculate(
            dt=dt,
            lon=lon,
            tz=body.tz,
            use_solar=body.solar_time_enabled,
            mode="single",
            gender=body.gender,
            request_id=request_id or str(uuid4()),
        )
    except ValidationException:
        raise
    except BusinessException:
        raise
    except Exception as exc:
        raise ServiceException(
            code=ErrorCode.SERVICE_EXTERNAL_ERROR,
            message="Failed to perform BaZi calculation for liuri/liushi",
            details={"error": str(exc)},
        )

    verify_response = calc_result.verify_response
    solar_offset_minutes = int(round(float(verify_response.solar_time_offset_minutes or 0.0)))
    dt_effective = normalized_birth.local_dt + timedelta(minutes=solar_offset_minutes)

    _td = body.target_date.date() if body.target_date else _date.today()
    _th = body.target_hour if body.target_hour is not None else dt_effective.hour

    liuri_payload, dayun_patch = build_liuri_liushi_enrichment(
        verify_response=verify_response,
        birth_dt=dt_effective,
        target_date=_td,
        target_hour=_th,
    )

    transition = None
    if body.include_dayun_transition and dayun_patch:
        transition = DayunTransitionModel.model_validate(dayun_patch)

    return LiuriLiushiEndpointResponse(
        request_id=request_id or str(uuid4()),
        liuri_liushi=LiuriLiushiModel.model_validate(liuri_payload),
        dayun_transition=transition,
    )


def patch_verify_liuri(
    response_data: dict,
    verify_response,
    body,
    dt: datetime,
    tz: str,
) -> dict:
    """Optionally attach liuri_liushi + missing_fields to verify response dict."""
    include = getattr(body, "include_liuri", None)
    if include is None:
        include = False
    if not include:
        return response_data

    from datetime import date as _date

    normalized_birth = normalize_birth_datetime(dt, tz, auto_dst=True)
    solar_offset_minutes = int(round(float(getattr(verify_response, "solar_time_offset_minutes", 0.0) or 0.0)))
    dt_effective = normalized_birth.local_dt + timedelta(minutes=solar_offset_minutes)

    _td = body.target_date.date() if getattr(body, "target_date", None) else _date.today()
    _th = body.target_hour if getattr(body, "target_hour", None) is not None else dt_effective.hour

    liuri_payload, dayun_patch = build_liuri_liushi_enrichment(
        verify_response=verify_response,
        birth_dt=dt_effective,
        target_date=_td,
        target_hour=_th,
    )
    response_data["liuri_liushi"] = liuri_payload

    if dayun_patch and response_data.get("dayun"):
        for key, val in dayun_patch.items():
            if val is not None:
                response_data["dayun"][key] = val

    _missing = set(response_data.get("missing_fields") or [])
    _missing.update(liuri_payload.get("missing_fields") or [])
    response_data["missing_fields"] = sorted(_missing)
    return response_data


def bazi_full(
    body: BaziFullRequest,
    request_id: str | None = None,
) -> BaziFullResponse:
    dt = _attach_tz(body.dt, body.tz)
    lon = validate_lon_strict(body.lon)
    liunian_years = body.liunian_years or _default_liunian_years(dt.year)
    normalized_birth = normalize_birth_datetime(dt, body.tz, auto_dst=True)
    warnings_raw = warn_lon_cn_range(body.tz, lon)
    warnings = [WarningModel.model_validate(w) for w in warnings_raw]

    # 先走一次 verify_full 兼容旧测试/旧链路的输入校验与 patch 点。
    # 后续完整分析仍由 calculate() 负责，确保响应继续补齐新字段。
    try:
        verify_full(dt, lon=lon, use_solar=body.solar_time_enabled, mode=body.mode)
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

    from services.bazi_engine_service import calculate

    try:
        calc_result = calculate(
            dt=dt,
            lon=lon,
            tz=body.tz,
            use_solar=body.solar_time_enabled,
            mode=body.mode,
            gender=body.gender,
            request_id=request_id or str(uuid4()),
            extra_warnings=[w.message for w in warnings],
            city_tier=body.city_tier,
            industry=body.industry,
            zi_day_rule=body.zi_day_rule,
        )
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

    verify_response = calc_result.verify_response.model_copy(deep=True)
    methods = BaziMethodsModel(
        day_boundary_rule=body.zi_day_rule,
        zi_day_rule=body.zi_day_rule,
        pillars_layer=calc_result.pillars_layer or "",
    )
    solar_offset_minutes = int(round(float(verify_response.solar_time_offset_minutes or 0.0)))
    dt_effective = normalized_birth.local_dt + timedelta(minutes=solar_offset_minutes)
    dt_effective_utc = dt_effective.astimezone(UTC)

    raw = BaziRawModel(
        tz_used=body.tz,
        dt_effective_local=dt_effective.isoformat(),
        dt_effective_utc=dt_effective_utc.isoformat(),
        dt_effective_local_offset_minutes=int(dt_effective.utcoffset().total_seconds() // 60)
        if dt_effective.utcoffset()
        else 0,
        solar_time_offset_minutes=solar_offset_minutes,
        day_boundary_rule_used=body.zi_day_rule,
        day_boundary_crossed=day_boundary_crossed(body.zi_day_rule, dt_effective.hour),
        jieqi_context={
            "birth_dt_local_normalized": normalized_birth.normalized_birth_dt_local,
            "birth_dt_utc_normalized": normalized_birth.normalized_birth_dt_utc,
            "is_potential_china_dst": normalized_birth.is_potential_china_dst,
            "dst_adjustment_minutes": normalized_birth.dst_adjustment_minutes,
            "dst_label": normalized_birth.dst_label,
            "time_risk_label": normalized_birth.time_risk_label,
            "time_risk_hint": normalized_birth.time_risk_hint,
        },
        dayun=BaziRawDayunModel(
            birth_to_jieqi_days=getattr(verify_response.dayun, "start_age_months", None),
            computed_months_before_rounding=None,
            rounding_applied=methods.dayun_rounding,
            anchor_jieqi_name=getattr(verify_response.dayun, "anchor_jieqi_name", None),
            anchor_jieqi_dt=getattr(verify_response.dayun, "anchor_jieqi_dt", None),
            direction=getattr(verify_response.dayun, "direction", None),
            direction_basis=getattr(verify_response.dayun, "direction_basis", None)
            or {"gender": None, "year_stem": None, "year_stem_yinyang": None},
            status="computed" if verify_response.dayun else "placeholder",
            sequence_start="from_month_pillar",
        ),
    )

    if liunian_years:
        try:
            verify_response.liunian = build_liunian(verify_response.pillars_primary, dt_effective, liunian_years)
        except Exception as exc:
            logger.warning("[bazi_full] build_liunian failed: %s", exc, exc_info=True)
            _mf = list(getattr(verify_response, "missing_fields", None) or [])
            if "liunian" not in _mf:
                _mf.append("liunian")
            verify_response.missing_fields = sorted(_mf)
            if verify_response.validation:
                verify_response.validation.warnings.append(
                    WarningModel(code="LIUNIAN_BUILD_FAIL", message="流年排盘计算失败")
                )

    kongwang = list(get_kongwang(verify_response.pillars_primary.day.stem, verify_response.pillars_primary.day.branch))
    if kongwang == ["未知", "未知"]:
        kongwang = []
    shensha_items = [item.model_dump() for item in (verify_response.shensha or [])]

    try:
        matched_rules = match_rules(
            geju=verify_response.geju,
            yongshen=verify_response.yongshen,
            shensha=verify_response.shensha,
        )
    except Exception:
        matched_rules = []

    payload = verify_response.model_dump()
    payload["pillar_details"] = {
        "year": _build_pillar_detail(
            "年柱",
            verify_response.pillars_primary.year.stem,
            verify_response.pillars_primary.year.branch,
            verify_response.pillars_primary.day.stem,
            kongwang,
            shensha_items,
        ),
        "month": _build_pillar_detail(
            "月柱",
            verify_response.pillars_primary.month.stem,
            verify_response.pillars_primary.month.branch,
            verify_response.pillars_primary.day.stem,
            kongwang,
            shensha_items,
        ),
        "day": _build_pillar_detail(
            "日柱",
            verify_response.pillars_primary.day.stem,
            verify_response.pillars_primary.day.branch,
            verify_response.pillars_primary.day.stem,
            kongwang,
            shensha_items,
        ),
        "hour": _build_pillar_detail(
            "时柱",
            verify_response.pillars_primary.hour.stem,
            verify_response.pillars_primary.hour.branch,
            verify_response.pillars_primary.day.stem,
            kongwang,
            shensha_items,
        ),
    }
    payload["kongwang"] = kongwang
    payload.update(
        {
            "api_version": API_VERSION,
            "rule_version": RULE_VERSION,
            "schema_version": "bazi_full@5.1",
            "request_id": request_id or str(uuid4()),
            "warnings": [*payload.get("warnings", []), *[w.model_dump() for w in warnings]],
            "methods": methods.model_dump(),
            "raw": raw.model_dump(),
            "rule_matches": matched_rules,
            "start_dayun_age": verify_response.start_dayun_age,
        }
    )

    if not payload.get("bazi_summary"):
        parts: list[str] = []
        if verify_response.geju:
            parts.append(f"格局：{verify_response.geju.geju_name}（{verify_response.geju.geju_level}）")
        if verify_response.day_master_strength:
            parts.append(
                f"日主：{verify_response.day_master_strength.tier}，评分{verify_response.day_master_strength.score:.1f}"
            )
        if verify_response.yongshen:
            favor = "、".join(verify_response.yongshen.favor[:3]) or "无"
            avoid = "、".join(verify_response.yongshen.avoid[:3]) or "无"
            parts.append(f"用神：喜{favor}，忌{avoid}")
        if verify_response.balance_advice:
            parts.append(f"五行建议：{verify_response.balance_advice}")
        if verify_response.current_fortune_summary:
            parts.append(
                f"当前运势：{verify_response.current_fortune_summary.current_dayun} / {verify_response.current_fortune_summary.current_liunian}"
            )
        if verify_response.liunian_detail:
            top_years = [f"{item.year}({item.annual_score})" for item in verify_response.liunian_detail[:3]]
            parts.append(f"关键年份：{'、'.join(top_years)}")
        payload["bazi_summary"] = "；".join(parts) + "。"

    relation_items: list[RelationItemModel] = []
    for raw_item in payload.get("dizhi_relations", []) or []:
        relation_items.append(
            RelationItemModel(
                type=_normalize_relation_type(str(raw_item.get("type") or raw_item.get("relation") or "干支互动")),
                subject=_text_or_empty(
                    raw_item.get("subject")
                    or raw_item.get("from")
                    or raw_item.get("a")
                    or "/".join(raw_item.get("branches", []) or [])
                    or "/".join(raw_item.get("positions", []) or [])
                    or raw_item.get("type")
                ),
                target=str(raw_item.get("target") or raw_item.get("to") or raw_item.get("b") or "") or None,
                summary=_text_or_empty(
                    raw_item.get("summary") or raw_item.get("desc") or raw_item.get("note") or raw_item.get("status")
                ),
                strength=raw_item.get("strength") if raw_item.get("strength") in {"strong", "medium", "weak"} else None,
            )
        )

    evidence_chain: list[EvidenceItemModel] = []
    if verify_response.geju:
        evidence_chain.append(
            EvidenceItemModel(
                title="格局",
                value=f"{verify_response.geju.geju_name}（{verify_response.geju.geju_level}）",
                source="geju",
                confidence="high",
            )
        )
    if verify_response.day_master_strength:
        evidence_chain.append(
            EvidenceItemModel(
                title="日主强弱",
                value=f"{verify_response.day_master_strength.tier} / {verify_response.day_master_strength.score:.1f}",
                source="day_master_strength",
                confidence="high",
            )
        )
    if verify_response.yongshen:
        evidence_chain.append(
            EvidenceItemModel(
                title="用神",
                value=f"喜{'、'.join(verify_response.yongshen.favor[:3]) or '无'}，忌{'、'.join(verify_response.yongshen.avoid[:3]) or '无'}",
                source="yongshen",
                confidence="medium",
            )
        )

    key_years = [
        TimelinePointModel(
            year=int(item.year),
            label="关键年",
            summary=str(item.interpretation_text or item.clash or ""),
            tone="current" if item.year == datetime.now().year else ("danger" if item.clash else "warn"),
        )
        for item in (verify_response.liunian_detail or [])[:4]
        if item.year is not None
    ]

    key_months = [
        TimelinePointModel(
            year=int(datetime.now().year),
            label=f"{idx + 1}月",
            summary=str(getattr(item, "interpretation_text", "") or getattr(item, "summary", "") or ""),
            tone="warn" if getattr(item, "clash", None) else "neutral",
        )
        for idx, item in enumerate((verify_response.monthly_fortune or [])[:4])
    ]

    month_branch = verify_response.pillars_primary.month.branch if verify_response.pillars_primary else None
    month_climate_rule = _MONTH_CLIMATE_RULES.get(month_branch or "", {})
    climate_value = month_climate_rule.get("climate") if isinstance(month_climate_rule, dict) else None
    climate_reason = month_climate_rule.get("reason") if isinstance(month_climate_rule, dict) else None
    climate_season = month_climate_rule.get("season") if isinstance(month_climate_rule, dict) else None

    adjustment_summary = AdjustmentSummaryModel(
        climate=climate_value if climate_value in {"寒", "暖", "燥", "湿", "平"} else "平",
        climate_source="services.bazi_engine.tables.MONTH_CLIMATE_RULES",
        climate_reason=(
            f"{climate_reason}（月令{month_branch or '—'}，{climate_season or '未知季节'}）" if climate_reason else ""
        ),
        tiaohou=(
            f"喜{'、'.join(verify_response.yongshen.favor[:2]) or '中和'}，忌{'、'.join(verify_response.yongshen.avoid[:2]) or '过旺'}"
            if verify_response.yongshen
            else None
        ),
        balance_direction="扶抑兼调候" if verify_response.yongshen else None,
        season_summary=verify_response.balance_advice,
        rationale=[
            f"月令：{month_branch}" if month_branch else "",
            f"调候：{climate_value}" if climate_value else "",
            f"日主强弱：{verify_response.day_master_strength.tier}" if verify_response.day_master_strength else "",
            f"格局：{verify_response.geju.geju_name}" if verify_response.geju else "",
        ],
    )

    payload["confidence_level"] = payload.get("confidence_level", "medium")
    payload["confidence_score"] = payload.get("confidence_score")
    payload["evidence_chain"] = [item.model_dump() for item in evidence_chain]
    payload["key_years"] = [item.model_dump() for item in key_years]
    payload["key_months"] = [item.model_dump() for item in key_months]
    payload["kongwang"] = payload.get("kongwang", [])
    payload["kongwang_source"] = "services.bazi_engine.tables.get_kongwang"
    tiangan_clash_notes = [
        _text_or_empty(item.get("note") or item.get("summary"))
        for item in (payload.get("tiangan_clashes", []) or [])
        if isinstance(item, dict)
    ]
    relation_summary_missing: list[str] = []
    if not relation_items:
        relation_summary_missing.append("relation_items")
    if not payload.get("kongwang"):
        relation_summary_missing.append("kongwang")
    if not verify_response.geju:
        relation_summary_missing.append("geju")

    _clash_summary = next((item.summary for item in relation_items if item.type == "冲" and item.summary), "")
    if not _clash_summary and tiangan_clash_notes:
        _clash_summary = tiangan_clash_notes[0]

    _combine_summary = next((item.summary for item in relation_items if item.type == "合" and item.summary), "")
    _harm_summary = next((item.summary for item in relation_items if item.type == "害" and item.summary), "")

    _interaction_parts = [
        text for text in [*(item.summary for item in relation_items[:3]), *(tiangan_clash_notes[:1])] if text
    ]
    _interaction_summary = "；".join(_interaction_parts)

    _has_clash_signal = any(item.type == "冲" for item in relation_items) or any(
        "冲" in note for note in tiangan_clash_notes
    )
    _has_combine_signal = any(item.type == "合" for item in relation_items) or any(
        kw in _interaction_summary for kw in ("合", "半合", "三合")
    )
    _has_harm_signal = any(item.type in {"害", "破", "刑"} for item in relation_items) or any(
        kw in _interaction_summary for kw in ("害", "破", "刑")
    )

    if not _clash_summary and _has_clash_signal:
        relation_summary_missing.append("clash_summary")
    if not _combine_summary and _has_combine_signal:
        relation_summary_missing.append("combine_summary")
    if not _harm_summary and _has_harm_signal:
        relation_summary_missing.append("harm_summary")
    if not _interaction_summary:
        relation_summary_missing.append("interaction_summary")

    if not climate_reason:
        relation_summary_missing.append("climate_reason")

    _score_reason = (
        "格局、日主强弱、用神、神煞、时间轴与关系摘要共同构成当前置信度"
        if verify_response.geju or verify_response.day_master_strength or verify_response.yongshen
        else ""
    )
    if not _score_reason:
        relation_summary_missing.append("confidence_score_reason")

    payload["bazi_structural_summary"] = BaziStructuralSummaryModel(
        core_snapshot={
            "pillars": payload.get("pillars_primary"),
            "ten_gods": payload.get("ten_gods"),
            "wuxing_score": payload.get("wuxing_score"),
            "wuxing_breakdown": payload.get("wuxing_breakdown"),
            "day_master_strength": payload.get("day_master_strength"),
            "geju_name": verify_response.geju.geju_name if verify_response.geju else None,
            "yongshen": payload.get("yongshen"),
        },
        relation_summary={
            "kongwang": payload.get("kongwang", []),
            "kongwang_source": "services.bazi_engine.tables.get_kongwang",
            "relation_items": [item.model_dump() for item in relation_items],
            "dizhi_relations": payload.get("dizhi_relations", []),
            "tiangan_clashes": payload.get("tiangan_clashes", []),
            "clash_summary": _clash_summary,
            "combine_summary": _combine_summary,
            "harm_summary": _harm_summary,
            "interaction_summary": _interaction_summary,
            "missing": relation_summary_missing,
        },
        adjustment_summary=adjustment_summary,
        timeline_summary={
            "key_years": [item.model_dump() for item in key_years],
            "key_months": [item.model_dump() for item in key_months],
        },
        confidence_summary=ConfidenceSummaryModel(
            level=payload["confidence_level"],
            score=payload.get("confidence_score") or 72,
            score_components={
                "geju": 30.0 if verify_response.geju else 0.0,
                "day_master_strength": 25.0 if verify_response.day_master_strength else 0.0,
                "yongshen": 20.0 if verify_response.yongshen else 0.0,
                "shensha": 10.0 if verify_response.shensha else 0.0,
                "timeline": 7.0 if verify_response.liunian_detail else 0.0,
                "relations": 8.0 if relation_items else 0.0,
            },
            score_reason=_score_reason,
            evidence=[item.model_dump() for item in evidence_chain],
            risk_notes=[w.message for w in verify_response.validation.warnings] if verify_response.validation else [],
            inference_notes=[payload["bazi_summary"]] if payload.get("bazi_summary") else [],
            blocked_fields=[],
        ).model_dump(),
        report_summary={
            "title": "八字结构摘要",
            "summary": payload.get("bazi_summary", ""),
            "highlights": [
                f"格局：{verify_response.geju.geju_name}" if verify_response.geju else "",
                f"日主：{verify_response.day_master_strength.tier}" if verify_response.day_master_strength else "",
                f"用神：{('、'.join(verify_response.yongshen.favor[:2]) if verify_response.yongshen else '')}",
            ],
            "warnings": [w.message for w in verify_response.validation.warnings] if verify_response.validation else [],
            "annotation_prompt": "可在报告页补充人工注释，说明格局、调候和关键年份。",
            "source": "services.bazi_full_service",
            "missing": [
                field_name
                for field_name, value in {
                    "geju_name": verify_response.geju.geju_name if verify_response.geju else None,
                    "day_master_strength": verify_response.day_master_strength.tier
                    if verify_response.day_master_strength
                    else None,
                    "yongshen": verify_response.yongshen.model_dump() if verify_response.yongshen else None,
                    "kongwang_source": payload.get("kongwang_source", None),
                }.items()
                if not value
            ],
        },
    ).model_dump()

    # B-P2-01: 流日/流时（默认开启；未传 target_date 时使用当天）
    _include_liuri = body.include_liuri if body.include_liuri is not None else True
    if _include_liuri:
        from datetime import date as _date

        _td = body.target_date.date() if body.target_date else _date.today()
        _th = body.target_hour if body.target_hour is not None else dt_effective.hour

        liuri_payload, dayun_patch = build_liuri_liushi_enrichment(
            verify_response=verify_response,
            birth_dt=dt_effective,
            target_date=_td,
            target_hour=_th,
        )
        payload["liuri_liushi"] = liuri_payload

        if dayun_patch and payload.get("dayun"):
            payload["dayun"]["days_to_next_transition"] = dayun_patch.get("days_to_next_transition")
            payload["dayun"]["next_transition_age"] = dayun_patch.get("next_transition_age")
            payload["dayun"]["next_transition_ganzhi"] = dayun_patch.get("next_transition_ganzhi")
            payload["dayun"]["next_transition_hint"] = dayun_patch.get("next_transition_hint")

    _liuri_missing = (
        payload.get("liuri_liushi", {}).get("missing_fields", [])
        if isinstance(payload.get("liuri_liushi"), dict)
        else []
    )
    _context_missing = _collect_context_missing_fields(body, verify_response, payload)
    payload["missing_fields"] = sorted(
        set(
            payload.get("missing_fields", [])
            + relation_summary_missing
            + _liuri_missing
            + _context_missing
            + list(getattr(verify_response, "missing_fields", None) or [])
        )
    )
    payload["provenance"] = build_bazi_provenance(
        verify_response,
        body,
        missing_fields=payload.get("missing_fields"),
    ).model_dump()
    try:
        from services.bazi_engine.classical_narrative import geju_classic_sentence, shun_ni

        geju_name = (payload.get("geju") or {}).get("geju_name") or ""
        if geju_name:
            derived = (payload.get("geju") or {}).get("derived_geju")
            payload.setdefault("geju", {})["classic_ref"] = payload.get("geju", {}).get(
                "classic_ref"
            ) or geju_classic_sentence(geju_name, derived)
        bss = payload.get("bazi_structural_summary") or {}
        if isinstance(bss, dict):
            dm = (payload.get("day_master_strength") or {}).get("tier") or ""
            dayun_data = payload.get("dayun") or {}
            direction = dayun_data.get("direction") or "forward"
            if direction not in ("forward", "backward"):
                direction = "forward" if str(direction).startswith("顺") else "backward"
            ys_shift = "neutral"
            liunian_items = (payload.get("liunian") or {}).get("items") or []
            if liunian_items:
                ys_shift = liunian_items[0].get("yongshen_shift", "neutral") or "neutral"
            bss["shun_ni"] = shun_ni(direction, ys_shift, tier=dm)
            payload["bazi_structural_summary"] = bss
    except Exception as exc:
        import logging

        logging.getLogger(__name__).debug("[classical_narrative] %s", exc)

    _classic_refs: list[dict] = []
    _seen_classic: set[str] = set()
    for item in verify_response.shensha or []:
        for ref in getattr(item, "classic_refs", None) or []:
            rid = ref.get("id", "") if isinstance(ref, dict) else ""
            if rid and rid not in _seen_classic:
                _seen_classic.add(rid)
                _classic_refs.append(ref)
    geju_block = payload.get("geju") or {}
    for ref in geju_block.get("geju_candidates") or []:
        if isinstance(ref, dict):
            rid = ref.get("id", "")
            if rid and rid not in _seen_classic:
                _seen_classic.add(rid)
                _classic_refs.append(ref)
    if geju_block.get("derived_geju"):
        from services.bazi_engine.classical_narrative import geju_classic_sentence

        derived_line = geju_classic_sentence(geju_block.get("geju_name", ""), geju_block.get("derived_geju"))
        if derived_line:
            _classic_refs.append(
                {
                    "id": f"derived_{geju_block.get('derived_geju')}",
                    "source": "衍生格局句式",
                    "text": derived_line,
                    "category": "格局",
                    "hint_type": "derived",
                }
            )
    if geju_block.get("classic_ref"):
        _classic_refs.append(
            {
                "id": "geju_narrative",
                "source": "典籍句式",
                "text": geju_block.get("classic_ref"),
                "category": "格局",
                "hint_type": "narrative",
            }
        )
    payload["classic_refs"] = _classic_refs[:12]
    payload["evidence_ids"] = _build_evidence_ids(
        payload.get("rule_matches") or [],
        payload.get("classic_refs") or [],
        payload.get("evidence_chain") or [],
    )

    payload["relations_summary"] = {
        "items": [item.model_dump() for item in relation_items],
        "clash_summary": _clash_summary,
        "combine_summary": _combine_summary,
        "harm_summary": _harm_summary,
        "interaction_summary": _interaction_summary,
        "missing": relation_summary_missing,
    }
    _shensha_raw = payload.get("shensha") or []
    _highlight_seen: set[str] = set()
    _shensha_highlights: list[str] = []
    for item in _shensha_raw:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name") or "")
        if name and name not in _highlight_seen:
            _highlight_seen.add(name)
            _shensha_highlights.append(name)
    payload["shensha_summary"] = {
        "items": _shensha_raw,
        "highlights": _shensha_highlights[:8],
        "missing": [] if _shensha_raw else ["shensha"],
    }

    from services.content_policy import content_versions_meta, default_disclaimer_block

    payload["disclaimer_block"] = default_disclaimer_block()
    payload["content_versions"] = content_versions_meta()

    _slim_full_interpretation(payload)

    return BaziFullResponse.model_validate(payload)


_FULL_SLIM_BLOCKS = (
    "geju",
    "yongshen",
    "career",
    "wealth_analysis",
    "health",
    "marriage_analysis",
    "relationship",
    "personality",
    "lifestyle",
)


def _collect_context_missing_fields(body, verify_response, payload: dict) -> list[str]:
    """R029: surface hour/jieqi/dual-track gaps for FE trust panels."""
    tokens: list[str] = []
    precision = getattr(body, "birth_time_precision", "exact") or "exact"
    if precision in ("unknown", "approximate"):
        tokens.append("hour_pillar")
    rf = getattr(verify_response, "risk_flags", None)
    if rf and getattr(rf, "near_jieqi_boundary", False):
        tokens.append("jieqi_boundary")
    if body.mode == "dual":
        secondary = payload.get("pillars_secondary")
        validation = getattr(verify_response, "validation", None)
        diff_fields = list(getattr(validation, "diff_fields", None) or [])
        if not secondary or diff_fields:
            tokens.append("pillars_secondary")
    return tokens


def _build_evidence_ids(
    rule_matches: list,
    classic_refs: list[dict],
    evidence_chain: list,
) -> list[str]:
    """R034: stable ids from rules, classics, and evidence chain sources."""
    ids: list[str] = []
    for rm in rule_matches:
        rid = rm.get("rule_id") if isinstance(rm, dict) else getattr(rm, "rule_id", "")
        if rid:
            ids.append(str(rid))
    for ref in classic_refs:
        if isinstance(ref, dict) and ref.get("id"):
            ids.append(str(ref["id"]))
    for item in evidence_chain:
        if isinstance(item, dict):
            src = item.get("source")
        else:
            src = getattr(item, "source", None)
        if src:
            ids.append(f"chain:{src}")
    return sorted(set(ids))


def _slim_full_interpretation(payload: dict) -> None:
    """R031: default /full omits long interpretation_text; use explain/batch instead."""
    for key in _FULL_SLIM_BLOCKS:
        block = payload.get(key)
        if isinstance(block, dict) and block.get("interpretation_text"):
            block["interpretation_text"] = ""


def apply_profile_slim(payload: dict) -> None:
    """IND-03: profile=slim strips domain narratives and dayun hint text."""
    _slim_full_interpretation(payload)
    for key in ("milestones", "love_windows"):
        if key in payload:
            payload[key] = []
    dayun = payload.get("dayun")
    if isinstance(dayun, dict):
        for hint_key in (
            "transition_hint",
            "next_transition_hint",
            "next_transition_ganzhi",
        ):
            dayun.pop(hint_key, None)
    for domain_key in (
        "career",
        "wealth_analysis",
        "health",
        "marriage_analysis",
        "relationship",
        "personality",
        "lifestyle",
    ):
        block = payload.get(domain_key)
        if isinstance(block, dict):
            if "interpretation_text" in block:
                block["interpretation_text"] = ""
            block.pop("narrative", None)
