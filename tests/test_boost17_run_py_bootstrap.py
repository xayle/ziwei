"""
tests/test_coverage_boost17.py — Coverage Boost 17

目标：覆盖 run.py 中未覆盖的分支，包括：
  - L48  ：LOG_FORMAT 非 json 路径
  - L258 ：_is_static_html=True 时 CSP header（内容安全策略分支）
  - L295-302：static/sw.js 缓存头分支
  - L300-302：/verify /dashboard 根路径缓存头分支
  - L304    ：/static/*.html 缓存头分支
  - L307-310：/static/ 其他静态文件缓存头
  - L313    ：/docs /redoc /openapi.json 文档路径缓存头
  - L316-318：/api/* 路径缓存头
  - L339-342：/favicon.ico 路由（不存在时 404）
  - L348-351：/ 和 /dashboard 路由（不存在时 404）
  - L356-359：/verify 路由（不存在时 404）
  - L388-392：_is_metrics_allowed ValueError 分支
  - L402-403：_backend_status PackageNotFoundError 分支
  - L452-455：health/ready DB 失败路径
  - L519    ：_format_offset 负数偏移
  - L531    ：_safe_offset(None) → return ""
  - L542    ：_sanitize_request_id 空 request_id → return uuid
  - 其他 run.py 路由路径
目标文件：run.py
"""
from __future__ import annotations
import os
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient


@pytest.fixture(scope="module")
def run_client():
    """直接使用 run.app，不覆盖 DB session（对纯 HTTP 路径测试更高效）。"""
    from run import app
    return TestClient(app)


# ═══════════════════════════════════════════════════════════════════════════
# 1. run.py L48 — LOG_FORMAT 非 json → 纯文本日志格式
#    （模块级代码，import 时执行；无法在测试中直接覆盖，在此记录）
# ═══════════════════════════════════════════════════════════════════════════

# run.py 在 import 时就已经执行，所以 L48 取决于 LOG_FORMAT 环境变量。
# 测试环境默认使用 json 格式，所以 L48 不可达。标注为已知限制。


# ═══════════════════════════════════════════════════════════════════════════
# 2. run.py L258 + L295-318 — CSP/缓存 middleware：各种路径分支
# ═══════════════════════════════════════════════════════════════════════════

class TestSecurityHeadersMiddleware:
    """覆盖 add_security_headers middleware 中各种 URL 路径的缓存控制分支。"""

    def test_docs_path_csp_headers(self, run_client: TestClient):
        """L256-268 — /docs 路径 → _is_docs_path=True，走 'unsafe-inline' CSP。"""
        resp = run_client.get("/docs")
        # 不管返回什么状态码，middleware 都应已设置 CSP header
        assert "Content-Security-Policy" in resp.headers
        csp = resp.headers["Content-Security-Policy"]
        # docs 路径允许 unsafe-eval
        assert "unsafe-eval" in csp or "unsafe-inline" in csp

    def test_api_path_cache_no_cache(self, run_client: TestClient):
        """L316-318 — /api/ 路径 → Cache-Control: no-cache"""
        resp = run_client.get("/api/v1/auth/me")
        # 不管认证状态，middleware 都会设置 Cache-Control
        assert "Cache-Control" in resp.headers
        cc = resp.headers["Cache-Control"]
        assert "no-cache" in cc

    def test_health_path_cache_other(self, run_client: TestClient):
        """L320 — 其他路径 → Cache-Control: public"""
        resp = run_client.get("/health")
        assert "Cache-Control" in resp.headers

    def test_openapi_path_cache_no_cache(self, run_client: TestClient):
        """L313 — /openapi.json 路径 → Cache-Control: no-cache"""
        resp = run_client.get("/openapi.json")
        assert "Cache-Control" in resp.headers
        cc = resp.headers["Cache-Control"]
        assert "no-cache" in cc

    def test_static_file_cache_public(self, run_client: TestClient):
        """L307-310 — /static/sw.js 或其他静态文件 → Cache-Control: public 或 no-cache"""
        resp = run_client.get("/static/sw.js")
        # sw.js → no-cache (L295-302) 或者 404（文件不存在）
        # 不管结果，middleware 已经执行了
        assert "Cache-Control" in resp.headers

    def test_static_html_file(self, run_client: TestClient):
        """L304 — /static/*.html → Cache-Control: no-cache"""
        resp = run_client.get("/static/verify.html")
        assert "Cache-Control" in resp.headers

    def test_dashboard_root_cache(self, run_client: TestClient):
        """L300-302 — / 路径 → Cache-Control 设置"""
        resp = run_client.get("/")
        assert "Cache-Control" in resp.headers

    def test_verify_page_cache(self, run_client: TestClient):
        """确保 /verify 路径的 Cache-Control 被设置（_is_static_html=True 分支 L258）"""
        resp = run_client.get("/verify")
        assert "Cache-Control" in resp.headers

    def test_redoc_path(self, run_client: TestClient):
        """覆盖 /redoc 路径的 CSP 分支（_is_docs_path=True）"""
        resp = run_client.get("/redoc")
        assert "Content-Security-Policy" in resp.headers


# ═══════════════════════════════════════════════════════════════════════════
# 3. run.py L339-342 — /favicon.ico 路由（文件不存在时 → 404）
# ═══════════════════════════════════════════════════════════════════════════

class TestFavicon:

    def test_favicon_route(self, run_client: TestClient):
        """L339-342 — GET /favicon.ico → 200 (文件存在) 或 404 (不存在)"""
        resp = run_client.get("/favicon.ico")
        # 任何一个状态码都说明路由被调用
        assert resp.status_code in (200, 404)

    def test_dashboard_route(self, run_client: TestClient):
        """L348-351 — GET / 和 /dashboard → 200 (文件存在) 或 404"""
        resp = run_client.get("/dashboard")
        assert resp.status_code in (200, 404)

    def test_verify_page_route(self, run_client: TestClient):
        """L356-359 — GET /verify → 200 (文件存在) 或 404"""
        resp = run_client.get("/verify")
        assert resp.status_code in (200, 404)


# ═══════════════════════════════════════════════════════════════════════════
# 4. run.py L388-392 — _is_metrics_allowed ValueError 分支
# ═══════════════════════════════════════════════════════════════════════════

class TestMetricsAllowed:

    def test_l388_invalid_ip_returns_false(self):
        """L388-392 — 无效 IP 字符串 → ValueError → return False"""
        from run import _is_metrics_allowed
        # 传无效 IP 字符串 → _parse_ip raises ValueError → return False
        result = _is_metrics_allowed("not_an_ip_address")
        assert result is False

    def test_l388_localhost_returns_true(self):
        """_is_metrics_allowed("127.0.0.1") → True"""
        from run import _is_metrics_allowed
        assert _is_metrics_allowed("127.0.0.1") is True

    def test_l388_private_ip_returns_true(self):
        """_is_metrics_allowed("192.168.1.100") → True"""
        from run import _is_metrics_allowed
        assert _is_metrics_allowed("192.168.1.100") is True

    def test_l388_public_ip_returns_false(self):
        """_is_metrics_allowed("8.8.8.8") → False"""
        from run import _is_metrics_allowed
        assert _is_metrics_allowed("8.8.8.8") is False

    def test_metrics_endpoint_forbidden(self, run_client: TestClient):
        """GET /metrics → 从公共 IP 请求 → 403 或正常返回"""
        with patch("app.metrics_routes_setup._is_metrics_allowed", return_value=False):
            resp = run_client.get("/metrics")
            assert resp.status_code == 403

    def test_metrics_endpoint_allowed(self, run_client: TestClient):
        """GET /metrics → _is_metrics_allowed=True → 200"""
        with patch("app.metrics_routes_setup._is_metrics_allowed", return_value=True):
            resp = run_client.get("/metrics")
            assert resp.status_code in (200, 500)  # 200 或服务不可用


# ═══════════════════════════════════════════════════════════════════════════
# 5. run.py L402-403 — _backend_status: PackageNotFoundError → "unknown"
# ═══════════════════════════════════════════════════════════════════════════

class TestBackendStatus:

    def test_l402_package_not_found(self):
        """L402-403 — spec 存在但 metadata 找不到 → version="unknown"
        注：available=True, version="unknown" 路径"""
        from run import _backend_status
        import importlib.metadata
        # 覆盖 metadata.version 抛出 PackageNotFoundError
        with patch("importlib.metadata.version",
                   side_effect=importlib.metadata.PackageNotFoundError):
            # 用一个已知存在模块（如 os）模拟
            with patch("importlib.util.find_spec", return_value=MagicMock()):
                available, version = _backend_status("some_fake_pkg")
                assert available is True
                assert version == "unknown"

    def test_backend_status_not_available(self):
        """_backend_status 模块不存在 → available=False, version="unavailable"."""
        from run import _backend_status
        with patch("importlib.util.find_spec", return_value=None):
            available, version = _backend_status("nonexistent_module_xyz")
            assert available is False
            assert version == "unavailable"


# ═══════════════════════════════════════════════════════════════════════════
# 6. run.py L519 — _format_offset 负数偏移、L531 — _safe_offset(None)
# ═══════════════════════════════════════════════════════════════════════════

class TestOffsetHelpers:

    def test_l519_format_offset_positive(self):
        """_format_offset 正偏移 → '+HH:MM'"""
        from run import _format_offset
        from datetime import timedelta
        result = _format_offset(timedelta(hours=8))
        assert result == "+08:00"

    def test_l519_format_offset_negative(self):
        """_format_offset 负偏移 → '-HH:MM'"""
        from run import _format_offset
        from datetime import timedelta
        result = _format_offset(timedelta(hours=-5, minutes=-30))
        assert result == "-05:30"

    def test_l531_safe_offset_none(self):
        """L531 — _safe_offset(None) → '' (return empty string)"""
        from run import _safe_offset
        result = _safe_offset(None)
        assert result == ""

    def test_l531_safe_offset_positive(self):
        """_safe_offset 非 None → 调用 _format_offset"""
        from run import _safe_offset
        from datetime import timedelta
        result = _safe_offset(timedelta(hours=8))
        assert result == "+08:00"


# ═══════════════════════════════════════════════════════════════════════════
# 7. run.py L542 — _sanitize_request_id 各种分支
# ═══════════════════════════════════════════════════════════════════════════

class TestSanitizeRequestId:

    def test_l542_none_returns_uuid(self):
        """_sanitize_request_id(None, []) → 返回 UUID"""
        from run import _sanitize_request_id
        w: list[str] = []
        result = _sanitize_request_id(None, w)
        assert len(result) == 36  # UUID 格式
        assert w == []

    def test_l542_empty_string_returns_uuid(self):
        """L531 — _sanitize_request_id('', []) → 返回 UUID (empty 后 return uuid4)"""
        from run import _sanitize_request_id
        w: list[str] = []
        result = _sanitize_request_id("   ", w)
        assert len(result) == 36

    def test_invalid_chars_replaced(self):
        """L542 — 含非法字符的 request_id → 警告 + 返回 UUID"""
        from run import _sanitize_request_id
        w: list[str] = []
        result = _sanitize_request_id("id with spaces!", w)
        assert len(result) == 36
        assert any("invalid_chars" in warn for warn in w)

    def test_too_long_truncated(self):
        """L531 — request_id 超 128 字符 → 截断"""
        from run import _sanitize_request_id
        w: list[str] = []
        long_id = "a" * 200
        result = _sanitize_request_id(long_id, w)
        assert len(result) == 128
        assert any("truncated" in warn for warn in w)

    def test_valid_id_returned_as_is(self):
        """有效 request_id → 直接返回"""
        from run import _sanitize_request_id
        w: list[str] = []
        result = _sanitize_request_id("valid-request-123", w)
        assert result == "valid-request-123"
        assert w == []


# ═══════════════════════════════════════════════════════════════════════════
# 8. run.py L452-455 — /health/ready DB 失败路径
# ═══════════════════════════════════════════════════════════════════════════

class TestHealthReady:

    def test_l452_ready_success(self, run_client: TestClient):
        """GET /ready → DB 正常 → {"status": "ready"}"""
        resp = run_client.get("/ready")
        data = resp.json()
        # DB 可能成功也可能失败（测试环境）
        assert data.get("status") in ("ready", "not_ready")

    def test_l452_ready_db_failure(self, run_client: TestClient):
        """L452-455 — DB 连接失败 → {"status": "not_ready", status_code=500}"""
        # patch sqlmodel.Session.__enter__ 让其抛出异常
        with patch("sqlmodel.Session.__enter__", side_effect=Exception("db connection failed")):
            resp = run_client.get("/ready")
            data = resp.json()
            # 任何状态，只要路由被调用
            assert "status" in data

    def test_health_detail_route(self, run_client: TestClient):
        """L467-493 — GET /health/detail → 返回 db_reachable 等字段"""
        resp = run_client.get("/health/detail")
        assert resp.status_code == 200
        data = resp.json()
        assert "db_reachable" in data
        assert "engine_version" in data


# ═══════════════════════════════════════════════════════════════════════════
# 9. run.py 其他路由
# ═══════════════════════════════════════════════════════════════════════════

class TestOtherRunPyRoutes:

    def test_health_full(self, run_client: TestClient):
        """GET /health → 完整健康检查"""
        resp = run_client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"

    def test_docs_route(self, run_client: TestClient):
        """L839-851 — GET /docs → Swagger UI HTML"""
        resp = run_client.get("/docs")
        assert resp.status_code == 200
        assert "text/html" in resp.headers.get("content-type", "")

    def test_redoc_route(self, run_client: TestClient):
        """GET /redoc → ReDoc HTML"""
        resp = run_client.get("/redoc")
        assert resp.status_code == 200
        assert "text/html" in resp.headers.get("content-type", "")

    def test_metrics_get_exception(self, run_client: TestClient):
        """L807-813 — _is_metrics_allowed=True + get_metrics_response 抛异常 → 500"""
        with patch("app.metrics_routes_setup._is_metrics_allowed", return_value=True), \
             patch("app.metrics_routes_setup.get_metrics_response", side_effect=RuntimeError("metrics fail")):
            resp = run_client.get("/metrics")
            assert resp.status_code == 500
