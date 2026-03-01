"""
services/bazi_engine/lifestyle/fengshui.py — 风水方位引擎 (M2.5 任务 2.53)
"""
from __future__ import annotations

from app.schemas.analysis import FengshuiModel

# 五行→吉方
_ELEMENT_DIRECTION: dict[str, str] = {
    "wood":  "东方/东南方",
    "fire":  "南方",
    "earth": "中部/西南/东北",
    "metal": "西方/西北方",
    "water": "北方",
}

# 五行→装饰建议
_ELEMENT_DECOR: dict[str, str] = {
    "wood":  "绿植盆栽、木质家具、竹帘",
    "fire":  "暖光灯、红色或橙色装饰、蜡烛",
    "earth": "陶瓷摆件、土黄或米色沙发、石材台面",
    "metal": "金属装饰品、白色/灰色家具、圆形吊灯",
    "water": "鱼缸/流水摆件、蓝黑色系装饰",
}

# 五行→植物
_ELEMENT_PLANT: dict[str, str] = {
    "wood":  "发财树/富贵竹",
    "fire":  "火鹤花/玫瑰",
    "earth": "多肉植物/仙人掌",
    "metal": "铁树/万年青",
    "water": "水培植物/水仙",
}

# 五行→幸运色
_ELEMENT_COLOR: dict[str, list[str]] = {
    "wood":  ["绿色", "青色", "深绿"],
    "fire":  ["红色", "橙色", "紫色"],
    "earth": ["黄色", "棕色", "米色"],
    "metal": ["白色", "金色", "银色"],
    "water": ["黑色", "蓝色", "深蓝"],
}

# 忌神→禁忌方位/颜色
_ELEMENT_TABOO_DIRECTION: dict[str, str] = {
    "wood":  "东方过度绿化",
    "fire":  "南方过多红色",
    "earth": "中央过多重物",
    "metal": "西方金属过多",
    "water": "北方潮湿阴暗",
}

_ELEMENT_CN: dict[str, str] = {
    "metal": "金", "wood": "木", "water": "水", "fire": "火", "earth": "土",
}


def compute_fengshui(
    yongshen_favor: list[str],
    yongshen_avoid: list[str],
) -> FengshuiModel:
    """
    根据用神/忌神给出风水方位、家居布置建议。
    """
    auspicious_directions: list[str] = []
    decor_list: list[str] = []
    plants: list[str] = []
    lucky_colors: list[str] = []
    taboo: list[str] = []

    for el in yongshen_favor[:3]:
        d = _ELEMENT_DIRECTION.get(el, "")
        if d and d not in auspicious_directions:
            auspicious_directions.append(d)
        d2 = _ELEMENT_DECOR.get(el, "")
        if d2 and d2 not in decor_list:
            decor_list.append(d2)
        p = _ELEMENT_PLANT.get(el, "")
        if p and p not in plants:
            plants.append(p)
        for c in _ELEMENT_COLOR.get(el, []):
            if c not in lucky_colors:
                lucky_colors.append(c)

    for el in yongshen_avoid[:2]:
        t = _ELEMENT_TABOO_DIRECTION.get(el, "")
        if t:
            taboo.append(t)

    if not auspicious_directions:
        auspicious_directions = ["东南方"]
    if not lucky_colors:
        lucky_colors = ["黄色", "棕色"]

    interp = (
        f"用神五行（{'、'.join(_ELEMENT_CN.get(e,e) for e in yongshen_favor[:2])}）对应"
        f"吉方为{'、'.join(auspicious_directions[:2])}，可在该方位强化布置。"
        f"（仅供学术研究参考）"
    )

    return FengshuiModel(
        auspicious_directions=auspicious_directions,
        decor=decor_list,
        plants=plants,
        lucky_colors=lucky_colors,
        taboo=taboo,
        interpretation_text=interp,
    )
