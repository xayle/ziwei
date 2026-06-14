"""
services/bazi_engine/lifestyle/fengshui.py — 风水方位引擎 (M2.5 任务 2.53)
"""

from __future__ import annotations

from app.schemas.analysis import FengshuiModel

# 五行→吉方
_ELEMENT_DIRECTION: dict[str, str] = {
    "wood": "东方/东南方",
    "fire": "南方",
    "earth": "中部/西南/东北",
    "metal": "西方/西北方",
    "water": "北方",
}

# 五行→装饰建议
_ELEMENT_DECOR: dict[str, str] = {
    "wood": "绿植盆栽、木质家具、竹帘",
    "fire": "暖光灯、红色或橙色装饰、蜡烛",
    "earth": "陶瓷摆件、土黄或米色沙发、石材台面",
    "metal": "金属装饰品、白色/灰色家具、圆形吊灯",
    "water": "鱼缸/流水摆件、蓝黑色系装饰",
}

# 五行→植物
_ELEMENT_PLANT: dict[str, str] = {
    "wood": "发财树/富贵竹",
    "fire": "火鹤花/玫瑰",
    "earth": "多肉植物/仙人掌",
    "metal": "铁树/万年青",
    "water": "水培植物/水仙",
}

# 五行→幸运色
_ELEMENT_COLOR: dict[str, list[str]] = {
    "wood": ["绿色", "青色", "深绿"],
    "fire": ["红色", "橙色", "紫色"],
    "earth": ["黄色", "棕色", "米色"],
    "metal": ["白色", "金色", "银色"],
    "water": ["黑色", "蓝色", "深蓝"],
}

# 忌神→禁忌方位/颜色
_ELEMENT_TABOO_DIRECTION: dict[str, str] = {
    "wood": "东方过度绿化",
    "fire": "南方过多红色",
    "earth": "中央过多重物",
    "metal": "西方金属过多",
    "water": "北方潮湿阴暗",
}

_ELEMENT_CN: dict[str, str] = {
    "metal": "金",
    "wood": "木",
    "water": "水",
    "fire": "火",
    "earth": "土",
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
            # 按房间拆分补充装饰建议
            if el == "wood":
                decor_list.append("书房放置绿植与竹编书架，引动木气")
                decor_list.append("卧室选用原木床架与棉麻床品，增益睡眠")
            elif el == "fire":
                decor_list.append("客厅挂暖色调装饰画，激活火能量")
                decor_list.append("书房点燃香薰蜡烛或暖光台灯，助集中")
            elif el == "earth":
                decor_list.append("玄关摆放陶土盆景或石材摆件，稳固入口气场")
                decor_list.append("餐厅选用土黄色桌布，助脾胃消化")
            elif el == "metal":
                decor_list.append("客厅悬挂圆形金属艺术品，聚气旺财")
                decor_list.append("书房用白色或银灰色收纳系统，利于思维清晰")
            elif el == "water":
                decor_list.append("玄关放置流水摆件或小型鱼缸，引动财水")
                decor_list.append("卧室使用蓝灰色系窗帘，助眠宁神")
        p = _ELEMENT_PLANT.get(el, "")
        if p and p not in plants:
            plants.append(p)
        for c in _ELEMENT_COLOR.get(el, []):
            if c not in lucky_colors:
                lucky_colors.append(c)

    for el in yongshen_avoid[:2]:
        t = _ELEMENT_TABOO_DIRECTION.get(el, "")
        if t:
            reason_map = {
                "wood": "过度绿化会加重木气郁结，引发情绪压抑",
                "fire": "过多红色在忌火命局中会引发躁动不安",
                "earth": "中央堆重物阻断气流，影响整体运势流通",
                "metal": "金属陈设过多会加重利器之气，影响人际",
                "water": "北方潮湿阴暗会使水气凝滞，耗损精力",
            }
            reason = reason_map.get(el, "忌神五行过旺会干扰命局平衡")
            taboo.append(f"{t}（原因：{reason}）")

    if not auspicious_directions:
        auspicious_directions = ["东南方"]
    if not lucky_colors:
        lucky_colors = ["黄色", "棕色"]

    _ys_cn = "、".join(_ELEMENT_CN.get(e, e) for e in yongshen_favor[:2])
    _dirs = "、".join(auspicious_directions[:2])
    _colors = "、".join(lucky_colors[:3])
    _plant_top = plants[0] if plants else "绿植"
    interp = (
        f"用神五行（{_ys_cn}）对应吉方为【{_dirs}】，可在该方位强化布置以汇聚气场。"
        f"室内装饰建议以【{_colors}】为主色调，搭配{_plant_top}等植物增添生机。"
        f"{'以下方位/颜色需规避：' + '；'.join(taboo[:2]) + '。' if taboo else '忌神方位无明显风险，整体布局较为均衡。'}"
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
