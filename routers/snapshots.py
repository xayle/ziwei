from __future__ import annotations

from typing import Any, List, cast

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy import desc
from sqlmodel import Session, select

from db import get_session
from app.models import Snapshot, User
from app.schemas import SnapshotOut
from app.dependencies import require_user, RequiredUser
from app.exceptions import ErrorCode, ResourceNotFoundException
from app.error_handling import handle_exceptions

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
    return SnapshotOut.model_validate(snap)
