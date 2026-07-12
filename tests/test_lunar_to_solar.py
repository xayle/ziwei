from __future__ import annotations

from fastapi.testclient import TestClient


def test_lunar_to_solar_endpoint(client: TestClient):
    resp = client.post(
        "/api/v1/bazi/lunar-to-solar",
        json={
            "lunar_year": 1990,
            "lunar_month": 1,
            "lunar_day": 15,
            "hour": 8,
            "minute": 30,
            "is_leap_month": False,
        },
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["solar_year"] == 1990
    assert data["solar_month"] == 2
    assert data["solar_day"] == 10
    assert data["solar_dt"] == "1990-02-10T08:30:00"
    assert "农历1990年1月15日" in data["lunar_label"]
