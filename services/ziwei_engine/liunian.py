"""
services/ziwei_engine/liunian.py — 流年 / 流月计算

默认口径（见 docs/design/ziwei/ENGINE-METHOD-REGISTRY.md）：
  - 流年命宫：太岁直落（taisui）
  - 流月：斗君法（doujun）
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .tables import BRANCHES, STEMS


@dataclass
class LiuyueInfo:
    """流月信息（Z-P1-01）。"""

    month: int
    month_name: str
    month_gz: str
    life_palace_branch: int
    palace_name: str
    sihua: dict[str, str] = field(default_factory=dict)
    liuyue_method: str = "doujun"
    doujun_branch: int | None = None


@dataclass
class LiunianInfo:
    year: int  # 公历流年
    year_stem_idx: int  # 流年天干
    year_branch_idx: int  # 流年地支
    year_gz: str  # 干支
    life_palace_branch: int  # 流年命宫地支
    liunian_life_method: str = "taisui"
    # 流年四化
    sihua: dict[str, str] = field(default_factory=dict)


def calc_liunian_life_branch(year_branch_idx: int, *, liunian_life_method: str = "taisui") -> int:
    """流年命宫地支：默认太岁直落；legacy 为寅宫起算。"""
    if liunian_life_method == "yin_start":
        return (2 + year_branch_idx) % 12
    return year_branch_idx


def calc_liunian(
    target_year: int,
    birth_year: int,
    life_palace_branch: int = 0,
    *,
    liunian_life_method: str = "taisui",
) -> LiunianInfo:
    """
    计算指定公历年的流年信息。

    life_palace_branch 保留兼容旧签名；taisui 模式下不使用本命命宫。
    """
    _ = (birth_year, life_palace_branch)

    stem_idx = (target_year - 4) % 10
    branch_idx = (target_year - 4) % 12
    liunian_life = calc_liunian_life_branch(branch_idx, liunian_life_method=liunian_life_method)

    from .transforms import SIHUA_TABLE

    sihua_map = SIHUA_TABLE.get(STEMS[stem_idx], {})
    sihua = {star: f"化{hua}" for hua, star in sihua_map.items()}

    return LiunianInfo(
        year=target_year,
        year_stem_idx=stem_idx,
        year_branch_idx=branch_idx,
        year_gz=STEMS[stem_idx] + BRANCHES[branch_idx],
        life_palace_branch=liunian_life,
        liunian_life_method=liunian_life_method,
        sihua=sihua,
    )


def calc_doujun(year_branch_idx: int, birth_month: int, birth_hour_branch: int) -> int:
    """
    斗君定位（设计文档 §四）：
    1. 流年地支宫起正月，逆数至生月
    2. 所止宫位起子时，顺数至生时
    """
    step2 = (year_branch_idx - (birth_month - 1)) % 12
    return (step2 + birth_hour_branch) % 12


def calc_liuyue(
    liunian_life_branch: int,
    month: int,
    *,
    doujun_branch: int | None = None,
    liuyue_method: str = "doujun",
) -> int:
    """
    流月命宫地支。
    doujun：以斗君为正月顺数；simplified：以流年命宫 + month-1。
    """
    if liuyue_method == "doujun" and doujun_branch is not None:
        return (doujun_branch + month - 1) % 12
    return (liunian_life_branch + month - 1) % 12


def overlay_palace_map(natal_life_branch: int, flow_branch: int) -> dict[str, str]:
    """
    叠宫映射：本命十二宫 → 流年/流月叠入之宫名（Z-04/Z-06）。

    offset = (natal_life - flow) % 12
    """
    from .tables import PALACE_NAMES

    offset = (natal_life_branch - flow_branch) % 12
    return {PALACE_NAMES[i]: PALACE_NAMES[(i + offset) % 12] for i in range(12)}


# 农历月份名称（对应公历约+1月：正月≈2月，依次顺推）
_LUNAR_MONTH_NAMES: list[str] = [
    "正月(寅)",
    "二月(卯)",
    "三月(辰)",
    "四月(巳)",
    "五月(午)",
    "六月(未)",
    "七月(申)",
    "八月(酉)",
    "九月(戌)",
    "十月(亥)",
    "十一月(子)",
    "十二月(丑)",
]
# 农历月份对应地支索引（寅=2起）
_MONTH_BRANCHES: list[int] = [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 0, 1]

# 五虎遁年：年干 → 正月天干起始索引
_WUHU_M1: list[int] = [2, 4, 6, 8, 0, 2, 4, 6, 8, 0]


def calc_liuyue_list(
    liunian: LiunianInfo,
    branch_to_palace_name: dict[int, str],
    birth_month: int,
    birth_hour_branch: int,
    *,
    liuyue_method: str = "doujun",
) -> list[LiuyueInfo]:
    """
    计算流年12个流月数据列表。
    """
    from .transforms import SIHUA_TABLE

    doujun_branch: int | None = None
    if liuyue_method == "doujun":
        doujun_branch = calc_doujun(liunian.year_branch_idx, birth_month, birth_hour_branch)

    items: list[LiuyueInfo] = []
    m1_stem = _WUHU_M1[liunian.year_stem_idx]
    for i in range(12):
        month = i + 1
        mo_stem_idx = (m1_stem + i) % 10
        mo_branch_idx = _MONTH_BRANCHES[i]
        mo_gz = STEMS[mo_stem_idx] + BRANCHES[mo_branch_idx]
        life_b = calc_liuyue(
            liunian.life_palace_branch,
            month,
            doujun_branch=doujun_branch,
            liuyue_method=liuyue_method,
        )
        palace_name = branch_to_palace_name.get(life_b, "—")
        mo_sihua_raw = SIHUA_TABLE.get(STEMS[mo_stem_idx], {})
        mo_sihua = {star: f"化{hua}" for hua, star in mo_sihua_raw.items()}
        items.append(
            LiuyueInfo(
                month=month,
                month_name=_LUNAR_MONTH_NAMES[i],
                month_gz=mo_gz,
                life_palace_branch=life_b,
                palace_name=palace_name,
                sihua=mo_sihua,
                liuyue_method=liuyue_method,
                doujun_branch=doujun_branch,
            )
        )
    return items
