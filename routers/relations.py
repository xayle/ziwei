from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Iterable
from uuid import uuid4
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, status
from sqlmodel import Session, select

from app.dependencies import RequiredUser
from app.error_handling import handle_exceptions
from app.exceptions import (
    AuthorizationException,
    ErrorCode,
    ResourceNotFoundException,
    ValidationException,
)
from app.models import Case, Snapshot
from app.schemas import (
    BaziFullRequest,
    RelationComputeRequest,
    RelationComputeResponse,
    RelationPoint,
    RelationProfile,
    RelationResult,
)
from constants import API_VERSION, RULE_VERSION
from db import get_session
from services.bazi_full_service import bazi_full
from services.normalize_input import validate_lon_strict, warn_lon_cn_range

router = APIRouter(prefix="/api/v1/relations", tags=["relations"])


_CLASH = {
    ("子", "午"), ("午", "子"),
    ("丑", "未"), ("未", "丑"),
    ("寅", "申"), ("申", "寅"),
    ("卯", "酉"), ("酉", "卯"),
    ("辰", "戌"), ("戌", "辰"),
    ("巳", "亥"), ("亥", "巳"),
}

_HARM = {
    ("子", "未"), ("未", "子"),
    ("丑", "午"), ("午", "丑"),
    ("寅", "巳"), ("巳", "寅"),
    ("卯", "辰"), ("辰", "卯"),
    ("申", "亥"), ("亥", "申"),
    ("酉", "戌"), ("戌", "酉"),
}

_COMBINE = {
    ("子", "丑"), ("丑", "子"),
    ("寅", "亥"), ("亥", "寅"),
    ("卯", "戌"), ("戌", "卯"),
    ("辰", "酉"), ("酉", "辰"),
    ("巳", "申"), ("申", "巳"),
    ("午", "未"), ("未", "午"),
}


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _parse_dt_local(dt_local: str, tz: str) -> datetime:
    try:
        dt = datetime.fromisoformat(dt_local)
    except ValueError as exc:
        raise ValidationException(
            code=ErrorCode.VALIDATION_INVALID_FORMAT,
            message="birth_dt_local must be ISO8601 without offset",
            details={"error": str(exc)},
        )
    if dt.tzinfo is not None and dt.utcoffset() is not None:
        raise ValidationException(
            code=ErrorCode.VALIDATION_INVALID_INPUT,
            message="birth_dt_local must be naive",
        )
    try:
        zone = ZoneInfo(tz)
    except Exception as exc:  # pragma: no cover - defensive
        raise ValidationException(
            code=ErrorCode.VALIDATION_INVALID_FORMAT,
            message="tz must be valid IANA name",
            details={"error": str(exc)},
        )
    return dt.replace(tzinfo=zone)


def _store_snapshot(
    session: Session,
    case: Case,
    kind: str,
    compute_flags: dict[str, Any],
    input_json: dict[str, Any],
    output_json: dict[str, Any],
) -> Snapshot:
    snap = Snapshot(
        case_id=case.id,
        kind=kind,
        compute_flags=compute_flags,
        input_json=input_json,
        output_json=output_json,
        api_version=API_VERSION,
        rule_version=RULE_VERSION,
    )
    session.add(snap)
    session.commit()
    session.refresh(snap)
    return snap


def _extract_branches(payload: dict) -> list[str]:
    pillars = payload.get("pillars_primary") or {}
    branches: list[str] = []
    for key in ("year", "month", "day", "hour"):
        pillar = pillars.get(key) or {}
        branch = pillar.get("branch")
        if isinstance(branch, str):
            branches.append(branch)
    return branches


def _build_profile(case: Case, payload: dict) -> RelationProfile:
    wuxing = payload.get("wuxing_score") or {}
    favor = []
    avoid = []
    yongshen = payload.get("yongshen") or {}
    if isinstance(yongshen.get("favor"), list):
        favor = list(yongshen.get("favor") or [])
    if isinstance(yongshen.get("avoid"), list):
        avoid = list(yongshen.get("avoid") or [])
    dominant = None
    if wuxing:
        dominant = max(wuxing.items(), key=lambda kv: kv[1])[0]
    return RelationProfile(
        case_id=case.id,
        name=case.name,
        dominant_element=dominant,
        yongshen_favor=favor,
        yongshen_avoid=avoid,
        wuxing_score={k: float(v) for k, v in wuxing.items() if isinstance(v, (int, float))},
    )


def _score_elements(a: RelationProfile, b: RelationProfile) -> tuple[list[RelationPoint], list[RelationPoint]]:
    supports: list[RelationPoint] = []
    conflicts: list[RelationPoint] = []

    if a.dominant_element and a.dominant_element in b.yongshen_favor:
        supports.append(RelationPoint(tag="favor", detail=f"{a.name}主用元素 {a.dominant_element} 扶助 {b.name}", weight=12))
    if b.dominant_element and b.dominant_element in a.yongshen_favor:
        supports.append(RelationPoint(tag="favor", detail=f"{b.name}主用元素 {b.dominant_element} 扶助 {a.name}", weight=12))

    if a.dominant_element and a.dominant_element in b.yongshen_avoid:
        conflicts.append(RelationPoint(tag="avoid", detail=f"{a.name}主用元素 {a.dominant_element} 被 {b.name}忌讳", weight=-12))
    if b.dominant_element and b.dominant_element in a.yongshen_avoid:
        conflicts.append(RelationPoint(tag="avoid", detail=f"{b.name}主用元素 {b.dominant_element} 被 {a.name}忌讳", weight=-12))

    shared_favor = set(a.yongshen_favor) & set(b.yongshen_favor)
    if shared_favor:
        supports.append(RelationPoint(tag="shared_favor", detail=f"共同喜用: {', '.join(sorted(shared_favor))}", weight=8))

    shared_avoid = set(a.yongshen_avoid) & set(b.yongshen_avoid)
    if shared_avoid:
        conflicts.append(RelationPoint(tag="shared_avoid", detail=f"共同忌神: {', '.join(sorted(shared_avoid))}", weight=-6))

    # Balance gap on five elements
    if a.wuxing_score and b.wuxing_score:
        gap = 0.0
        for elem in ("wood", "fire", "earth", "metal", "water"):
            gap += abs(a.wuxing_score.get(elem, 0.0) - b.wuxing_score.get(elem, 0.0))
        if gap <= 80:
            supports.append(RelationPoint(tag="balance", detail="五行强弱接近，易互补", weight=6))
        else:
            conflicts.append(RelationPoint(tag="imbalance", detail="五行差距较大，需协调用神", weight=-6))

    return supports, conflicts


def _score_branches(branches_a: Iterable[str], branches_b: Iterable[str]) -> tuple[list[RelationPoint], list[RelationPoint]]:
    supports: list[RelationPoint] = []
    conflicts: list[RelationPoint] = []
    for ba in branches_a:
        for bb in branches_b:
            if (ba, bb) in _CLASH:
                conflicts.append(RelationPoint(tag="clash", detail=f"{ba}-{bb} 相冲", weight=-10))
            elif (ba, bb) in _HARM:
                conflicts.append(RelationPoint(tag="harm", detail=f"{ba}-{bb} 相害", weight=-8))
            elif (ba, bb) in _COMBINE:
                supports.append(RelationPoint(tag="combine", detail=f"{ba}-{bb} 六合/合化", weight=6))
    return supports, conflicts


def _aggregate_score(supports: list[RelationPoint], conflicts: list[RelationPoint], relation_type: str) -> tuple[float, str]:
    base = 60.0
    support_score = sum(p.weight for p in supports)
    conflict_score = sum(abs(p.weight) for p in conflicts)
    raw = base + support_score - conflict_score

    # Relation-specific nudges
    if relation_type == "couple":
        raw += 2
    elif relation_type == "parent_child":
        raw += 1

    score = max(0.0, min(100.0, raw))
    summary = f"匹配度 {score:.1f}/100，助力 {len(supports)} 项，冲突 {len(conflicts)} 项"
    return score, summary


def _compute_relation(
    profile_a: RelationProfile,
    profile_b: RelationProfile,
    branches_a: list[str],
    branches_b: list[str],
    relation_type: str,
) -> RelationResult:
    support_points: list[RelationPoint] = []
    conflict_points: list[RelationPoint] = []

    se_support, se_conflict = _score_elements(profile_a, profile_b)
    support_points.extend(se_support)
    conflict_points.extend(se_conflict)

    br_support, br_conflict = _score_branches(branches_a, branches_b)
    support_points.extend(br_support)
    conflict_points.extend(br_conflict)

    score, summary = _aggregate_score(support_points, conflict_points, relation_type)

    advice_parts = []
    if conflict_points:
        advice_parts.append("建议：化解冲突元素，优先使用共同喜用神，避免共同忌神。")
    if not conflict_points and support_points:
        advice_parts.append("助力较多，可保持当前节奏，放大共同优势。")
    if not advice_parts:
        advice_parts.append("关系平稳，可根据实际需要调整。")

    return RelationResult(
        relation_type=relation_type,  # type: ignore[arg-type]
        compatibility_score=score,
        summary=summary,
        support_points=support_points,
        conflict_points=conflict_points,
        advice=" ".join(advice_parts),
        meta={},
    )


@router.post("/compat", response_model=RelationComputeResponse, status_code=status.HTTP_200_OK)
@handle_exceptions(ErrorCode.SYSTEM_INTERNAL_ERROR)
def compute_relation(
    payload: RelationComputeRequest,
    current_user: RequiredUser,
    session: Session = Depends(get_session),
):
    if payload.case_a_id == payload.case_b_id:
        raise ValidationException(
            code=ErrorCode.VALIDATION_INVALID_INPUT,
            message="case_a_id and case_b_id must be different",
        )

    case_ids = [payload.case_a_id, payload.case_b_id]
    cases = session.exec(
        select(Case).where(Case.id.in_(case_ids), Case.deleted_at.is_(None))  # type: ignore
    ).all()
    case_map = {c.id: c for c in cases}
    if payload.case_a_id not in case_map or payload.case_b_id not in case_map:
        missing = [cid for cid in case_ids if cid not in case_map]
        raise ResourceNotFoundException(
            message="case not found",
            details={"missing": missing},
        )

    # 两个 case 都必须归属当前用户
    for cid, case in case_map.items():
        if case.owner_id is not None and case.owner_id != current_user.id:
            raise AuthorizationException(
                code=ErrorCode.AUTHZ_PERMISSION_DENIED,
                message="You don't have permission to access this case",
                details={"case_id": cid},
            )

    relation_request_id = str(uuid4())

    def get_or_compute(case: Case) -> tuple[dict, Snapshot]:
        snap = session.exec(
            select(Snapshot)
            .where(
                Snapshot.case_id == case.id,
                Snapshot.kind == "bazi",
                Snapshot.deleted_at.is_(None),  # type: ignore[union-attr]
            )
            .order_by(Snapshot.created_at.desc())  # type: ignore[union-attr]  # type: ignore[union-attr]
        ).first()

        if snap and snap.output_json:
            return snap.output_json, snap

        dt_aware = _parse_dt_local(case.birth_dt_local, case.tz)
        lon = validate_lon_strict(case.lon)
        warnings = warn_lon_cn_range(case.tz, lon)
        compute_flags = {
            "relation_request_id": relation_request_id,
            "warnings": warnings,
            "effective": {
                "dt_local": case.birth_dt_local,
                "tz": case.tz,
                "lon": lon,
                "mode": "dual",
                "solar_time_enabled": case.solar_time_enabled,
            },
        }
        bazi_payload = BaziFullRequest(
            dt=dt_aware,
            tz=case.tz,
            lon=lon,
            mode="dual",
            solar_time_enabled=case.solar_time_enabled,
            liunian_years=[-2, 2],
        )
        bazi_result = bazi_full(bazi_payload, request_id=relation_request_id)
        output = bazi_result.model_dump()
        snap_new = _store_snapshot(
            session,
            case,
            kind="bazi",
            compute_flags=compute_flags,
            input_json=compute_flags.get("effective", {}),
            output_json=output,
        )
        return output, snap_new

    payload_a, snap_a = get_or_compute(case_map[payload.case_a_id])
    payload_b, snap_b = get_or_compute(case_map[payload.case_b_id])

    profile_a = _build_profile(case_map[payload.case_a_id], payload_a)
    profile_b = _build_profile(case_map[payload.case_b_id], payload_b)

    branches_a = _extract_branches(payload_a)
    branches_b = _extract_branches(payload_b)

    result = _compute_relation(profile_a, profile_b, branches_a, branches_b, payload.relation_type)

    # Persist relation snapshot to both cases for追溯
    relation_flags = {
        "relation_request_id": relation_request_id,
        "relation_type": payload.relation_type,
        "case_a_id": payload.case_a_id,
        "case_b_id": payload.case_b_id,
    }
    relation_snapshot_ids: list[str] = []
    for case in (case_map[payload.case_a_id], case_map[payload.case_b_id]):
        snap_rel = _store_snapshot(
            session,
            case,
            kind="relation",
            compute_flags=relation_flags,
            input_json={"case_a": payload.case_a_id, "case_b": payload.case_b_id},
            output_json=result.model_dump(),
        )
        relation_snapshot_ids.append(snap_rel.id)
        case.last_snapshot_at = _now_utc()
        case.updated_at = _now_utc()
        session.add(case)
    session.commit()

    return RelationComputeResponse(
        case_a=profile_a,
        case_b=profile_b,
        result=result,
        snapshots_created=[snap_a.id, snap_b.id, *relation_snapshot_ids],
    )
