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
        assert elem in score
        assert elem in breakdown["stem_contrib"]
        assert elem in breakdown["branch_contrib"]
        assert elem in breakdown["hidden_contrib"]

    assert abs(sum(score[e] for e in score) - 100.0) < 1.0

    strength = data["day_master_strength"]
    assert strength["tier"] in ["\u6781\u65fa", "\u504f\u65fa", "\u4e2d\u548c", "\u504f\u5f31", "\u6781\u5f31"]

    yongshen = data["yongshen"]
    assert len(yongshen["favor"]) >= 1
    assert len(yongshen["avoid"]) >= 1
    assert yongshen["rationale"]
