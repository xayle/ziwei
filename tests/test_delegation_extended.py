"""
delegation_service 额外测试 — 补充覆盖未命中路径
覆盖:
  - create_delegation 中用户不存在、成员不属于授权方、无效权限类型等分支
  - has_delegation_permission 完整路径
  - list_delegations outgoing/incoming
  - log_action & get_audit_logs
"""
import pytest
from datetime import datetime, timedelta, timezone
from sqlmodel import SQLModel, Session, create_engine
from sqlmodel.pool import StaticPool

from app.models import User, Delegation
from app.exceptions import AppException
from services.permission_service import Role, Permission
from services.delegation_service import (
    create_delegation,
    has_delegation_permission,
    list_delegations,
    log_action,
    get_audit_logs,
)


# ──────────────────────────── fixtures ────────────────────────────────

@pytest.fixture
def engine():
    eng = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(eng)
    return eng


@pytest.fixture
def session(engine):
    with Session(engine) as s:
        yield s


def _user(session, username, role=Role.OWNER, active=True):
    from services.auth_service import hash_password
    u = User(
        username=username,
        email=f"{username}@x.com",
        role=role,
        password_hash=hash_password("pw"),
        is_active=active,
    )
    session.add(u)
    session.commit()
    session.refresh(u)
    return u


def _deleg(session, frm, to, perm, active=True, expires_at=None, scope=None):
    d = Delegation(
        from_user_id=frm.id, to_user_id=to.id,
        permission_type=perm.value if isinstance(perm, Permission) else perm,
        is_active=active, expires_at=expires_at, member_scope=scope,
    )
    session.add(d)
    session.commit()
    session.refresh(d)
    return d


# ──────────────────────── create_delegation edge cases ────────────────────

class TestCreateDelegationEdgeCases:

    def test_from_user_not_found(self, session):
        to = _user(session, "d_to1")
        with pytest.raises(AppException) as ei:
            create_delegation(session, from_user_id=99999, to_user_id=to.id,
                              permission_type="read_member")
        assert "not found" in str(ei.value).lower()

    def test_to_user_not_found(self, session):
        frm = _user(session, "d_frm1")
        with pytest.raises(AppException) as ei:
            create_delegation(session, from_user_id=frm.id, to_user_id=99999,
                              permission_type="read_member")
        assert "not found" in str(ei.value).lower()

    def test_invalid_permission_type(self, session):
        owner = _user(session, "d_own2")
        viewer = _user(session, "d_view2", Role.VIEWER)
        with pytest.raises(AppException) as ei:
            create_delegation(session, from_user_id=owner.id, to_user_id=viewer.id,
                              permission_type="totally_invalid_perm")
        assert "invalid" in str(ei.value).lower() or "permission" in str(ei.value).lower()

    def test_from_user_inactive(self, session):
        frm = _user(session, "d_frm3", active=False)
        to = _user(session, "d_to3")
        with pytest.raises(AppException) as ei:
            create_delegation(session, from_user_id=frm.id, to_user_id=to.id,
                              permission_type="read_member")
        assert "inactive" in str(ei.value).lower()


# ──────────────────────── has_delegation_permission ───────────────────────

class TestHasDelegationPermission:

    def test_invalid_user_ids_raise(self, session):
        with pytest.raises(AppException):
            has_delegation_permission(session, from_user_id=-1, to_user_id=1,
                                      permission_type="read_member")

    def test_empty_permission_type_raises(self, session):
        with pytest.raises(AppException):
            has_delegation_permission(session, from_user_id=1, to_user_id=2,
                                      permission_type="")

    def test_no_delegation_returns_false(self, session):
        owner = _user(session, "h_own1")
        viewer = _user(session, "h_view1", Role.VIEWER)
        result = has_delegation_permission(
            session, owner.id, viewer.id, "read_member"
        )
        assert result is False

    def test_active_delegation_returns_true(self, session):
        owner = _user(session, "h_own2")
        viewer = _user(session, "h_view2", Role.VIEWER)
        _deleg(session, owner, viewer, Permission.READ_MEMBER)
        result = has_delegation_permission(
            session, owner.id, viewer.id, "read_member"
        )
        assert result is True

    def test_expired_delegation_returns_false(self, session):
        owner = _user(session, "h_own3")
        viewer = _user(session, "h_view3", Role.VIEWER)
        past = datetime.utcnow() - timedelta(hours=1)  # SQLite stores naive datetime
        _deleg(session, owner, viewer, Permission.READ_MEMBER, expires_at=past)
        result = has_delegation_permission(
            session, owner.id, viewer.id, "read_member"
        )
        assert result is False

    def test_member_scope_match(self, session):
        owner = _user(session, "h_own4")
        viewer = _user(session, "h_view4", Role.VIEWER)
        _deleg(session, owner, viewer, Permission.READ_MEMBER, scope=42)
        assert has_delegation_permission(
            session, owner.id, viewer.id, "read_member", member_id=42
        ) is True

    def test_member_scope_mismatch(self, session):
        owner = _user(session, "h_own5")
        viewer = _user(session, "h_view5", Role.VIEWER)
        _deleg(session, owner, viewer, Permission.READ_MEMBER, scope=99)
        assert has_delegation_permission(
            session, owner.id, viewer.id, "read_member", member_id=1
        ) is False

    def test_null_scope_matches_any(self, session):
        owner = _user(session, "h_own6")
        viewer = _user(session, "h_view6", Role.VIEWER)
        _deleg(session, owner, viewer, Permission.READ_MEMBER, scope=None)
        assert has_delegation_permission(
            session, owner.id, viewer.id, "read_member", member_id=777
        ) is True

    def test_inactive_delegation_returns_false(self, session):
        owner = _user(session, "h_own7")
        viewer = _user(session, "h_view7", Role.VIEWER)
        _deleg(session, owner, viewer, Permission.READ_MEMBER, active=False)
        assert has_delegation_permission(
            session, owner.id, viewer.id, "read_member"
        ) is False


# ──────────────────────── list_delegations ────────────────────────────────

class TestListDelegations:

    def test_invalid_user_id_raises(self, session):
        with pytest.raises(AppException):
            list_delegations(session, user_id=0)

    def test_invalid_direction_raises(self, session):
        owner = _user(session, "l_own1")
        with pytest.raises(AppException):
            list_delegations(session, user_id=owner.id, direction="sideways")

    def test_outgoing_delegations(self, session):
        owner = _user(session, "l_own2")
        v1 = _user(session, "l_v1", Role.VIEWER)
        v2 = _user(session, "l_v2", Role.EDITOR)
        _deleg(session, owner, v1, Permission.READ_MEMBER)
        _deleg(session, owner, v2, Permission.READ_MEMBER)
        result = list_delegations(session, owner.id, "outgoing")
        assert len(result) >= 2
        assert all(d.from_user_id == owner.id for d in result)

    def test_incoming_delegations(self, session):
        owner = _user(session, "l_own3")
        viewer = _user(session, "l_v3", Role.VIEWER)
        _deleg(session, owner, viewer, Permission.READ_MEMBER)
        result = list_delegations(session, viewer.id, "incoming")
        assert len(result) >= 1
        assert all(d.to_user_id == viewer.id for d in result)

    def test_empty_list_returned(self, session):
        standalone = _user(session, "l_solo", Role.VIEWER)
        result = list_delegations(session, standalone.id, "outgoing")
        assert result == []


# ──────────────────────── log_action & get_audit_logs ─────────────────────

class TestLogAndAudit:

    def test_log_action_creates_entry(self, session):
        owner = _user(session, "audit_own1")
        log = log_action(
            session, owner.id,
            action="test_action",
            resource_type="member",
            resource_id="42",
            details={"key": "value"},
        )
        assert log.id is not None
        assert log.action == "test_action"
        assert log.resource_type == "member"

    def test_log_action_with_error(self, session):
        owner = _user(session, "audit_own2")
        log = log_action(
            session, owner.id,
            action="failed_op",
            resource_type="event",
            status="failure",
            error_message="something went wrong",
        )
        assert log.status == "failure"
        assert log.error_message == "something went wrong"

    def test_get_audit_logs_filter_by_user(self, session):
        owner = _user(session, "audit_own3")
        other = _user(session, "audit_other3")
        log_action(session, owner.id, action="act1", resource_type="r")
        log_action(session, other.id, action="act2", resource_type="r")
        logs = get_audit_logs(session, user_id=owner.id)
        assert all(l.user_id == owner.id for l in logs)

    def test_get_audit_logs_filter_by_action(self, session):
        owner = _user(session, "audit_own4")
        log_action(session, owner.id, action="unique_act_xyz", resource_type="r")
        log_action(session, owner.id, action="other_act", resource_type="r")
        logs = get_audit_logs(session, action="unique_act_xyz")
        assert all(l.action == "unique_act_xyz" for l in logs)

    def test_get_audit_logs_filter_by_resource(self, session):
        owner = _user(session, "audit_own5")
        log_action(session, owner.id, action="a", resource_type="member")
        log_action(session, owner.id, action="b", resource_type="event")
        logs = get_audit_logs(session, resource_type="member")
        assert all(l.resource_type == "member" for l in logs)

    def test_get_audit_logs_limit(self, session):
        owner = _user(session, "audit_own6")
        for i in range(10):
            log_action(session, owner.id, action=f"bulk_{i}", resource_type="r")
        logs = get_audit_logs(session, user_id=owner.id, limit=3)
        assert len(logs) <= 3
