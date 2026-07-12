"""Explain batch API tests."""

from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from app.schemas.explain import ExplainBatchRequest
from services.chart_snapshot_service import reset_snapshot_cache_for_tests
from services.explain_service import explain_bazi_batch, explain_ziwei_batch


def test_bazi_explain_batch_geju_relations_summary():
    reset_snapshot_cache_for_tests()
    req = ExplainBatchRequest(
        dt=datetime(1990, 5, 15, 10, 30, tzinfo=ZoneInfo("Asia/Shanghai")),
        lon=116.4,
        mode="single",
        gender="male",
        sections=["geju", "relations", "reading"],
    )
    out = explain_bazi_batch(req, request_id="explain-test")
    assert out.chart_hash
    assert out.disclaimer_block.text
    ids = {s.section_id for s in out.sections}
    assert ids == {"geju", "relations", "reading"}
    for section in out.sections:
        assert section.blocks
        for block in section.blocks:
            if block.layer == "cite":
                assert block.classic_id


def test_bazi_explain_batch_max_four_sections():
    reset_snapshot_cache_for_tests()
    req = ExplainBatchRequest(
        dt=datetime(1985, 3, 3, 8, 0, tzinfo=ZoneInfo("Asia/Shanghai")),
        lon=121.5,
        mode="single",
        gender="female",
        sections=["geju", "relations", "dayun", "summary"],
    )
    out = explain_bazi_batch(req)
    assert len(out.sections) == 4


def test_ziwei_explain_palaces_uses_star_profiles_reference():
    reset_snapshot_cache_for_tests()
    from app.schemas.explain import ZiweiExplainBatchRequest

    req = ZiweiExplainBatchRequest(
        year=1990,
        month=5,
        day=15,
        hour=10,
        minute=30,
        gender="男",
        lon=116.4,
        sections=["palaces"],
    )
    out = explain_ziwei_batch(req)
    palaces = next(s for s in out.sections if s.section_id == "palaces")
    texts = " ".join(b.text for b in palaces.blocks)
    assert "命宫" in texts
    inference_blocks = [b for b in palaces.blocks if b.layer == "inference"]
    assert inference_blocks, "star_profiles key_points should surface as inference blocks"
