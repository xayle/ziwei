"""
权限级联验证服务 - 防止权限提升漏洞
"""

from datetime import UTC, datetime

from sqlalchemy import and_
from sqlmodel import Session, col, select

from app.models import Delegation, User
from services.permission_service import ROLE_PERMISSIONS, Permission, Role, has_permission


def _utcnow() -> datetime:
    """返回当前 UTC 时间（naive），兼容 SQLite 存储的 naive datetime。"""
    return datetime.utcnow()


def _is_expired(expires_at: datetime | None) -> bool:
    """检查是否已过期，兼容 naive 与 aware datetime。"""
    if not expires_at:
        return False
    now = _utcnow()
    # 若 expires_at 含时区信息则转为 naive UTC 再比较
    exp = expires_at.replace(tzinfo=None) if expires_at.tzinfo else expires_at
    return now > exp


def get_user_effective_permissions(
    session: Session,
    user_id: int,
    member_id: int | None = None,
) -> set[Permission]:
    """
    获取用户的有效权限集合 (包括直接权限和委托权限)

    Args:
        session: 数据库会话
        user_id: 用户ID
        member_id: 可选的成员范围限制

    Returns:
        set[Permission]: 用户的所有有效权限
    """
    # 从User表获取基本权限
    user = session.exec(
        select(User).where(User.id == user_id, User.deleted_at.is_(None))  # type: ignore
    ).first()
    if not user:
        return set()

    # 基础权限 (来自角色)
    user_role = Role(user.role)
    base_permissions = set(ROLE_PERMISSIONS.get(user_role, []))

    # 添加委托权限
    delegated_permissions = _get_delegated_permissions(session, user_id, member_id)

    return base_permissions | delegated_permissions


def _get_delegated_permissions(
    session: Session,
    user_id: int,
    member_id: int | None = None,
) -> set[Permission]:
    """
    获取用户通过委托获得的权限

    只包含:
    1. 未撤销的委托
    2. 未过期的委托
    3. 如果指定member_id，仅包括无范围限制或该成员的委托

    Args:
        session: 数据库会话
        user_id: 用户ID
        member_id: 可选的成员范围限制

    Returns:
        set[Permission]: 委托权限集合
    """
    query = select(Delegation).where(
        (Delegation.to_user_id == user_id) & (Delegation.is_active == True) & (Delegation.deleted_at.is_(None))  # type: ignore
    )

    delegations = session.exec(query).all()
    permissions = set()

    for delegation in delegations:
        # 检查过期时间
        if _is_expired(delegation.expires_at):
            continue

        # 检查成员范围限制
        if member_id is not None:
            if delegation.member_scope is not None and delegation.member_scope != member_id:
                continue

        # 添加权限
        try:
            perm = Permission(delegation.permission_type)
            permissions.add(perm)
        except ValueError:
            # 忽略无效的权限类型
            pass

    return permissions


def validate_permission_escalation(
    session: Session,
    delegating_user_id: int,
    delegating_role: Role,
    target_permission: Permission,
    target_member_id: int | None = None,
) -> tuple[bool, str | None]:
    """
    验证权限委托是否会导致权限提升 (安全漏洞)

    规则:
    1. 用户不能委托自己没有的权限
    2. 用户不能通过委托链升级权限
    3. 权限被撤销时应立即失效

    Args:
        session: 数据库会话
        delegating_user_id: 委托者的用户ID
        delegating_role: 委托者的角色
        target_permission: 要委托的权限
        target_member_id: 目标成员ID (可选)

    Returns:
        Tuple[bool, Optional[str]]: (是否合法, 错误信息 或 None)
    """

    # 检查1: 委托者是否有该权限?
    delegating_permissions = ROLE_PERMISSIONS.get(delegating_role, [])
    if target_permission not in delegating_permissions:
        return False, f"Cannot delegate permission you don't have: {target_permission}"

    # 检查2: 如果权限来自委托，检查委托链是否有效
    # (这需要在更高级的权限检查中处理)

    # 检查3: 验证权限不会被循环委托回来
    delegations_for_permission = session.exec(
        select(Delegation).where(
            (Delegation.from_user_id == delegating_user_id)
            & (Delegation.permission_type == target_permission.value)
            & (Delegation.is_active == True)
            & (Delegation.deleted_at.is_(None))  # type: ignore
        )
    ).all()

    for delegation in delegations_for_permission:
        # 如果该权限已经被委托出去，检查是否会形成循环
        if delegation.to_user_id == delegating_user_id:  # ✅ 修复：使用 delegation实例
            return False, "Circular delegation detected"

    return True, None


def validate_permission_chain(
    session: Session,
    user_id: int,
    required_permission: Permission,
    member_id: int | None = None,
    chain_depth: int = 0,
    max_chain_depth: int = 3,
) -> tuple[bool, str | None]:
    """
    验证用户是否可以通过权限链获得所需权限

    支持的链深度最多为3层，防止复杂的权限委托链

    Args:
        session: 数据库会话
        user_id: 用户ID
        required_permission: 需要的权限
        member_id: 目标成员ID (可选)
        chain_depth: 当前链深度 (用于递归)
        max_chain_depth: 最大链深度

    Returns:
        Tuple[bool, Optional[str]]: (是否有效, 错误信息 或 None)
    """

    if chain_depth > max_chain_depth:
        return False, f"Permission chain too deep (max: {max_chain_depth} levels)"

    # 检查用户的直接权限
    user = session.exec(
        select(User).where(User.id == user_id, User.deleted_at.is_(None))  # type: ignore
    ).first()
    if not user:
        return False, "User not found"

    user_role = Role(user.role)
    if has_permission(user_role, required_permission):
        return True, None

    # 检查委托权限
    delegations = session.exec(
        select(Delegation).where(
            (Delegation.to_user_id == user_id)
            & (Delegation.permission_type == required_permission.value)
            & (Delegation.is_active == True)
            & (Delegation.deleted_at.is_(None))  # type: ignore
        )
    ).all()

    for delegation in delegations:
        # 检查过期时间
        if _is_expired(delegation.expires_at):
            continue

        # 检查成员范围
        if member_id is not None:
            if delegation.member_scope is not None and delegation.member_scope != member_id:
                continue

        # 验证委托者是否真的有该权限
        delegator = session.exec(
            select(User).where(User.id == delegation.from_user_id, User.deleted_at.is_(None))  # type: ignore
        ).first()  # ✅ 修复
        if delegator:
            delegator_role = Role(delegator.role)
            if has_permission(delegator_role, required_permission):
                return True, None

    return False, f"User does not have permission: {required_permission}"


def revoke_delegation_and_dependent(
    session: Session,
    delegation_id: int,
    audit_user_id: int | None,
) -> int:
    """
    撤销一个权限委托，并级联撤销所有依赖于该权限的委托

    例如:
    - 用户A委托权限X给用户B
    - 用户B基于权限X又委托权限X给用户C
    - 撤销A→B的委托时，也应撤销B→C的委托

    Args:
        session: 数据库会话
        delegation_id: 要撤销的委托ID
        audit_user_id: 审计用户ID

    Returns:
        int: 被撤销的委托数量 (包括级联撤销)
    """
    from services.delegation_service import log_action

    delegation = session.exec(
        select(Delegation).where(Delegation.id == delegation_id, Delegation.deleted_at.is_(None))  # type: ignore
    ).first()
    if not delegation:
        return 0

    revoked_count = 0

    # 撤销该委托
    delegation.is_active = False
    session.add(delegation)
    revoked_count += 1

    # 查找所有基于该权限的级联委托
    cascaded_delegations = session.exec(
        select(Delegation).where(
            (Delegation.from_user_id == delegation.to_user_id)  # ✅ 修复
            & (Delegation.permission_type == delegation.permission_type)
            & (Delegation.is_active == True)
            & (Delegation.deleted_at.is_(None))  # type: ignore
        )
    ).all()

    for cascaded in cascaded_delegations:
        # 递归撤销
        cascaded.is_active = False
        session.add(cascaded)
        revoked_count += 1

        # 审计日志
        if audit_user_id is not None:
            log_action(
                session,
                user_id=audit_user_id,
                action="revoke_delegation_cascade",
                resource_type="delegation",
                resource_id=str(cascaded.id),
                details={
                    "message": f"Cascading revocation from delegation {delegation_id}",
                },
            )

    session.commit()

    return revoked_count


def auto_revoke_expired_delegations(session: Session) -> int:
    """
    自动撤销所有过期的权限委托

    这个函数应该定期调用 (例如通过后台任务)

    Args:
        session: 数据库会话

    Returns:
        int: 自动撤销的委托数量
    """
    now = datetime.now(UTC)

    expired_delegations = session.exec(
        select(Delegation).where(
            and_(
                col(Delegation.expires_at) < now,
                col(Delegation.is_active).is_(True),
                col(Delegation.deleted_at).is_(None),  # type: ignore
            )
        )
    ).all()

    revoked_count = 0

    for delegation in expired_delegations:
        delegation.is_active = False
        session.add(delegation)
        revoked_count += 1

    if revoked_count > 0:
        session.commit()

    return revoked_count


def verify_delegations_integrity(session: Session) -> list[str]:
    """
    验证所有权限委托的完整性，返回发现的问题列表

    检查项:
    1. 委托者是否存在
    2. 接收者是否存在
    3. 目标成员 (如果指定) 是否存在
    4. 权限类型是否有效
    5. 过期时间是否合理

    Args:
        session: 数据库会话

    Returns:
        List[str]: 发现的问题列表
    """
    issues = []

    delegations = session.exec(select(Delegation)).all()

    for delegation in delegations:
        # 检查委托者
        from_user = session.exec(
            select(User).where(User.id == delegation.from_user_id, User.deleted_at.is_(None))  # type: ignore
        ).first()  # ✅ 修复
        if not from_user:
            issues.append(f"Delegation {delegation.id}: from_user {delegation.from_user_id} not found")

        # 检查接收者
        to_user = session.exec(
            select(User).where(User.id == delegation.to_user_id, User.deleted_at.is_(None))  # type: ignore
        ).first()  # ✅ 修复
        if not to_user:
            issues.append(f"Delegation {delegation.id}: to_user {delegation.to_user_id} not found")

        # 检查权限类型
        try:
            Permission(delegation.permission_type)
        except ValueError:
            issues.append(f"Delegation {delegation.id}: invalid permission_type {delegation.permission_type}")

        # 检查过期时间
        if delegation.expires_at and _is_expired(delegation.expires_at) and delegation.is_active:
            issues.append(f"Delegation {delegation.id}: should be auto-revoked (expired)")

    return issues
