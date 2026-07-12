"""Typed structural_summary / ziwei_structural_summary."""

from __future__ import annotations

import pytest

from services.ziwei_engine import ziwei_full
from services.ziwei_engine.structural_summary import (
    build_chart_structural_summary,
    build_sanfang_structure,
)

GOLDEN = dict(
    year=2002, month=3, day=13, hour=14, minute=55, gender="女", liunian_year=2026,
)


class TestStructuralSummaryBuilder:
    def test_sanfang_has_typed_palaces(self):
        chart = ziwei_full(**GOLDEN)
        sanfang = build_sanfang_structure(chart)
        assert sanfang.life_palace.name == "命宫"
        assert sanfang.life_palace.branch_idx == chart.life_palace_branch
        assert len(sanfang.triad_palaces) == 2
        assert all(p.index >= 0 for p in sanfang.triad_palaces)

    def test_chart_structural_summary_body_palace(self):
        chart = ziwei_full(**GOLDEN)
        summary = build_chart_structural_summary(chart)
        assert summary.body_palace.branch_idx == chart.body_palace_branch
        assert summary.life_branch_idx == chart.life_palace_branch
        assert summary.source == "routers.ziwei.build_response"


class TestStructuralSummaryApi:
    def test_full_response_typed_structural_summary(self, client):
        r = client.post("/api/v1/ziwei/full", json=GOLDEN)
        assert r.status_code == 200
        data = r.json()
        ss = data.get("structural_summary")
        assert ss is not None
        assert ss["life_palace"]["name"] == "命宫"
        assert "sanfang" in ss
        assert isinstance(ss["sanfang"]["triad_palaces"], list)
        assert ss["life_branch_idx"] == data["life_palace_branch_idx"]

    def test_ziwei_structural_summary_core_snapshot_typed(self, client):
        r = client.post("/api/v1/ziwei/full", json=GOLDEN)
        zss = r.json().get("ziwei_structural_summary") or {}
        core = zss.get("core_snapshot") or {}
        assert core.get("life_palace_gz") == r.json()["life_palace_gz"]
        assert "wuxing_ju_name" in core
        pattern = zss.get("pattern_summary") or {}
        assert "special_pattern_names" in pattern
        assert "patterns" in pattern

    def test_sihua_trace_typed_entries(self, client):
        r = client.post("/api/v1/ziwei/full", json=GOLDEN)
        trace = r.json().get("sihua_trace") or []
        if trace:
            entry = trace[0]
            assert "palace" in entry
            assert "flying_out" in entry
            assert isinstance(entry["missing"], bool)
