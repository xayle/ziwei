"""
services/event_signal_engine.py — 命理事件信号识别引擎

架构：
  1. 基础命盘（natal_base）      +1
  2. 大运触发（dayun_trigger）   +2
  3. 流年触发（liunian_trigger） +2
  4. 流月应期（month_trigger）   +1
  5. 三层叠加奖励（≥3层）        +1

风险等级映射：
  0       → none
  1-2     → low
  3-4     → medium
  5-6     → medium_high
  7+      → high
"""
from __future__ import annotations

from datetime import datetime
import logging
from typing import Optional

from app.schemas.event_prediction import (
    ClassicalNote,
    EventResult,
    EventSignal,
    MultiYearTrendResponse,
    YearSummary,
)
from services.bazi_engine.analysis.liunian_domain import _TAOHUAL_MAP, _YIMA_MAP
from services.bazi_engine.liunian import compute_liunian
from services.bazi_engine.tables import BRANCH_CHONG, STEM_ELEMENT, get_ten_god

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# 常量
# ─────────────────────────────────────────────────────────────────────────────

_STEMS    = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
_BRANCHES = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]

# 五行克关系：A 克 B
_OVERCOME: dict[str, str] = {
    "wood": "earth", "fire": "metal", "earth": "water",
    "metal": "wood", "water": "fire",
}

# 月支五行（寅=正月起）
_MONTH_BR_12 = ["寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥", "子", "丑"]
_BRANCH_WX   = {
    "寅": "wood", "卯": "wood", "辰": "earth", "巳": "fire",
    "午": "fire", "未": "earth", "申": "metal", "酉": "metal",
    "戌": "earth", "亥": "water", "子": "water", "丑": "earth",
}

# 风险评分 → 等级
_RISK_MAP = {0: "none", 1: "low", 2: "low", 3: "medium", 4: "medium",
             5: "medium_high", 6: "medium_high"}

# 机会评分 → 等级
_OPP_MAP = {0: "none", 1: "low", 2: "low", 3: "medium", 4: "medium", 5: "high"}

# 年份评分（风险vs机会换算）
_RISK_SCORE_MAP  = {"none": 88, "low": 75, "medium": 60, "medium_high": 40, "high": 25}
_OPP_SCORE_MAP   = {"none": 50, "low": 60, "medium": 70, "high": 85}


# ─────────────────────────────────────────────────────────────────────────────
# 辅助函数
# ─────────────────────────────────────────────────────────────────────────────

def _year_ganzhi(year: int) -> tuple[str, str]:
    return _STEMS[(year - 4) % 10], _BRANCHES[(year - 4) % 12]


def _score_to_risk(score: int) -> str:
    return _RISK_MAP.get(min(score, 6), "high")


def _score_to_opp(score: int) -> str:
    return _OPP_MAP.get(min(score, 5), "high")


def _compute_notable_months(yongshen_favor: list[str]) -> list[int]:
    return [i + 1 for i, br in enumerate(_MONTH_BR_12)
            if _BRANCH_WX.get(br) in yongshen_favor][:4]


def _get_dayun_for_year(dayun_model, target_year: int):
    """返回 target_year 所在大运步的 DaYunItemModel，找不到返回 None"""
    if not dayun_model or not dayun_model.items:
        return None
    current = None
    for item in dayun_model.items:
        sy = getattr(item, "start_year", None)
        if sy is not None and sy <= target_year:
            current = item
        elif sy is not None and sy > target_year:
            break
    return current


def _wxscore_dict(vr) -> dict[str, float]:
    wx = vr.wuxing_score
    if not wx:
        return {}
    return {
        "wood": float(getattr(wx, "wood", 0)),
        "fire": float(getattr(wx, "fire", 0)),
        "earth": float(getattr(wx, "earth", 0)),
        "metal": float(getattr(wx, "metal", 0)),
        "water": float(getattr(wx, "water", 0)),
    }


def _sig(key: str, label: str, layer: str, severity: str,
          rule_id: Optional[str] = None) -> EventSignal:
    return EventSignal(signal_key=key, label=label, layer=layer,  # type: ignore[arg-type]
                       severity=severity, rule_id=rule_id)  # type: ignore[arg-type]


def _confidence(risk_score: int, opp_score: int) -> float:
    raw = (risk_score + opp_score) * 0.12 + 0.35
    return round(min(raw, 0.95), 2)


def _main_judgment(event_type: str, risk: str, opp: str, year: int,
                   subtypes: list[str]) -> str:
    """生成一句话结论"""
    RISK_DESC = {
        "none": "整体平稳，无明显风险",
        "low": "有轻微波动，总体可控",
        "medium": "存在一定压力，需要主动应对",
        "medium_high": "压力较明显，是重要的压力测试年",
        "high": "进入高风险震荡期，变化力度较大",
    }
    OPP_DESC = {
        "none": "",
        "low": "有小机会可把握",
        "medium": "同时存在发展机遇",
        "high": "机遇明显",
    }
    type_label = {
        "marriage": "婚姻感情", "wealth": "财务财运",
        "property": "房产居住", "career": "事业职场", "health": "健康状态",
    }.get(event_type, event_type)
    opp_note = OPP_DESC.get(opp, "")
    return f"{year}年{type_label}{RISK_DESC.get(risk, '')}{'，' + opp_note if opp_note else ''}。"


def _trigger_summary(signals: list[EventSignal]) -> str:
    """生成信号摘要（给 LLM 作边界约束）"""
    parts = [s.label for s in signals if s.severity in ("primary", "secondary")][:3]
    return "；".join(parts) if parts else "无明显命理信号"


# ─────────────────────────────────────────────────────────────────────────────
# 婚姻信号
# ─────────────────────────────────────────────────────────────────────────────

def _signals_marriage(
    year: int, liunian: dict, dayun_item, day_branch: str,
    gender: str, yongshen_favor: list[str],
    notable_months: list[int], dm_tier: str,
) -> tuple[list[EventSignal], list[EventSignal]]:  # (risk_sigs, opp_sigs)
    risk_sigs: list[EventSignal] = []
    opp_sigs: list[EventSignal] = []

    ten_god   = liunian.get("ten_god", "")
    liunian_br = liunian.get("branch", "")
    liunian_wx = liunian.get("flow_wuxing", "")
    clash_val  = liunian.get("clash")   # 流年支 vs 日支

    # ── natal_base ──────────────────────────────────────────────────────────
    if dm_tier in ("偏弱", "极弱"):
        risk_sigs.append(_sig("natal_weak_dm", "日主偏弱受外界影响更大",
                               "natal_base", "tertiary"))

    # ── dayun_trigger ──────────────────────────────────────────────────────
    if dayun_item:
        dy_tg = getattr(dayun_item, "ten_god", "")
        if dy_tg in ("正官", "七杀") and gender == "female":
            risk_sigs.append(_sig("dayun_guansha_female", f"大运{dy_tg}（女命感情压力）",
                                   "dayun_trigger", "secondary"))
        elif dy_tg in ("偏财",) and gender == "male":
            opp_sigs.append(_sig("dayun_piancai_male", "大运偏财（男命异性缘旺）",
                                  "dayun_trigger", "secondary"))
        elif dy_tg in ("劫财", "比肩"):
            risk_sigs.append(_sig("dayun_bijie_marriage", f"大运{dy_tg}（第三方风险）",
                                   "dayun_trigger", "secondary"))
        elif dy_tg in ("食神", "伤官") and gender == "female":
            risk_sigs.append(_sig("dayun_shishang_female", f"大运{dy_tg}女命感情变数",
                                   "dayun_trigger", "tertiary"))

    # ── liunian_trigger ────────────────────────────────────────────────────
    # 夫妻宫受冲（日支被流年冲）
    if clash_val and "冲" in clash_val:
        risk_sigs.append(_sig("day_branch_clashed",
                               f"流年冲日支（夫妻宫受冲）",
                               "liunian_trigger", "primary",
                               rule_id="marriage_day_branch_clash"))    # 本命年（值太岁）——感情流年不稳
    if clash_val and "值太岁" in clash_val:
        risk_sigs.append(_sig("ben_ming_nian_marriage", "本命年（值太岁）感情感情容易工于内心",
                               "liunian_trigger", "secondary"))
    # 桃花
    taohua = _TAOHUAL_MAP.get(day_branch)
    if taohua and liunian_br == taohua:
        opp_sigs.append(_sig("taohua_triggered", "流年临桃花（感情缘分旺）",
                              "liunian_trigger", "secondary",
                              rule_id="marriage_taohua_liunian"))

    # 十神信号
    if ten_god == "正官" and gender == "female":
        opp_sigs.append(_sig("guanxing_female", "流年正官（女命夫星当令）",
                              "liunian_trigger", "secondary",
                              rule_id="marriage_guanxing_female"))
    elif ten_god == "七杀" and gender == "female":
        risk_sigs.append(_sig("qisha_female", "流年七杀（女命感情摩擦）",
                               "liunian_trigger", "secondary",
                               rule_id="marriage_qisha_female"))
    elif ten_god == "偏财" and gender == "male":
        opp_sigs.append(_sig("piancai_male", "流年偏财（男命异性缘活跃）",
                              "liunian_trigger", "secondary",
                              rule_id="marriage_piancai_male"))
    elif ten_god in ("比肩", "劫财"):
        risk_sigs.append(_sig("bijie_marriage", f"流年{ten_god}（第三方干扰风险）",
                               "liunian_trigger", "secondary",
                               rule_id="marriage_bijie_jiucai"))
    elif ten_god == "食神" and liunian_wx in yongshen_favor:
        opp_sigs.append(_sig("shishen_marriage", "流年食神用神得令（感情温暖）",
                              "liunian_trigger", "tertiary",
                              rule_id="marriage_shishen_harmonious"))
    elif ten_god in ("正官", "七杀") and gender == "male":
        risk_sigs.append(_sig("guansha_male_stress", f"流年{ten_god}（职场压力波及感情）",
                               "liunian_trigger", "tertiary"))

    # ── month_trigger ──────────────────────────────────────────────────────
    if notable_months:
        opp_sigs.append(_sig("notable_months_marriage",
                              f"用神旺月（{','.join(str(m) for m in notable_months[:2])}月）感情易有进展",
                              "month_trigger", "tertiary"))

    return risk_sigs, opp_sigs


# ─────────────────────────────────────────────────────────────────────────────
# 财运信号
# ─────────────────────────────────────────────────────────────────────────────

def _signals_wealth(
    year: int, liunian: dict, dayun_item,
    yongshen_favor: list[str], yongshen_avoid: list[str],
    wx_scores: dict[str, float], notable_months: list[int],
) -> tuple[list[EventSignal], list[EventSignal]]:
    risk_sigs: list[EventSignal] = []
    opp_sigs: list[EventSignal] = []

    ten_god    = liunian.get("ten_god", "")
    liunian_wx = liunian.get("flow_wuxing", "")

    # ── natal_base ──────────────────────────────────────────────────────────
    total_wx = sum(wx_scores.values()) or 1.0
    for el, sc in wx_scores.items():
        if el in yongshen_avoid and (sc / total_wx) > 0.35:
            risk_sigs.append(_sig(f"natal_avoid_{el}",
                                   f"命局{el}五行偏多（忌神过旺）",
                                   "natal_base", "tertiary",
                                   rule_id="wealth_wuxing_overload_risk"))

    # ── dayun_trigger ──────────────────────────────────────────────────────
    dy_tg = getattr(dayun_item, "ten_god", "") if dayun_item else ""
    dy_wx = getattr(dayun_item, "flow_wuxing", "") if dayun_item else ""

    dayun_risk = False
    dayun_opp  = False
    if dy_tg == "劫财":
        risk_sigs.append(_sig("dayun_jiucai", "大运劫财（财运长期不稳）",
                               "dayun_trigger", "secondary"))
        dayun_risk = True
    elif dy_tg in ("偏财", "食神") and dy_wx in yongshen_favor:
        opp_sigs.append(_sig("dayun_piancai_wealth", f"大运{dy_tg}（财运活跃期）",
                              "dayun_trigger", "secondary",
                              rule_id="wealth_piancai_dayun"))
        dayun_opp = True
    elif dy_tg == "正财":
        opp_sigs.append(_sig("dayun_zhengcai", "大运正财（收入稳步积累）",
                              "dayun_trigger", "secondary"))
        dayun_opp = True
    elif dy_tg in ("正印", "偏印") and dy_wx not in yongshen_favor:
        risk_sigs.append(_sig("dayun_yinxing", "大运印星（财运承压）",
                               "dayun_trigger", "tertiary",
                               rule_id="wealth_yinxing_suppresses_wealth"))

    # ── liunian_trigger ────────────────────────────────────────────────────
    if ten_god == "劫财":
        risk_sigs.append(_sig("liunian_jiucai", "流年劫财（破财合伙风险）",
                               "liunian_trigger", "primary",
                               rule_id="wealth_jiucai_loss"))
        if dayun_risk:  # 大运+流年双劫财
            risk_sigs.append(_sig("double_jiucai", "大运流年双劫财（重大破财警示）",
                                   "liunian_trigger", "primary",
                                   rule_id="wealth_dayun_jiucai_double"))
    elif ten_god == "比肩":
        risk_sigs.append(_sig("liunian_bijie", "流年比肩（竞争财被分）",
                               "liunian_trigger", "secondary",
                               rule_id="wealth_bijie_competition"))
    elif ten_god == "偏财" and liunian_wx in yongshen_favor:
        opp_sigs.append(_sig("liunian_piancai_opp", "流年偏财（横财副业机会）",
                              "liunian_trigger", "secondary",
                              rule_id="wealth_piancai_opportunity"))
        if dayun_opp:  # 双偏财
            opp_sigs.append(_sig("double_piancai", "大运流年双偏财（财运高峰）",
                                  "liunian_trigger", "secondary",
                                  rule_id="wealth_piancai_dayun"))
    elif ten_god == "偏财" and liunian_wx not in yongshen_favor:
        risk_sigs.append(_sig("liunian_piancai_risk", "流年偏财忌神（财来财去）",
                               "liunian_trigger", "tertiary"))
    elif ten_god == "正财":
        opp_sigs.append(_sig("liunian_zhengcai", "流年正财（本职收入稳增）",
                              "liunian_trigger", "tertiary",
                              rule_id="wealth_zhengcai_stable"))
    elif ten_god == "食神" and liunian_wx in yongshen_favor:
        opp_sigs.append(_sig("liunian_shishen_wealth", "流年食神生财（才华变现）",
                              "liunian_trigger", "secondary",
                              rule_id="wealth_shishen_caiyun"))
    elif ten_god in ("正印", "偏印") and liunian_wx not in yongshen_favor:
        risk_sigs.append(_sig("liunian_yinxing", "流年印星（主动创收受阻）",
                               "liunian_trigger", "secondary",
                               rule_id="wealth_yinxing_suppresses_wealth"))
    elif ten_god == "伤官":
        # 伤官年财运变数
        risk_sigs.append(_sig("liunian_shangguan", "流年伤官（财运有变数）",
                               "liunian_trigger", "secondary",
                               rule_id="wealth_shangguan_variable"))

    # ── month_trigger ──────────────────────────────────────────────────────
    if notable_months:
        opp_sigs.append(_sig("notable_months_wealth",
                              f"用神旺月（{','.join(str(m) for m in notable_months[:2])}月）财运有利",
                              "month_trigger", "tertiary"))

    return risk_sigs, opp_sigs


# ─────────────────────────────────────────────────────────────────────────────
# 房产信号
# ─────────────────────────────────────────────────────────────────────────────

def _signals_property(
    year: int, liunian: dict, dayun_item, day_branch: str,
    yongshen_favor: list[str], notable_months: list[int],
) -> tuple[list[EventSignal], list[EventSignal]]:
    risk_sigs: list[EventSignal] = []
    opp_sigs: list[EventSignal] = []

    ten_god    = liunian.get("ten_god", "")
    liunian_br = liunian.get("branch", "")
    liunian_wx = liunian.get("flow_wuxing", "")

    # ── dayun_trigger ──────────────────────────────────────────────────────
    dy_tg = getattr(dayun_item, "ten_god", "") if dayun_item else ""
    dy_br = getattr(dayun_item, "branch", "") if dayun_item else ""

    dayun_piancai = False
    if dy_tg in ("偏财", "正财"):
        opp_sigs.append(_sig("dayun_property_opp", f"大运{dy_tg}（置业财力积累期）",
                              "dayun_trigger", "secondary",
                              rule_id="property_zhengcai_dayun"))
        dayun_piancai = True
    yima = _YIMA_MAP.get(day_branch, "")
    if dy_br == yima:
        opp_sigs.append(_sig("dayun_yima_move", "大运临驿马（居住迁移长期动象）",
                              "dayun_trigger", "secondary",
                              rule_id="property_yima_dayun"))

    # ── liunian_trigger ────────────────────────────────────────────────────
    if ten_god == "偏财":
        opp_sigs.append(_sig("liunian_piancai_property", "流年偏财（买房动象）",
                              "liunian_trigger", "secondary",
                              rule_id="property_piancai_purchase"))
        if dayun_piancai:
            opp_sigs.append(_sig("double_piancai_property", "大运流年双偏财（强买房信号）",
                                  "liunian_trigger", "primary",
                                  rule_id="property_dayun_liunian_double_piancai"))
    if liunian_br == yima:
        opp_sigs.append(_sig("yima_triggered", "流年临驿马（搬家动象）",
                              "liunian_trigger", "secondary",
                              rule_id="property_yima_move"))
    if ten_god in ("正官", "七杀"):
        risk_sigs.append(_sig("guansha_property_dispute", "流年官杀（房产事宜有阻力）",
                               "liunian_trigger", "tertiary",
                               rule_id="property_family_dispute_risk"))
    if ten_god == "食神":
        opp_sigs.append(_sig("shishen_renovation", "流年食神（适合装修改善居所）",
                              "liunian_trigger", "tertiary",
                              rule_id="property_shishen_investment"))

    # ── month_trigger ──────────────────────────────────────────────────────
    if notable_months:
        opp_sigs.append(_sig("notable_months_property",
                              f"用神旺月（{','.join(str(m) for m in notable_months[:2])}月）置业时机较优",
                              "month_trigger", "tertiary"))

    return risk_sigs, opp_sigs


# ─────────────────────────────────────────────────────────────────────────────
# 事业信号
# ─────────────────────────────────────────────────────────────────────────────

def _signals_career(
    year: int, liunian: dict, dayun_item,
    yongshen_favor: list[str], dm_tier: str, notable_months: list[int],
) -> tuple[list[EventSignal], list[EventSignal]]:
    risk_sigs: list[EventSignal] = []
    opp_sigs: list[EventSignal] = []

    ten_god    = liunian.get("ten_god", "")
    liunian_wx = liunian.get("flow_wuxing", "")

    # ── natal_base ──────────────────────────────────────────────────────────
    if dm_tier in ("偏旺", "极旺"):
        opp_sigs.append(_sig("natal_strong_dm", "日主偏旺（事业主动性强）",
                              "natal_base", "tertiary"))

    # ── dayun_trigger ──────────────────────────────────────────────────────
    dy_tg = getattr(dayun_item, "ten_god", "") if dayun_item else ""
    if dy_tg in ("正官", "七杀"):
        opp_sigs.append(_sig("dayun_guansha_career", f"大运{dy_tg}（职场地位受重视）",
                              "dayun_trigger", "secondary"))
    elif dy_tg == "正印":
        opp_sigs.append(_sig("dayun_zhengyin_career", "大运正印（贵人持续扶助）",
                              "dayun_trigger", "secondary",
                              rule_id="career_dayun_zhengyin"))
    elif dy_tg in ("劫财", "比肩"):
        risk_sigs.append(_sig("dayun_bijie_career", f"大运{dy_tg}（职场竞争加剧）",
                               "dayun_trigger", "secondary",
                               rule_id="career_bijie_competition"))

    # ── liunian_trigger ────────────────────────────────────────────────────
    if ten_god == "正官":
        opp_sigs.append(_sig("zhengguan_promotion", "流年正官（晋升机遇）",
                              "liunian_trigger", "secondary",
                              rule_id="career_zhengguan_promotion"))
    elif ten_god == "七杀":
        risk_sigs.append(_sig("qisha_pressure", "流年七杀（职场压力上升）",
                               "liunian_trigger", "secondary",
                               rule_id="career_qisha_pressure"))
    elif ten_god == "伤官":
        opp_sigs.append(_sig("shangguan_change", "流年伤官（跳槽转型窗口）",
                              "liunian_trigger", "secondary",
                              rule_id="career_shangguan_change"))
    elif ten_god == "食神":
        opp_sigs.append(_sig("shishen_innovation", "流年食神（创意专业突破）",
                              "liunian_trigger", "secondary",
                              rule_id="career_shishen_innovation"))
    elif ten_god == "正印":
        opp_sigs.append(_sig("zhengyin_study", "流年正印（进修考证有利）",
                              "liunian_trigger", "tertiary",
                              rule_id="career_zhengyin_study"))
    elif ten_god in ("比肩", "劫财"):
        risk_sigs.append(_sig("bijie_competition_career", f"流年{ten_god}（同行竞争激烈）",
                               "liunian_trigger", "secondary",
                               rule_id="career_bijie_competition"))
    elif ten_god == "偏财":
        opp_sigs.append(_sig("piancai_cross_industry", "流年偏财（跨界副业机会）",
                              "liunian_trigger", "tertiary",
                              rule_id="career_piancai_cross_industry"))

    # ── month_trigger ──────────────────────────────────────────────────────
    if notable_months:
        opp_sigs.append(_sig("notable_months_career",
                              f"用神旺月（{','.join(str(m) for m in notable_months[:2])}月）事业有利",
                              "month_trigger", "tertiary"))

    return risk_sigs, opp_sigs


# ─────────────────────────────────────────────────────────────────────────────
# 健康信号
# ─────────────────────────────────────────────────────────────────────────────

def _signals_health(
    year: int, liunian: dict, dayun_item, day_stem: str,
    yongshen_avoid: list[str], wx_scores: dict[str, float], notable_months: list[int],
) -> tuple[list[EventSignal], list[EventSignal]]:
    risk_sigs: list[EventSignal] = []
    opp_sigs: list[EventSignal] = []

    ten_god    = liunian.get("ten_god", "")
    liunian_wx = liunian.get("flow_wuxing", "")
    clash_val  = liunian.get("clash")

    day_wx_tuple = STEM_ELEMENT.get(day_stem)
    day_wx = day_wx_tuple[0] if day_wx_tuple else ""

    # ── natal_base ──────────────────────────────────────────────────────────
    total_wx = sum(wx_scores.values()) or 1.0
    dominant_el = max(wx_scores, key=lambda k: wx_scores.get(k, 0.0)) if wx_scores else ""
    dominant_ratio = wx_scores.get(dominant_el, 0.0) / total_wx if dominant_el else 0.0
    if dominant_ratio > 0.45:
        risk_sigs.append(_sig(f"dominant_{dominant_el}", f"命局{dominant_el}偏旺（对应脏腑长期承压）",
                               "natal_base", "secondary",
                               rule_id="health_wuxing_dominant_organ"))

    # ── dayun_trigger ──────────────────────────────────────────────────────
    dy_wx = getattr(dayun_item, "flow_wuxing", "") if dayun_item else ""
    if dy_wx and dy_wx in yongshen_avoid:
        risk_sigs.append(_sig("dayun_avoid_element", f"大运{dy_wx}五行为忌（体质长期承压）",
                               "dayun_trigger", "secondary"))
    elif dy_wx and _OVERCOME.get(dy_wx) == day_wx:
        risk_sigs.append(_sig("dayun_ke_rizhu", f"大运{dy_wx}克日主（精力长期消耗）",
                               "dayun_trigger", "secondary"))

    # ── liunian_trigger ────────────────────────────────────────────────────
    # 流年五行克日主五行
    if liunian_wx and day_wx and _OVERCOME.get(liunian_wx) == day_wx:
        risk_sigs.append(_sig("ke_rizhu", f"流年{liunian_wx}克日主（健康压力年）",
                               "liunian_trigger", "primary",
                               rule_id="health_liunian_ke_rizhu"))

    # 本命年（值太岁）——六親支压、身心不稳
    if clash_val and "值太岁" in clash_val:
        risk_sigs.append(_sig("ben_ming_nian_health", "本命年（值太岁），传统命理认为需防健康不高",
                               "liunian_trigger", "secondary"))

    # 七杀临年
    if ten_god == "七杀":
        risk_sigs.append(_sig("qisha_injury", "流年七杀（磕碰损伤风险）",
                               "liunian_trigger", "secondary",
                               rule_id="health_qisha_injury"))

    # 比劫过旺
    if ten_god in ("比肩", "劫财"):
        risk_sigs.append(_sig("bijie_overwork", "流年比劫（过劳身竭风险）",
                               "liunian_trigger", "secondary",
                               rule_id="health_overwork_bijie"))

    # 地支冲（冲太岁/冲日支，健康压力）
    if clash_val and "冲" in clash_val:
        risk_sigs.append(_sig("chong_health", "流年冲日支（精气神消耗）",
                               "liunian_trigger", "secondary",
                               rule_id="health_tajsui_impact"))

    # 五行特化
    if liunian_wx == "wood":
        risk_sigs.append(_sig("wood_liver", "流年木旺（肝胆系统注意）",
                               "liunian_trigger", "tertiary",
                               rule_id="health_liver_wood_strong"))
    elif liunian_wx == "metal":
        risk_sigs.append(_sig("metal_lung", "流年金旺（肺呼吸道注意）",
                               "liunian_trigger", "tertiary",
                               rule_id="health_metal_lung"))

    # 情绪压力（流年凶神多）
    if len(risk_sigs) >= 2:
        risk_sigs.append(_sig("emotional_pressure", "年内压力偏大（注意身心健康）",
                               "liunian_trigger", "tertiary",
                               rule_id="health_emotional_pressure"))

    # 用神旺月 - 健康恢复较好
    if notable_months:
        opp_sigs.append(_sig("notable_months_health",
                              f"用神旺月（{','.join(str(m) for m in notable_months[:2])}月）精力较充沛",
                              "month_trigger", "tertiary"))

    return risk_sigs, opp_sigs


# ─────────────────────────────────────────────────────────────────────────────
# 评分与等级计算
# ─────────────────────────────────────────────────────────────────────────────

def _compute_levels(
    risk_sigs: list[EventSignal],
    opp_sigs: list[EventSignal],
) -> tuple[str, str, float]:
    """返回 (risk_level, opportunity_level, confidence)"""
    risk_score = 0
    opp_score  = 0
    risk_layers: set[str] = set()
    opp_layers:  set[str] = set()

    sev_score = {"primary": 3, "secondary": 2, "tertiary": 1}

    for s in risk_sigs:
        if s.layer not in risk_layers:
            risk_layers.add(s.layer)
            risk_score += {"natal_base": 1, "dayun_trigger": 2,
                           "liunian_trigger": 2, "month_trigger": 1}[s.layer]
        risk_score += sev_score.get(s.severity, 0)

    for s in opp_sigs:
        if s.layer not in opp_layers:
            opp_layers.add(s.layer)
            opp_score += {"natal_base": 1, "dayun_trigger": 2,
                          "liunian_trigger": 2, "month_trigger": 1}.get(s.layer, 0)
        opp_score += sev_score.get(s.severity, 0)

    # 三层叠加奖励
    all_layers = risk_layers | opp_layers
    if len(all_layers) >= 3:
        risk_score += 1

    risk_level = _score_to_risk(risk_score)
    opp_level  = _score_to_opp(opp_score)
    conf = _confidence(risk_score, opp_score)
    return risk_level, opp_level, conf


# ─────────────────────────────────────────────────────────────────────────────
# 子事件类型推断
# ─────────────────────────────────────────────────────────────────────────────

def _infer_subtypes(event_type: str, risk_sigs: list[EventSignal],
                    opp_sigs: list[EventSignal]) -> list[str]:
    """根据信号的 rule_id 推断具体子事件类型（从 event_rules.json 读取）"""
    from services.event_rule_matcher import get_subtypes_for_rule_ids
    rule_ids = [s.rule_id for s in (risk_sigs + opp_sigs) if s.rule_id]
    return get_subtypes_for_rule_ids(rule_ids)


# ─────────────────────────────────────────────────────────────────────────────
# 单年单类事件分析
# ─────────────────────────────────────────────────────────────────────────────

def _analyze_single_event(
    event_type: str,
    year: int,
    liunian_info: dict,
    dayun_item,
    day_stem: str,
    day_branch: str,
    gender: str,
    yongshen_favor: list[str],
    yongshen_avoid: list[str],
    wx_scores: dict[str, float],
    notable_months: list[int],
    dm_tier: str,
) -> EventResult:
    if event_type == "marriage":
        risk_sigs, opp_sigs = _signals_marriage(
            year, liunian_info, dayun_item, day_branch,
            gender, yongshen_favor, notable_months, dm_tier,
        )
    elif event_type == "wealth":
        risk_sigs, opp_sigs = _signals_wealth(
            year, liunian_info, dayun_item,
            yongshen_favor, yongshen_avoid, wx_scores, notable_months,
        )
    elif event_type == "property":
        risk_sigs, opp_sigs = _signals_property(
            year, liunian_info, dayun_item, day_branch,
            yongshen_favor, notable_months,
        )
    elif event_type == "career":
        risk_sigs, opp_sigs = _signals_career(
            year, liunian_info, dayun_item,
            yongshen_favor, dm_tier, notable_months,
        )
    elif event_type == "health":
        risk_sigs, opp_sigs = _signals_health(
            year, liunian_info, dayun_item, day_stem,
            yongshen_avoid, wx_scores, notable_months,
        )
    else:
        risk_sigs, opp_sigs = [], []

    risk_level, opp_level, conf = _compute_levels(risk_sigs, opp_sigs)
    all_sigs = risk_sigs + opp_sigs
    subtypes  = _infer_subtypes(event_type, risk_sigs, opp_sigs)

    # 从规则库获取素材
    from services.event_rule_matcher import get_materials_for_signals
    rule_ids = [s.rule_id for s in all_sigs if s.rule_id]
    materials = get_materials_for_signals(rule_ids)

    return EventResult(
        event_type=event_type,
        year=year,
        risk_level=risk_level,  # type: ignore[arg-type]
        opportunity_level=opp_level,  # type: ignore[arg-type]
        confidence=conf,
        main_judgment=_main_judgment(event_type, risk_level, opp_level, year, subtypes),
        trigger_summary=_trigger_summary(all_sigs),
        event_subtypes=subtypes,
        signals=all_sigs,
        possible_manifestations=materials.get("manifestations", []),
        key_months=notable_months[:4],
        omens=materials.get("omens", []),
        advice=materials.get("advice", []),
        classical_notes=materials.get("classical_notes", []),
        avoid_overclaim=materials.get("avoid_overclaim"),
    )


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────

def analyze_year_events(
    verify_response,
    birth_dt: datetime,
    year: int,
    event_types: list[str],
    gender: str = "male",
) -> dict[str, "EventResult"]:
    """
    分析指定年份的多类事件信号。

    参数:
        verify_response: VerifyResponse（来自 bazi_engine_service.calculate()）
        birth_dt:        出生日期（用于计算年龄/大运起点定位）
        year:            目标流年
        event_types:     要分析的事件类别列表
        gender:          "male" / "female"
    返回:
        dict[event_type, EventResult]
    """
    vr  = verify_response
    rp  = vr.pillars_primary
    day_stem   = rp.day.stem
    day_branch = rp.day.branch

    favor: list[str] = list(vr.yongshen.favor) if vr.yongshen and vr.yongshen.favor else []
    avoid: list[str] = list(vr.yongshen.avoid) if vr.yongshen and vr.yongshen.avoid else []
    wx_scores = _wxscore_dict(vr)
    dm_tier   = (vr.day_master_strength.tier if vr.day_master_strength else "") or ""

    # 流年干支 + 十神/冲 信息
    year_stem, year_branch = _year_ganzhi(year)
    liunian_items = compute_liunian(day_stem, day_branch, year, year + 1)
    liunian_info  = liunian_items[0] if liunian_items else {}

    # 补充 flow_wuxing（STEM_ELEMENT 返回 (element, yin_yang) 元组，取第一元）
    if not liunian_info.get("flow_wuxing"):
        liunian_info = dict(liunian_info)
        _elem_tuple = STEM_ELEMENT.get(year_stem)
        liunian_info["flow_wuxing"] = _elem_tuple[0] if _elem_tuple else ""

    # 大运信息
    dayun_item = _get_dayun_for_year(vr.dayun, year)

    # 用神旺月
    notable_months = _compute_notable_months(favor)

    results: dict[str, EventResult] = {}
    for et in event_types:
        try:
            results[et] = _analyze_single_event(
                event_type=et,
                year=year,
                liunian_info=liunian_info,
                dayun_item=dayun_item,
                day_stem=day_stem,
                day_branch=day_branch,
                gender=gender,
                yongshen_favor=favor,
                yongshen_avoid=avoid,
                wx_scores=wx_scores,
                notable_months=notable_months,
                dm_tier=dm_tier,
            )
        except Exception as exc:
            logger.error("analyze_year_events(%s, %s) failed: %s", year, et, exc)

    return results


def analyze_multi_year_trend(
    verify_response,
    birth_dt: datetime,
    years: list[int],
    gender: str = "male",
) -> "MultiYearTrendResponse":
    """
    分析多年趋势，返回时间线摘要。
    """
    summaries: list[YearSummary] = []
    theme_parts: list[str] = []

    for year in years:
        try:
            events = analyze_year_events(
                verify_response, birth_dt, year,
                ["marriage", "wealth", "property", "career", "health"],
                gender,
            )
            # 找出风险最高或机会最高的事件作为年份主题
            RISK_ORD = {"high": 5, "medium_high": 4, "medium": 3, "low": 2, "none": 1}
            OPP_ORD  = {"high": 5, "medium": 3, "low": 2, "none": 1}

            best_risk = max(events.values(), key=lambda e: RISK_ORD.get(e.risk_level, 0)) \
                if events else None
            best_opp  = max(events.values(), key=lambda e: OPP_ORD.get(e.opportunity_level, 0)) \
                if events else None

            # 选代表性事件
            representative = None
            if best_risk and RISK_ORD.get(best_risk.risk_level, 0) >= 3:
                representative = best_risk
            elif best_opp and OPP_ORD.get(best_opp.opportunity_level, 0) >= 3:
                representative = best_opp
            else:
                representative = list(events.values())[0] if events else None

            top_events: list[str] = []
            for e in list(events.values())[:3]:
                top_events.extend(e.event_subtypes[:2])
            top_events = list(dict.fromkeys(top_events))[:4]  # dedup

            max_risk  = max((e.risk_level for e in events.values()), key=lambda r: RISK_ORD.get(r, 0)) \
                if events else "none"
            max_opp   = max((e.opportunity_level for e in events.values()), key=lambda o: OPP_ORD.get(o, 0)) \
                if events else "none"

            avg_score = int(sum(
                (_RISK_SCORE_MAP.get(e.risk_level, 60) + _OPP_SCORE_MAP.get(e.opportunity_level, 50)) // 2
                for e in events.values()
            ) / max(len(events), 1))

            year_stem, _ = _year_ganzhi(year)
            year_stem2, year_branch2 = _year_ganzhi(year)
            ganzhi = year_stem2 + year_branch2

            theme = representative.main_judgment if representative else f"{year}年运势平稳"
            theme_short_map = {
                "婚姻感情整体平稳": "感情稳定",
                "婚姻感情压力较明显": "婚姻压力",
                "婚姻感情进入高风险": "婚姻动荡",
                "财务财运存在一定压力": "财运波动",
                "财务财运进入高风险": "财运压力",
                "房产居住存在一定压力": "置业动象",
                "事业职场同时存在发展机遇": "事业机遇",
                "健康状态压力较明显": "健康须防",
            }
            for kw, short in theme_short_map.items():
                if kw in theme:
                    theme = short
                    break
            else:
                # 取 main_judgment 前6字
                if representative:
                    jt = representative.main_judgment
                    theme = jt[5:11] if len(jt) > 11 else jt[:8]

            theme_parts.append(f"{year}年{theme}")
            summaries.append(YearSummary(
                year=year,
                year_ganzhi=ganzhi,
                main_theme=representative.main_judgment if representative else f"{year}年运势平稳",
                top_events=top_events,
                risk=max_risk,  # type: ignore[arg-type]
                opportunity=max_opp,  # type: ignore[arg-type]
                annual_score=avg_score,
            ))
        except Exception as exc:
            logger.error("analyze_multi_year_trend year=%s failed: %s", year, exc)

    timeline_summary = "，".join(theme_parts) + "。" if theme_parts else ""

    from app.schemas.event_prediction import MultiYearTrendResponse as _MTR
    return _MTR(
        case_id="",   # caller fills this in
        timeline_summary=timeline_summary,
        summaries=summaries,
    )


def compute_overall_year_score(events: dict[str, "EventResult"]) -> int:
    """根据各类事件结果计算年份综合评分 0-100"""
    if not events:
        return 60
    scores = []
    for e in events.values():
        rs = _RISK_SCORE_MAP.get(e.risk_level, 60)
        os = _OPP_SCORE_MAP.get(e.opportunity_level, 50)
        scores.append((rs + os) // 2)
    return int(sum(scores) / len(scores))
