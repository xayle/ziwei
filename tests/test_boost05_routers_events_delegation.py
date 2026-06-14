"""
Coverage Boost #5 — routers/events.py, routers/delegation.py, routers/relations.py (helpers)

目标：覆盖三个路由文件的大量缺失分支，预计将整体覆盖率从 91.6% 推向 93%+。
"""
import pytest
from datetime import datetime, timedelta, timezone
from uuid import uuid4
from unittest.mock import patch, MagicMock

from sqlmodel import Session as SQLModelSession
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Minimal valid bazi_json (passes EventJsonValidator.validate_bazi_json)
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
# TestEventsRouterCoverage
# ===========================================================================
class TestEventsRouterCoverage:
    """routers/events.py — 覆盖 CRUD 所有分支（lines 41-595）"""

    # ------------------------------------------------------------------
    # POST /events
    # ------------------------------------------------------------------

    def test_create_event_success_returns_201(
        self, client_with_auth: TestClient, test_member
    ):
        """成功创建事件 → 201"""
        resp = client_with_auth.post("/api/v1/events", json={
            "member_id": test_member.id,
            "name": "Boost5 Event",
            "event_type": "consultation",
            "bazi_json": _BAZI_JSON,
            "L_level": 1,
            "confidence_score": 0.9,
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "Boost5 Event"
        assert "id" in data

    def test_create_event_member_not_found_returns_404(
        self, client_with_auth: TestClient
    ):
        """成员不存在 → 404"""
        resp = client_with_auth.post("/api/v1/events", json={
            "member_id": 999991,
            "name": "NoMember Event",
            "event_type": "consultation",
            "bazi_json": _BAZI_JSON,
        })
        assert resp.status_code == 404

    def test_create_event_member_wrong_owner_returns_403(
        self, client: TestClient, admin_user, test_member
    ):
        """成员属于他人 → 403"""
        from services.auth_service import create_access_token
        td = create_access_token(user_id=admin_user.id, username=admin_user.username, role=admin_user.role)
        resp = client.post("/api/v1/events", json={
            "member_id": test_member.id,
            "name": "WrongOwner Event",
            "event_type": "consultation",
            "bazi_json": _BAZI_JSON,
        }, headers={"Authorization": f"Bearer {td['access_token']}"})
        assert resp.status_code == 403

    # ------------------------------------------------------------------
    # GET /events
    # ------------------------------------------------------------------

    def test_list_events_returns_200(
        self, client_with_auth: TestClient, test_event
    ):
        """列表 → 200"""
        resp = client_with_auth.get("/api/v1/events")
        assert resp.status_code == 200
        d = resp.json()
        assert "items" in d and "total" in d

    def test_list_events_with_member_id_filter(
        self, client_with_auth: TestClient, test_event, test_member
    ):
        """按 member_id 过滤 → 200"""
        resp = client_with_auth.get(f"/api/v1/events?member_id={test_member.id}")
        assert resp.status_code == 200

    def test_list_events_with_event_type_filter(
        self, client_with_auth: TestClient, test_event
    ):
        """按 event_type 过滤 → 200"""
        resp = client_with_auth.get("/api/v1/events?event_type=marriage")
        assert resp.status_code == 200

    def test_list_events_with_last_id(
        self, client_with_auth: TestClient, test_event
    ):
        """游标分页 last_id → 200"""
        resp = client_with_auth.get(f"/api/v1/events?last_id={test_event.id - 1}&limit=5")
        assert resp.status_code == 200

    def test_list_events_member_filter_wrong_owner_returns_403(
        self, client: TestClient, admin_user, test_member
    ):
        """member_id 属于他人 → 403"""
        from services.auth_service import create_access_token
        import routers.events as _events_router
        _events_router._events_cache.clear()  # 清除模块级缓存避免测试间污染
        td = create_access_token(user_id=admin_user.id, username=admin_user.username, role=admin_user.role)
        resp = client.get(f"/api/v1/events?member_id={test_member.id}",
                          headers={"Authorization": f"Bearer {td['access_token']}"})
        assert resp.status_code == 403

    # ------------------------------------------------------------------
    # GET /events/{id}
    # ------------------------------------------------------------------

    def test_get_event_success(
        self, client_with_auth: TestClient, test_event
    ):
        """成功获取单个事件 → 200"""
        resp = client_with_auth.get(f"/api/v1/events/{test_event.id}")
        assert resp.status_code == 200
        assert resp.json()["id"] == test_event.id

    def test_get_event_not_found_returns_404(
        self, client_with_auth: TestClient
    ):
        """事件不存在 → 404"""
        resp = client_with_auth.get("/api/v1/events/999991")
        assert resp.status_code == 404

    def test_get_event_wrong_owner_returns_403(
        self, client: TestClient, admin_user, test_event
    ):
        """事件属于他人 → 403"""
        from services.auth_service import create_access_token
        td = create_access_token(user_id=admin_user.id, username=admin_user.username, role=admin_user.role)
        resp = client.get(f"/api/v1/events/{test_event.id}",
                          headers={"Authorization": f"Bearer {td['access_token']}"})
        assert resp.status_code == 403

    # ------------------------------------------------------------------
    # PATCH /events/{id}
    # ------------------------------------------------------------------

    def test_patch_event_success(
        self, client_with_auth: TestClient, test_event
    ):
        """成功 PATCH 事件 → 200"""
        resp = client_with_auth.patch(f"/api/v1/events/{test_event.id}", json={
            "name": "Patched Event",
            "L_level": 2,
        })
        assert resp.status_code == 200
        assert resp.json()["name"] == "Patched Event"

    def test_patch_event_not_found_returns_404(
        self, client_with_auth: TestClient
    ):
        """事件不存在，PATCH → 404"""
        resp = client_with_auth.patch("/api/v1/events/999992", json={"name": "Ghost"})
        assert resp.status_code == 404

    def test_patch_event_wrong_owner_returns_403(
        self, client: TestClient, admin_user, test_event
    ):
        """事件属于他人，PATCH → 403"""
        from services.auth_service import create_access_token
        td = create_access_token(user_id=admin_user.id, username=admin_user.username, role=admin_user.role)
        resp = client.patch(f"/api/v1/events/{test_event.id}",
                            json={"name": "Hijack"},
                            headers={"Authorization": f"Bearer {td['access_token']}"})
        assert resp.status_code == 403

    # ------------------------------------------------------------------
    # PUT /events/{id}
    # ------------------------------------------------------------------

    def test_put_event_success(
        self, client_with_auth: TestClient, test_event, test_member
    ):
        """成功 PUT 事件 → 200"""
        resp = client_with_auth.put(f"/api/v1/events/{test_event.id}", json={
            "member_id": test_member.id,
            "name": "Updated Event",
            "event_type": "verification",
            "bazi_json": _BAZI_JSON,
            "L_level": 3,
            "confidence_score": 0.8,
        })
        assert resp.status_code == 200
        assert resp.json()["name"] == "Updated Event"

    def test_put_event_not_found_returns_404(
        self, client_with_auth: TestClient, test_member
    ):
        """事件不存在，PUT → 404"""
        resp = client_with_auth.put("/api/v1/events/999993", json={
            "member_id": test_member.id,
            "name": "Ghost",
            "event_type": "consultation",
            "bazi_json": _BAZI_JSON,
        })
        assert resp.status_code == 404

    def test_put_event_wrong_owner_returns_403(
        self, client: TestClient, admin_user, test_event, test_member
    ):
        """事件属于他人，PUT → 403"""
        from services.auth_service import create_access_token
        td = create_access_token(user_id=admin_user.id, username=admin_user.username, role=admin_user.role)
        resp = client.put(f"/api/v1/events/{test_event.id}", json={
            "member_id": test_member.id,
            "name": "Hijack",
            "event_type": "consultation",
            "bazi_json": _BAZI_JSON,
        }, headers={"Authorization": f"Bearer {td['access_token']}"})
        assert resp.status_code == 403

    # ------------------------------------------------------------------
    # DELETE /events/{id}
    # ------------------------------------------------------------------

    def test_delete_event_success_returns_204(
        self, client_with_auth: TestClient, test_event
    ):
        """成功删除事件 → 204"""
        resp = client_with_auth.delete(f"/api/v1/events/{test_event.id}")
        assert resp.status_code == 204

    def test_delete_event_not_found_returns_404(
        self, client_with_auth: TestClient
    ):
        """事件不存在，DELETE → 404"""
        resp = client_with_auth.delete("/api/v1/events/999994")
        assert resp.status_code == 404

    def test_delete_event_wrong_owner_returns_403(
        self, client: TestClient, admin_user, test_event
    ):
        """事件属于他人，DELETE → 403"""
        from services.auth_service import create_access_token
        td = create_access_token(user_id=admin_user.id, username=admin_user.username, role=admin_user.role)
        resp = client.delete(f"/api/v1/events/{test_event.id}",
                             headers={"Authorization": f"Bearer {td['access_token']}"})
        assert resp.status_code == 403

    # ------------------------------------------------------------------
    # GET /members/{member_id}/events
    # ------------------------------------------------------------------

    def test_list_member_events_success(
        self, client_with_auth: TestClient, test_event, test_member
    ):
        """列出特定成员的事件 → 200"""
        resp = client_with_auth.get(f"/api/v1/members/{test_member.id}/events")
        assert resp.status_code == 200
        data = resp.json()
        assert "events" in data
        assert data["total_returned"] >= 1

    def test_list_member_events_with_last_id(
        self, client_with_auth: TestClient, test_event, test_member
    ):
        """游标分页 last_id → 200"""
        resp = client_with_auth.get(
            f"/api/v1/members/{test_member.id}/events?last_id={test_event.id - 1}&limit=10"
        )
        assert resp.status_code == 200

    def test_list_member_events_member_not_found(
        self, client_with_auth: TestClient
    ):
        """成员不存在 → 404"""
        resp = client_with_auth.get("/api/v1/members/999995/events")
        assert resp.status_code == 404

    def test_list_member_events_wrong_owner_returns_403(
        self, client: TestClient, admin_user, test_member
    ):
        """成员属于他人 → 403"""
        from services.auth_service import create_access_token
        td = create_access_token(user_id=admin_user.id, username=admin_user.username, role=admin_user.role)
        resp = client.get(f"/api/v1/members/{test_member.id}/events",
                          headers={"Authorization": f"Bearer {td['access_token']}"})
        assert resp.status_code == 403


# ===========================================================================
# TestDelegationRouterCoverage
# ===========================================================================
class TestDelegationRouterCoverage:
    """routers/delegation.py — 委托 CRUD 和工作流端点（lines 65-525）"""

    # ------------------------------------------------------------------
    # POST /delegations
    # ------------------------------------------------------------------

    def test_create_delegation_to_nonexistent_user_returns_404(
        self, client_with_auth: TestClient
    ):
        """被授权用户不存在 → 404"""
        resp = client_with_auth.post("/api/v1/delegations", json={
            "to_user_id": 999991,
            "permission_type": "view",
        })
        assert resp.status_code == 404

    def test_create_delegation_to_self_returns_422(
        self, client_with_auth: TestClient, test_user
    ):
        """授权给自己 → 422"""
        resp = client_with_auth.post("/api/v1/delegations", json={
            "to_user_id": test_user.id,
            "permission_type": "view",
        })
        assert resp.status_code == 422

    def test_create_delegation_invalid_permission_type_returns_422(
        self, client_with_auth: TestClient, admin_user
    ):
        """无效 permission_type → 422"""
        resp = client_with_auth.post("/api/v1/delegations", json={
            "to_user_id": admin_user.id,
            "permission_type": "invalid_type",
        })
        assert resp.status_code == 422

    def test_create_delegation_success_returns_201(
        self, client_with_auth: TestClient, admin_user
    ):
        """成功创建委托 → 201"""
        resp = client_with_auth.post("/api/v1/delegations", json={
            "to_user_id": admin_user.id,
            "permission_type": "view",
            "expires_days": 7,
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["permission_type"] == "view"
        assert data["is_active"] is True

    # ------------------------------------------------------------------
    # GET /delegations/outgoing
    # ------------------------------------------------------------------

    def test_list_outgoing_delegations(
        self, client_with_auth: TestClient, test_delegation
    ):
        """列出我授予他人的委托 → 200"""
        resp = client_with_auth.get("/api/v1/delegations/outgoing")
        assert resp.status_code == 200
        data = resp.json()
        assert "delegations" in data
        assert "total" in data

    # ------------------------------------------------------------------
    # GET /delegations/incoming
    # ------------------------------------------------------------------

    def test_list_incoming_delegations(
        self, client: TestClient, admin_user, test_delegation
    ):
        """列出他人授予我的委托 → 200"""
        from services.auth_service import create_access_token
        td = create_access_token(user_id=admin_user.id, username=admin_user.username, role=admin_user.role)
        resp = client.get("/api/v1/delegations/incoming",
                          headers={"Authorization": f"Bearer {td['access_token']}"})
        assert resp.status_code == 200
        d = resp.json()
        assert "delegations" in d

    # ------------------------------------------------------------------
    # DELETE /delegations/{id}
    # ------------------------------------------------------------------

    def test_revoke_delegation_not_found_returns_404(
        self, client_with_auth: TestClient
    ):
        """委托不存在，DELETE → 404"""
        resp = client_with_auth.delete("/api/v1/delegations/999991")
        assert resp.status_code == 404

    def test_revoke_delegation_wrong_owner_returns_403(
        self, client: TestClient, admin_user, test_delegation
    ):
        """委托的授权方不是当前用户 → 403"""
        from services.auth_service import create_access_token
        td = create_access_token(user_id=admin_user.id, username=admin_user.username, role=admin_user.role)
        resp = client.delete(f"/api/v1/delegations/{test_delegation.id}",
                             headers={"Authorization": f"Bearer {td['access_token']}"})
        assert resp.status_code == 403

    def test_revoke_delegation_success_returns_204(
        self, client_with_auth: TestClient, test_delegation
    ):
        """成功撤销委托 → 204"""
        resp = client_with_auth.delete(f"/api/v1/delegations/{test_delegation.id}")
        assert resp.status_code == 204

    # ------------------------------------------------------------------
    # POST /permissions/request
    # ------------------------------------------------------------------

    def test_request_permission_invalid_type_returns_422(
        self, client_with_auth: TestClient
    ):
        """无效 permission_type → 422"""
        resp = client_with_auth.post("/api/v1/permissions/request", json={
            "permission_type": "super_admin",
        })
        assert resp.status_code == 422

    def test_request_permission_success_returns_201(
        self, client_with_auth: TestClient
    ):
        """成功发起权限申请 → 201"""
        resp = client_with_auth.post("/api/v1/permissions/request", json={
            "permission_type": "view",
            "expires_days": 14,
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["status"] == "pending"

    # ------------------------------------------------------------------
    # PUT /permissions/request/{id}/approve
    # ------------------------------------------------------------------

    def test_approve_request_not_found_returns_404(
        self, client: TestClient, admin_user
    ):
        """申请不存在，approve → 404"""
        from services.auth_service import create_access_token
        td = create_access_token(user_id=admin_user.id, username=admin_user.username, role=admin_user.role)
        resp = client.put("/api/v1/permissions/request/999991/approve",
                          json={},
                          headers={"Authorization": f"Bearer {td['access_token']}"})
        assert resp.status_code == 404

    def test_approve_request_self_approval_forbidden(
        self, client_with_auth: TestClient, db_session: SQLModelSession, test_user
    ):
        """自我审批 → 403"""
        from app.models import Delegation
        delegation = Delegation(
            from_user_id=0,
            to_user_id=test_user.id,
            permission_type="view",
            is_active=False,
            status="pending",
            requested_by=test_user.id,  # same as approver
        )
        db_session.add(delegation)
        db_session.commit()
        db_session.refresh(delegation)
        # test_user is not admin, but test_approve for admin scenario
        # Use admin_user to test self-approval with admin fixture would need another setup
        # Instead just confirm the 403 path: request where requested_by == approver
        # We need an admin token; use patch to make test_user is_admin
        test_user.is_admin = True
        db_session.add(test_user)
        db_session.commit()
        resp = client_with_auth.put(f"/api/v1/permissions/request/{delegation.id}/approve")
        assert resp.status_code == 403
        # Cleanup
        test_user.is_admin = False
        db_session.add(test_user)
        db_session.commit()

    def test_approve_request_success(
        self, client: TestClient, admin_user, db_session: SQLModelSession, test_user
    ):
        """成功批准申请 → 200"""
        from app.models import Delegation
        from services.auth_service import create_access_token
        delegation = Delegation(
            from_user_id=0,
            to_user_id=test_user.id,
            permission_type="view",
            is_active=False,
            status="pending",
            requested_by=test_user.id,
        )
        db_session.add(delegation)
        db_session.commit()
        db_session.refresh(delegation)
        td = create_access_token(user_id=admin_user.id, username=admin_user.username, role=admin_user.role)
        resp = client.put(f"/api/v1/permissions/request/{delegation.id}/approve",
                          json={},
                          headers={"Authorization": f"Bearer {td['access_token']}"})
        assert resp.status_code == 200
        assert resp.json()["status"] == "approved"

    def test_approve_already_approved_returns_409(
        self, client: TestClient, admin_user, db_session: SQLModelSession, test_user
    ):
        """重复审批 → 409"""
        from app.models import Delegation
        from services.auth_service import create_access_token
        delegation = Delegation(
            from_user_id=admin_user.id,
            to_user_id=test_user.id,
            permission_type="edit",
            is_active=True,
            status="approved",
            requested_by=test_user.id,
        )
        db_session.add(delegation)
        db_session.commit()
        db_session.refresh(delegation)
        td = create_access_token(user_id=admin_user.id, username=admin_user.username, role=admin_user.role)
        resp = client.put(f"/api/v1/permissions/request/{delegation.id}/approve",
                          json={},
                          headers={"Authorization": f"Bearer {td['access_token']}"})
        assert resp.status_code == 409

    # ------------------------------------------------------------------
    # PUT /permissions/request/{id}/reject
    # ------------------------------------------------------------------

    def test_reject_request_success(
        self, client: TestClient, admin_user, db_session: SQLModelSession, test_user
    ):
        """成功拒绝申请 → 200"""
        from app.models import Delegation
        from services.auth_service import create_access_token
        delegation = Delegation(
            from_user_id=0,
            to_user_id=test_user.id,
            permission_type="share",
            is_active=False,
            status="pending",
            requested_by=test_user.id,
        )
        db_session.add(delegation)
        db_session.commit()
        db_session.refresh(delegation)
        td = create_access_token(user_id=admin_user.id, username=admin_user.username, role=admin_user.role)
        resp = client.put(f"/api/v1/permissions/request/{delegation.id}/reject",
                          json={"reject_reason": "Not authorized at this time"},
                          headers={"Authorization": f"Bearer {td['access_token']}"})
        assert resp.status_code == 200
        assert resp.json()["status"] == "rejected"

    def test_reject_approved_request_returns_409(
        self, client: TestClient, admin_user, db_session: SQLModelSession, test_user
    ):
        """已批准申请不能 reject → 409"""
        from app.models import Delegation
        from services.auth_service import create_access_token
        delegation = Delegation(
            from_user_id=admin_user.id,
            to_user_id=test_user.id,
            permission_type="manage",
            is_active=True,
            status="approved",
            requested_by=test_user.id,
        )
        db_session.add(delegation)
        db_session.commit()
        db_session.refresh(delegation)
        td = create_access_token(user_id=admin_user.id, username=admin_user.username, role=admin_user.role)
        resp = client.put(f"/api/v1/permissions/request/{delegation.id}/reject",
                          json={},
                          headers={"Authorization": f"Bearer {td['access_token']}"})
        assert resp.status_code == 409

    def test_reject_request_not_found_returns_404(
        self, client: TestClient, admin_user
    ):
        """申请不存在，reject → 404"""
        from services.auth_service import create_access_token
        td = create_access_token(user_id=admin_user.id, username=admin_user.username, role=admin_user.role)
        resp = client.put("/api/v1/permissions/request/999992/reject",
                          json={},
                          headers={"Authorization": f"Bearer {td['access_token']}"})
        assert resp.status_code == 404

    # ------------------------------------------------------------------
    # DELETE /permissions/request/{id}/revoke
    # ------------------------------------------------------------------

    def test_revoke_approved_permission_success(
        self, client: TestClient, admin_user, db_session: SQLModelSession, test_user
    ):
        """成功撤销已批准权限 → 200"""
        from app.models import Delegation
        from services.auth_service import create_access_token
        delegation = Delegation(
            from_user_id=admin_user.id,
            to_user_id=test_user.id,
            permission_type="view",
            is_active=True,
            status="approved",
            requested_by=test_user.id,
        )
        db_session.add(delegation)
        db_session.commit()
        db_session.refresh(delegation)
        td = create_access_token(user_id=admin_user.id, username=admin_user.username, role=admin_user.role)
        resp = client.delete(f"/api/v1/permissions/request/{delegation.id}/revoke",
                             headers={"Authorization": f"Bearer {td['access_token']}"})
        assert resp.status_code == 200
        assert resp.json()["status"] == "revoked"

    def test_revoke_non_approved_returns_409(
        self, client: TestClient, admin_user, db_session: SQLModelSession, test_user
    ):
        """Pending 状态不能 revoke → 409"""
        from app.models import Delegation
        from services.auth_service import create_access_token
        delegation = Delegation(
            from_user_id=0,
            to_user_id=test_user.id,
            permission_type="edit",
            is_active=False,
            status="pending",
            requested_by=test_user.id,
        )
        db_session.add(delegation)
        db_session.commit()
        db_session.refresh(delegation)
        td = create_access_token(user_id=admin_user.id, username=admin_user.username, role=admin_user.role)
        resp = client.delete(f"/api/v1/permissions/request/{delegation.id}/revoke",
                             headers={"Authorization": f"Bearer {td['access_token']}"})
        assert resp.status_code == 409

    def test_revoke_not_found_returns_404(
        self, client: TestClient, admin_user
    ):
        """委托不存在，revoke → 404"""
        from services.auth_service import create_access_token
        td = create_access_token(user_id=admin_user.id, username=admin_user.username, role=admin_user.role)
        resp = client.delete("/api/v1/permissions/request/999993/revoke",
                             headers={"Authorization": f"Bearer {td['access_token']}"})
        assert resp.status_code == 404

    def test_non_admin_cannot_approve(
        self, client_with_auth: TestClient, db_session: SQLModelSession, test_user
    ):
        """非 admin / 无 manage delegation 的用户 approve → 403"""
        from app.models import Delegation
        delegation = Delegation(
            from_user_id=0,
            to_user_id=99,
            permission_type="view",
            is_active=False,
            status="pending",
            requested_by=99,
        )
        db_session.add(delegation)
        db_session.commit()
        db_session.refresh(delegation)
        resp = client_with_auth.put(f"/api/v1/permissions/request/{delegation.id}/approve")
        assert resp.status_code == 403


# ===========================================================================
# TestRelationsHelpers
# ===========================================================================
class TestRelationsHelpers:
    """routers/relations.py 纯函数单元测试（lines 65-240）"""

    def test_parse_dt_local_valid(self):
        """正常解析 ISO8601 naive datetime"""
        from routers.relations import _parse_dt_local
        dt = _parse_dt_local("2000-05-15T12:00:00", "Asia/Shanghai")
        assert dt.year == 2000
        assert dt.tzinfo is not None

    def test_parse_dt_local_invalid_string_raises_422(self):
        """无效 datetime 字符串 → ValidationException"""
        from routers.relations import _parse_dt_local
        from app.exceptions import ValidationException
        with pytest.raises(ValidationException):
            _parse_dt_local("not-a-date", "Asia/Shanghai")

    def test_parse_dt_local_aware_datetime_raises_422(self):
        """带时区的 datetime → ValidationException（必须是 naive）"""
        from routers.relations import _parse_dt_local
        from app.exceptions import ValidationException
        with pytest.raises(ValidationException):
            _parse_dt_local("2000-05-15T12:00:00+08:00", "Asia/Shanghai")

    def test_extract_branches_with_full_pillars(self):
        """提取四柱地支"""
        from routers.relations import _extract_branches
        payload = {
            "pillars_primary": {
                "year": {"branch": "子"},
                "month": {"branch": "丑"},
                "day": {"branch": "寅"},
                "hour": {"branch": "卯"},
            }
        }
        branches = _extract_branches(payload)
        assert branches == ["子", "丑", "寅", "卯"]

    def test_extract_branches_missing_pillars(self):
        """缺少地支字段 → 空列表"""
        from routers.relations import _extract_branches
        branches = _extract_branches({})
        assert branches == []

    def test_build_profile_with_wuxing_and_yongshen(self):
        """构建 RelationProfile（含五行分数和用神）"""
        from routers.relations import _build_profile
        from app.models import Case
        case = Case(id="test_case_1", name="TestCase", gender="M",
                    birth_dt_local="2000-01-01T12:00:00", tz="Asia/Shanghai",
                    birth_dt="2000-01-01T04:00:00Z", lon=121.0, owner_id=1)
        payload = {
            "wuxing_score": {"wood": 30, "fire": 20, "earth": 15, "metal": 25, "water": 10},
            "yongshen": {"favor": ["fire", "wood"], "avoid": ["water"]},
        }
        profile = _build_profile(case, payload)
        assert profile.dominant_element == "wood"
        assert "fire" in profile.yongshen_favor
        assert "water" in profile.yongshen_avoid

    def test_build_profile_empty_payload(self):
        """空 payload → profile 有默认值"""
        from routers.relations import _build_profile
        from app.models import Case
        case = Case(id="test_case_2", name="Empty", gender="F",
                    birth_dt_local="1990-01-01T08:00:00", tz="Asia/Shanghai",
                    birth_dt="1990-01-01T00:00:00Z", lon=116.0, owner_id=1)
        profile = _build_profile(case, {})
        assert profile.dominant_element is None
        assert profile.yongshen_favor == []

    def test_score_elements_supports_and_conflicts(self):
        """_score_elements 产生 support 和 conflict points"""
        from routers.relations import _score_elements
        from app.schemas import RelationProfile
        a = RelationProfile(case_id="a", name="A", dominant_element="fire",
                            yongshen_favor=["fire"], yongshen_avoid=["water"],
                            wuxing_score={"wood": 20, "fire": 40, "earth": 10, "metal": 15, "water": 15})
        b = RelationProfile(case_id="b", name="B", dominant_element="water",
                            yongshen_favor=["fire", "wood"], yongshen_avoid=["metal"],
                            wuxing_score={"wood": 18, "fire": 38, "earth": 12, "metal": 17, "water": 15})
        supports, conflicts = _score_elements(a, b)
        # fire (a.dominant) is in b.yongshen_favor → support
        assert any(p.tag == "favor" for p in supports)

    def test_score_elements_shared_favor_and_avoid(self):
        """共同喜用 / 共同忌神"""
        from routers.relations import _score_elements
        from app.schemas import RelationProfile
        a = RelationProfile(case_id="c", name="C", dominant_element="metal",
                            yongshen_favor=["earth", "metal"], yongshen_avoid=["wood"],
                            wuxing_score={"wood": 5, "fire": 10, "earth": 30, "metal": 40, "water": 15})
        b = RelationProfile(case_id="d", name="D", dominant_element="earth",
                            yongshen_favor=["earth", "fire"], yongshen_avoid=["wood"],
                            wuxing_score={"wood": 5, "fire": 15, "earth": 35, "metal": 35, "water": 10})
        supports, conflicts = _score_elements(a, b)
        assert any(p.tag == "shared_favor" for p in supports)
        assert any(p.tag == "shared_avoid" for p in conflicts)

    def test_score_branches_clash(self):
        """地支相冲"""
        from routers.relations import _score_branches
        supports, conflicts = _score_branches(["子"], ["午"])
        assert any(p.tag == "clash" for p in conflicts)

    def test_score_branches_harm(self):
        """地支相害"""
        from routers.relations import _score_branches
        supports, conflicts = _score_branches(["子"], ["未"])
        assert any(p.tag == "harm" for p in conflicts)

    def test_score_branches_combine(self):
        """地支六合"""
        from routers.relations import _score_branches
        supports, conflicts = _score_branches(["子"], ["丑"])
        assert any(p.tag == "combine" for p in supports)

    def test_score_branches_no_interaction(self):
        """无特殊关系 → 空列表"""
        from routers.relations import _score_branches
        supports, conflicts = _score_branches(["甲"], ["乙"])
        assert supports == [] and conflicts == []

    def test_aggregate_score_couple_nudge(self):
        """couple 关系正向加成"""
        from routers.relations import _aggregate_score
        from app.schemas import RelationPoint
        supports = [RelationPoint(tag="favor", detail="test", weight=10)]
        conflicts = []
        score, summary = _aggregate_score(supports, conflicts, "couple")
        assert score > 60  # base(60) + 10 + 2 = 72

    def test_aggregate_score_clamped_at_100(self):
        """分数不超过 100"""
        from routers.relations import _aggregate_score
        from app.schemas import RelationPoint
        supports = [RelationPoint(tag="favor", detail="x", weight=100)]
        conflicts = []
        score, _ = _aggregate_score(supports, conflicts, "friend")
        assert score == 100.0

    def test_aggregate_score_clamped_at_0(self):
        """分数不低于 0"""
        from routers.relations import _aggregate_score
        from app.schemas import RelationPoint
        supports = []
        conflicts = [RelationPoint(tag="clash", detail="x", weight=-100)]
        score, _ = _aggregate_score(supports, conflicts, "rival")
        assert score == 0.0

    def test_compute_relation_full_pipeline(self):
        """_compute_relation 完整流水线"""
        from routers.relations import _compute_relation
        from app.schemas import RelationProfile
        pa = RelationProfile(case_id="e", name="E", dominant_element="fire",
                             yongshen_favor=["fire"], yongshen_avoid=["water"],
                             wuxing_score={"wood": 20, "fire": 40, "earth": 10, "metal": 15, "water": 15})
        pb = RelationProfile(case_id="f", name="F", dominant_element="water",
                             yongshen_favor=["water"], yongshen_avoid=["fire"],
                             wuxing_score={"wood": 20, "fire": 10, "earth": 20, "metal": 30, "water": 20})
        result = _compute_relation(pa, pb, ["子", "午"], ["午", "子"], "couple")
        assert 0 <= result.compatibility_score <= 100
        assert result.relation_type == "couple"
        assert result.advice  # 非空

    # ------------------------------------------------------------------
    # POST /relations/compat — 端点测试（基本路径）
    # ------------------------------------------------------------------

    def test_compat_same_case_id_returns_422(
        self, client_with_auth: TestClient, test_case
    ):
        """case_a_id == case_b_id → 422"""
        resp = client_with_auth.post("/api/v1/relations/compat", json={
            "case_a_id": test_case.id,
            "case_b_id": test_case.id,
            "relation_type": "couple",
        })
        assert resp.status_code == 422

    def test_compat_case_not_found_returns_404(
        self, client_with_auth: TestClient, test_case
    ):
        """其中一个 case 不存在 → 404"""
        resp = client_with_auth.post("/api/v1/relations/compat", json={
            "case_a_id": test_case.id,
            "case_b_id": "nonexistent_case_id_xyz",
            "relation_type": "couple",
        })
        assert resp.status_code == 404
