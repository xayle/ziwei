"""
services/bazi_engine/shensha.py — 神煞计算（M1 任务 1.09）

支持神煞:
  优先级 A（吉）: 天乙贵人、文昌贵人、将星
  优先级 A（凶）: 劫煞、亡神
  优先级 B（吉）: 驿马、桃花（咸池）
  优先级 B（凶）: 白虎
  优先级 C（参考）: 华盖、红鸾、天喜、天德、月德、地解、孤辰、寡宿、将星、月刃

判断依据：年柱或日柱地支，命局4地支均检查

规则：
  - ≥3 条相关神煞 → star=True（宿命之星）
  - 结果按 priority → name 排序返回
"""

from __future__ import annotations

from services.bazi_engine.tables import (
    BRANCHES,
    JIESHA,
    TAOHUA,
    TIANYI_GUIREN,
    WANGSHEN,
    WENCHANG_GUIREN,
    YIMA,
)

# ──────────────────────────────────────────────────────────────────────────────
# 额外神煞表（tables.py 未含的）
# ──────────────────────────────────────────────────────────────────────────────

# 华盖: {年/日支三合首支: 华盖支}
HUAGAO: dict[str, str] = {
    "寅": "戌",
    "午": "戌",
    "戌": "戌",
    "申": "辰",
    "子": "辰",
    "辰": "辰",
    "亥": "未",
    "卯": "未",
    "未": "未",
    "巳": "丑",
    "酉": "丑",
    "丑": "丑",
}

# 将星: {三合首: 将星支}
JIANXING: dict[str, str] = {
    "申": "子",
    "子": "子",
    "辰": "子",
    "寅": "午",
    "午": "午",
    "戌": "午",
    "亥": "卯",
    "卯": "卯",
    "未": "卯",
    "巳": "酉",
    "酉": "酉",
    "丑": "酉",
}

# 红鸾: {年支: 红鸾支}  子→卯，逆数
_HONG_LUAN_BASE = ["卯", "寅", "丑", "子", "亥", "戌", "酉", "申", "未", "午", "巳", "辰"]
HONG_LUAN: dict[str, str] = {BRANCHES[i]: _HONG_LUAN_BASE[i] for i in range(12)}

# 天喜: 与红鸾对冲
TIAN_XI: dict[str, str] = {k: BRANCHES[(BRANCHES.index(v) + 6) % 12] for k, v in HONG_LUAN.items()}

# 天德贵人（按月支）
TIAN_DE: dict[str, str] = {
    "寅": "丁",
    "卯": "申",
    "辰": "壬",
    "巳": "辛",
    "午": "亥",
    "未": "甲",
    "申": "癸",
    "酉": "寅",
    "戌": "丙",
    "亥": "乙",
    "子": "巳",
    "丑": "庚",
}

# 月德贵人（按月支）
YUE_DE: dict[str, str] = {
    "寅": "丙",
    "午": "丙",
    "戌": "丙",
    "申": "壬",
    "子": "壬",
    "辰": "壬",
    "亥": "甲",
    "卯": "甲",
    "未": "甲",
    "巳": "庚",
    "酉": "庚",
    "丑": "庚",
}

# 孤辰: {年支: 孤辰支}
GU_CHEN: dict[str, str] = {
    "寅": "巳",
    "卯": "巳",
    "辰": "巳",
    "巳": "申",
    "午": "申",
    "未": "申",
    "申": "亥",
    "酉": "亥",
    "戌": "亥",
    "亥": "寅",
    "子": "寅",
    "丑": "寅",
}

# 寡宿: {年支: 寡宿支}
GUA_SU: dict[str, str] = {
    "寅": "丑",
    "卯": "丑",
    "辰": "丑",
    "巳": "辰",
    "午": "辰",
    "未": "辰",
    "申": "未",
    "酉": "未",
    "戌": "未",
    "亥": "戌",
    "子": "戌",
    "丑": "戌",
}

# 月刃（羊刃）: {天干: 月刃支}
YUEYAN: dict[str, str] = {
    "甲": "卯",
    "乙": "辰",
    "丙": "午",
    "丁": "未",
    "戊": "午",
    "己": "未",
    "庚": "酉",
    "辛": "戌",
    "壬": "子",
    "癸": "丑",
}

# 白虎: {年支三合首: 白虎支}
BAI_HU: dict[str, str] = JIESHA.copy()  # 白虎与劫煞同位（粗略近似，某些流派略有差异）

# 太极贵人: {日/年干: [可命中地支]} — 临子午/寅申/亥巳/辰戌/卯酉
TAIJI_GUIREN: dict[str, list[str]] = {
    "甲": ["子", "午"],
    "戊": ["子", "午"],
    "庚": ["子", "午"],
    "乙": ["寅", "申"],
    "己": ["寅", "申"],
    "丙": ["亥", "巳"],
    "丁": ["亥", "巳"],
    "辛": ["辰", "戌"],
    "壬": ["卯", "酉"],
    "癸": ["卯", "酉"],
}

# 金舆: {日干: 金舆支} — 乘坐金舆，主富贵
JIN_YU: dict[str, str] = {
    "甲": "辰",
    "乙": "巳",
    "丙": "未",
    "丁": "申",
    "戊": "戌",
    "己": "亥",
    "庚": "丑",
    "辛": "寅",
    "壬": "辰",
    "癸": "巳",
}

# 魁罡: 日柱干支组合为以下4种之一
KUIGANG_PILLARS: frozenset[str] = frozenset({"庚辰", "庚戌", "壬辰", "戊戌"})

# 三奇: 四柱天干含三组特殊组合之一（天三奇/地三奇/人三奇）
SANQI_GROUPS: list[frozenset[str]] = [
    frozenset({"甲", "戊", "庚"}),  # 天三奇
    frozenset({"乙", "丙", "丁"}),  # 地三奇
    frozenset({"壬", "癸", "辛"}),  # 人三奇（部分流派）
]

# ── v8.0 N2.02 新增神煞查表 ────────────────────────────────────────────────

# 血刃: 年支→血刃日支（对冲位），《三命通会》
XUELUN: dict[str, str] = {
    "子": "午",
    "丑": "未",
    "寅": "申",
    "卯": "酉",
    "辰": "戌",
    "巳": "亥",
    "午": "子",
    "未": "丑",
    "申": "寅",
    "酉": "卯",
    "戌": "辰",
    "亥": "巳",
}

# 灾煞: 三合局各五行绝命支（查绝地表，非位移计算）
# 申子辰水局绝于巳，寅午戌火局绝于亥，巳酉丑金局绝于寅，亥卯未木局绝于申
ZAISHA: dict[str, str] = {
    "申": "巳",
    "子": "巳",
    "辰": "巳",
    "寅": "亥",
    "午": "亥",
    "戌": "亥",
    "巳": "寅",
    "酉": "寅",
    "丑": "寅",
    "亥": "申",
    "卯": "申",
    "未": "申",
}

# 天厨贵人: 日干→命局月支，《三命通会》
TIANCHU_GUIREN: dict[str, str] = {
    "甲": "巳",
    "乙": "午",
    "丙": "巳",
    "丁": "午",
    "戊": "申",
    "己": "酉",
    "庚": "亥",
    "辛": "子",
    "壬": "寅",
    "癸": "卯",
}


# ──────────────────────────────────────────────────────────────────────────────
# 神煞元数据
# ──────────────────────────────────────────────────────────────────────────────

SHENSHA_META: dict[str, dict] = {
    "天乙贵人": {
        "priority": "A",
        "polarity": "+",
        "topic": "命运",
        "note": "逢之遇贵人相助，化险为夷",
        "classic": "《三命通会》",
    },
    "文昌贵人": {
        "priority": "A",
        "polarity": "+",
        "topic": "才学",
        "note": "主聪明才学，利读书考试",
        "classic": "《渊海子平》",
    },
    "将星": {
        "priority": "A",
        "polarity": "+",
        "topic": "领导",
        "note": "主权威领导，职场掌权",
        "classic": "《三命通会》",
    },
    "驿马": {
        "priority": "B",
        "polarity": "+",
        "topic": "奔波",
        "note": "主奔波迁动，利出行贸易",
        "classic": "《三命通会》",
    },
    "桃花": {
        "priority": "B",
        "polarity": "+",
        "topic": "感情",
        "note": "主感情缘分，人缘旺",
        "classic": "《三命通会》",
    },
    "红鸾": {
        "priority": "B",
        "polarity": "+",
        "topic": "婚恋",
        "note": "主婚姻喜事，感情之象",
        "classic": "《三命通会》",
    },
    "天喜": {
        "priority": "B",
        "polarity": "+",
        "topic": "喜事",
        "note": "主喜庆之事，婚庆生育",
        "classic": "《三命通会》",
    },
    "华盖": {
        "priority": "C",
        "polarity": "~",
        "topic": "宗教",
        "note": "主孤独、宗教艺术，有仙缘",
        "classic": "《三命通会》",
    },
    "天德贵人": {
        "priority": "A",
        "polarity": "+",
        "topic": "庇护",
        "note": "主官非化解，贵人庇护",
        "classic": "《三命通会》",
    },
    "月德贵人": {
        "priority": "A",
        "polarity": "+",
        "topic": "庇护",
        "note": "主疾厄化解，逢凶化吉",
        "classic": "《三命通会》",
    },
    "劫煞": {
        "priority": "A",
        "polarity": "-",
        "topic": "破财",
        "note": "主劫夺破财，防小人",
        "classic": "《三命通会》",
    },
    "亡神": {
        "priority": "A",
        "polarity": "-",
        "topic": "暗耗",
        "note": "主暗耗损失，宜积阴德",
        "classic": "《神峰通考》",
    },
    "白虎": {
        "priority": "B",
        "polarity": "-",
        "topic": "血光",
        "note": "主血光意外，手术之象",
        "classic": "《神峰通考》",
    },
    "孤辰": {
        "priority": "C",
        "polarity": "-",
        "topic": "孤寡",
        "note": "男命孤独，宜积极社交",
        "classic": "《三命通会》",
    },
    "寡宿": {
        "priority": "C",
        "polarity": "-",
        "topic": "孤寡",
        "note": "女命孤寡，婚姻宜晚",
        "classic": "《三命通会》",
    },
    "月刃": {
        "priority": "B",
        "polarity": "-",
        "topic": "刚烈",
        "note": "性格刚烈，防意外血光",
        "classic": "《子平真诠》",
    },
    # v7.0 新增 4 种（P0-06 ≥20）
    "太极贵人": {
        "priority": "A",
        "polarity": "+",
        "topic": "智慧",
        "note": "主聪慧有谋，临机决断力强",
        "classic": "《三命通会》",
    },
    "金舆": {
        "priority": "B",
        "polarity": "+",
        "topic": "财富",
        "note": "主富贵，金钱财帛有余",
        "classic": "《三命通会》",
    },
    "魁罡": {
        "priority": "A",
        "polarity": "~",
        "topic": "权威",
        "note": "刚毅果断，逢岁运生旺则权威大，遇冲则凶",
        "classic": "《三命通会》",
    },
    "三奇": {
        "priority": "A",
        "polarity": "+",
        "topic": "奇特",
        "note": "天地人三奇，主出奇制胜，运势奇特不凡",
        "classic": "《三命通会》",
    },
    # v8.0 N2.02 新增 5 种
    "血刃": {
        "priority": "B",
        "polarity": "-",
        "topic": "血光",
        "note": "主血光横祸，宜防刀伤车祸",
        "classic": "《三命通会》",
    },
    "灾煞": {
        "priority": "B",
        "polarity": "-",
        "topic": "灾祸",
        "note": "三合局绝地，主灾祸横至，宜低调守成",
        "classic": "《三命通会》",
    },
    "天罗": {
        "priority": "C",
        "polarity": "-",
        "topic": "困厄",
        "note": "戌亥并见，主困厄缠身，逢运难解",
        "classic": "《三命通会》",
    },
    "地网": {
        "priority": "C",
        "polarity": "-",
        "topic": "困厄",
        "note": "辰巳并见，主牢狱官非，行事受阻",
        "classic": "《三命通会》",
    },
    "天厨贵人": {
        "priority": "A",
        "polarity": "+",
        "topic": "饮食",
        "note": "主衣食丰足，财禄充裕，享美食之福",
        "classic": "《三命通会》",
    },
}


# ──────────────────────────────────────────────────────────────────────────────
# 主函数
# ──────────────────────────────────────────────────────────────────────────────


def compute_shensha(
    year_stem: str,
    year_branch: str,
    month_stem: str,
    month_branch: str,
    day_stem: str,
    day_branch: str,
    hour_stem: str,
    hour_branch: str,
) -> dict:
    """
    计算四柱神煞.

    Returns:
    {
        "items": [{"name": str, "priority": str, "polarity": str, "pillar": str,
                   "topic": str, "note": str}],
        "star": bool,     # ≥3条神煞
        "summary": str,   # 简要描述
    }
    """
    branches = {
        "year": year_branch,
        "month": month_branch,
        "day": day_branch,
        "hour": hour_branch,
    }
    stems = {
        "year": year_stem,
        "month": month_stem,
        "day": day_stem,
        "hour": hour_stem,
    }
    results: list[dict] = []

    def _add(name: str, pillar: str) -> None:
        if name in SHENSHA_META:
            meta = SHENSHA_META[name]
            results.append(
                {
                    "name": name,
                    "priority": meta["priority"],
                    "polarity": meta["polarity"],
                    "pillar": pillar,
                    "topic": meta["topic"],
                    "note": meta["note"],
                    "classic": meta.get("classic", ""),
                }
            )

    # ── 天乙贵人（按日干/年干查四柱地支）────────────────────────────────────
    for stem_key in ("day", "year"):
        s = stems[stem_key]
        guiren_branches = TIANYI_GUIREN.get(s, [])
        for br_key, br in branches.items():
            if br in guiren_branches:
                _add("天乙贵人", br_key)

    # ── 文昌贵人（按日干/年干查地支）──────────────────────────────────────────
    for stem_key in ("day", "year"):
        s = stems[stem_key]
        wc = WENCHANG_GUIREN.get(s)
        if wc:
            for br_key, br in branches.items():
                if br == wc:
                    _add("文昌贵人", br_key)

    # ── 将星（按年支/日支所在三合首）─────────────────────────────────────────
    for ref_key in ("year", "day"):
        js = JIANXING.get(branches[ref_key])
        if js:
            for br_key, br in branches.items():
                if br == js and br_key != ref_key:
                    _add("将星", br_key)

    # ── 驿马（按年支/日支）────────────────────────────────────────────────────
    for ref_key in ("year", "day"):
        ym = YIMA.get(branches[ref_key])
        if ym:
            for br_key, br in branches.items():
                if br == ym and br_key != ref_key:
                    _add("驿马", br_key)

    # ── 桃花（按年支/日支）────────────────────────────────────────────────────
    for ref_key in ("year", "day"):
        tf = TAOHUA.get(branches[ref_key])
        if tf:
            for br_key, br in branches.items():
                if br == tf and br_key != ref_key:
                    _add("桃花", br_key)

    # ── 劫煞（按年支/日支）────────────────────────────────────────────────────
    for ref_key in ("year", "day"):
        js = JIESHA.get(branches[ref_key])
        if js:
            for br_key, br in branches.items():
                if br == js and br_key != ref_key:
                    _add("劫煞", br_key)

    # ── 亡神（按年支/日支）────────────────────────────────────────────────────
    for ref_key in ("year", "day"):
        ws = WANGSHEN.get(branches[ref_key])
        if ws:
            for br_key, br in branches.items():
                if br == ws and br_key != ref_key:
                    _add("亡神", br_key)

    # ── 华盖（按年支/日支）────────────────────────────────────────────────────
    for ref_key in ("year", "day"):
        hg = HUAGAO.get(branches[ref_key])
        if hg:
            for br_key, br in branches.items():
                if br == hg and br_key != ref_key:
                    _add("华盖", br_key)

    # ── 红鸾（按年支）──────────────────────────────────────────────────────────
    hl = HONG_LUAN.get(year_branch)
    if hl:
        for br_key, br in branches.items():
            if br == hl and br_key != "year":
                _add("红鸾", br_key)

    # ── 天喜（按年支）──────────────────────────────────────────────────────────
    tx = TIAN_XI.get(year_branch)
    if tx:
        for br_key, br in branches.items():
            if br == tx and br_key != "year":
                _add("天喜", br_key)

    # ── 天德贵人（按月支查干）────────────────────────────────────────────────
    td = TIAN_DE.get(month_branch)
    if td:
        for st_key, st in stems.items():
            if st == td:
                _add("天德贵人", st_key)

    # ── 月德贵人（按月支查干）────────────────────────────────────────────────
    yd = YUE_DE.get(month_branch)
    if yd:
        for st_key, st in stems.items():
            if st == yd:
                _add("月德贵人", st_key)

    # ── 月刃（羊刃，按日干）──────────────────────────────────────────────────
    yr = YUEYAN.get(day_stem)
    if yr:
        for br_key, br in branches.items():
            if br == yr and br_key != "day":
                _add("月刃", br_key)

    # ── 孤辰（按年支）──────────────────────────────────────────────────────────
    gc = GU_CHEN.get(year_branch)
    if gc:
        for br_key, br in branches.items():
            if br == gc and br_key != "year":
                _add("孤辰", br_key)

    # ── 寡宿（按年支）──────────────────────────────────────────────────────────
    gs = GUA_SU.get(year_branch)
    if gs:
        for br_key, br in branches.items():
            if br == gs and br_key != "year":
                _add("寡宿", br_key)

    # ── 太极贵人（按日干/年干查四柱地支）────────────────────────────────────
    for stem_key in ("day", "year"):
        s = stems[stem_key]
        taiji_list = TAIJI_GUIREN.get(s, [])
        for br_key, br in branches.items():
            if br in taiji_list:
                _add("太极贵人", br_key)

    # ── 金舆（按日干查四柱地支）──────────────────────────────────────────────
    jy = JIN_YU.get(day_stem)
    if jy:
        for br_key, br in branches.items():
            if br == jy and br_key != "day":
                _add("金舆", br_key)

    # ── 魁罡（日柱干支组合）──────────────────────────────────────────────────
    day_ganzhi = day_stem + day_branch
    if day_ganzhi in KUIGANG_PILLARS:
        _add("魁罡", "day")

    # ── 三奇（四柱天干含三奇组合）────────────────────────────────────────────
    all_stems_set = {year_stem, month_stem, day_stem, hour_stem}
    for group in SANQI_GROUPS:
        if group <= all_stems_set:
            _add("三奇", "year")  # 以年柱为代表位
            break

    # ── 血刃（年支→日支对照，B/-）────────────────────────────────────────────
    xl = XUELUN.get(year_branch)
    if xl and day_branch == xl:
        _add("血刃", "day")

    # ── 灾煞（三合局绝地，按年支/日支查，B/-）───────────────────────────────
    for ref_key in ("year", "day"):
        zs = ZAISHA.get(branches[ref_key])
        if zs:
            for br_key, br in branches.items():
                if br == zs and br_key != ref_key:
                    _add("灾煞", br_key)

    # ── 天罗（四柱同时出现戌 AND 亥，C/-）───────────────────────────────────
    all_branches_set = set(branches.values())
    if "戌" in all_branches_set and "亥" in all_branches_set:
        _add("天罗", "year")  # 以年柱为代表位

    # ── 地网（四柱同时出现辰 AND 巳，C/-）───────────────────────────────────
    if "辰" in all_branches_set and "巳" in all_branches_set:
        _add("地网", "year")  # 以年柱为代表位

    # ── 天厨贵人（日干→固定月支，A/+）──────────────────────────────────────
    tc = TIANCHU_GUIREN.get(day_stem)
    if tc and month_branch == tc:
        _add("天厨贵人", "month")

    # ── 去重 + 排序 ───────────────────────────────────────────────────────────
    seen: set[str] = set()
    unique: list[dict] = []
    for item in results:
        key = f"{item['name']}@{item['pillar']}"
        if key not in seen:
            seen.add(key)
            unique.append(item)

    priority_order = {"A": 0, "B": 1, "C": 2}
    unique.sort(key=lambda x: (priority_order.get(x["priority"], 9), x["name"]))

    star = len(unique) >= 3
    positives = [x["name"] for x in unique if x["polarity"] == "+"]
    negatives = [x["name"] for x in unique if x["polarity"] == "-"]
    summary_parts = []
    if positives:
        summary_parts.append(f"吉神: {'、'.join(positives)}")
    if negatives:
        summary_parts.append(f"凶煞: {'、'.join(negatives)}")
    summary = "；".join(summary_parts) if summary_parts else "无特殊神煞"

    return {
        "items": unique,
        "star": star,
        "summary": summary,
    }
