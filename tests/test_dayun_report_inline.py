from __future__ import annotations

from fastapi.testclient import TestClient

from run import app

client = TestClient(app)


def test_dayun_report_inline_no_auth():
    payload = {
        "dt": "1990-01-15T08:30:00",
        "lon": 116.41,
        "tz": "Asia/Shanghai",
        "mode": "single",
        "solar_time_enabled": False,
        "gender": "male",
    }
    resp = client.post("/api/v1/bazi/dayun-report/inline", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    assert isinstance(data["items"], list)
    assert len(data["items"]) > 0
    assert "narrative_total_chars" in data
    assert data["narrative_total_chars"] > 0
    first = data["items"][0]
    assert first.get("ganzhi")
    assert first.get("narrative")
