from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional, Sequence, Union
from uuid import uuid4
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from app.config import settings
from app.dependencies import RequiredUser
from app.error_handling import handle_exceptions
from app.exceptions import (
    AppException,
    AuthorizationException,
    ErrorCode,
    ResourceNotFoundException,
    ValidationException,
)
from app.models import Case, Snapshot
from app.schemas import (
    BackendInfo,
    BaziFullRequest,
    ComputeRequest,
    ComputeResponse,
    ComputeTaskStatus,
    SnapshotOut,
    ValidationModel,
    WarningModel,
)
from constants import API_VERSION, RULE_VERSION
from db import get_session
from services.bazi_full_service import bazi_full
from services.delegation_service import log_action
from services.normalize_input import validate_lon_strict, warn_lon_cn_range
from verify import verify_full

router = APIRouter(prefix="/api/v1/cases", tags=["compute"])


def _now_utc():
    return datetime.now(timezone.utc)


def _parse_dt_local(dt_local: str, tz: str) -> datetime:
    try:
        dt = datetime.fromisoformat(dt_local)
    except ValueError:
        raise ValidationException(
            code=ErrorCode.VALIDATION_INVALID_FORMAT,
            message="dt_local must be ISO8601 without offset",
        )
    if dt.tzinfo is not None and dt.utcoffset() is not None:
        raise ValidationException(
            code=ErrorCode.VALIDATION_INVALID_INPUT,
            message="dt_local must be naive (no offset)",
        )
    try:
        zone = ZoneInfo(tz)
    except Exception:
        raise ValidationException(
            code=ErrorCode.VALIDATION_INVALID_FORMAT,
            message="tz must be a valid IANA timezone",
        )
    return dt.replace(tzinfo=zone)


WarningLike = Union[dict[str, Any], str]


def _build_warning_objects(raw_warnings: Sequence[WarningLike]) -> list[WarningModel]:
    parsed: list[WarningModel] = []
    for w in raw_warnings:
        if isinstance(w, dict):
            parsed.append(WarningModel.model_validate(w))
        else:
            parsed.append(WarningModel(code="legacy", message=str(w)))
    return parsed


def _store_snapshot(
    session: Session,
    case: Case,
    kind: str,
    compute_flags: Dict[str, Any],
    input_json: Dict[str, Any],
    output_json: Dict[str, Any],
    backend_json: Optional[Dict[str, Any]] = None,
    summary_level: Optional[str] = None,
    summary_warning_count: Optional[int] = None,
    summary_diff_count: Optional[int] = None,
) -> Snapshot:
    snap = Snapshot(
        case_id=case.id,
        kind=kind,
        compute_flags=compute_flags,
        input_json=input_json,
        output_json=output_json,
        backend_json=backend_json,
        api_version=API_VERSION,
        rule_version=RULE_VERSION,
        summary_level=summary_level,
        summary_warning_count=summary_warning_count,
        summary_diff_count=summary_diff_count,
    )
    session.add(snap)
    session.commit()
    session.refresh(snap)
    return snap


def _do_compute_for_case(
    session: Session,
    case: Case,
    payload: ComputeRequest,
) -> ComputeResponse:
    """核心计算逻辑：对已存在的 Case 执行 bazi+verify 并写入 Snapshot。
    可被 compute_case 路由和 quickstart 路由共享调用。"""
    compute_batch_id = str(uuid4())

    # Effective input assembly
    dt_local = case.birth_dt_local
    tz = case.tz
    lon = validate_lon_strict(case.lon)
    warnings = warn_lon_cn_range(tz, lon)

    mode = payload.mode or "dual"
    solar_enabled = payload.solar_time_enabled if payload.solar_time_enabled is not None else case.solar_time_enabled
    liunian_years = payload.liunian_years or [-2, 2]

    dt_aware = _parse_dt_local(dt_local, tz)

    compute_flags = {
        "compute_batch_id": compute_batch_id,
        "requested": payload.model_dump(),
        "effective": {
            "dt_local": dt_local,
            "tz": tz,
            "lon": lon,
            "mode": mode,
            "solar_time_enabled": solar_enabled,
            "liunian_years": liunian_years,
        },
    }

    input_effective = compute_flags["effective"]

    snapshots_created: list[SnapshotOut] = []
    tasks_status: dict[str, ComputeTaskStatus] = {
        "bazi": ComputeTaskStatus(status="skipped", snapshot_id=None, message=None),
        "verify": ComputeTaskStatus(status="skipped", snapshot_id=None, message=None),
    }

    # --- bazi task ---
    try:
        bazi_payload = BaziFullRequest(
            dt=dt_aware,
            tz=tz,
            lon=lon,
            mode=mode,
            solar_time_enabled=solar_enabled,
            liunian_years=liunian_years,
        )
        bazi_result = bazi_full(bazi_payload, request_id=compute_batch_id)
        bazi_output = bazi_result.model_dump()
        snap_bazi = _store_snapshot(
            session,
            case,
            kind="bazi",
            compute_flags=compute_flags,
            input_json=input_effective,
            output_json=bazi_output,
            backend_json=None,
            summary_level=None,
            summary_warning_count=None,
            summary_diff_count=None,
        )
        snapshots_created.append(SnapshotOut.model_validate(snap_bazi))
        tasks_status["bazi"] = ComputeTaskStatus(status="success", snapshot_id=snap_bazi.id, message=None)
    except AppException as exc:
        error_payload = {
            "status": "failed",
            "error": {"code": exc.code.value, "message": exc.message, "detail": exc.details},
            "warnings": warnings,
            "request_id": compute_batch_id,
        }
        snap_bazi = _store_snapshot(
            session, case, kind="bazi",
            compute_flags=compute_flags, input_json=input_effective, output_json=error_payload,
            backend_json=None, summary_level=None, summary_warning_count=None, summary_diff_count=None,
        )
        snapshots_created.append(SnapshotOut.model_validate(snap_bazi))
        tasks_status["bazi"] = ComputeTaskStatus(status="failed", snapshot_id=snap_bazi.id, message=exc.message)
    except Exception as exc:
        error_payload = {
            "status": "failed",
            "error": {"code": "exception", "message": str(exc), "detail": {}},
            "warnings": warnings,
            "request_id": compute_batch_id,
        }
        snap_bazi = _store_snapshot(
            session, case, kind="bazi",
            compute_flags=compute_flags, input_json=input_effective, output_json=error_payload,
            backend_json=None, summary_level=None, summary_warning_count=None, summary_diff_count=None,
        )
        snapshots_created.append(SnapshotOut.model_validate(snap_bazi))
        tasks_status["bazi"] = ComputeTaskStatus(status="failed", snapshot_id=snap_bazi.id, message=str(exc))

    # --- verify task ---
    try:
        result = verify_full(dt_aware, lon=lon, use_solar=solar_enabled, mode=mode)

        backend_info = BackendInfo(
            primary=settings.primary_backend,
            secondary="cnlunar" if mode == "dual" else None,
            sxtwl_available=True,
            cnlunar_available=True,
        )

        rp = {
            "year": result.pillars_primary.year.__dict__,
            "month": result.pillars_primary.month.__dict__,
            "day": result.pillars_primary.day.__dict__,
            "hour": result.pillars_primary.hour.__dict__,
        }
        rs = None
        if result.pillars_secondary:
            rs = {
                "year": result.pillars_secondary.year.__dict__,
                "month": result.pillars_secondary.month.__dict__,
                "day": result.pillars_secondary.day.__dict__,
                "hour": result.pillars_secondary.hour.__dict__,
            }

        rf = result.risk_flags.__dict__
        v_payload = result.validation.__dict__.copy()
        v_payload["risk_flags"] = rf
        raw_warnings = list(result.validation.warnings) + warnings
        parsed_warnings = [w.model_dump() for w in _build_warning_objects(raw_warnings)]
        v_payload["warnings"] = parsed_warnings
        v = ValidationModel(**v_payload)

        verify_output = {
            "api_version": API_VERSION,
            "rule_version": RULE_VERSION,
            "request_id": compute_batch_id,
            "backend": backend_info.model_dump(),
            "mode_requested": result.mode_requested,
            "mode_effective": result.mode_effective,
            "pillars_primary": rp,
            "pillars_secondary": rs,
            "risk_flags": rf,
            "validation": v.model_dump(),
            "solar_time_offset_minutes": result.solar_time_offset_minutes,
            "dt_input": dt_aware.isoformat(),
            "dt_effective_utc8": dt_aware.isoformat(),
            "tz": tz,
        }

        summary_level = v.level
        summary_warning_count = len(v.warnings)
        summary_diff_count = len(v.diff_fields)

        snap_verify = _store_snapshot(
            session, case, kind="verify",
            compute_flags=compute_flags, input_json=input_effective, output_json=verify_output,
            backend_json=None, summary_level=summary_level,
            summary_warning_count=summary_warning_count, summary_diff_count=summary_diff_count,
        )
        snapshots_created.append(SnapshotOut.model_validate(snap_verify))
        tasks_status["verify"] = ComputeTaskStatus(status="success", snapshot_id=snap_verify.id, message=None)
    except AppException as exc:
        error_payload = {
            "status": "failed",
            "error": {"code": exc.code.value, "message": exc.message, "detail": exc.details},
            "warnings": warnings,
            "request_id": compute_batch_id,
        }
        snap_verify = _store_snapshot(
            session, case, kind="verify",
            compute_flags=compute_flags, input_json=input_effective, output_json=error_payload,
            backend_json=None, summary_level=None, summary_warning_count=None, summary_diff_count=None,
        )
        snapshots_created.append(SnapshotOut.model_validate(snap_verify))
        tasks_status["verify"] = ComputeTaskStatus(status="failed", snapshot_id=snap_verify.id, message=exc.message)
    except Exception as exc:
        error_payload = {
            "status": "failed",
            "error": {"code": "exception", "message": str(exc), "detail": {}},
            "warnings": warnings,
            "request_id": compute_batch_id,
        }
        snap_verify = _store_snapshot(
            session, case, kind="verify",
            compute_flags=compute_flags, input_json=input_effective, output_json=error_payload,
            backend_json=None, summary_level=None, summary_warning_count=None, summary_diff_count=None,
        )
        snapshots_created.append(SnapshotOut.model_validate(snap_verify))
        tasks_status["verify"] = ComputeTaskStatus(status="failed", snapshot_id=snap_verify.id, message=str(exc))

    return ComputeResponse(
        compute_batch_id=compute_batch_id,
        case_id=case.id,
        input_effective=input_effective,
        tasks=tasks_status,
        snapshots_created=snapshots_created,
    )


@router.post("/{case_id}/compute", response_model=ComputeResponse)
@handle_exceptions(ErrorCode.SYSTEM_INTERNAL_ERROR)
def compute_case(
    case_id: str,
    payload: ComputeRequest,
    current_user: RequiredUser,
    session: Session = Depends(get_session),
):
    case = session.exec(
        select(Case).where(Case.id == case_id, Case.deleted_at.is_(None))  # type: ignore
    ).first()
    if not case:
        raise ResourceNotFoundException(
            message="case not found",
            details={"resource_type": "case", "resource_id": case_id},
        )

    # 权限检查：只有 case 的归属用户可以触发计算
    if case.owner_id is not None and case.owner_id != current_user.id:
        raise AuthorizationException(
            code=ErrorCode.AUTHZ_PERMISSION_DENIED,
            message="You don't have permission to compute this case",
        )

    result = _do_compute_for_case(session, case, payload)
    log_action(
        session,
        user_id=current_user.id or 0,
        action="compute_case",
        resource_type="case",
        resource_id=str(case_id),
        details={"tasks": getattr(payload, "tasks", None)},  # type: ignore[misc]
    )
    return result
