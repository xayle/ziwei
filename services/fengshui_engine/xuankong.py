"""玄空飞星 — 三元九运 + 九宫飞布。

从 services/bazi_engine/liuri.py 误粘贴代码迁出（2026-07-11）。
"""

from __future__ import annotations

# 洛书九宫 (方位→宫数)
LUOSHU = [
    (6, "西北", "乾"),
    (1, "北", "坎"),
    (8, "东北", "艮"),
    (7, "西", "兑"),
    (5, "中", "中"),
    (3, "东", "震"),
    (2, "西南", "坤"),
    (9, "南", "离"),
    (4, "东南", "巽"),
]

# 九星名称
STAR_NAMES = {
    1: "一白水",
    2: "二黑土",
    3: "三碧木",
    4: "四绿木",
    5: "五黄土",
    6: "六白金",
    7: "七赤金",
    8: "八白土",
    9: "九紫火",
}

STAR_AUSPICIOUS = {
    1: "吉",
    2: "凶",
    3: "凶",
    4: "平",
    5: "大凶",
    6: "吉",
    7: "凶",
    8: "大吉",
    9: "吉",
}

# 飞星路径 (洛书轨迹: 中→西北→西→东北→南→北→西南→东→东南→中)
FLY_PATH = [5, 6, 7, 8, 9, 1, 2, 3, 4]


def _fly_star(center: int) -> list[int]:
    """以 center 入中宫, 按飞星路径排列九宫。"""
    start = FLY_PATH.index(center)
    return FLY_PATH[start:] + FLY_PATH[:start]


def _time_period(year: int) -> int:
    """三元九运: 每20年一运。"""
    if year < 1864:
        return 1
    elapsed = year - 1864
    return (elapsed // 20) % 9 + 1


def _facing_to_gong(direction_deg: float) -> tuple[int, str, str]:
    """朝向角度 → (宫数, 方位名, 卦名)。"""
    idx = int(((direction_deg % 360) + 22.5) // 45) % 8
    mapping = [
        (1, "北", "坎"),
        (8, "东北", "艮"),
        (3, "东", "震"),
        (4, "东南", "巽"),
        (9, "南", "离"),
        (2, "西南", "坤"),
        (7, "西", "兑"),
        (6, "西北", "乾"),
    ]
    return mapping[idx]


def compute_xuankong(year: int, facing_deg: float) -> dict:
    """计算玄空飞星盘。"""
    period = _time_period(year)
    facing_num, facing_name, facing_gua = _facing_to_gong(facing_deg)

    yun_stars = _fly_star(period)

    shan_center = (facing_num + period) % 9 or 9
    xiang_center = (period - facing_num) % 9 or 9
    if xiang_center <= 0:
        xiang_center += 9

    shan_stars = _fly_star(shan_center)
    xiang_stars = _fly_star(xiang_center)

    palaces = []
    for i, (gong_num, direction, gua) in enumerate(LUOSHU):
        palaces.append(
            {
                "gong": gong_num,
                "direction": direction,
                "gua": gua,
                "yun_star": yun_stars[i],
                "shan_star": shan_stars[i],
                "xiang_star": xiang_stars[i],
                "yun_name": STAR_NAMES.get(yun_stars[i], ""),
                "shan_name": STAR_NAMES.get(shan_stars[i], ""),
                "xiang_name": STAR_NAMES.get(xiang_stars[i], ""),
            }
        )

    return {
        "period": period,
        "period_name": f"{'上' if period <= 3 else '中' if period <= 6 else '下'}元{((period - 1) % 3) + 1}运",
        "year": year,
        "facing_deg": facing_deg,
        "facing": facing_name,
        "facing_gua": facing_gua,
        "palaces": palaces,
    }
