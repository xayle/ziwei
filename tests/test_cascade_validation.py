"""
级联权限验证测试 - 简化版

测试权限级联系统的核心功能：
- 权限提升防御
- 级联撤销
"""

import pytest
from datetime import datetime, timezone, timedelta
from sqlmodel import SQLModel, Session, select, create_engine
from sqlmodel.pool import StaticPool

from app.models import User, Delegation
from app.exceptions import AppException
from services.delegation_service import (
    create_delegation, revoke_delegation
)
from services.permission_service import Role, Permission, ROLE_PERMISSIONS


@pytest.fixture
def mock_db():
    """创建内存数据库用于测试"""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture
def test_users(mock_db: Session):
    """创建测试用户"""
    from services.auth_service import hash_password
    
    # 所有者 (OWNER角色)
    owner = User(
        username="owner_user",
        email="owner@test.com",
        role=Role.OWNER,
        password_hash=hash_password("pass123"),
        is_active=True,
    )
    
    # 编辑者 (EDITOR角色)
    editor1 = User(
        username="editor1",
        email="editor1@test.com",
        role=Role.EDITOR,
        password_hash=hash_password("pass123"),
        is_active=True,
    )
    
    editor2 = User(
        username="editor2",
        email="editor2@test.com",
        role=Role.EDITOR,
        password_hash=hash_password("pass123"),
        is_active=True,
    )
    
    # 查看者 (VIEWER角色)
    viewer = User(
        username="viewer",
        email="viewer@test.com",
        role=Role.VIEWER,
        password_hash=hash_password("pass123"),
        is_active=True,
    )
    
    mock_db.add_all([owner, editor1, editor2, viewer])
    mock_db.commit()
    
    mock_db.refresh(owner)
    mock_db.refresh(editor1)
    mock_db.refresh(editor2)
    mock_db.refresh(viewer)
    
    return {
        "owner": owner,
        "editor1": editor1,
        "editor2": editor2,
        "viewer": viewer,
    }


class TestDelegationBasics:
    """测试委托的基本功能"""
    
    def test_owner_can_create_delegation(self, mock_db: Session, test_users):
        """测试OWNER可以创建委托"""
        owner = test_users["owner"]
        editor = test_users["editor1"]
        
        # OWNER有CREATE_MEMBER权限，可以委托
        delegation = create_delegation(
            mock_db,
            from_user_id=owner.id,
            to_user_id=editor.id,
            permission_type="create_member",
            audit_user_id=owner.id,
        )
        
        assert delegation is not None
        assert delegation.is_active
        assert delegation.from_user_id == owner.id
        assert delegation.to_user_id == editor.id
    
    def test_cannot_delegate_to_self(self, mock_db: Session, test_users):
        """测试不能向自己委托"""
        owner = test_users["owner"]
        
        with pytest.raises(AppException) as exc_info:
            create_delegation(
                mock_db,
                from_user_id=owner.id,
                to_user_id=owner.id,
                permission_type="create_member",
                audit_user_id=owner.id,
            )
        
        assert "cannot delegate" in str(exc_info.value).lower()
    
    def test_cannot_delegate_to_inactive_user(self, mock_db: Session, test_users):
        """测试不能向非活跃用户委托"""
        owner = test_users["owner"]
        editor = test_users["editor1"]
        
        # 禁用编辑者
        editor.is_active = False
        mock_db.add(editor)
        mock_db.commit()
        
        with pytest.raises(AppException) as exc_info:
            create_delegation(
                mock_db,
                from_user_id=owner.id,
                to_user_id=editor.id,
                permission_type="create_member",
                audit_user_id=owner.id,
            )
        
        assert "inactive" in str(exc_info.value).lower()


class TestEscalationPrevention:
    """测试权限提升防御"""
    
    def test_editor_cannot_delegate_delete(self, mock_db: Session, test_users):
        """测试EDITOR不能委托DELETE_MEMBER权限"""
        editor1 = test_users["editor1"]
        editor2 = test_users["editor2"]
        
        # EDITOR角色没有DELETE权限
        with pytest.raises(AppException) as exc_info:
            create_delegation(
                mock_db,
                from_user_id=editor1.id,
                to_user_id=editor2.id,
                permission_type="delete_member",  # EDITOR没有这个权限
                audit_user_id=editor1.id,
            )
        
        assert "escalation" in str(exc_info.value).lower() or "permission" in str(exc_info.value).lower()
    
    def test_viewer_cannot_delegate_create(self, mock_db: Session, test_users):
        """测试VIEWER不能委托CREATE_MEMBER权限"""
        viewer = test_users["viewer"]
        editor = test_users["editor1"]
        
        # VIEWER角色没有CREATE权限
        with pytest.raises(AppException) as exc_info:
            create_delegation(
                mock_db,
                from_user_id=viewer.id,
                to_user_id=editor.id,
                permission_type="create_member",
                audit_user_id=viewer.id,
            )
        
        assert "escalation" in str(exc_info.value).lower() or "permission" in str(exc_info.value).lower()


class TestRevocation:
    """测试撤销功能"""
    
    def test_revoke_delegation(self, mock_db: Session, test_users):
        """测试撤销委托"""
        owner = test_users["owner"]
        editor = test_users["editor1"]
        
        # 创建委托
        delegation = create_delegation(
            mock_db,
            from_user_id=owner.id,
            to_user_id=editor.id,
            permission_type="create_member",
            audit_user_id=owner.id,
        )
        
        assert delegation is not None
        assert delegation.id is not None
        delegation_id = delegation.id

        # 撤销委托
        count = revoke_delegation(
            mock_db,
            delegation_id=delegation_id,
            audit_user_id=owner.id,
        )
        
        assert count >= 1
        
        # 验证委托已被标记为非活跃
        revoked = mock_db.exec(
            select(Delegation).where(Delegation.id == delegation_id)
        ).first()
        assert revoked is not None
        assert not revoked.is_active
    
    def test_cannot_revoke_already_revoked(self, mock_db: Session, test_users):
        """测试不能撤销已被撤销的委托"""
        owner = test_users["owner"]
        editor = test_users["editor1"]
        
        # 创建并撤销委托
        delegation = create_delegation(
            mock_db,
            from_user_id=owner.id,
            to_user_id=editor.id,
            permission_type="create_member",
            audit_user_id=owner.id,
        )
        
        assert delegation is not None
        assert delegation.id is not None
        delegation_id = delegation.id
        revoke_delegation(
            mock_db,
            delegation_id=delegation_id,
            audit_user_id=owner.id,
        )
        
        # 尝试再次撤销
        with pytest.raises(AppException) as exc_info:
            revoke_delegation(
                mock_db,
                delegation_id=delegation_id,
                audit_user_id=owner.id,
            )
        
        assert "already revoked" in str(exc_info.value).lower()
    
    def test_cannot_revoke_nonexistent(self, mock_db: Session, test_users):
        """测试不能撤销不存在的委托"""
        owner = test_users["owner"]
        
        with pytest.raises(AppException) as exc_info:
            revoke_delegation(
                mock_db,
                delegation_id=99999,
                audit_user_id=owner.id,
            )
        
        assert "not found" in str(exc_info.value).lower()


class TestDelegationExpiry:
    """测试委托过期"""
    
    def test_delegation_expires(self, mock_db: Session, test_users):
        """测试委托在指定天数后过期"""
        owner = test_users["owner"]
        editor = test_users["editor1"]
        
        # 创建委托，仅有效1天
        delegation = create_delegation(
            mock_db,
            from_user_id=owner.id,
            to_user_id=editor.id,
            permission_type="create_member",
            expires_days=1,
            audit_user_id=owner.id,
        )
        
        assert delegation is not None
        assert delegation.expires_at is not None
        now = datetime.now(timezone.utc)
        # 过期时间应该大于现在
        expires_naive = delegation.expires_at.replace(tzinfo=None)
        now_naive = now.replace(tzinfo=None)
        assert expires_naive > now_naive
        # 过期时间应该小于现在+2天
        assert expires_naive < now_naive + timedelta(days=2)


class TestPermissionChecks:
    """测试权限验证"""
    
    def test_role_permissions_owner(self, mock_db: Session, test_users):
        """测试OWNER角色拥有正确的权限"""
        owner = test_users["owner"]
        owner_role = Role(owner.role)
        perms = ROLE_PERMISSIONS.get(owner_role, [])
        
        # OWNER应该有DELETE_MEMBER权限
        assert Permission.DELETE_MEMBER in perms
    
    def test_role_permissions_editor(self, mock_db: Session, test_users):
        """测试EDITOR角色的权限"""
        editor = test_users["editor1"]
        editor_role = Role(editor.role)
        perms = ROLE_PERMISSIONS.get(editor_role, [])
        
        # EDITOR有READ和UPDATE权限
        assert Permission.READ_MEMBER in perms
        assert Permission.UPDATE_MEMBER in perms
        # 但不应该有CREATE和DELETE权限
        assert Permission.CREATE_MEMBER not in perms
        assert Permission.DELETE_MEMBER not in perms
    
    def test_role_permissions_viewer(self, mock_db: Session, test_users):
        """测试VIEWER角色的权限"""
        viewer = test_users["viewer"]
        viewer_role = Role(viewer.role)
        perms = ROLE_PERMISSIONS.get(viewer_role, [])
        
        # VIEWER只有读权限
        assert Permission.READ_MEMBER in perms
        # 不应该有写权限
        assert Permission.CREATE_MEMBER not in perms
        assert Permission.DELETE_MEMBER not in perms
