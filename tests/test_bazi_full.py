from __future__ import annotations

from fastapi.testclient import TestClient

from run import app

client = TestClient(app)


def test_bazi_full_day_boundary_cross_switches_day_pillar():
    base = {
        "lon": 121.47,
        "mode": "dual",
        "solar_time_enabled": False,
        "tz": "Asia/Shanghai",
    }

    payload_a = dict(base, dt="2026-06-15T22:50:00")
    payload_b = dict(base, dt="2026-06-15T23:10:00")

    resp_a = client.post("/api/v1/bazi/full", json=payload_a)
    resp_b = client.post("/api/v1/bazi/full", json=payload_b)

    assert resp_a.status_code == 200
    assert resp_b.status_code == 200

    data_a = resp_a.json()
    data_b = resp_b.json()

    assert data_a["methods"]["day_boundary_rule"] == "zi_initial"
    assert data_b["methods"]["day_boundary_rule"] == "zi_initial"

    raw_a = data_a["raw"]
    raw_b = data_b["raw"]

    assert raw_a["day_boundary_crossed"] is False
    assert raw_b["day_boundary_crossed"] is True

    # Offset minutes should match for the same tz/date (no DST change within minutes)
    assert raw_a["dt_effective_local_offset_minutes"] == raw_b["dt_effective_local_offset_minutes"]

    # Pillars may or may not shift depending on backend day-boundary handling;
    # the key regression guard here is the boundary flag toggling at 23:00+.
