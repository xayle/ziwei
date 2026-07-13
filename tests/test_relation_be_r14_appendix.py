"""BE-R14 multi_compat alignment + T113 relation appendix API."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.models import Case
from services.chart_snapshot_service import reset_snapshot_cache_for_tests

_PERSON_A = {
    "year": 1990,
    "month": 7,
    "day": 17,
    "hour": 12,
    "minute": 25,
    "gender": "女",
    "longitude": 117.18,
}
_PERSON_B = {
    "year": 1990,
    "month": 6,
    "day": 17,
    "hour": 20,
    "minute": 15,
    "gender": "男",
    "longitude": 117.49,
}


@pytest.fixture(autouse=True)
def _reset_cache():
    reset_snapshot_cache_for_tests()
    yield
    reset_snapshot_cache_for_tests()


def test_multi_compat_legacy_shape_unchanged(client: TestClient):
    resp = client.post(
        "/api/v1/ziwei/multi_compat",
        json={"person_list": [_PERSON_A, _PERSON_B]},
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["schema_version"] == "multi-compat@1.0"
    assert data["person_count"] == 2
    pair = data["pairs"][0]
    assert pair["combined_score"] is None
    assert "matrix" in data


def test_multi_compat_with_relation_dims(client: TestClient):
    resp = client.post(
        "/api/v1/ziwei/multi_compat",
        json={
            "person_list": [_PERSON_A, _PERSON_B],
            "relation_type": "couple",
            "include_relation_dims": True,
            "labels": ["刘博", "程安东"],
        },
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["schema_version"] == "multi-compat@1.1"
    assert data["relation_type"] == "couple"
    pair = data["pairs"][0]
    assert pair["combined_score"] is not None
    assert pair["bazi_score"] is not None
    assert pair["ziwei_score"] is not None
    assert pair["grade"]
    assert len(pair["dimension_highlights"]) >= 1


def test_relation_appendix_not_found(client_with_auth):
    resp = client_with_auth.get(
        "/api/v1/relation/appendix",
        params={"case_id": "nonexistent-a", "partner_case_id": "nonexistent-b"},
    )
    assert resp.status_code == 404


def test_relation_appendix_for_cases(client_with_auth, test_case, db_session):
    partner = Case(
        id=str(uuid4()),
        name="Partner Case",
        gender="female",
        birth_dt_local="1990-06-17T20:15:00",
        tz="Asia/Shanghai",
        birth_dt="1990-06-17T12:15:00Z",
        city="Tianjin",
        lon=117.49,
        solar_time_enabled=False,
        owner_id=test_case.owner_id,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db_session.add(partner)
    db_session.commit()

    resp = client_with_auth.get(
        "/api/v1/relation/appendix",
        params={
            "case_id": test_case.id,
            "partner_case_id": partner.id,
            "relation_type": "couple",
        },
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["schema_version"] == "relation-appendix@1.0"
    assert data["case_id"] == test_case.id
    assert data["partner_case_id"] == partner.id
    assert data["combined_score"] > 0
    assert len(data["sections"]) >= 1
    assert data["sections"][0]["layer"] == "fact"
    assert data.get("disclaimer_block", {}).get("text")
