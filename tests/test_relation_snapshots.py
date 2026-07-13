"""BE-R16 relation snapshot list/detail API."""

from __future__ import annotations

from datetime import UTC, datetime, timezone
from uuid import uuid4

import pytest

from app.models import Case
from services.chart_snapshot_service import reset_snapshot_cache_for_tests


@pytest.fixture(autouse=True)
def _reset_cache():
    reset_snapshot_cache_for_tests()
    yield
    reset_snapshot_cache_for_tests()


@pytest.fixture
def partner_case(db_session, test_case):
    case = Case(
        id=str(uuid4()),
        name="Partner Case",
        gender="male",
        birth_dt_local="1990-06-17T20:15:00",
        tz="Asia/Shanghai",
        birth_dt="1990-06-17T12:15:00Z",
        city="Tianjin",
        lon=117.49,
        solar_time_enabled=False,
        owner_id=test_case.owner_id,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    db_session.add(case)
    db_session.commit()
    db_session.refresh(case)
    return case


def test_relation_snapshots_empty(client_with_auth, test_case):
    resp = client_with_auth.get(
        "/api/v1/relation/snapshots",
        params={"case_id": test_case.id},
    )
    assert resp.status_code == 200, resp.text
    assert resp.json() == []


def test_relation_full_creates_listable_snapshot(client_with_auth, test_case, partner_case):
    payload = {
        "relation_type": "couple",
        "person_a": {
            "case_id": test_case.id,
            "label": test_case.name,
        },
        "person_b": {
            "case_id": partner_case.id,
            "label": partner_case.name,
        },
    }
    full = client_with_auth.post("/api/v1/relation/full", json=payload)
    assert full.status_code == 200, full.text
    meta = full.json().get("meta") or {}
    assert meta.get("snapshots_created")

    listed = client_with_auth.get(
        "/api/v1/relation/snapshots",
        params={"case_id": test_case.id, "partner_case_id": partner_case.id},
    )
    assert listed.status_code == 200, listed.text
    items = listed.json()
    assert len(items) >= 1
    item = items[0]
    assert item["partner_case_id"] == partner_case.id
    assert item["relation_type"] == "couple"
    assert item["combined_score"] is not None

    detail = client_with_auth.get(f"/api/v1/relation/snapshots/{item['id']}")
    assert detail.status_code == 200, detail.text
    body = detail.json()
    assert body["output"]["schema_version"] == "relation-compat@1.0"
    assert body["partner_case_id"] == partner_case.id
    assert body["output"]["combined_score"] == item["combined_score"]


def test_relation_snapshot_not_found(client_with_auth):
    resp = client_with_auth.get("/api/v1/relation/snapshots/nonexistent-id")
    assert resp.status_code == 404
