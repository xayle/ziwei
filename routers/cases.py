from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import cast
from uuid import uuid4

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import func
from sqlalchemy.sql.elements import ColumnElement
from sqlmodel import Session, select

from app.dependencies import RequiredUser
from app.error_handling import handle_exceptions
from app.exceptions import (
    AuthorizationException,
    ErrorCode,
    ResourceNotFoundException,
)
from app.models import Case, Snapshot
from app.schemas import CaseCreate, CaseListResponse, CaseOut, CasePatch
from db import get_session
from services.case_leap_month import infer_case_leap_month
from services.delegation_service import log_action
from services.normalize_input import normalize_birth_datetime

router = APIRouter(prefix="/api/v1/cases", tags=["cases"])


def _now_utc() -> datetime:
    return datetime.now(UTC)


def _apply_inferred_leap_month(case: Case) -> Case:
    inferred = infer_case_leap_month(case.birth_dt_local, case.calendar_mode)
    if inferred is not None:
        case.is_leap_month = inferred
    return case


def _build_case_out(case: Case, latest_verify_summary: dict | None = None) -> CaseOut:
    inferred = infer_case_leap_month(case.birth_dt_local, case.calendar_mode)
    if inferred is not None:
        case.is_leap_month = inferred
    co = CaseOut.model_validate(case)
    co.latest_verify_summary = latest_verify_summary
    co.is_leap_month_inferred = inferred
    return co


@router.post("", response_model=CaseOut, status_code=status.HTTP_201_CREATED)
@handle_exceptions(ErrorCode.SYSTEM_INTERNAL_ERROR)
def create_case(payload: CaseCreate, current_user: RequiredUser, session: Session = Depends(get_session)):
    case_data = payload.model_dump()
    try:
        normalized_birth = normalize_birth_datetime(
            datetime.fromisoformat(payload.birth_dt_local),
            payload.tz,
            auto_dst=payload.solar_time_enabled,
            precision=payload.birth_time_precision,
            unknown_time_fallback=payload.unknown_time_fallback,
        )
        case_data["birth_dt"] = normalized_birth.normalized_birth_dt_utc
    except Exception:
        case_data["birth_dt"] = None
    inferred_leap_month = infer_case_leap_month(case_data.get("birth_dt_local"), case_data.get("calendar_mode"))
    if inferred_leap_month is not None:
        case_data["is_leap_month"] = inferred_leap_month
    # 案例未带 utm 时继承用户首触归因
    if case_data.get("utm_source") is None and getattr(current_user, "utm_source", None):
        case_data["utm_source"] = current_user.utm_source
    if case_data.get("utm_campaign") is None and getattr(current_user, "utm_campaign", None):
        case_data["utm_campaign"] = current_user.utm_campaign
    if case_data.get("content_id") is None and getattr(current_user, "content_id", None):
        case_data["content_id"] = current_user.content_id
    case = Case(**case_data)
    # 本地 bypass 兜底场景下，current_user.id 可能为空或无效。
    # 仅在用户 ID 有效时写入 owner_id，避免外键约束导致 500。
    if isinstance(current_user.id, int) and current_user.id > 0:
        case.owner_id = current_user.id  # 所有权归属当前用户
    else:
        case.owner_id = None
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
    case = _apply_inferred_leap_month(case)
    return _build_case_out(case)


@router.get("", response_model=CaseListResponse)
@handle_exceptions(ErrorCode.SYSTEM_INTERNAL_ERROR)
def list_cases(
    current_user: RequiredUser,
    session: Session = Depends(get_session),
    q: str | None = Query(default=None, description="Search by name substring"),
    tag: str | None = Query(default=None, description="Filter by tag substring"),
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
            Snapshot.deleted_at.is_(None),  # type: ignore[union-attr]
        )
        .order_by(Snapshot.case_id, Snapshot.created_at.desc())  # type: ignore[union-attr]
    ).all()

    # ✅ 第五步：构建 case_id → snapshot 的映射（避免重复）
    snapshot_map = {}
    for snap in all_snapshots:
        if snap.case_id not in snapshot_map:
            snapshot_map[snap.case_id] = snap

    # ✅ 第六步：构建结果（只需数据操作，无额外数据库查询）
    results: list[CaseOut] = []
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
        c = _apply_inferred_leap_month(c)
        results.append(_build_case_out(c, summary))
    return {
        "items": results,
        "total": total_count,
        "next_cursor": None,
    }


@router.get("/{case_id}", response_model=CaseOut)
@handle_exceptions(ErrorCode.SYSTEM_INTERNAL_ERROR)
def get_case(case_id: str, current_user: RequiredUser, session: Session = Depends(get_session)):
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
                Snapshot.deleted_at.is_(None),  # type: ignore[union-attr]
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
    case = _apply_inferred_leap_month(case)
    return _build_case_out(case, summary)


@router.patch("/{case_id}", response_model=CaseOut)
@handle_exceptions(ErrorCode.SYSTEM_INTERNAL_ERROR)
def patch_case(case_id: str, payload: CasePatch, current_user: RequiredUser, session: Session = Depends(get_session)):
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
    try:
        normalized_birth = normalize_birth_datetime(
            datetime.fromisoformat(case.birth_dt_local),
            case.tz,
            auto_dst=case.solar_time_enabled,
            precision=case.birth_time_precision,
            unknown_time_fallback=case.unknown_time_fallback,
        )
        case.birth_dt = normalized_birth.normalized_birth_dt_utc
    except Exception:
        case.birth_dt = None
    inferred_leap_month = infer_case_leap_month(case.birth_dt_local, case.calendar_mode)
    if inferred_leap_month is not None:
        case.is_leap_month = inferred_leap_month
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
    case = _apply_inferred_leap_month(case)
    return _build_case_out(case)


@router.delete("/{case_id}", status_code=status.HTTP_204_NO_CONTENT)
@handle_exceptions(ErrorCode.SYSTEM_INTERNAL_ERROR)
def delete_case(case_id: str, current_user: RequiredUser, session: Session = Depends(get_session)):
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


# ─────────────────────────────────────────────────────────────────────────────
# B6: 隐私分享链接
# ─────────────────────────────────────────────────────────────────────────────


@router.post("/{case_id}/share-token", status_code=status.HTTP_201_CREATED)
@handle_exceptions(ErrorCode.SYSTEM_INTERNAL_ERROR)
def create_share_token(
    case_id: str,
    current_user: RequiredUser,
    session: Session = Depends(get_session),
):
    """B6: 生成 24h 匹名分享 token，返回链接（不含出生日期原始数据）"""
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
            message="You don't have permission to share this case",
        )
    token = str(uuid4())
    expires_at = datetime.now(UTC) + timedelta(hours=24)
    case.share_token = token
    case.share_expires_at = expires_at
    case.updated_at = _now_utc()
    session.add(case)
    session.commit()
    return {"share_url": f"/api/v1/share/{token}", "expires_at": expires_at.isoformat()}


# NOTE: 公开分享路由（无需 token），路由前缀不同，单独注册
_share_router = APIRouter(prefix="/api/v1/share", tags=["cases"])


@_share_router.get("/{token}")
def get_shared_case(token: str, session: Session = Depends(get_session)):
    """B6: 凭 token 返回脆敏命盘（不含出生日期原始值）。token 过期 → 404"""
    case = session.exec(
        select(Case).where(Case.share_token == token, Case.deleted_at.is_(None))  # type: ignore
    ).first()
    if not case:
        raise ResourceNotFoundException(
            message="share token not found or expired",
            details={"token": token[:8] + "..."},
        )
    if case.share_expires_at and case.share_expires_at < datetime.now(UTC):
        raise ResourceNotFoundException(
            message="share token has expired",
            details={"token": token[:8] + "..."},
        )
    # 返回脆敏命盘：排除 birth_dt_local / lon / tz / notes
    return {
        "id": case.id,
        "name": case.name,
        "gender": case.gender,
        "city": case.city,
        "tags": case.tags,
        "schema_version": case.schema_version,
        "created_at": case.created_at.isoformat() if case.created_at else None,
    }
