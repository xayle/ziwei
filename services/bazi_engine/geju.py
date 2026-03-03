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
    "曲直格": {"type": "outer", "note": "木气专旺（≥70%），主仁慈文学，宜东方发展"},
    "炎上格": {"type": "outer", "note": "火气专旺（≥70%），主礼智名显，利南方"},
    "稼穑格": {"type": "outer", "note": "土气专旺（≥70%），主信厚诚实，守成持业"},
    "从革格": {"type": "outer", "note": "金气专旺（≥70%），主威武刚烈，利西方金融"},
    "润下格": {"type": "outer", "note": "水气专旺（≥70%），主智谋机变，利北方"},
    # ── 从格（日主极弱，顺从最强之神）────────────────────────────────
    "从财格": {"type": "cong",  "note": "日主极弱，全局财星最旺，宜顺从理财，忌比劫"},
    "从官杀格": {"type": "cong", "note": "日主极弱，全局官杀最旺，宜服从管理，利官场"},
    "从儿格": {"type": "cong",  "note": "日主极弱，食伤广布，专事创作技艺"},
    "从势格": {"type": "cong",  "note": "日主极弱，财官食伤均衡，顺势应变"},
    # ── 特殊格 ───────────────────────────────────────────────────────
    "建禄格": {"type": "special", "note": "月令为日主临官位（禄），日主有根有力"},
    "羊刃格": {"type": "special", "note": "月令为日主刃旺，刚烈之象"},
    "普通格": {"type": "none",  "note": "五行较均衡，无明显格局"},
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

# 五合化气规则: frozenset({干A, 干B}) → (化出五行英文, 格局名称)
_WUHE_HUAQI: dict[frozenset, tuple[str, str]] = {
    frozenset({"甲", "己"}): ("earth", "化土格"),
    frozenset({"乙", "庚"}): ("metal", "化金格"),
    frozenset({"丙", "辛"}): ("water", "化水格"),
    frozenset({"丁", "壬"}): ("wood",  "化木格"),
    frozenset({"戊", "癸"}): ("fire",  "化火格"),
}

# 克化关系: key=被克五行, value=克它的五行
_WUXING_KE_BY: dict[str, str] = {
    "earth": "wood",
    "metal": "fire",
    "water": "earth",
    "wood":  "metal",
    "fire":  "water",
}

# 相生关系: key=生者, value=被生者（a生b）
_WUXING_SHENG: dict[str, str] = {
    "wood":  "fire",
    "fire":  "earth",
    "earth": "metal",
    "metal": "water",
    "water": "wood",
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
    wuxing_scores: dict[str, float] | None = None,   # 五行得分，用于外格判断
    year_branch: str | None = None,                  # N1.03 三合局检测
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
    # ── 1. 月令主气（取藏干权重最大的那个）─────────────────────────────
    hidden = BRANCH_HIDDEN_STEMS.get(month_branch, [])
    if not hidden:
        return _no_geju("月支藏干数据缺失")

    main_hidden_stem, _ = max(hidden, key=lambda x: x[1])
    month_qi = main_hidden_stem
    month_qi_elem, _ = STEM_ELEMENT.get(month_qi, ("?", "?"))

    # ── 2. 透干检查（不含日干，日干是主体）──────────────────────────────
    candidate_stems = [year_stem, month_stem, hour_stem]
    toukan_stem: str | None = None
    for s in candidate_stems:
        s_elem, _ = STEM_ELEMENT.get(s, ("?", "?"))
        if s_elem == month_qi_elem:
            toukan_stem = s
            break
    ref_stem = toukan_stem if toukan_stem else month_qi

    # ── 四柱全部天干（化气格判断需含日干）────────────────────────────────
    all_stems_full = [year_stem, month_stem, day_stem, hour_stem]

    # ══════════════════════════════════════════════════════════════════════
    # 优先级 1: 化气格（N1.02）——高于一切外格/内格
    # ══════════════════════════════════════════════════════════════════════
    huaqi = _check_huaqi(all_stems_full, month_branch)
    if huaqi["is_huaqi"]:
        geju_name  = huaqi["huaqi_name"]
        ten_god    = ""   # 化气格不以月令十神取格
        confidence = huaqi["confidence"]
        meta       = GEJU_META.get(geju_name, GEJU_META["普通格"])
    else:
        # ── 3. 十神关系 → 格局（正常取格链）──────────────────────────
        ten_god   = get_ten_god(day_stem, ref_stem)
        geju_name = _SHISHEN_TO_GEJU.get(ten_god, "普通格")

        # ══════════════════════════════════════════════════════════════
        # 优先级 2: 外格判断（覆盖建禄/羊刃/普通格）
        # ══════════════════════════════════════════════════════════════
        if wuxing_scores and geju_name in ("普通格", "建禄格", "羊刃格"):
            outer = _check_outer_geju(wuxing_scores, day_stem, month_stem, month_branch)
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
                    confidence = min(0.5 + ratio * 0.5, 0.95)   # 从旺格类（同气）
                else:
                    confidence = min(0.4 + ratio * 0.4, 0.85)   # 专旺格类（异气）
            else:
                confidence = 0.75
        elif meta["type"] == "cong":
            confidence = 0.70
        elif meta["type"] == "special":   # 建禄格 / 羊刃格
            confidence = 0.80
        elif toukan_stem:
            confidence = 0.85             # 正格透干成格
        elif geju_name != "普通格":
            confidence = 0.65             # 正格无透干靠藏干
        else:
            confidence = 0.40             # 普通格

    # ══════════════════════════════════════════════════════════════════════
    # 优先级 3: 三合全合 confidence 调整（N1.03）
    # ══════════════════════════════════════════════════════════════════════
    if year_branch and day_branch and hour_branch:
        try:
            from services.bazi_engine.relations import get_branch_relations as _gbr
            day_elem_adj, _ = STEM_ELEMENT.get(day_stem, ("?", "?"))
            sanhe_list = [
                r for r in _gbr(year_branch, month_branch, day_branch, hour_branch)
                if r["type"] == "三合全合"
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

    return {
        "name":        geju_name,
        "type":        meta["type"],
        "month_qi":    month_qi,
        "toukan_stem": toukan_stem,
        "ten_god":     ten_god,
        "note":        meta["note"],
        "confident":   geju_name != "普通格",
        "confidence":  confidence if not po["broken"] else max(0.0, confidence - 0.3),
        "po_geju":     po,
    }


# ──────────────────────────────────────────────────────────────────────────────
# 化气格判定（N1.02）
# ──────────────────────────────────────────────────────────────────────────────

def _check_huaqi(
    stems: list[str],     # [year_stem, month_stem, day_stem, hour_stem] 必须含日干
    month_branch: str,
) -> dict:
    """
    化气格判定（D1 修订标准）.

    条件：
      1. day_stem 与某一柱天干（月/年/时）成天干五合
      2. 月支主气五行 == 化出五行

    confidence 规则:
      基础 0.70；命局四柱天干+月支主气中无任何元素克化出五行 → 加 0.10（上限 0.80）

    Returns:
        {"is_huaqi": bool, "huaqi_element": str, "huaqi_name": str, "confidence": float}
    """
    if len(stems) < 4:
        return {"is_huaqi": False, "huaqi_element": "", "huaqi_name": "", "confidence": 0.0}

    year_stem, month_stem, day_stem, hour_stem = stems

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
        key = frozenset({day_stem, other_stem})
        if key in _WUHE_HUAQI:
            huaqi_elem, huaqi_name = _WUHE_HUAQI[key]
            # 月支主气五行必须等于化出五行
            if branch_elem == huaqi_elem:
                confidence = 0.70
                # 无克制判断：四柱天干 + 月支主气中，无元素克化出五行
                ke_elem = _WUXING_KE_BY.get(huaqi_elem, "")
                if ke_elem:
                    chart_elems: set[str] = set()
                    for s in stems:
                        e, _ = STEM_ELEMENT.get(s, ("?", "?"))
                        chart_elems.add(e)
                    chart_elems.add(branch_elem)  # 月支主气
                    if ke_elem not in chart_elems:
                        confidence += 0.10  # 无克制加成 → 0.80
                return {
                    "is_huaqi":    True,
                    "huaqi_element": huaqi_elem,
                    "huaqi_name":  huaqi_name,
                    "confidence":  confidence,
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
        "po_geju": {"broken": False, "reason": "", "severity": "none"},
    }


# 五行专旺格：元素 → 格局名
_WUXING_SPECIAL_GEJU: dict[str, str] = {
    "wood":  "曲直格",
    "fire":  "炎上格",
    "earth": "稼穑格",
    "metal": "从革格",
    "water": "润下格",
}

# 十神 → 从格分类
_SHISHEN_CONG_GEJU: dict[str, str] = {
    "正财": "从财格",  "偏财": "从财格",
    "正官": "从官杀格", "七杀": "从官杀格",
    "食神": "从儿格",  "伤官": "从儿格",
}


def _check_outer_geju(
    wuxing_scores: dict[str, float],
    day_stem: str,
    month_stem: str,
    month_branch: str,
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

    # ── 1. 专旺判断（≥ 70%）────────────────────────────────────────────
    for elem, score in wuxing_scores.items():
        pct = score / total
        if pct >= 0.70:
            if elem == day_elem:
                # 日主同元素专旺 → 从旺格（或带名称的专旺）
                return _WUXING_SPECIAL_GEJU.get(elem, "从旺格")
            else:
                # 非日主元素专旺 → 五行专旺格
                return _WUXING_SPECIAL_GEJU.get(elem, "专旺格")

    # ── 2. 从格判断（日主极弱 ≤ 10%，他方 ≥ 55%）──────────────────────
    day_pct = (wuxing_scores.get(day_elem, 0.0) / total) if day_elem != "?" else 1.0
    if day_pct <= 0.10:
        # 找最旺的非日主元素
        strongest_elem = max(
            ((e, s) for e, s in wuxing_scores.items() if e != day_elem),
            key=lambda x: x[1],
            default=(None, 0.0),
        )
        if strongest_elem[0] and strongest_elem[1] / total >= 0.55:
            se = strongest_elem[0]
            # 根据最旺元素对应的十神推断从格类型
            # 简化映射：财星(metal/earth生金，水)+官星→相应从格
            # 通过五行反查对日主的十神
            from services.bazi_engine.tables import get_ten_god as _gtg
            # 找与最旺元素同属的天干代表（取主气）
            _ELEM_REPR_STEM = {
                "wood": "甲", "fire": "丙", "earth": "戊",
                "metal": "庚", "water": "壬",
            }
            repr_stem = _ELEM_REPR_STEM.get(se, "甲")
            ten_god = _gtg(day_stem, repr_stem)
            cong_geju = _SHISHEN_CONG_GEJU.get(ten_god)
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
        }
    """
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
            return {"broken": True, "reason": "伤官透干克制正官，官被伤破", "severity": "major"}
        if "七杀" in tg_set:
            return {"broken": True, "reason": "官杀混杂，格局混乱", "severity": "major"}

    # ── 七杀格 ───────────────────────────────────────────────────────────
    elif geju_name == "七杀格":
        has_shishen = "食神" in tg_set or "伤官" in tg_set
        if not has_shishen:
            # 无制杀，且日主本身较弱（比劫 < 10%）
            day_el = _day_elem()
            if _elem_ratio(day_el) < 0.20:
                return {"broken": True, "reason": "七杀无制且日主弱，格局凶险", "severity": "major"}
            # 有根但无制，仍视作轻微破格
            return {"broken": True, "reason": "七杀无食神制杀，威力失控", "severity": "minor"}

    # ── 正印格 ───────────────────────────────────────────────────────────
    elif geju_name == "正印格":
        # 财多克印：财星（正财/偏财）的五行比例超过印星
        # 财星以"正财"/"偏财"在十神中体现
        cai_count = tgs.count("正财") + tgs.count("偏财")
        if cai_count >= 2:
            return {"broken": True, "reason": "财星多，财克印，正印格被破", "severity": "major"}
        if cai_count == 1:
            return {"broken": True, "reason": "财星克印，正印格受损", "severity": "minor"}

    # ── 偏印格 ───────────────────────────────────────────────────────────
    elif geju_name == "偏印格":
        if "食神" in tg_set:
            return {"broken": True, "reason": "食神透干，枭印夺食之象，格局被牵制", "severity": "minor"}

    # ── 正财格 ───────────────────────────────────────────────────────────
    elif geju_name == "正财格":
        bijie_count = tgs.count("比肩") + tgs.count("劫财")
        if bijie_count >= 2:
            return {"broken": True, "reason": "比劫多，群劫争财，正财格被破", "severity": "major"}
        if bijie_count == 1:
            return {"broken": True, "reason": "有比劫分财，正财格减力", "severity": "minor"}

    # ── 偏财格 ───────────────────────────────────────────────────────────
    elif geju_name == "偏财格":
        bijie_count = tgs.count("比肩") + tgs.count("劫财")
        if bijie_count >= 2:
            return {"broken": True, "reason": "比劫过多，偏财格被劫破", "severity": "major"}
        if bijie_count == 1:
            return {"broken": True, "reason": "有比劫分夺偏财，格局稍弱", "severity": "minor"}

    # ── 食神格 ───────────────────────────────────────────────────────────
    elif geju_name == "食神格":
        if "偏印" in tg_set:
            return {"broken": True, "reason": "偏印（枭神）透干，枭印夺食，食神格被破", "severity": "major"}

    # ── 伤官格 ───────────────────────────────────────────────────────────
    elif geju_name == "伤官格":
        if "正官" in tg_set:
            return {"broken": True, "reason": "伤官见官，格局大忌，凶险重重", "severity": "major"}
        if "七杀" in tg_set:
            return {"broken": True, "reason": "伤官遇七杀，混杂不纯", "severity": "minor"}

    return {"broken": False, "reason": "", "severity": "none"}
