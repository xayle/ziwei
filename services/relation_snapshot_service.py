"""Query relation_v1 snapshots (BE-R16)."""

from __future__ import annotations

from typing import Any

from fastapi import HTTPException
from sqlalchemy import desc
from sqlmodel import Session, select

from app.models import Snapshot, User
from app.schemas.relation_compat import (
    RelationFullResponse,
    RelationSnapshotDetail,
    RelationSnapshotSummary,
)
from services.relation_engine.case_resolver import load_case_for_user

_RELATION_KINDS = frozenset({"relation_v1", "relation"})


def _partner_case_id(case_id: str, flags: dict[str, Any] | None) -> str | None:
    if not flags:
        return None
    a_id = flags.get("case_a_id")
    b_id = flags.get("case_b_id")
    if case_id == a_id:
        return str(b_id) if b_id else None
    if case_id == b_id:
        return str(a_id) if a_id else None
    return None


def _summary_from_snapshot(snap: Snapshot, *, case_id: str, partner_case_id: str) -> RelationSnapshotSummary:
    flags = snap.compute_flags or {}
    output = snap.output_json or {}
    pa = output.get("person_a") or {}
    pb = output.get("person_b") or {}
    relation_type = flags.get("relation_type") or output.get("relation_type") or "couple"
    return RelationSnapshotSummary(
        id=str(snap.id),
        case_id=case_id,
        partner_case_id=partner_case_id,
        relation_type=relation_type,
        combined_score=output.get("combined_score"),
        grade=output.get("grade"),
        person_a_label=pa.get("label"),
        person_b_label=pb.get("label"),
        created_at=snap.created_at,
    )


def list_relation_snapshots(
    session: Session,
    user: User,
    *,
    case_id: str,
    partner_case_id: str | None = None,
    limit: int = 20,
) -> list[RelationSnapshotSummary]:
    load_case_for_user(session, case_id, user)
    created_col = Snapshot.created_at  # type: ignore[assignment]
    stmt = (
        select(Snapshot)
        .where(
            Snapshot.case_id == case_id,
            Snapshot.kind.in_(tuple(_RELATION_KINDS)),  # type: ignore[union-attr]
            Snapshot.deleted_at.is_(None),  # type: ignore[union-attr]
        )
        .order_by(desc(created_col))
        .limit(limit)
    )
    snaps = session.exec(stmt).all()
    results: list[RelationSnapshotSummary] = []
    for snap in snaps:
        partner = _partner_case_id(case_id, snap.compute_flags)
        if not partner:
            inp = snap.input_json or {}
            partner = inp.get("case_b_id") or inp.get("case_a_id")
            if partner == case_id:
                partner = inp.get("case_a_id") if inp.get("case_b_id") == case_id else inp.get("case_b_id")
        if not partner:
            continue
        if partner_case_id and str(partner) != partner_case_id:
            continue
        results.append(_summary_from_snapshot(snap, case_id=case_id, partner_case_id=str(partner)))
    return results


def get_relation_snapshot_detail(
    session: Session,
    user: User,
    snapshot_id: str,
) -> RelationSnapshotDetail:
    snap = session.exec(
        select(Snapshot).where(
            Snapshot.id == snapshot_id,
            Snapshot.deleted_at.is_(None),  # type: ignore[union-attr]
        )
    ).first()
    if snap is None or snap.kind not in _RELATION_KINDS:
        raise HTTPException(404, "Relation snapshot not found")
    load_case_for_user(session, str(snap.case_id), user)
    flags = snap.compute_flags or {}
    partner = _partner_case_id(str(snap.case_id), flags)
    if not partner:
        inp = snap.input_json or {}
        for key in ("case_a_id", "case_b_id"):
            cid = inp.get(key)
            if cid and str(cid) != str(snap.case_id):
                partner = str(cid)
                break
    if not partner:
        raise HTTPException(422, "Snapshot missing partner case reference")

    output_raw = snap.output_json or {}
    relation_full = output_raw.get("relation_full_v1") or output_raw
    if relation_full.get("schema_version") != "relation-compat@1.0":
        raise HTTPException(422, "Snapshot output is not relation-compat@1.0")
    relation_type = flags.get("relation_type") or relation_full.get("relation_type") or "couple"
    return RelationSnapshotDetail(
        snapshot_id=str(snap.id),
        case_id=str(snap.case_id),
        partner_case_id=str(partner),
        relation_type=relation_type,
        output=RelationFullResponse(**relation_full),
    )
