from __future__ import annotations

from typing import Any, List, cast

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import desc
from sqlmodel import Session, select

from db import get_session
from app.models import Case, Snapshot, User
from app.schemas import SnapshotOut
from app.dependencies import require_user, RequiredUser
from app.exceptions import AuthorizationException, ErrorCode, ResourceNotFoundException
from app.error_handling import handle_exceptions
from services.delegation_service import log_action

router = APIRouter(prefix="/api/v1", tags=["snapshots"])


@router.get("/cases/{case_id}/snapshots", response_model=List[SnapshotOut])
@handle_exceptions(ErrorCode.SYSTEM_INTERNAL_ERROR)
def list_snapshots(
    case_id: str,
    current_user: RequiredUser,
    session: Session = Depends(get_session),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    # 验证 Case 存在
    case = session.exec(
        select(Case).where(Case.id == case_id, Case.deleted_at.is_(None))  # type: ignore
    ).first()
    if not case:
        raise ResourceNotFoundException(
            message="Case not found",
            details={"resource_type": "case", "resource_id": case_id},
        )
    # 验证归属权
    if case.owner_id is not None and case.owner_id != current_user.id:
        raise AuthorizationException(
            code=ErrorCode.AUTHZ_PERMISSION_DENIED,
            message="Permission denied: case not owned by current user",
        )
    created_col = cast(Any, Snapshot.created_at)  # allow SQLAlchemy column methods
    stmt = (
        select(Snapshot)
        .where(Snapshot.case_id == case_id, Snapshot.deleted_at.is_(None))  # type: ignore
        .order_by(desc(created_col))
    )
    stmt = stmt.offset(offset).limit(limit)
    snaps = session.exec(stmt).all()
    return [SnapshotOut.model_validate(s) for s in snaps]


@router.get("/snapshots/{snapshot_id}", response_model=SnapshotOut)
@handle_exceptions(ErrorCode.SYSTEM_INTERNAL_ERROR)
def get_snapshot(
    snapshot_id: str,
    current_user: RequiredUser,
    session: Session = Depends(get_session),
):
    snap = session.exec(
        select(Snapshot).where(Snapshot.id == snapshot_id, Snapshot.deleted_at.is_(None))  # type: ignore
    ).first()
    if not snap:
        raise ResourceNotFoundException(
            message="snapshot not found",
            details={"resource_type": "snapshot", "resource_id": snapshot_id},
        )
    # 验证所属 Case 的归属权
    case = session.exec(
        select(Case).where(Case.id == snap.case_id, Case.deleted_at.is_(None))  # type: ignore
    ).first()
    if case and case.owner_id is not None and case.owner_id != current_user.id:
        raise AuthorizationException(
            code=ErrorCode.AUTHZ_PERMISSION_DENIED,
            message="Permission denied: snapshot not owned by current user",
        )
    return SnapshotOut.model_validate(snap)


@router.delete("/snapshots/{snapshot_id}", status_code=status.HTTP_204_NO_CONTENT)
@handle_exceptions(ErrorCode.SYSTEM_INTERNAL_ERROR)
def delete_snapshot(
    snapshot_id: str,
    current_user: RequiredUser,
    session: Session = Depends(get_session),
):
    """软删除快照：验证归属权后设置 deleted_at。"""
    snap = session.exec(
        select(Snapshot).where(Snapshot.id == snapshot_id, Snapshot.deleted_at.is_(None))  # type: ignore
    ).first()
    if not snap:
        raise ResourceNotFoundException(
            message="snapshot not found",
            details={"resource_type": "snapshot", "resource_id": snapshot_id},
        )
    # 验证所属 Case 的归属权
    case = session.exec(
        select(Case).where(Case.id == snap.case_id, Case.deleted_at.is_(None))  # type: ignore
    ).first()
    if case and case.owner_id is not None and case.owner_id != current_user.id:
        raise AuthorizationException(
            code=ErrorCode.AUTHZ_PERMISSION_DENIED,
            message="Permission denied: snapshot not owned by current user",
        )
    snap.deleted_at = datetime.now(timezone.utc)
    session.add(snap)
    session.commit()
    log_action(
        session,
        user_id=current_user.id or 0,
        action="delete_snapshot",
        resource_type="snapshot",
        resource_id=str(snapshot_id),
        details={"case_id": str(snap.case_id)},
    )
