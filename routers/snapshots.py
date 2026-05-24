from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, cast

from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel
from sqlalchemy import desc
from sqlmodel import Session, select

from app.dependencies import RequiredUser
from app.error_handling import handle_exceptions
from app.exceptions import AuthorizationException, ErrorCode, ResourceNotFoundException
from app.models import Case, Snapshot
from app.schemas import SnapshotOut
from db import get_session
from services.delegation_service import log_action

router = APIRouter(prefix="/api/v1", tags=["snapshots"])


# ── POST /cases/{case_id}/snapshots 创建快照 ─────────────────

class SnapshotCreate(BaseModel):
    kind: str = "ziwei"
    compute_flags: Optional[Dict] = None
    input_json: Optional[Dict] = None
    output_json: Optional[Dict] = None
    backend_json: Optional[Dict] = None
    api_version: Optional[str] = None
    rule_version: Optional[str] = None
    schema_version: Optional[str] = "snapshot@5.0"
    summary_level: Optional[str] = None
    summary_warning_count: Optional[int] = None
    summary_diff_count: Optional[int] = None
    summary_engine_primary: Optional[str] = None
    note: Optional[str] = None


@router.post("/cases/{case_id}/snapshots", response_model=SnapshotOut, status_code=status.HTTP_201_CREATED)
@handle_exceptions(ErrorCode.SYSTEM_INTERNAL_ERROR)
def create_snapshot(
    case_id: str,
    payload: SnapshotCreate,
    current_user: RequiredUser,
    session: Session = Depends(get_session),
):
    """为指定 Case 创建新快照（保存排盘结果）。"""
    case = session.exec(
        select(Case).where(Case.id == case_id, Case.deleted_at.is_(None))  # type: ignore
    ).first()
    if not case:
        raise ResourceNotFoundException(
            message="Case not found",
            details={"resource_type": "case", "resource_id": case_id},
        )
    if case.owner_id is not None and case.owner_id != current_user.id:
        raise AuthorizationException(
            code=ErrorCode.AUTHZ_PERMISSION_DENIED,
            message="Permission denied: case not owned by current user",
        )
    snap = Snapshot(
        case_id=case_id,
        kind=payload.kind,
        compute_flags=payload.compute_flags,
        input_json=payload.input_json,
        output_json=payload.output_json,
        backend_json=payload.backend_json,
        api_version=payload.api_version,
        rule_version=payload.rule_version,
        schema_version=payload.schema_version or "snapshot@5.0",
        summary_level=payload.summary_level,
        summary_warning_count=payload.summary_warning_count,
        summary_diff_count=payload.summary_diff_count,
        summary_engine_primary=payload.summary_engine_primary,
        note=payload.note,
        created_at=datetime.now(timezone.utc),
    )
    session.add(snap)
    # 更新 Case 的 last_snapshot_at
    case.last_snapshot_at = snap.created_at
    if payload.api_version:
        case.api_version_last = payload.api_version
    session.add(case)
    session.commit()
    session.refresh(snap)
    log_action(
        session,
        user_id=current_user.id or 0,
        action="create_snapshot",
        resource_type="snapshot",
        resource_id=str(snap.id),
        details={"case_id": case_id, "kind": payload.kind},
    )
    return SnapshotOut.model_validate(snap)


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


# ─────────────────────────────────────────────────────────────────────────────
# W3  快照 diff  GET /api/v1/snapshots/diff?a=<id>&b=<id>
# ─────────────────────────────────────────────────────────────────────────────

class SnapshotDiffField(BaseModel):
    field: str
    value_a: Any
    value_b: Any


class SnapshotDiffResponse(BaseModel):
    snapshot_a: str
    snapshot_b: str
    changed_fields: List[SnapshotDiffField]
    added_fields: List[str]    # 在 b 中新增的键
    removed_fields: List[str]  # 在 a 中有但 b 中没有的键
    total_changes: int


def _flat_dict(d: Any, prefix: str = "") -> Dict[str, Any]:
    """递归展平嵌套 dict，用 '.' 连接键路径。"""
    result: Dict[str, Any] = {}
    if isinstance(d, dict):
        for k, v in d.items():
            full_key = f"{prefix}.{k}" if prefix else k
            if isinstance(v, dict):
                result.update(_flat_dict(v, full_key))
            else:
                result[full_key] = v
    else:
        result[prefix] = d
    return result


@router.get(
    "/snapshots/diff",
    response_model=SnapshotDiffResponse,
    summary="W3 快照字段差异对比",
    description="对比两个快照的 output_json 字段，返回变更/新增/删除的键列表，用于算法升级前后验证。",
)
@handle_exceptions(ErrorCode.SYSTEM_INTERNAL_ERROR)
def snapshot_diff(
    current_user: RequiredUser,
    a: str = Query(..., description="快照 ID A"),
    b: str = Query(..., description="快照 ID B"),
    session: Session = Depends(get_session),
) -> SnapshotDiffResponse:
    """W3: 对比两快照的 output_json，逐字段展示差异。"""
    def _get_snap(sid: str) -> Snapshot:
        s = session.exec(
            select(Snapshot).where(Snapshot.id == sid, Snapshot.deleted_at.is_(None))  # type: ignore
        ).first()
        if not s:
            raise ResourceNotFoundException(
                message=f"快照不存在: {sid}",
                details={"resource_id": sid},
            )
        # 归属权检查
        case = session.exec(
            select(Case).where(Case.id == s.case_id, Case.deleted_at.is_(None))  # type: ignore
        ).first()
        if case and case.owner_id is not None and case.owner_id != current_user.id:
            raise AuthorizationException(
                code=ErrorCode.AUTHZ_PERMISSION_DENIED,
                message="Permission denied",
            )
        return s

    snap_a = _get_snap(a)
    snap_b = _get_snap(b)

    data_a = _flat_dict(snap_a.output_json or {})
    data_b = _flat_dict(snap_b.output_json or {})

    keys_a = set(data_a.keys())
    keys_b = set(data_b.keys())

    changed: List[SnapshotDiffField] = []
    for key in sorted(keys_a & keys_b):
        if data_a[key] != data_b[key]:
            changed.append(SnapshotDiffField(field=key, value_a=data_a[key], value_b=data_b[key]))

    added = sorted(keys_b - keys_a)
    removed = sorted(keys_a - keys_b)

    return SnapshotDiffResponse(
        snapshot_a=a,
        snapshot_b=b,
        changed_fields=changed,
        added_fields=added,
        removed_fields=removed,
        total_changes=len(changed) + len(added) + len(removed),
    )
