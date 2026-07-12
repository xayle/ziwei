"""
services/ziwei_engine/liuri.py — 流日 / 流时（最小实现）

口径：docs/design/ziwei/01-大限流年.md §五
  - 流日：以流月命宫地支起初一，顺行
  - 流时：以流日命宫地支起子时，顺行
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .tables import BRANCHES, PALACE_NAMES


@dataclass
class LiuriInfo:
    """流日信息。"""

    lunar_day: int
    life_palace_branch: int
    branch: str
    palace_name: str = ""
    liuyue_month: int = 1
    method: str = "standard"


@dataclass
class LiushiInfo:
    """流时信息。"""

    hour_branch_idx: int
    life_palace_branch: int
    branch: str
    palace_name: str = ""
    hour_label: str = ""
    method: str = "standard"


@dataclass
class LiuriLiushiBundle:
    """流日 + 流时组合。"""

    liuri: LiuriInfo
    liushi: LiushiInfo
    missing_fields: list[str] = field(default_factory=list)


_HOUR_LABELS = ["子时", "丑时", "寅时", "卯时", "辰时", "巳时", "午时", "未时", "申时", "酉时", "戌时", "亥时"]


def calc_liuri_branch(liuyue_life_branch: int, lunar_day: int) -> int:
    """流日命宫地支：流月宫起初一顺行。"""
    if lunar_day < 1:
        return liuyue_life_branch
    return (liuyue_life_branch + lunar_day - 1) % 12


def calc_liushi_branch(liuri_branch: int, hour_branch_idx: int) -> int:
    """流时命宫地支：流日宫起子时顺行。"""
    return (liuri_branch + hour_branch_idx) % 12


def _branch_to_palace_name(life_palace_branch: int, target_branch: int) -> str:
    offset = (life_palace_branch - target_branch) % 12
    if 0 <= offset < len(PALACE_NAMES):
        return PALACE_NAMES[offset]
    return "—"


def calc_liuri_liushi(
    *,
    life_palace_branch: int,
    liuyue_life_branch: int,
    lunar_day: int,
    hour_branch_idx: int,
    liuyue_month: int = 1,
) -> LiuriLiushiBundle:
    """计算指定流月日、时辰的流日/流时落宫。"""
    missing: list[str] = []
    if liuyue_life_branch < 0 or liuyue_life_branch > 11:
        missing.append("liuyue_life_branch")
    if hour_branch_idx < 0 or hour_branch_idx > 11:
        missing.append("hour_branch_idx")

    liuri_b = calc_liuri_branch(liuyue_life_branch, lunar_day)
    liushi_b = calc_liushi_branch(liuri_b, hour_branch_idx)

    liuri = LiuriInfo(
        lunar_day=lunar_day,
        life_palace_branch=liuri_b,
        branch=BRANCHES[liuri_b],
        palace_name=_branch_to_palace_name(life_palace_branch, liuri_b),
        liuyue_month=liuyue_month,
    )
    liushi = LiushiInfo(
        hour_branch_idx=hour_branch_idx,
        life_palace_branch=liushi_b,
        branch=BRANCHES[liushi_b],
        palace_name=_branch_to_palace_name(life_palace_branch, liushi_b),
        hour_label=_HOUR_LABELS[hour_branch_idx],
    )
    return LiuriLiushiBundle(liuri=liuri, liushi=liushi, missing_fields=missing)
