from __future__ import annotations

import time

from fastapi.testclient import TestClient

from run import app

client = TestClient(app)

# ── 共用 payload helpers ──────────────────────────────────────────────────────

def _base_payload(**override):
    p = {
        "dt": "2026-02-24T12:34:56+08:00",
        "lon": 120.0,
        "mode": "dual",
        "solar_time_enabled": False,
        "tz": "Asia/Shanghai",
    }
    p.update(override)
    return p


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


# ══════════════════════════════════════════════════════════════════════════════
# M6.04  路由级集成: 400 / 422 / 500 状态码验收
# ══════════════════════════════════════════════════════════════════════════════

def test_verify_400_year_out_of_range():
    """年份低于 BAZI_VERIFY_YEAR_MIN 应返回 400 [P0-06]"""
    resp = client.post("/api/v1/verify", json=_base_payload(dt="1699-06-01T12:00:00+08:00"))
    assert resp.status_code == 400
    assert "超出支持范围" in resp.json().get("detail", "")


def test_verify_400_invalid_tz():
    """无效时区字符串应返回 400，不能 500 [红线26]"""
    resp = client.post("/api/v1/verify", json=_base_payload(tz="Invalid/Zone"))
    assert resp.status_code == 400


def test_verify_422_missing_required_field():
    """缺少必填字段 dt 应返回 422"""
    resp = client.post("/api/v1/verify", json={"lon": 120.0, "mode": "dual",
                                                "solar_time_enabled": False, "tz": "Asia/Shanghai"})
    assert resp.status_code == 422


def test_verify_422_lon_too_large():
    """lon>180 应返回 422 (Pydantic validator) [P0-05]"""
    resp = client.post("/api/v1/verify", json=_base_payload(lon=999.0))
    assert resp.status_code == 422


def test_verify_200_solar_time_enabled():
    """solar_time_enabled=true 仍返回 200 且 solar_time_offset_minutes 有值"""
    resp = client.post("/api/v1/verify", json=_base_payload(solar_time_enabled=True))
    assert resp.status_code == 200
    data = resp.json()
    # offset 可能非零（lon=120 恰好是标准时，偏差为0也合法）
    assert "solar_time_offset_minutes" in data


def test_verify_response_has_rule_version():
    """rule_version 必须随每次计算输出 [红线32]"""
    resp = client.post("/api/v1/verify", json=_base_payload())
    assert resp.status_code == 200
    assert resp.json().get("rule_version") is not None


# ══════════════════════════════════════════════════════════════════════════════
# M6.07  性能基线: /verify 含全部分析 < 3 秒 (P99 on localhost)
# 注: 直接调用 verify_full() 以避免消耗速率限制配额；计算层即为 /verify 耗时主体
# ══════════════════════════════════════════════════════════════════════════════

def test_verify_latency_under_3s():
    """/verify 核心计算耗时 < 3.0s [M6.07]"""
    from datetime import datetime
    from zoneinfo import ZoneInfo
    from verify import verify_full
    dt = datetime(2026, 2, 24, 12, 34, 56, tzinfo=ZoneInfo("Asia/Shanghai"))
    t0 = time.perf_counter()
    result = verify_full(dt, lon=120.0, use_solar=True, mode="dual")
    elapsed = time.perf_counter() - t0
    assert result is not None
    assert elapsed < 3.0, f"verify_full 耗时 {elapsed:.3f}s 超出 3.0s 基线"


def test_verify_latency_p99_5_calls():
    """连续5次 verify_full()，所有调用最大耗时 < 3.0s [M6.07 P99 近似]"""
    from datetime import datetime
    from zoneinfo import ZoneInfo
    from verify import verify_full
    dt = datetime(2026, 2, 24, 12, 34, 56, tzinfo=ZoneInfo("Asia/Shanghai"))
    times = []
    for _ in range(5):
        t0 = time.perf_counter()
        verify_full(dt, lon=120.0, use_solar=False, mode="dual")
        times.append(time.perf_counter() - t0)
    p99_approx = max(times)
    assert p99_approx < 3.0, f"最慢调用 {p99_approx:.3f}s 超出 3s 基线（5次: {[f'{t:.3f}' for t in times]}）"
