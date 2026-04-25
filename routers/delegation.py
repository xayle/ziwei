"""
权限委托路由 - 用户之间的权限授予和撤销
包括 N3.02 工作流端点（申请/批准/拒绝/撤销）
"""
from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel
from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from db import get_session
from app.models import User, Delegation
from app.dependencies import RequiredUser
from services.delegation_service import (
    create_delegation,
    revoke_delegation,
    list_delegations,
    log_action,
)
from app.exceptions import (
    AuthorizationException,
    BusinessException,
    ErrorCode,
    ResourceNotFoundException,
    ResourceConflictException,
    ValidationException,
)
from app.error_handling import handle_exceptions
from app.dependencies.permissions import _permission_cache

router = APIRouter(prefix="/api/v1", tags=["delegation"])


class DelegationCreateRequest(BaseModel):
    """创建权限委托请求"""
    to_user_id: int
    permission_type: str  # 委托级别: "view"/"edit"/"share"/"manage" 或精细权限如 "read_member"
    member_id: Optional[int] = None  # 可选：限制到特定成员
    expires_days: int = 30


class DelegationResponse(BaseModel):
    """权限委托响应"""
    id: int
    from_user_id: int      # ✅ 修复：授权者 ID
    to_user_id: int        # ✅ 修复：被授权者 ID
    permission_type: str
    member_scope: Optional[int]
    is_active: bool
    created_at: datetime
    expires_at: Optional[datetime]


@router.post("/delegations", response_model=DelegationResponse, status_code=201)
@handle_exceptions(ErrorCode.SYSTEM_INTERNAL_ERROR)
def create_user_delegation(
    body: DelegationCreateRequest,
    current_user: RequiredUser,
    session: Session = Depends(get_session),
):
    """
    创建权限委托 - 授予其他用户访问你的成员的权限
    """
    # 验证被授权用户存在
    to_user = session.exec(select(User).where(User.id == body.to_user_id)).first()
    if not to_user or not to_user.is_active:
        raise ResourceNotFoundException(
            message="target user not found or disabled",
            details={"resource_type": "user", "resource_id": body.to_user_id},
        )
    
    # 不能授予自己权限
    if body.to_user_id == current_user.id:
        raise ValidationException(
            code=ErrorCode.VALIDATION_INVALID_INPUT,
            message="Cannot delegate to yourself",
        )
    
    # 有效的permission_type
    valid_types = ["view", "edit", "share", "manage"]
    if body.permission_type not in valid_types:
        raise ValidationException(
            code=ErrorCode.VALIDATION_INVALID_INPUT,
            message=f"Invalid permission_type. Must be one of: {', '.join(valid_types)}",
        )
    
    # 创建委托
    delegation = create_delegation(
        session,
        from_user_id=current_user.id or 0,
        to_user_id=body.to_user_id,
        permission_type=body.permission_type,
        member_scope=body.member_id,
        expires_days=body.expires_days,
        audit_user_id=current_user.id or 0,
    )
    
    if not delegation:
        raise BusinessException(
            code=ErrorCode.BUSINESS_OPERATION_FAILED,
            message="Failed to create delegation",
        )
    
    # 记录额外的审计日志
    log_action(
        session,
        user_id=current_user.id or 0,
        action="create_delegation",
        resource_type="delegation",
        resource_id=str(delegation.id or 0),
        details={
            "to_user_id": body.to_user_id,
            "permission_type": body.permission_type,
            "member_id": body.member_id,
            "expires_days": body.expires_days,
        }
    )
    
    return DelegationResponse(
        id=delegation.id or 0,
        from_user_id=delegation.from_user_id,    # ✅ 修复
        to_user_id=delegation.to_user_id,        # ✅ 修复
        permission_type=delegation.permission_type,
        member_scope=delegation.member_scope,
        is_active=delegation.is_active,
        created_at=delegation.created_at,
        expires_at=delegation.expires_at,
    )


@router.get("/delegations/outgoing")
@handle_exceptions(ErrorCode.SYSTEM_INTERNAL_ERROR)
def list_outgoing_delegations(
    current_user: RequiredUser,
    session: Session = Depends(get_session),
):
    """
    列出我授予他人的权限委托
    """
    delegations = list_delegations(session, current_user.id or 0, direction="outgoing")
    
    return {
        "delegations": [
            {
                "id": d.id,
                "to_user_id": d.to_user_id,        # ✅ 修复
                "permission_type": d.permission_type,
                "member_scope": d.member_scope,
                "is_active": d.is_active,
                "expires_at": d.expires_at,
            }
            for d in delegations
        ],
        "total": len(delegations),
    }


@router.get("/delegations/incoming")
@handle_exceptions(ErrorCode.SYSTEM_INTERNAL_ERROR)
def list_incoming_delegations(
    current_user: RequiredUser,
    session: Session = Depends(get_session),
):
    """
    列出他人授予我的权限委托
    """
    delegations = list_delegations(session, current_user.id or 0, direction="incoming")
    
    return {
        "delegations": [
            {
                "id": d.id,
                "from_user_id": d.from_user_id,        # ✅ 修复
                "permission_type": d.permission_type,
                "member_scope": d.member_scope,
                "is_active": d.is_active,
                "expires_at": d.expires_at,
            }
            for d in delegations
        ],
        "total": len(delegations),
    }


@router.delete("/delegations/{delegation_id}", status_code=204)
@handle_exceptions(ErrorCode.SYSTEM_INTERNAL_ERROR)
def revoke_user_delegation(
    delegation_id: int,
    current_user: RequiredUser,
    session: Session = Depends(get_session),
):
    """
    撤销权限委托(只有授权方可以撤销)
    """
    # 验证委托存在且属于当前用户
    delegation = session.exec(
        select(Delegation).where(Delegation.id == delegation_id, Delegation.deleted_at.is_(None))  # type: ignore[union-attr]
    ).first()
    
    if not delegation:
        raise ResourceNotFoundException(
            message="Delegation not found",
            details={"resource_type": "delegation", "resource_id": delegation_id},
        )
    
    if delegation.from_user_id != current_user.id:  # ✅ 修复
        raise AuthorizationException(
            code=ErrorCode.AUTHZ_PERMISSION_DENIED,
            message="Only the delegating user can revoke a delegation",
        )
    
    # 撤销委托
    success = revoke_delegation(session, delegation_id, audit_user_id=current_user.id or 0)
    
    if not success:
        raise BusinessException(
            code=ErrorCode.BUSINESS_OPERATION_FAILED,
            message="Failed to revoke delegation",
        )


# ══════════════════════════════════════════════════════════════════════════════
# N3.02 — 权限申请工作流端点
# ══════════════════════════════════════════════════════════════════════════════

class PermissionRequestBody(BaseModel):
    """发起权限申请"""
    permission_type: str  # "view"/"edit"/"share"/"manage"
    from_user_id: Optional[int] = None  # 向谁申请；默认向任意 admin 申请
    member_scope: Optional[int] = None
    expires_days: int = 30


class RejectBody(BaseModel):
    reject_reason: Optional[str] = None


def _require_manage_permission(current_user: User, session: Session) -> None:
    """
    检查当前用户是否拥有 MANAGE 权限。
    满足以下任一条件：
      1. is_admin = True
      2. 拥有 status='approved' 的 manage 级别委托
    """
    if current_user.is_admin:
        return
    manage_delegation = session.exec(
        select(Delegation).where(
            Delegation.to_user_id == current_user.id,
            Delegation.permission_type == "manage",
            Delegation.status == "approved",
            Delegation.is_active.is_(True),   # type: ignore[union-attr]
            Delegation.deleted_at.is_(None),  # type: ignore[union-attr]
        )
    ).first()
    if not manage_delegation:
        raise AuthorizationException(
            code=ErrorCode.AUTHZ_PERMISSION_DENIED,
            message="MANAGE permission required",
        )


@router.post("/permissions/request", status_code=201)
@handle_exceptions(ErrorCode.SYSTEM_INTERNAL_ERROR)
def request_permission(
    body: PermissionRequestBody,
    current_user: RequiredUser,
    session: Session = Depends(get_session),
):
    """
    N3.02 — 发起权限申请（status=pending）
    任何已登录用户均可发起；审批人需有 MANAGE 权限。
    """
    valid_types = ["view", "edit", "share", "manage"]
    if body.permission_type not in valid_types:
        raise ValidationException(
            code=ErrorCode.VALIDATION_INVALID_INPUT,
            message=f"Invalid permission_type. Must be one of: {', '.join(valid_types)}",
        )

    from_uid = body.from_user_id or 0

    delegation = Delegation(
        from_user_id=from_uid,
        to_user_id=current_user.id or 0,
        permission_type=body.permission_type,
        member_scope=body.member_scope,
        is_active=False,           # 未批准前不生效
        expires_at=None,
        status="pending",
        requested_by=current_user.id or 0,
    )
    session.add(delegation)
    session.commit()
    session.refresh(delegation)

    log_action(
        session,
        user_id=current_user.id or 0,
        action="request_permission",
        resource_type="delegation",
        resource_id=str(delegation.id or 0),
        details={
            "permission_type": body.permission_type,
            "from_user_id": from_uid,
            "member_scope": body.member_scope,
            "expires_days": body.expires_days,
            "old_status": None,
            "new_status": "pending",
            "operator_id": current_user.id,
        },
    )

    return {
        "id": delegation.id,
        "to_user_id": delegation.to_user_id,
        "permission_type": delegation.permission_type,
        "status": delegation.status,
        "requested_by": delegation.requested_by,
        "created_at": delegation.created_at,
    }


@router.put("/permissions/request/{delegation_id}/approve")
@handle_exceptions(ErrorCode.SYSTEM_INTERNAL_ERROR)
def approve_permission_request(
    delegation_id: int,
    current_user: RequiredUser,
    session: Session = Depends(get_session),
):
    """
    N3.02 — 批准权限申请（status: pending → approved）
    需要 MANAGE 权限。
    - 禁止自我审批（requested_by == current_user.id → 403）
    - 重复审批（已非 pending）→ 409
    - 并发：UPDATE WHERE status='pending'，rowcount==0 → 409
    """
    _require_manage_permission(current_user, session)

    delegation = session.exec(
        select(Delegation).where(
            Delegation.id == delegation_id,
            Delegation.deleted_at.is_(None),  # type: ignore[union-attr]
        )
    ).first()

    if not delegation:
        raise ResourceNotFoundException(
            message="Permission request not found",
            details={"resource_type": "delegation", "resource_id": delegation_id},
        )

    # 禁止自我审批
    if delegation.requested_by == current_user.id:
        raise AuthorizationException(
            code=ErrorCode.AUTHZ_PERMISSION_DENIED,
            message="Self-approval is not allowed",
        )

    # 重复审批检查
    if delegation.status != "pending":
        raise ResourceConflictException(
            resource_type="delegation",
            code=ErrorCode.RESOURCE_CONFLICT,
            message=f"Cannot approve: current status is '{delegation.status}' (expected 'pending')",
            resource_id=str(delegation_id),
        )

    # 乐观状态锁：UPDATE WHERE status='pending'
    from sqlalchemy import text as sa_text
    result = session.exec(  # type: ignore[call-overload]
        sa_text(  # type: ignore[arg-type]
            "UPDATE delegations SET status='approved', approved_by=:approver, "
            "approved_at=:now, is_active=1, from_user_id=:from_uid "
            "WHERE id=:id AND status='pending'"
        ).bindparams(
            approver=current_user.id,
            now=datetime.now(timezone.utc).replace(tzinfo=None),
            from_uid=current_user.id,
            id=delegation_id,
        )
    )
    session.commit()

    if result.rowcount == 0:  # type: ignore[union-attr]
        raise ResourceConflictException(
            resource_type="delegation",
            code=ErrorCode.RESOURCE_CONFLICT,
            message="Concurrent approval detected: request already processed",
            resource_id=str(delegation_id),
        )

    # 刷新
    session.refresh(delegation)

    # 主动清除权限缓存
    cache_key = f"perm:{delegation.to_user_id}:{delegation.permission_type}"
    _permission_cache.invalidate(cache_key)

    log_action(
        session,
        user_id=current_user.id or 0,
        action="approve_permission",
        resource_type="delegation",
        resource_id=str(delegation_id),
        details={
            "old_status": "pending",
            "new_status": "approved",
            "operator_id": current_user.id,
            "to_user_id": delegation.to_user_id,
            "permission_type": delegation.permission_type,
        },
    )

    return {
        "id": delegation.id,
        "status": delegation.status,
        "approved_by": delegation.approved_by,
        "approved_at": delegation.approved_at,
    }


@router.put("/permissions/request/{delegation_id}/reject")
@handle_exceptions(ErrorCode.SYSTEM_INTERNAL_ERROR)
def reject_permission_request(
    delegation_id: int,
    body: RejectBody,
    current_user: RequiredUser,
    session: Session = Depends(get_session),
):
    """
    N3.02 — 拒绝权限申请（status: pending → rejected）
    需要 MANAGE 权限。
    - 已 approved 的申请不得直接 reject → 409（须走 revoke 端点）
    """
    _require_manage_permission(current_user, session)

    delegation = session.exec(
        select(Delegation).where(
            Delegation.id == delegation_id,
            Delegation.deleted_at.is_(None),  # type: ignore[union-attr]
        )
    ).first()

    if not delegation:
        raise ResourceNotFoundException(
            message="Permission request not found",
            details={"resource_type": "delegation", "resource_id": delegation_id},
        )

    # 已 approved 不得 reject（须用 revoke）
    if delegation.status == "approved":
        raise ResourceConflictException(
            resource_type="delegation",
            code=ErrorCode.RESOURCE_CONFLICT,
            message="Cannot reject an already-approved request; use the revoke endpoint instead",
            resource_id=str(delegation_id),
        )

    if delegation.status != "pending":
        raise ResourceConflictException(
            resource_type="delegation",
            code=ErrorCode.RESOURCE_CONFLICT,
            message=f"Cannot reject: current status is '{delegation.status}' (expected 'pending')",
            resource_id=str(delegation_id),
        )

    old_status = delegation.status
    delegation.status = "rejected"
    delegation.reject_reason = body.reject_reason
    session.add(delegation)
    session.commit()
    session.refresh(delegation)

    # 清除权限缓存（虽然 pending 时缓存一般无 True，但保持一致）
    cache_key = f"perm:{delegation.to_user_id}:{delegation.permission_type}"
    _permission_cache.invalidate(cache_key)

    log_action(
        session,
        user_id=current_user.id or 0,
        action="reject_permission",
        resource_type="delegation",
        resource_id=str(delegation_id),
        details={
            "old_status": old_status,
            "new_status": "rejected",
            "operator_id": current_user.id,
            "reject_reason": body.reject_reason,
            "to_user_id": delegation.to_user_id,
            "permission_type": delegation.permission_type,
        },
    )

    return {
        "id": delegation.id,
        "status": delegation.status,
        "reject_reason": delegation.reject_reason,
    }


@router.delete("/permissions/request/{delegation_id}/revoke", status_code=200)
@handle_exceptions(ErrorCode.SYSTEM_INTERNAL_ERROR)
def revoke_approved_permission(
    delegation_id: int,
    current_user: RequiredUser,
    session: Session = Depends(get_session),
):
    """
    N3.02 — 撤销已批准的权限（status: approved → revoked）
    需要 MANAGE 权限。
    - 仅 approved 状态可撤销；其他状态 → 409
    - ⚠️ 最高风险操作，审计日志强制写入
    """
    _require_manage_permission(current_user, session)

    delegation = session.exec(
        select(Delegation).where(
            Delegation.id == delegation_id,
            Delegation.deleted_at.is_(None),  # type: ignore[union-attr]
        )
    ).first()

    if not delegation:
        raise ResourceNotFoundException(
            message="Permission record not found",
            details={"resource_type": "delegation", "resource_id": delegation_id},
        )

    if delegation.status != "approved":
        raise ResourceConflictException(
            resource_type="delegation",
            code=ErrorCode.RESOURCE_CONFLICT,
            message=f"Cannot revoke: current status is '{delegation.status}' (expected 'approved')",
            resource_id=str(delegation_id),
        )

    delegation.status = "revoked"
    delegation.is_active = False
    session.add(delegation)
    session.commit()
    session.refresh(delegation)

    # 主动清除权限缓存（撤销为高风险操作，必须立即清缓存）
    cache_key = f"perm:{delegation.to_user_id}:{delegation.permission_type}"
    _permission_cache.invalidate(cache_key)
    _permission_cache.invalidate_user(delegation.to_user_id or 0)

    # ⚠️ 审计日志强制写入（append-only，撤销操作尤关键）
    log_action(
        session,
        user_id=current_user.id or 0,
        action="revoke_permission",
        resource_type="delegation",
        resource_id=str(delegation_id),
        details={
            "old_status": "approved",
            "new_status": "revoked",
            "operator_id": current_user.id,
            "to_user_id": delegation.to_user_id,
            "permission_type": delegation.permission_type,
        },
    )

    return {
        "id": delegation.id,
        "status": delegation.status,
        "message": "Permission successfully revoked",
    }


@router.post("/admin/expire-delegations", status_code=200)
@handle_exceptions(ErrorCode.SYSTEM_INTERNAL_ERROR)
def admin_expire_delegations(
    current_user: RequiredUser,
    session: Session = Depends(get_session),
):
    """
    [ADMIN] O12 — 手动触发过期委托清理。
    仅 is_admin=True 的用户可调用。
    """
    if not current_user.is_admin:
        raise AuthorizationException(
            code=ErrorCode.AUTHZ_PERMISSION_DENIED,
            message="Permission denied: admin required",
        )
    from services.permission_cascade_service import auto_revoke_expired_delegations
    n = auto_revoke_expired_delegations(session)
    return {"revoked": n, "message": f"已撤销 {n} 个过期委托"}
