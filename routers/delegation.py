"""
权限委托路由 - 用户之间的权限授予和撤销
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from fastapi import APIRouter, Depends, Request
from sqlmodel import Session, select

from db import get_session
from app.models import User, Delegation
from app.dependencies import require_user, RequiredUser
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
    ValidationException,
)
from app.error_handling import handle_exceptions

router = APIRouter(prefix="/api/v1", tags=["delegation"])


class DelegationCreateRequest(BaseModel):
    """创建权限委托请求"""
    to_user_id: int
    permission_type: str  # "view", "edit", "share", "manage"
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
