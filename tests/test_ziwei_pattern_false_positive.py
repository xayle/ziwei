"""紫微格局负例回归 — ZW01–ZW16 各 1 条应不成立格局（PRODUCT-P-ROADMAP W4 / BE-P1-02）。"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from services.ziwei_engine import ziwei_full

ROOT = Path(__file__).parent.parent
GT_PATH = ROOT / "data" / "ziwei_ground_truth.json"

# case_id -> pattern that must NOT appear (historical false-positive targets)
_NEGATIVE_BY_CASE: list[tuple[str, str]] = [
    ("ZW01", "紫府同宫"),
    ("ZW02", "紫府同宫"),
    ("ZW03", "紫府同宫"),
    ("ZW04", "杀破狼"),
    ("ZW05", "紫府同宫"),
    ("ZW06", "紫府同宫"),
    ("ZW07", "禄存守命"),
    ("ZW08", "杀破狼"),
    ("ZW09", "紫府同宫"),
    ("ZW10", "杀破狼"),
    ("ZW11", "杀破狼"),
    ("ZW12", "紫府同宫"),
    ("ZW13", "紫府同宫"),
    ("ZW14", "紫府同宫"),
    ("ZW15", "紫府同宫"),
    ("ZW16", "紫府同宫"),
]


def _load_cases() -> dict[str, dict]:
    data = json.loads(GT_PATH.read_text(encoding="utf-8"))
    return {c["id"]: c for c in data["cases"]}


@pytest.mark.parametrize("case_id,pattern_name", _NEGATIVE_BY_CASE)
def test_pattern_must_not_fire(case_id: str, pattern_name: str):
    cases = _load_cases()
    case = cases[case_id]
    b = case["birth"]
    chart = ziwei_full(
        b["year"],
        b["month"],
        b["day"],
        b["hour"],
        b.get("minute", 0),
        b["gender"],
    )
    detected = {p.name for p in chart.patterns}
    assert pattern_name not in detected, f"{case_id} false positive: {pattern_name} in {sorted(detected)}"
