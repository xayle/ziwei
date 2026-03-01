from __future__ import annotations

from datetime import datetime, timedelta

from fastapi.testclient import TestClient

from run import app


client = TestClient(app)


def test_dayun_next_jieqi_anchor_boundary_is_stable():
    base = {
        "lon": 121.47,
        "mode": "dual",
        "solar_time_enabled": False,
        "tz": "Asia/Shanghai",
        # Pick an arbitrary local time; anchor will drive before/after.
        "dt": "2024-05-10T12:00:00",
    }

    # Step 1: fetch anchor at a base time
    resp = client.post("/api/v1/bazi/full", json=base)
    assert resp.status_code == 200
    data = resp.json()
    raw = data["raw"]
    dayun = raw["dayun"]

    # Anchor must be tz-aware with +08:00
    anchor_iso = dayun["anchor_jieqi_dt"]
    assert anchor_iso is not None
    anchor_dt = datetime.fromisoformat(anchor_iso)
    assert anchor_dt.utcoffset() == timedelta(hours=8)

    # Next anchor should be after effective local time
    eff_local = datetime.fromisoformat(raw["dt_effective_local"])
    assert anchor_dt > eff_local

    # Step 2: before/after around the anchor
    before = dict(base, dt=(anchor_dt - timedelta(minutes=10)).isoformat())
    after = dict(base, dt=(anchor_dt + timedelta(minutes=10)).isoformat())

    resp_before = client.post("/api/v1/bazi/full", json=before)
    resp_after = client.post("/api/v1/bazi/full", json=after)
    assert resp_before.status_code == 200
    assert resp_after.status_code == 200

    raw_before = resp_before.json()["raw"]["dayun"]
    raw_after = resp_after.json()["raw"]["dayun"]

    # sequence_start should stay explicit
    assert raw_before.get("sequence_start") == "from_month_pillar"
    assert raw_after.get("sequence_start") == "from_month_pillar"

    anchor_before = datetime.fromisoformat(raw_before["anchor_jieqi_dt"])
    anchor_after = datetime.fromisoformat(raw_after["anchor_jieqi_dt"])

    # Before stays on the same anchor, after moves to the next
    assert anchor_before == anchor_dt
    assert anchor_after > anchor_dt

    # Names should differ across the boundary
    assert raw_before.get("anchor_jieqi_name") != raw_after.get("anchor_jieqi_name")

    # birth_to_jieqi_days grows after crossing
    assert raw_before["birth_to_jieqi_days"] < raw_after["birth_to_jieqi_days"]
