"""
tests/test_normalize_rate_auth.py

覆盖三个低覆盖率模块的缺失分支：

  1. services/normalize_input.py   → 3 missing lines (None/type check, range raise, cn_range append)
  2. services/rate_limit.py        → 3 missing lines (认证用户 user_id key 路径)
  3. app/dependencies/auth.py      → 9 missing lines (_local_dummy_user body, bypass path,
                                      ValueError path, inactive/missing user, require_user raise)
"""
from __future__ import annotations

import os
import pytest
from unittest.mock import MagicMock, patch


# ═══════════════════════════════════════════════════════════════════════════════
# 1. services/normalize_input.py
# ═══════════════════════════════════════════════════════════════════════════════

class TestValidateLonStrict:
    """validate_lon_strict(): None/类型错误 及 范围越界 分支"""

    def test_none_raises_400(self):
        """lon=None → HTTPException 400 lon_invalid  (line 12)"""
        from services.normalize_input import validate_lon_strict
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            validate_lon_strict(None)  # type: ignore[arg-type]
        assert exc_info.value.status_code == 400
        assert exc_info.value.detail["code"] == "lon_invalid"

    def test_string_raises_400(self):
        """lon='abc' → not isinstance(float) → HTTPException 400  (line 12)"""
        from services.normalize_input import validate_lon_strict
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            validate_lon_strict("not_a_number")  # type: ignore[arg-type]
        assert exc_info.value.status_code == 400
        assert exc_info.value.detail["code"] == "lon_invalid"

    def test_out_of_range_raises_400(self):
        """lon=999.0 → range check fails → HTTPException 400 lon_out_of_range  (line 14)"""
        from services.normalize_input import validate_lon_strict
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            validate_lon_strict(999.0)
        assert exc_info.value.status_code == 400
        assert exc_info.value.detail["code"] == "lon_out_of_range"

    def test_negative_out_of_range_raises(self):
        """lon=-200.0 → 也属于 range 越界"""
        from services.normalize_input import validate_lon_strict
        from fastapi import HTTPException
        with pytest.raises(HTTPException):
            validate_lon_strict(-200.0)

    def test_valid_lon_returns_value(self):
        """lon=120.0 → returns 120.0 (正常路径 smoke)"""
        from services.normalize_input import validate_lon_strict
        result = validate_lon_strict(120.0)
        assert result == 120.0

    def test_boundary_min_lon_ok(self):
        """lon=-180.0 → 边界值，合法"""
        from services.normalize_input import validate_lon_strict
        assert validate_lon_strict(-180.0) == -180.0

    def test_boundary_max_lon_ok(self):
        """lon=180.0 → 边界值，合法"""
        from services.normalize_input import validate_lon_strict
        assert validate_lon_strict(180.0) == 180.0


class TestWarnLonCnRange:
    """warn_lon_cn_range(): cn_range append 分支  (line 24)"""

    def test_outside_cn_range_shanghai_tz_returns_warning(self):
        """tz=Asia/Shanghai + lon 在中国范围 [73,135] 以外 → 追加警告  (line 24)"""
        from services.normalize_input import warn_lon_cn_range
        # lon=50 < 73 → outside CN range
        warns = warn_lon_cn_range("Asia/Shanghai", 50.0)
        assert len(warns) == 1
        assert warns[0]["code"] == "lon_out_of_cn_range"
        assert warns[0]["meta"]["lon"] == 50.0

    def test_above_cn_range_returns_warning(self):
        """lon=140 > 135 → 也在 CN 范围之外"""
        from services.normalize_input import warn_lon_cn_range
        warns = warn_lon_cn_range("Asia/Shanghai", 140.0)
        assert len(warns) == 1
        assert warns[0]["code"] == "lon_out_of_cn_range"

    def test_inside_cn_range_no_warning(self):
        """lon=116.4 在 [73,135] 之内 → 空列表"""
        from services.normalize_input import warn_lon_cn_range
        warns = warn_lon_cn_range("Asia/Shanghai", 116.4)
        assert warns == []

    def test_non_shanghai_tz_no_warning(self):
        """非 Asia/Shanghai 时区 → 不触发检查 → 空列表"""
        from services.normalize_input import warn_lon_cn_range
        warns = warn_lon_cn_range("America/New_York", 50.0)
        assert warns == []


# ═══════════════════════════════════════════════════════════════════════════════
# 2. services/rate_limit.py
# ═══════════════════════════════════════════════════════════════════════════════

class TestRateLimitKey:
    """_rate_limit_key(): 三条路径覆盖"""

    def test_auth_bypass_returns_unique_key(self):
        """AUTH_BYPASS=true → 每次返回不同 UUID → 不触发限流"""
        from services.rate_limit import _rate_limit_key
        request = MagicMock()
        with patch.dict(os.environ, {"AUTH_BYPASS": "true"}):
            k1 = _rate_limit_key(request)
            k2 = _rate_limit_key(request)
        # 两次不同以保证每请求独立
        assert k1 != k2
        # 格式为 UUID hex 字符串
        assert len(k1) == 36  # uuid4 with dashes

    def test_authenticated_user_id_attr(self):
        """AUTH_BYPASS=false + user.id=42 → 返回 'user:42'  (lines 23-25)"""
        from services.rate_limit import _rate_limit_key
        request = MagicMock()
        mock_user = MagicMock()
        mock_user.id = 42
        mock_user.user_id = None
        request.state.user = mock_user
        with patch.dict(os.environ, {"AUTH_BYPASS": "false"}):
            key = _rate_limit_key(request)
        assert key == "user:42"

    def test_authenticated_user_user_id_fallback(self):
        """user.id=None → 回退到 user.user_id  (lines 23-25)"""
        from services.rate_limit import _rate_limit_key
        request = MagicMock()
        mock_user = MagicMock()
        mock_user.id = None        # id 为 None → falsy → 用 user_id
        mock_user.user_id = 99
        request.state.user = mock_user
        with patch.dict(os.environ, {"AUTH_BYPASS": "false"}):
            key = _rate_limit_key(request)
        assert key == "user:99"

    def test_unauthenticated_falls_back_to_ip(self):
        """无 user 属性 → 回退到 remote IP"""
        from services.rate_limit import _rate_limit_key

        class _NoAttrState:
            pass  # 没有 .user 属性

        request = MagicMock()
        request.state = _NoAttrState()
        with patch.dict(os.environ, {"AUTH_BYPASS": "false"}):
            with patch("services.rate_limit.get_remote_address", return_value="1.2.3.4"):
                key = _rate_limit_key(request)
        assert key == "1.2.3.4"

    def test_user_none_state_falls_back_to_ip(self):
        """request.state.user=None → 回退到 remote IP"""
        from services.rate_limit import _rate_limit_key
        request = MagicMock()
        request.state.user = None
        with patch.dict(os.environ, {"AUTH_BYPASS": "false"}):
            with patch("services.rate_limit.get_remote_address", return_value="5.6.7.8"):
                key = _rate_limit_key(request)
        assert key == "5.6.7.8"


# ═══════════════════════════════════════════════════════════════════════════════
# 3. app/dependencies/auth.py
# ═══════════════════════════════════════════════════════════════════════════════

class TestLocalDummyUser:
    """_local_dummy_user(): 函数体 (lines 29-30)"""

    def test_returns_user_with_expected_fields(self):
        from app.dependencies.auth import _local_dummy_user
        user = _local_dummy_user()
        assert user.id == 0
        assert user.username == "local"
        assert user.email == "local@example.com"
        assert user.is_active is True
        assert user.is_admin is True
        assert user.role == "owner"
        assert user.password_hash == ""

    def test_returns_user_type(self):
        """确认返回值是 User 实例"""
        from app.dependencies.auth import _local_dummy_user
        from app.models import User
        user = _local_dummy_user()
        assert isinstance(user, User)


class TestGetCurrentUser:
    """get_current_user(): 各缺失分支"""

    def _make_request(self, auth_header: str | None) -> MagicMock:
        request = MagicMock()
        request.headers.get.return_value = auth_header
        return request

    def test_no_header_bypass_returns_dummy_user(self):
        """无 Authorization header + AUTH_BYPASS=true → 返回 dummy user  (line 61)"""
        from app.dependencies.auth import get_current_user
        request = self._make_request(None)
        session = MagicMock()
        with patch.dict(os.environ, {"AUTH_BYPASS": "true"}):
            user = get_current_user(request, session)
        assert user is not None
        assert user.id == 0
        assert user.username == "local"

    def test_no_header_no_bypass_returns_none(self):
        """无 Authorization header + AUTH_BYPASS=false → None"""
        from app.dependencies.auth import get_current_user
        request = self._make_request(None)
        session = MagicMock()
        with patch.dict(os.environ, {"AUTH_BYPASS": "false"}):
            user = get_current_user(request, session)
        assert user is None

    def test_malformed_header_no_space_returns_none(self):
        """'MalformedToken'（无空格）→ split() unpack ValueError → None  (lines 70-72)"""
        from app.dependencies.auth import get_current_user
        request = self._make_request("MalformedToken")
        session = MagicMock()
        with patch.dict(os.environ, {"AUTH_BYPASS": "false"}):
            user = get_current_user(request, session)
        assert user is None

    def test_malformed_header_too_many_parts_returns_none(self):
        """'Bearer tok extra'（三段）→ ValueError → None"""
        from app.dependencies.auth import get_current_user
        request = self._make_request("Bearer tok extra")
        session = MagicMock()
        with patch.dict(os.environ, {"AUTH_BYPASS": "false"}):
            user = get_current_user(request, session)
        assert user is None

    def test_non_bearer_scheme_returns_none(self):
        """'Basic xxx' → scheme != bearer → None"""
        from app.dependencies.auth import get_current_user
        request = self._make_request("Basic sometoken")
        session = MagicMock()
        with patch.dict(os.environ, {"AUTH_BYPASS": "false"}):
            user = get_current_user(request, session)
        assert user is None

    def test_invalid_token_returns_none(self):
        """Bearer 头 + verify_token 返回 None → None  (line 77)"""
        from app.dependencies.auth import get_current_user
        request = self._make_request("Bearer invalidjwttoken")
        session = MagicMock()
        with patch.dict(os.environ, {"AUTH_BYPASS": "false"}):
            with patch("app.dependencies.auth.verify_token", return_value=None):
                user = get_current_user(request, session)
        assert user is None

    def test_inactive_user_returns_none(self):
        """有效 token + DB 中用户 is_active=False → None  (line 88)"""
        from app.dependencies.auth import get_current_user
        request = self._make_request("Bearer valid.jwt.token")
        session = MagicMock()
        mock_payload = MagicMock()
        mock_payload.user_id = 1
        inactive_user = MagicMock()
        inactive_user.is_active = False
        session.exec.return_value.first.return_value = inactive_user
        with patch.dict(os.environ, {"AUTH_BYPASS": "false"}):
            with patch("app.dependencies.auth.verify_token", return_value=mock_payload):
                user = get_current_user(request, session)
        assert user is None

    def test_user_not_found_in_db_returns_none(self):
        """有效 token + DB 中无此用户（first()=None）→ None  (line 88)"""
        from app.dependencies.auth import get_current_user
        request = self._make_request("Bearer valid.jwt.token")
        session = MagicMock()
        mock_payload = MagicMock()
        mock_payload.user_id = 999
        session.exec.return_value.first.return_value = None
        with patch.dict(os.environ, {"AUTH_BYPASS": "false"}):
            with patch("app.dependencies.auth.verify_token", return_value=mock_payload):
                user = get_current_user(request, session)
        assert user is None


class TestRequireUser:
    """require_user(): AuthenticationException 分支  (line 111)"""

    def test_none_user_raises_authentication_exception(self):
        """user=None → 抛出 AuthenticationException  (line 111)"""
        from app.dependencies.auth import require_user
        from app.exceptions import AuthenticationException
        with pytest.raises(AuthenticationException) as exc_info:
            require_user(None)
        # 错误码应为 AUTH_MISSING_TOKEN
        from app.exceptions import ErrorCode
        assert exc_info.value.code == ErrorCode.AUTH_MISSING_TOKEN

    def test_valid_user_passes_through(self):
        """user 存在 → 直接返回 user"""
        from app.dependencies.auth import require_user
        from app.models import User
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)
        user = User(
            id=1,
            username="alice",
            email="alice@example.com",
            password_hash="x",
            is_active=True,
            role="user",
            is_admin=False,
            created_at=now,
            updated_at=now,
        )
        result = require_user(user)
        assert result is user
