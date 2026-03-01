from __future__ import annotations

from fastapi.testclient import TestClient

from run import app

client = TestClient(app)


def test_wuxing_breakdown_sums_to_score():
    payload = {
        "dt": "2024-05-10T12:00:00",
        "lon": 121.47,
        "mode": "dual",
        "solar_time_enabled": False,
        "tz": "Asia/Shanghai",
    }
    resp = client.post("/api/v1/bazi/full", json=payload)
    assert resp.status_code == 200
    data = resp.json()

    score = data["wuxing_score"]
    breakdown = data["wuxing_breakdown"]

    for elem in ["wood", "fire", "earth", "metal", "water"]:
        total = (
            breakdown["stem_contrib"].get(elem, 0)
            + breakdown["branch_contrib"].get(elem, 0)
            + breakdown["hidden_contrib"].get(elem, 0)
        )
        assert abs(total - score[elem]) < 1e-6

    strength = data["day_master_strength"]
    assert strength["tier"] in ["strong", "balanced", "weak"]

    yongshen = data["yongshen"]
    assert len(yongshen["favor"]) >= 1
    assert len(yongshen["avoid"]) >= 1
    assert yongshen["rationale"]
