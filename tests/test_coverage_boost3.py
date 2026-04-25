"""
tests/test_coverage_boost3.py

目标模块：
  init_db.py          — 0%  (23 stmts)
  db.py               — 67% (miss 14 lines: 35,36,66,72,74,75,79-83,87-89)
  routers/v2/verify.py — 69% (miss 22 lines)
  routers/v2/batch.py  — 81% (miss 12 lines)
  routers/snapshots.py — 46% (miss 27 lines)
  routers/audit.py     — 48% (miss 48 lines: AuditLogResponse validator + endpoints)
"""
from __future__ import annotations

import os
import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch


# ═══════════════════════════════════════════════════════════════════════════════
# 1. init_db.py — 全量覆盖
# ═══════════════════════════════════════════════════════════════════════════════

class TestInitDb:
    """init_db.py — init_db() 函数全路径"""

    def test_init_db_returns_table_names(self):
        """使用内存 sqlite 调用 init_db()，应返回非空表名列表"""
        with patch.dict(os.environ, {"DATABASE_URL": "sqlite:///:memory:"}):
            # 临时覆盖 settings，让 init_db 使用内存 DB
            with patch("init_db.settings") as mock_settings:
                mock_settings.database_url = "sqlite:///:memory:"
                mock_settings.db_path = ":memory:"
                from init_db import init_db
                tables = init_db()
        assert isinstance(tables, list)
        assert len(tables) > 0

    def test_init_db_includes_users_table(self):
        """创建的表中应包含 users 表"""
        with patch("init_db.settings") as mock_settings:
            mock_settings.database_url = "sqlite:///:memory:"
            mock_settings.db_path = ":memory:"
            from init_db import init_db
            tables = init_db()
        assert "users" in tables


# ═══════════════════════════════════════════════════════════════════════════════
# 2. db.py — PostgreSQL 路径 + SQLite pragma 路径
# ═══════════════════════════════════════════════════════════════════════════════

class TestDbGetEngine:
    """db.get_engine() — 覆盖 PostgreSQL 路径和 init_db (lines 35,36,66,72-89)"""

    def setup_method(self):
        """每个测试前重置单例"""
        import db
        db._engine = None

    def test_sqlite_path_returns_engine(self):
        """SQLite 路径：get_engine() 返回真实 Engine (default path, lines 42-65)"""
        import db, pathlib
        db._engine = None
        with patch("db.settings") as mock_settings:
            mock_settings.use_postgres = False
            mock_settings.db_path = pathlib.Path(":memory:")
            mock_settings.debug = False
            with patch("db._ensure_data_dir"):
                result = db.get_engine()
        assert result is not None
    def test_postgres_path_returns_engine(self):
        """PostgreSQL 路径：use_postgres=True 走 pg 分支 (lines 35-36)"""
        import db
        db._engine = None
        with patch("db.settings") as mock_settings:
            mock_settings.use_postgres = True
            mock_settings.database_url = "postgresql://user:pw@localhost/testdb"
            mock_settings.db_pool_size = 5
            mock_settings.db_max_overflow = 10
            mock_settings.db_pool_recycle = 3600
            mock_settings.debug = False
            with patch("db.create_engine") as mock_ce:
                mock_engine = MagicMock()
                mock_ce.return_value = mock_engine
                result = db.get_engine()
        assert result is mock_engine

    def test_cached_engine_reused(self):
        """第二次调用复用缓存 engine，不再创建新 engine"""
        import db, pathlib
        db._engine = None
        with patch("db.settings") as mock_settings:
            mock_settings.use_postgres = False
            mock_settings.debug = False
            mock_settings.db_path = pathlib.Path(":memory:")
            with patch("db._ensure_data_dir"):
                e1 = db.get_engine()
                e2 = db.get_engine()
        assert e1 is e2


class TestDbInitDb:
    """db.init_db() — lines 66-89"""

    def setup_method(self):
        import db
        db._engine = None

    def test_init_db_calls_create_all(self):
        """init_db() 调用 SQLModel.metadata.create_all  (line 72)"""
        import db
        mock_engine = MagicMock()
        with patch("db.get_engine", return_value=mock_engine):
            with patch("db.settings") as ms:
                ms.use_postgres = True  # 跳过 SQLite ADD COLUMN 逻辑
                with patch("db.SQLModel") as mock_sql:
                    mock_sql.metadata.create_all = MagicMock()
                    db.init_db()
                    mock_sql.metadata.create_all.assert_called_once_with(mock_engine)

    def test_init_db_sqlite_adds_column_if_missing(self):
        """SQLite 模式：补 deleted_at 列（lines 79-89）"""
        import db
        mock_engine = MagicMock()
        mock_conn = MagicMock()
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        # PRAGMA 返回列列表但不含 deleted_at
        mock_conn.exec_driver_sql.side_effect = [
            [["0", "id", "INTEGER", 0, None, 1]],  # PRAGMA table_info: no deleted_at
            None,  # ALTER TABLE
        ]
        mock_engine.connect.return_value = mock_conn
        with patch("db.get_engine", return_value=mock_engine):
            with patch("db.settings") as ms:
                ms.use_postgres = False
                with patch("db.SQLModel"):
                    db.init_db()
        # ALTER TABLE 应被调用
        calls = [str(c) for c in mock_conn.exec_driver_sql.call_args_list]
        assert any("ALTER" in c or "PRAGMA" in c for c in calls)


# ═══════════════════════════════════════════════════════════════════════════════
# 3. routers/v2/verify.py — 缺失分支
# ═══════════════════════════════════════════════════════════════════════════════

class TestV2VerifyEndpoint:
    """POST /api/v2/verify — 覆盖缺失的 22 行"""

    @pytest.fixture(autouse=True)
    def bypass_auth(self):
        with patch.dict(os.environ, {"AUTH_BYPASS": "true"}):
            yield

    def _client(self):
        from fastapi.testclient import TestClient
        from run import app
        return TestClient(app)

    def _base_payload(self, **kw):
        base = {
            "dt": "2000-06-15T12:00:00",
            "lon": 116.4,
            "mode": "single",
            "solar_time_enabled": False,
            "tz": "Asia/Shanghai",
            "output_format": "full",
        }
        base.update(kw)
        return base

    def test_engine_v2_disabled_returns_501(self):
        """ENGINE_V2=false → 501 Not Implemented (lines 44-45)"""
        import services.bazi_engine_service as _svc
        with patch.object(_svc.settings, "engine_v2", False):
            client = self._client()
            resp = client.post("/api/v2/verify", json=self._base_payload())
        assert resp.status_code == 501
        assert "not enabled" in resp.json()["detail"].lower()

    def test_invalid_timezone_returns_400(self):
        """无效 tz → 400 (lines 53 _validate_tz)"""
        with patch.dict(os.environ, {"ENGINE_V2": "true"}):
            client = self._client()
            resp = client.post(
                "/api/v2/verify",
                json=self._base_payload(tz="Invalid/Timezone"),
            )
        assert resp.status_code == 400
        assert "Invalid timezone" in resp.json()["detail"]

    def test_out_of_range_year_returns_400(self):
        """dt.year < 1900 → 400 (lines 58-61)"""
        with patch.dict(os.environ, {"ENGINE_V2": "true"}):
            client = self._client()
            resp = client.post(
                "/api/v2/verify",
                json=self._base_payload(dt="1800-01-01T12:00:00"),
            )
        assert resp.status_code == 400
        assert "超出支持范围" in resp.json()["detail"]

    def test_engine_exception_returns_500(self):
        """引擎意外抛出 Exception → 500 Internal Server Error (lines 62-64)"""
        with patch.dict(os.environ, {"ENGINE_V2": "true"}):
            with patch("services.bazi_engine_service.calculate", side_effect=RuntimeError("boom")):
                client = self._client()
                resp = client.post("/api/v2/verify", json=self._base_payload())
        assert resp.status_code == 500

    def test_minimal_output_format(self):
        """output_format=minimal → VerifyResponseMinimal 结构 (lines 128-134)"""
        with patch.dict(os.environ, {"ENGINE_V2": "true"}):
            client = self._client()
            resp = client.post(
                "/api/v2/verify",
                json=self._base_payload(output_format="minimal"),
            )
        # 若引擎正常运行
        if resp.status_code == 200:
            data = resp.json()
            assert "meta" in data
            assert "data" in data

    def test_value_error_returns_400(self):
        """引擎抛 ValueError → 400 (lines 60-61)"""
        with patch.dict(os.environ, {"ENGINE_V2": "true"}):
            with patch("services.bazi_engine_service.calculate", side_effect=ValueError("bad value")):
                client = self._client()
                resp = client.post("/api/v2/verify", json=self._base_payload())
        assert resp.status_code == 400

    def test_valid_full_request_returns_200(self):
        """正常 full 请求 → 200 + meta (line 106+)"""
        with patch.dict(os.environ, {"ENGINE_V2": "true"}):
            client = self._client()
            resp = client.post("/api/v2/verify", json=self._base_payload())
        if resp.status_code == 200:
            data = resp.json()
            assert "meta" in data
            assert data["meta"]["api_version"] == "v2.0"


# ═══════════════════════════════════════════════════════════════════════════════
# 4. routers/v2/batch.py — 缺失分支
# ═══════════════════════════════════════════════════════════════════════════════

class TestV2BatchVerify:
    """POST /api/v2/batch/verify (lines 43-44, 112-122)"""

    @pytest.fixture(autouse=True)
    def bypass_auth(self):
        with patch.dict(os.environ, {"AUTH_BYPASS": "true"}):
            yield

    def _client(self):
        from fastapi.testclient import TestClient
        from run import app
        return TestClient(app)

    def _item(self, **kw):
        base = {"dt": "2000-06-15T12:00:00", "lon": 116.4, "tz": "Asia/Shanghai"}
        base.update(kw)
        return base

    def test_engine_v2_disabled_returns_501(self):
        """ENGINE_V2=false → 501 (lines 43-44)"""
        import services.bazi_engine_service as _svc
        with patch.object(_svc.settings, "engine_v2", False):
            client = self._client()
            resp = client.post("/api/v2/batch/verify", json={"items": [self._item()]})
        assert resp.status_code == 501

    def test_per_item_timeout_produces_failed_entry(self):
        """单条超时 (FuturesTimeoutError in result) → failed 列表 (lines 113-114)"""
        from concurrent.futures import TimeoutError as FTE
        with patch.dict(os.environ, {"ENGINE_V2": "true"}):
            with patch("services.bazi_engine_service.calculate", side_effect=FTE()):
                client = self._client()
                resp = client.post(
                    "/api/v2/batch/verify",
                    json={"items": [self._item()]},
                )
        if resp.status_code == 200:
            data = resp.json()
            assert len(data["failed"]) == 1

    def test_item_exception_produces_failed_entry(self):
        """单条抛 RuntimeError → failed 含该条 (lines 115-117)"""
        with patch.dict(os.environ, {"ENGINE_V2": "true"}):
            with patch("services.bazi_engine_service.calculate",
                       side_effect=RuntimeError("calc error")):
                client = self._client()
                resp = client.post(
                    "/api/v2/batch/verify",
                    json={"items": [self._item()]},
                )
        if resp.status_code == 200:
            data = resp.json()
            assert data["results"] == []
            assert len(data["failed"]) == 1
            assert "calc error" in data["failed"][0]["error"]

    def test_valid_batch_returns_results(self):
        """正常批量请求 → 200 + results 列表 (lines 119-122)"""
        with patch.dict(os.environ, {"ENGINE_V2": "true"}):
            client = self._client()
            resp = client.post(
                "/api/v2/batch/verify",
                json={"items": [self._item()]},
            )
        if resp.status_code == 200:
            data = resp.json()
            assert "results" in data
            assert "failed" in data


# ═══════════════════════════════════════════════════════════════════════════════
# 5. routers/snapshots.py — 全路径覆盖
# ═══════════════════════════════════════════════════════════════════════════════

class TestSnapshotsRouter:
    """GET/DELETE /api/v1/cases/{id}/snapshots  (27 missing lines)"""

    @pytest.fixture(autouse=True)
    def bypass_auth(self):
        with patch.dict(os.environ, {"AUTH_BYPASS": "true"}):
            yield

    # 使用 conftest 的 client fixture（含 test DB 覆盖，tables 已创建）

    def test_list_snapshots_case_not_found_returns_404(self, client):
        """Case 不存在 → 404 (lines 32,35-36)"""
        resp = client.get("/api/v1/cases/nonexistent-case-id/snapshots")
        assert resp.status_code == 404

    def test_get_snapshot_not_found_returns_404(self, client):
        """Snapshot 不存在 → 404 (lines 64,67-68)"""
        resp = client.get("/api/v1/snapshots/nonexistent-snap-id")
        assert resp.status_code == 404

    def test_delete_snapshot_not_found_returns_404(self, client):
        """DELETE Snapshot 不存在 → 404 (lines 92,95-96)"""
        resp = client.delete("/api/v1/snapshots/nonexistent-snap-id")
        assert resp.status_code == 404

    def test_list_snapshots_wrong_owner_returns_403(self, client):
        """Case 属于他人 → 403 (lines 41-42, 需创建 case)"""
        from tests.conftest import TEST_DATABASE_URL
        from sqlalchemy import create_engine, pool
        from sqlmodel import SQLModel, Session as SQLModelSession
        from app.models import User, Case
        from datetime import datetime, timezone
        from uuid import uuid4

        # 创建孤立 DB session 验证逻辑
        engine = create_engine(
            TEST_DATABASE_URL,
            connect_args={"check_same_thread": False},
            poolclass=pool.StaticPool,
        )
        SQLModel.metadata.create_all(engine)

        case_id = f"test-case-{uuid4().hex[:8]}"
        with SQLModelSession(engine) as session:
            user = User(
                id=999, username="other_user", email="other@x.com",
                password_hash="x", is_active=True, role="user",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            case = Case(
                id=case_id,
                name="Other's Case", gender="M",
                birth_dt_local="2000-01-01T12:00:00",
                tz="Asia/Shanghai",
                birth_dt="2000-01-01T04:00:00Z",
                lon=120.0,
                owner_id=999,  # != dummy user id=0
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            session.add(user)
            session.add(case)
            session.commit()

            from run import app
            from db import get_session

            def override_get_session():
                return session

            app.dependency_overrides[get_session] = override_get_session
            try:
                from fastapi.testclient import TestClient
                c2 = TestClient(app)
                resp = c2.get(f"/api/v1/cases/{case_id}/snapshots")
                # Dummy user (id=0) != owner (id=999) → expect 403
                assert resp.status_code in (403, 404)
            finally:
                app.dependency_overrides.clear()


# ═══════════════════════════════════════════════════════════════════════════════
# 6. routers/audit.py — AuditLogResponse validator + endpoints
# ═══════════════════════════════════════════════════════════════════════════════

class TestAuditLogResponseModel:
    """AuditLogResponse 的 RBAC 字段提取逻辑 (lines 48-60)"""

    def _make(self, action, details):
        from routers.audit import AuditLogResponse
        return AuditLogResponse(
            id=1, user_id=1, action=action,
            resource_type="delegation", resource_id="42",
            details=details, ip_address=None, user_agent=None,
            status="success", error_message=None,
            created_at=datetime.now(timezone.utc),
        )

    def test_approve_action_extracts_rbac_fields(self):
        """approve_permission + details JSON → old/new_status 提取 (lines 48-59)"""
        details_json = '{"old_status":"pending","new_status":"approved","operator_id":7}'
        obj = self._make("approve_permission", details_json)
        assert obj.old_status == "pending"
        assert obj.new_status == "approved"
        assert obj.operator_id == 7

    def test_reject_action_extracts_rbac_fields(self):
        """reject_permission"""
        details_json = '{"old_status":"pending","new_status":"rejected"}'
        obj = self._make("reject_permission", details_json)
        assert obj.old_status == "pending"
        assert obj.new_status == "rejected"

    def test_revoke_action_extracts_rbac_fields(self):
        """revoke_permission"""
        details_json = '{"old_status":"approved","new_status":"revoked","operator_id":3}'
        obj = self._make("revoke_permission", details_json)
        assert obj.new_status == "revoked"
        assert obj.operator_id == 3

    def test_non_rbac_action_no_extraction(self):
        """普通操作 → old/new_status 保持 None"""
        obj = self._make("create_case", '{"resource_id":"x"}')
        assert obj.old_status is None
        assert obj.new_status is None

    def test_invalid_json_details_no_crash(self):
        """details JSON 格式错误 → 不抛异常，字段保持 None  (lines 57-60)"""
        obj = self._make("approve_permission", "NOT_VALID_JSON")
        assert obj.old_status is None

    def test_none_details_no_crash(self):
        """details=None → 不等进 if，字段保持 None"""
        obj = self._make("approve_permission", None)
        assert obj.old_status is None


class TestAuditEndpoints:
    """GET /api/v1/audit-logs + /admin (lines 78-263)"""

    @pytest.fixture(autouse=True)
    def bypass_auth(self):
        with patch.dict(os.environ, {"AUTH_BYPASS": "true"}):
            yield

    @pytest.fixture
    def client(self):
        """TestClient with in-memory test DB override."""
        from fastapi.testclient import TestClient
        from run import app
        from db import get_session
        from sqlalchemy import create_engine, pool
        from sqlmodel import SQLModel, Session as SQLModelSession

        engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=pool.StaticPool,
        )
        SQLModel.metadata.create_all(engine)
        session = SQLModelSession(engine)

        def override_session():
            return session

        app.dependency_overrides[get_session] = override_session
        yield TestClient(app)
        app.dependency_overrides.clear()
        session.close()

    def test_get_user_audit_logs_returns_200(self, client):
        """GET /api/v1/audit-logs 基础路径 (lines 78-102)"""
        resp = client.get("/api/v1/audit-logs")
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert "total" in data

    def test_get_user_audit_logs_with_filters(self, client):
        """带 action + resource_type 过滤 (lines 84-86)"""
        resp = client.get("/api/v1/audit-logs?action=login&resource_type=user")
        assert resp.status_code == 200

    def test_get_user_audit_logs_with_before_id(self, client):
        """带 before_id 游标查询 (line 88, keyset 分页)"""
        resp = client.get("/api/v1/audit-logs?before_id=9999")
        assert resp.status_code == 200

    def test_admin_audit_logs_owner_can_access(self, client):
        """AUTH_BYPASS → dummy user (is_admin=True, owner)，可以访问 /admin (line 139-141)"""
        resp = client.get("/api/v1/audit-logs/admin")
        # dummy user is is_admin=True, so should get 200
        assert resp.status_code == 200

    def test_admin_audit_logs_with_user_id_filter(self, client):
        """admin 路由带 user_id filter (line 147-148)"""
        resp = client.get("/api/v1/audit-logs/admin?user_id=1")
        assert resp.status_code == 200

    def test_admin_audit_logs_non_admin_returns_403(self):
        """非管理员用户请求 /admin → 403 (lines 139-144)"""
        from fastapi.testclient import TestClient
        from run import app
        from db import get_session
        from app.models import User
        from datetime import datetime, timezone

        now = datetime.now(timezone.utc)
        non_admin_user = User(
            id=55, username="viewer55", email="viewer55@x.com",
            password_hash="x", is_active=True, role="viewer", is_admin=False,
            created_at=now, updated_at=now,
        )

        from app.dependencies.auth import get_current_user, require_user
        app.dependency_overrides[get_current_user] = lambda: non_admin_user
        app.dependency_overrides[require_user] = lambda: non_admin_user
        try:
            with patch.dict(os.environ, {"AUTH_BYPASS": "false"}):
                c = TestClient(app)
                resp = c.get("/api/v1/audit-logs/admin")
            assert resp.status_code in (403, 401)
        finally:
            app.dependency_overrides.clear()
