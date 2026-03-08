"""
services/ziwei_engine/liunian.py — 流年 / 流月计算

流年命宫：每年从寅宫起，按实岁（或虚岁）顺数。
  流年命宫地支 = (命宫地支 + 年差) % 12
  实际：流年以"太岁"为准，太岁即当年的地支年。
  流年十二宫 = 以虎(寅)为起点，流年地支宫为当年命宫，顺布12宫。

流月：以流年命宫为基点，每月顺数一宫。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from .tables import STEMS, BRANCHES
from .lunar import LunarInfo


@dataclass
class LiunianInfo:
    year: int              # 公历流年
    year_stem_idx: int     # 流年天干
    year_branch_idx: int   # 流年地支
    year_gz: str           # 干支
    life_palace_branch: int  # 流年命宫地支
    # 流年四化
    sihua: dict[str, str] = field(default_factory=dict)


def calc_liunian(target_year: int, birth_year: int,
                 life_palace_branch: int) -> LiunianInfo:
    """
    计算指定公历年的流年信息。

    target_year        : 流年（公历）
    birth_year         : 出生公历年
    life_palace_branch : 本命命宫地支索引（子=0）
    """
    # 流年干支：天干 = (target_year - 4) % 10，地支 = (target_year - 4) % 12
    # 甲子年=公历4年（甲=0, 子=0）：(year-4)%10=stem, (year-4)%12=branch
    stem_idx   = (target_year - 4) % 10
    branch_idx = (target_year - 4) % 12

    # 流年命宫：以寅(2)为起点，加太岁地支，注意顺数
    # 标准：子年在寅(2)，丑年在卯(3)...
    # 流年命宫 = (2 + branch_idx) % 12
    # 但也有按"命宫所在宫位 + 年龄偏移"的方法；
    # 最常见为：流年命宫地支 = (2 + branch_idx) % 12（太岁寅宫起）
    liunian_life = (2 + branch_idx) % 12

    from .transforms import SIHUA_TABLE
    sihua_map = SIHUA_TABLE.get(STEMS[stem_idx], {})
    sihua = {star: f"化{hua}" for hua, star in sihua_map.items()}

    return LiunianInfo(
        year=target_year,
        year_stem_idx=stem_idx,
        year_branch_idx=branch_idx,
        year_gz=STEMS[stem_idx] + BRANCHES[branch_idx],
        life_palace_branch=liunian_life,
        sihua=sihua,
    )


def calc_liuyue(liunian_life_branch: int, month: int) -> int:
    """
    流月命宫地支：以流年命宫为起点，从寅月(月份1)顺数。
    month: 1-12 (农历月)
    """
    return (liunian_life_branch + month - 1) % 12
