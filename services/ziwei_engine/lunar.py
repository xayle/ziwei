"""
services/ziwei_engine/lunar.py — 公历→农历转换 + 干支提取

复用 sxtwl (寿星天文历) 库，与八字引擎共享依赖。
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional
import sxtwl  # type: ignore[import]

from .tables import STEMS, BRANCHES, WUHU_M1_STEM, hour_to_branch


@dataclass
class LunarInfo:
    """公历转农历后的完整干支信息"""
    # 农历
    lunar_year: int       # 农历年（与公历同年，可能有偏差）
    lunar_month: int      # 农历月 (1-12, 闰月为负或特殊标记)
    lunar_day: int        # 农历日 (1-30)
    is_leap_month: bool   # 是否闰月

    # 干支
    year_stem_idx: int    # 年天干索引 (甲=0…癸=9)
    year_branch_idx: int  # 年地支索引 (子=0…亥=11)
    month_stem_idx: int   # 月天干索引
    month_branch_idx: int # 月地支索引 (正月=寅=2)
    hour_branch_idx: int  # 时辰地支索引 (子=0…亥=11)

    # 名称（方便展示）
    year_gz: str          # 如 "壬午"
    month_gz: str         # 如 "壬寅"
    hour_branch: str      # 如 "未"


def solar_to_lunar(
    year: int, month: int, day: int,
    hour: int = 0, minute: int = 0,
) -> LunarInfo:
    """
    公历转农历，返回 LunarInfo。

    Args:
        year, month, day: 公历日期 (如 2002, 3, 13)
        hour, minute: 24小时制 (如 14, 55)

    Returns:
        LunarInfo 包含农历月日、干支等
    """
    day_obj = sxtwl.fromSolar(year, month, day)

    # 年干支 (注意 sxtwl 的 getYearGZ() 返回当前节气年的干支)
    year_gz_obj = day_obj.getYearGZ()
    ys_idx = year_gz_obj.tg   # 天干索引 甲=0
    yb_idx = year_gz_obj.dz   # 地支索引 子=0

    # 农历月日
    l_month = day_obj.getLunarMonth()
    l_day   = day_obj.getLunarDay()
    is_leap = day_obj.isLunarLeap()

    # 月支：正月=寅(2)，二月=卯(3)，以此类推
    month_branch_idx = (l_month + 1) % 12  # 正月(1)+1=2=寅 ✓

    # 月干：五虎遁年口诀
    m1_stem = WUHU_M1_STEM[ys_idx]
    month_stem_idx = (m1_stem + l_month - 1) % 10

    # 时辰
    hb_idx = hour_to_branch(hour, minute)

    year_gz_str  = STEMS[ys_idx] + BRANCHES[yb_idx]
    month_gz_str = STEMS[month_stem_idx] + BRANCHES[month_branch_idx]
    hour_b_str   = BRANCHES[hb_idx]

    return LunarInfo(
        lunar_year       = year,
        lunar_month      = l_month,
        lunar_day        = l_day,
        is_leap_month    = bool(is_leap),
        year_stem_idx    = ys_idx,
        year_branch_idx  = yb_idx,
        month_stem_idx   = month_stem_idx,
        month_branch_idx = month_branch_idx,
        hour_branch_idx  = hb_idx,
        year_gz          = year_gz_str,
        month_gz         = month_gz_str,
        hour_branch      = hour_b_str,
    )
