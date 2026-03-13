"""
Coverage Boost #4 — routers/auth.py, routers/scenarios.py, routers/members.py

目标：覆盖三个路由文件的大量缺失分支，预计将整体覆盖率从 89.8% 推向 91%+。

使用 conftest.py 提供的 fixtures（client, client_with_auth, test_user,
admin_user, test_member, test_scenario, db_session, access_token, refresh_token）。
"""
import os
import pytest
from datetime import datetime, timedelta, timezone
from uuid import uuid4
from unittest.mock import patch

from sqlmodel import Session as SQLModelSession
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# TestAuthRouterCoverage
# ---------------------------------------------------------------------------

class TestAuthRouterCoverage:
    """routers/auth.py — 覆盖缺失的登录/注册/刷新/登出/改密码路径"""

    # ------------------------------------------------------------------
    # get_current_user_from_token 分支
    # ------------------------------------------------------------------

    def test_no_header_bypass_enabled_returns_user_id_zero(self, client: TestClient):
        """bypass 开启 + 无 Authorization header → user_id=0 → 404 (user not in DB)"""
        with patch("routers.auth._auth_bypass_enabled", return_value=True):
            resp = client.get("/api/v1/auth/me")
        assert resp.status_code == 404

    def test_no_header_bypass_disabled_returns_401(self, client: TestClient):
        """bypass 关闭 + 无 Authorization header → 401"""
        with patch("routers.auth._auth_bypass_enabled", return_value=False):
            resp = client.get("/api/v1/auth/me")
        assert resp.status_code == 401

    def test_malformed_bearer_format_returns_401(self, client: TestClient):
        """Authorization header 格式非 'Bearer <token>' → 401"""
        resp = client.get("/api/v1/auth/me", headers={"Authorization": "NotBearerFormat"})
        assert resp.status_code == 401

    def test_bearer_wrong_scheme_returns_401(self, client: TestClient):
        """Authorization 使用非 bearer scheme → 401"""
        resp = client.get("/api/v1/auth/me", headers={"Authorization": "Basic dXNlcjpwYXNz"})
        assert resp.status_code == 401

    def test_invalid_jwt_token_returns_401(self, client: TestClient):
        """Bearer 格式正确但 token 无效 → verify_token 返回 None → 401"""
        resp = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer invalid.jwt.token"})
        assert resp.status_code == 401

    # ------------------------------------------------------------------
    # POST /auth/login
    # ------------------------------------------------------------------

    def test_login_user_not_found_returns_401(self, client: TestClient):
        """用户名不存在 → 401"""
        resp = client.post("/api/v1/auth/login", json={
            "username": "no_such_user_xyz",
            "password": "Password123",
        })
        assert resp.status_code == 401

    def test_login_wrong_password_returns_401(self, client: TestClient, test_user):
        """密码错误 → 401"""
        resp = client.post("/api/v1/auth/login", json={
            "username": test_user.username,
            "password": "WrongPassword99",
        })
        assert resp.status_code == 401

    def test_login_inactive_user_returns_401(
        self, client: TestClient, test_user, db_session: SQLModelSession
    ):
        """用户已停用 → 401"""
        test_user.is_active = False
        db_session.add(test_user)
        db_session.commit()
        resp = client.post("/api/v1/auth/login", json={
            "username": test_user.username,
            "password": "test_password_123!",
        })
        assert resp.status_code == 401

    # ------------------------------------------------------------------
    # POST /auth/register
    # ------------------------------------------------------------------

    def test_register_success_returns_tokens(self, client: TestClient):
        """新用户注册 → 200，返回 access_token"""
        resp = client.post("/api/v1/auth/register", json={
            "username": "newreg_boost4",
            "email": "newreg_boost4@example.com",
            "password": "Passw0rd1",
        })
        assert resp.status_code == 200
        assert "access_token" in resp.json()

    def test_register_duplicate_username_returns_409(
        self, client: TestClient, test_user
    ):
        """重复用户名 → 409"""
        resp = client.post("/api/v1/auth/register", json={
            "username": test_user.username,
            "email": "unique99@boost4.com",
            "password": "Passw0rd1",
        })
        assert resp.status_code == 409

    def test_register_duplicate_email_returns_409(
        self, client: TestClient, test_user
    ):
        """重复邮箱 → 409"""
        resp = client.post("/api/v1/auth/register", json={
            "username": "unique_boost4",
            "email": test_user.email,
            "password": "Passw0rd1",
        })
        assert resp.status_code == 409

    # ------------------------------------------------------------------
    # GET /auth/me
    # ------------------------------------------------------------------

    def test_get_me_returns_user_info(self, client_with_auth: TestClient):
        """正常获取当前用户信息 → 200"""
        resp = client_with_auth.get("/api/v1/auth/me")
        assert resp.status_code == 200
        data = resp.json()
        assert "user_id" in data
        assert "username" in data
        assert "role" in data

    def test_get_me_user_not_in_db_returns_404(self, client: TestClient):
        """Token 有效但 user_id 不在数据库中 → 404"""
        from services.auth_service import create_access_token
        token_data = create_access_token(user_id=99991, username="ghost_user", role="owner")
        headers = {"Authorization": f"Bearer {token_data['access_token']}"}
        resp = client.get("/api/v1/auth/me", headers=headers)
        assert resp.status_code == 404

    # ------------------------------------------------------------------
    # POST /auth/refresh
    # ------------------------------------------------------------------

    def test_refresh_token_success(
        self, client: TestClient, test_user, refresh_token: str
    ):
        """有效 refresh token → 200，返回新 tokens"""
        resp = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert "refresh_token" in data

    def test_refresh_token_invalid_returns_401(self, client: TestClient):
        """无效 refresh token → 401"""
        resp = client.post("/api/v1/auth/refresh", json={"refresh_token": "fake_token_does_not_exist"})
        assert resp.status_code == 401

    def test_refresh_token_expired_returns_401(
        self, client: TestClient, test_user, db_session: SQLModelSession
    ):
        """已过期 refresh token → 401"""
        from app.models import RefreshToken
        token_val = f"expired_{uuid4().hex}"
        rt = RefreshToken(
            user_id=test_user.id,
            token=token_val,
            expires_at=datetime.now(timezone.utc) - timedelta(days=1),
            is_revoked=False,
        )
        db_session.add(rt)
        db_session.commit()
        resp = client.post("/api/v1/auth/refresh", json={"refresh_token": token_val})
        assert resp.status_code == 401

    def test_refresh_token_revoked_returns_401(
        self, client: TestClient, test_user, db_session: SQLModelSession
    ):
        """已撤销 refresh token → 401"""
        from app.models import RefreshToken
        token_val = f"revoked_{uuid4().hex}"
        rt = RefreshToken(
            user_id=test_user.id,
            token=token_val,
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
            is_revoked=True,
        )
        db_session.add(rt)
        db_session.commit()
        resp = client.post("/api/v1/auth/refresh", json={"refresh_token": token_val})
        assert resp.status_code == 401

    def test_refresh_token_inactive_user_returns_401(
        self, client: TestClient, test_user, db_session: SQLModelSession
    ):
        """Refresh Token 有效但用户已停用 → 401"""
        from app.models import RefreshToken
        # 先停用用户
        test_user.is_active = False
        db_session.add(test_user)
        db_session.flush()
        # 创建有效 refresh token
        token_val = f"inactive_{uuid4().hex}"
        rt = RefreshToken(
            user_id=test_user.id,
            token=token_val,
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
            is_revoked=False,
        )
        db_session.add(rt)
        db_session.commit()
        resp = client.post("/api/v1/auth/refresh", json={"refresh_token": token_val})
        assert resp.status_code == 401

    # ------------------------------------------------------------------
    # POST /auth/logout
    # ------------------------------------------------------------------

    def test_logout_with_valid_bearer_returns_204(
        self, client_with_auth: TestClient, refresh_token: str
    ):
        """携带有效 Bearer + refresh token 登出 → 204（覆盖 JTI 撤销和 refresh_token 撤销）"""
        resp = client_with_auth.post("/api/v1/auth/logout", json={"refresh_token": refresh_token})
        assert resp.status_code == 204

    def test_logout_without_bearer_header_returns_204(
        self, client: TestClient, refresh_token: str
    ):
        """无 Authorization header 登出（只撤销 refresh token）→ 204"""
        with patch("routers.auth._auth_bypass_enabled", return_value=False):
            resp = client.post("/api/v1/auth/logout", json={"refresh_token": refresh_token})
        assert resp.status_code == 204

    def test_logout_with_invalid_bearer_still_returns_204(
        self, client: TestClient, refresh_token: str
    ):
        """无效 Bearer token 登出 → JTI 解码失败，记录 warning，仍返回 204"""
        resp = client.post(
            "/api/v1/auth/logout",
            json={"refresh_token": refresh_token},
            headers={"Authorization": "Bearer totally.invalid.jwt"},
        )
        assert resp.status_code == 204

    def test_logout_nonexistent_refresh_token_returns_204(
        self, client_with_auth: TestClient
    ):
        """Refresh token 不存在 → revoke 失败但仍返回 204"""
        resp = client_with_auth.post("/api/v1/auth/logout", json={"refresh_token": "nonexistent_rt"})
        assert resp.status_code == 204

    # ------------------------------------------------------------------
    # POST /auth/change-password
    # ------------------------------------------------------------------

    def test_change_password_success(self, client_with_auth: TestClient):
        """成功改密码 → 200"""
        resp = client_with_auth.post("/api/v1/auth/change-password", json={
            "old_password": "test_password_123!",
            "new_password": "NewPass456",
        })
        assert resp.status_code == 200
        assert "message" in resp.json()

    def test_change_password_wrong_old_password_returns_401(
        self, client_with_auth: TestClient
    ):
        """旧密码错误 → 401"""
        resp = client_with_auth.post("/api/v1/auth/change-password", json={
            "old_password": "definitely_wrong",
            "new_password": "NewPass456",
        })
        assert resp.status_code == 401

    def test_change_password_same_passwords_returns_422(
        self, client_with_auth: TestClient
    ):
        """新旧密码相同 → 422"""
        resp = client_with_auth.post("/api/v1/auth/change-password", json={
            "old_password": "test_password_123!",
            "new_password": "test_password_123!",
        })
        assert resp.status_code == 422

    def test_change_password_user_not_in_db_returns_404(self, client: TestClient):
        """Token 有效但 user_id 不在数据库中 → 404"""
        from services.auth_service import create_access_token
        token_data = create_access_token(user_id=99992, username="ghost2", role="owner")
        headers = {"Authorization": f"Bearer {token_data['access_token']}"}
        resp = client.post(
            "/api/v1/auth/change-password",
            json={"old_password": "OldPass1x", "new_password": "NewPass2x"},
            headers=headers,
        )
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# TestScenariosRouterCoverage
# ---------------------------------------------------------------------------

class TestScenariosRouterCoverage:
    """routers/scenarios.py — 覆盖 CRUD 错误路径"""

    # ------------------------------------------------------------------
    # check_member_ownership 分支 (lines 58–66)
    # ------------------------------------------------------------------

    def test_create_scenario_member_not_found_returns_404(
        self, client_with_auth: TestClient
    ):
        """member 不存在 → 404"""
        resp = client_with_auth.post("/api/v1/scenarios", json={
            "base_member_id": 999991,
            "name": "Orphan Scenario",
            "scenario_type": "custom",
        })
        assert resp.status_code == 404

    def test_create_scenario_member_wrong_owner_returns_403(
        self,
        client: TestClient,
        admin_user,
        test_member,
    ):
        """member 属于他人 → 403"""
        from services.auth_service import create_access_token
        token_data = create_access_token(
            user_id=admin_user.id, username=admin_user.username, role=admin_user.role
        )
        headers = {"Authorization": f"Bearer {token_data['access_token']}"}
        resp = client.post("/api/v1/scenarios", json={
            "base_member_id": test_member.id,
            "name": "WrongOwner Scenario",
            "scenario_type": "custom",
        }, headers=headers)
        assert resp.status_code == 403

    # ------------------------------------------------------------------
    # POST /scenarios — 权限检查 + 创建成功
    # ------------------------------------------------------------------

    def test_create_scenario_viewer_role_returns_403(
        self, client: TestClient, db_session: SQLModelSession
    ):
        """viewer 角色无 CREATE_SCENARIO 权限 → 403"""
        import services.auth_service as _auth_svc
        from app.models import User
        viewer = User(
            username="viewer_scenario_test",
            email="viewer_scenario@test.com",
            password_hash=_auth_svc.hash_password("Passw0rd1"),
            role="viewer",
            is_active=True,
            is_admin=False,
        )
        db_session.add(viewer)
        db_session.commit()
        db_session.refresh(viewer)
        token_data = _auth_svc.create_access_token(
            user_id=viewer.id, username=viewer.username, role=viewer.role
        )
        headers = {"Authorization": f"Bearer {token_data['access_token']}"}
        resp = client.post("/api/v1/scenarios", json={
            "base_member_id": 1,
            "name": "Viewer Scenario",
            "scenario_type": "custom",
        }, headers=headers)
        assert resp.status_code == 403

    def test_create_scenario_success_returns_201(
        self, client_with_auth: TestClient, test_member
    ):
        """成功创建场景 → 201"""
        resp = client_with_auth.post("/api/v1/scenarios", json={
            "base_member_id": test_member.id,
            "name": "Boost4 Scenario",
            "scenario_type": "comparison",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "Boost4 Scenario"
        assert "id" in data

    # ------------------------------------------------------------------
    # GET /scenarios
    # ------------------------------------------------------------------

    def test_list_scenarios_returns_200(self, client_with_auth: TestClient):
        """列表查询 → 200，包含 items / total / next_cursor"""
        resp = client_with_auth.get("/api/v1/scenarios")
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert "total" in data

    def test_list_scenarios_with_filters(
        self, client_with_auth: TestClient, test_member
    ):
        """带 member_id 和 scenario_type 过滤的列表查询"""
        resp = client_with_auth.get(
            f"/api/v1/scenarios?member_id={test_member.id}&scenario_type=comparison"
        )
        assert resp.status_code == 200

    # ------------------------------------------------------------------
    # GET /scenarios/{id}
    # ------------------------------------------------------------------

    def test_get_scenario_not_found_returns_404(self, client_with_auth: TestClient):
        """场景不存在 → 404"""
        resp = client_with_auth.get("/api/v1/scenarios/999991")
        assert resp.status_code == 404

    def test_get_scenario_wrong_owner_returns_403(
        self,
        client: TestClient,
        admin_user,
        test_scenario,
    ):
        """场景属于他人 → 403"""
        from services.auth_service import create_access_token
        token_data = create_access_token(
            user_id=admin_user.id, username=admin_user.username, role=admin_user.role
        )
        headers = {"Authorization": f"Bearer {token_data['access_token']}"}
        resp = client.get(f"/api/v1/scenarios/{test_scenario.id}", headers=headers)
        assert resp.status_code == 403

    def test_get_scenario_success(self, client_with_auth: TestClient, test_scenario):
        """成功获取场景 → 200"""
        resp = client_with_auth.get(f"/api/v1/scenarios/{test_scenario.id}")
        assert resp.status_code == 200
        assert resp.json()["id"] == test_scenario.id

    # ------------------------------------------------------------------
    # PUT /scenarios/{id}
    # ------------------------------------------------------------------

    def test_update_scenario_success(
        self, client_with_auth: TestClient, test_scenario
    ):
        """成功更新场景 → 200"""
        resp = client_with_auth.put(f"/api/v1/scenarios/{test_scenario.id}", json={
            "name": "Updated Scenario Name",
            "scenario_type": "comparison",
        })
        assert resp.status_code == 200
        assert resp.json()["name"] == "Updated Scenario Name"

    def test_update_scenario_not_found_returns_404(self, client_with_auth: TestClient):
        """场景不存在 → 404"""
        resp = client_with_auth.put("/api/v1/scenarios/999992", json={
            "name": "Ghost Update",
        })
        assert resp.status_code == 404

    def test_update_scenario_wrong_owner_returns_403(
        self,
        client: TestClient,
        admin_user,
        test_scenario,
    ):
        """场景属于他人，PUT → 403"""
        from services.auth_service import create_access_token
        token_data = create_access_token(
            user_id=admin_user.id, username=admin_user.username, role=admin_user.role
        )
        headers = {"Authorization": f"Bearer {token_data['access_token']}"}
        resp = client.put(f"/api/v1/scenarios/{test_scenario.id}", json={
            "name": "Hijacked"
        }, headers=headers)
        assert resp.status_code == 403

    # ------------------------------------------------------------------
    # DELETE /scenarios/{id}
    # ------------------------------------------------------------------

    def test_delete_scenario_success_returns_204(
        self, client_with_auth: TestClient, test_scenario
    ):
        """成功删除场景 → 204"""
        resp = client_with_auth.delete(f"/api/v1/scenarios/{test_scenario.id}")
        assert resp.status_code == 204

    def test_delete_scenario_not_found_returns_404(self, client_with_auth: TestClient):
        """场景不存在，DELETE → 404"""
        resp = client_with_auth.delete("/api/v1/scenarios/999993")
        assert resp.status_code == 404

    def test_delete_scenario_wrong_owner_returns_403(
        self,
        client: TestClient,
        admin_user,
        test_scenario,
    ):
        """场景属于他人，DELETE → 403"""
        from services.auth_service import create_access_token
        token_data = create_access_token(
            user_id=admin_user.id, username=admin_user.username, role=admin_user.role
        )
        headers = {"Authorization": f"Bearer {token_data['access_token']}"}
        resp = client.delete(f"/api/v1/scenarios/{test_scenario.id}", headers=headers)
        assert resp.status_code == 403

    # ------------------------------------------------------------------
    # GET /members/{member_id}/scenarios
    # ------------------------------------------------------------------

    def test_list_member_scenarios_success(
        self, client_with_auth: TestClient, test_member
    ):
        """列出特定成员的场景 → 200"""
        resp = client_with_auth.get(f"/api/v1/members/{test_member.id}/scenarios")
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data

    def test_list_member_scenarios_member_not_found(
        self, client_with_auth: TestClient
    ):
        """成员不存在 → 404"""
        resp = client_with_auth.get("/api/v1/members/999994/scenarios")
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# TestMembersRouterCoverage
# ---------------------------------------------------------------------------

class TestMembersRouterCoverage:
    """routers/members.py — 覆盖 CRUD 错误路径（lines 55-66, 87-123）"""

    # ------------------------------------------------------------------
    # POST /members
    # ------------------------------------------------------------------

    def test_create_member_success_returns_201(self, client_with_auth: TestClient):
        """成功创建成员 → 201"""
        resp = client_with_auth.post("/api/v1/members", json={
            "name": "Boost4 Member",
            "birth_date": "1990-05-15",
            "gender": "M",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "Boost4 Member"
        assert data["birth_time"] is None

    def test_create_member_with_birth_time_shorthand(self, client_with_auth: TestClient):
        """使用 'HH:MM' 便捷格式创建成员 → 201"""
        resp = client_with_auth.post("/api/v1/members", json={
            "name": "BirthTime Member",
            "birth_date": "1985-08-20",
            "gender": "F",
            "birth_time": "14:30",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["birth_time"] == "14:30"
        assert data["birth_time_hour"] == 14
        assert data["birth_time_minute"] == 30

    def test_create_member_no_permission_viewer(
        self, client: TestClient, db_session: SQLModelSession
    ):
        """viewer 角色无 CREATE_MEMBER 权限 → 403"""
        import services.auth_service as _auth_svc
        from app.models import User
        viewer = User(
            username="viewer_member_test",
            email="viewer_member@test.com",
            password_hash=_auth_svc.hash_password("Passw0rd1"),
            role="viewer",
            is_active=True,
            is_admin=False,
        )
        db_session.add(viewer)
        db_session.commit()
        db_session.refresh(viewer)
        token_data = _auth_svc.create_access_token(
            user_id=viewer.id, username=viewer.username, role=viewer.role
        )
        headers = {"Authorization": f"Bearer {token_data['access_token']}"}
        resp = client.post("/api/v1/members", json={
            "name": "ShouldFail",
            "birth_date": "1990-01-01",
            "gender": "M",
        }, headers=headers)
        assert resp.status_code == 403

    # ------------------------------------------------------------------
    # GET /members
    # ------------------------------------------------------------------

    def test_list_members_success(
        self, client_with_auth: TestClient, test_member
    ):
        """列出成员 → 200"""
        resp = client_with_auth.get("/api/v1/members")
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert "total" in data
        assert data["total"] >= 1

    def test_list_members_with_last_id(
        self, client_with_auth: TestClient, test_member
    ):
        """游标分页 last_id 参数 → 200"""
        resp = client_with_auth.get(f"/api/v1/members?last_id={test_member.id - 1}")
        assert resp.status_code == 200

    # ------------------------------------------------------------------
    # GET /members/{id}
    # ------------------------------------------------------------------

    def test_get_member_not_found_returns_404(self, client_with_auth: TestClient):
        """成员不存在 → 404"""
        resp = client_with_auth.get("/api/v1/members/999991")
        assert resp.status_code == 404

    def test_get_member_wrong_owner_returns_403(
        self,
        client: TestClient,
        admin_user,
        test_member,
    ):
        """成员属于他人 → 403"""
        from services.auth_service import create_access_token
        token_data = create_access_token(
            user_id=admin_user.id, username=admin_user.username, role=admin_user.role
        )
        headers = {"Authorization": f"Bearer {token_data['access_token']}"}
        resp = client.get(f"/api/v1/members/{test_member.id}", headers=headers)
        assert resp.status_code == 403

    # ------------------------------------------------------------------
    # PUT /members/{id}
    # ------------------------------------------------------------------

    def test_update_member_success_returns_200(
        self, client_with_auth: TestClient, test_member
    ):
        """成功更新成员 → 200"""
        resp = client_with_auth.put(f"/api/v1/members/{test_member.id}", json={
            "name": "Updated Member",
            "birth_date": "2000-01-01",
            "gender": "F",
        })
        assert resp.status_code == 200
        assert resp.json()["name"] == "Updated Member"

    def test_update_member_not_found_returns_404(self, client_with_auth: TestClient):
        """成员不存在，PUT → 404"""
        resp = client_with_auth.put("/api/v1/members/999992", json={
            "name": "Ghost",
            "birth_date": "2000-01-01",
            "gender": "M",
        })
        assert resp.status_code == 404

    def test_update_member_wrong_owner_returns_403(
        self,
        client: TestClient,
        admin_user,
        test_member,
    ):
        """成员属于他人，PUT → 403"""
        from services.auth_service import create_access_token
        token_data = create_access_token(
            user_id=admin_user.id, username=admin_user.username, role=admin_user.role
        )
        headers = {"Authorization": f"Bearer {token_data['access_token']}"}
        resp = client.put(f"/api/v1/members/{test_member.id}", json={
            "name": "Hijack",
            "birth_date": "2000-01-01",
            "gender": "M",
        }, headers=headers)
        assert resp.status_code == 403

    # ------------------------------------------------------------------
    # PATCH /members/{id}
    # ------------------------------------------------------------------

    def test_patch_member_success_returns_200(
        self, client_with_auth: TestClient, test_member
    ):
        """成功 PATCH 成员 → 200"""
        resp = client_with_auth.patch(f"/api/v1/members/{test_member.id}", json={
            "name": "Patched Member",
        })
        assert resp.status_code == 200
        assert resp.json()["name"] == "Patched Member"

    def test_patch_member_with_birth_time(
        self, client_with_auth: TestClient, test_member
    ):
        """PATCH 含 birth_time 字段 → 200"""
        resp = client_with_auth.patch(f"/api/v1/members/{test_member.id}", json={
            "birth_time": "09:45",
        })
        assert resp.status_code == 200
        assert resp.json()["birth_time"] == "09:45"

    def test_patch_member_not_found_returns_404(self, client_with_auth: TestClient):
        """成员不存在，PATCH → 404"""
        resp = client_with_auth.patch("/api/v1/members/999993", json={"name": "Ghost"})
        assert resp.status_code == 404

    def test_patch_member_wrong_owner_returns_403(
        self,
        client: TestClient,
        admin_user,
        test_member,
    ):
        """成员属于他人，PATCH → 403"""
        from services.auth_service import create_access_token
        token_data = create_access_token(
            user_id=admin_user.id, username=admin_user.username, role=admin_user.role
        )
        headers = {"Authorization": f"Bearer {token_data['access_token']}"}
        resp = client.patch(
            f"/api/v1/members/{test_member.id}",
            json={"name": "Hijack Patch"},
            headers=headers,
        )
        assert resp.status_code == 403

    # ------------------------------------------------------------------
    # DELETE /members/{id}
    # ------------------------------------------------------------------

    def test_delete_member_success_returns_204(
        self, client_with_auth: TestClient, test_member
    ):
        """成功删除成员 → 204"""
        resp = client_with_auth.delete(f"/api/v1/members/{test_member.id}")
        assert resp.status_code == 204

    def test_delete_member_not_found_returns_404(self, client_with_auth: TestClient):
        """成员不存在，DELETE → 404"""
        resp = client_with_auth.delete("/api/v1/members/999994")
        assert resp.status_code == 404

    def test_delete_member_wrong_owner_returns_403(
        self,
        client: TestClient,
        admin_user,
        test_member,
    ):
        """成员属于他人，DELETE → 403"""
        from services.auth_service import create_access_token
        token_data = create_access_token(
            user_id=admin_user.id, username=admin_user.username, role=admin_user.role
        )
        headers = {"Authorization": f"Bearer {token_data['access_token']}"}
        resp = client.delete(f"/api/v1/members/{test_member.id}", headers=headers)
        assert resp.status_code == 403
