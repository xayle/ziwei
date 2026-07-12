from __future__ import annotations

from app.schemas.ziwei import ZiweiRequest
from routers.ziwei import _chart_to_response, _ziwei_full_args
from services.ziwei_classic_refs import (
    ZIWEI_CLASSIC_REFS,
    build_chart_classic_refs,
    pattern_candidates,
    star_candidates,
)
from services.ziwei_engine import ziwei_full


def test_ziwei_classic_refs_catalog():
    from services.ziwei_classic_refs import catalog_self_check

    check = catalog_self_check()
    assert check["count"] >= 100
    assert check["with_ctext_page"] == check["count"]
    assert any(r["category"] == "主星" for r in ZIWEI_CLASSIC_REFS)
    assert any(r["category"] == "格局" for r in ZIWEI_CLASSIC_REFS)
    assert all(r.get("source_page") and r.get("ctext_ref") for r in ZIWEI_CLASSIC_REFS[:5])


def test_star_and_pattern_candidates():
    stars = star_candidates(["紫微", "天府"], limit=3)
    assert stars and any("紫微" in s.get("tags", []) for s in stars)
    pats = pattern_candidates("紫府同宫", limit=1)
    assert pats and pats[0].get("category") == "格局"


def test_ziwei_full_response_includes_classic_refs():
    req = ZiweiRequest(
        year=2002,
        month=3,
        day=13,
        hour=14,
        minute=55,
        gender="女",
    )
    chart = ziwei_full(*_ziwei_full_args(req))
    refs = build_chart_classic_refs(chart)
    assert refs
    resp = _chart_to_response(chart, req=req)
    assert resp.classic_refs
    assert resp.classic_refs[0].get("source")
    if resp.patterns:
        assert resp.patterns[0].classic_ref or resp.patterns[0].classic_refs
