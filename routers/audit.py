"""
审计日志路由 - 查看操作历史和安全审计
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from fastapi import APIRouter, Depends, Query
from sqlmodel import Session, select

from db import get_session
from app.models import User, AuditLog
from app.dependencies import require_user, RequiredUser
from services.delegation_service import get_audit_logs, log_action
from services.permission_service import Permission, Role, has_permission
from app.exceptions import (
    AuthorizationException,
    ErrorCode,
    ResourceNotFoundException,
)
from app.error_handling import handle_exceptions

router = APIRouter(prefix="/api/v1", tags=["audit"])


class AuditLogResponse(BaseModel):
    """审计日志响应"""
    id: int
    user_id: int
    action: str
    resource_type: str
    resource_id: Optional[str]
    details: Optional[str]
    ip_address: Optional[str]
    user_agent: Optional[str]
    status: str
    error_message: Optional[str]
    created_at: datetime


@router.get("/audit-logs")
@handle_exceptions(ErrorCode.SYSTEM_INTERNAL_ERROR)
def get_user_audit_logs(
    current_user: RequiredUser,
    session: Session = Depends(get_session),
    action: Optional[str] = Query(None, description="按操作类型过滤"),
    resource_type: Optional[str] = Query(None, description="按资源类型过滤"),
    limit: int = Query(100, ge=1, le=1000, description="返回数量限制"),
):
    """
    获取当前用户的审计日志
    """
    logs = get_audit_logs(
        session,
        user_id=current_user.id,
        action=action,
        resource_type=resource_type,
        limit=limit,
    )
    
    return {
        "logs": [
            AuditLogResponse(
                id=log.id or 0,
                user_id=log.user_id or 0,
                action=log.action,
                resource_type=log.resource_type,
                resource_id=log.resource_id,
                details=log.details,
                ip_address=log.ip_address,
                user_agent=log.user_agent,
                status=log.status,
                error_message=log.error_message,
                created_at=log.created_at,
            )
            for log in logs
        ],
        "total": len(logs),
    }


@router.get("/audit-logs/admin")
@handle_exceptions(ErrorCode.SYSTEM_INTERNAL_ERROR)
def get_all_audit_logs(
    current_user: RequiredUser,
    session: Session = Depends(get_session),
    user_id: Optional[int] = Query(None, description="按用户过滤"),
    action: Optional[str] = Query(None, description="按操作类型过滤"),
    resource_type: Optional[str] = Query(None, description="按资源类型过滤"),
    limit: int = Query(500, ge=1, le=5000, description="返回数量限制"),
):
    """
    获取全局审计日志 - 仅限管理员或具有VIEW_AUDIT_LOG权限
    """
    # 检查权限
    user_role = Role(current_user.role)
    if not has_permission(user_role, Permission.VIEW_AUDIT_LOG) and not current_user.is_admin:
        raise AuthorizationException(
            code=ErrorCode.AUTHZ_PERMISSION_DENIED,
            message="Permission denied: VIEW_AUDIT_LOG required",
        )
    
    logs = get_audit_logs(
        session,
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        limit=limit,
    )
    
    return {
        "logs": [
            AuditLogResponse(
                id=log.id or 0,
                user_id=log.user_id or 0,
                action=log.action,
                resource_type=log.resource_type,
                resource_id=log.resource_id,
                details=log.details,
                ip_address=log.ip_address,
                user_agent=log.user_agent,
                status=log.status,
                error_message=log.error_message,
                created_at=log.created_at,
            )
            for log in logs
        ],
        "total": len(logs),
    }


@router.get("/audit-logs/{log_id}")
@handle_exceptions(ErrorCode.SYSTEM_INTERNAL_ERROR)
def get_audit_log_detail(
    log_id: int,
    current_user: RequiredUser,
    session: Session = Depends(get_session),
):
    """
    获取单个审计日志详情
    """
    log = session.exec(
        select(AuditLog).where(AuditLog.id == log_id, AuditLog.deleted_at.is_(None))  # type: ignore[union-attr]
    ).first()
    
    if not log:
        raise ResourceNotFoundException(
            message="Audit log not found",
            details={"resource_type": "audit_log", "resource_id": log_id},
        )
    
    # 用户只能查看自己的日志，除非是管理员
    if log.user_id != current_user.id and not current_user.is_admin:
        raise AuthorizationException(
            code=ErrorCode.AUTHZ_PERMISSION_DENIED,
            message="Access denied",
        )
    
    return AuditLogResponse(
        id=log.id or 0,
        user_id=log.user_id or 0,
        action=log.action,
        resource_type=log.resource_type,
        resource_id=log.resource_id,
        details=log.details,
        ip_address=log.ip_address,
        user_agent=log.user_agent,
        status=log.status,
        error_message=log.error_message,
        created_at=log.created_at,
    )


@router.post("/audit-logs/manual")
@handle_exceptions(ErrorCode.SYSTEM_INTERNAL_ERROR)
def log_manual_action(
    current_user: RequiredUser,
    session: Session = Depends(get_session),
    action: str = Query(..., description="操作类型"),
    resource_type: str = Query(..., description="资源类型"),
    resource_id: Optional[str] = Query(None, description="资源ID"),
):
    """
    手动记录自定义审计日志
    """
    log = log_action(
        session,
        user_id=current_user.id or 0,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details={"manual": True},
    )
    
    return AuditLogResponse(
        id=log.id or 0,
        user_id=log.user_id or 0,
        action=log.action,
        resource_type=log.resource_type,
        resource_id=log.resource_id,
        details=log.details,
        ip_address=log.ip_address,
        user_agent=log.user_agent,
        status=log.status,
        error_message=log.error_message,
        created_at=log.created_at,
    )
