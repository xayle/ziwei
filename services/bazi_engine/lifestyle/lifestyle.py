"""
services/bazi_engine/lifestyle/lifestyle.py — 生活方式引擎 (M2.5 任务 2.55)
"""
from __future__ import annotations

from app.schemas.analysis import LifestyleModel

# 五行→运动建议
_ELEMENT_EXERCISE: dict[str, str] = {
    "wood":  "太极、瑜伽、登山、林中慢跑",
    "fire":  "游泳、冥想、气功、低强度有氧",
    "earth": "快走、徒步、健身操",
    "metal": "户外呼吸运动、骑行、拳击",
    "water": "拉伸、水中运动、普拉提",
}

# 五行→最佳时间
_ELEMENT_BEST_TIMES: dict[str, str] = {
    "wood":  "寅时（3-5点）、卯时（5-7点）即早晨",
    "fire":  "午时（11-13点）阳气最旺",
    "earth": "巳时（9-11点）和申时（15-17点）",
    "metal": "酉时（17-19点）傍晚",
    "water": "子时（23-1点）或亥时（21-23点）",
}

# 五行→饮食
_ELEMENT_DIET: dict[str, str] = {
    "wood":  "多食绿色蔬菜（菠菜/韭菜），少辛辣",
    "fire":  "多食苦味食物（苦瓜/莲子），清心降火",
    "earth": "多食黄色食物（玉米/南瓜/小米），规律三餐",
    "metal": "多食白色食物（梨/山药/白萝卜），润肺",
    "water": "多食黑色食物（黑豆/核桃/黑芝麻），补肾",
}

# 五行→旅行方向
_ELEMENT_TRAVEL: dict[str, str] = {
    "wood":  "东方/东南（森林、山地）",
    "fire":  "南方（温暖气候）",
    "earth": "中原/西南（平原、田野）",
    "metal": "西方/西北（高原、沙漠）",
    "water": "北方/海边（水边、港口城市）",
}

# 五行→睡眠建议
_ELEMENT_SLEEP: dict[str, str] = {
    "wood":  "头朝东而睡，23点前入睡，保护肝胆",
    "fire":  "保持睡眠规律，避免深夜玩手机，有助心气恢复",
    "earth": "午后小憩15-20分钟，规律作息暖脾胃",
    "metal": "头朝西，充足睡眠（7-8小时），保护肺气",
    "water": "头朝北，早睡早起有益肾气，避免熬夜",
}

_ELEMENT_CN: dict[str, str] = {
    "metal": "金", "wood": "木", "water": "水", "fire": "火", "earth": "土",
}


def compute_lifestyle(
    yongshen_favor: list[str],
    yongshen_avoid: list[str],
) -> LifestyleModel:
    """
    根据用神五行给出全面生活方式建议。
    """
    prim = yongshen_favor[0] if yongshen_favor else "earth"
    sec  = yongshen_favor[1] if len(yongshen_favor) > 1 else prim
    tert = yongshen_favor[2] if len(yongshen_favor) > 2 else None

    _ex3 = (
        _ELEMENT_EXERCISE.get(tert, "每周 2-3 次有氧运动，保持整体体能平衡")
        if tert and tert not in (prim, sec)
        else "每周 2-3 次有氧运动，保持整体体能平衡"
    )
    exercise       = [
        _ELEMENT_EXERCISE.get(prim, "适量有氧运动"),
        _ELEMENT_EXERCISE.get(sec, "拉伸放松运动") if sec != prim else "每天快走或慢跑 30 分钟",
        _ex3,
    ]
    best_times     = _ELEMENT_BEST_TIMES.get(prim, "早晨 7-9 点")
    diet           = [
        _ELEMENT_DIET.get(prim, "均衡饮食，清淡为主"),
        _ELEMENT_DIET.get(sec, "多食新鲜蔬果") if sec != prim else "每天至少五种颜色蔬果",
        "每日饮水不少于 1500ml，避免高糖高油饮食",
        "晚餐清淡少量，睡前两小时不再进食",
    ]
    travel_direction = _ELEMENT_TRAVEL.get(prim, "东南方")
    sleep_advice   = _ELEMENT_SLEEP.get(prim, "保持规律作息，早睡早起")

    el_cn = "、".join(_ELEMENT_CN.get(e, e) for e in yongshen_favor[:2])
    interp = (
        f"用神五行（{el_cn}）主导生活节律，运动以「{exercise[0]}」和「{exercise[1]}」为主。"
        f"每日最佳活动时间段为【{best_times}】，此时精力最充沛，适合重要事务。"
        f"饮食以「{diet[0]}」为核心方向，同时保证充足水分摄入与规律三餐节律。"
        f"出行旅游方向推荐{travel_direction}，睡眠建议：{sleep_advice}。"
        f"（仅供学术研究参考）"
    )

    return LifestyleModel(
        exercise=exercise,
        best_times=best_times,
        diet=diet,
        travel_direction=travel_direction,
        sleep_advice=sleep_advice,
        interpretation_text=interp,
    )
