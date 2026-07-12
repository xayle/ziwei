"""
services/ziwei_engine/dayun.py — 紫微斗数大限计算

紫微大限规则：
  起运虚岁 = 五行局数（水二局=2, 木三局=3, 金四局=4, 土五局=5, 火六局=6）
  方向：阳男阴女顺行、阴男阳女逆行
  干支：每大限干支 = 对应宫位本身的天干（五虎遁）+ 地支
  每限十年，共排12限(120年)
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .lunar import LunarInfo
from .tables import BRANCHES, STEMS, WUHU_M1_STEM


@dataclass
class DayunItem:
    index: int  # 第几柱大运（从1开始）
    stem_idx: int  # 天干索引
    branch_idx: int  # 地支索引
    ganzhi: str  # 干支文字
    start_age: int  # 起运虚岁
    end_age: int  # 终运虚岁
    start_year: int  # 起运公历年
    sihua: dict[str, str] = field(default_factory=dict)  # 大运四化 {星名: "化禄"/"化权"/"化科"/"化忌"}
    boshi_stars: dict[str, str] = field(default_factory=dict)  # 博士十二流曜 {星名: 地支名}


@dataclass
class DayunResult:
    forward: bool  # True=顺行，False=逆行
    start_age_exact: float  # 精确起运岁数（可带小数）
    start_age: int  # 起运虚岁（取整）
    start_age_text: str = ""  # 起运年龄文字，如 "3年2月26天"
    items: list[DayunItem] = field(default_factory=list)


def resolve_current_dayun_item(dayun: DayunResult | None, virtual_age: int) -> DayunItem | None:
    """按虚岁返回当前大运项；起运前返回 None，超过末限则取最后一柱。"""
    if dayun is None or not dayun.items:
        return None
    for item in dayun.items:
        if item.start_age <= virtual_age < item.start_age + 10:
            return item
    if virtual_age >= dayun.items[-1].start_age:
        return dayun.items[-1]
    return None


def _is_yang_year(year_stem_idx: int) -> bool:
    return year_stem_idx % 2 == 0


def _calc_dayun_direction(year_stem_idx: int, gender: str) -> bool:
    """True = 顺行（forward）"""
    yang = _is_yang_year(year_stem_idx)
    male = gender.upper() in ("M", "男", "MALE")
    return (yang and male) or (not yang and not male)


def calc_dayun(
    info: LunarInfo,
    gender: str,
    birth_year: int,
    birth_month_solar: int = 0,
    birth_day_solar: int = 0,
    birth_hour: int = 12,
    birth_minute: int = 0,
    wuxing_ju: int = 5,
    life_branch_idx: int = 2,
    life_stem_idx: int = 4,
) -> DayunResult:
    """
    计算紫微斗数大限（十年大运）。

    紫微大限规则：
      起运虚岁 = 五行局数（水二局=2, 木三局=3, 金四局=4, 土五局=5, 火六局=6）
      阳男阴女顺行，阴男阳女逆行
      各大限干支 = 对应宫位的天干（五虎遁）+ 地支
    """
    ys = info.year_stem_idx

    forward = _calc_dayun_direction(ys, gender)

    # ── 紫微大限起运虚岁 = 五行局数 ─────────────────────────
    start_age = wuxing_ju

    # ── 构建大限序列（12宫，共120年）──────────────────────────
    # 从命宫地支出发，顺/逆遍历12宫；
    # 每宫的天干 = 五虎遁公式（由年干决定）
    wuhu_base = WUHU_M1_STEM[ys]  # 该年干对应的寅宫天干
    items: list[DayunItem] = []
    for i in range(12):
        if forward:
            branch = (life_branch_idx + i) % 12
        else:
            branch = (life_branch_idx - i) % 12

        # 五虎遁：stem = (寅宫起始天干 + 地支距寅的偏移) % 10
        stem = (wuhu_base + (branch - 2 + 12) % 12) % 10

        age_start = start_age + i * 10
        age_end = age_start + 9
        year_start = birth_year + age_start - 1  # 虚岁转公历年

        items.append(
            DayunItem(
                index=i + 1,
                stem_idx=stem,
                branch_idx=branch,
                ganzhi=STEMS[stem] + BRANCHES[branch],
                start_age=age_start,
                end_age=age_end,
                start_year=year_start,
            )
        )

    return DayunResult(
        forward=forward,
        start_age_exact=float(start_age),
        start_age=start_age,
        start_age_text=f"{start_age}岁起运",
        items=items,
    )
