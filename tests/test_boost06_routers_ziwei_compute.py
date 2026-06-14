"""
Coverage Boost #6 — routers/ziwei.py, routers/compute.py,
                     routers/snapshots.py, routers/relations.py

目标：覆盖四个路由文件的缺失分支，预计将整体覆盖率从 92.9% 推向 94%+。
"""
import pytest
from datetime import datetime, timezone
from uuid import uuid4
from unittest.mock import patch

from sqlmodel import Session as SQLModelSession
from fastapi.testclient import TestClient


# ===========================================================================
# TestZiweiRouterCoverage
# ===========================================================================
class TestZiweiRouterCoverage:
    """routers/ziwei.py — 覆盖 demo + full 端点（lines 34-221）。
    ziwei 端点无需认证。"""

    @pytest.fixture
    def plain_client(self, app_with_test_db) -> TestClient:
        return TestClient(app_with_test_db)

    # -----------------------------------------------------------------------
    def test_ziwei_demo_returns_200(self, plain_client: TestClient):
        """GET /api/v1/ziwei/demo → 200，覆盖 _chart_to_response 全路径"""
        resp = plain_client.get("/api/v1/ziwei/demo")
        assert resp.status_code == 200
        data = resp.json()
        assert "lunar" in data
        assert "palaces" in data
        assert "dayun" in data

    def test_ziwei_full_valid_returns_200(self, plain_client: TestClient):
        """POST /api/v1/ziwei/full 合法请求 → 200"""
        resp = plain_client.post("/api/v1/ziwei/full", json={
            "year": 1990,
            "month": 6,
            "day": 15,
            "hour": 10,
            "minute": 30,
            "gender": "男",
            "liunian_year": 2024,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "lunar" in data
        assert "palaces" in data

    def test_ziwei_full_engine_exception_returns_400(self, plain_client: TestClient):
        """ziwei_full 抛出异常 → compute_ziwei 返回 400（lines 193-194）"""
        with patch("routers.ziwei.ziwei_full", side_effect=ValueError("engine error")):
            resp = plain_client.post("/api/v1/ziwei/full", json={
                "year": 1990, "month": 6, "day": 15,
                "hour": 10, "minute": 30, "gender": "男",
            })
        assert resp.status_code == 400
        assert "engine error" in resp.json()["detail"]

    def test_ziwei_demo_engine_exception_returns_500(self, plain_client: TestClient):
        """ziwei_full 抛出异常 → demo_ziwei 返回 500（lines 204-207）"""
        with patch("routers.ziwei.ziwei_full", side_effect=RuntimeError("demo err")):
            resp = plain_client.get("/api/v1/ziwei/demo")
        assert resp.status_code == 500
        assert "demo err" in resp.json()["detail"]


# ===========================================================================
# TestComputeRouterCoverage
# ===========================================================================
class TestComputeRouterCoverage:
    """routers/compute.py — 覆盖 helper 函数 + compute_case 端点
    缺失 lines: _parse_dt_local (43,49-50,55,61-62),
                _build_warning_objects (75,76,78),
                compute_case route (319,322-323,329,335-336,344),
                _do_compute_for_case error branches (181-202, 273-300)
    """

    # ── 通用辅助 ───────────────────────────────────────────────────────────
    def _auth_headers(self, user):
        from services.auth_service import create_access_token
        td = create_access_token(
            user_id=user.id, username=user.username, role=user.role
        )
        return {"Authorization": f"Bearer {td['access_token']}"}

    # ── fixtures ───────────────────────────────────────────────────────────
    @pytest.fixture
    def owned_case(self, db_session: SQLModelSession, test_user):
        from app.models import Case
        case = Case(
            id=str(uuid4()),
            owner_id=test_user.id,
            name="Compute Test Case",
            birth_dt_local="1990-01-15T10:00:00",
            tz="Asia/Shanghai",
            lon=121.5,
        )
        db_session.add(case)
        db_session.commit()
        db_session.refresh(case)
        return case

    @pytest.fixture
    def other_case(self, db_session: SQLModelSession):
        from app.models import Case, User
        other = User(
            username=f"cmp_other_{uuid4().hex[:6]}",
            email=f"cmp_{uuid4().hex[:6]}@x.com",
            password_hash="x", role="viewer",
            is_active=True, is_admin=False,
        )
        db_session.add(other)
        db_session.flush()
        case = Case(
            id=str(uuid4()),
            owner_id=other.id,
            name="Other Compute Case",
            birth_dt_local="1990-01-15T10:00:00",
            tz="Asia/Shanghai",
            lon=121.5,
        )
        db_session.add(case)
        db_session.commit()
        db_session.refresh(case)
        return case

    # ── _parse_dt_local 单元测试 ───────────────────────────────────────────
    def test_parse_dt_local_invalid_format_raises(self):
        """非法日期格式 → ValidationException（lines 43-44）"""
        from routers.compute import _parse_dt_local
        from app.exceptions import ValidationException
        with pytest.raises(ValidationException):
            _parse_dt_local("not-a-date", "Asia/Shanghai")

    def test_parse_dt_local_aware_datetime_raises(self):
        """带时区偏移的 ISO8601 → ValidationException（lines 49-50）"""
        from routers.compute import _parse_dt_local
        from app.exceptions import ValidationException
        with pytest.raises(ValidationException):
            _parse_dt_local("1990-01-15T10:00:00+08:00", "Asia/Shanghai")

    def test_parse_dt_local_invalid_timezone_raises(self):
        """非法时区名称 → ValidationException（lines 55, 61-62）"""
        from routers.compute import _parse_dt_local
        from app.exceptions import ValidationException
        with pytest.raises(ValidationException):
            _parse_dt_local("1990-01-15T10:00:00", "Not/A/Timezone")

    # ── _build_warning_objects 单元测试 ────────────────────────────────────
    def test_build_warning_objects_dict_input(self):
        """dict 类型的 warning → WarningModel.model_validate（lines 75-76）"""
        from routers.compute import _build_warning_objects
        result = _build_warning_objects([{"code": "W001", "message": "test warn"}])
        assert len(result) == 1
        assert result[0].code == "W001"

    def test_build_warning_objects_str_input(self):
        """str 类型的 warning → legacy WarningModel（line 78）"""
        from routers.compute import _build_warning_objects
        result = _build_warning_objects(["legacy warning text"])
        assert len(result) == 1
        assert result[0].code == "legacy"
        assert result[0].message == "legacy warning text"

    # ── compute_case 端点测试 ──────────────────────────────────────────────
    def test_compute_case_not_found_returns_404(
        self, client: TestClient, test_user
    ):
        """Case 不存在 → 404（lines 322-323）"""
        headers = self._auth_headers(test_user)
        resp = client.post(
            f"/api/v1/cases/nonexistent-{uuid4().hex}/compute",
            json={},
            headers=headers,
        )
        assert resp.status_code == 404

    def test_compute_case_wrong_owner_returns_403(
        self, client: TestClient, test_user, other_case
    ):
        """Case 属于他人 → 403（lines 329-330, 335-336）"""
        headers = self._auth_headers(test_user)
        resp = client.post(
            f"/api/v1/cases/{other_case.id}/compute",
            json={},
            headers=headers,
        )
        assert resp.status_code == 403

    def test_compute_case_success(
        self, client: TestClient, test_user, owned_case
    ):
        """正常计算 → 200，包含 compute_batch_id 和 snapshots（line 344 log_action）"""
        headers = self._auth_headers(test_user)
        resp = client.post(
            f"/api/v1/cases/{owned_case.id}/compute",
            json={"mode": "dual"},
            headers=headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "compute_batch_id" in data
        assert "tasks" in data

    def test_compute_case_bazi_app_exception(
        self, client: TestClient, test_user, owned_case
    ):
        """bazi_full 抛 AppException → 200 但 bazi 任务失败（lines 181-196）"""
        from app.exceptions import ValidationException, ErrorCode
        headers = self._auth_headers(test_user)
        exc = ValidationException(
            code=ErrorCode.VALIDATION_INVALID_INPUT,
            message="forced bazi fail",
        )
        with patch("routers.compute.bazi_full", side_effect=exc):
            resp = client.post(
                f"/api/v1/cases/{owned_case.id}/compute",
                json={},
                headers=headers,
            )
        assert resp.status_code == 200
        assert resp.json()["tasks"]["bazi"]["status"] == "failed"

    def test_compute_case_bazi_generic_exception(
        self, client: TestClient, test_user, owned_case
    ):
        """bazi_full 抛通用 Exception → 200 但 bazi 任务失败（lines 193-202）"""
        headers = self._auth_headers(test_user)
        with patch("routers.compute.bazi_full", side_effect=RuntimeError("engine crash")):
            resp = client.post(
                f"/api/v1/cases/{owned_case.id}/compute",
                json={},
                headers=headers,
            )
        assert resp.status_code == 200
        assert resp.json()["tasks"]["bazi"]["status"] == "failed"

    def test_compute_case_verify_app_exception(
        self, client: TestClient, test_user, owned_case
    ):
        """verify_full 抛 AppException → 200 但 verify 任务失败（lines 273-280）"""
        from app.exceptions import ValidationException, ErrorCode
        headers = self._auth_headers(test_user)
        exc = ValidationException(
            code=ErrorCode.VALIDATION_INVALID_INPUT,
            message="forced verify fail",
        )
        with patch("routers.compute.verify_full", side_effect=exc):
            resp = client.post(
                f"/api/v1/cases/{owned_case.id}/compute",
                json={},
                headers=headers,
            )
        assert resp.status_code == 200
        assert resp.json()["tasks"]["verify"]["status"] == "failed"

    def test_compute_case_verify_generic_exception(
        self, client: TestClient, test_user, owned_case
    ):
        """verify_full 抛通用 Exception → 200 但 verify 任务失败（lines 285-300）"""
        headers = self._auth_headers(test_user)
        with patch("routers.compute.verify_full", side_effect=RuntimeError("verify crash")):
            resp = client.post(
                f"/api/v1/cases/{owned_case.id}/compute",
                json={},
                headers=headers,
            )
        assert resp.status_code == 200
        assert resp.json()["tasks"]["verify"]["status"] == "failed"


# ===========================================================================
# TestSnapshotsRouterCoverage
# ===========================================================================
class TestSnapshotsRouterCoverage:
    """routers/snapshots.py — 覆盖未测路径
    缺失 lines: 46-47 (list 权限), 52-54 (list query),
                73, 76-77, 81 (get_snapshot), 101, 104-105, 109-112 (delete)
    """

    # ── fixtures ───────────────────────────────────────────────────────────
    @pytest.fixture
    def owned_case(self, db_session: SQLModelSession, test_user):
        from app.models import Case
        case = Case(
            id=str(uuid4()),
            owner_id=test_user.id,
            name="Snap My Case",
            birth_dt_local="1990-01-15T10:00:00",
            tz="Asia/Shanghai",
            lon=121.5,
        )
        db_session.add(case)
        db_session.commit()
        db_session.refresh(case)
        return case

    @pytest.fixture
    def other_case(self, db_session: SQLModelSession):
        from app.models import Case, User
        other = User(
            username=f"snap_other_{uuid4().hex[:6]}",
            email=f"snap_{uuid4().hex[:6]}@x.com",
            password_hash="x", role="viewer",
            is_active=True, is_admin=False,
        )
        db_session.add(other)
        db_session.flush()
        case = Case(
            id=str(uuid4()),
            owner_id=other.id,
            name="Snap Other Case",
            birth_dt_local="1990-01-15T10:00:00",
            tz="Asia/Shanghai",
            lon=121.5,
        )
        db_session.add(case)
        db_session.commit()
        db_session.refresh(case)
        return case

    @pytest.fixture
    def owned_snapshot(self, db_session: SQLModelSession, owned_case):
        from app.models import Snapshot
        snap = Snapshot(
            case_id=owned_case.id,
            kind="bazi",
            output_json={"status": "test_snap"},
        )
        db_session.add(snap)
        db_session.commit()
        db_session.refresh(snap)
        return snap

    @pytest.fixture
    def other_snapshot(self, db_session: SQLModelSession, other_case):
        from app.models import Snapshot
        snap = Snapshot(
            case_id=other_case.id,
            kind="bazi",
            output_json={"status": "other_snap"},
        )
        db_session.add(snap)
        db_session.commit()
        db_session.refresh(snap)
        return snap

    def _auth_headers(self, user):
        from services.auth_service import create_access_token
        td = create_access_token(
            user_id=user.id, username=user.username, role=user.role
        )
        return {"Authorization": f"Bearer {td['access_token']}"}

    # ── list_snapshots ─────────────────────────────────────────────────────
    def test_list_snapshots_success(
        self, client: TestClient, test_user, owned_case
    ):
        """list_snapshots 正常返回 200（覆盖 lines 52-54 query building）"""
        headers = self._auth_headers(test_user)
        resp = client.get(
            f"/api/v1/cases/{owned_case.id}/snapshots",
            headers=headers,
        )
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_list_snapshots_wrong_owner_returns_403(
        self, client: TestClient, test_user, other_case
    ):
        """Case 属于他人 → 403（lines 46-47）"""
        headers = self._auth_headers(test_user)
        resp = client.get(
            f"/api/v1/cases/{other_case.id}/snapshots",
            headers=headers,
        )
        assert resp.status_code == 403

    # ── get_snapshot ───────────────────────────────────────────────────────
    def test_get_snapshot_success(
        self, client: TestClient, test_user, owned_snapshot
    ):
        """get_snapshot 正常返回 200（覆盖 line 81 false → return）"""
        headers = self._auth_headers(test_user)
        resp = client.get(
            f"/api/v1/snapshots/{owned_snapshot.id}",
            headers=headers,
        )
        assert resp.status_code == 200
        assert resp.json()["id"] == owned_snapshot.id

    def test_get_snapshot_wrong_owner_returns_403(
        self, client: TestClient, test_user, other_snapshot
    ):
        """他人 case 的 snapshot → 403（lines 76-77, 81 true branch）"""
        headers = self._auth_headers(test_user)
        resp = client.get(
            f"/api/v1/snapshots/{other_snapshot.id}",
            headers=headers,
        )
        assert resp.status_code == 403

    def test_get_snapshot_not_found_returns_404(
        self, client: TestClient, test_user
    ):
        """Snapshot 不存在 → 404（lines 73, 76）"""
        headers = self._auth_headers(test_user)
        resp = client.get(
            f"/api/v1/snapshots/nonexistent-{uuid4().hex}",
            headers=headers,
        )
        assert resp.status_code == 404

    # ── delete_snapshot ────────────────────────────────────────────────────
    def test_delete_snapshot_success(
        self, client: TestClient, test_user, owned_snapshot
    ):
        """delete_snapshot 成功 → 204（lines 109-112 soft-delete + log_action）"""
        headers = self._auth_headers(test_user)
        resp = client.delete(
            f"/api/v1/snapshots/{owned_snapshot.id}",
            headers=headers,
        )
        assert resp.status_code == 204

    def test_delete_snapshot_wrong_owner_returns_403(
        self, client: TestClient, test_user, other_snapshot
    ):
        """他人 case 的 snapshot → 403（lines 104-105）"""
        headers = self._auth_headers(test_user)
        resp = client.delete(
            f"/api/v1/snapshots/{other_snapshot.id}",
            headers=headers,
        )
        assert resp.status_code == 403

    def test_delete_snapshot_not_found_returns_404(
        self, client: TestClient, test_user
    ):
        """Snapshot 不存在 → 404（line 101）"""
        headers = self._auth_headers(test_user)
        resp = client.delete(
            f"/api/v1/snapshots/nonexistent-{uuid4().hex}",
            headers=headers,
        )
        assert resp.status_code == 404


# ===========================================================================
# TestRelationsEndpointCoverage
# ===========================================================================
class TestRelationsEndpointCoverage:
    """routers/relations.py — 覆盖 compat 端点主路径（lines 280-372）"""

    # ── fixtures ───────────────────────────────────────────────────────────
    @pytest.fixture
    def case_a(self, db_session: SQLModelSession, test_user):
        from app.models import Case
        case = Case(
            id=str(uuid4()),
            owner_id=test_user.id,
            name="Relations Person A",
            birth_dt_local="1990-01-15T10:00:00",
            tz="Asia/Shanghai",
            lon=121.5,
        )
        db_session.add(case)
        db_session.commit()
        db_session.refresh(case)
        return case

    @pytest.fixture
    def case_b(self, db_session: SQLModelSession, test_user):
        from app.models import Case
        case = Case(
            id=str(uuid4()),
            owner_id=test_user.id,
            name="Relations Person B",
            birth_dt_local="1992-08-22T14:00:00",
            tz="Asia/Shanghai",
            lon=121.5,
        )
        db_session.add(case)
        db_session.commit()
        db_session.refresh(case)
        return case

    @pytest.fixture
    def other_case(self, db_session: SQLModelSession):
        from app.models import Case, User
        other = User(
            username=f"rel_other_{uuid4().hex[:6]}",
            email=f"rel_{uuid4().hex[:6]}@x.com",
            password_hash="x", role="viewer",
            is_active=True, is_admin=False,
        )
        db_session.add(other)
        db_session.flush()
        case = Case(
            id=str(uuid4()),
            owner_id=other.id,
            name="Rel Other Person",
            birth_dt_local="1985-03-01T08:00:00",
            tz="Asia/Shanghai",
            lon=121.5,
        )
        db_session.add(case)
        db_session.commit()
        db_session.refresh(case)
        return case

    def _auth_headers(self, user):
        from services.auth_service import create_access_token
        td = create_access_token(
            user_id=user.id, username=user.username, role=user.role
        )
        return {"Authorization": f"Bearer {td['access_token']}"}

    # ── tests ──────────────────────────────────────────────────────────────
    def test_compute_relation_success(
        self, client: TestClient, test_user, case_a, case_b
    ):
        """两个有效 case → 200，覆盖 get_or_compute + bazi_full 执行路径（lines 301-372）"""
        headers = self._auth_headers(test_user)
        resp = client.post(
            "/api/v1/relations/compat",
            json={
                "case_a_id": case_a.id,
                "case_b_id": case_b.id,
                "relation_type": "couple",
            },
            headers=headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "result" in data
        assert "compatibility_score" in data["result"]

    def test_compute_relation_reuses_existing_snapshot(
        self,
        client: TestClient,
        test_user,
        case_a,
        case_b,
        db_session: SQLModelSession,
    ):
        """已有 bazi snapshot → 复用缓存而非重算（lines 304-310）"""
        from app.models import Snapshot
        # 为 case_a 预设 bazi 快照
        snap_output = {
            "wuxing": {"木": 25, "火": 20, "土": 20, "金": 20, "水": 15},
            "yongshen": {"favor": ["木", "水"], "avoid": ["土", "金"]},
            "pillars_primary": {
                "year_pillar":  {"heavenly_stem": "庚", "earthly_branch": "午"},
                "month_pillar": {"heavenly_stem": "壬", "earthly_branch": "申"},
                "day_pillar":   {"heavenly_stem": "甲", "earthly_branch": "子"},
                "time_pillar":  {"heavenly_stem": "丙", "earthly_branch": "寅"},
            },
        }
        snap = Snapshot(
            case_id=case_a.id,
            kind="bazi",
            output_json=snap_output,
        )
        db_session.add(snap)
        db_session.commit()

        headers = self._auth_headers(test_user)
        resp = client.post(
            "/api/v1/relations/compat",
            json={
                "case_a_id": case_a.id,
                "case_b_id": case_b.id,
                "relation_type": "friend",
            },
            headers=headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "result" in data

    def test_compute_relation_unauthorized_case_returns_403(
        self, client: TestClient, test_user, case_a, other_case
    ):
        """其中一 case 属于他人 → 403（lines 288-291）"""
        headers = self._auth_headers(test_user)
        resp = client.post(
            "/api/v1/relations/compat",
            json={
                "case_a_id": case_a.id,
                "case_b_id": other_case.id,
                "relation_type": "couple",
            },
            headers=headers,
        )
        assert resp.status_code == 403

    def test_compute_relation_missing_case_returns_404(
        self, client: TestClient, test_user, case_a
    ):
        """其中一 case 不存在 → 404（lines 280-282）"""
        headers = self._auth_headers(test_user)
        resp = client.post(
            "/api/v1/relations/compat",
            json={
                "case_a_id": case_a.id,
                "case_b_id": f"nonexistent-{uuid4().hex}",
                "relation_type": "couple",
            },
            headers=headers,
        )
        assert resp.status_code == 404
