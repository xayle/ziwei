from __future__ import annotations

from app.schemas.ziwei import ZiweiRequest
from routers.ziwei import _ziwei_full_args
from services.ziwei_engine import ziwei_full
from services.ziwei_provenance import build_ziwei_provenance


def test_build_ziwei_provenance_includes_method_notes():
    req = ZiweiRequest(
        year=2002,
        month=3,
        day=13,
        hour=14,
        minute=55,
        gender="女",
        year_divide="lichun",
        day_divide="forward",
    )
    chart = ziwei_full(*_ziwei_full_args(req))
    prov = build_ziwei_provenance(chart, req)
    assert prov.stars.layer == "engine"
    assert prov.patterns.note and "forward" in prov.patterns.note
    assert prov.forecast.layer == "heuristic"
