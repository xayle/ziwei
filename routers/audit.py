"""
审计日志路由 - 查看操作历史和安全审计
"""
from datetime import datetime
import json
from typing import Any, Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, model_validator
from sqlalchemy import func
from sqlmodel import Session, select

from app.dependencies import RequiredUser
from app.error_handling import handle_exceptions
from app.exceptions import (
    AuthorizationException,
    ErrorCode,
    ResourceNotFoundException,
)
from app.models import AuditLog, User
from db import get_session
from services.delegation_service import get_audit_logs, log_action
from services.permission_service import Permission, Role, has_permission

router = APIRouter(prefix="/api/v1", tags=["audit"])


class AuditLogResponse(BaseModel):
    """审计日志响应（N3.06：新增 RBAC 操作关键字段）"""
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
    # N3.06 新增字段：从 details JSON 提取，approve/reject/revoke 操作可用
    old_status: Optional[str] = None
    new_status: Optional[str] = None
    operator_id: Optional[int] = None

    @model_validator(mode="after")  # type: ignore[misc]
    def _extract_rbac_fields(self) -> "AuditLogResponse":
        """从 details JSON 中提取 RBAC 关键字段（仅在字段未显式设置时）"""
        if self.details and self.action in (
            "approve_permission", "reject_permission", "revoke_permission"
        ):
            try:
                d: dict[str, Any] = json.loads(self.details)
                if self.old_status is None:
                    self.old_status = d.get("old_status")
                if self.new_status is None:
                    self.new_status = d.get("new_status")
                if self.operator_id is None:
                    self.operator_id = d.get("operator_id")
            except (json.JSONDecodeError, TypeError):
                pass
        return self


@router.get("/audit-logs")
@handle_exceptions(ErrorCode.SYSTEM_INTERNAL_ERROR)
def get_user_audit_logs(
    current_user: RequiredUser,
    session: Session = Depends(get_session),
    action: Optional[str] = Query(None, description="按操作类型过滤"),
    resource_type: Optional[str] = Query(None, description="按资源类型过滤"),
    limit: int = Query(50, ge=1, le=200, description="返回数量限制"),
    before_id: Optional[int] = Query(None, description="keyset 分页游标：仅返回 id 小于此值的记录"),
):
    """
    获取当前用户的审计日志（keyset 分页：传入 next_cursor 作为下次 before_id）
    """
    # 基础过滤条件（不含游标）
    base_filters = [
        AuditLog.deleted_at.is_(None),  # type: ignore[union-attr]
        AuditLog.user_id == current_user.id,
    ]
    if action:
        base_filters.append(AuditLog.action == action)  # type: ignore[arg-type]
    if resource_type:
        base_filters.append(AuditLog.resource_type == resource_type)  # type: ignore[arg-type]

    # COUNT 查询获取真实总数（游标无关）
    count_stmt = select(func.count()).select_from(AuditLog).where(*base_filters)
    total_count: int = session.exec(count_stmt).one()  # type: ignore[assignment]

    logs = get_audit_logs(
        session,
        user_id=current_user.id,
        action=action,
        resource_type=resource_type,
        limit=limit,
        before_id=before_id,
    )

    next_cursor = logs[-1].id if len(logs) == limit else None

    return {
        "items": [
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
        "total": total_count,
        "next_cursor": next_cursor,
    }


@router.get("/audit-logs/admin")
@handle_exceptions(ErrorCode.SYSTEM_INTERNAL_ERROR)
def get_all_audit_logs(
    current_user: RequiredUser,
    session: Session = Depends(get_session),
    user_id: Optional[int] = Query(None, description="按用户过滤"),
    action: Optional[str] = Query(None, description="按操作类型过滤"),
    resource_type: Optional[str] = Query(None, description="按资源类型过滤"),
    limit: int = Query(100, ge=1, le=1000, description="返回数量限制"),
    before_id: Optional[int] = Query(None, description="keyset 分页游标：仅返回 id 小于此值的记录"),
):
    """
    获取全局审计日志 - 仅限管理员或具有VIEW_AUDIT_LOG权限（keyset 分页）
    """
    # 检查权限
    user_role = Role(current_user.role)
    if not has_permission(user_role, Permission.VIEW_AUDIT_LOG) and not current_user.is_admin:
        raise AuthorizationException(
            code=ErrorCode.AUTHZ_PERMISSION_DENIED,
            message="Permission denied: VIEW_AUDIT_LOG required",
        )

    # 基础过滤条件（不含游标）
    admin_base_filters: list = [AuditLog.deleted_at.is_(None)]  # type: ignore[union-attr]
    if user_id:
        admin_base_filters.append(AuditLog.user_id == user_id)  # type: ignore[arg-type]
    if action:
        admin_base_filters.append(AuditLog.action == action)  # type: ignore[arg-type]
    if resource_type:
        admin_base_filters.append(AuditLog.resource_type == resource_type)  # type: ignore[arg-type]

    # COUNT 查询获取真实总数
    admin_count_stmt = select(func.count()).select_from(AuditLog).where(*admin_base_filters)
    admin_total_count: int = session.exec(admin_count_stmt).one()  # type: ignore[assignment]

    logs = get_audit_logs(
        session,
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        limit=limit,
        before_id=before_id,
    )

    next_cursor = logs[-1].id if len(logs) == limit else None

    return {
        "items": [
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
        "total": admin_total_count,
        "next_cursor": next_cursor,
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


class ManualAuditLogRequest(BaseModel):
    """手动审计日志请求体"""
    action: str
    resource_type: str
    resource_id: Optional[str] = None


@router.post("/audit-logs/manual")
@handle_exceptions(ErrorCode.SYSTEM_INTERNAL_ERROR)
def log_manual_action(
    body: ManualAuditLogRequest,
    current_user: RequiredUser,
    session: Session = Depends(get_session),
):
    """
    手动记录自定义审计日志
    """
    action = body.action
    resource_type = body.resource_type
    resource_id = body.resource_id
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


@router.get("/admin/stats")
@handle_exceptions(ErrorCode.SYSTEM_INTERNAL_ERROR)
def admin_stats(
    current_user: RequiredUser,
    session: Session = Depends(get_session),
):
    """
    管理员统计面板 — 仅限 is_admin=True 的用户
    返回: 用户、审计日志、案例、快照、审核、相似盘库、API Key、实验等统计
    """
    if not current_user.is_admin:
        raise AuthorizationException(
            code=ErrorCode.AUTHZ_PERMISSION_DENIED,
            message="Permission denied: admin required",
        )

    from datetime import timezone

    from app.models.api_key import ApiKey
    from app.models.case import Case, Snapshot
    from app.models.chart_case import ChartCase
    from app.models.experiment import Experiment, ExperimentEvent
    from app.models.review import ChartReview

    def _count(model, *filters):
        stmt = select(func.count()).select_from(model)
        for f in filters:
            stmt = stmt.where(f)
        return session.exec(stmt).one() or 0

    total_users: int   = _count(User, User.deleted_at.is_(None))  # type: ignore[attr-defined]
    active_users: int  = _count(User, User.deleted_at.is_(None), User.is_active.is_(True))  # type: ignore[attr-defined]
    total_audit_logs: int = _count(AuditLog, AuditLog.deleted_at.is_(None))  # type: ignore[attr-defined]
    total_cases:     int  = _count(Case,      Case.deleted_at.is_(None))  # type: ignore[attr-defined]
    total_snapshots: int  = _count(Snapshot,  Snapshot.deleted_at.is_(None))  # type: ignore[attr-defined]
    total_chart_cases: int = _count(ChartCase, ChartCase.deleted_at.is_(None))  # type: ignore[attr-defined]

    # 审核统计
    review_pending:  int = _count(ChartReview, ChartReview.deleted_at.is_(None), ChartReview.status == "pending")  # type: ignore[attr-defined]
    review_approved: int = _count(ChartReview, ChartReview.deleted_at.is_(None), ChartReview.status == "approved")  # type: ignore[attr-defined]
    review_rejected: int = _count(ChartReview, ChartReview.deleted_at.is_(None), ChartReview.status == "rejected")  # type: ignore[attr-defined]
    review_revised:  int = _count(ChartReview, ChartReview.deleted_at.is_(None), ChartReview.status == "revised")  # type: ignore[attr-defined]

    # API Key 统计
    total_api_keys:  int = _count(ApiKey, ApiKey.revoked_at.is_(None))  # type: ignore[attr-defined]

    # 实验统计
    total_experiments: int          = _count(Experiment)
    running_experiments: int        = _count(Experiment, Experiment.status == "running")  # type: ignore[attr-defined]
    total_experiment_events: int    = _count(ExperimentEvent)

    # 最活跃格局（前 5）
    top_patterns: list[dict] = []
    try:
        pattern_rows = session.exec(
            select(ChartCase.pattern_summary)
            .where(ChartCase.deleted_at.is_(None))  # type: ignore[attr-defined]
            .where(ChartCase.pattern_summary != "")
        ).all()
        from collections import Counter
        pctr: Counter = Counter()
        for row in pattern_rows:
            for pn in row.split(","):
                pn = pn.strip()
                if pn:
                    pctr[pn] += 1
        top_patterns = [{"name": n, "count": c} for n, c in pctr.most_common(5)]
    except Exception:
        pass

    # 最活跃五行局（前 6）
    top_wuxing: list[dict] = []
    try:
        wj_rows = session.exec(
            select(ChartCase.wuxing_ju_name, func.count(ChartCase.id).label("cnt"))
            .where(ChartCase.deleted_at.is_(None))  # type: ignore[attr-defined]
            .where(ChartCase.wuxing_ju_name != "")
            .group_by(ChartCase.wuxing_ju_name)
            .order_by(func.count(ChartCase.id).desc())
            .limit(6)
        ).all()
        top_wuxing = [{"name": row[0], "count": row[1]} for row in wj_rows]
    except Exception:
        pass

    return {
        "users": {
            "total": total_users,
            "active": active_users,
            "inactive": total_users - active_users,
        },
        "audit_logs": {"total": total_audit_logs},
        "cases": {"total": total_cases},
        "snapshots": {"total": total_snapshots},
        "chart_cases": {"total": total_chart_cases},
        "reviews": {
            "pending": review_pending,
            "approved": review_approved,
            "rejected": review_rejected,
            "revised": review_revised,
            "total": review_pending + review_approved + review_rejected + review_revised,
        },
        "api_keys": {"total": total_api_keys},
        "experiments": {
            "total": total_experiments,
            "running": running_experiments,
            "total_events": total_experiment_events,
        },
        "top_patterns": top_patterns,
        "top_wuxing": top_wuxing,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
