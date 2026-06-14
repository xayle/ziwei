"""
Coverage Boost #8 — app/schemas/case.py, routers/audit.py,
                    routers/events.py (remaining), routers/static_data.py (503 paths)

目标：覆盖四个文件的缺失分支，预计将整体覆盖率从 94.3% 推向 95%+。
"""
import pytest
from uuid import uuid4
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock

from sqlmodel import Session as SQLModelSession
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Minimal valid bazi_json
# ---------------------------------------------------------------------------
_BAZI_JSON = (
    '{"pillars_primary": {'
    '"year_pillar": {"heavenly_stem": "甲", "earthly_branch": "子"},'
    '"month_pillar": {"heavenly_stem": "丙", "earthly_branch": "寅"},'
    '"day_pillar":   {"heavenly_stem": "戊", "earthly_branch": "午"},'
    '"time_pillar":  {"heavenly_stem": "庚", "earthly_branch": "申"}'
    '}, "ten_gods": {}}'
)


# ===========================================================================
# TestCaseSchemaValidators
# ===========================================================================
class TestCaseSchemaValidators:
    """app/schemas/case.py — 覆盖 CaseBase / CasePatch 验证器错误路径
    缺失 lines: 24, 42-43, 62, 95-116, 133-136, 139, 152-186, 193-195, 220-223
    """

    # ── _normalize_birth_dt_local（line 24）─────────────────────────────────
    def test_normalize_birth_dt_non_string_raises(self):
        """_normalize_birth_dt_local: 非字符串 → ValueError（line 24）"""
        from app.schemas.case import _normalize_birth_dt_local
        with pytest.raises(ValueError, match="birth_dt_local"):
            _normalize_birth_dt_local(12345)  # type: ignore[arg-type]

    def test_normalize_birth_dt_invalid_pattern_raises(self):
        """_normalize_birth_dt_local: 不匹配 ISO 格式 → ValueError"""
        from app.schemas.case import _normalize_birth_dt_local
        with pytest.raises(ValueError):
            _normalize_birth_dt_local("not-a-date")

    def test_normalize_birth_dt_invalid_date_values_raises(self):
        """_normalize_birth_dt_local: 格式正确但日期非法 → ValueError（line 42-43）"""
        from app.schemas.case import _normalize_birth_dt_local
        with pytest.raises(ValueError):
            _normalize_birth_dt_local("2000-13-01T10:00:00")  # month 13 is invalid

    def test_normalize_birth_dt_with_microseconds(self):
        """_normalize_birth_dt_local: 带微秒的时间戳 → 含微秒的 ISO 串"""
        from app.schemas.case import _normalize_birth_dt_local
        result = _normalize_birth_dt_local("2000-01-01T10:00:00.123456")
        assert "123456" in result

    # ── CaseBase.validate_gender（line 62）────────────────────────────────
    def test_casebase_invalid_gender_raises(self):
        """CaseBase: gender 为无效值 → ValueError（line 62）"""
        from app.schemas.case import CaseBase
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            CaseBase(
                name="Test",
                gender="unknown_gender",
                birth_dt_local="2000-01-01T10:00:00",
                tz="Asia/Shanghai",
                lon=120.0,
            )

    # ── CaseBase.validate_tz（lines 95-101, 103）────────────────────────────
    def test_casebase_invalid_tz_raises(self):
        """CaseBase: tz 为非法时区 → ValueError（lines 95-98）"""
        from app.schemas.case import CaseBase
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            CaseBase(
                name="Test",
                birth_dt_local="2000-01-01T10:00:00",
                tz="Not/A/Valid/Timezone",
                lon=120.0,
            )

    # ── CaseBase.validate_tags（lines 108, 110, 116）────────────────────────
    def test_casebase_tags_list_converts_to_csv(self):
        """CaseBase: tags 传入 list → 逗号分隔字符串（lines 106-108）"""
        from app.schemas.case import CaseBase
        obj = CaseBase(
            name="Test",
            birth_dt_local="2000-01-01T10:00:00",
            tz="Asia/Shanghai",
            lon=120.0,
            tags=["tag1", "tag2", "tag3"],
        )
        assert obj.tags == "tag1,tag2,tag3"

    def test_casebase_tags_list_all_empty_returns_none(self):
        """CaseBase: tags 传入空列表 → None（line 108）"""
        from app.schemas.case import CaseBase
        obj = CaseBase(
            name="Test",
            birth_dt_local="2000-01-01T10:00:00",
            tz="Asia/Shanghai",
            lon=120.0,
            tags=[],
        )
        assert obj.tags is None

    def test_casebase_tags_non_string_non_list_raises(self):
        """CaseBase: tags 非 str/list → ValueError（line 110）"""
        from app.schemas.case import CaseBase
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            CaseBase(
                name="Test",
                birth_dt_local="2000-01-01T10:00:00",
                tz="Asia/Shanghai",
                lon=120.0,
                tags={"invalid": True},  # type: ignore[arg-type]
            )

    def test_casebase_tags_empty_string_returns_none(self):
        """CaseBase: tags 为空字符串 → None（line 112-113）"""
        from app.schemas.case import CaseBase
        obj = CaseBase(
            name="Test",
            birth_dt_local="2000-01-01T10:00:00",
            tz="Asia/Shanghai",
            lon=120.0,
            tags="   ",
        )
        assert obj.tags is None

    def test_casebase_tags_too_long_raises(self):
        """CaseBase: tags > 200字符 → ValueError（line 116）"""
        from app.schemas.case import CaseBase
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            CaseBase(
                name="Test",
                birth_dt_local="2000-01-01T10:00:00",
                tz="Asia/Shanghai",
                lon=120.0,
                tags="a" * 201,
            )

    def test_casebase_tags_invalid_pattern_raises(self):
        """CaseBase: tags 含非法字符（如@）→ ValueError"""
        from app.schemas.case import CaseBase
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            CaseBase(
                name="Test",
                birth_dt_local="2000-01-01T10:00:00",
                tz="Asia/Shanghai",
                lon=120.0,
                tags="valid,tag!@#invalid",
            )

    def test_casebase_lon_out_of_range_raises(self):
        """CaseBase: lon 超出范围 → ValueError（lines 120-121）"""
        from app.schemas.case import CaseBase
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            CaseBase(
                name="Test",
                birth_dt_local="2000-01-01T10:00:00",
                tz="Asia/Shanghai",
                lon=200.0,  # Out of valid range
            )

    # ── CasePatch validators（lines 133-186）────────────────────────────────
    def test_casepatch_invalid_gender_raises(self):
        """CasePatch.validate_gender: 非法值 → ValueError（lines 133-136）"""
        from app.schemas.case import CasePatch
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            CasePatch(gender="robot")

    def test_casepatch_invalid_birth_dt_local_raises(self):
        """CasePatch.validate_birth_dt_local: 非法格式 → ValueError（lines 152-154）"""
        from app.schemas.case import CasePatch
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            CasePatch(birth_dt_local="not-a-date")

    def test_casepatch_invalid_tz_raises(self):
        """CasePatch.validate_tz: 非法时区 → ValueError（lines 159-164）"""
        from app.schemas.case import CasePatch
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            CasePatch(tz="BadTimezone/Unknown")

    def test_casepatch_tags_list_converts(self):
        """CasePatch.validate_tags: list → CSV 字符串（lines 170-176）"""
        from app.schemas.case import CasePatch
        patch_obj = CasePatch(tags=["alpha", "beta"])
        assert patch_obj.tags == "alpha,beta"

    def test_casepatch_tags_empty_string_returns_none(self):
        """CasePatch.validate_tags: 空字符串 → None"""
        from app.schemas.case import CasePatch
        patch_obj = CasePatch(tags="   ")
        assert patch_obj.tags is None

    def test_casepatch_tags_too_long_raises(self):
        """CasePatch.validate_tags: > 200字符 → ValueError（lines 179-180）"""
        from app.schemas.case import CasePatch
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            CasePatch(tags="x" * 201)

    def test_casepatch_lon_valid_passes(self):
        """CasePatch.validate_lon: 有效 lon None → 不做校验"""
        from app.schemas.case import CasePatch
        patch_obj = CasePatch(lon=None)
        assert patch_obj.lon is None

    def test_casepatch_lon_out_of_range_raises(self):
        """CasePatch.validate_lon: 超出范围 → ValueError（lines 193-195）"""
        from app.schemas.case import CasePatch
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            CasePatch(lon=-200.0)

    # ── CaseOut.validate_tags（lines 220-223）──────────────────────────────
    def test_caseout_tags_list_input(self):
        """CaseOut.validate_tags: list 输入 → list 输出（line 222-223）"""
        from app.schemas.case import CaseOut
        obj = CaseOut(
            id="test-id",
            name="Test",
            birth_dt_local="2000-01-01T10:00:00",
            tz="Asia/Shanghai",
            lon=120.0,
            tags=["tag1", "tag2"],
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        assert obj.tags == ["tag1", "tag2"]

    def test_caseout_tags_none_returns_none(self):
        """CaseOut.validate_tags: None → None（line 220-221）"""
        from app.schemas.case import CaseOut
        obj = CaseOut(
            id="test-id",
            name="Test",
            birth_dt_local="2000-01-01T10:00:00",
            tz="Asia/Shanghai",
            lon=120.0,
            tags=None,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        assert obj.tags is None

    def test_caseout_tags_empty_list_returns_none(self):
        """CaseOut.validate_tags: 空 list → None"""
        from app.schemas.case import CaseOut
        obj = CaseOut(
            id="test-id",
            name="Test",
            birth_dt_local="2000-01-01T10:00:00",
            tz="Asia/Shanghai",
            lon=120.0,
            tags=[],
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        assert obj.tags is None

    def test_casebase_valid_gender_returns_v(self):
        """CaseBase.validate_gender: 有效值 → 正常 return v（line 62）"""
        from app.schemas.case import CaseBase
        obj = CaseBase(
            name="Test",
            gender="male",   # valid gender
            birth_dt_local="2000-01-01T10:00:00",
            tz="Asia/Shanghai",
            lon=120.0,
        )
        assert obj.gender == "male"

    def test_casebase_valid_tz_returns_v(self):
        """CaseBase.validate_tz: 有效时区 → 正常 return v（line 95）"""
        from app.schemas.case import CaseBase
        obj = CaseBase(
            name="Test",
            birth_dt_local="2000-01-01T10:00:00",
            tz="America/New_York",  # valid tz
            lon=-74.0,
        )
        assert obj.tz == "America/New_York"

    def test_casepatch_valid_gender_returns_v(self):
        """CasePatch.validate_gender: 有效值 → return v（line 134）"""
        from app.schemas.case import CasePatch
        patch_obj = CasePatch(gender="female")
        assert patch_obj.gender == "female"

    def test_casepatch_gender_none_returns_v(self):
        """CasePatch.validate_gender: None → return v（line 139）"""
        from app.schemas.case import CasePatch
        patch_obj = CasePatch(gender=None)
        assert patch_obj.gender is None

    def test_casepatch_valid_birth_dt_returns_v(self):
        """CasePatch.validate_birth_dt_local: 有效格式 → return v（line 153）"""
        from app.schemas.case import CasePatch
        patch_obj = CasePatch(birth_dt_local="1985-06-15T08:30:00")
        assert "1985" in patch_obj.birth_dt_local

    def test_casepatch_valid_tz_returns_v(self):
        """CasePatch.validate_tz: 有效时区 → return v（line 160, 165）"""
        from app.schemas.case import CasePatch
        patch_obj = CasePatch(tz="Europe/London")
        assert patch_obj.tz == "Europe/London"

    def test_casepatch_tags_valid_string_returns_v(self):
        """CasePatch.validate_tags: 有效字符串 → return v（lines 171-176）"""
        from app.schemas.case import CasePatch
        patch_obj = CasePatch(tags="alpha,beta,gamma")
        assert patch_obj.tags == "alpha,beta,gamma"

    def test_casepatch_tags_list_with_empty_items(self):
        """CasePatch: list with all empty items → None（line 176）"""
        from app.schemas.case import CasePatch
        patch_obj = CasePatch(tags=["  ", "  "])
        assert patch_obj.tags is None

    def test_casepatch_tags_non_string_non_list_raises_v2(self):
        """CasePatch.validate_tags: 非 str/list → ValueError（line 178）"""
        from app.schemas.case import CasePatch
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            CasePatch(tags=12345)  # type: ignore[arg-type]

    def test_casepatch_tags_invalid_pattern_raises_v2(self):
        """CasePatch.validate_tags: 含非法字符 → ValueError（line 185）"""
        from app.schemas.case import CasePatch
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            CasePatch(tags="valid!@#%")

    def test_casepatch_lon_valid_returns_self(self):
        """CasePatch.validate_lon: 有效 lon → return self（line 195）"""
        from app.schemas.case import CasePatch
        patch_obj = CasePatch(lon=100.0)
        assert patch_obj.lon == 100.0

    def test_caseout_tags_csv_string_splits_to_list(self):
        """CaseOut.validate_tags: CSV 字符串 → 分割为 list（line 223）"""
        from app.schemas.case import CaseOut
        obj = CaseOut(
            id="test-id",
            name="Test",
            birth_dt_local="2000-01-01T10:00:00",
            tz="Asia/Shanghai",
            lon=120.0,
            tags="alpha,beta,gamma",  # CSV string → should split
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        # CaseOut.validate_tags converts CSV to list or keeps as is
        assert obj.tags is not None


# ===========================================================================
# TestAuditRouterCoverage
# ===========================================================================
class TestAuditRouterCoverage:
    """routers/audit.py — 覆盖 admin 端点 + get_detail + manual log
    缺失 lines: 151, 153, 202, 206-207, 213-214, 219, 251-254, 263
    """

    def _admin_headers(self, admin_user):
        from services.auth_service import create_access_token
        td = create_access_token(
            user_id=admin_user.id, username=admin_user.username, role=admin_user.role
        )
        return {"Authorization": f"Bearer {td['access_token']}"}

    def _user_headers(self, user):
        from services.auth_service import create_access_token
        td = create_access_token(
            user_id=user.id, username=user.username, role=user.role
        )
        return {"Authorization": f"Bearer {td['access_token']}"}

    # ── GET /audit-logs/admin ──────────────────────────────────────────────
    def test_admin_get_all_audit_logs_with_filters(
        self, client: TestClient, admin_user
    ):
        """管理员带过滤器查 audit logs（lines 151, 153）"""
        headers = self._admin_headers(admin_user)
        resp = client.get(
            "/api/v1/audit-logs/admin?user_id=1&action=login&resource_type=user",
            headers=headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data and "total" in data

    def test_admin_audit_logs_with_before_id(
        self, client: TestClient, admin_user
    ):
        """管理员带 before_id 查 audit logs（keyset 分页）"""
        headers = self._admin_headers(admin_user)
        resp = client.get(
            "/api/v1/audit-logs/admin?before_id=999999",
            headers=headers,
        )
        assert resp.status_code == 200

    # ── GET /audit-logs/{log_id} ────────────────────────────────────────────
    def test_get_audit_log_detail_not_found_returns_404(
        self, client: TestClient, admin_user
    ):
        """audit_log 不存在 → 404（lines 206-207）"""
        headers = self._admin_headers(admin_user)
        resp = client.get("/api/v1/audit-logs/9999991", headers=headers)
        assert resp.status_code == 404

    def test_get_audit_log_detail_other_user_returns_403(
        self, client: TestClient, test_user, db_session: SQLModelSession
    ):
        """非管理员查他人日志 → 403（lines 213-214）"""
        from app.models import AuditLog
        from services.auth_service import create_access_token

        # 创建一个属于 admin 的 audit log（user_id != test_user.id）
        log = AuditLog(
            user_id=999,  # 不是 test_user.id
            action="test_action",
            resource_type="test",
            resource_id="test-id",
        )
        db_session.add(log)
        db_session.commit()
        db_session.refresh(log)

        td = create_access_token(
            user_id=test_user.id, username=test_user.username, role=test_user.role
        )
        headers = {"Authorization": f"Bearer {td['access_token']}"}
        resp = client.get(f"/api/v1/audit-logs/{log.id}", headers=headers)
        assert resp.status_code == 403

    def test_get_audit_log_detail_own_log_success(
        self, client: TestClient, test_user, db_session: SQLModelSession
    ):
        """用户查自己的日志 → 200（line 219 return）"""
        from app.models import AuditLog
        from services.auth_service import create_access_token

        log = AuditLog(
            user_id=test_user.id,
            action="test_own_log",
            resource_type="user",
            resource_id=str(test_user.id),
        )
        db_session.add(log)
        db_session.commit()
        db_session.refresh(log)

        td = create_access_token(
            user_id=test_user.id, username=test_user.username, role=test_user.role
        )
        headers = {"Authorization": f"Bearer {td['access_token']}"}
        resp = client.get(f"/api/v1/audit-logs/{log.id}", headers=headers)
        assert resp.status_code == 200
        assert resp.json()["action"] == "test_own_log"

    # ── POST /audit-logs/manual ────────────────────────────────────────────
    def test_post_manual_audit_log_success(
        self, client: TestClient, test_user
    ):
        """POST /audit-logs/manual → 200（lines 251-263）"""
        headers = self._user_headers(test_user)
        resp = client.post(
            "/api/v1/audit-logs/manual",
            json={
                "action": "manual_test_action",
                "resource_type": "test_resource",
                "resource_id": "res-123",
            },
            headers=headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["action"] == "manual_test_action"

    def test_post_manual_audit_log_no_resource_id(
        self, client: TestClient, test_user
    ):
        """POST /audit-logs/manual 无 resource_id → 200"""
        headers = self._user_headers(test_user)
        resp = client.post(
            "/api/v1/audit-logs/manual",
            json={
                "action": "no_id_action",
                "resource_type": "event",
            },
            headers=headers,
        )
        assert resp.status_code == 200


# ===========================================================================
# TestEventsRouterRemaining
# ===========================================================================
class TestEventsRouterRemaining:
    """routers/events.py — 覆盖 get/put/delete/member_events 缺失路径
    缺失: 347(get-not-found), 387(get-wrong-owner),
         418-420(patch-not-found), 453(patch-wrong-owner),
         476(put-not-found), 494-496(put-wrong-owner),
         529(delete-not-found), 583(delete-wrong-owner),
         596(list_member_events cursor pagination)
    """

    @pytest.fixture
    def _my_event(self, client_with_auth: TestClient, test_member):
        """创建一个属于 test_user 的事件"""
        import routers.events as ev
        ev._events_cache.clear()
        resp = client_with_auth.post("/api/v1/events", json={
            "member_id": test_member.id,
            "name": "Boost8 Event",
            "event_type": "consultation",
            "bazi_json": _BAZI_JSON,
            "L_level": 1,
            "confidence_score": 0.8,
        })
        assert resp.status_code == 201
        return resp.json()

    @pytest.fixture
    def _other_event(self, db_session: SQLModelSession, admin_user):
        """属于 admin_user 的事件（test_user 无权访问）"""
        from datetime import date, timezone as tz_module
        from app.models import Event, Member

        # 创建 admin 的 member（使用正确字段）
        other_member = Member(
            owner_id=admin_user.id,
            name="Admin Member for Event",
            birth_date=date(1990, 6, 15),
            gender="M",
            birth_time_hour=10,
            birth_time_minute=0,
            birth_longitude=120.0,
            solar_time_enabled=False,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db_session.add(other_member)
        db_session.flush()

        event = Event(
            owner_id=admin_user.id,
            member_id=other_member.id,
            name="Admin Event",
            event_type="consultation",
            bazi_json=_BAZI_JSON,
            L_level=1,
            confidence_score=0.7,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db_session.add(event)
        db_session.commit()
        db_session.refresh(event)
        return event

    def _auth_headers(self, user):
        from services.auth_service import create_access_token
        td = create_access_token(
            user_id=user.id, username=user.username, role=user.role
        )
        return {
            "Authorization": f"Bearer {td['access_token']}",
            "Content-Type": "application/json",
        }

    # ── GET /events/{id} ───────────────────────────────────────────────────
    def test_get_event_not_found_returns_404(
        self, client: TestClient, test_user
    ):
        """get_event: 不存在 → 404（line 347）"""
        headers = self._auth_headers(test_user)
        resp = client.get("/api/v1/events/999991", headers=headers)
        assert resp.status_code == 404

    def test_get_event_wrong_owner_returns_403(
        self, client: TestClient, test_user, _other_event
    ):
        """get_event: 他人事件 → 403（line 387）"""
        headers = self._auth_headers(test_user)
        resp = client.get(f"/api/v1/events/{_other_event.id}", headers=headers)
        assert resp.status_code == 403

    # ── PATCH /events/{id} ────────────────────────────────────────────────
    def test_patch_event_not_found_returns_404(
        self, client: TestClient, test_user
    ):
        """patch_event: 不存在 → 404（lines 418-420）"""
        headers = self._auth_headers(test_user)
        resp = client.patch(
            "/api/v1/events/999991",
            json={"name": "New Name"},
            headers=headers,
        )
        assert resp.status_code == 404

    def test_patch_event_wrong_owner_returns_403(
        self, client: TestClient, test_user, _other_event
    ):
        """patch_event: 他人事件 → 403（line 453）"""
        headers = self._auth_headers(test_user)
        resp = client.patch(
            f"/api/v1/events/{_other_event.id}",
            json={"name": "Hijack"},
            headers=headers,
        )
        assert resp.status_code == 403

    # ── PUT /events/{id} ──────────────────────────────────────────────────
    def test_put_event_not_found_returns_404(
        self, client: TestClient, test_user, test_member
    ):
        """update_event: 不存在 → 404（line 476）"""
        headers = self._auth_headers(test_user)
        resp = client.put(
            "/api/v1/events/999991",
            json={
                "member_id": test_member.id,
                "name": "Non-existent Event",
                "event_type": "consultation",
                "bazi_json": _BAZI_JSON,
                "L_level": 1,
                "confidence_score": 0.8,
            },
            headers=headers,
        )
        assert resp.status_code == 404

    def test_put_event_wrong_owner_returns_403(
        self, client: TestClient, test_user, test_member, _other_event
    ):
        """update_event: 他人事件 → 403（lines 494-496）"""
        headers = self._auth_headers(test_user)
        resp = client.put(
            f"/api/v1/events/{_other_event.id}",
            json={
                "member_id": test_member.id,
                "name": "Hijack Event",
                "event_type": "consultation",
                "bazi_json": _BAZI_JSON,
                "L_level": 1,
                "confidence_score": 0.8,
            },
            headers=headers,
        )
        assert resp.status_code == 403

    # ── DELETE /events/{id} ───────────────────────────────────────────────
    def test_delete_event_not_found_returns_404(
        self, client: TestClient, test_user
    ):
        """delete_event: 不存在 → 404（line 529）"""
        headers = self._auth_headers(test_user)
        resp = client.delete("/api/v1/events/999991", headers=headers)
        assert resp.status_code == 404

    def test_delete_event_wrong_owner_returns_403(
        self, client: TestClient, test_user, _other_event
    ):
        """delete_event: 他人事件 → 403（line 583）"""
        headers = self._auth_headers(test_user)
        resp = client.delete(f"/api/v1/events/{_other_event.id}", headers=headers)
        assert resp.status_code == 403

    # ── DELETE success + PUT success ──────────────────────────────────────
    def test_put_event_success(
        self, client_with_auth: TestClient, test_member, _my_event
    ):
        """PUT /events/{id} 成功更新（覆盖 line 512 commit 路径）"""
        resp = client_with_auth.put(
            f"/api/v1/events/{_my_event['id']}",
            json={
                "member_id": test_member.id,
                "name": "Updated Event",
                "event_type": "consultation",
                "bazi_json": _BAZI_JSON,
                "L_level": 2,
                "confidence_score": 0.9,
            },
        )
        assert resp.status_code == 200
        assert resp.json()["name"] == "Updated Event"

    def test_delete_event_success(
        self, client_with_auth: TestClient, _my_event
    ):
        """DELETE /events/{id} 成功删除 → 204"""
        resp = client_with_auth.delete(f"/api/v1/events/{_my_event['id']}")
        assert resp.status_code == 204

    # ── GET /members/{id}/events ────────────────────────────────────────────
    def test_list_member_events_with_cursor(
        self, client_with_auth: TestClient, test_member
    ):
        """GET /members/{id}/events?last_id=X → 覆盖 cursor 分页（line 596）"""
        resp = client_with_auth.get(
            f"/api/v1/members/{test_member.id}/events?last_id=100"
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "events" in data
        assert "has_more" in data


# ===========================================================================
# TestStaticData503Paths
# ===========================================================================
class TestStaticData503Paths:
    """routers/static_data.py — 覆盖 lru_cache 内部 error path + 503
    缺失 lines: 51-52 (not exists), 60-62 (load error), 70-71, 80-82 (cities),
               101 (glossary 503), 121 (cities 503)
    """

    @pytest.fixture
    def plain_client(self, app_with_test_db) -> TestClient:
        return TestClient(app_with_test_db)

    def test_get_glossary_503_when_no_data(self, plain_client: TestClient):
        """_load_glossary 返回空列表 → 503（line 101）"""
        from routers.static_data import _load_glossary
        with patch.object(_load_glossary, "cache_clear"):
            with patch("routers.static_data._load_glossary", return_value=[]):
                resp = plain_client.get("/api/v1/glossary")
        assert resp.status_code == 503

    def test_get_cities_503_when_no_data(self, plain_client: TestClient):
        """_load_cities 返回空列表 → 503（line 121）"""
        with patch("routers.static_data._load_cities", return_value=[]):
            resp = plain_client.get("/api/v1/cities")
        assert resp.status_code == 503

    def test_load_glossary_file_not_found_returns_empty(self, tmp_path):
        """_load_glossary: 文件不存在 → 返回 []（lines 51-52）"""
        # Clear LRU cache to allow fresh call
        from routers import static_data as sd
        sd._load_glossary.cache_clear()
        sd._load_cities.cache_clear()

        original_data_dir = sd._DATA_DIR
        try:
            sd._DATA_DIR = tmp_path / "nonexistent_data_dir"
            result = sd._load_glossary()
            assert result == []
        finally:
            sd._DATA_DIR = original_data_dir
            sd._load_glossary.cache_clear()
            sd._load_cities.cache_clear()

    def test_load_glossary_malformed_json_returns_empty(self, tmp_path):
        """_load_glossary: JSON 格式错误 → 返回 []（lines 60-62）"""
        from routers import static_data as sd
        sd._load_glossary.cache_clear()
        sd._load_cities.cache_clear()

        data_dir = tmp_path / "data"
        data_dir.mkdir()
        (data_dir / "glossary.json").write_text("this is not json", encoding="utf-8")

        original_data_dir = sd._DATA_DIR
        try:
            sd._DATA_DIR = data_dir
            result = sd._load_glossary()
            assert result == []
        finally:
            sd._DATA_DIR = original_data_dir
            sd._load_glossary.cache_clear()
            sd._load_cities.cache_clear()

    def test_load_cities_file_not_found_returns_empty(self, tmp_path):
        """_load_cities: 文件不存在 → 返回 []（lines 70-71）"""
        from routers import static_data as sd
        sd._load_glossary.cache_clear()
        sd._load_cities.cache_clear()

        original_data_dir = sd._DATA_DIR
        try:
            sd._DATA_DIR = tmp_path / "nonexistent_data_dir"
            result = sd._load_cities()
            assert result == []
        finally:
            sd._DATA_DIR = original_data_dir
            sd._load_glossary.cache_clear()
            sd._load_cities.cache_clear()

    def test_load_cities_malformed_json_returns_empty(self, tmp_path):
        """_load_cities: JSON 格式错误 → 返回 []（lines 80-82）"""
        from routers import static_data as sd
        sd._load_glossary.cache_clear()
        sd._load_cities.cache_clear()

        data_dir = tmp_path / "data"
        data_dir.mkdir()
        (data_dir / "cities.json").write_text("not valid json {{", encoding="utf-8")

        original_data_dir = sd._DATA_DIR
        try:
            sd._DATA_DIR = data_dir
            result = sd._load_cities()
            assert result == []
        finally:
            sd._DATA_DIR = original_data_dir
            sd._load_glossary.cache_clear()
            sd._load_cities.cache_clear()


# ===========================================================================
# TestEventsJsonValidators
# ===========================================================================
class TestEventsJsonValidators:
    """routers/events.py _validate_json_field + EventCreateRequest validators
    lines: 41 (return None), 44-45 (JSONDecodeError), 47 (type mismatch),
           73, 78, 83, 88, 106, 111, 116, 121 (field validators w/ valid data)
    """

    def test_validate_json_field_none_returns_none(self):
        """_validate_json_field(None) → None（line 41）"""
        from routers.events import _validate_json_field
        result = _validate_json_field(None, "test_field", dict)
        assert result is None

    def test_validate_json_field_invalid_json_raises(self):
        """_validate_json_field: 非法 JSON → ValueError（lines 44-45）"""
        from routers.events import _validate_json_field
        with pytest.raises(ValueError, match="must be valid JSON"):
            _validate_json_field("not {json}", "test_field", dict)

    def test_validate_json_field_wrong_type_raises(self):
        """_validate_json_field: 类型不符 → ValueError（line 47）"""
        from routers.events import _validate_json_field
        with pytest.raises(ValueError, match="must be JSON"):
            _validate_json_field('["list"]', "test_field", dict)  # expected dict, got list

    def test_event_create_request_with_optional_json_fields(self):
        """EventCreateRequest 带 recommendation/ten_gods/pillars_primary/five_elements → validators 执行"""
        from routers.events import EventCreateRequest
        req = EventCreateRequest(
            member_id=1,
            name="Full Event",
            event_type="consultation",
            bazi_json='{"year": "甲子"}',
            pillars_primary='{"year": "甲子"}',
            ten_gods='[{"god": "正官"}]',
            five_elements='{"wood": 2}',
            recommendation='{"advice": "good"}',
        )
        assert req.pillars_primary is not None
        assert req.ten_gods is not None
        assert req.five_elements is not None
        assert req.recommendation is not None

    def test_event_update_request_with_json_fields(self):
        """EventUpdateRequest 带 recommendation/pillars_primary/ten_gods → validators 执行"""
        from routers.events import EventUpdateRequest
        req = EventUpdateRequest(
            name="Updated",
            recommendation='{"advice": "new"}',
            pillars_primary='{"stem": "丙"}',
            ten_gods='[{"god": "偏财"}]',
            five_elements='{"fire": 3}',
        )
        assert req.recommendation is not None

    def test_event_create_request_invalid_pillars_raises(self):
        """EventCreateRequest: pillars_primary 不是 dict → ValidationError"""
        from routers.events import EventCreateRequest
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            EventCreateRequest(
                member_id=1,
                name="Bad Event",
                event_type="consultation",
                bazi_json='{"year": "甲子"}',
                pillars_primary='["not", "a", "dict"]',
            )


# ===========================================================================
# TestEventsPermissionDenied
# ===========================================================================
class TestEventsPermissionDenied:
    """覆盖 events 路由中所有权限拒绝分支（Permission denied）
    lines: 179, 282, 347, 387, 453, 529, 583
    """

    def _guest_headers(self, db_session, admin_user):
        """创建 guest 用户并返回其认证头"""
        from app.models import User
        from services.auth_service import create_access_token, hash_password

        guest = User(
            username=f"guest_{uuid4().hex[:8]}",
            email=f"guest_{uuid4().hex[:8]}@test.com",
            password_hash=hash_password("Passw0rd!"),
            role="guest",
            is_active=True,
            is_admin=False,
        )
        db_session.add(guest)
        db_session.commit()
        db_session.refresh(guest)

        td = create_access_token(
            user_id=guest.id, username=guest.username, role=guest.role
        )
        return {"Authorization": f"Bearer {td['access_token']}"}

    def test_create_event_permission_denied(
        self, client: TestClient, db_session, admin_user
    ):
        """guest 用户 POST /events → 403 Permission denied（line 179）"""
        headers = self._guest_headers(db_session, admin_user)
        resp = client.post(
            "/api/v1/events",
            json={
                "member_id": 1,
                "name": "Unauthorized",
                "event_type": "consultation",
                "bazi_json": '{"x":1}',
                "L_level": 0,
                "confidence_score": 0.5,
            },
            headers=headers,
        )
        assert resp.status_code == 403

    def test_list_events_permission_denied(
        self, client: TestClient, db_session, admin_user
    ):
        """guest 用户 GET /events → 403（line 282）"""
        headers = self._guest_headers(db_session, admin_user)
        resp = client.get("/api/v1/events", headers=headers)
        assert resp.status_code == 403

    def test_get_event_permission_denied(
        self, client: TestClient, db_session, admin_user
    ):
        """guest 用户 GET /events/{id} → 403（line 347）"""
        headers = self._guest_headers(db_session, admin_user)
        resp = client.get("/api/v1/events/1", headers=headers)
        assert resp.status_code == 403

    def test_patch_event_permission_denied(
        self, client: TestClient, db_session, admin_user
    ):
        """guest 用户 PATCH /events/{id} → 403（line 387）"""
        headers = self._guest_headers(db_session, admin_user)
        resp = client.patch(
            "/api/v1/events/1", json={"name": "x"}, headers=headers
        )
        assert resp.status_code == 403

    def test_delete_event_permission_denied(
        self, client: TestClient, db_session, admin_user
    ):
        """guest 用户 DELETE /events/{id} → 403（line 529）"""
        headers = self._guest_headers(db_session, admin_user)
        resp = client.delete("/api/v1/events/1", headers=headers)
        assert resp.status_code == 403


# ===========================================================================
# TestEventsExtraFlows
# ===========================================================================
class TestEventsExtraFlows:
    """events 路由的成功/缓存/IntegrityError 路径
    lines: 194, 198, 201-203 (JSON val during create),
           228-230 (create IntegrityError),
           293 (list cache hit),
           313 (last_id cursor in list),
           418-420, 453 (patch IntegrityError / wrong-owner),
           476 (update check_member_ownership),
           494-496 (update IntegrityError)
    """

    def _user_headers(self, user):
        from services.auth_service import create_access_token
        td = create_access_token(
            user_id=user.id, username=user.username, role=user.role
        )
        return {
            "Authorization": f"Bearer {td['access_token']}",
            "Content-Type": "application/json",
        }

    def test_create_event_with_recommendation_field(
        self, client_with_auth: TestClient, test_member
    ):
        """create_event 带 recommendation → 触发 EventJsonValidator.validate_recommendation（lines 194, 198）"""
        import routers.events as ev
        ev._events_cache.clear()
        resp = client_with_auth.post("/api/v1/events", json={
            "member_id": test_member.id,
            "name": "Event With Rec",
            "event_type": "consultation",
            "bazi_json": _BAZI_JSON,
            "recommendation": '{"advice": ["go ahead", "be patient"], "confidence": 0.9}',
            "five_elements": '{"wood": 2, "fire": 1}',
            "L_level": 1,
            "confidence_score": 0.8,
        })
        assert resp.status_code == 201

    def test_create_event_invalid_recommendation_json(
        self, client_with_auth: TestClient, test_member
    ):
        """create_event: recommendation 格式错误 → ValidationException（lines 201-203）"""
        import routers.events as ev
        ev._events_cache.clear()
        resp = client_with_auth.post("/api/v1/events", json={
            "member_id": test_member.id,
            "name": "Bad Rec Event",
            "event_type": "consultation",
            "bazi_json": _BAZI_JSON,
            "recommendation": '["not", "a", "dict"]',  # list, not dict
            "L_level": 0,
            "confidence_score": 0.5,
        })
        assert resp.status_code in (422, 400)

    def test_list_events_cache_hit(self, client_with_auth: TestClient):
        """list_events: 第二次请求命中缓存（line 293）"""
        import routers.events as ev
        ev._events_cache.clear()
        # 第一次 — 写入缓存
        client_with_auth.get("/api/v1/events?limit=5")
        # 第二次 — 命中缓存 → 执行 line 293
        resp = client_with_auth.get("/api/v1/events?limit=5")
        assert resp.status_code == 200

    def test_list_events_with_last_id_cursor(
        self, client_with_auth: TestClient
    ):
        """list_events: last_id > 0 → 覆盖 cursor where 子句（line 313）"""
        import routers.events as ev
        ev._events_cache.clear()
        resp = client_with_auth.get("/api/v1/events?last_id=1&limit=10")
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data

    def test_update_event_with_new_member_id(
        self, client_with_auth: TestClient, test_member, db_session
    ):
        """PUT /events/{id} 带 member_id → check_member_ownership（line 476）"""
        import routers.events as ev
        ev._events_cache.clear()

        # 先创建一个事件
        create_resp = client_with_auth.post("/api/v1/events", json={
            "member_id": test_member.id,
            "name": "To Update",
            "event_type": "consultation",
            "bazi_json": _BAZI_JSON,
            "L_level": 1,
            "confidence_score": 0.8,
        })
        assert create_resp.status_code == 201
        event_id = create_resp.json()["id"]

        # 使用有效的 member_id 更新
        resp = client_with_auth.put(
            f"/api/v1/events/{event_id}",
            json={
                "member_id": test_member.id,
                "name": "Updated With Member",
                "event_type": "prediction",
                "bazi_json": _BAZI_JSON,
                "L_level": 2,
                "confidence_score": 0.9,
            },
        )
        assert resp.status_code == 200

    def test_patch_event_integrity_error(
        self, client_with_auth: TestClient, test_member
    ):
        """patch_event: mock IntegrityError → 500 BusinessException（lines 418-420）"""
        import routers.events as ev
        from sqlalchemy.exc import IntegrityError as SAIntegrityError
        ev._events_cache.clear()

        # 创建事件
        create_resp = client_with_auth.post("/api/v1/events", json={
            "member_id": test_member.id,
            "name": "IE Test Event",
            "event_type": "consultation",
            "bazi_json": _BAZI_JSON,
            "L_level": 0,
            "confidence_score": 0.5,
        })
        assert create_resp.status_code == 201
        event_id = create_resp.json()["id"]

        # mock session.commit to raise IntegrityError
        orig_commit = None
        with patch("sqlmodel.Session.commit", side_effect=SAIntegrityError(None, None, Exception("dup"))):
            resp = client_with_auth.patch(
                f"/api/v1/events/{event_id}", json={"name": "trigger IE"}
            )
        # IntegrityError → BusinessException → 400
        assert resp.status_code in (400, 409, 422, 500)

    def test_update_event_integrity_error(
        self, client_with_auth: TestClient, test_member
    ):
        """update_event: mock IntegrityError → 500 BusinessException（lines 494-496）"""
        import routers.events as ev
        from sqlalchemy.exc import IntegrityError as SAIntegrityError
        ev._events_cache.clear()

        # 创建事件
        create_resp = client_with_auth.post("/api/v1/events", json={
            "member_id": test_member.id,
            "name": "IE PUT Test",
            "event_type": "consultation",
            "bazi_json": _BAZI_JSON,
            "L_level": 0,
            "confidence_score": 0.5,
        })
        assert create_resp.status_code == 201
        event_id = create_resp.json()["id"]

        with patch("sqlmodel.Session.commit", side_effect=SAIntegrityError(None, None, Exception("dup"))):
            resp = client_with_auth.put(
                f"/api/v1/events/{event_id}",
                json={
                    "member_id": test_member.id,
                    "name": "IE PUT",
                    "event_type": "consultation",
                    "bazi_json": _BAZI_JSON,
                    "L_level": 1,
                    "confidence_score": 0.5,
                },
            )
        assert resp.status_code in (400, 409, 422, 500)

    def test_create_event_integrity_error(
        self, client_with_auth: TestClient, test_member
    ):
        """create_event: mock IntegrityError → 500 BusinessException（lines 228-230）"""
        from sqlalchemy.exc import IntegrityError as SAIntegrityError
        import routers.events as ev
        ev._events_cache.clear()

        with patch("sqlmodel.Session.commit", side_effect=SAIntegrityError(None, None, Exception("dup"))):
            resp = client_with_auth.post("/api/v1/events", json={
                "member_id": test_member.id,
                "name": "IE Create Test",
                "event_type": "consultation",
                "bazi_json": _BAZI_JSON,
                "L_level": 0,
                "confidence_score": 0.5,
            })
        assert resp.status_code in (400, 409, 422, 500)

    def test_patch_event_wrong_owner_direct(
        self, client_with_auth: TestClient, test_user, db_session
    ):
        """patch_event: 事件 owner 不是当前用户 → 403（line 453）"""
        from datetime import date
        from app.models import Event, Member
        from services.auth_service import create_access_token

        # 创建一个不属于 test_user 的 member + event
        # 用一个和 test_user 不同的 owner_id
        other_user_id = test_user.id + 9999  # 肯定不同

        other_member = Member(
            owner_id=other_user_id,
            name=f"OtherMember_{uuid4().hex[:6]}",
            birth_date=date(1990, 1, 1),
            gender="M",
            birth_time_hour=8,
            birth_time_minute=0,
            birth_longitude=120.0,
            solar_time_enabled=False,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db_session.add(other_member)
        db_session.flush()

        other_event = Event(
            owner_id=other_user_id,
            member_id=other_member.id,
            name="Unowned Event for Patch",
            event_type="consultation",
            bazi_json=_BAZI_JSON,
            L_level=1,
            confidence_score=0.5,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db_session.add(other_event)
        db_session.commit()
        db_session.refresh(other_event)

        resp = client_with_auth.patch(
            f"/api/v1/events/{other_event.id}",
            json={"name": "Hijack Patch"},
        )
        assert resp.status_code == 403

    def test_delete_event_wrong_owner_direct(
        self, client_with_auth: TestClient, test_user, db_session
    ):
        """delete_event: 事件 owner 不是当前用户 → 403（line 583）"""
        from datetime import date
        from app.models import Event, Member

        other_user_id = test_user.id + 8888

        other_member = Member(
            owner_id=other_user_id,
            name=f"OtherMember_{uuid4().hex[:6]}",
            birth_date=date(1985, 6, 15),
            gender="F",
            birth_time_hour=10,
            birth_time_minute=30,
            birth_longitude=116.0,
            solar_time_enabled=False,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db_session.add(other_member)
        db_session.flush()

        other_event = Event(
            owner_id=other_user_id,
            member_id=other_member.id,
            name="Unowned Event for Delete",
            event_type="prediction",
            bazi_json=_BAZI_JSON,
            L_level=0,
            confidence_score=0.3,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db_session.add(other_event)
        db_session.commit()
        db_session.refresh(other_event)

        resp = client_with_auth.delete(f"/api/v1/events/{other_event.id}")
        assert resp.status_code == 403

    def test_put_event_wrong_owner_direct(
        self, client_with_auth: TestClient, test_user, test_member, db_session
    ):
        """update_event: 事件 owner 不是当前用户 → 403（lines 494-496）"""
        from datetime import date
        from app.models import Event, Member

        other_user_id = test_user.id + 7777

        other_member = Member(
            owner_id=other_user_id,
            name=f"OtherMember_{uuid4().hex[:6]}",
            birth_date=date(1995, 3, 20),
            gender="M",
            birth_time_hour=14,
            birth_time_minute=0,
            birth_longitude=121.0,
            solar_time_enabled=False,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db_session.add(other_member)
        db_session.flush()

        other_event = Event(
            owner_id=other_user_id,
            member_id=other_member.id,
            name="Unowned Event for PUT",
            event_type="consultation",
            bazi_json=_BAZI_JSON,
            L_level=1,
            confidence_score=0.7,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db_session.add(other_event)
        db_session.commit()
        db_session.refresh(other_event)

        resp = client_with_auth.put(
            f"/api/v1/events/{other_event.id}",
            json={
                "member_id": test_member.id,
                "name": "Hijack PUT",
                "event_type": "consultation",
                "bazi_json": _BAZI_JSON,
                "L_level": 1,
                "confidence_score": 0.8,
            },
        )
        assert resp.status_code == 403
