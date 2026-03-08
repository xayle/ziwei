from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional, cast

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy import func
from sqlalchemy.sql.elements import ColumnElement
from sqlmodel import Session, select

from db import get_session
from app.models import Case, Snapshot, User
from app.schemas import CaseCreate, CaseOut, CasePatch, CaseListResponse
from app.dependencies import RequiredUser
from app.exceptions import (
    AuthorizationException,
    ErrorCode,
    ResourceNotFoundException,
)
from app.error_handling import handle_exceptions
from services.delegation_service import log_action

router = APIRouter(prefix="/api/v1/cases", tags=["cases"])


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


@router.post("", response_model=CaseOut, status_code=status.HTTP_201_CREATED)
@handle_exceptions(ErrorCode.SYSTEM_INTERNAL_ERROR)
def create_case(
    payload: CaseCreate,
    current_user: RequiredUser,
    session: Session = Depends(get_session)
):
    case = Case(**payload.model_dump())
    case.owner_id = current_user.id  # 所有权归属当前用户
    now = _now_utc()
    case.created_at = now
    case.updated_at = now
    session.add(case)
    session.commit()
    session.refresh(case)
    log_action(
        session,
        user_id=current_user.id or 0,
        action="create_case",
        resource_type="case",
        resource_id=str(case.id),
        details={"name": case.name},
    )
    return CaseOut.model_validate(case)


@router.get("", response_model=CaseListResponse)
@handle_exceptions(ErrorCode.SYSTEM_INTERNAL_ERROR)
def list_cases(
    current_user: RequiredUser,
    session: Session = Depends(get_session),
    q: Optional[str] = Query(default=None, description="Search by name substring"),
    tag: Optional[str] = Query(default=None, description="Filter by tag substring"),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    order: str = Query(default="updated_at", pattern="^(updated_at|created_at|name)$"),
    dir: str = Query(default="desc", pattern="^(asc|desc)$"),
):
    # ✅ 第一步：构建共用的 WHERE 条件
    name_col = cast(ColumnElement[str], Case.name)
    tags_col = cast(ColumnElement[str], Case.tags)

    base_filters = [Case.deleted_at.is_(None), Case.owner_id == current_user.id]  # type: ignore
    if q:
        base_filters.append(name_col.contains(q))
    if tag:
        base_filters.append(tags_col.contains(tag))

    # ✅ 第二步：COUNT 查询获取真实总数
    count_stmt = select(func.count()).select_from(Case).where(*base_filters)
    total_count: int = session.exec(count_stmt).one()  # type: ignore[assignment]

    # ✅ 第三步：获取 case 列表（1 次查询）
    order_col = cast(ColumnElement, getattr(Case, order))
    if dir == "desc":
        order_col = order_col.desc()
    else:
        order_col = order_col.asc()
    stmt = select(Case).where(*base_filters).order_by(order_col).offset(offset).limit(limit)
    cases = session.exec(stmt).all()

    if not cases:
        return {"items": [], "total": total_count, "next_cursor": None}

    # ✅ 第四步：批量加载所有 case 的最新 verify snapshot（1 次查询，而不是 N 次！）
    case_ids = [c.id for c in cases]

    # 为每个 case_id 获取最新的 snapshot
    all_snapshots = session.exec(
        select(Snapshot)
        .where(
            Snapshot.case_id.in_(case_ids),  # type: ignore[union-attr]
            Snapshot.kind == "verify",
            Snapshot.deleted_at.is_(None)  # type: ignore[union-attr]
        )
        .order_by(Snapshot.case_id, Snapshot.created_at.desc())  # type: ignore[union-attr]
    ).all()
    
    # ✅ 第五步：构建 case_id → snapshot 的映射（避免重复）
    snapshot_map = {}
    for snap in all_snapshots:
        if snap.case_id not in snapshot_map:
            snapshot_map[snap.case_id] = snap

    # ✅ 第六步：构建结果（只需数据操作，无额外数据库查询）
    results: List[CaseOut] = []
    for c in cases:
        summary = None
        latest_verify = snapshot_map.get(c.id)
        if latest_verify:
            summary = {
                "snapshot_id": latest_verify.id,
                "summary_level": latest_verify.summary_level,
                "summary_warning_count": latest_verify.summary_warning_count,
                "summary_diff_count": latest_verify.summary_diff_count,
            }
        co = CaseOut.model_validate(c)
        co.latest_verify_summary = summary
        results.append(co)
    return {
        "items": results,
        "total": total_count,
        "next_cursor": None,
    }


@router.get("/{case_id}", response_model=CaseOut)
@handle_exceptions(ErrorCode.SYSTEM_INTERNAL_ERROR)
def get_case(
    case_id: str,
    current_user: RequiredUser,
    session: Session = Depends(get_session)
):
    case = session.exec(
        select(Case).where(Case.id == case_id, Case.deleted_at.is_(None))  # type: ignore[union-attr]
    ).first()
    if not case:
        raise ResourceNotFoundException(
            message="case not found",
            details={"resource_type": "case", "resource_id": case_id},
        )
    # 所有权校验——兼容旧数据（owner_id 可能为 None）
    if case.owner_id is not None and case.owner_id != current_user.id:
        raise AuthorizationException(
            code=ErrorCode.AUTHZ_PERMISSION_DENIED,
            message="You don't have permission to access this case",
        )
    latest_verify = (
        session.exec(
            select(Snapshot)
            .where(
                Snapshot.case_id == case.id,
                Snapshot.kind == "verify",
                Snapshot.deleted_at.is_(None)  # type: ignore[union-attr]
            )
            .order_by(cast(ColumnElement[datetime], Snapshot.created_at).desc())
            .limit(1)
        ).first()
        or None
    )
    summary = None
    if latest_verify:
        summary = {
            "snapshot_id": latest_verify.id,
            "summary_level": latest_verify.summary_level,
            "summary_warning_count": latest_verify.summary_warning_count,
            "summary_diff_count": latest_verify.summary_diff_count,
        }
    co = CaseOut.model_validate(case)
    co.latest_verify_summary = summary
    return co


@router.patch("/{case_id}", response_model=CaseOut)
@handle_exceptions(ErrorCode.SYSTEM_INTERNAL_ERROR)
def patch_case(
    case_id: str,
    payload: CasePatch,
    current_user: RequiredUser,
    session: Session = Depends(get_session)
):
    case = session.exec(
        select(Case).where(Case.id == case_id, Case.deleted_at.is_(None))  # type: ignore
    ).first()
    if not case:
        raise ResourceNotFoundException(
            message="case not found",
            details={"resource_type": "case", "resource_id": case_id},
        )
    # 所有权校验
    if case.owner_id is not None and case.owner_id != current_user.id:
        raise AuthorizationException(
            code=ErrorCode.AUTHZ_PERMISSION_DENIED,
            message="You don't have permission to update this case",
        )
    data = payload.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(case, key, value)
    case.updated_at = _now_utc()
    session.add(case)
    session.commit()
    session.refresh(case)
    log_action(
        session,
        user_id=current_user.id or 0,
        action="patch_case",
        resource_type="case",
        resource_id=str(case.id),
        details={k: str(v) for k, v in data.items()},
    )
    co = CaseOut.model_validate(case)
    return co


@router.delete("/{case_id}", status_code=status.HTTP_204_NO_CONTENT)
@handle_exceptions(ErrorCode.SYSTEM_INTERNAL_ERROR)
def delete_case(
    case_id: str,
    current_user: RequiredUser,
    session: Session = Depends(get_session)
):
    """软删除 Case（设置 deleted_at）——需要所有权"""
    case = session.exec(
        select(Case).where(Case.id == case_id, Case.deleted_at.is_(None))  # type: ignore
    ).first()
    if not case:
        raise ResourceNotFoundException(
            message="case not found",
            details={"resource_type": "case", "resource_id": case_id},
        )
    if case.owner_id is not None and case.owner_id != current_user.id:
        raise AuthorizationException(
            code=ErrorCode.AUTHZ_PERMISSION_DENIED,
            message="You don't have permission to delete this case",
        )
    case.deleted_at = _now_utc()
    case.updated_at = _now_utc()
    session.add(case)
    session.commit()
    log_action(
        session,
        user_id=current_user.id or 0,
        action="delete_case",
        resource_type="case",
        resource_id=str(case_id),
    )
