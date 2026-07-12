"""R033: bazi /full horoscope edge cases — no 500 on boundary inputs."""

from __future__ import annotations

from unittest.mock import patch

from fastapi.testclient import TestClient

from run import app

client = TestClient(app)

_BASE = {
    "lon": 121.47,
    "mode": "dual",
    "solar_time_enabled": False,
    "tz": "Asia/Shanghai",
    "gender": "male",
}


def test_full_early_zi_window_returns_200():
    """子时边界：23:30 不应 500。"""
    resp = client.post(
        "/api/v1/bazi/full",
        json={**_BASE, "mode": "single", "dt": "2026-06-15T23:30:00"},
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["raw"]["day_boundary_crossed"] is True


def test_full_solar_time_enabled_returns_200():
    """真太阳时切换不应 500。"""
    resp = client.post(
        "/api/v1/bazi/full",
        json={**_BASE, "dt": "1990-07-17T12:20:00", "solar_time_enabled": True},
    )
    assert resp.status_code == 200, resp.text
    assert resp.json().get("pillars_primary")


def test_full_dual_mode_dayun_liunian_present():
    """双轨模式：大运/流年骨架应存在。"""
    resp = client.post(
        "/api/v1/bazi/full",
        json={**_BASE, "dt": "1990-07-17T12:20:00", "liunian_years": [-1, 1]},
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["dayun"]["items"]
    assert data["liunian"]["items"]


def test_full_monthly_fortune_is_list_or_none():
    """流月：允许空列表，不得异常。"""
    resp = client.post(
        "/api/v1/bazi/full",
        json={**_BASE, "dt": "1990-07-17T12:20:00"},
    )
    assert resp.status_code == 200, resp.text
    monthly = resp.json().get("monthly_fortune")
    assert monthly is None or isinstance(monthly, list)


def test_full_jieqi_unavailable_dayun_still_200():
    """节气上下文缺失时仍应 200（大运可降级，不得 500）。"""
    with patch("services.bazi_full_service.get_jieqi_context", return_value=None):
        resp = client.post(
            "/api/v1/bazi/full",
            json={**_BASE, "dt": "1990-07-17T12:20:00"},
        )
    assert resp.status_code == 200, resp.text
    assert "dayun" in resp.json()


def test_missing_fields_hour_pillar_when_unknown_precision():
    """R029: unknown 时辰精度标注 hour_pillar。"""
    resp = client.post(
        "/api/v1/bazi/full",
        json={**_BASE, "dt": "1990-07-17T12:20:00", "birth_time_precision": "unknown"},
    )
    assert resp.status_code == 200, resp.text
    assert "hour_pillar" in resp.json().get("missing_fields", [])


def test_missing_fields_jieqi_boundary_near_anchor():
    """R029: 节气边界窗口标注 jieqi_boundary。"""
    resp = client.post(
        "/api/v1/bazi/full",
        json={**_BASE, "dt": "1990-03-06T05:00:00"},
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data.get("risk_flags", {}).get("near_jieqi_boundary") is True
    assert "jieqi_boundary" in data.get("missing_fields", [])


def test_evidence_ids_linked_to_rules_and_chain():
    """R034: evidence_ids 来自 rule_matches / evidence_chain。"""
    resp = client.post(
        "/api/v1/bazi/full",
        json={**_BASE, "dt": "1990-07-17T12:20:00"},
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    evidence_ids = data.get("evidence_ids") or []
    assert isinstance(evidence_ids, list)
    rule_ids = [rm.get("rule_id") for rm in (data.get("rule_matches") or []) if rm.get("rule_id")]
    for rid in rule_ids:
        assert rid in evidence_ids
    chain_sources = [item.get("source") for item in (data.get("evidence_chain") or []) if item.get("source")]
    for src in chain_sources:
        assert f"chain:{src}" in evidence_ids
