"""
services/bazi_engine/geju.py — 格局判断（M1 任务 1.10）

支持10种格局（月干透干取格，正格为主）:
  正格（8种）: 正官/七杀/正印/偏印/正财/偏财/食神/伤官
  特殊外格（2种）: 从旺/专旺

算法:
  1. 月令地支取藏干（主气）→ 对应天干五行
  2. 年月日时天干中，与月令主气五行相同的天干 → 透干
  3. 以透干与日主的十神关系 → 格局名称
  4. 若无透干 → 以月支主气直接确定格局
  5. 外格（从旺/专旺）: 五行分布极端（某一元素≥70%）时判入

本实现：只判成格，不判破格（破格在 M3 补充）
"""
from __future__ import annotations

from services.bazi_engine.tables import (
    BRANCH_HIDDEN_STEMS,
    STEM_ELEMENT,
    get_ten_god,
)

# ──────────────────────────────────────────────────────────────────────────────
# 格局元数据
# ──────────────────────────────────────────────────────────────────────────────

GEJU_META: dict[str, dict] = {
    "正官格": {"type": "inner", "note": "官清印顺，利仕途功名"},
    "七杀格": {"type": "inner", "note": "杀需有制，有制则威权赫赫"},
    "正印格": {"type": "inner", "note": "印旺生身，利学业才德"},
    "偏印格": {"type": "inner", "note": "枭印逢食则化，主技艺出众"},
    "正财格": {"type": "inner", "note": "财有根透，日主有力能承财"},
    "偏财格": {"type": "inner", "note": "偏财主横财，利商贸"},
    "食神格": {"type": "inner", "note": "食神生财，才学丰富"},
    "伤官格": {"type": "inner", "note": "伤官见官凶，无官则清高"},
    "从旺格": {"type": "outer", "note": "日强极旺，顺势而为"},
    "专旺格": {"type": "outer", "note": "五行专一极旺，顺之则吉"},
    "建禄格": {"type": "special", "note": "月令为日主帝旺，日主极强"},
    "羊刃格": {"type": "special", "note": "月令为日主刃旺，刚烈之象"},
    "普通格": {"type": "none",  "note": "五行较均衡，无明显格局"},
}

# 正官/七杀 等 十神 → 格局名映射
_SHISHEN_TO_GEJU: dict[str, str] = {
    "正官": "正官格",
    "七杀": "七杀格",
    "正印": "正印格",
    "偏印": "偏印格",
    "正财": "正财格",
    "偏财": "偏财格",
    "食神": "食神格",
    "伤官": "伤官格",
    "比肩": "建禄格",
    "劫财": "羊刃格",
}

# 月支 → 建禄/羊刃对应的天干
_JIANLU_STEM: dict[str, str] = {
    "寅": "甲", "卯": "乙",   # 木
    "午": "丙戊", "巳": "丙",  # 火
    "申": "庚", "酉": "辛",   # 金
    "子": "壬", "亥": "癸",   # 水
    "辰": "戊", "戌": "戊",   # 土
    "丑": "己", "未": "己",
}


# ──────────────────────────────────────────────────────────────────────────────
# 主函数
# ──────────────────────────────────────────────────────────────────────────────

def compute_geju(
    year_stem: str,
    month_stem: str,
    month_branch: str,
    day_stem: str,
    hour_stem: str,
    wuxing_scores: dict[str, float] | None = None,  # 五行得分，用于外格判断
) -> dict:
    """
    判断命局格局.

    Parameters:
        year_stem, month_stem, month_branch, day_stem, hour_stem: 四柱干支
        wuxing_scores: dict[element, 0-100 float]（来自 wuxing.py）

    Returns:
    {
        "name": str,           # 格局名称
        "type": str,           # inner/outer/special/none
        "month_qi": str,       # 月令主气天干
        "toukan_stem": str,    # 透干（如有）
        "ten_god": str,        # 月令主气对日主的十神
        "note": str,           # 格局说明
        "confident": bool,     # 是否明确成格
    }
    """
    # 1. 月令主气（取藏干权重最大的那个）
    hidden = BRANCH_HIDDEN_STEMS.get(month_branch, [])
    if not hidden:
        return _no_geju("月支藏干数据缺失")

    # 主气 = 权重最大的藏干
    main_hidden_stem, main_weight = max(hidden, key=lambda x: x[1])
    month_qi = main_hidden_stem

    # 2. 月令主气五行
    month_qi_elem, _ = STEM_ELEMENT.get(month_qi, ("?", "?"))

    # 3. 透干检查：四柱天干中与月令主气同元素者
    candidate_stems = [year_stem, month_stem, hour_stem]   # 不含日干（日干是主体）
    toukan_stem: str | None = None
    for s in candidate_stems:
        s_elem, _ = STEM_ELEMENT.get(s, ("?", "?"))
        if s_elem == month_qi_elem:
            toukan_stem = s
            break

    # 取格依据
    ref_stem = toukan_stem if toukan_stem else month_qi

    # 4. 十神关系 → 格局
    ten_god = get_ten_god(day_stem, ref_stem)
    geju_name = _SHISHEN_TO_GEJU.get(ten_god, "普通格")

    # 5. 外格判断（覆盖内格）
    if wuxing_scores and geju_name in ("普通格", "建禄格", "羊刃格"):
        outer = _check_outer_geju(wuxing_scores, day_stem, month_stem, month_branch)
        if outer:
            geju_name = outer

    meta = GEJU_META.get(geju_name, GEJU_META["普通格"])

    return {
        "name": geju_name,
        "type": meta["type"],
        "month_qi": month_qi,
        "toukan_stem": toukan_stem,
        "ten_god": ten_god,
        "note": meta["note"],
        "confident": geju_name != "普通格",
    }


def _no_geju(reason: str = "") -> dict:
    return {
        "name": "普通格",
        "type": "none",
        "month_qi": "",
        "toukan_stem": None,
        "ten_god": "",
        "note": reason or GEJU_META["普通格"]["note"],
        "confident": False,
    }


def _check_outer_geju(
    wuxing_scores: dict[str, float],
    day_stem: str,
    month_stem: str,
    month_branch: str,
) -> str | None:
    """
    判断外格（从旺/专旺）
    规则: 某一五行得分 ≥ 70 且日主同元素 → 从旺/专旺
    """
    total = sum(wuxing_scores.values()) or 1.0
    day_elem, _ = STEM_ELEMENT.get(day_stem, ("?", "?"))
    for elem, score in wuxing_scores.items():
        pct = score / total
        if pct >= 0.70:
            if elem == day_elem:
                return "从旺格"
            else:
                return "专旺格"
    return None
