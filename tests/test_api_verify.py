from __future__ import annotations

from fastapi.testclient import TestClient

from run import app

client = TestClient(app)


def test_verify_ok_with_request_id():
    payload = {
        "dt": "2026-02-24T12:34:56+08:00",
        "lon": 120.0,
        "mode": "dual",
        "solar_time_enabled": False,
        "tz": "Asia/Shanghai",
    }
    headers = {"X-Request-Id": "test-123"}
    resp = client.post("/api/v1/verify", json=payload, headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    for key in [
        "api_version",
        "rule_version",
        "request_id",
        "backend",
        "pillars_primary",
        "risk_flags",
        "validation",
        "mode_requested",
        "mode_effective",
        "dt_input",
        "dt_effective_utc8",
    ]:
        assert key in data
    assert data["solar_time_offset_minutes"] == 0.0
    assert data["validation"]["mode"] in ["dual", "single"]
    assert data["request_id"] == "test-123"
    assert resp.headers.get("X-Request-Id") == "test-123"


def test_verify_lon_out_of_range():
    payload = {
        "dt": "2026-02-24T12:34:56+08:00",
        "lon": 200.0,
        "mode": "dual",
        "solar_time_enabled": False,
        "tz": "Asia/Shanghai",
    }
    resp = client.post("/api/v1/verify", json=payload)
    assert resp.status_code == 422
    detail = str(resp.json().get("detail", ""))
    assert "lon must be between" in detail


def test_verify_single_mode_has_no_secondary():
    payload = {
        "dt": "2026-02-24T12:34:56+08:00",
        "lon": 120.0,
        "mode": "single",
        "solar_time_enabled": False,
        "tz": "Asia/Shanghai",
    }
    resp = client.post("/api/v1/verify", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["validation"]["mode"] == "single"
    assert data["pillars_secondary"] is None


def test_verify_tz_mismatch_warning():
    payload = {
        "dt": "2026-02-24T12:34:56+09:00",
        "lon": 120.0,
        "mode": "dual",
        "solar_time_enabled": False,
        "tz": "Asia/Shanghai",
    }
    resp = client.post("/api/v1/verify", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    warnings = data["validation"].get("warnings", [])
    assert any(w.get("code") == "legacy" and "tz_mismatch" in w.get("message", "") for w in warnings)


def test_request_id_invalid_chars_replaced_with_warning():
    payload = {
        "dt": "2026-02-24T12:34:56+08:00",
        "lon": 120.0,
        "mode": "dual",
        "solar_time_enabled": False,
        "tz": "Asia/Shanghai",
    }
    bad_id = "bad id"
    resp = client.post("/api/v1/verify", json=payload, headers={"X-Request-Id": bad_id})
    assert resp.status_code == 200
    data = resp.json()
    assert data["request_id"] != bad_id
    assert resp.headers.get("X-Request-Id") == data["request_id"]
    warnings = data["validation"].get("warnings", [])
    assert any(w.get("code") == "legacy" and "request_id_invalid_chars" in w.get("message", "") for w in warnings)


def test_request_id_truncated_with_warning():
    payload = {
        "dt": "2026-02-24T12:34:56+08:00",
        "lon": 120.0,
        "mode": "dual",
        "solar_time_enabled": False,
        "tz": "Asia/Shanghai",
    }
    long_id = "a" * 130
    resp = client.post("/api/v1/verify", json=payload, headers={"X-Request-Id": long_id})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["request_id"]) == 128
    assert data["request_id"].startswith("a" * 128)
    assert resp.headers.get("X-Request-Id") == data["request_id"]
    warnings = data["validation"].get("warnings", [])
    assert any(w.get("code") == "legacy" and "request_id_truncated" in w.get("message", "") for w in warnings)
