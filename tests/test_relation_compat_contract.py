"""Contract tests for relation-compat@1.0 response."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from services.chart_snapshot_service import reset_snapshot_cache_for_tests

ROOT = Path(__file__).resolve().parent.parent
GOLDEN_PATH = ROOT / "data" / "relation_golden_cases.json"

COUPLE_PAYLOAD = {
    "relation_type": "couple",
    "person_a": {
        "birth_datetime": "1990-07-17T12:25:00",
        "tz": "Asia/Shanghai",
        "longitude": 117.18,
        "gender": "female",
        "label": "刘博",
    },
    "person_b": {
        "birth_datetime": "1990-06-17T20:15:00",
        "tz": "Asia/Shanghai",
        "longitude": 117.49,
        "gender": "male",
        "label": "程安东",
    },
    "options": {"include_bazi": True, "include_ziwei": True, "liunian_year": 2026},
}


@pytest.fixture(autouse=True)
def _reset_cache():
    reset_snapshot_cache_for_tests()
    yield
    reset_snapshot_cache_for_tests()


class TestRelationCompatContract:
    def test_relation_full_returns_schema_version(self, client: TestClient):
        resp = client.post("/api/v1/relation/full", json=COUPLE_PAYLOAD)
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["schema_version"] == "relation-compat@1.0"
        assert data["relation_type"] == "couple"
        assert "combined_score" in data
        assert "dimensions" in data
        assert len(data["dimensions"]) >= 6
        assert len(data.get("summary_cards") or []) >= 3
        assert len(data.get("timeline") or []) >= 4
        assert len(data.get("palace_cross") or []) >= 2
        assert data.get("disclaimer_block", {}).get("text")

    def test_day_branch_dimension_present(self, client: TestClient):
        resp = client.post("/api/v1/relation/full", json=COUPLE_PAYLOAD)
        data = resp.json()
        dims = {d["id"]: d for d in data["dimensions"]}
        assert "day_branch" in dims
        assert dims["day_branch"]["score"] <= dims["day_branch"]["max_score"] * 0.2 + 1

    def test_compat_full_deprecated_delegates(self, client: TestClient):
        payload = {
            "person_a": COUPLE_PAYLOAD["person_a"],
            "person_b": COUPLE_PAYLOAD["person_b"],
            "include_bazi": True,
            "include_ziwei": True,
        }
        resp = client.post("/api/v1/compat/full", json=payload)
        assert resp.status_code == 200, resp.text
        assert resp.headers.get("Deprecation") == "true"
        body = resp.json()
        assert body["combined_score"] > 0

    def test_supervisor_requires_role(self, client: TestClient):
        payload = {
            "relation_type": "supervisor_subordinate",
            "person_a": COUPLE_PAYLOAD["person_a"],
            "person_b": COUPLE_PAYLOAD["person_b"],
        }
        resp = client.post("/api/v1/relation/full", json=payload)
        assert resp.status_code == 422
