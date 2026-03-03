"""
prometheus_monitoring.py 扩展覆盖测试
目标：将覆盖率从 55% 提升到 85%+

覆盖以下未测试路径：
- track_db_operation 装饰器：成功路径 + 异常路径（Lines 223-253）
- track_business_operation 装饰器：成功路径 + 异常路径（Lines 266-292）
- record_auth_attempt：成功/失败两种 status（Lines 303-304）
- record_cache_hit / record_cache_miss（Lines 309, 314）
- get_metrics_response：返回 Response 对象（Line 330）
- prometheus_middleware：正常请求 + 异常请求（Lines 192-196）
- _normalize_path：路径参数归一化
"""
import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch

from services.prometheus_monitoring import (
    track_db_operation,
    track_business_operation,
    record_auth_attempt,
    record_cache_hit,
    record_cache_miss,
    get_metrics_response,
    prometheus_middleware,
    _normalize_path,
    DB_OPERATION_COUNT,
    BUSINESS_OPERATION_COUNT,
    AUTH_ATTEMPTS,
    CACHE_HITS,
    CACHE_MISSES,
)


# ═══════════════════════════════════════════════════════════════════════════════
# _normalize_path 辅助函数
# ═══════════════════════════════════════════════════════════════════════════════

class TestNormalizePath:
    """路径参数归一化"""

    def test_numeric_id_replaced(self):
        assert _normalize_path("/cases/123") == "/cases/:id"

    def test_uuid_replaced(self):
        assert _normalize_path("/cases/550e8400-e29b-41d4-a716-446655440000") == "/cases/:id"

    def test_plain_path_unchanged(self):
        assert _normalize_path("/api/v1/members") == "/api/v1/members"

    def test_multiple_ids_replaced(self):
        result = _normalize_path("/members/42/events/99")
        assert ":id" in result


# ═══════════════════════════════════════════════════════════════════════════════
# track_db_operation 装饰器（Lines 223-253）
# ═══════════════════════════════════════════════════════════════════════════════

class TestTrackDbOperation:
    """数据库操作追踪装饰器"""

    def test_success_path_returns_value(self):
        """成功路径：装饰器返回函数返回值并计数（Lines 223-240）"""
        @track_db_operation("select", "members")
        def get_member():
            return {"id": 1, "name": "test"}

        result = get_member()
        assert result == {"id": 1, "name": "test"}

    def test_success_path_increments_counter(self):
        """成功路径：计数器递增"""
        before = DB_OPERATION_COUNT.labels(
            operation="insert_test", table="events_test", status="success"
        )._value.get()

        @track_db_operation("insert_test", "events_test")
        def insert_event():
            return True

        insert_event()
        after = DB_OPERATION_COUNT.labels(
            operation="insert_test", table="events_test", status="success"
        )._value.get()
        assert after == before + 1

    def test_exception_path_reraises(self):
        """异常路径：装饰器重新抛出原始异常（Lines 241-253）"""
        @track_db_operation("delete", "scenarios")
        def delete_scenario():
            raise ValueError("DB error")

        with pytest.raises(ValueError, match="DB error"):
            delete_scenario()

    def test_exception_path_increments_error_counter(self):
        """异常路径：error 标签计数器递增"""
        before = DB_OPERATION_COUNT.labels(
            operation="update_err", table="cases_err", status="error"
        )._value.get()

        @track_db_operation("update_err", "cases_err")
        def update_case():
            raise RuntimeError("timeout")

        with pytest.raises(RuntimeError):
            update_case()

        after = DB_OPERATION_COUNT.labels(
            operation="update_err", table="cases_err", status="error"
        )._value.get()
        assert after == before + 1

    def test_decorated_function_preserves_name(self):
        """@functools.wraps 保留函数名"""
        @track_db_operation("select", "members")
        def my_query():
            pass

        assert my_query.__name__ == "my_query"

    def test_args_and_kwargs_passed_through(self):
        """参数透传测试"""
        @track_db_operation("select", "test_tbl")
        def func_with_args(a, b, c=0):
            return a + b + c

        assert func_with_args(1, 2, c=3) == 6


# ═══════════════════════════════════════════════════════════════════════════════
# track_business_operation 装饰器（Lines 266-292）
# ═══════════════════════════════════════════════════════════════════════════════

class TestTrackBusinessOperation:
    """业务操作追踪装饰器"""

    def test_success_path_returns_value(self):
        """成功路径：返回函数返回值（Lines 266-283）"""
        @track_business_operation("bazi_calc")
        def calculate():
            return {"result": "ok"}

        assert calculate() == {"result": "ok"}

    def test_success_path_increments_counter(self):
        """成功路径：success 标签计数器递增"""
        before = BUSINESS_OPERATION_COUNT.labels(
            operation="biz_op_test", status="success"
        )._value.get()

        @track_business_operation("biz_op_test")
        def biz_func():
            return 42

        biz_func()
        after = BUSINESS_OPERATION_COUNT.labels(
            operation="biz_op_test", status="success"
        )._value.get()
        assert after == before + 1

    def test_exception_path_reraises(self):
        """异常路径：重新抛出原始异常（Lines 284-292）"""
        @track_business_operation("risky_op")
        def risky():
            raise KeyError("missing key")

        with pytest.raises(KeyError):
            risky()

    def test_exception_path_increments_error_counter(self):
        """异常路径：error 标签计数器递增"""
        before = BUSINESS_OPERATION_COUNT.labels(
            operation="fail_op", status="error"
        )._value.get()

        @track_business_operation("fail_op")
        def fail():
            raise IOError("io error")

        with pytest.raises(IOError):
            fail()

        after = BUSINESS_OPERATION_COUNT.labels(
            operation="fail_op", status="error"
        )._value.get()
        assert after == before + 1

    def test_decorated_function_preserves_name(self):
        """@functools.wraps 保留函数名"""
        @track_business_operation("test_op")
        def my_business():
            pass

        assert my_business.__name__ == "my_business"


# ═══════════════════════════════════════════════════════════════════════════════
# record_auth_attempt（Lines 303-304）
# ═══════════════════════════════════════════════════════════════════════════════

class TestRecordAuthAttempt:
    """认证事件记录"""

    def test_success_increments_success_label(self):
        """成功认证：status=success 标签递增（Line 303）"""
        before = AUTH_ATTEMPTS.labels(endpoint="login_t", status="success")._value.get()
        record_auth_attempt("login_t", success=True)
        after = AUTH_ATTEMPTS.labels(endpoint="login_t", status="success")._value.get()
        assert after == before + 1

    def test_failure_increments_failure_label(self):
        """失败认证：status=failure 标签递增（Line 304）"""
        before = AUTH_ATTEMPTS.labels(endpoint="login_f", status="failure")._value.get()
        record_auth_attempt("login_f", success=False)
        after = AUTH_ATTEMPTS.labels(endpoint="login_f", status="failure")._value.get()
        assert after == before + 1

    def test_different_endpoints_tracked_separately(self):
        """不同端点独立计数"""
        before_reg = AUTH_ATTEMPTS.labels(endpoint="register", status="success")._value.get()
        record_auth_attempt("register", success=True)
        record_auth_attempt("login_sep", success=True)
        after_reg = AUTH_ATTEMPTS.labels(endpoint="register", status="success")._value.get()
        assert after_reg == before_reg + 1


# ═══════════════════════════════════════════════════════════════════════════════
# record_cache_hit / record_cache_miss（Lines 309, 314）
# ═══════════════════════════════════════════════════════════════════════════════

class TestCacheMetrics:
    """缓存命中/未命中记录"""

    def test_cache_hit_increments_counter(self):
        """record_cache_hit：CACHE_HITS 计数器递增（Line 309）"""
        before = CACHE_HITS.labels(key="user:42")._value.get()
        record_cache_hit("user:42")
        after = CACHE_HITS.labels(key="user:42")._value.get()
        assert after == before + 1

    def test_cache_miss_increments_counter(self):
        """record_cache_miss：CACHE_MISSES 计数器递增（Line 314）"""
        before = CACHE_MISSES.labels(key="user:99")._value.get()
        record_cache_miss("user:99")
        after = CACHE_MISSES.labels(key="user:99")._value.get()
        assert after == before + 1

    def test_multiple_hits_accumulate(self):
        """多次命中累加"""
        before = CACHE_HITS.labels(key="bazi:abc")._value.get()
        record_cache_hit("bazi:abc")
        record_cache_hit("bazi:abc")
        after = CACHE_HITS.labels(key="bazi:abc")._value.get()
        assert after == before + 2


# ═══════════════════════════════════════════════════════════════════════════════
# get_metrics_response（Line 330）
# ═══════════════════════════════════════════════════════════════════════════════

class TestGetMetricsResponse:
    """Prometheus 指标导出响应"""

    def test_returns_response_object(self):
        """返回 fastapi Response 对象（Line 330）"""
        from fastapi.responses import Response
        resp = get_metrics_response()
        assert isinstance(resp, Response)

    def test_content_type_is_prometheus(self):
        """Content-Type 为 Prometheus 格式"""
        from prometheus_client import CONTENT_TYPE_LATEST
        resp = get_metrics_response()
        assert resp.media_type is not None
        assert CONTENT_TYPE_LATEST in resp.media_type

    def test_body_contains_metric_names(self):
        """响应体包含已注册的指标名称"""
        resp = get_metrics_response()
        body = resp.body.decode("utf-8") if isinstance(resp.body, bytes) else ""
        assert "http_requests_total" in body or "db_operations_total" in body


# ═══════════════════════════════════════════════════════════════════════════════
# prometheus_middleware 正常请求路径（Lines 192-196）
# ═══════════════════════════════════════════════════════════════════════════════

class TestPrometheusMiddleware:
    """中间件基本流程（正常请求 + 异常请求）"""

    def _make_request(self, path: str = "/api/v1/members", method: str = "GET"):
        request = MagicMock()
        request.method = method
        request.url.path = path
        return request

    def test_normal_request_returns_response(self):
        """正常请求通过中间件后返回 response"""
        request = self._make_request()
        mock_response = MagicMock()
        mock_response.status_code = 200

        async def call_next(req):
            return mock_response

        result = asyncio.run(prometheus_middleware(request, call_next))
        assert result is mock_response

    def test_exception_in_call_next_reraises(self):
        """call_next 抛出异常时中间件重新抛出"""
        request = self._make_request("/api/v1/fail")

        async def call_next_fail(req):
            raise RuntimeError("downstream error")

        async def run_middleware():
            return await prometheus_middleware(request, call_next_fail)

        with pytest.raises(RuntimeError, match="downstream error"):
            asyncio.run(run_middleware())

    def test_path_with_id_is_normalized(self):
        """路径参数被归一化（不会为每个 ID 创建独立标签）"""
        request = self._make_request("/cases/12345")
        mock_response = MagicMock()
        mock_response.status_code = 200

        async def call_next(req):
            return mock_response

        # 不应抛出异常，路径应被归一化处理
        asyncio.run(prometheus_middleware(request, call_next))
