"""
权限委托管理服务 - 用户之间的权限授予和撤销
"""
from datetime import datetime, timedelta, timezone
from typing import Optional, List
from sqlmodel import Session, col, select
from sqlalchemy import and_, or_

from app.models import Delegation, User, Member, AuditLog
from services.permission_service import Permission, Role
from services.permission_cascade_service import (
    validate_permission_escalation,
    validate_permission_chain,
    revoke_delegation_and_dependent,
)

# ✅ Week 4: 集成新的错误处理系统
from app.exceptions import (
    AuthorizationException,
    ValidationException,
    ResourceNotFoundException,
    BusinessException,
    ErrorCode,
)
from app.error_handling import handle_exceptions


@handle_exceptions(ErrorCode.SYSTEM_INTERNAL_ERROR)
def create_delegation(
    session: Session,
    from_user_id: int,
    to_user_id: int,
    permission_type: str,
    member_scope: Optional[int] = None,
    expires_days: int = 30,
    audit_user_id: Optional[int] = None,
) -> Optional[Delegation]:
    """
    创建权限委托（从一个用户授予另一个用户权限）
    
    支持权限级联验证，防止权限提升漏洞
    
    Args:
        session: 数据库会话
        from_user_id: 授权方用户ID
        to_user_id: 被授权方用户ID
        permission_type: 权限类型 (创建为Permission枚举值)
        member_scope: 可选的成员ID限制，NULL表示所有成员
        expires_days: 委托有效天数（默认30天）
        audit_user_id: 执行此操作的用户ID（用于审计）
        
    Returns:
        创建的Delegation对象或None
        
    Raises:
        ResourceNotFoundException: 用户不存在
        ValidationException: 用户未激活或参数无效
        AuthorizationException: 权限检查失败
    """
    # 验证两个用户都存在且活跃
    from_user = session.exec(
        select(User).where(User.id == from_user_id, User.deleted_at.is_(None))  # type: ignore
    ).first()
    to_user = session.exec(
        select(User).where(User.id == to_user_id, User.deleted_at.is_(None))  # type: ignore
    ).first()
    
    if not from_user:
        raise ResourceNotFoundException(
            code=ErrorCode.RESOURCE_NOT_FOUND,
            message=f"User {from_user_id} not found",
            resource_type="User",
            resource_id=str(from_user_id),
        )
    
    if not to_user:
        raise ResourceNotFoundException(
            code=ErrorCode.RESOURCE_NOT_FOUND,
            message=f"User {to_user_id} not found",
            resource_type="User",
            resource_id=str(to_user_id),
        )
    
    if not from_user.is_active or not to_user.is_active:
        raise ValidationException(
            code=ErrorCode.VALIDATION_INVALID_INPUT,
            message="One or both users are inactive",
            details={
                "from_user_active": from_user.is_active,
                "to_user_active": to_user.is_active,
            },
        )
    
    # 防止自身委托
    if from_user_id == to_user_id:
        raise ValidationException(
            code=ErrorCode.VALIDATION_INVALID_INPUT,
            message="Cannot delegate permissions to yourself",
        )
    
    # 如果指定了member_scope，验证该成员属于from_user
    if member_scope:
        member = session.exec(
            select(Member).where(Member.id == member_scope, Member.deleted_at.is_(None))  # type: ignore
        ).first()
        if not member or member.owner_id != from_user_id:
            raise ValidationException(
                code=ErrorCode.VALIDATION_INVALID_INPUT,
                message=f"Member {member_scope} does not belong to delegating user",
                details={"member_id": member_scope, "owner_id": from_user_id},
            )
    
    # ========== 权限级联验证 ==========
    try:
        target_permission = Permission(permission_type)
    except ValueError:
        raise ValidationException(
            code=ErrorCode.VALIDATION_INVALID_INPUT,
            message=f"Invalid permission type: {permission_type}",
            details={"provided": permission_type},
        )
    
    # 检查权限提升漏洞
    from_user_role = Role(from_user.role)
    is_valid, error_msg = validate_permission_escalation(
        session,
        from_user_id,
        from_user_role,
        target_permission,
        member_scope,
    )
    
    if not is_valid:
        raise AuthorizationException(
            code=ErrorCode.AUTHZ_PERMISSION_DENIED,
            message=f"Permission escalation check failed: {error_msg}",
            details={"reason": error_msg},
        )
    
    # 验证权限链的有效性
    is_valid, error_msg = validate_permission_chain(
        session,
        from_user_id,
        target_permission,
        member_scope,
    )
    
    if not is_valid:
        raise ValidationException(
            code=ErrorCode.VALIDATION_INVALID_INPUT,
            message=f"Permission chain validation failed: {error_msg}",
            details={"reason": error_msg},
        )
    
    # ========== 创建委托 ==========
    expires_at = datetime.now(timezone.utc) + timedelta(days=expires_days)
    
    delegation = Delegation(
        from_user_id=from_user_id,      # ✅ 修复字段名
        to_user_id=to_user_id,          # ✅ 修复字段名
        permission_type=permission_type,
        member_scope=member_scope,
        is_active=True,
        expires_at=expires_at,
    )
    
    session.add(delegation)
    session.commit()
    session.refresh(delegation)
    
    # 记录审计日志
    if audit_user_id:
        log_action(
            session,
            user_id=audit_user_id,
            action="create_delegation",
            resource_type="delegation",
            resource_id=str(delegation.id),
            details={
                "from_user": from_user_id,
                "to_user": to_user_id,
                "permission_type": permission_type,
                "member_scope": member_scope,
                "expires_days": expires_days,
                "validation": "cascade_verified",
            }
        )
    
    return delegation


@handle_exceptions(ErrorCode.SYSTEM_INTERNAL_ERROR)
def revoke_delegation(
    session: Session,
    delegation_id: int,
    audit_user_id: Optional[int] = None,
) -> int:
    """
    撤销权限委托（支持级联撤销）
    
    当撤销一个委托时，所有依赖于它的子委托也会被撤销
    例如：A→B→C，撤销A→B时，B→C也会被自动撤销
    
    Args:
        session: 数据库会话
        delegation_id: 要撤销的委托ID
        audit_user_id: 执行此操作的用户ID（用于审计）
        
    Returns:
        被撤销的委托总数（包括依赖的委托）
        
    Raises:
        ResourceNotFoundException: 委托不存在
        BusinessException: 委托已被撤销
    """
    # 查找要撤销的委托
    delegation = session.exec(
        select(Delegation).where(Delegation.id == delegation_id, Delegation.deleted_at.is_(None))  # type: ignore
    ).first()
    
    if not delegation:
        raise ResourceNotFoundException(
            code=ErrorCode.RESOURCE_NOT_FOUND,
            message=f"Delegation {delegation_id} not found",
            resource_type="Delegation",
            resource_id=str(delegation_id),
        )
    
    if not delegation.is_active:
        raise BusinessException(
            code=ErrorCode.BUSINESS_INVALID_STATE,
            message=f"Delegation {delegation_id} is already revoked",
            details={"delegation_id": delegation_id},
        )
    
    # 使用级联撤销函数 - 自动处理依赖的委托
    count = revoke_delegation_and_dependent(
        session,
        delegation_id,
        audit_user_id,
    )
    
    # 记录审计日志 - 级联撤销已在revoke_delegation_and_dependent内部记录
    if audit_user_id:
        log_action(
            session,
            user_id=audit_user_id,
            action="revoke_delegation",
            resource_type="delegation",
            resource_id=str(delegation_id),
            details={
                "revoked_count": count,
                "cascade_revocation": count > 1,
            }
        )
    
    return count


@handle_exceptions(ErrorCode.SYSTEM_INTERNAL_ERROR)
def has_delegation_permission(
    session: Session,
    from_user_id: int,
    to_user_id: int,
    permission_type: str,
    member_id: Optional[int] = None,
) -> bool:
    """
    检查是否存在有效的权限委托
    
    Args:
        session: 数据库会话
        from_user_id: 授权方用户ID
        to_user_id: 被授权方用户ID
        permission_type: 权限类型
        member_id: 检查特定成员或None表示任何成员
        
    Returns:
        是否有权限
        
    Raises:
        ValidationException: 参数无效
    """
    # 参数验证
    if from_user_id <= 0 or to_user_id <= 0:
        raise ValidationException(
            code=ErrorCode.VALIDATION_INVALID_INPUT,
            message="User IDs must be positive integers",
            details={"from_user_id": from_user_id, "to_user_id": to_user_id},
        )
    
    if not permission_type:
        raise ValidationException(
            code=ErrorCode.VALIDATION_MISSING_FIELD,
            message="Permission type is required",
        )
    
    # 查询有效的委托
    now = datetime.now(timezone.utc)
    
    query = select(Delegation).where(
        and_(
            col(Delegation.from_user_id) == from_user_id,   # ✅ 修复
            col(Delegation.to_user_id) == to_user_id,       # ✅ 修复
            col(Delegation.permission_type) == permission_type,
            col(Delegation.is_active).is_(True),
            col(Delegation.deleted_at).is_(None),
            or_(
                col(Delegation.expires_at).is_(None),
                col(Delegation.expires_at) > now,
            ),
        )
    )
    
    delegations = session.exec(query).all()
    
    # 如果没有委托，返回False
    if not delegations:
        return False
    
    # 如果未指定member_id，任何活跃的委托都有效
    if member_id is None:
        return True
    
    # 检查是否有匹配member_scope的委托
    for delegation in delegations:
        # NULL scope表示所有成员，或匹配特定的member_id
        if delegation.member_scope is None or delegation.member_scope == member_id:
            return True
    
    return False


@handle_exceptions(ErrorCode.SYSTEM_INTERNAL_ERROR)
def list_delegations(
    session: Session,
    user_id: int,
    direction: str = "outgoing",
) -> List[Delegation]:
    """
    列出用户的委托
    
    Args:
        session: 数据库会话
        user_id: 用户ID
        direction: "outgoing" (授予他人) 或 "incoming" (从他人接收)
        
    Returns:
        委托列表
        
    Raises:
        ValidationException: 参数无效
    """
    # 参数验证
    if user_id <= 0:
        raise ValidationException(
            code=ErrorCode.VALIDATION_INVALID_INPUT,
            message="User ID must be a positive integer",
            details={"user_id": user_id},
        )
    
    if direction not in ("outgoing", "incoming"):
        raise ValidationException(
            code=ErrorCode.VALIDATION_INVALID_INPUT,
            message='Direction must be "outgoing" or "incoming"',
            details={"provided": direction},
        )
    
    if direction == "outgoing":
        query = select(Delegation).where(
            Delegation.from_user_id == user_id,
            Delegation.deleted_at.is_(None)  # type: ignore
        )  # ✅ 修复
    else:
        query = select(Delegation).where(
            Delegation.to_user_id == user_id,
            Delegation.deleted_at.is_(None)  # type: ignore
        )    # ✅ 修复
    
    return list(session.exec(query).all())


def log_action(
    session: Session,
    user_id: int,
    action: str,
    resource_type: str,
    resource_id: Optional[str] = None,
    details: Optional[dict] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    status: str = "success",
    error_message: Optional[str] = None,
) -> AuditLog:
    """
    记录审计日志
    
    Args:
        session: 数据库会话
        user_id: 执行操作的用户ID
        action: 操作类型
        resource_type: 资源类型 (member, event, scenario, etc.)
        resource_id: 资源ID
        details: 额外的上下文信息（JSON）
        ip_address: 请求IP地址
        user_agent: 用户代理字符串
        status: 操作状态 (success, failure, etc.)
        error_message: 如果失败，错误信息
        
    Returns:
        创建的AuditLog对象
    """
    import json
    
    log = AuditLog(
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details=json.dumps(details) if details else None,
        ip_address=ip_address,
        user_agent=user_agent,
        status=status,
        error_message=error_message,
        created_at=datetime.now(timezone.utc),
    )
    
    session.add(log)
    session.commit()
    session.refresh(log)
    
    return log


def get_audit_logs(
    session: Session,
    user_id: Optional[int] = None,
    action: Optional[str] = None,
    resource_type: Optional[str] = None,
    limit: int = 100,
) -> List[AuditLog]:
    """
    获取审计日志列表
    
    Args:
        session: 数据库会话
        user_id: 按用户过滤
        action: 按操作类型过滤
        resource_type: 按资源类型过滤
        limit: 返回最多多少条记录
        
    Returns:
        审计日志列表
    """
    query = select(AuditLog)
    
    if user_id:
        query = query.where(AuditLog.user_id == user_id)
    
    if action:
        query = query.where(AuditLog.action == action)
    
    if resource_type:
        query = query.where(AuditLog.resource_type == resource_type)
    
    # 按时间倒序（最新在前）
    query = query.order_by(col(AuditLog.created_at).desc()).limit(limit)
    
    return list(session.exec(query).all())
