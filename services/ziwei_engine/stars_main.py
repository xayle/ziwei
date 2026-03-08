"""
services/ziwei_engine/stars_main.py — 14主星布局

算法来源：《紫微斗数全书》安星次序

一、紫微星定位（安紫微）
  给定五行局数 n, 农历生日 d:
  q, r = divmod(d, n)
  if r == 0:
    紫微 = 寅(2) + q - 1   (mod 12)
  else:
    找最小步数 step 使得 (d + step) 能被 n 整除且步数为奇数
    (即跳到下一个能被整除的日子，按奇数偶数方向跳)
    具体：一阳一阴交替，从1步开始：
      step=1 → d+1 能否整除? 方向+
      step=1 → d-1 能否整除? 方向-
      依此类推直到能整除
    紫微 = 寅(2) + (d+step)/n - 1 (mod 12)，方向按跳转方向

二、天府星定位
  天府 = (4 - 紫微支) mod 12  [等价于 (2*寅 - 紫微) mod 12]

三、其余星位 = 紫微/天府 + 固定偏移 (见 tables.py)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional
from .tables import (
    BRANCHES, ALL_MAIN_STARS,
    ZIWEI_OFFSETS, TIANFU_OFFSETS,
    get_brightness,
)


@dataclass
class StarPosition:
    name: str
    branch_idx: int          # 所在地支索引 (子=0…亥=11)
    branch: str              # 地支名
    brightness_val: int      # 亮度值 5庙…0陷
    brightness: str          # 亮度名
    transforms: list[str] = field(default_factory=list)  # 化禄/化权/化科/化忌


def _place_ziwei(day: int, ju: int) -> int:
    """
    返回紫微星所在地支索引（子=0）。

    日期能被局数整除：直接定位
    不能整除：按"奇加偶减"规则跳步直到整除
    """
    q, r = divmod(day, ju)
    if r == 0:
        return (2 + q - 1) % 12   # 寅(2) + q - 1

    # 奇数步+，偶数步-
    step = 1
    while step <= 30:
        d_plus  = day + step
        d_minus = day - step
        if d_plus > 0 and d_plus % ju == 0:
            q2 = d_plus // ju
            return (2 + q2 - 1) % 12
        if d_minus > 0 and d_minus % ju == 0:
            q2 = d_minus // ju
            return (2 + q2 - 1) % 12
        step += 1

    # 安全兜底：不应到达此处
    return (2 + (day // ju) - 1) % 12  # pragma: no cover


def place_main_stars(lunar_day: int, wuxing_ju: int) -> dict[str, StarPosition]:
    """
    布局14主星，返回 {星名: StarPosition}。

    Args:
        lunar_day: 农历日 (1-30)
        wuxing_ju: 五行局数 (2/3/4/5/6)
    """
    ziwei_b = _place_ziwei(lunar_day, wuxing_ju)
    # 天府：令 (2 * 寅 - 紫微) % 12 = (4 - ziwei_b) % 12
    tianfu_b = (4 - ziwei_b) % 12

    result: dict[str, StarPosition] = {}

    # 紫微系（6星）
    for name, offset in ZIWEI_OFFSETS.items():
        b = (ziwei_b + offset) % 12
        bv, bn = get_brightness(name, b)
        result[name] = StarPosition(
            name=name, branch_idx=b, branch=BRANCHES[b],
            brightness_val=bv, brightness=bn,
        )

    # 天府系（8星）
    for name, offset in TIANFU_OFFSETS.items():
        b = (tianfu_b + offset) % 12
        bv, bn = get_brightness(name, b)
        result[name] = StarPosition(
            name=name, branch_idx=b, branch=BRANCHES[b],
            brightness_val=bv, brightness=bn,
        )

    return result
