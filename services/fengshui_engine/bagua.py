"""
services/fengshui_engine/bagua.py — §15 八宅风水方位推荐

算法基础：八宅明镜派（八宅法）
================================
1. 根据出生年份与性别计算**命卦**（1-9，无5）
2. 按命卦查八方吉凶表（四吉：生气/天医/延年/伏位；四凶：绝命/五鬼/六煞/祸害）
3. 可选：提供房屋朝向 → 推算房屋卦 → 人宅相合判断
4. 推荐床头/书桌/大门最佳朝向

命卦计算
--------
利用出生年份**后两位**求数字根，再按公式：
  - 1900–1999 男：10 − 数字根；女：数字根 + 5
  - 2000 后   男：9  − 数字根；女：数字根 + 6
结果若为 5，男取 2，女取 8；若为 0，取 9。

免责声明
--------
本模块仅供参考/研究用途，不构成任何专业风水指导建议。
所有建议均应理性评估并结合实际情况，如涉及结构改动请咨询专业人士。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

# ─────────────────────────────────────────────────────────────
# 方向常量
# ─────────────────────────────────────────────────────────────

# 八方向英文缩写（顺时针，从北开始）
DIRECTIONS: list[str] = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]

DIRECTIONS_ZH: dict[str, str] = {
    "N":  "北",
    "NE": "东北",
    "E":  "东",
    "SE": "东南",
    "S":  "南",
    "SW": "西南",
    "W":  "西",
    "NW": "西北",
}

# 可选的房屋朝向（用于前端下拉）
HOUSE_FACING_OPTIONS: dict[str, str] = {
    "N":  "坐南朝北（坎宅）",
    "NE": "坐西南朝东北（艮宅）",
    "E":  "坐西朝东（震宅）",
    "SE": "坐西北朝东南（巽宅）",
    "S":  "坐北朝南（离宅）",
    "SW": "坐东北朝西南（坤宅）",
    "W":  "坐东朝西（兑宅）",
    "NW": "坐东南朝西北（乾宅）",
}

# ─────────────────────────────────────────────────────────────
# 命卦属性
# ─────────────────────────────────────────────────────────────

_GUA_NAME: dict[int, str] = {
    1: "坎", 2: "坤", 3: "震", 4: "巽",
    6: "乾", 7: "兑", 8: "艮", 9: "离",
}

_GUA_ELEMENT: dict[int, str] = {
    1: "水", 2: "土", 3: "木", 4: "木",
    6: "金", 7: "金", 8: "土", 9: "火",
}

# 东四命 / 西四命
_EAST_GROUP = frozenset({1, 3, 4, 9})
_WEST_GROUP = frozenset({2, 6, 7, 8})

# ─────────────────────────────────────────────────────────────
# 八宅方位吉凶表
# 数据来源：《八宅明镜》标准表
# 格式：命卦 → {能量标签: 方向英文}
# ─────────────────────────────────────────────────────────────

_GUA_TABLE: dict[int, dict[str, str]] = {
    1: {  # 坎卦（东四命）
        "生气": "SE", "天医": "E",  "延年": "S",  "伏位": "N",
        "绝命": "NW", "五鬼": "NE", "六煞": "W",  "祸害": "SW",
    },
    2: {  # 坤卦（西四命）
        "生气": "NE", "天医": "W",  "延年": "NW", "伏位": "SW",
        "绝命": "S",  "五鬼": "E",  "六煞": "SE", "祸害": "N",
    },
    3: {  # 震卦（东四命）
        "生气": "S",  "天医": "N",  "延年": "SE", "伏位": "E",
        "绝命": "NE", "五鬼": "SW", "六煞": "NW", "祸害": "W",
    },
    4: {  # 巽卦（东四命）
        "生气": "N",  "天医": "S",  "延年": "E",  "伏位": "SE",
        "绝命": "W",  "五鬼": "NW", "六煞": "SW", "祸害": "NE",
    },
    6: {  # 乾卦（西四命）
        "生气": "W",  "天医": "NE", "延年": "SW", "伏位": "NW",
        "绝命": "S",  "五鬼": "SE", "六煞": "E",  "祸害": "N",
    },
    7: {  # 兑卦（西四命）
        "生气": "NW", "天医": "SW", "延年": "NE", "伏位": "W",
        "绝命": "E",  "五鬼": "N",  "六煞": "S",  "祸害": "SE",
    },
    8: {  # 艮卦（西四命）
        "生气": "SW", "天医": "NW", "延年": "W",  "伏位": "NE",
        "绝命": "E",  "五鬼": "S",  "六煞": "N",  "祸害": "SE",
    },
    9: {  # 离卦（东四命）
        "生气": "E",  "天医": "SE", "延年": "N",  "伏位": "S",
        "绝命": "SW", "五鬼": "W",  "六煞": "NE", "祸害": "NW",
    },
}

# 吉凶级别与说明
_LABEL_INFO: dict[str, dict[str, str]] = {
    "生气": {
        "level": "最吉", "level_css": "ji1",
        "desc": "生气方：旺气最盛，宜卧室床头、办公桌面向此方，可增旺财运与贵人缘。",
    },
    "天医": {
        "level": "大吉", "level_css": "ji2",
        "desc": "天医方：利健康、调养，宜卧室床头面向。年迈或体弱者可优先选此方。",
    },
    "延年": {
        "level": "吉",   "level_css": "ji3",
        "desc": "延年方：利婚姻、感情、事业持久，宜大门或主卧面向。",
    },
    "伏位": {
        "level": "小吉", "level_css": "ji4",
        "desc": "伏位方：稳定本命，宜书房、储藏室，不宜主卧长期使用。",
    },
    "祸害": {
        "level": "小凶", "level_css": "xiong4",
        "desc": "祸害方：易引发口舌是非，宜将此方设为卫生间/杂物间，不宜主要居住。",
    },
    "六煞": {
        "level": "凶",   "level_css": "xiong3",
        "desc": "六煞方：影响健康与人际，不宜卧室床头面向，可放置重物压制。",
    },
    "五鬼": {
        "level": "大凶", "level_css": "xiong2",
        "desc": "五鬼方：易生意外与小人，不宜大门、卧室，可用屏风/柜橱遮挡。",
    },
    "绝命": {
        "level": "最凶", "level_css": "xiong1",
        "desc": "绝命方：影响最重，应避免卧室与大门朝向此方，可设卫生间/储藏室以泄化。",
    },
}

# 房屋朝向 → 房屋卦数
_FACING_TO_GUA: dict[str, int] = {
    "N": 1, "NE": 8, "E": 3, "SE": 4,
    "S": 9, "SW": 2, "W": 7, "NW": 6,
}


# ─────────────────────────────────────────────────────────────
# 计算命卦
# ─────────────────────────────────────────────────────────────

def _digit_root(n: int) -> int:
    """计算数字根（迭代求各位数之和直至单位数）。"""
    while n >= 10:
        n = sum(int(d) for d in str(n))
    return n


def calc_life_gua(birth_year: int, gender: str) -> int:
    """
    计算命卦数（1-9，无5）。

    参数
    ----
    birth_year : 出生公历年份（如 1985）
    gender     : "男" 或 "女"

    返回
    ----
    命卦数（1/2/3/4/6/7/8/9）
    """
    y = _digit_root(birth_year % 100)

    if birth_year < 2000:
        gua = (10 - y) if gender != "女" else (y + 5)
    else:
        gua = (9 - y) if gender != "女" else (y + 6)

    gua = _digit_root(gua)

    if gua == 0:
        gua = 9
    if gua == 5:
        gua = 2 if gender != "女" else 8

    return gua


# ─────────────────────────────────────────────────────────────
# 数据结构
# ─────────────────────────────────────────────────────────────

@dataclass
class DirectionItem:
    """单方向吉凶条目。"""
    direction: str       # "N" / "NE" …
    direction_zh: str    # "北" / "东北" …
    label: str           # 生气/天医/延年/伏位/祸害/六煞/五鬼/绝命
    level: str           # 最吉/大吉/吉/小吉/小凶/凶/大凶/最凶
    level_css: str       # ji1/ji2/ji3/ji4/xiong4/xiong3/xiong2/xiong1
    desc: str            # 说明文字


@dataclass
class FurnitureTip:
    """家具方位建议。"""
    item: str            # 床头/书桌/大门
    direction: str       # "SE"
    direction_zh: str    # "东南"
    label: str           # 生气
    reason: str          # 说明


@dataclass
class BaguaResult:
    """八宅命卦完整分析结果。"""
    life_gua: int
    gua_name: str
    gua_element: str
    group: str                         # 东四命 / 西四命
    birth_year: int
    gender: str

    auspicious: list[DirectionItem] = field(default_factory=list)    # 四吉（排序：生气、天医、延年、伏位）
    inauspicious: list[DirectionItem] = field(default_factory=list)  # 四凶

    # 家具建议
    bed_tip: Optional[FurnitureTip] = None
    desk_tip: Optional[FurnitureTip] = None
    door_tip: Optional[FurnitureTip] = None

    # 房屋信息（可选）
    house_facing: Optional[str] = None
    house_gua: Optional[int] = None
    house_gua_name: Optional[str] = None
    house_group: Optional[str] = None
    compatibility: Optional[str] = None    # 相合 / 不合
    compatibility_note: Optional[str] = None

    disclaimer: str = (
        "温馨提示：以下分析仅基于八宅派理论供参考，不构成专业风水指导建议。"
        "如需改动房屋结构，请咨询专业人士并结合实际情况做出理性判断。"
    )


# ─────────────────────────────────────────────────────────────
# 主计算函数
# ─────────────────────────────────────────────────────────────

def calc_bagua(
    birth_year: int,
    gender: str,
    house_facing: Optional[str] = None,
) -> BaguaResult:
    """
    计算八宅命卦与方位建议。

    参数
    ----
    birth_year   : 出生年份（公历）
    gender       : "男" 或 "女"
    house_facing : 房屋朝向（如 "S"=朝南），可选
    """
    life_gua = calc_life_gua(birth_year, gender)
    gua_table = _GUA_TABLE[life_gua]
    group = "东四命" if life_gua in _EAST_GROUP else "西四命"

    # 构建吉凶方向列表
    ji_labels = ["生气", "天医", "延年", "伏位"]
    xiong_labels = ["绝命", "五鬼", "六煞", "祸害"]

    auspicious: list[DirectionItem] = []
    for lab in ji_labels:
        d = gua_table[lab]
        info = _LABEL_INFO[lab]
        auspicious.append(DirectionItem(
            direction=d, direction_zh=DIRECTIONS_ZH[d],
            label=lab, level=info["level"], level_css=info["level_css"],
            desc=info["desc"],
        ))

    inauspicious: list[DirectionItem] = []
    for lab in xiong_labels:
        d = gua_table[lab]
        info = _LABEL_INFO[lab]
        inauspicious.append(DirectionItem(
            direction=d, direction_zh=DIRECTIONS_ZH[d],
            label=lab, level=info["level"], level_css=info["level_css"],
            desc=info["desc"],
        ))

    # 家具建议
    bed_dir = gua_table["天医"]      # 床头：天医（利健康）
    desk_dir = gua_table["生气"]    # 书桌：生气（旺运）
    door_dir = gua_table["生气"]    # 大门首选生气
    # 若生气与床重合，大门可选延年
    if door_dir == bed_dir:
        door_dir = gua_table["延年"]

    def _tip(item: str, d: str, lab: str) -> FurnitureTip:
        info = _LABEL_INFO[lab]
        return FurnitureTip(
            item=item, direction=d, direction_zh=DIRECTIONS_ZH[d],
            label=lab, reason=info["desc"],
        )

    bed_tip  = _tip("床头朝向",   bed_dir,  "天医")
    desk_tip = _tip("书桌/工位面向", desk_dir, "生气")
    door_tip = _tip("大门朝向",   gua_table["生气"], "生气")

    # 房屋判断（可选）
    house_gua: Optional[int] = None
    house_gua_name: Optional[str] = None
    house_group: Optional[str] = None
    compatibility: Optional[str] = None
    compatibility_note: Optional[str] = None

    if house_facing and house_facing in _FACING_TO_GUA:
        house_gua = _FACING_TO_GUA[house_facing]
        house_gua_name = _GUA_NAME[house_gua]
        house_group = "东四宅" if house_gua in _EAST_GROUP else "西四宅"

        person_group_type = "东" if life_gua in _EAST_GROUP else "西"
        house_group_type  = "东" if house_gua  in _EAST_GROUP else "西"

        if person_group_type == house_group_type:
            compatibility = "相合"
            compatibility_note = (
                f"您属于{group}（{_GUA_NAME[life_gua]}卦），"
                f"该房屋属于{house_group}（{house_gua_name}卦），"
                "方位相合，有助于整体运势；四吉方即为您在此宅中的最优方位。"
            )
        else:
            compatibility = "不合"
            compatibility_note = (
                f"您属于{group}（{_GUA_NAME[life_gua]}卦），"
                f"该房屋属于{house_group}（{house_gua_name}卦），"
                "人宅不合——建议通过合理布局（将卧室/书房安置于个人命卦的四吉方）来调和。"
            )

    return BaguaResult(
        life_gua=life_gua,
        gua_name=_GUA_NAME[life_gua],
        gua_element=_GUA_ELEMENT[life_gua],
        group=group,
        birth_year=birth_year,
        gender=gender,
        auspicious=auspicious,
        inauspicious=inauspicious,
        bed_tip=bed_tip,
        desk_tip=desk_tip,
        door_tip=door_tip,
        house_facing=house_facing,
        house_gua=house_gua,
        house_gua_name=house_gua_name,
        house_group=house_group,
        compatibility=compatibility,
        compatibility_note=compatibility_note,
    )
