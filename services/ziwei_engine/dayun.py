"""
services/ziwei_engine/dayun.py — 大运计算

规则：
  阳年生男 / 阴年生女 → 顺行
  阳年生女 / 阴年生男 → 逆行
  阳年: 年干索引为偶数（甲0,丙2,戊4,庚6,壬8）
  阴年: 年干索引为奇数（乙1,丁3,己5,辛7,癸9）

大运起始年龄：
  距上（顺行=下一个节气；逆行=上一个节气）的天数 / 3 = 起运岁数（取整）
  本系统用 sxtwl 获取节气信息来准确计算。
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Optional

try:
    import sxtwl  # type: ignore
except ImportError:
    sxtwl = None  # type: ignore

from .tables import STEMS, BRANCHES
from .lunar import LunarInfo


@dataclass
class DayunItem:
    index: int            # 第几柱大运（从1开始）
    stem_idx: int         # 天干索引
    branch_idx: int       # 地支索引
    ganzhi: str           # 干支文字
    start_age: int        # 起运虚岁
    end_age: int          # 终运虚岁
    start_year: int       # 起运公历年
    sihua: dict[str, str] = field(default_factory=dict)       # 大运四化 {星名: "化禄"/"化权"/"化科"/"化忌"}
    boshi_stars: dict[str, str] = field(default_factory=dict) # 博士十二流曜 {星名: 地支名}


@dataclass
class DayunResult:
    forward: bool                    # True=顺行，False=逆行
    start_age_exact: float           # 精确起运岁数（可带小数）
    start_age: int                   # 起运虚岁（取整）
    items: list[DayunItem] = field(default_factory=list)


def _is_yang_year(year_stem_idx: int) -> bool:
    return year_stem_idx % 2 == 0


def _calc_dayun_direction(year_stem_idx: int, gender: str) -> bool:
    """True = 顺行（forward）"""
    yang = _is_yang_year(year_stem_idx)
    male = gender.upper() in ("M", "男", "MALE")
    return (yang and male) or (not yang and not male)


def _jiazi_step(stem_idx: int, branch_idx: int, forward: bool, steps: int = 1) -> tuple[int, int]:
    """干支序列向前/向后 steps 步。"""
    if forward:
        s = (stem_idx + steps) % 10
        b = (branch_idx + steps) % 12
    else:
        s = (stem_idx - steps) % 10
        b = (branch_idx - steps) % 12
    return s, b


_TWELVE_JIE_IDX = {3, 5, 7, 9, 11, 13, 15, 17, 19, 21, 23, 1}  # 12节（排除12气）


def _get_jieqi_jds(year: int) -> list[float]:
    """返回指定年份所有12节的儒略日列表（使用 sxtwl.getJieQiByYear）。"""
    if sxtwl is None:
        return []
    try:
        infos = sxtwl.getJieQiByYear(year)
        result = []
        for info in infos:
            if int(info.jqIndex) in _TWELVE_JIE_IDX:
                result.append(float(info.jd))
        return result
    except Exception:
        return []


def _birth_jd(year: int, month: int, day: int) -> float:
    """出生日的近似儒略日（用于天数计算，精度到日即足够）。"""
    if sxtwl is not None:
        try:
            # 使用 sxtwl.fromSolar 返回对象里读不到 JD，但可用公式近似
            pass
        except Exception:
            pass
    # 儒略日公式（精确到日）
    a = (14 - month) // 12
    y = year + 4800 - a
    m = month + 12 * a - 3
    jdn = day + (153 * m + 2) // 5 + 365 * y + y // 4 - y // 100 + y // 400 - 32045
    return float(jdn)


def _get_solar_term_days(birth_year: int, birth_month: int, birth_day: int,
                          forward: bool) -> float:
    """
    计算从出生日到最近"节"（顺行=下一节；逆行=上一节）的天数。
    使用 sxtwl.getJieQiByYear + JD。
    若 sxtwl 不可用则返回估算值 30.0。
    """
    if sxtwl is None:
        return 30.0

    try:
        # 收集前后3年的所有节气JD
        all_jq: list[float] = []
        for yr in (birth_year - 1, birth_year, birth_year + 1):
            all_jq.extend(_get_jieqi_jds(yr))

        if not all_jq:
            return 30.0

        b_jd = _birth_jd(birth_year, birth_month, birth_day)

        if forward:
            candidates = [jd for jd in all_jq if jd > b_jd]
            if candidates:
                return min(candidates) - b_jd
        else:
            candidates = [jd for jd in all_jq if jd < b_jd]
            if candidates:
                return b_jd - max(candidates)
    except Exception:
        pass

    return 30.0  # fallback


def calc_dayun(info: LunarInfo, gender: str,
               birth_year: int, birth_month_solar: int, birth_day_solar: int) -> DayunResult:
    """
    计算大运。
    info      : LunarInfo（含年干月干月支等）
    gender    : "男"/"女"
    birth_*   : 出生公历年月日（用于节气计算）
    """
    ys = info.year_stem_idx
    ms = info.month_stem_idx
    mb = info.month_branch_idx

    forward = _calc_dayun_direction(ys, gender)

    # ── 起运岁数 ───────────────────────────────────────────
    days_to_jieqi = _get_solar_term_days(birth_year, birth_month_solar, birth_day_solar, forward)
    # 每3天对应1年
    start_age_exact = days_to_jieqi / 3.0
    # 虚岁：floor(周岁) + 1
    start_age = int(start_age_exact) + 1

    # ── 构建大运序列（8柱，共80年）──────────────────────────
    items: list[DayunItem] = []
    cur_s, cur_b = ms, mb
    for i in range(1, 9):
        cur_s, cur_b = _jiazi_step(cur_s, cur_b, forward, steps=1)
        age_start = start_age + (i - 1) * 10
        age_end = age_start + 9
        year_start = birth_year + age_start - 1   # 虚岁转公历年
        items.append(DayunItem(
            index=i,
            stem_idx=cur_s,
            branch_idx=cur_b,
            ganzhi=STEMS[cur_s] + BRANCHES[cur_b],
            start_age=age_start,
            end_age=age_end,
            start_year=year_start,
        ))

    return DayunResult(
        forward=forward,
        start_age_exact=round(start_age_exact, 2),
        start_age=start_age,
        items=items,
    )
