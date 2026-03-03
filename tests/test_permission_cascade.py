"""
权限级联服务完整测试
覆盖 services/permission_cascade_service.py 中未覆盖的核心路径
"""
import pytest
from datetime import datetime, timedelta, timezone
from sqlmodel import SQLModel, Session, select, create_engine
from sqlmodel.pool import StaticPool

from app.models import User, Delegation
from services.permission_service import Role, Permission, ROLE_PERMISSIONS
from services.permission_cascade_service import (
    get_user_effective_permissions,
    _get_delegated_permissions,
    validate_permission_escalation,
    validate_permission_chain,
    revoke_delegation_and_dependent,
    auto_revoke_expired_delegations,
    verify_delegations_integrity,
)


# ──────────────────────────────── fixtures ────────────────────────────────

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


def _make_user(session: Session, username: str, role: Role, active: bool = True) -> User:
    from services.auth_service import hash_password
    u = User(
        username=username,
        email=f"{username}@test.com",
        role=role,
        password_hash=hash_password("pass"),
        is_active=active,
    )
    session.add(u)
    session.commit()
    session.refresh(u)
    return u


def _make_delegation(
    session: Session,
    from_user: User,
    to_user: User,
    perm: Permission,
    is_active: bool = True,
    expires_at=None,
    member_scope=None,
) -> Delegation:
    d = Delegation(
        from_user_id=from_user.id,
        to_user_id=to_user.id,
        permission_type=perm.value,
        is_active=is_active,
        expires_at=expires_at,
        member_scope=member_scope,
    )
    session.add(d)
    session.commit()
    session.refresh(d)
    return d


# ──────────────────────────── get_user_effective_permissions ──────────────

class TestGetUserEffectivePermissions:

    def test_nonexistent_user_returns_empty(self, session: Session):
        result = get_user_effective_permissions(session, user_id=99999)
        assert result == set()

    def test_base_permissions_from_role(self, session: Session):
        owner = _make_user(session, "p_owner", Role.OWNER)
        perms = get_user_effective_permissions(session, owner.id)
        assert Permission.DELETE_MEMBER in perms

    def test_viewer_base_permissions(self, session: Session):
        viewer = _make_user(session, "p_viewer", Role.VIEWER)
        perms = get_user_effective_permissions(session, viewer.id)
        assert Permission.READ_MEMBER in perms
        assert Permission.DELETE_MEMBER not in perms

    def test_includes_delegated_permissions(self, session: Session):
        owner = _make_user(session, "p_owner2", Role.OWNER)
        viewer = _make_user(session, "p_viewer2", Role.VIEWER)
        _make_delegation(session, owner, viewer, Permission.CREATE_MEMBER)
        perms = get_user_effective_permissions(session, viewer.id)
        assert Permission.CREATE_MEMBER in perms

    def test_expired_delegation_not_included(self, session: Session):
        owner = _make_user(session, "p_owner3", Role.OWNER)
        viewer = _make_user(session, "p_viewer3", Role.VIEWER)
        past = datetime.utcnow() - timedelta(hours=1)  # SQLite stores naive datetime
        _make_delegation(session, owner, viewer, Permission.CREATE_MEMBER, expires_at=past)
        perms = get_user_effective_permissions(session, viewer.id)
        assert Permission.CREATE_MEMBER not in perms

    def test_member_scope_filter(self, session: Session):
        """不匹配 member_scope 的委托不应出现在结果中"""
        owner = _make_user(session, "p_owner4", Role.OWNER)
        viewer = _make_user(session, "p_viewer4", Role.VIEWER)
        _make_delegation(session, owner, viewer, Permission.CREATE_MEMBER, member_scope=555)
        # 查询 member_id=1，与委托的 scope=555 不匹配
        perms = get_user_effective_permissions(session, viewer.id, member_id=1)
        assert Permission.CREATE_MEMBER not in perms

    def test_null_scope_matches_any_member(self, session: Session):
        """member_scope=None 委托应匹配任何 member_id"""
        owner = _make_user(session, "p_owner5", Role.OWNER)
        viewer = _make_user(session, "p_viewer5", Role.VIEWER)
        _make_delegation(session, owner, viewer, Permission.CREATE_MEMBER, member_scope=None)
        perms = get_user_effective_permissions(session, viewer.id, member_id=42)
        assert Permission.CREATE_MEMBER in perms

    def test_inactive_delegation_not_included(self, session: Session):
        owner = _make_user(session, "p_owner6", Role.OWNER)
        viewer = _make_user(session, "p_viewer6", Role.VIEWER)
        _make_delegation(session, owner, viewer, Permission.CREATE_MEMBER, is_active=False)
        perms = get_user_effective_permissions(session, viewer.id)
        assert Permission.CREATE_MEMBER not in perms


# ──────────────────────────── validate_permission_escalation ──────────────

class TestValidatePermissionEscalation:

    def test_valid_escalation_owner_has_perm(self, session: Session):
        owner = _make_user(session, "e_owner1", Role.OWNER)
        ok, err = validate_permission_escalation(
            session, owner.id, Role.OWNER,
            Permission.DELETE_MEMBER,
        )
        assert ok is True
        assert err is None

    def test_invalid_escalation_viewer_lacks_perm(self, session: Session):
        viewer = _make_user(session, "e_viewer1", Role.VIEWER)
        ok, err = validate_permission_escalation(
            session, viewer.id, Role.VIEWER,
            Permission.DELETE_MEMBER,
        )
        assert ok is False
        assert err is not None

    def test_circular_delegation_detected(self, session: Session):
        """自己委托给自己 → 循环检测"""
        owner = _make_user(session, "e_owner2", Role.OWNER)
        # 先手动插入一条 from=owner → to=owner 的委托
        d = Delegation(
            from_user_id=owner.id,
            to_user_id=owner.id,
            permission_type=Permission.DELETE_MEMBER.value,
            is_active=True,
        )
        session.add(d)
        session.commit()
        ok, err = validate_permission_escalation(
            session, owner.id, Role.OWNER,
            Permission.DELETE_MEMBER,
        )
        assert ok is False
        assert err is not None


# ──────────────────────────── validate_permission_chain ──────────────────

class TestValidatePermissionChain:

    def test_user_not_found(self, session: Session):
        ok, err = validate_permission_chain(
            session, user_id=88888,
            required_permission=Permission.READ_MEMBER,
        )
        assert ok is False
        assert "not found" in (err or "").lower()

    def test_direct_role_permission(self, session: Session):
        owner = _make_user(session, "c_owner1", Role.OWNER)
        ok, err = validate_permission_chain(
            session, owner.id,
            required_permission=Permission.DELETE_MEMBER,
        )
        assert ok is True
        assert err is None

    def test_missing_permission_no_delegation(self, session: Session):
        viewer = _make_user(session, "c_viewer1", Role.VIEWER)
        ok, err = validate_permission_chain(
            session, viewer.id,
            required_permission=Permission.DELETE_MEMBER,
        )
        assert ok is False

    def test_via_active_delegation(self, session: Session):
        owner = _make_user(session, "c_owner2", Role.OWNER)
        viewer = _make_user(session, "c_viewer2", Role.VIEWER)
        _make_delegation(session, owner, viewer, Permission.DELETE_MEMBER)
        ok, _ = validate_permission_chain(
            session, viewer.id,
            required_permission=Permission.DELETE_MEMBER,
        )
        assert ok is True

    def test_expired_delegation_chain_fails(self, session: Session):
        owner = _make_user(session, "c_owner3", Role.OWNER)
        viewer = _make_user(session, "c_viewer3", Role.VIEWER)
        past = datetime.utcnow() - timedelta(hours=2)  # SQLite stores naive datetime
        _make_delegation(session, owner, viewer, Permission.DELETE_MEMBER, expires_at=past)
        ok, _ = validate_permission_chain(
            session, viewer.id,
            required_permission=Permission.DELETE_MEMBER,
        )
        assert ok is False

    def test_member_scope_mismatch_chain_fails(self, session: Session):
        owner = _make_user(session, "c_owner4", Role.OWNER)
        viewer = _make_user(session, "c_viewer4", Role.VIEWER)
        _make_delegation(session, owner, viewer, Permission.DELETE_MEMBER, member_scope=999)
        ok, _ = validate_permission_chain(
            session, viewer.id,
            required_permission=Permission.DELETE_MEMBER,
            member_id=1,
        )
        assert ok is False

    def test_chain_depth_exceeded(self, session: Session):
        viewer = _make_user(session, "c_viewer5", Role.VIEWER)
        ok, err = validate_permission_chain(
            session, viewer.id,
            required_permission=Permission.DELETE_MEMBER,
            chain_depth=10,
            max_chain_depth=3,
        )
        assert ok is False
        assert "deep" in (err or "").lower()


# ──────────────────────────── revoke_delegation_and_dependent ─────────────

class TestRevokeDelegationAndDependent:

    def test_nonexistent_returns_zero(self, session: Session):
        count = revoke_delegation_and_dependent(session, delegation_id=77777, audit_user_id=None)
        assert count == 0

    def test_revokes_single(self, session: Session):
        owner = _make_user(session, "r_owner1", Role.OWNER)
        viewer = _make_user(session, "r_viewer1", Role.VIEWER)
        d = _make_delegation(session, owner, viewer, Permission.READ_MEMBER)
        count = revoke_delegation_and_dependent(session, d.id, audit_user_id=owner.id)
        assert count == 1
        session.refresh(d)
        assert d.is_active is False

    def test_cascade_revoke(self, session: Session):
        """A→B，B→C（同权限），撤销 A→B 应同时撤销 B→C"""
        owner = _make_user(session, "r_owner2", Role.OWNER)
        editor = _make_user(session, "r_editor2", Role.EDITOR)
        viewer = _make_user(session, "r_viewer2", Role.VIEWER)
        d1 = _make_delegation(session, owner, editor, Permission.READ_MEMBER)
        d2 = _make_delegation(session, editor, viewer, Permission.READ_MEMBER)
        count = revoke_delegation_and_dependent(session, d1.id, audit_user_id=owner.id)
        assert count >= 2
        session.refresh(d1)
        session.refresh(d2)
        assert d1.is_active is False
        assert d2.is_active is False


# ──────────────────────────── auto_revoke_expired_delegations ─────────────

class TestAutoRevokeExpiredDelegations:

    def test_no_expired_returns_zero(self, session: Session):
        count = auto_revoke_expired_delegations(session)
        assert count == 0

    def test_revokes_expired(self, session: Session):
        owner = _make_user(session, "a_owner1", Role.OWNER)
        viewer = _make_user(session, "a_viewer1", Role.VIEWER)
        past = datetime.utcnow() - timedelta(hours=3)  # SQLite stores naive datetime
        _make_delegation(session, owner, viewer, Permission.READ_MEMBER, expires_at=past)
        count = auto_revoke_expired_delegations(session)
        assert count == 1

    def test_does_not_revoke_active(self, session: Session):
        owner = _make_user(session, "a_owner2", Role.OWNER)
        viewer = _make_user(session, "a_viewer2", Role.VIEWER)
        future = datetime.utcnow() + timedelta(days=30)  # SQLite stores naive datetime
        _make_delegation(session, owner, viewer, Permission.READ_MEMBER, expires_at=future)
        count = auto_revoke_expired_delegations(session)
        assert count == 0


# ──────────────────────────── verify_delegations_integrity ─────────────────

class TestVerifyDelegationsIntegrity:

    def test_empty_db_no_issues(self, session: Session):
        issues = verify_delegations_integrity(session)
        assert issues == []

    def test_valid_delegation_no_issues(self, session: Session):
        owner = _make_user(session, "v_owner1", Role.OWNER)
        viewer = _make_user(session, "v_viewer1", Role.VIEWER)
        _make_delegation(session, owner, viewer, Permission.READ_MEMBER)
        issues = verify_delegations_integrity(session)
        assert issues == []

    def test_invalid_permission_type_flagged(self, session: Session):
        owner = _make_user(session, "v_owner2", Role.OWNER)
        viewer = _make_user(session, "v_viewer2", Role.VIEWER)
        bad = Delegation(
            from_user_id=owner.id,
            to_user_id=viewer.id,
            permission_type="invalid_perm_xyz",
            is_active=True,
        )
        session.add(bad)
        session.commit()
        issues = verify_delegations_integrity(session)
        assert any("invalid" in i.lower() for i in issues)

    def test_expired_but_active_flagged(self, session: Session):
        owner = _make_user(session, "v_owner3", Role.OWNER)
        viewer = _make_user(session, "v_viewer3", Role.VIEWER)
        past = datetime.utcnow() - timedelta(days=1)  # SQLite stores naive datetime
        _make_delegation(session, owner, viewer, Permission.READ_MEMBER, expires_at=past)
        issues = verify_delegations_integrity(session)
        assert any("auto-revoked" in i.lower() or "expired" in i.lower() for i in issues)
