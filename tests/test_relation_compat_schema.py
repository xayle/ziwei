"""Contract shape validation for relation-compat@1.0 (no jsonschema dep)."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from services.chart_snapshot_service import reset_snapshot_cache_for_tests

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

REQUIRED_TOP = {
    "schema_version",
    "relation_type",
    "person_a",
    "person_b",
    "combined_score",
    "summary",
    "disclaimer_block",
    "layers",
    "dimensions",
    "timeline",
    "missing_fields",
}


@pytest.fixture(autouse=True)
def _reset_cache():
    reset_snapshot_cache_for_tests()
    yield
    reset_snapshot_cache_for_tests()


def _assert_contract_shape(data: dict) -> None:
    assert data.get("schema_version") == "relation-compat@1.0"
    missing = REQUIRED_TOP - set(data.keys())
    assert not missing, f"missing keys: {missing}"
    assert isinstance(data["dimensions"], list) and data["dimensions"]
    assert isinstance(data["timeline"], list) and len(data["timeline"]) >= 4
    assert data["disclaimer_block"].get("text")
    for dim in data["dimensions"]:
        for key in ("id", "label", "score", "max_score", "weight", "description", "layer"):
            assert key in dim, dim
    layers = data["layers"]
    for layer in ("fact", "cite", "inference"):
        assert layer in layers


class TestRelationCompatSchema:
    def test_response_required_fields(self, client: TestClient):
        resp = client.post("/api/v1/relation/full", json=COUPLE_PAYLOAD)
        assert resp.status_code == 200, resp.text
        _assert_contract_shape(resp.json())

    def test_summary_cards_have_action_tone(self, client: TestClient):
        resp = client.post("/api/v1/relation/full", json=COUPLE_PAYLOAD)
        tones = {c["tone"] for c in resp.json().get("summary_cards") or []}
        assert "action" in tones

    def test_forbidden_copy_not_in_friend_summary(self, client: TestClient):
        payload = {
            **COUPLE_PAYLOAD,
            "relation_type": "friend",
            "person_b": {
                "birth_datetime": "1992-03-08T08:00:00",
                "tz": "Asia/Shanghai",
                "longitude": 116.41,
                "gender": "male",
                "label": "友人",
            },
        }
        resp = client.post("/api/v1/relation/full", json=payload)
        assert resp.status_code == 200
        assert "婚后" not in (resp.json().get("summary") or "")
