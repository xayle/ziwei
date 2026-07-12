"""Golden-case regression for relation/full."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from services.chart_snapshot_service import reset_snapshot_cache_for_tests

GOLDEN_PATH = Path(__file__).resolve().parent.parent / "data" / "relation_golden_cases.json"


@pytest.fixture(autouse=True)
def _reset_cache():
    reset_snapshot_cache_for_tests()
    yield
    reset_snapshot_cache_for_tests()


def _load_cases():
    raw = json.loads(GOLDEN_PATH.read_text(encoding="utf-8"))
    return raw["cases"]


@pytest.mark.parametrize("case", _load_cases(), ids=lambda c: c["id"])
def test_golden_relation_case(client: TestClient, case: dict):
    req = case["request"]
    resp = client.post("/api/v1/relation/full", json=req)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assertions = case.get("assertions") or {}

    if "day_branch_max_score_ratio" in assertions:
        dims = {d["id"]: d for d in data["dimensions"]}
        db = dims["day_branch"]
        ratio = db["score"] / db["max_score"]
        assert ratio <= assertions["day_branch_max_score_ratio"] + 0.05

    if "day_branch_contains" in assertions:
        dims = {d["id"]: d for d in data["dimensions"]}
        assert assertions["day_branch_contains"] in dims["day_branch"]["description"]

    if "summary_cards_conflict_contains" in assertions:
        needle = assertions["summary_cards_conflict_contains"]
        cards = data.get("summary_cards") or []
        conflict_texts = [c["text"] for c in cards if c.get("tone") == "conflict"]
        assert any(needle in t for t in conflict_texts)

    if "min_dimensions" in assertions:
        assert len(data["dimensions"]) >= assertions["min_dimensions"]

    if "min_timeline_nodes" in assertions:
        assert len(data.get("timeline") or []) >= assertions["min_timeline_nodes"]

    if "min_palace_cross" in assertions:
        assert len(data.get("palace_cross") or []) >= assertions["min_palace_cross"]

    if "forbidden_in_summary" in assertions:
        summary = data.get("summary") or ""
        for word in assertions["forbidden_in_summary"]:
            assert word not in summary

    if "dimension_ids_include" in assertions:
        ids_set = {d["id"] for d in data["dimensions"]}
        for dim_id in assertions["dimension_ids_include"]:
            assert dim_id in ids_set

    if "palace_cross_contains_palace" in assertions:
        palace = assertions["palace_cross_contains_palace"]
        crosses = data.get("palace_cross") or []
        assert any(
            palace in (c.get("a_palace") or "") or palace in (c.get("b_palace") or "")
            for c in crosses
        )

    if assertions.get("min_summary_cards"):
        assert len(data.get("summary_cards") or []) >= assertions["min_summary_cards"]
