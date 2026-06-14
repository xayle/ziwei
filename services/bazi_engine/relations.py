"""
services/bazi_engine/relations.py — 地支关系 & 天干相克（M1 任务 1.16/1.17）

1.16: 地支关系 status 枚举: 全合/半合/拱合 + position 输出
  全合: 三合三支全部出现
  半合: 三合中只有2支出现（含主气）
  拱合: 三合中只有首尾两支（中间支缺失，"暗拱"）
  六合: 六合对成立

1.17: 天干相克 scope 参数
  scope="day_related"（默认）: 只返回与日主相关的相克关系
  scope="all": 返回四柱所有天干相克关系
"""

from __future__ import annotations

from typing import Literal

from services.bazi_engine.tables import (
    BRANCH_CHONG,
    LIU_HE,
    SAN_HE,
    STEM_ELEMENT,
)

# ──────────────────────────────────────────────────────────────────────────────
# 天干五行相克（ke_me: 克日主的元素；i_ke: 日主所克的元素）
# ──────────────────────────────────────────────────────────────────────────────

_STEM_KE: dict[str, str] = {
    "木": "土",
    "土": "水",
    "水": "火",
    "火": "金",
    "金": "木",
}
_ELEM_TO_CN: dict[str, str] = {"wood": "木", "fire": "火", "earth": "土", "metal": "金", "water": "水"}
_CN_TO_ELEM: dict[str, str] = {v: k for k, v in _ELEM_TO_CN.items()}


def _elem_cn(stem: str) -> str:
    elem, _ = STEM_ELEMENT.get(stem, ("?", "?"))
    return _ELEM_TO_CN.get(elem, "?")


def get_stem_clashes(
    year_stem: str,
    month_stem: str,
    day_stem: str,
    hour_stem: str,
    scope: Literal["day_related", "all"] = "day_related",
) -> list[dict]:
    """
    计算四柱天干相克关系.

    scope="day_related": 只返回含日主天干的相克对
    scope="all":         返回四柱所有相克对

    Returns list of:
    {
        "stem_a": str,
        "stem_b": str,
        "direction": "a_ke_b" | "b_ke_a",   # a克b 或 b克a
        "pillar_a": str,                      # year/month/day/hour
        "pillar_b": str,
    }
    """
    pillar_map = {
        "year": year_stem,
        "month": month_stem,
        "day": day_stem,
        "hour": hour_stem,
    }
    pairs = [
        ("year", "month"),
        ("year", "day"),
        ("year", "hour"),
        ("month", "day"),
        ("month", "hour"),
        ("day", "hour"),
    ]
    results = []
    for pa, pb in pairs:
        sa = pillar_map[pa]
        sb = pillar_map[pb]
        if scope == "day_related" and "day" not in (pa, pb):
            continue
        ea = _elem_cn(sa)
        eb = _elem_cn(sb)
        if _STEM_KE.get(ea) == eb:
            results.append(
                {
                    "stem_a": sa,
                    "stem_b": sb,
                    "direction": "a_ke_b",
                    "pillar_a": pa,
                    "pillar_b": pb,
                    "scope": scope,  # P0-11 scope字段存在且非null
                    "note": f"{sa}[{ea}]克{sb}[{eb}]",
                }
            )
        elif _STEM_KE.get(eb) == ea:
            results.append(
                {
                    "stem_a": sa,
                    "stem_b": sb,
                    "direction": "b_ke_a",
                    "pillar_a": pa,
                    "pillar_b": pb,
                    "scope": scope,  # P0-11 scope字段存在且非null
                    "note": f"{sb}[{eb}]克{sa}[{ea}]",
                }
            )
    return results


# ──────────────────────────────────────────────────────────────────────────────
# 地支关系 (1.16)
# ──────────────────────────────────────────────────────────────────────────────


def _branches_in_chart(
    year_branch: str,
    month_branch: str,
    day_branch: str,
    hour_branch: str,
) -> dict[str, str]:
    return {
        "year": year_branch,
        "month": month_branch,
        "day": day_branch,
        "hour": hour_branch,
    }


def _positions_of(branch: str, pillar_map: dict[str, str]) -> list[str]:
    return [pos for pos, b in pillar_map.items() if b == branch]


def get_branch_relations(
    year_branch: str,
    month_branch: str,
    day_branch: str,
    hour_branch: str,
) -> list[dict]:
    """
    计算四柱地支关系（全合/半合/拱合/六合/六冲）.

    每条关系 dict:
    {
        "type": str,       # "三合全合"/"三合半合"/"三合拱合"/"六合"/"六冲"
        "status": str,     # "全合"/"半合"/"拱合"/"合"/"冲"
        "branches": list,  # 参与支
        "positions": list, # 参与柱位
        "element": str,    # 成局五行（三合适用）/ None
    }
    """
    pm = _branches_in_chart(year_branch, month_branch, day_branch, hour_branch)
    present = set(pm.values())
    results = []

    # 三合 (全合/半合/拱合)
    for (b1, b2, b3), elem in SAN_HE:
        trio = {b1, b2, b3}
        hit = trio & present
        if len(hit) == 3:
            status = "全合"
            rtype = "三合全合"
            involved = [b1, b2, b3]
        elif len(hit) == 2 and b2 in hit:  # 含主气(中间支)
            status = "半合"
            rtype = "三合半合"
            involved = sorted(hit, key=lambda x: [b1, b2, b3].index(x))
        elif hit == {b1, b3}:  # 暗拱: 首尾有，主气缺
            status = "拱合"
            rtype = "三合拱合"
            involved = [b1, b3]
        else:
            continue

        positions = [pos for b in involved for pos in _positions_of(b, pm)]
        results.append(
            {
                "type": rtype,
                "status": status,
                "branches": involved,
                "positions": positions,
                "element": elem,
            }
        )

    # 六合
    seen_liuhe: set[frozenset] = set()
    for pos_a, ba in pm.items():
        bb = LIU_HE.get(ba)
        if bb and bb in present:
            key = frozenset({ba, bb})
            if key not in seen_liuhe:
                seen_liuhe.add(key)
                pos_b = [p for p, b in pm.items() if b == bb]
                results.append(
                    {
                        "type": "六合",
                        "status": "合",
                        "branches": [ba, bb],
                        "positions": [pos_a] + pos_b,
                        "element": None,
                    }
                )

    # 六冲
    seen_chong: set[frozenset] = set()
    for pos_a, ba in pm.items():
        bc = BRANCH_CHONG.get(ba)
        if bc and bc in present:
            key = frozenset({ba, bc})
            if key not in seen_chong:
                seen_chong.add(key)
                pos_c = [p for p, b in pm.items() if b == bc]
                results.append(
                    {
                        "type": "六冲",
                        "status": "冲",
                        "branches": [ba, bc],
                        "positions": [pos_a] + pos_c,
                        "element": None,
                    }
                )

    return results
