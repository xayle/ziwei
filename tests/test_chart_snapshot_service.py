"""ChartSnapshot single-compute tests."""

from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from app.schemas import BaziFullRequest
from services.chart_snapshot_service import (
    build_bazi_snapshot,
    get_build_counts,
    reset_snapshot_cache_for_tests,
)


def _sample_request() -> BaziFullRequest:
    return BaziFullRequest(
        dt=datetime(1990, 5, 15, 10, 30, tzinfo=ZoneInfo("Asia/Shanghai")),
        lon=116.4,
        mode="single",
        gender="male",
    )


def test_bazi_snapshot_computes_once_per_hash():
    reset_snapshot_cache_for_tests()
    req = _sample_request()
    snap1 = build_bazi_snapshot(req, request_id="r1")
    snap2 = build_bazi_snapshot(req, request_id="r2")
    assert snap1.chart_hash == snap2.chart_hash
    assert snap1.response.request_id == snap2.response.request_id
    counts = get_build_counts()
    assert counts["bazi"] == 1
