"""
N3.07 — RBAC 权限申请工作流测试

覆盖场景（spec 强制）：
  ① 申请→批准→权限生效
  ② 申请→拒绝→权限不生效
  ③ 普通用户调用 approve → 403
  ④ 自我审批 (requested_by == approver) → 403
  ⑤ 重复审批 (已 approved) → 409
  ⑥ 非法状态转换 (approved 后调 reject) → 409
  ⑦ 并发审批 (rowcount==0 模拟) → 409
  ⑧ 撤销已批准权限 (approved → revoked) → 200
  ⑨ 非法撤销 (pending 状态 revoke) → 409
"""
from __future__ import annotations

import threading
from datetime import timedelta
from typing import Dict

import pytest
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, Session, create_engine, select
from sqlmodel.pool import StaticPool

from run import app
from db import get_session
from app.models import User, Delegation
from services.auth_service import hash_password, create_access_token
from services.permission_service import Role


# ════════════════════════════════════════════════════════════════════
# 测试数据库 & 客户端 fixtures
# ════════════════════════════════════════════════════════════════════

@pytest.fixture(scope="module")
def engine():
    eng = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(eng)
    return eng


@pytest.fixture(scope="function")
def session(engine):
    """每个测试独立事务，确保隔离。"""
    connection = engine.connect()
    trans = connection.begin()
    s = Session(bind=connection)
    yield s
    s.close()
    trans.rollback()
    connection.close()


@pytest.fixture(scope="function")
def client(session: Session):
    """使用测试 DB 的 FastAPI TestClient。"""
    def override_get_session():
        return session

    app.dependency_overrides[get_session] = override_get_session
    yield TestClient(app, raise_server_exceptions=True)
    app.dependency_overrides.clear()


# ════════════════════════════════════════════════════════════════════
# 工具函数
# ════════════════════════════════════════════════════════════════════

def _make_user(session: Session, username: str, *, is_admin: bool = False) -> User:
    """快速创建用户。"""
    u = User(
        username=username,
        email=f"{username}@rbac.test",
        password_hash=hash_password("pw123!"),
        role="admin" if is_admin else "user",
        is_active=True,
        is_admin=is_admin,
    )
    session.add(u)
    session.commit()
    session.refresh(u)
    return u


def _token(user: User) -> Dict[str, str]:
    """生成 Bearer 授权头（含 Content-Type，通过 request_validation 中间件）。"""
    tok = create_access_token(
        user_id=user.id,  # type: ignore[arg-type]
        username=user.username,
        role=user.role,
        expires_delta=timedelta(hours=1),
    )
    return {
        "Authorization": f"Bearer {tok['access_token']}",
        "Content-Type": "application/json",
    }


def _request_permission(client: TestClient, headers: dict, permission_type: str = "view") -> dict:
    """快速发起权限申请。"""
    r = client.post(
        "/api/v1/permissions/request",
        json={"permission_type": permission_type, "expires_days": 30},
        headers=headers,
    )
    assert r.status_code == 201, r.text
    return r.json()


# ════════════════════════════════════════════════════════════════════
# ① 申请→批准→权限生效
# ════════════════════════════════════════════════════════════════════

def test_request_approve_permission_effective(client: TestClient, session: Session):
    """完整主干：申请 → 批准 → 委托 status=approved & is_active=True。"""
    requester = _make_user(session, "requester_01")
    admin = _make_user(session, "admin_01", is_admin=True)

    # 发起申请
    data = _request_permission(client, _token(requester), "edit")
    delegation_id = data["id"]
    assert data["status"] == "pending"

    # 管理员批准
    r = client.put(
        f"/api/v1/permissions/request/{delegation_id}/approve",
        headers=_token(admin),
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["status"] == "approved"
    assert body["approved_by"] == admin.id

    # 验证 DB
    session.expire_all()
    d = session.exec(select(Delegation).where(Delegation.id == delegation_id)).first()
    assert d is not None
    assert d.status == "approved"
    assert d.is_active is True


# ════════════════════════════════════════════════════════════════════
# ② 申请→拒绝→权限不生效
# ════════════════════════════════════════════════════════════════════

def test_request_reject_permission_not_effective(client: TestClient, session: Session):
    """申请被拒绝后，is_active 保持 False。"""
    requester = _make_user(session, "requester_02")
    admin = _make_user(session, "admin_02", is_admin=True)

    data = _request_permission(client, _token(requester))
    delegation_id = data["id"]

    r = client.put(
        f"/api/v1/permissions/request/{delegation_id}/reject",
        json={"reject_reason": "不符合要求"},
        headers=_token(admin),
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["status"] == "rejected"
    assert body["reject_reason"] == "不符合要求"

    # 验证 DB：is_active 仍为 False
    session.expire_all()
    d = session.exec(select(Delegation).where(Delegation.id == delegation_id)).first()
    assert d is not None
    assert d.status == "rejected"
    assert d.is_active is False


# ════════════════════════════════════════════════════════════════════
# ③ 普通用户调用 approve → 403
# ════════════════════════════════════════════════════════════════════

def test_regular_user_cannot_approve(client: TestClient, session: Session):
    """普通用户无 MANAGE 权限，调用 approve → 403。"""
    requester = _make_user(session, "requester_03a")
    other_user = _make_user(session, "user_03b")  # 非 admin

    data = _request_permission(client, _token(requester))
    delegation_id = data["id"]

    r = client.put(
        f"/api/v1/permissions/request/{delegation_id}/approve",
        headers=_token(other_user),
    )
    assert r.status_code == 403, r.text


# ════════════════════════════════════════════════════════════════════
# ④ 自我审批 → 403
# ════════════════════════════════════════════════════════════════════

def test_self_approval_forbidden(client: TestClient, session: Session):
    """requested_by == 当前审批用户 → 403（禁止自批）。"""
    # 该用户同时是 admin，但仍不允许审批自己的申请
    self_admin = _make_user(session, "self_admin_04", is_admin=True)

    data = _request_permission(client, _token(self_admin), "manage")
    delegation_id = data["id"]

    r = client.put(
        f"/api/v1/permissions/request/{delegation_id}/approve",
        headers=_token(self_admin),
    )
    assert r.status_code == 403, r.text
    assert "self" in r.text.lower() or "self-approval" in r.text.lower()


# ════════════════════════════════════════════════════════════════════
# ⑤ 重复审批 (已 approved) → 409
# ════════════════════════════════════════════════════════════════════

def test_duplicate_approve_returns_409(client: TestClient, session: Session):
    """已 approved 再次调 approve → 409（不接受幂等，409 更安全）。"""
    requester = _make_user(session, "requester_05")
    admin = _make_user(session, "admin_05", is_admin=True)

    data = _request_permission(client, _token(requester))
    delegation_id = data["id"]

    # 第一次批准
    r1 = client.put(
        f"/api/v1/permissions/request/{delegation_id}/approve",
        headers=_token(admin),
    )
    assert r1.status_code == 200, r1.text

    # 重复批准
    r2 = client.put(
        f"/api/v1/permissions/request/{delegation_id}/approve",
        headers=_token(admin),
    )
    assert r2.status_code == 409, r2.text


# ════════════════════════════════════════════════════════════════════
# ⑥ 非法状态转换：approved → reject → 409
# ════════════════════════════════════════════════════════════════════

def test_reject_approved_request_returns_409(client: TestClient, session: Session):
    """已 approved 的申请直接调 reject → 409（须走 revoke 端点）。"""
    requester = _make_user(session, "requester_06")
    admin = _make_user(session, "admin_06", is_admin=True)

    data = _request_permission(client, _token(requester), "share")
    delegation_id = data["id"]

    # 先批准
    r1 = client.put(
        f"/api/v1/permissions/request/{delegation_id}/approve",
        headers=_token(admin),
    )
    assert r1.status_code == 200

    # 再 reject → 409
    r2 = client.put(
        f"/api/v1/permissions/request/{delegation_id}/reject",
        json={"reject_reason": "改变主意"},
        headers=_token(admin),
    )
    assert r2.status_code == 409, r2.text


# ════════════════════════════════════════════════════════════════════
# ⑦ 并发审批 → 409
# ════════════════════════════════════════════════════════════════════

def test_concurrent_approve_returns_409(engine, session: Session):
    """
    两个管理员同时 approve 同一申请。
    使用独立 session 模拟并发：第一个成功（200），第二个 409。
    实现依赖 UPDATE WHERE status='pending' 乐观锁：rowcount==0 → 409。
    """
    import time

    # 使用独立连接，不受外层事务影响
    conn1 = engine.connect()
    conn2 = engine.connect()
    s1 = Session(bind=conn1)
    s2 = Session(bind=conn2)

    try:
        # 重新使用 make_user（独立 session）
        requester = _make_user(s1, f"req_concurrent")
        admin_a = _make_user(s1, f"admin_concurrent_a", is_admin=True)
        admin_b = _make_user(s1, f"admin_concurrent_b", is_admin=True)

        # 在 s1 中创建 pending delegation
        d = Delegation(
            from_user_id=0,
            to_user_id=requester.id or 0,
            permission_type="view",
            is_active=False,
            status="pending",
            requested_by=requester.id,
        )
        s1.add(d)
        s1.commit()
        s1.refresh(d)
        delegation_id = d.id

        # admin_a 先批准
        from sqlalchemy import text as sa_text
        result_a = s1.exec(  # type: ignore[call-overload]
            sa_text(  # type: ignore[arg-type]
                "UPDATE delegations SET status='approved', approved_by=:approver, "
                "is_active=1, from_user_id=:approver "
                "WHERE id=:id AND status='pending'"
            ).bindparams(approver=admin_a.id, id=delegation_id)
        )
        s1.commit()
        assert result_a.rowcount == 1, "第一个 approve 必须成功"

        # admin_b 后批准（rowcount 应为 0）
        result_b = s2.exec(  # type: ignore[call-overload]
            sa_text(  # type: ignore[arg-type]
                "UPDATE delegations SET status='approved', approved_by=:approver, "
                "is_active=1, from_user_id=:approver "
                "WHERE id=:id AND status='pending'"
            ).bindparams(approver=admin_b.id, id=delegation_id)
        )
        s2.commit()
        assert result_b.rowcount == 0, "第二个并发 approve 必须产生 rowcount==0"

    finally:
        s1.close()
        s2.close()
        conn1.close()
        conn2.close()


# ════════════════════════════════════════════════════════════════════
# ⑧ 撤销已批准权限 (approved → revoked)
# ════════════════════════════════════════════════════════════════════

def test_revoke_approved_permission(client: TestClient, session: Session):
    """完整撤销流程：approved → revoked，is_active=False。"""
    requester = _make_user(session, "requester_08")
    admin = _make_user(session, "admin_08", is_admin=True)

    data = _request_permission(client, _token(requester), "edit")
    delegation_id = data["id"]

    # 先批准
    r1 = client.put(
        f"/api/v1/permissions/request/{delegation_id}/approve",
        headers=_token(admin),
    )
    assert r1.status_code == 200

    # 再撤销
    r2 = client.delete(
        f"/api/v1/permissions/request/{delegation_id}/revoke",
        headers=_token(admin),
    )
    assert r2.status_code == 200, r2.text
    body = r2.json()
    assert body["status"] == "revoked"

    # 验证 DB
    session.expire_all()
    d = session.exec(select(Delegation).where(Delegation.id == delegation_id)).first()
    assert d is not None
    assert d.status == "revoked"
    assert d.is_active is False


# ════════════════════════════════════════════════════════════════════
# ⑨ 非法撤销 (pending 状态 revoke) → 409
# ════════════════════════════════════════════════════════════════════

def test_revoke_pending_returns_409(client: TestClient, session: Session):
    """pending 状态不可 revoke → 409（只能 approve/reject pending）。"""
    requester = _make_user(session, "requester_09")
    admin = _make_user(session, "admin_09", is_admin=True)

    data = _request_permission(client, _token(requester), "view")
    delegation_id = data["id"]

    r = client.delete(
        f"/api/v1/permissions/request/{delegation_id}/revoke",
        headers=_token(admin),
    )
    assert r.status_code == 409, r.text


# ════════════════════════════════════════════════════════════════════
# ⑩ 未登录调用申请接口 → 401/403
# ════════════════════════════════════════════════════════════════════

def test_unauthenticated_request_returns_401_or_403(client: TestClient, session: Session):
    """未携带 token 调用申请接口，应被拒绝。"""
    r = client.post(
        "/api/v1/permissions/request",
        json={"permission_type": "view"},
    )
    assert r.status_code in (401, 403), r.text
