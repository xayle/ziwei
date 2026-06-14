"""
tests/test_coverage_boost2.py

目标文件和缺失行：
  routers/bazi.py             miss=[21-30, 44]
  services/permission_service.py miss=[137,138,142,155,156,157]
  services/auth_service.py    miss=[52,53,55,58-64, 73-81, 233, 343,344]
  app/dependencies/permissions.py miss=[41,44,45,61,70,95,97,101,102,
                                  107-119,125,135,136,138,139,144]
"""
from __future__ import annotations

import os
import time as _time
import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch


# ═══════════════════════════════════════════════════════════════════════════════
# 1. routers/bazi.py — _sanitize_request_id (lines 21-30) + route warning (44)
# ═══════════════════════════════════════════════════════════════════════════════

class TestSanitizeRequestId:
    """_sanitize_request_id 的全部分支（lines 21-30）"""

    @pytest.fixture(autouse=True)
    def _import(self):
        from routers.bazi import _sanitize_request_id
        from app.schemas import WarningModel
        self._fn = _sanitize_request_id
        self._WM = WarningModel

    def _call(self, candidate, warnings=None):
        if warnings is None:
            warnings = []
        return self._fn(candidate, warnings), warnings

    # None → early return (line 19-20, already covered; regression guard)
    def test_none_returns_uuid_no_warnings(self):
        result, warns = self._call(None)
        assert len(result) == 36
        assert warns == []

    # empty string after strip → uuid (lines 21-23)
    def test_empty_string_returns_uuid(self):
        result, warns = self._call("")
        assert len(result) == 36
        assert warns == []

    def test_whitespace_only_returns_uuid(self):
        result, warns = self._call("   ")
        assert len(result) == 36
        assert warns == []

    # invalid chars (lines 24-26)
    def test_invalid_chars_returns_uuid_and_warning(self):
        result, warns = self._call("req@invalid!")
        assert len(result) == 36
        assert any(w.code == "request_id_invalid_chars" for w in warns)

    def test_special_chars_trigger_warning(self):
        result, warns = self._call("abc<script>")
        assert len(result) == 36
        assert any(w.code == "request_id_invalid_chars" for w in warns)

    # too long (lines 27-30)
    def test_long_id_truncated_to_128(self):
        long_id = "a" * 200
        result, warns = self._call(long_id)
        assert len(result) == 128
        assert any(w.code == "request_id_truncated" for w in warns)

    def test_exactly_128_chars_no_warning(self):
        ok_id = "x" * 128
        result, warns = self._call(ok_id)
        assert result == ok_id
        assert warns == []

    def test_valid_id_returned_unchanged(self):
        result, warns = self._call("req-abc.123_XYZ")
        assert result == "req-abc.123_XYZ"
        assert warns == []


class TestBaziRouteWarnings:
    """/api/v1/bazi/full — result.warnings.extend(warnings) (line 44)

    当 X-Request-Id 包含非法字符时，handler 将 warning 写入响应。
    """

    def test_invalid_request_id_header_produces_warning_in_response(self):
        """X-Request-Id 含非法字符 → handler 将 request_id_invalid_chars 写入 warnings (line 44)"""
        from fastapi.testclient import TestClient
        from run import app

        payload = {
            "dt": "2000-06-15T12:00:00",
            "lon": 116.4,
            "mode": "single",
            "solar_time_enabled": False,
            "tz": "Asia/Shanghai",
        }
        with patch.dict(os.environ, {"AUTH_BYPASS": "true"}):
            client = TestClient(app)
            resp = client.post(
                "/api/v1/bazi/full",
                json=payload,
                headers={"X-Request-Id": "req@invalid!"},
            )
        assert resp.status_code == 200
        data = resp.json()
        warnings = data.get("warnings", [])
        codes = [w.get("code") for w in warnings]
        assert "request_id_invalid_chars" in codes


# ═══════════════════════════════════════════════════════════════════════════════
# 2. services/permission_service.py — check_member_access + get_user_role
# ═══════════════════════════════════════════════════════════════════════════════

class TestCheckMemberAccess:
    """check_member_access (lines 137,138,142)"""

    def test_owner_with_read_permission_allowed(self):
        """user_id == member_owner_id + has read perm → True  (lines 137-138)"""
        from services.permission_service import check_member_access, Permission, Role
        result = check_member_access(
            user_id=1, member_owner_id=1,
            required_permission=Permission.READ_MEMBER,
            user_role=Role.OWNER,
        )
        assert result is True

    def test_owner_delete_as_viewer_denied(self):
        """user_id == member_owner_id but VIEWER can't DELETE  (lines 137-138)"""
        from services.permission_service import check_member_access, Permission, Role
        result = check_member_access(
            user_id=1, member_owner_id=1,
            required_permission=Permission.DELETE_MEMBER,
            user_role=Role.VIEWER,
        )
        assert result is False

    def test_non_owner_returns_false(self):
        """user_id != member_owner_id → return False  (line 142)"""
        from services.permission_service import check_member_access, Permission, Role
        result = check_member_access(
            user_id=2, member_owner_id=1,
            required_permission=Permission.READ_MEMBER,
            user_role=Role.OWNER,
        )
        assert result is False


class TestGetUserRole:
    """get_user_role (lines 155-157)"""

    def test_admin_returns_owner(self):
        """is_admin=True → Role.OWNER  (line 155-156)"""
        from services.permission_service import get_user_role, Role
        assert get_user_role(is_admin=True) == Role.OWNER

    def test_non_admin_returns_editor(self):
        """is_admin=False → Role.EDITOR  (line 157)"""
        from services.permission_service import get_user_role, Role
        assert get_user_role(is_admin=False) == Role.EDITOR

    def test_default_non_admin(self):
        """默认 is_admin=False"""
        from services.permission_service import get_user_role, Role
        assert get_user_role() == Role.EDITOR


# ═══════════════════════════════════════════════════════════════════════════════
# 3. services/auth_service.py — session 路径 + load_revoked_jtis
# ═══════════════════════════════════════════════════════════════════════════════

class TestRevokeAccessTokenJti:
    """revoke_access_token_jti(jti, session=...) — lines 52-64"""

    def _make_session(self, existing=None):
        session = MagicMock()
        session.exec.return_value.first.return_value = existing
        return session

    def test_new_jti_added_to_db(self):
        """JTI 不在 DB → add + commit  (lines 52-64)"""
        from services.auth_service import revoke_access_token_jti
        jti = "test-jti-new-session"
        session = self._make_session(existing=None)  # not in DB
        revoke_access_token_jti(jti, session=session)
        session.add.assert_called_once()
        session.commit.assert_called_once()

    def test_existing_jti_skips_insert(self):
        """JTI 已在 DB → 跳过 add/commit  (lines 57 branch)"""
        from services.auth_service import revoke_access_token_jti
        jti = "test-jti-already-exists"
        existing_stub = MagicMock()  # non-None = already in DB
        session = self._make_session(existing=existing_stub)
        revoke_access_token_jti(jti, session=session)
        session.add.assert_not_called()
        session.commit.assert_not_called()

    def test_commit_exception_rolls_back(self):
        """commit 抛异常 → rollback  (lines 62-64)"""
        from services.auth_service import revoke_access_token_jti
        jti = "test-jti-commit-fail"
        session = self._make_session(existing=None)
        session.commit.side_effect = Exception("DB error")
        revoke_access_token_jti(jti, session=session)
        session.rollback.assert_called_once()

    def test_jti_added_to_memory_set_regardless(self):
        """无论 session 成功还是失败，内存集合始终更新"""
        from services import auth_service as _as
        jti = f"mem-only-{id(self)}"
        session = self._make_session(existing=None)
        _as.revoke_access_token_jti(jti, session=session)
        assert jti in _as._revoked_jtis


class TestLoadRevokedJtis:
    """load_revoked_jtis_from_db(session) — lines 73-81"""

    def _make_row(self, jti_value: str):
        row = MagicMock()
        row.jti = jti_value
        return row

    def test_loads_rows_into_memory(self):
        """DB 返回两行 → 两个 JTI 加入内存集合  (lines 73-81)"""
        from services import auth_service as _as
        rows = [self._make_row("jti-A"), self._make_row("jti-B")]
        session = MagicMock()
        session.exec.return_value.all.return_value = rows
        count = _as.load_revoked_jtis_from_db(session)
        assert count == 2
        assert "jti-A" in _as._revoked_jtis
        assert "jti-B" in _as._revoked_jtis

    def test_empty_db_returns_zero(self):
        """DB 无记录 → 返回 0  (lines 73-81)"""
        from services import auth_service as _as
        session = MagicMock()
        session.exec.return_value.all.return_value = []
        count = _as.load_revoked_jtis_from_db(session)
        assert count == 0

    def test_idempotent_reload(self):
        """多次 load 不会出错（集合 add 是幂等的）"""
        from services import auth_service as _as
        jti = "reload-jti"
        session = MagicMock()
        session.exec.return_value.all.return_value = [self._make_row(jti)]
        _as.load_revoked_jtis_from_db(session)
        _as.load_revoked_jtis_from_db(session)
        assert jti in _as._revoked_jtis


# ═══════════════════════════════════════════════════════════════════════════════
# 4. app/dependencies/permissions.py — PermissionCache 过期路径 + _check 函数
# ═══════════════════════════════════════════════════════════════════════════════

class TestPermissionCacheExpired:
    """PermissionCache.get() 过期条目删除 (lines ~41,44,45)"""

    def test_expired_entry_returns_none(self):
        """TTL 极短 → get() 应返回 None 并删除该条目  (lines 41,44,45)"""
        from app.dependencies.permissions import PermissionCache
        cache = PermissionCache(ttl=0)  # 0s TTL → 立即过期
        cache.set("k1", "v1")
        # 等待一微小间隔确保 monotonic 时间推进
        _time.sleep(0.01)
        result = cache.get("k1")
        assert result is None
        assert "k1" not in cache._cache  # 应被删除

    def test_valid_entry_returned(self):
        """TTL 足够长 → 正常返回"""
        from app.dependencies.permissions import PermissionCache
        cache = PermissionCache(ttl=300)
        cache.set("k2", True)
        assert cache.get("k2") is True

    def test_nonexistent_key_returns_none(self):
        from app.dependencies.permissions import PermissionCache
        cache = PermissionCache(ttl=300)
        assert cache.get("nonexistent") is None


class TestInvalidateUser:
    """PermissionCache.invalidate_user() — 前缀匹配删除 (line ~61)"""

    def test_invalidate_user_removes_matching_keys(self):
        from app.dependencies.permissions import PermissionCache
        cache = PermissionCache(ttl=300)
        cache.set("perm:5:read_case", True)
        cache.set("perm:5:write_case", True)
        cache.set("perm:7:read_case", True)   # 不同用户
        cache.invalidate_user(5)
        assert cache.get("perm:5:read_case") is None
        assert cache.get("perm:5:write_case") is None
        # 其他用户不受影响
        assert cache.get("perm:7:read_case") is True

    def test_invalidate_user_no_entries_is_noop(self):
        from app.dependencies.permissions import PermissionCache
        cache = PermissionCache(ttl=300)
        # 不应抛异常
        cache.invalidate_user(999)


class TestRequireResourcePermissionCheck:
    """require_resource_permission() 返回的 _check 函数 — 24 missing lines"""

    def _make_check_fn(self, resource="case", action="read"):
        from app.dependencies.permissions import require_resource_permission
        # 清理全局 cache，避免测试间干扰
        from app.dependencies.permissions import _permission_cache
        _permission_cache._cache.clear()
        return require_resource_permission(resource, action), _permission_cache

    def test_none_user_raises_authorization_exception(self):
        """current_user=None → AuthorizationException (lines ~95)"""
        from app.exceptions import AuthorizationException
        check_fn, _ = self._make_check_fn()
        with pytest.raises(AuthorizationException):
            check_fn(current_user=None, session=MagicMock())

    def test_admin_user_returns_immediately(self):
        """is_admin=True → 直接放行，不查 DB (line ~99)"""
        check_fn, _ = self._make_check_fn()
        mock_user = MagicMock()
        mock_user.is_admin = True
        mock_user.id = 1
        session = MagicMock()
        result = check_fn(current_user=mock_user, session=session)
        assert result is None  # 无异常 = 已放行
        session.exec.assert_not_called()

    def test_cached_true_returns_immediately(self):
        """cache=True → 放行，不查 DB (lines ~101-102)"""
        check_fn, perm_cache = self._make_check_fn()
        mock_user = MagicMock()
        mock_user.is_admin = False
        mock_user.id = 10
        perm_cache.set("perm:10:read_case", True)
        session = MagicMock()
        result = check_fn(current_user=mock_user, session=session)
        assert result is None
        session.exec.assert_not_called()

    def test_cached_false_raises(self):
        """cache=False → 立即抛 AuthorizationException (line ~97)"""
        from app.exceptions import AuthorizationException
        check_fn, perm_cache = self._make_check_fn()
        mock_user = MagicMock()
        mock_user.is_admin = False
        mock_user.id = 11
        perm_cache.set("perm:11:read_case", False)
        with pytest.raises(AuthorizationException):
            check_fn(current_user=mock_user, session=MagicMock())

    def test_db_delegation_found_allows(self):
        """DB 中找到 Delegation → 缓存 True + 放行 (lines ~107-125)"""
        from app.models.other import Delegation
        check_fn, perm_cache = self._make_check_fn()
        mock_user = MagicMock()
        mock_user.is_admin = False
        mock_user.id = 20
        session = MagicMock()
        mock_delegation = MagicMock(spec=Delegation)
        session.exec.return_value.first.return_value = mock_delegation  # 找到权限
        result = check_fn(current_user=mock_user, session=session)
        assert result is None
        assert perm_cache.get("perm:20:read_case") is True

    def test_db_no_delegation_raises(self):
        """DB 中未找到 Delegation → 缓存 False + 抛 AuthorizationException (lines ~135-144)"""
        from app.exceptions import AuthorizationException
        check_fn, perm_cache = self._make_check_fn()
        mock_user = MagicMock()
        mock_user.is_admin = False
        mock_user.id = 21
        session = MagicMock()
        session.exec.return_value.first.return_value = None  # 无权限
        with pytest.raises(AuthorizationException):
            check_fn(current_user=mock_user, session=session)
        assert perm_cache.get("perm:21:read_case") is False

    def test_user_id_none_uses_zero(self):
        """user.id=None → user_id=0 (line ~101)"""
        from app.exceptions import AuthorizationException
        check_fn, _ = self._make_check_fn()
        mock_user = MagicMock()
        mock_user.is_admin = False
        mock_user.id = None   # id=None → user_id=0
        session = MagicMock()
        session.exec.return_value.first.return_value = None
        with pytest.raises(AuthorizationException):
            check_fn(current_user=mock_user, session=session)
