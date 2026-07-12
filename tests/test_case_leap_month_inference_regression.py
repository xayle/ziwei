from __future__ import annotations

from fastapi.testclient import TestClient


LEAP_MONTH_CASE_PAYLOAD = {
    "name": "闰月回归案例",
    "gender": "female",
    "birth_dt_local": "1990-07-17T20:00:00",
    "tz": "Asia/Shanghai",
    "birth_dt": "1990-07-17T12:00:00Z",
    "city": "Shanghai",
    "lon": 121.47,
    "solar_time_enabled": False,
    "calendar_mode": "gregorian",
}


def _create_leap_month_case(client_with_auth: TestClient) -> dict:
    response = client_with_auth.post("/api/v1/cases", json=LEAP_MONTH_CASE_PAYLOAD)
    assert response.status_code == 201, response.text
    payload = response.json()
    assert payload["is_leap_month"] is True
    assert payload["is_leap_month_inferred"] is True
    return payload


def test_case_detail_returns_inferred_leap_month(client_with_auth: TestClient):
    created = _create_leap_month_case(client_with_auth)

    response = client_with_auth.get(f"/api/v1/cases/{created['id']}")
    assert response.status_code == 200, response.text

    payload = response.json()
    assert payload["id"] == created["id"]
    assert payload["is_leap_month"] is True
    assert payload["is_leap_month_inferred"] is True


def test_case_list_returns_inferred_leap_month(client_with_auth: TestClient):
    created = _create_leap_month_case(client_with_auth)

    response = client_with_auth.get("/api/v1/cases")
    assert response.status_code == 200, response.text

    payload = response.json()
    items = payload["items"]
    matched = next((item for item in items if item["id"] == created["id"]), None)
    assert matched is not None, payload
    assert matched["is_leap_month"] is True
    assert matched["is_leap_month_inferred"] is True


def test_case_export_returns_inferred_leap_month(client_with_auth: TestClient):
    created = _create_leap_month_case(client_with_auth)

    response = client_with_auth.get(f"/api/v1/cases/{created['id']}/export")
    assert response.status_code == 200, response.text

    payload = response.json()
    input_snapshot = payload["input_snapshot"]
    assert input_snapshot["id"] == created["id"]
    assert input_snapshot["is_leap_month"] is True
