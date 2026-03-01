"""
services/bazi_engine/tables.py — 八字命理核心查找表（共11张）
# 来源：《三命通会》卷二

M1 任务 1.01: 11张查找表 + self_check()
每张表 assert 行数 + 数据正确性校验
  - 藏干权重和=1.0
  - 纳音60条
  - 空亡6旬
"""
from __future__ import annotations

# ─────────────────────────────────────────────────────────────────────────────
# 表1  十天干（ganzhi.py 天干序列）
# 来源：《三命通会》卷二
# ─────────────────────────────────────────────────────────────────────────────
STEMS: list[str] = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]

# ─────────────────────────────────────────────────────────────────────────────
# 表2  十二地支
# 来源：《三命通会》卷二
# ─────────────────────────────────────────────────────────────────────────────
BRANCHES: list[str] = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]

# ─────────────────────────────────────────────────────────────────────────────
# 表3  天干五行阴阳 {干: (五行element, 阴阳yin_yang)}
# 来源：《三命通会》卷二
# ─────────────────────────────────────────────────────────────────────────────
STEM_ELEMENT: dict[str, tuple[str, str]] = {
    "甲": ("wood",  "yang"),
    "乙": ("wood",  "yin"),
    "丙": ("fire",  "yang"),
    "丁": ("fire",  "yin"),
    "戊": ("earth", "yang"),
    "己": ("earth", "yin"),
    "庚": ("metal", "yang"),
    "辛": ("metal", "yin"),
    "壬": ("water", "yang"),
    "癸": ("water", "yin"),
}

# ─────────────────────────────────────────────────────────────────────────────
# 表4  地支五行阴阳 {支: (五行, 阴阳)}
# 来源：《三命通会》卷二
# ─────────────────────────────────────────────────────────────────────────────
BRANCH_ELEMENT: dict[str, tuple[str, str]] = {
    "子": ("water", "yang"),
    "丑": ("earth", "yin"),
    "寅": ("wood",  "yang"),
    "卯": ("wood",  "yin"),
    "辰": ("earth", "yang"),
    "巳": ("fire",  "yin"),
    "午": ("fire",  "yang"),
    "未": ("earth", "yin"),
    "申": ("metal", "yang"),
    "酉": ("metal", "yin"),
    "戌": ("earth", "yang"),
    "亥": ("water", "yin"),
}

# ─────────────────────────────────────────────────────────────────────────────
# 表5  地支藏干（主气+中气+余气及其权重）
# 来源：《三命通会》卷二 "论支藏干"
# 权重之和必须 = 1.0（由 self_check 验证）
# ─────────────────────────────────────────────────────────────────────────────
BRANCH_HIDDEN_STEMS: dict[str, list[tuple[str, float]]] = {
    "子": [("癸", 1.0)],
    "丑": [("己", 0.6), ("癸", 0.3), ("辛", 0.1)],
    "寅": [("甲", 0.6), ("丙", 0.3), ("戊", 0.1)],
    "卯": [("乙", 1.0)],
    "辰": [("戊", 0.6), ("乙", 0.3), ("癸", 0.1)],
    "巳": [("丙", 0.6), ("庚", 0.3), ("戊", 0.1)],
    "午": [("丁", 0.6), ("己", 0.4)],
    "未": [("己", 0.6), ("丁", 0.3), ("乙", 0.1)],
    "申": [("庚", 0.6), ("壬", 0.3), ("戊", 0.1)],
    "酉": [("辛", 1.0)],
    "戌": [("戊", 0.6), ("辛", 0.3), ("丁", 0.1)],
    "亥": [("壬", 0.7), ("甲", 0.3)],
}

# ─────────────────────────────────────────────────────────────────────────────
# 表6  十神对照（以日主天干为基准）
# 来源：《三命通会》卷三
# {(日干五行阴阳, 对象干五行阴阳): 十神名}
# ─────────────────────────────────────────────────────────────────────────────
# 规则: 我生=食神/伤官, 生我=正印/偏印, 我克=正财/偏财,
#       克我=正官/七杀, 同我=比肩/劫财
# 阴阳同→同性，阴阳异→异性
TEN_GOD_TABLE: dict[tuple[str, str, str, str], str] = {}

def _build_ten_god_table() -> None:
    """构建完整的十神对照表"""
    elements = ["wood", "fire", "earth", "metal", "water"]
    sheng = {  # 相生：a生b
        "wood": "fire", "fire": "earth", "earth": "metal",
        "metal": "water", "water": "wood"
    }
    ke = {  # 相克：a克b
        "wood": "earth", "earth": "water", "water": "fire",
        "fire": "metal", "metal": "wood"
    }
    sheng_rev = {v: k for k, v in sheng.items()}  # 生我
    ke_rev = {v: k for k, v in ke.items()}  # 克我

    for day_elem in elements:
        for day_yin_yang in ("yang", "yin"):
            for obj_elem in elements:
                for obj_yin_yang in ("yang", "yin"):
                    same_polarity = (day_yin_yang == obj_yin_yang)
                    rel = day_elem
                    if obj_elem == rel:
                        # 同我
                        ten_god = "比肩" if same_polarity else "劫财"
                    elif sheng.get(rel) == obj_elem:
                        # 我生
                        ten_god = "食神" if same_polarity else "伤官"
                    elif ke.get(rel) == obj_elem:
                        # 我克
                        ten_god = "正财" if same_polarity else "偏财"
                    elif sheng_rev.get(rel) == obj_elem:
                        # 生我
                        ten_god = "正印" if same_polarity else "偏印"
                    elif ke_rev.get(rel) == obj_elem:
                        # 克我
                        ten_god = "正官" if same_polarity else "七杀"
                    else:
                        continue
                    TEN_GOD_TABLE[(day_elem, day_yin_yang, obj_elem, obj_yin_yang)] = ten_god

_build_ten_god_table()


def get_ten_god(day_stem: str, obj_stem: str) -> str:
    """
    获取十神名称。
    :param day_stem: 日主天干，如"甲"
    :param obj_stem: 对象天干，如"庚"
    :return: 十神名，如"七杀"
    """
    if day_stem not in STEM_ELEMENT or obj_stem not in STEM_ELEMENT:
        return "未知"
    d_elem, d_yy = STEM_ELEMENT[day_stem]
    o_elem, o_yy = STEM_ELEMENT[obj_stem]
    return TEN_GOD_TABLE.get((d_elem, d_yy, o_elem, o_yy), "未知")


# ─────────────────────────────────────────────────────────────────────────────
# 表7  月令旺相休囚死（五行在12月中的旺衰状态）
# 来源：《三命通会》卷二 "五行旺相休囚死例"
# 月支对应五行旺相状态 {月支: {五行: 旺衰值(0-4, 4=旺)}}
# ─────────────────────────────────────────────────────────────────────────────
WANGXIANG: dict[str, dict[str, int]] = {
    #        wood fire earth metal water
    "寅": {"wood": 4, "fire": 3, "earth": 2, "metal": 0, "water": 1},
    "卯": {"wood": 4, "fire": 3, "earth": 2, "metal": 0, "water": 1},
    "辰": {"wood": 1, "fire": 2, "earth": 4, "metal": 3, "water": 0},
    "巳": {"wood": 0, "fire": 4, "earth": 3, "metal": 2, "water": 1},
    "午": {"wood": 0, "fire": 4, "earth": 3, "metal": 2, "water": 1},
    "未": {"wood": 1, "fire": 2, "earth": 4, "metal": 3, "water": 0},
    "申": {"wood": 0, "fire": 1, "earth": 2, "metal": 4, "water": 3},
    "酉": {"wood": 0, "fire": 1, "earth": 2, "metal": 4, "water": 3},
    "戌": {"wood": 1, "fire": 0, "earth": 4, "metal": 3, "water": 2},
    "亥": {"wood": 3, "fire": 0, "earth": 1, "metal": 2, "water": 4},
    "子": {"wood": 3, "fire": 0, "earth": 1, "metal": 2, "water": 4},
    "丑": {"wood": 1, "fire": 0, "earth": 4, "metal": 3, "water": 2},
}

# 旺衰值→名称
WANGXIANG_LABEL: dict[int, str] = {4: "旺", 3: "相", 2: "休", 1: "囚", 0: "死"}

# ─────────────────────────────────────────────────────────────────────────────
# 表8  地支六冲 {支: 冲支}
# 来源：《三命通会》卷二
# ─────────────────────────────────────────────────────────────────────────────
BRANCH_CHONG: dict[str, str] = {
    "子": "午", "午": "子",
    "丑": "未", "未": "丑",
    "寅": "申", "申": "寅",
    "卯": "酉", "酉": "卯",
    "辰": "戌", "戌": "辰",
    "巳": "亥", "亥": "巳",
}

# ─────────────────────────────────────────────────────────────────────────────
# 表9  地支三合局（含成局五行）
# 来源：《三命通会》卷二
# ─────────────────────────────────────────────────────────────────────────────
SAN_HE: list[tuple[tuple[str, str, str], str]] = [
    (("申", "子", "辰"), "water"),
    (("亥", "卯", "未"), "wood"),
    (("寅", "午", "戌"), "fire"),
    (("巳", "酉", "丑"), "metal"),
]

# 地支六合 {支: 合支}
LIU_HE: dict[str, str] = {
    "子": "丑", "丑": "子",
    "寅": "亥", "亥": "寅",
    "卯": "戌", "戌": "卯",
    "辰": "酉", "酉": "辰",
    "巳": "申", "申": "巳",
    "午": "未", "未": "午",
}

# ─────────────────────────────────────────────────────────────────────────────
# 表10  纳音五行（60甲子纳音，每对干支对应一种纳音）
# 来源：《三命通会》卷二
# 共60条（由 self_check 验证）
# ─────────────────────────────────────────────────────────────────────────────
NAYIN: dict[str, str] = {
    "甲子": "海中金", "乙丑": "海中金",
    "丙寅": "炉中火", "丁卯": "炉中火",
    "戊辰": "大林木", "己巳": "大林木",
    "庚午": "路旁土", "辛未": "路旁土",
    "壬申": "剑锋金", "癸酉": "剑锋金",
    "甲戌": "山头火", "乙亥": "山头火",
    "丙子": "涧下水", "丁丑": "涧下水",
    "戊寅": "城头土", "己卯": "城头土",
    "庚辰": "白蜡金", "辛巳": "白蜡金",
    "壬午": "杨柳木", "癸未": "杨柳木",
    "甲申": "泉中水", "乙酉": "泉中水",
    "丙戌": "屋上土", "丁亥": "屋上土",
    "戊子": "霹雳火", "己丑": "霹雳火",
    "庚寅": "松柏木", "辛卯": "松柏木",
    "壬辰": "长流水", "癸巳": "长流水",
    "甲午": "沙中金", "乙未": "沙中金",
    "丙申": "山下火", "丁酉": "山下火",
    "戊戌": "平地木", "己亥": "平地木",
    "庚子": "壁上土", "辛丑": "壁上土",
    "壬寅": "金箔金", "癸卯": "金箔金",
    "甲辰": "覆灯火", "乙巳": "覆灯火",
    "丙午": "天河水", "丁未": "天河水",
    "戊申": "大驿土", "己酉": "大驿土",
    "庚戌": "钗钏金", "辛亥": "钗钏金",
    "壬子": "桑柘木", "癸丑": "桑柘木",
    "甲寅": "大溪水", "乙卯": "大溪水",
    "丙辰": "沙中土", "丁巳": "沙中土",
    "戊午": "天上火", "己未": "天上火",
    "庚申": "石榴木", "辛酉": "石榴木",
    "壬戌": "大海水", "癸亥": "大海水",
}

# ─────────────────────────────────────────────────────────────────────────────
# 表11  空亡（六旬旬空，每旬2支空亡）
# 来源：《三命通会》卷二 "论空亡"
# {旬首天干: (空亡支1, 空亡支2)}
# 共6旬（由 self_check 验证）
# ─────────────────────────────────────────────────────────────────────────────
KONGWANG: dict[str, tuple[str, str]] = {
    "甲子": ("戌", "亥"),
    "甲戌": ("申", "酉"),
    "甲申": ("午", "未"),
    "甲午": ("辰", "巳"),
    "甲辰": ("寅", "卯"),
    "甲寅": ("子", "丑"),
}


def get_kongwang(stem: str, branch: str) -> tuple[str, str]:
    """
    根据干支求该柱所属旬的空亡支。
    :param stem: 天干，如"甲"
    :param branch: 地支，如"子"
    :return: (空亡支1, 空亡支2)
    """
    stem_idx = STEMS.index(stem)
    branch_idx = BRANCHES.index(branch)
    # 旬首: 同组的甲干对应地支
    xun_branch_idx = branch_idx % 12
    # 找旬首: stem_idx%10 与 branch_idx%12 关系
    # 旬首天干必定是甲，地支从子到亥每10步一旬
    # 找旬首地支: xun_start = branch_idx - (branch_idx - stem_idx*1) % 10
    offset = (branch_idx - stem_idx) % 10
    xun_start_branch_idx = (branch_idx - offset) % 12
    xun_branch = BRANCHES[xun_start_branch_idx]
    key = f"甲{xun_branch}"
    return KONGWANG.get(key, ("未知", "未知"))


# ─────────────────────────────────────────────────────────────────────────────
# 神煞查找基础数据（供 shensha.py 使用）
# ─────────────────────────────────────────────────────────────────────────────

# 天乙贵人 {日干: [贵人地支]}
TIANYI_GUIREN: dict[str, list[str]] = {
    "甲": ["丑", "未"],
    "乙": ["子", "申"],
    "丙": ["亥", "酉"],
    "丁": ["亥", "酉"],
    "戊": ["丑", "未"],
    "己": ["子", "申"],
    "庚": ["丑", "未"],
    "辛": ["寅", "午"],
    "壬": ["卯", "巳"],
    "癸": ["卯", "巳"],
}

# 文昌贵人 {日干: 文昌地支}
WENCHANG_GUIREN: dict[str, str] = {
    "甲": "巳", "乙": "午", "丙": "申", "丁": "酉",
    "戊": "申", "己": "酉", "庚": "亥", "辛": "子",
    "壬": "寅", "癸": "卯",
}

# 驿马 {年/日支所在地支组: 驿马支}
YIMA: dict[str, str] = {
    "申": "寅", "子": "寅", "辰": "寅",
    "寅": "申", "午": "申", "戌": "申",
    "亥": "巳", "卯": "巳", "未": "巳",
    "巳": "亥", "酉": "亥", "丑": "亥",
}

# 桃花（咸池） {年/日支所在三合首: 桃花支}
TAOHUA: dict[str, str] = {
    "申": "酉", "子": "酉", "辰": "酉",
    "寅": "卯", "午": "卯", "戌": "卯",
    "亥": "子", "卯": "子", "未": "子",
    "巳": "午", "酉": "午", "丑": "午",
}

# 劫煞 {年/日支三合尾支: 劫煞支}
JIESHA: dict[str, str] = {
    "申": "巳", "子": "巳", "辰": "巳",
    "寅": "亥", "午": "亥", "戌": "亥",
    "亥": "申", "卯": "申", "未": "申",
    "巳": "寅", "酉": "寅", "丑": "寅",
}

# 亡神 {三合首: 亡神支}
WANGSHEN: dict[str, str] = {
    "申": "亥", "子": "亥", "辰": "亥",
    "寅": "巳", "午": "巳", "戌": "巳",
    "亥": "寅", "卯": "寅", "未": "寅",
    "巳": "申", "酉": "申", "丑": "申",
}


# ─────────────────────────────────────────────────────────────────────────────
# self_check() — 验证所有查找表完整性
# ─────────────────────────────────────────────────────────────────────────────

def self_check() -> None:
    """运行所有查找表的完整性校验。启动时调用一次。"""
    # 表1: 天干10条
    assert len(STEMS) == 10, f"STEMS should have 10 entries, got {len(STEMS)}"

    # 表2: 地支12条
    assert len(BRANCHES) == 12, f"BRANCHES should have 12 entries, got {len(BRANCHES)}"

    # 表3: 天干五行10条
    assert len(STEM_ELEMENT) == 10, f"STEM_ELEMENT should have 10 entries"

    # 表4: 地支五行12条
    assert len(BRANCH_ELEMENT) == 12, f"BRANCH_ELEMENT should have 12 entries"

    # 表5: 藏干权重和 = 1.0
    for branch, hidden in BRANCH_HIDDEN_STEMS.items():
        total = sum(w for _, w in hidden)
        assert abs(total - 1.0) < 1e-9, (
            f"BRANCH_HIDDEN_STEMS[{branch}] weights sum to {total}, expected 1.0"
        )
    assert len(BRANCH_HIDDEN_STEMS) == 12, "BRANCH_HIDDEN_STEMS should have 12 entries"

    # 表6: 十神表应含所有组合
    assert len(TEN_GOD_TABLE) == 100, (
        f"TEN_GOD_TABLE should have 100 entries (10x10), got {len(TEN_GOD_TABLE)}"
    )

    # 表7: 月令旺衰12支
    assert len(WANGXIANG) == 12, f"WANGXIANG should have 12 entries"
    for branch, vals in WANGXIANG.items():
        assert set(vals.keys()) == {"wood", "fire", "earth", "metal", "water"}, (
            f"WANGXIANG[{branch}] missing elements"
        )

    # 表8: 六冲12条（6对）
    assert len(BRANCH_CHONG) == 12, f"BRANCH_CHONG should have 12 entries"
    for a, b in BRANCH_CHONG.items():
        assert BRANCH_CHONG[b] == a, f"BRANCH_CHONG not symmetric for {a}"

    # 表9: 三合4局
    assert len(SAN_HE) == 4, f"SAN_HE should have 4 entries"

    # 表10: 纳音60条
    assert len(NAYIN) == 60, f"NAYIN should have 60 entries, got {len(NAYIN)}"

    # 表11: 空亡6旬
    assert len(KONGWANG) == 6, f"KONGWANG should have 6 entries, got {len(KONGWANG)}"


# 模块加载时立即自检
self_check()
