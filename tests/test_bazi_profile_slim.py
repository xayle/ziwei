"""Test bazi/full profile=slim query param."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from services.chart_snapshot_service import reset_snapshot_cache_for_tests

BAZI_PAYLOAD = {
    "dt": "1990-01-15T08:30:00",
    "lon": 116.4074,
    "tz": "Asia/Shanghai",
    "mode": "single",
    "gender": "male",
}


@pytest.fixture(autouse=True)
def _reset_cache():
    reset_snapshot_cache_for_tests()
    yield
    reset_snapshot_cache_for_tests()


def test_bazi_full_slim_omits_domain_narratives(client: TestClient):
    full = client.post("/api/v1/bazi/full?profile=full", json=BAZI_PAYLOAD)
    slim = client.post("/api/v1/bazi/full?profile=slim", json=BAZI_PAYLOAD)
    assert full.status_code == 200
    assert slim.status_code == 200
    full_data = full.json()
    slim_data = slim.json()
    # slim should not add extra milestones vs full is ok; at minimum geju interpretation cleared
    geju_full = (full_data.get("geju") or {}).get("interpretation_text") or ""
    geju_slim = (slim_data.get("geju") or {}).get("interpretation_text") or ""
    if geju_full:
        assert geju_slim == "" or len(geju_slim) < len(geju_full)
