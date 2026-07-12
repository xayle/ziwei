"""Dual-person timeline merge for relation compatibility."""

from __future__ import annotations

from datetime import datetime
from typing import Any

# 地支 → 生肖
_BRANCH_ANIMAL = {
    "子": "鼠",
    "丑": "牛",
    "寅": "虎",
    "卯": "兔",
    "辰": "龙",
    "巳": "蛇",
    "午": "马",
    "未": "羊",
    "申": "猴",
    "酉": "鸡",
    "戌": "狗",
    "亥": "猪",
}

_CHONG_PAIRS = {
    frozenset({"子", "午"}),
    frozenset({"丑", "未"}),
    frozenset({"寅", "申"}),
    frozenset({"卯", "酉"}),
    frozenset({"辰", "戌"}),
    frozenset({"巳", "亥"}),
}


def _liunian_branch(year: int) -> str:
    stems = "甲乙丙丁戊己庚辛壬癸"
    branches = "子丑寅卯辰巳午未申酉戌亥"
    return stems[(year - 4) % 10] + branches[(year - 4) % 12]


def _tai_sui_tag(person_branch: str, liunian_branch: str) -> str | None:
    lb = liunian_branch[1] if len(liunian_branch) > 1 else liunian_branch
    pb = person_branch
    if lb == pb:
        return "值太岁"
    pair = frozenset({lb, pb})
    if pair in _CHONG_PAIRS:
        return "冲太岁"
    return None


def build_timeline(
    *,
    year_a: str,
    year_b: str,
    liunian_year: int | None = None,
    span_before: int = 1,
    span_after: int = 2,
    relation_type: str = "couple",
) -> list[dict[str, Any]]:
    base = liunian_year or datetime.now().year
    nodes: list[dict[str, Any]] = []
    ba = year_a[1] if len(year_a) > 1 else year_a
    bb = year_b[1] if len(year_b) > 1 else year_b

    for y in range(base - span_before, base + span_after + 1):
        gz = _liunian_branch(y)
        lb = gz[1]
        tags: list[str] = []
        risk = "低"
        for label, pb in (("甲", ba), ("乙", bb)):
            ts = _tai_sui_tag(pb, gz)
            if ts:
                tags.append(f"{label}·{ts}")
                if ts == "冲太岁":
                    risk = "高"
                elif ts == "值太岁" and risk != "高":
                    risk = "中"
        if lb == ba or lb == bb:
            tags.append(f"流年{lb}与年支呼应")
        summary_parts = tags or [f"{y}年{gz}，平稳过渡"]
        nodes.append(
            {
                "year": y,
                "label": f"{y}·{gz}",
                "summary": "；".join(summary_parts)[:200],
                "risk_level": risk,
            }
        )

    return nodes
