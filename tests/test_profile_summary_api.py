"""GET /api/v1/profile/{case_id}/summary — profile-summary@1.0."""

from __future__ import annotations

from services.chart_snapshot_service import reset_snapshot_cache_for_tests


def test_profile_summary_returns_disclaimer_block(client_with_auth, test_case):
    reset_snapshot_cache_for_tests()
    resp = client_with_auth.get(f"/api/v1/profile/{test_case.id}/summary")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["schema_version"] == "profile-summary@1.0"
    assert data["case_id"] == test_case.id
    assert data["pillars_primary"]
    disclaimer = data.get("disclaimer_block") or {}
    assert disclaimer.get("text")
    assert disclaimer.get("jurisdiction") in (None, "CN", "")


def test_profile_summary_not_found(client_with_auth):
    resp = client_with_auth.get("/api/v1/profile/nonexistent-case-id/summary")
    assert resp.status_code == 404
