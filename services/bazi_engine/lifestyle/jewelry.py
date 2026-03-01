"""
services/bazi_engine/lifestyle/jewelry.py — 首饰/配饰推荐引擎 (M2.5 任务 2.52)
"""
from __future__ import annotations

from app.schemas.analysis import JewelryModel, JewelryItemModel

# 五行→贵金属/宝石推荐
_ELEMENT_MATERIAL: dict[str, str] = {
    "metal": "银/白金/铂金",
    "wood":  "绿松石/翡翠金",
    "water": "黑玛瑙/铂金",
    "fire":  "玫瑰金/黄金",
    "earth": "黄金/土黄系石",
}

_ELEMENT_GEMSTONE: dict[str, str] = {
    "metal": "白水晶/白色玉石",
    "wood":  "绿翡翠/碧玺",
    "water": "蓝宝石/海蓝宝",
    "fire":  "红宝石/石榴石",
    "earth": "黄水晶/虎眼石",
}

_ELEMENT_POSITION: dict[str, str] = {
    "metal": "右手/右腕",
    "wood":  "左手/左腕",
    "water": "颈部",
    "fire":  "耳饰/耳环",
    "earth": "腰带/腰部配件",
}

_ELEMENT_CN: dict[str, str] = {
    "metal": "金", "wood": "木", "water": "水", "fire": "火", "earth": "土",
}

# 忌神对应禁忌材质
_ELEMENT_TABOO_MATERIAL: dict[str, str] = {
    "metal": "铁器/黑色金属",
    "wood":  "木制大件",
    "water": "深蓝/黑色宝石",
    "fire":  "红色/橙色饰品",
    "earth": "土黄系饰品",
}


def compute_jewelry(
    yongshen_favor: list[str],
    yongshen_avoid: list[str],
) -> JewelryModel:
    """
    根据用神/忌神推荐首饰配饰。
    """
    primary_list: list[JewelryItemModel] = []
    secondary_list: list[JewelryItemModel] = []
    taboo: list[str] = []

    for el in yongshen_favor[:2]:
        primary_list.append(JewelryItemModel(
            material=_ELEMENT_MATERIAL.get(el, "黄金"),
            gemstone=_ELEMENT_GEMSTONE.get(el, "白水晶"),
            position=_ELEMENT_POSITION.get(el, "任意"),
            wuxing=_ELEMENT_CN.get(el, el),
        ))

    for el in yongshen_favor[2:4]:
        secondary_list.append(JewelryItemModel(
            material=_ELEMENT_MATERIAL.get(el, "银"),
            gemstone=_ELEMENT_GEMSTONE.get(el, "玉石"),
            position=_ELEMENT_POSITION.get(el, "任意"),
            wuxing=_ELEMENT_CN.get(el, el),
        ))

    for el in yongshen_avoid[:2]:
        taboo.append(_ELEMENT_TABOO_MATERIAL.get(el, el))

    if not primary_list:
        primary_list = [JewelryItemModel(
            material="黄金", gemstone="黄水晶", position="右腕", wuxing="土",
        )]

    combination = (
        "主饰用神五行材质为核，配饰辅助协调整体气场，禁忌材质请避免叠戴。"
    )
    interp = (
        f"推荐用神五行（{'、'.join(_ELEMENT_CN.get(e,e) for e in yongshen_favor[:2])}）"
        f"对应首饰，有助提升运势气场。（仅供学术研究参考）"
    )

    primary_item   = primary_list[0] if primary_list else JewelryItemModel(
        material="黄金", gemstone="黄水晶", position="右腕", wuxing="土",
    )
    secondary_item = secondary_list[0] if secondary_list else JewelryItemModel(
        material="银", gemstone="白水晶", position="左腕", wuxing="金",
    )

    return JewelryModel(
        primary=primary_item,
        secondary=secondary_item,
        combination=combination,
        taboo=taboo,
        interpretation_text=interp,
    )
