"""
services/bazi_engine/lifestyle/tables.py — 五行→生活建议映射表

M1 任务 1.04:
  基础版 WUXING_TO_ORGAN（M2 health.py 需要此表）
  以及其余生活映射表：颜色/数字/方位/运动/饮食/植物/摆设

来源：传统命理学·五行养生对应关系
"""

from __future__ import annotations

# ─────────────────────────────────────────────────────────────────────────────
# WUXING_TO_ORGAN — 五行→脏腑 mapping（M2 health.py 核心依赖）
# ─────────────────────────────────────────────────────────────────────────────
WUXING_TO_ORGAN: dict[str, dict[str, list[str]]] = {
    "wood": {
        "zang": ["肝"],  # 五脏（主）
        "fu": ["胆"],  # 六腑
        "body": ["筋", "眼", "指甲"],
        "excess": ["肝火旺", "胆汁分泌异常", "眼睛疲劳"],
        "deficient": ["肝血不足", "视力模糊", "筋脉松弛"],
    },
    "fire": {
        "zang": ["心"],
        "fu": ["小肠"],
        "body": ["血脉", "舌", "面色"],
        "excess": ["心火上炎", "口舌生疮", "失眠多梦"],
        "deficient": ["心气虚", "心悸气短", "面色苍白"],
    },
    "earth": {
        "zang": ["脾"],
        "fu": ["胃"],
        "body": ["肌肉", "四肢", "唇"],
        "excess": ["脾胃湿热", "消化积滞", "腹胀"],
        "deficient": ["脾虚泄泻", "四肢无力", "食欲不振"],
    },
    "metal": {
        "zang": ["肺"],
        "fu": ["大肠"],
        "body": ["皮毛", "鼻", "呼吸道"],
        "excess": ["肺热咳嗽", "大肠燥热", "皮肤炎症"],
        "deficient": ["肺气虚", "皮肤干燥", "容易感冒"],
    },
    "water": {
        "zang": ["肾"],
        "fu": ["膀胱"],
        "body": ["骨", "髓", "耳", "发"],
        "excess": ["肾水泛滥", "下肢湿寒", "水肿"],
        "deficient": ["肾虚", "耳鸣", "骨质疏松", "发白早衰"],
    },
}


def get_risk_organs(wuxing_element: str, is_excess: bool = False) -> list[str]:
    """
    获取某五行对应的风险脏腑（偏旺取excess，偏弱取deficient症状描述）。
    :param wuxing_element: 五行名（wood/fire/earth/metal/water）
    :param is_excess: True=偏旺(过亢), False=偏弱(虚损)
    :return: 脏腑/症状描述列表
    """
    info = WUXING_TO_ORGAN.get(wuxing_element, {})
    organs = info.get("zang", []) + info.get("fu", [])
    symptoms = info.get("excess" if is_excess else "deficient", [])
    return organs + symptoms


# ─────────────────────────────────────────────────────────────────────────────
# WUXING_TO_COLOR — 五行→颜色（开运颜色、忌讳颜色）
# ─────────────────────────────────────────────────────────────────────────────
WUXING_TO_COLOR: dict[str, dict[str, list[str]]] = {
    "wood": {"lucky": ["绿色", "青色", "碧色"], "avoid": ["白色", "银色"]},
    "fire": {"lucky": ["红色", "粉色", "橙色"], "avoid": ["黑色", "深蓝"]},
    "earth": {"lucky": ["黄色", "土色", "棕色"], "avoid": ["绿色", "青色"]},
    "metal": {"lucky": ["白色", "金色", "银色"], "avoid": ["红色", "粉色"]},
    "water": {"lucky": ["黑色", "蓝色", "深灰"], "avoid": ["黄色", "土色"]},
}

# ─────────────────────────────────────────────────────────────────────────────
# WUXING_TO_DIRECTION — 五行→方位
# ─────────────────────────────────────────────────────────────────────────────
WUXING_TO_DIRECTION: dict[str, str] = {
    "wood": "东",
    "fire": "南",
    "earth": "中",
    "metal": "西",
    "water": "北",
}

# ─────────────────────────────────────────────────────────────────────────────
# WUXING_TO_NUMBER — 五行→幸运数字
# ─────────────────────────────────────────────────────────────────────────────
WUXING_TO_NUMBER: dict[str, list[int]] = {
    "wood": [3, 8],
    "fire": [2, 7],
    "earth": [5, 0],
    "metal": [4, 9],
    "water": [1, 6],
}

# ─────────────────────────────────────────────────────────────────────────────
# WUXING_TO_LIFESTYLE — 五行→运动/饮食/生活建议
# ─────────────────────────────────────────────────────────────────────────────
WUXING_TO_LIFESTYLE: dict[str, dict[str, list[str] | str]] = {
    "wood": {
        "exercise": ["瑜伽", "爬山", "跑步", "伸展运动"],
        "diet": ["绿叶蔬菜", "醋类食品", "枸杞", "菠菜"],
        "sleep": "晚22:30前入睡，避免熬夜伤肝",
        "tips": ["多在绿色环境中活动", "保持心情舒畅"],
    },
    "fire": {
        "exercise": ["有氧舞蹈", "跳绳", "团体运动", "太极"],
        "diet": ["红枣", "枸杞", "苦瓜", "莲子心"],
        "sleep": "午时（11-13时）小憩10-20分钟养心",
        "tips": ["情绪管理为首要", "避免剧烈情绪波动"],
    },
    "earth": {
        "exercise": ["散步", "太极拳", "八段锦", "游泳"],
        "diet": ["小米粥", "山药", "南瓜", "红薯"],
        "sleep": "规律饮食，饭后伏案休息20分钟",
        "tips": ["避免思虑过度", "保持饮食规律"],
    },
    "metal": {
        "exercise": ["游泳", "深呼吸练习", "慢跑", "高尔夫"],
        "diet": ["梨", "白萝卜", "百合", "银耳"],
        "sleep": "寅时（3-5时）为肺经当令，此时宜熟睡",
        "tips": ["保持室内空气清新", "戒烟酒"],
    },
    "water": {
        "exercise": ["游泳", "太极", "冥想", "慢走"],
        "diet": ["黑豆", "枸杞", "山药", "核桃", "黑芝麻"],
        "sleep": "子时（23-01时）前必须入睡养肾",
        "tips": ["避免熬夜", "保暖腰腹部"],
    },
}

# ─────────────────────────────────────────────────────────────────────────────
# WUXING_TO_FENGSHUI — 五行→风水摆设建议
# ─────────────────────────────────────────────────────────────────────────────
WUXING_TO_FENGSHUI: dict[str, dict[str, list[str]]] = {
    "wood": {
        "decor": ["木质家具", "绿色植物", "竹制品"],
        "plants": ["富贵竹", "绿萝", "常青藤"],
        "avoid": ["大量白色金属装饰", "超多西向摆设"],
    },
    "fire": {
        "decor": ["红色装饰品", "蜡烛", "南面摆设"],
        "plants": ["红掌", "凤梨", "向日葵"],
        "avoid": ["黑色大件物品", "大量水景正南"],
    },
    "earth": {
        "decor": ["陶瓷摆件", "黄色/土色装饰", "方形物件"],
        "plants": ["多肉植物", "石斛兰", "仙人球"],
        "avoid": ["大量绿植挤满空间"],
    },
    "metal": {
        "decor": ["金属工艺品", "白色装饰", "圆形物件"],
        "plants": ["白色兰花", "铁树", "吊兰"],
        "avoid": ["大量红色装饰", "南面大量火焰装饰"],
    },
    "water": {
        "decor": ["流水摆件", "蓝色/黑色装饰", "鱼缸（北面）"],
        "plants": ["荷花（盆栽）", "铜钱草", "水培植物"],
        "avoid": ["黄色大件土类装饰（正中）"],
    },
}

# ─────────────────────────────────────────────────────────────────────────────
# WUXING_TO_JEWELRY — 五行→饰品推荐
# ─────────────────────────────────────────────────────────────────────────────
WUXING_TO_JEWELRY: dict[str, dict[str, str]] = {
    "wood": {
        "material": "木质/翡翠/绿色玉石",
        "gemstone": "绿幽灵/碧玺/翡翠",
        "position": "手腕/颈部",
        "taboo": "避免过多纯白金属配件",
    },
    "fire": {
        "material": "红宝石/珊瑚/赤铁矿",
        "gemstone": "红宝石/石榴石/红玛瑙",
        "position": "手腕/左胸口袋",
        "taboo": "避免大量蓝黑宝石叠戴",
    },
    "earth": {
        "material": "黄水晶/蜜蜡/琥珀",
        "gemstone": "黄水晶/虎眼石/蜜蜡",
        "position": "中指/腹部",
        "taboo": "避免大量绿色或纯木质装饰",
    },
    "metal": {
        "material": "白金/铂金/银饰",
        "gemstone": "白水晶/月光石/钻石",
        "position": "手腕/颈部",
        "taboo": "避免过多红色宝石叠戴",
    },
    "water": {
        "material": "蓝宝石/青金石/黑曜石",
        "gemstone": "蓝宝石/海蓝宝/黑水晶",
        "position": "手腕/腰带扣",
        "taboo": "避免大量黄色/土色装饰",
    },
}


def self_check() -> None:
    """验证映射表完整性"""
    elements = {"wood", "fire", "earth", "metal", "water"}
    assert set(WUXING_TO_ORGAN.keys()) == elements
    assert set(WUXING_TO_COLOR.keys()) == elements
    assert set(WUXING_TO_DIRECTION.keys()) == elements
    assert set(WUXING_TO_NUMBER.keys()) == elements
    assert set(WUXING_TO_LIFESTYLE.keys()) == elements
    assert set(WUXING_TO_FENGSHUI.keys()) == elements
    assert set(WUXING_TO_JEWELRY.keys()) == elements
    # 每个 WUXING_TO_ORGAN 条目都含4个必须字段
    for elem, info in WUXING_TO_ORGAN.items():
        for key in ("zang", "fu", "body", "excess", "deficient"):
            assert key in info, f"WUXING_TO_ORGAN[{elem}] missing '{key}'"


self_check()
