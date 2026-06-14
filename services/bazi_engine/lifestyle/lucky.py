"""
services/bazi_engine/lifestyle/lucky.py — 开运数字/颜色/方位引擎 (M2.5 任务 2.54)
"""

from __future__ import annotations

from app.schemas.analysis import LuckyModel

# 五行→幸运数字
_ELEMENT_NUMBERS: dict[str, list[int]] = {
    "wood": [3, 4, 8],
    "fire": [2, 7, 9],
    "earth": [5, 0, 8],
    "metal": [4, 9, 1],
    "water": [1, 6, 3],
}

# 五行→幸运颜色
_ELEMENT_COLOR: dict[str, list[str]] = {
    "wood": ["绿色", "青色"],
    "fire": ["红色", "紫色"],
    "earth": ["黄色", "棕色"],
    "metal": ["白色", "金色"],
    "water": ["黑色", "蓝色"],
}

# 五行→幸运方向
_ELEMENT_DIRECTION: dict[str, str] = {
    "wood": "东方",
    "fire": "南方",
    "earth": "中部",
    "metal": "西方",
    "water": "北方",
}

# 五行→开运物品
_ELEMENT_ITEM: dict[str, str] = {
    "wood": "绿色植物/翡翠摆件",
    "fire": "红色香囊/玛瑙饰品",
    "earth": "黄水晶/土陶器皿",
    "metal": "白水晶/金属铃铛",
    "water": "蓝色宝石/流水摆件",
}

_ELEMENT_CN: dict[str, str] = {
    "metal": "金",
    "wood": "木",
    "water": "水",
    "fire": "火",
    "earth": "土",
}


def compute_lucky(
    yongshen_favor: list[str],
    yongshen_avoid: list[str],
) -> LuckyModel:
    """
    根据用神五行计算幸运数字、颜色、方位、开运物。
    """
    lucky_colors: list[str] = []
    lucky_numbers: list[int] = []
    lucky_direction = ""
    lucky_item = ""

    for el in yongshen_favor[:2]:
        for c in _ELEMENT_COLOR.get(el, []):
            if c not in lucky_colors:
                lucky_colors.append(c)
        for n in _ELEMENT_NUMBERS.get(el, []):
            if n not in lucky_numbers:
                lucky_numbers.append(n)
        if not lucky_direction:
            lucky_direction = _ELEMENT_DIRECTION.get(el, "东方")
        if not lucky_item:
            lucky_item = _ELEMENT_ITEM.get(el, "白水晶")

    if not lucky_colors:
        lucky_colors = ["黄色"]
    if not lucky_numbers:
        lucky_numbers = [5, 8]
    if not lucky_direction:
        lucky_direction = "中部"

    # B7: 忌神颜色和忌神方位——忌神对应的生活用色应谨慎使用
    avoid_colors: list[str] = []
    avoid_direction = ""
    for el in yongshen_avoid[:2]:
        for c in _ELEMENT_COLOR.get(el, []):
            if c not in avoid_colors:
                avoid_colors.append(c)
        if not avoid_direction:
            avoid_direction = _ELEMENT_DIRECTION.get(el, "")

    el_cn = "、".join(_ELEMENT_CN.get(e, e) for e in yongshen_favor[:2])
    el_avoid_cn = "、".join(_ELEMENT_CN.get(e, e) for e in yongshen_avoid[:2])
    _colors_top = "、".join(lucky_colors[:2])
    _nums_top = "、".join(str(n) for n in lucky_numbers[:3])
    _avoid_colors_top = "、".join(avoid_colors[:2]) if avoid_colors else "无"
    interp = (
        f"用神五行为【{el_cn}】，幸运色为【{_colors_top}】，旺运数字为【{_nums_top}】。"
        f"旺运方位【{lucky_direction}】，出行、择座或开会时优先选择该方向可增添气场。"
        f"开运物「{lucky_item}」适合随身携带或置于工作桌上，在重要场合与面试、签约前使用效果更佳。"
        f"【忌神五行为{el_avoid_cn}】，日常穿搭建议谨慎使用忌色【{_avoid_colors_top}】"
        + (f"，忌神方位【{avoid_direction}】宜少居少占。" if avoid_direction else "。")
        + "将幸运色融入日常穿搭或配饰中，有助于在社交与职场中彰显个人磁场。"
        "（仅供学术研究参考）"
    )

    return LuckyModel(
        lucky_colors=lucky_colors,
        lucky_numbers=lucky_numbers,
        lucky_direction=lucky_direction,
        lucky_item=lucky_item,
        interpretation_text=interp,
        avoid_colors=avoid_colors,
        avoid_direction=avoid_direction,
    )
