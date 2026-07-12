"""
services/bazi_engine/geju.py — 格局判断（M1 任务 1.10）

支持10种格局（月干透干取格，正格为主）:
  正格（8种）: 正官/七杀/正印/偏印/正财/偏财/食神/伤官
  特殊外格（2种）: 从旺/专旺

算法:
  1. 月令地支取藏干（主气/司令）→ 对应天干五行
  2. 子平透干见格链（见 _resolve_ref_stem）：月干藏干透出 > 月干同气 > 年/时藏干透出 > 司令定正偏
  3. 以参考天干与日主的十神关系 → 格局名称
  4. 比劫非司令时不夺格；年/时比劫透出藏干时仍以司令正格为准
  5. 外格（从旺/专旺）: 五行分布极端（某一元素≥70%）时判入

本实现：支持成格判断和破格检测（M3 补充）
  破格规则:
    正官格: 伤官透干 / 官杀混杂
    七杀格: 食神缺失（无制杀）
    正印格: 财星过旺（财克印）
    正财格: 比劫多（比劫争财）
    偏财格: 比劫劫财多
    食神格: 偏印（枭印）透干夺食
    伤官格: 正官透干（伤官见官）
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
    # ── 正格（八格）──────────────────────────────────────────────────────
    "正官格": {"type": "inner", "note": "官清印顺，利仕途功名"},
    "七杀格": {"type": "inner", "note": "杀需有制，有制则威权赫赫"},
    "正印格": {"type": "inner", "note": "印旺生身，利学业才德"},
    "偏印格": {"type": "inner", "note": "枭印逢食则化，主技艺出众"},
    "正财格": {"type": "inner", "note": "财有根透，日主有力能承财"},
    "偏财格": {"type": "inner", "note": "偏财主横财，利商贸"},
    "食神格": {"type": "inner", "note": "食神生财，才学丰富"},
    "伤官格": {"type": "inner", "note": "伤官见官凶，无官则清高"},
    # ── 外格：从旺/专旺及五行专旺细分 ──────────────────────────────────
    "从旺格": {"type": "outer", "note": "日主元素极旺（≥70%），顺势而为，宜助旺忌克"},
    "专旺格": {"type": "outer", "note": "五行专一极旺，顺之则吉，逆之则凶"},
    "曲直格": {"type": "outer", "note": "木日主亥卯未三合、仲春绝金，仁寿之格；亦可用木气≥70%判定"},
    "炎上格": {"type": "outer", "note": "火气专旺（≥70%），主礼智名显，利南方"},
    "稼穑格": {"type": "outer", "note": "土气专旺（≥70%），主信厚诚实，守成持业"},
    "从革格": {"type": "outer", "note": "金气专旺（≥70%），主威武刚烈，利西方金融"},
    "润下格": {"type": "outer", "note": "水气专旺（≥70%），主智谋机变，利北方"},
    # ── 从格（日主极弱，顺从最强之神）────────────────────────────────
    "从财格": {"type": "cong", "note": "日主极弱，全局财星最旺，宜顺从理财，忌比劫"},
    "从官杀格": {"type": "cong", "note": "日主极弱，全局官杀最旺，宜服从管理，利官场"},
    "从儿格": {"type": "cong", "note": "日主极弱，食伤广布，专事创作技艺"},
    "从势格": {"type": "cong", "note": "日主极弱，财官食伤均衡，顺势应变"},
    # ── 特殊格 ───────────────────────────────────────────────────────
    "建禄格": {"type": "special", "note": "月令为日主临官位（禄），日主有根有力"},
    "月刃格": {"type": "special", "note": "月令为日主刃旺（古籍亦称羊刃），刚烈之象"},
    "普通格": {"type": "none", "note": "五行较均衡，无明显格局"},
    # ── 化气格（天干五合，日主参与，月支归属五行匹配）────────────────
    "化土格": {"type": "huaqi", "note": "甲己化土，日主参与五合，月支土气归属"},
    "化金格": {"type": "huaqi", "note": "乙庚化金，日主参与五合，月支金气归属"},
    "化水格": {"type": "huaqi", "note": "丙辛化水，日主参与五合，月支水气归属"},
    "化木格": {"type": "huaqi", "note": "丁壬化木，日主参与五合，月支木气归属"},
    "化火格": {"type": "huaqi", "note": "戊癸化火，日主参与五合，月支火气归属"},
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
    "劫财": "月刃格",
}

# 曲直仁寿格：亥卯未三合 + 仲春 + 绝金（千里命稿口径）
_QUZHI_SANHE_BRANCHES = frozenset({"亥", "卯", "未"})
_SPRING_MONTH_BRANCHES = frozenset({"寅", "卯", "辰"})
_METAL_STEMS = frozenset({"庚", "辛"})
_METAL_BRANCHES = frozenset({"申", "酉"})


def _chart_has_metal(stems: list[str], branches: list[str]) -> bool:
    """四柱天干或地支（含藏干主气）见金，则非曲直绝金格。"""
    if any(s in _METAL_STEMS for s in stems if s):
        return True
    for br in branches:
        if not br:
            continue
        if br in _METAL_BRANCHES:
            return True
        for hs, weight in BRANCH_HIDDEN_STEMS.get(br, []):
            if hs in _METAL_STEMS and weight >= 0.3:
                return True
    return False


def _check_quzhi_geju(
    day_stem: str,
    month_branch: str,
    year_branch: str | None,
    day_branch: str | None,
    hour_branch: str | None,
    all_stems: list[str],
) -> bool:
    """
    曲直仁寿格（千里命稿 / 子平外格）结构判定。

    条件：木日主；月支寅卯辰；四柱地支齐见亥卯未；四柱绝金。
    用于补充五行得分未达 70% 但三合木局已成之经典命例（如千里命稿例8/52）。
    """
    day_elem, _ = STEM_ELEMENT.get(day_stem, ("?", "?"))
    if day_elem != "wood":
        return False
    if month_branch not in _SPRING_MONTH_BRANCHES:
        return False
    branches = [b for b in (year_branch, month_branch, day_branch, hour_branch) if b]
    if not _QUZHI_SANHE_BRANCHES.issubset(set(branches)):
        return False
    return not _chart_has_metal(all_stems, branches)


_SUMMER_MONTH_BRANCHES = frozenset({"巳", "午", "未"})
_WINTER_MONTH_BRANCHES = frozenset({"亥", "子", "丑"})
_YANSHANG_SANHE = frozenset({"寅", "午", "戌"})
_RUNXIA_SANHE = frozenset({"申", "子", "辰"})
_JIAXU_EARTH_HEAVY = frozenset({"辰", "戌", "丑", "未"})
_CONGGE_SANHE = frozenset({"巳", "酉", "丑"})


def _branches_full(year_branch, month_branch, day_branch, hour_branch) -> set[str]:
    return {b for b in (year_branch, month_branch, day_branch, hour_branch) if b}


def _check_yanshang_geju(
    day_stem: str,
    month_branch: str,
    year_branch: str | None,
    day_branch: str | None,
    hour_branch: str | None,
) -> bool:
    """炎上格：火日主；夏月；寅午戌三合全见。"""
    day_elem, _ = STEM_ELEMENT.get(day_stem, ("?", "?"))
    if day_elem != "fire":
        return False
    if month_branch not in _SUMMER_MONTH_BRANCHES:
        return False
    return _YANSHANG_SANHE.issubset(_branches_full(year_branch, month_branch, day_branch, hour_branch))


def _check_runxia_geju(
    day_stem: str,
    month_branch: str,
    year_branch: str | None,
    day_branch: str | None,
    hour_branch: str | None,
) -> bool:
    """润下格：水日主；冬月；申子辰三合全见。"""
    day_elem, _ = STEM_ELEMENT.get(day_stem, ("?", "?"))
    if day_elem != "water":
        return False
    if month_branch not in _WINTER_MONTH_BRANCHES:
        return False
    return _RUNXIA_SANHE.issubset(_branches_full(year_branch, month_branch, day_branch, hour_branch))


def _check_jiaxu_geju(
    day_stem: str,
    month_branch: str,
    year_branch: str | None,
    day_branch: str | None,
    hour_branch: str | None,
) -> bool:
    """稼穑格：土日主；四季月；辰戌丑未占其三以上。"""
    day_elem, _ = STEM_ELEMENT.get(day_stem, ("?", "?"))
    if day_elem != "earth":
        return False
    if month_branch not in _JIAXU_EARTH_HEAVY:
        return False
    brs = _branches_full(year_branch, month_branch, day_branch, hour_branch)
    return len(brs & _JIAXU_EARTH_HEAVY) >= 3


def _check_congge_structural(
    day_stem: str,
    month_branch: str,
    year_branch: str | None,
    day_branch: str | None,
    hour_branch: str | None,
    all_stems: list[str],
) -> bool:
    """从革格：金日主；巳酉丑三合；四柱绝木（对标曲直绝金）。"""
    day_elem, _ = STEM_ELEMENT.get(day_stem, ("?", "?"))
    if day_elem != "metal":
        return False
    if month_branch not in {"申", "酉", "戌"}:
        return False
    branches = list(_branches_full(year_branch, month_branch, day_branch, hour_branch))
    if not _CONGGE_SANHE.issubset(set(branches)):
        return False
    for s in all_stems:
        elem, _ = STEM_ELEMENT.get(s, ("?", "?"))
        if elem == "wood":
            return False
    for br in branches:
        for hs, _w in BRANCH_HIDDEN_STEMS.get(br, []):
            elem, _ = STEM_ELEMENT.get(hs, ("?", "?"))
            if elem == "wood":
                return False
    return True


def _derive_composite_geju(geju_name: str, ten_god: str, day_stem: str, month_stem: str) -> str | None:
    """衍生格命名（不替代八正格 name）。"""
    from services.bazi_engine.tables import get_ten_god as _gtg

    ms_god = _gtg(day_stem, month_stem)
    if geju_name == "伤官格" and ms_god in ("正印", "偏印"):
        return "伤官佩印格"
    if geju_name == "七杀格" and ms_god in ("正印", "偏印"):
        return "杀印相生格"
    if geju_name == "七杀格" and _gtg(day_stem, month_stem) == "食神" or ten_god == "食神":
        for s in (month_stem,):
            if _gtg(day_stem, s) == "食神":
                return "食神制杀格"
    if geju_name == "七杀格" and ms_god in ("正财", "偏财"):
        return "财滋弱杀格"
    return None


_JIANLU_BRANCH: dict[str, str] = {
    "甲": "寅",
    "乙": "卯",
    "丙": "巳",
    "丁": "午",
    "戊": "巳",
    "己": "午",
    "庚": "申",
    "辛": "酉",
    "壬": "亥",
    "癸": "子",
}
_YANGREN_BRANCH: dict[str, str] = {
    "甲": "卯",
    "乙": "寅",
    "丙": "午",
    "丁": "巳",
    "戊": "午",
    "己": "巳",
    "庚": "酉",
    "辛": "申",
    "壬": "子",
    "癸": "亥",
}


def _day_root_branches(day_stem: str) -> set[str]:
    """日主临官/帝旺地支（化气与建禄判断用）。"""
    branches: set[str] = set()
    if day_stem in _JIANLU_BRANCH:
        branches.add(_JIANLU_BRANCH[day_stem])
    if day_stem in _YANGREN_BRANCH:
        branches.add(_YANGREN_BRANCH[day_stem])
    return branches


# 月支 → 建禄/羊刃对应的天干（legacy reference）
_JIANLU_STEM: dict[str, str] = {
    "寅": "甲",
    "卯": "乙",  # 木
    "午": "丙戊",
    "巳": "丙",  # 火
    "申": "庚",
    "酉": "辛",  # 金
    "子": "壬",
    "亥": "癸",  # 水
    "辰": "戊",
    "戌": "戊",  # 土
    "丑": "己",
    "未": "己",
}

# 五合化气规则: frozenset({干A, 干B}) → (化出五行英文, 格局名称)
_WUHE_HUAQI: dict[frozenset, tuple[str, str]] = {
    frozenset({"甲", "己"}): ("earth", "化土格"),
    frozenset({"乙", "庚"}): ("metal", "化金格"),
    frozenset({"丙", "辛"}): ("water", "化水格"),
    frozenset({"丁", "壬"}): ("wood", "化木格"),
    frozenset({"戊", "癸"}): ("fire", "化火格"),
}

# 五合化气得地：命局见对应地支可成真化（滴天髓「逢五而化」口径）
_HUAQI_BRANCH_SEED: dict[frozenset, set[str]] = {
    frozenset({"甲", "己"}): {"辰", "戌"},
    frozenset({"乙", "庚"}): {"申", "酉"},
    frozenset({"丙", "辛"}): {"亥", "子"},
    frozenset({"丁", "壬"}): {"寅", "卯"},
    frozenset({"戊", "癸"}): {"巳", "午"},
}

# 克化关系: key=被克五行, value=克它的五行
_WUXING_KE_BY: dict[str, str] = {
    "earth": "wood",
    "metal": "fire",
    "water": "earth",
    "wood": "metal",
    "fire": "water",
}

# 相生关系: key=生者, value=被生者（a生b）
_WUXING_SHENG: dict[str, str] = {
    "wood": "fire",
    "fire": "earth",
    "earth": "metal",
    "metal": "water",
    "water": "wood",
}


def _hour_branch_guansha_override(
    day_stem: str,
    hour_branch: str | None,
    month_stem: str,
    month_qi: str,
    month_stem_in_hidden: bool,
) -> str | None:
    """
    月令透比劫司令时，时支本气为官杀可夺格（千里命稿 ZIP06 吴佩孚口径）。
    """
    if not day_stem or not hour_branch or not month_stem_in_hidden:
        return None
    m_tg = get_ten_god(day_stem, month_stem)
    if m_tg not in ("比肩", "劫财"):
        return None
    hidden_h = BRANCH_HIDDEN_STEMS.get(hour_branch, [])
    if not hidden_h:
        return None
    hour_main, _ = max(hidden_h, key=lambda x: x[1])
    if get_ten_god(day_stem, hour_main) not in ("七杀", "正官"):
        return None
    return hour_main


def _resolve_ref_stem(
    year_stem: str,
    month_stem: str,
    month_branch: str,
    hour_stem: str,
    day_stem: str = "",
    hour_branch: str | None = None,
) -> tuple[str, str, str | None]:
    """
    子平取格：确定用于定格局的参考天干。

    优先级（《子平真诠》透干见格 + 司令本位）：
      1. 月干为月令藏干透出（藏干完全一致；比劫非司令时不夺格）
      2. 月干五行在月令藏干中但未入库（同气月干，如亥月癸、子月壬）
      3. 年/时干为月令藏干透出
      4. 年/月/时干与司令同五行异干 → 以司令定正偏（如申月辛透取庚正财）
      5. 月令透比劫司令而时支本气为官杀 → 时支本气夺格（千里命稿势论）
      6. 否则取月令司令

    Returns:
        (ref_stem, month_qi, toukan_stem)
        toukan_stem: 实际参与取格的透干（若 ref 来自透干），否则 None
    """
    hidden = BRANCH_HIDDEN_STEMS.get(month_branch, [])
    if not hidden:
        return month_stem, month_stem, None

    month_qi, _ = max(hidden, key=lambda x: x[1])
    hidden_set = {h for h, _ in hidden}
    hidden_elems = {STEM_ELEMENT[h][0] for h in hidden_set if h in STEM_ELEMENT}
    month_qi_elem = STEM_ELEMENT.get(month_qi, ("?", "?"))[0]

    if month_stem in hidden_set:
        tg = get_ten_god(day_stem, month_stem) if day_stem else ""
        hour_ref = _hour_branch_guansha_override(day_stem, hour_branch, month_stem, month_qi, True)
        if hour_ref:
            return hour_ref, month_qi, hour_ref
        if month_stem == month_qi or tg not in ("比肩", "劫财"):
            return month_stem, month_qi, month_stem

    if month_stem not in hidden_set and month_stem in STEM_ELEMENT:
        if STEM_ELEMENT[month_stem][0] in hidden_elems:
            return month_stem, month_qi, month_stem

    for stem in (year_stem, hour_stem):
        if stem in hidden_set:
            tg = get_ten_god(day_stem, stem) if day_stem else ""
            if tg in ("比肩", "劫财"):
                continue
            return stem, month_qi, stem

    for stem in (year_stem, month_stem, hour_stem):
        stem_elem = STEM_ELEMENT.get(stem, ("?", "?"))[0]
        if stem_elem == month_qi_elem:
            if stem != month_qi:
                return month_qi, month_qi, stem
            return stem, month_qi, stem

    return month_qi, month_qi, None


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
    year_branch: str | None = None,  # N1.03 三合局检测
    day_branch: str | None = None,
    hour_branch: str | None = None,
) -> dict:
    """
    判断命局格局.

    Parameters:
        year_stem, month_stem, month_branch, day_stem, hour_stem: 四柱干支
        wuxing_scores: dict[element, 0-100 float]（来自 wuxing.py）
        year_branch, day_branch, hour_branch: 四柱地支（N1.03 三合局调整，可缺省）

    格局优先级链:
        1. 化气格（日主参与五合 + 月支归属五行匹配）
        2. 从旺格 / 专旺格（五行 ≥70%，极端分布）
        3. 三合全合 confidence 调整（不单独成格）
        4. 正格（月令透干/藏干）
        5. 建禄格 / 羊刃格（月令临官/帝旺）
        6. 普通格

    Returns:
    {
        "name": str,           # 格局名称
        "type": str,           # inner/outer/special/huaqi/cong/none
        "month_qi": str,       # 月令主气天干
        "toukan_stem": str,    # 透干（如有）
        "ten_god": str,        # 月令主气对日主的十神
        "note": str,           # 格局说明
        "confident": bool,     # 是否明确成格
        "confidence": float,   # 置信度 0-1
        "po_geju": dict,       # 破格信息
    }
    """
    # ── 五行得分：未传入时按四柱自动估算（pillar_direct / 结构从格用）────
    if wuxing_scores is None and year_branch and day_branch and hour_branch:
        from services.bazi_engine.wuxing import compute_wuxing as _cwx

        wuxing_scores = _cwx(
            year_stem,
            year_branch,
            month_stem,
            month_branch,
            day_stem,
            day_branch,
            hour_stem,
            hour_branch,
        ).scores_weighted

    # ── 1. 月令主气（取藏干权重最大的那个）─────────────────────────────
    hidden = BRANCH_HIDDEN_STEMS.get(month_branch, [])
    if not hidden:
        return _no_geju("月支藏干数据缺失")

    ref_stem, month_qi, toukan_stem = _resolve_ref_stem(
        year_stem, month_stem, month_branch, hour_stem, day_stem, hour_branch
    )

    # ── 四柱全部天干（化气格判断需含日干）────────────────────────────────
    all_stems_full = [year_stem, month_stem, day_stem, hour_stem]

    # ══════════════════════════════════════════════════════════════════════
    # 优先级 1: 化气格（N1.02）——高于一切外格/内格
    # ══════════════════════════════════════════════════════════════════════
    huaqi = _check_huaqi(
        all_stems_full,
        month_branch,
        day_stem=day_stem,
        day_branch=day_branch,
        hour_branch=hour_branch,
        year_branch=year_branch,
    )
    if huaqi["is_huaqi"]:
        geju_name = huaqi["huaqi_name"]
        ten_god = ""  # 化气格不以月令十神取格
        confidence = huaqi["confidence"]
        meta = GEJU_META.get(geju_name, GEJU_META["普通格"])
    elif (
        year_branch
        and day_branch
        and hour_branch
        and _check_yanshang_geju(day_stem, month_branch, year_branch, day_branch, hour_branch)
    ):
        geju_name = "炎上格"
        ten_god = ""
        confidence = 0.82
        meta = GEJU_META.get("炎上格", GEJU_META["曲直格"])
    elif (
        year_branch
        and day_branch
        and hour_branch
        and _check_runxia_geju(day_stem, month_branch, year_branch, day_branch, hour_branch)
    ):
        geju_name = "润下格"
        ten_god = ""
        confidence = 0.82
        meta = GEJU_META.get("润下格", GEJU_META["曲直格"])
    elif (
        year_branch
        and day_branch
        and hour_branch
        and _check_jiaxu_geju(day_stem, month_branch, year_branch, day_branch, hour_branch)
    ):
        geju_name = "稼穑格"
        ten_god = ""
        confidence = 0.80
        meta = GEJU_META.get("稼穑格", GEJU_META["曲直格"])
    elif (
        year_branch
        and day_branch
        and hour_branch
        and _check_congge_structural(day_stem, month_branch, year_branch, day_branch, hour_branch, all_stems_full)
    ):
        geju_name = "从革格"
        ten_god = ""
        confidence = 0.82
        meta = GEJU_META.get("从革格", GEJU_META["曲直格"])
    elif (
        year_branch
        and day_branch
        and hour_branch
        and _check_quzhi_geju(day_stem, month_branch, year_branch, day_branch, hour_branch, all_stems_full)
    ):
        geju_name = "曲直格"
        ten_god = ""
        confidence = 0.82
        meta = GEJU_META["曲直格"]
    elif _YANGREN_BRANCH.get(day_stem) == month_branch:
        geju_name = "月刃格"
        ten_god = "劫财"
        confidence = 0.80
        meta = GEJU_META["月刃格"]
    elif _JIANLU_BRANCH.get(day_stem) == month_branch:
        geju_name = "建禄格"
        ten_god = "比肩"
        confidence = 0.80
        meta = GEJU_META["建禄格"]
    else:
        # ── 3. 十神关系 → 格局（正常取格链）──────────────────────────
        ten_god = get_ten_god(day_stem, ref_stem)
        geju_name = _SHISHEN_TO_GEJU.get(ten_god, "普通格")
        # 非临官/刃月不得因月令比劫十神贴建禄/月刃标签
        if geju_name in ("建禄格", "月刃格"):
            geju_name = "普通格"

        # ══════════════════════════════════════════════════════════════
        # 优先级 2: 外格判断（覆盖建禄/羊刃/普通格）
        # ══════════════════════════════════════════════════════════════
        if wuxing_scores and geju_name in ("普通格", "建禄格", "月刃格"):
            outer = _check_outer_geju(wuxing_scores, day_stem, month_stem, month_branch, hour_stem)
            if outer:
                geju_name = outer

        meta = GEJU_META.get(geju_name, GEJU_META["普通格"])

        # ── 置信度计算（N1.01 修订规则）───────────────────────────────
        day_elem, _ = STEM_ELEMENT.get(day_stem, ("?", "?"))
        total_wx = sum(wuxing_scores.values()) if wuxing_scores else 1.0

        if meta["type"] == "outer":
            # 动态置信度：取主导五行比例计算
            if wuxing_scores:
                dominant_elem = max(wuxing_scores, key=lambda k: wuxing_scores.get(k) or 0.0)
                ratio = wuxing_scores[dominant_elem] / total_wx
                if dominant_elem == day_elem:
                    confidence = min(0.5 + ratio * 0.5, 0.95)  # 从旺格类（同气）
                else:
                    confidence = min(0.4 + ratio * 0.4, 0.85)  # 专旺格类（异气）
            else:
                confidence = 0.75
        elif meta["type"] == "cong":
            confidence = 0.70
        elif meta["type"] == "special":  # 建禄格 / 月刃格
            confidence = 0.80
        elif toukan_stem:
            confidence = 0.85  # 正格透干成格
        elif geju_name != "普通格":
            confidence = 0.65  # 正格无透干靠藏干
        else:
            confidence = 0.40  # 普通格

    # 外格/从格可覆盖正格（滴天髓从象：财官势旺而日主无根）
    if not huaqi["is_huaqi"] and wuxing_scores and meta.get("type") == "inner" and geju_name not in ("曲直格",):
        outer = _check_outer_geju(wuxing_scores, day_stem, month_stem, month_branch, hour_stem)
        if outer:
            geju_name = outer
            meta = GEJU_META.get(geju_name, GEJU_META["普通格"])
            if meta["type"] == "cong":
                confidence = 0.70
            elif meta["type"] == "outer" and wuxing_scores:
                day_elem, _ = STEM_ELEMENT.get(day_stem, ("?", "?"))
                total_wx = sum(wuxing_scores.values()) or 1.0
                dominant_elem = max(wuxing_scores, key=lambda k: wuxing_scores.get(k) or 0.0)
                ratio = wuxing_scores[dominant_elem] / total_wx
                if dominant_elem == day_elem:
                    confidence = min(0.5 + ratio * 0.5, 0.95)
                else:
                    confidence = min(0.4 + ratio * 0.4, 0.85)
        elif year_branch and day_branch and hour_branch:
            struct = _check_sanhe_cong_geju(
                day_stem,
                year_stem,
                month_stem,
                hour_stem,
                year_branch,
                month_branch,
                day_branch,
                hour_branch,
                wuxing_scores,
            ) or _check_structural_cong_geju(
                day_stem,
                year_stem,
                month_stem,
                hour_stem,
                year_branch,
                month_branch,
                day_branch,
                hour_branch,
                wuxing_scores,
            )
            if struct:
                geju_name = struct
                meta = GEJU_META.get(geju_name, GEJU_META["普通格"])
                confidence = 0.68

    # 外格（专旺/从旺）可覆盖建禄/羊刃/普通格 — 与 else 分支内逻辑一致
    if not huaqi["is_huaqi"] and wuxing_scores and geju_name in ("普通格", "建禄格", "月刃格"):
        outer = _check_outer_geju(wuxing_scores, day_stem, month_stem, month_branch, hour_stem)
        if outer:
            geju_name = outer
            meta = GEJU_META.get(geju_name, GEJU_META["普通格"])
            day_elem, _ = STEM_ELEMENT.get(day_stem, ("?", "?"))
            total_wx = sum(wuxing_scores.values()) or 1.0
            dominant_elem = max(wuxing_scores, key=lambda k: wuxing_scores.get(k) or 0.0)
            ratio = wuxing_scores[dominant_elem] / total_wx
            if dominant_elem == day_elem:
                confidence = min(0.5 + ratio * 0.5, 0.95)
            else:
                confidence = min(0.4 + ratio * 0.4, 0.85)

    # ══════════════════════════════════════════════════════════════════════
    # 优先级 3: 三合全合 confidence 调整（N1.03）
    # ══════════════════════════════════════════════════════════════════════
    if year_branch and day_branch and hour_branch:
        try:
            from services.bazi_engine.relations import get_branch_relations as _gbr

            day_elem_adj, _ = STEM_ELEMENT.get(day_stem, ("?", "?"))
            sanhe_list = [
                r for r in _gbr(year_branch, month_branch, day_branch, hour_branch) if r["type"] == "三合全合"
            ]
            for sanhe in sanhe_list:
                sanhe_elem = sanhe.get("element", "")
                if not sanhe_elem or day_elem_adj == "?":
                    continue
                if sanhe_elem == day_elem_adj:
                    # 三合五行 == 日主五行 → 日主得势
                    confidence = min(confidence * 1.1, 0.95)
                elif _WUXING_SHENG.get(sanhe_elem) == day_elem_adj:
                    # 三合五行 生 日主五行 → 日主得生
                    confidence = min(confidence * 1.05, 0.95)
                elif _WUXING_KE_BY.get(day_elem_adj) == sanhe_elem:
                    # 三合五行 克 日主五行 → 日主受制
                    confidence = max(confidence * 0.85, 0.0)
        except Exception:
            pass  # 三合检测失败不影响主流程

    # ── 破格判断 ──────────────────────────────────────────────────────────
    po = check_po_geju(geju_name, all_stems_full, day_stem, wuxing_scores)
    derived_geju = _derive_composite_geju(geju_name, ten_god, day_stem, month_stem)

    return {
        "name": geju_name,
        "derived_geju": derived_geju,
        "type": meta["type"],
        "month_qi": month_qi,
        "toukan_stem": toukan_stem,
        "ten_god": ten_god,
        "note": meta["note"],
        "confident": geju_name != "普通格",
        "confidence": confidence if not po["broken"] else max(0.0, confidence - 0.3),
        "po_geju": po,
    }


# ──────────────────────────────────────────────────────────────────────────────
# 化气格判定（N1.02）
# ──────────────────────────────────────────────────────────────────────────────


def _huaqi_blocked_by_branch_ke(
    ke_elem: str,
    month_branch: str,
    day_branch: str | None = None,
    hour_branch: str | None = None,
    min_weight: float = 0.5,
) -> bool:
    """日支/时支藏干本气克化神（如化土遇卯中乙木）→ 合而不化；月令藏干不单独破格。"""
    for br in (day_branch, hour_branch):
        if not br:
            continue
        for hs, weight in BRANCH_HIDDEN_STEMS.get(br, []):
            if weight < min_weight:
                continue
            elem, _ = STEM_ELEMENT.get(hs, ("?", "?"))
            if elem == ke_elem:
                return True
    return False


def _check_huaqi(
    stems: list[str],  # [year_stem, month_stem, day_stem, hour_stem] 必须含日干
    month_branch: str,
    day_stem: str | None = None,
    day_branch: str | None = None,
    hour_branch: str | None = None,
    year_branch: str | None = None,
) -> dict:
    """
    化气格判定（D1 修订标准）.

    条件：
      1. day_stem 与某一柱天干（月/年/时）成天干五合
      2. 月支主气五行 == 化出五行，或命局见五合化气得地地支（滴天髓逢辰而化）

    confidence 规则:
      基础 0.70；命局四柱天干+月支主气中无任何元素克化出五行 → 加 0.10（上限 0.80）

    Returns:
        {"is_huaqi": bool, "huaqi_element": str, "huaqi_name": str, "confidence": float}
    """
    if len(stems) < 4:
        return {"is_huaqi": False, "huaqi_element": "", "huaqi_name": "", "confidence": 0.0}

    year_stem, month_stem, day_stem_val, hour_stem = stems

    # 日主坐临官/帝旺有根时不取化气（子平：有根不化）
    if day_stem and day_branch and day_stem_val == day_stem and day_branch in _day_root_branches(day_stem):
        return {"is_huaqi": False, "huaqi_element": "", "huaqi_name": "", "confidence": 0.0}

    # 月支主气五行
    hidden = BRANCH_HIDDEN_STEMS.get(month_branch, [])
    if not hidden:
        return {"is_huaqi": False, "huaqi_element": "", "huaqi_name": "", "confidence": 0.0}
    main_branch_stem = max(hidden, key=lambda x: x[1])[0]
    branch_elem, _ = STEM_ELEMENT.get(main_branch_stem, ("?", "?"))
    if branch_elem == "?":
        return {"is_huaqi": False, "huaqi_element": "", "huaqi_name": "", "confidence": 0.0}

    # 日主与其他柱天干五合检查（月日 / 年日 / 时日），其余三对不构成化气格
    partner_stems = [month_stem, year_stem, hour_stem]
    for other_stem in partner_stems:
        key = frozenset({day_stem_val, other_stem})
        if key in _WUHE_HUAQI:
            huaqi_elem, huaqi_name = _WUHE_HUAQI[key]
            seeds = _HUAQI_BRANCH_SEED.get(key, set())
            # 化气得地以日支为准（滴天髓「得一辰字」；年/时支逢之不足以单成格）
            has_seed = bool(seeds and day_branch and day_branch in seeds)
            # 月支主气五行等于化出五行，或命局见化气得地
            if branch_elem != huaqi_elem and not has_seed:
                continue
            ke_elem = _WUXING_KE_BY.get(huaqi_elem, "")
            if ke_elem and _huaqi_blocked_by_branch_ke(ke_elem, month_branch, day_branch, hour_branch):
                continue

            confidence = 0.70
            chart_elems: set[str] = set()
            for s in stems:
                e, _ = STEM_ELEMENT.get(s, ("?", "?"))
                if e != "?":
                    chart_elems.add(e)
            chart_elems.add(branch_elem)
            if ke_elem and ke_elem not in chart_elems:
                confidence += 0.10  # 无天干克化加成 → 0.80
            return {
                "is_huaqi": True,
                "huaqi_element": huaqi_elem,
                "huaqi_name": huaqi_name,
                "confidence": confidence,
            }

    return {"is_huaqi": False, "huaqi_element": "", "huaqi_name": "", "confidence": 0.0}


def _no_geju(reason: str = "") -> dict:
    return {
        "name": "普通格",
        "type": "none",
        "month_qi": "",
        "toukan_stem": None,
        "ten_god": "",
        "note": reason or GEJU_META["普通格"]["note"],
        "confident": False,
        "confidence": 0.0,
        "po_geju": {
            "broken": False,
            "reason": "",
            "severity": "none",
            "po_jiu": {"saved": False, "method": "", "note": ""},
        },
    }


# 五行专旺格：元素 → 格局名
_WUXING_SPECIAL_GEJU: dict[str, str] = {
    "wood": "曲直格",
    "fire": "炎上格",
    "earth": "稼穑格",
    "metal": "从革格",
    "water": "润下格",
}

# 十神 → 从格分类
_SHISHEN_CONG_GEJU: dict[str, str] = {
    "正财": "从财格",
    "偏财": "从财格",
    "正官": "从官杀格",
    "七杀": "从官杀格",
    "食神": "从儿格",
    "伤官": "从儿格",
}

_ELEM_REPR_STEM: dict[str, str] = {
    "wood": "甲",
    "fire": "丙",
    "earth": "戊",
    "metal": "庚",
    "water": "壬",
}


def _hour_stem_bijie_blocks_cong(day_stem: str, hour_stem: str) -> bool:
    """时干透出比肩/劫财则日主有党，不取从格（ZIP09 乙酉时助身）。"""
    if not day_stem or not hour_stem:
        return False
    tg = get_ten_god(day_stem, hour_stem)
    return tg in ("比肩", "劫财")


def _cong_geju_for_dominant(day_stem: str, elem: str) -> str | None:
    from services.bazi_engine.tables import get_ten_god as _gtg

    repr_stem = _ELEM_REPR_STEM.get(elem, "甲")
    ten_god = _gtg(day_stem, repr_stem)
    return _SHISHEN_CONG_GEJU.get(ten_god)


def _check_sanhe_cong_geju(
    day_stem: str,
    year_stem: str,
    month_stem: str,
    hour_stem: str,
    year_branch: str,
    month_branch: str,
    day_branch: str,
    hour_branch: str,
    wuxing_scores: dict[str, float],
) -> str | None:
    """
    三合全合 + 局五行势旺 → 从格/从旺（巳酉丑/亥卯未/寅午戌/申子辰）。
    时干比劫助身时阻断。从官杀：月令透官杀时单干即可，否则需双透或局五行≥45%。
    """
    if _hour_stem_bijie_blocks_cong(day_stem, hour_stem):
        return None

    from services.bazi_engine.relations import get_branch_relations as _gbr
    from services.bazi_engine.tables import get_ten_god as _gtg

    relations = _gbr(year_branch, month_branch, day_branch, hour_branch)
    sanhe_list = [r for r in relations if r.get("type") == "三合全合"]
    if not sanhe_list:
        return None

    day_elem, _ = STEM_ELEMENT.get(day_stem, ("?", "?"))
    total = sum(wuxing_scores.values()) or 1.0
    day_pct = (wuxing_scores.get(day_elem, 0.0) / total) if day_elem != "?" else 1.0
    if day_pct > 0.40:
        return None

    roots = _day_root_branches(day_stem)
    if any(br in roots for br in (year_branch, month_branch, hour_branch)):
        return None

    best = max(sanhe_list, key=lambda r: wuxing_scores.get(r.get("element") or "", 0.0))
    elem = best.get("element")
    if not elem:
        return None
    elem_pct = wuxing_scores.get(elem, 0.0) / total
    if elem_pct < 0.30:
        return None

    if elem == day_elem and elem_pct >= 0.45:
        return _WUXING_SPECIAL_GEJU.get(elem, "从旺格")

    cong = _cong_geju_for_dominant(day_stem, elem)
    if not cong:
        return None

    stem_roles = {
        "从官杀格": ("正官", "七杀"),
        "从财格": ("正财", "偏财"),
        "从儿格": ("食神", "伤官"),
    }
    target = stem_roles.get(cong, ())
    stem_hits = sum(1 for s in (year_stem, month_stem, hour_stem) if _gtg(day_stem, s) in target)
    month_in_target = _gtg(day_stem, month_stem) in target
    if cong == "从官杀格":
        min_stems = 1 if month_in_target else 2
    else:
        min_stems = 1
    if stem_hits < min_stems and elem_pct < 0.45:
        return None
    return cong


def _check_structural_cong_geju(
    day_stem: str,
    year_stem: str,
    month_stem: str,
    hour_stem: str,
    year_branch: str,
    month_branch: str,
    day_branch: str,
    hour_branch: str,
    wuxing_scores: dict[str, float],
) -> str | None:
    """
    滴天髓从象：四柱财官势旺、日主无强根时可单从结构判定从格。
    用于五行占比未达从格阈值但「四柱皆财」类命例（ZIP07）。
    """
    from services.bazi_engine.tables import get_ten_god as _gtg

    if _hour_stem_bijie_blocks_cong(day_stem, hour_stem):
        return None

    day_elem, _ = STEM_ELEMENT.get(day_stem, ("?", "?"))
    total = sum(wuxing_scores.values()) or 1.0
    day_pct = (wuxing_scores.get(day_elem, 0.0) / total) if day_elem != "?" else 1.0
    if day_pct > 0.25:
        return None

    roots = _day_root_branches(day_stem)
    for br in (year_branch, month_branch, hour_branch):
        if br in roots:
            return None

    wealth_pillars = 0
    guansha_pillars = 0
    has_help = False
    pillar_pairs = (
        (year_stem, year_branch, False),
        (month_stem, month_branch, False),
        (hour_stem, hour_branch, False),
        (day_stem, day_branch, True),
    )
    for stem, br, is_day_col in pillar_pairs:
        stem_tg = None if is_day_col else _gtg(day_stem, stem)
        hidden = BRANCH_HIDDEN_STEMS.get(br, [])
        main_stem = max(hidden, key=lambda x: x[1])[0] if hidden else None
        main_tg = _gtg(day_stem, main_stem) if main_stem else None

        pillar_wealth = stem_tg in ("正财", "偏财") or main_tg in ("正财", "偏财")
        pillar_guansha = stem_tg in ("正官", "七杀") or main_tg in ("正官", "七杀")
        pillar_help = (stem_tg in ("比肩", "劫财", "正印", "偏印")) or (main_tg in ("比肩", "劫财", "正印", "偏印"))

        if pillar_help:
            has_help = True
        if pillar_wealth:
            wealth_pillars += 1
        if pillar_guansha:
            guansha_pillars += 1

    if has_help:
        return None
    if wealth_pillars >= 3:
        return "从财格"
    if guansha_pillars >= 3:
        return "从官杀格"
    return None


def _check_outer_geju(
    wuxing_scores: dict[str, float],
    day_stem: str,
    month_stem: str,
    month_branch: str,
    hour_stem: str | None = None,
) -> str | None:
    """
    判断外格（从旺/专旺/五行专旺格/从格）

    优先级:
      1. 专旺系（某元素 ≥ 70%）→ 若与日主同气 → 从旺格/五行专旺格细分
                                  若非日主元素 → 五行专旺格细分
      2. 从格（日主元素 ≤ 10%，另一元素 ≥ 55%）
    """
    total = sum(wuxing_scores.values()) or 1.0
    day_elem, _ = STEM_ELEMENT.get(day_stem, ("?", "?"))
    bijie_blocked = bool(hour_stem and _hour_stem_bijie_blocks_cong(day_stem, hour_stem))

    # ── 1. 专旺判断（≥ 70%）────────────────────────────────────────────
    day_pct = (wuxing_scores.get(day_elem, 0.0) / total) if day_elem != "?" else 1.0
    for elem, score in wuxing_scores.items():
        pct = score / total
        if pct >= 0.70:
            if elem == day_elem:
                # 日主同元素专旺 → 从旺格（或带名称的专旺）
                return _WUXING_SPECIAL_GEJU.get(elem, "从旺格")
            # 日主弱且主导五行为财/官杀/食伤 → 从格，否则五行专旺
            cong = _cong_geju_for_dominant(day_stem, elem)
            if day_pct <= 0.20 and cong and not bijie_blocked:
                return cong
            return _WUXING_SPECIAL_GEJU.get(elem, "专旺格")

    # ── 2. 从格判断（日主极弱 ≤ 10%，他方 ≥ 55%）──────────────────────
    if bijie_blocked:
        return None
    if day_pct <= 0.10:
        # 找最旺的非日主元素
        strongest_elem = max(
            ((e, s) for e, s in wuxing_scores.items() if e != day_elem),
            key=lambda x: x[1],
            default=(None, 0.0),
        )
        if strongest_elem[0] and strongest_elem[1] / total >= 0.55:
            se = strongest_elem[0]
            cong_geju = _cong_geju_for_dominant(day_stem, se)
            if cong_geju:
                return cong_geju
            # 财官食均衡（无单一主导十神）→ 从势格
            return "从势格"

    return None


# ──────────────────────────────────────────────────────────────────────────────
# 破格判断（M3 补充）
# ──────────────────────────────────────────────────────────────────────────────


def check_po_geju(
    geju_name: str,
    all_stems: list[str],
    day_stem: str,
    wuxing_scores: dict[str, float] | None = None,
) -> dict:
    """
    检测命局格局是否被破坏（破格判断）.

    主要规则:
      正官格  → 伤官透干 / 官杀混杂（七杀同时出现）
      七杀格  → 无食神制杀
      正印格  → 财星过旺（财克印）
      偏印格  → 食神透干（枭神夺食，但偏印格自身反被牵制）
      正财格  → 比肩劫财多（比劫争财）
      偏财格  → 比肩劫财多
      食神格  → 偏印（枭神）透干
      伤官格  → 正官透干（伤官见官）

    Parameters:
        geju_name   : 已判定的格局名称
        all_stems   : 四柱天干 [年干, 月干, 日干, 时干]
        day_stem    : 日主天干
        wuxing_scores: 五行得分（用于强弱判断）

    Returns:
        {
            "broken": bool,     # 是否破格
            "reason": str,      # 破格原因
            "severity": str,    # none / minor / major
            "po_jiu": dict,     # 救应 {saved, method, note}
        }
    """

    def _po_result(
        broken: bool,
        reason: str = "",
        severity: str = "none",
        *,
        saved: bool = False,
        method: str = "",
        note: str = "",
    ) -> dict:
        return {
            "broken": broken,
            "reason": reason,
            "severity": severity,
            "po_jiu": {"saved": saved, "method": method, "note": note},
        }

    def _ten_gods_in_stems() -> list[str]:
        """获取除日主外所有天干的十神列表"""
        gods = []
        for s in all_stems:
            if s != day_stem:
                g = get_ten_god(day_stem, s)
                if g:
                    gods.append(g)
        return gods

    def _elem_ratio(elem: str) -> float:
        if not wuxing_scores:
            return 0.0
        total = sum(wuxing_scores.values()) or 1.0
        return wuxing_scores.get(elem, 0.0) / total

    def _day_elem() -> str:
        return STEM_ELEMENT.get(day_stem, ("?", "?"))[0]

    tgs = _ten_gods_in_stems()
    tg_set = set(tgs)

    # ── 正官格 ───────────────────────────────────────────────────────────
    if geju_name == "正官格":
        if "伤官" in tg_set:
            return _po_result(True, "伤官透干克制正官，官被伤破", "major")
        if "七杀" in tg_set:
            return _po_result(True, "官杀混杂，格局混乱", "major")

    # ── 七杀格 ───────────────────────────────────────────────────────────
    elif geju_name == "七杀格":
        has_shishen = "食神" in tg_set
        has_shangguan = "伤官" in tg_set
        has_yin = "正印" in tg_set or "偏印" in tg_set
        if has_shishen:
            return _po_result(
                False,
                saved=True,
                method="食神制杀",
                note="食神透干制杀，杀有制而不破",
            )
        if has_yin:
            return _po_result(
                False,
                saved=True,
                method="印制杀",
                note="印星化杀，杀印相生救应",
            )
        if has_shangguan:
            return _po_result(
                False,
                saved=True,
                method="伤官制杀",
                note="伤官制杀，格局有救",
            )
        day_el = _day_elem()
        if _elem_ratio(day_el) < 0.20:
            return _po_result(True, "七杀无制且日主弱，格局凶险", "major")
        return _po_result(True, "七杀无食神制杀，威力失控", "minor")

    # ── 正印格 ───────────────────────────────────────────────────────────
    elif geju_name == "正印格":
        # 财多克印：财星（正财/偏财）的五行比例超过印星
        # 财星以"正财"/"偏财"在十神中体现
        cai_count = tgs.count("正财") + tgs.count("偏财")
        if cai_count >= 2:
            return _po_result(True, "财星多，财克印，正印格被破", "major")
        if cai_count == 1:
            return _po_result(True, "财星克印，正印格受损", "minor")

    # ── 偏印格 ───────────────────────────────────────────────────────────
    elif geju_name == "偏印格":
        if "食神" in tg_set:
            return _po_result(True, "食神透干，枭印夺食之象，格局被牵制", "minor")

    # ── 正财格 ───────────────────────────────────────────────────────────
    elif geju_name == "正财格":
        bijie_count = tgs.count("比肩") + tgs.count("劫财")
        if bijie_count >= 2:
            return _po_result(True, "比劫多，群劫争财，正财格被破", "major")
        if bijie_count == 1:
            return _po_result(True, "有比劫分财，正财格减力", "minor")

    # ── 偏财格 ───────────────────────────────────────────────────────────
    elif geju_name == "偏财格":
        bijie_count = tgs.count("比肩") + tgs.count("劫财")
        if bijie_count >= 2:
            return _po_result(True, "比劫过多，偏财格被劫破", "major")
        if bijie_count == 1:
            return _po_result(True, "有比劫分夺偏财，格局稍弱", "minor")

    # ── 食神格 ───────────────────────────────────────────────────────────
    elif geju_name == "食神格":
        if "偏印" in tg_set:
            return _po_result(True, "偏印（枭神）透干，枭印夺食，食神格被破", "major")

    # ── 伤官格 ───────────────────────────────────────────────────────────
    elif geju_name == "伤官格":
        if "正官" in tg_set:
            return _po_result(True, "伤官见官，格局大忌，凶险重重", "major")
        if "七杀" in tg_set:
            return _po_result(True, "伤官遇七杀，混杂不纯", "minor")

    return _po_result(False)
