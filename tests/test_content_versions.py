"""content_versions meta on full + explain responses (R018)."""

from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from app.schemas import BaziFullRequest
from app.schemas.explain import ExplainBatchRequest, ZiweiExplainBatchRequest
from services.bazi_full_service import bazi_full
from services.chart_snapshot_service import reset_snapshot_cache_for_tests
from services.explain_service import explain_bazi_batch, explain_ziwei_batch


def test_bazi_full_includes_content_versions():
    req = BaziFullRequest(
        dt=datetime(1990, 5, 15, 10, 30, tzinfo=ZoneInfo("Asia/Shanghai")),
        lon=116.4,
        mode="single",
        gender="male",
    )
    resp = bazi_full(req, request_id="content-versions-test")
    assert resp.content_versions
    assert "classics" in resp.content_versions or "disclaimer" in resp.content_versions


def test_ziwei_full_includes_content_versions_and_wenmo_advisory(client):
    resp = client.post(
        "/api/v1/ziwei/full",
        json={
            "year": 1990,
            "month": 5,
            "day": 15,
            "hour": 10,
            "minute": 30,
            "gender": "男",
            "lon": 116.4,
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("content_versions")
    assert data.get("wenmo_advisory")
    assert "文墨" in data["wenmo_advisory"]


def test_explain_batch_includes_content_versions():
    reset_snapshot_cache_for_tests()
    req = ExplainBatchRequest(
        dt=datetime(1990, 5, 15, 10, 30, tzinfo=ZoneInfo("Asia/Shanghai")),
        lon=116.4,
        mode="single",
        gender="male",
        sections=["geju"],
    )
    out = explain_bazi_batch(req)
    assert out.content_versions
    assert "disclaimer" in out.content_versions


def test_ziwei_explain_includes_wenmo_advisory():
    reset_snapshot_cache_for_tests()
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
    assert out.wenmo_advisory
    assert "advisory" in out.wenmo_advisory.lower() or "文墨" in out.wenmo_advisory
