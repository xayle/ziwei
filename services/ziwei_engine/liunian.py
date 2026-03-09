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


# 农历月份名称（对应公历约+1月：正月≈2月，依次顺推）
_LUNAR_MONTH_NAMES: list[str] = [
    '正月(寅)', '二月(卯)', '三月(辰)', '四月(巳)', '五月(午)', '六月(未)',
    '七月(申)', '八月(酉)', '九月(戌)', '十月(亥)', '十一月(子)', '十二月(丑)',
]
# 农历月份对应地支索引（寅=2起）
_MONTH_BRANCHES: list[int] = [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 0, 1]

# 五虎遁年：年干 → 正月天干起始索引（甲己→丙(2)，乙庚→戊(4)，丙辛→庚(6)，丁壬→壬(8)，戊癸→甲(0)）
_WUHU_M1: list[int] = [2, 4, 6, 8, 0, 2, 4, 6, 8, 0]


def calc_liuyue_list(
    liunian: 'LiunianInfo',
    branch_to_palace_name: dict[int, str],
) -> list[dict]:
    """
    计算流年12个流月数据列表。
    每项: {month, month_name, month_gz, life_palace_branch, palace_name, sihua}
    """
    from .tables import STEMS, BRANCHES
    from .transforms import SIHUA_TABLE
    items: list[dict] = []
    m1_stem = _WUHU_M1[liunian.year_stem_idx]
    for i in range(12):
        month = i + 1
        mo_stem_idx = (m1_stem + i) % 10
        mo_branch_idx = _MONTH_BRANCHES[i]
        mo_gz = STEMS[mo_stem_idx] + BRANCHES[mo_branch_idx]
        life_b = calc_liuyue(liunian.life_palace_branch, month)
        palace_name = branch_to_palace_name.get(life_b, '—')
        # 流月四化（月干四化）
        mo_sihua_raw = SIHUA_TABLE.get(STEMS[mo_stem_idx], {})
        mo_sihua = {star: f"化{hua}" for hua, star in mo_sihua_raw.items()}
        items.append({
            'month': month,
            'month_name': _LUNAR_MONTH_NAMES[i],
            'month_gz': mo_gz,
            'life_palace_branch': life_b,
            'palace_name': palace_name,
            'sihua': mo_sihua,
        })
    return items
