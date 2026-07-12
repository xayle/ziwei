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


def test_ziwei_explain_palaces_blocks_at_least_forty_chars():
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
    assert len(palaces.blocks) >= 12
    for block in palaces.blocks:
        assert len(block.text) >= 40, block.text


def test_ziwei_explain_fortune_dayun_blocks_are_substantive():
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
        sections=["fortune"],
    )
    out = explain_ziwei_batch(req)
    fortune = next(s for s in out.sections if s.section_id == "fortune")
    dayun_blocks = [b for b in fortune.blocks if b.text.startswith("第") and "限" in b.text]
    assert dayun_blocks
    assert all(len(b.text) >= 40 for b in dayun_blocks)


def test_bazi_explain_relations_block_at_least_forty_chars():
    reset_snapshot_cache_for_tests()
    req = ExplainBatchRequest(
        dt=datetime(1990, 1, 15, 8, 30, tzinfo=ZoneInfo("Asia/Shanghai")),
        lon=116.41,
        mode="single",
        gender="male",
        sections=["relations"],
    )
    out = explain_bazi_batch(req)
    relations = next(s for s in out.sections if s.section_id == "relations")
    assert relations.blocks
    assert all(len(b.text) >= 40 for b in relations.blocks)


def test_bazi_explain_dayun_formats_age_and_includes_detail():
    reset_snapshot_cache_for_tests()
    req = ExplainBatchRequest(
        dt=datetime(1990, 1, 15, 8, 30, tzinfo=ZoneInfo("Asia/Shanghai")),
        lon=116.41,
        mode="single",
        gender="male",
        sections=["dayun"],
    )
    out = explain_bazi_batch(req)
    dayun = next(s for s in out.sections if s.section_id == "dayun")
    assert dayun.blocks
    joined = " ".join(b.text for b in dayun.blocks)
    assert ".0岁" not in joined
    assert any(len(b.text) >= 40 for b in dayun.blocks)
