"""GET /life/volumes/{case_id} draft API (R096)."""

from __future__ import annotations

from services.chart_snapshot_service import reset_snapshot_cache_for_tests


def test_life_volumes_returns_eight_volumes(client_with_auth, test_case):
    reset_snapshot_cache_for_tests()
    resp = client_with_auth.get(f"/api/v1/life/volumes/{test_case.id}")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["schema_version"] == "life-volume@1.0"
    assert data["case_id"] == test_case.id
    assert data["chart_hash"]
    assert len(data["volumes"]) == 8
    assert data["disclaimer_block"]["text"]
    assert data["colophon"]["summary_lines"]
    assert len(data["colophon"]["summary_lines"]) <= 3
    ids = [v["id"] for v in data["volumes"]]
    assert ids == ["preface", "vol1", "vol2", "vol3", "vol4", "vol5", "vol6", "colophon"]


def test_life_volumes_vol5_collapsed_by_default(client_with_auth, test_case):
    reset_snapshot_cache_for_tests()
    resp = client_with_auth.get(f"/api/v1/life/volumes/{test_case.id}")
    vol5 = next(v for v in resp.json()["volumes"] if v["id"] == "vol5")
    if vol5["sections"]:
        assert all(s.get("collapsed_default") for s in vol5["sections"])


def test_life_volumes_not_found(client_with_auth):
    resp = client_with_auth.get("/api/v1/life/volumes/nonexistent-case-id")
    assert resp.status_code == 404
