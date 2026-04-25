"""
services/ziwei_engine/lunar.py — 公历→农历转换 + 干支提取

复用 sxtwl (寿星天文历) 库，与八字引擎共享依赖。
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional
import sxtwl  # type: ignore[import]

from .tables import STEMS, BRANCHES, WUHU_M1_STEM, WUSHU_H0_STEM, hour_to_branch


def _jd_from_solar(year: int, month: int, day: int) -> float:
    """儿略日（精确到日，用于节气距离计算）。"""
    a = (14 - month) // 12
    y = year + 4800 - a
    m = month + 12 * a - 3
    return float(day + (153 * m + 2) // 5 + 365 * y + y // 4 - y // 100 + y // 400 - 32045)


# 节气“节”的 sxtwl jqIndex → 月支索引映射
_JIE_BRANCH_MAP: dict[int, int] = {
    1: 1,   # 小寒 → 丑(1)
    3: 2,   # 立春 → 寅(2)
    5: 3,   # 惊蛯 → 卯(3)
    7: 4,   # 清明 → 辰(4)
    9: 5,   # 立夏 → 巳(5)
    11: 6,  # 芒种 → 午(6)
    13: 7,  # 小暑 → 未(7)
    15: 8,  # 立秋 → 申(8)
    17: 9,  # 白露 → 酉(9)
    19: 10, # 寒露 → 戌(10)
    21: 11, # 立冬 → 亥(11)
    23: 0,  # 大雪 → 子(0)
}


def _calc_jieqi_month_gz(
    year: int, month: int, day: int,
    year_stem_idx: int,
) -> str:
    """
    根据节气（节）界定月份，计算节气月干支。

    八字传统：每月从“节”开始（立春/惊蛯/清明等），
    与紫微斗数使用农历月的方式不同。
    """
    if sxtwl is None:
        return ""
    try:
        b_jd = _jd_from_solar(year, month, day)
        # 收集前后 2 年的所有节气 JD
        jie_list: list[tuple[float, int]] = []
        for yr in (year - 1, year, year + 1):
            for info in sxtwl.getJieQiByYear(yr):
                jq_idx = int(info.jqIndex)
                if jq_idx in _JIE_BRANCH_MAP:
                    jie_list.append((float(info.jd), _JIE_BRANCH_MAP[jq_idx]))
        jie_list.sort()
        # 找出出生日前最近的“节”
        cur_branch = jie_list[0][1]
        for jd, b_idx in jie_list:
            if jd <= b_jd:
                cur_branch = b_idx
            else:
                break
        # 对应月数（寅月=正月=1，卯月=2，…，丑月=12）
        jieqi_month_num = (cur_branch - 2) % 12 + 1
        m1_stem = WUHU_M1_STEM[year_stem_idx]
        jieqi_stem_idx = (m1_stem + jieqi_month_num - 1) % 10
        return STEMS[jieqi_stem_idx] + BRANCHES[cur_branch]
    except Exception:
        return ""


@dataclass
class LunarInfo:
    """公历转农历后的完整干支信息"""
    # 农历
    lunar_year: int       # 农历年（与公历同年，可能有偏差）
    lunar_month: int      # 农历月 (1-12)，存原始月份（闰五月=5，不+1），用于展示
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
    month_gz: str         # 如 "壬寅"（农历月柱）
    hour_branch: str      # 如 "未"
    jieqi_month_gz: str = ""  # 节气月柱（八字法，按节界定月份）
    day_gz: str = ""          # 日柱干支，如 "癸未"
    hour_gz: str = ""         # 时柱干支，如 "丁巳"
    day_stem_idx: int = 0     # 日天干索引（0=甲…9=癸）
    leap_month_method: str = "next"  # "next"=视为下月(传统) | "same"=视为本月 | "mid"=月中分界

    @property
    def calc_lunar_month(self) -> int:
        """
        计算用月份（紫微斗数排盘用）。
        leap_month_method 决定闰月如何处理：
          next: 闰月统一视为下月（传统/当前默认）
          same: 闰月统一视为本月
          mid : 月中分界，农历日<=15视为本月，>15视为下月
        """
        if not self.is_leap_month:
            return self.lunar_month
        if self.leap_month_method == "same":
            return self.lunar_month
        elif self.leap_month_method == "mid":
            return self.lunar_month + (1 if self.lunar_day > 15 else 0)
        else:  # "next"（默认传统做法）
            return self.lunar_month + 1


def solar_to_lunar(
    year: int, month: int, day: int,
    hour: int = 0, minute: int = 0,
    leap_month_method: str = "next",
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
    l_month = day_obj.getLunarMonth()    # 原始农历月（闰五月=5）
    l_day   = day_obj.getLunarDay()
    is_leap = day_obj.isLunarLeap()
    # 计算用月份（月柱干支计算用），依 leap_month_method 决定闰月处理
    if not is_leap:
        l_month_calc = l_month
    elif leap_month_method == "same":
        l_month_calc = l_month            # 闰月视为本月
    elif leap_month_method == "mid":
        l_month_calc = l_month + (1 if l_day > 15 else 0)  # 月中分界
    else:  # "next"（传统/默认）
        l_month_calc = l_month + 1        # 闰月视为下月

    # 月支：正月=寅(2)，二月=卯(3)，以此类推（使用计算月份）
    month_branch_idx = (l_month_calc + 1) % 12  # 正月(1)+1=2=寅 ✓

    # 月干：五虎遁年口诀（使用计算月份）
    m1_stem = WUHU_M1_STEM[ys_idx]
    month_stem_idx = (m1_stem + l_month_calc - 1) % 10

    # 时辰
    hb_idx = hour_to_branch(hour, minute)

    year_gz_str  = STEMS[ys_idx] + BRANCHES[yb_idx]
    month_gz_str = STEMS[month_stem_idx] + BRANCHES[month_branch_idx]
    hour_b_str   = BRANCHES[hb_idx]
    # 节气月柱（八字法，按节界定月份）
    jieqi_month_gz_str = _calc_jieqi_month_gz(year, month, day, ys_idx)
    # 日柱干支（sxtwl 直接查表）
    day_gz_obj = day_obj.getDayGZ()
    ds_idx = day_gz_obj.tg
    db_idx = day_gz_obj.dz
    day_gz_str = STEMS[ds_idx] + BRANCHES[db_idx]
    # 时柱干支（五鼠遁日）
    hs_idx = (WUSHU_H0_STEM[ds_idx] + hb_idx) % 10
    hour_gz_str = STEMS[hs_idx] + BRANCHES[hb_idx]

    return LunarInfo(
        lunar_year          = year,
        lunar_month         = l_month,       # 保留原始月份（展示用），闰五月=5
        lunar_day           = l_day,
        is_leap_month       = bool(is_leap),
        year_stem_idx       = ys_idx,
        year_branch_idx     = yb_idx,
        month_stem_idx      = month_stem_idx,
        month_branch_idx    = month_branch_idx,
        hour_branch_idx     = hb_idx,
        year_gz             = year_gz_str,
        month_gz            = month_gz_str,
        hour_branch         = hour_b_str,
        jieqi_month_gz      = jieqi_month_gz_str,
        day_gz              = day_gz_str,
        hour_gz             = hour_gz_str,
        day_stem_idx        = ds_idx,
        leap_month_method   = leap_month_method,
    )
