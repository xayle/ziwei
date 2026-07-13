"""Multi-person compatibility — optional alignment with relation/full (BE-R14)."""

from __future__ import annotations

from typing import Any

from app.schemas.relation_compat import RelationTypeEnum
from app.schemas.ziwei import MultiCompatPairResponse, ZiweiRequest
from services.relation_engine.composer import compute_relation_full


def ziwei_request_to_person(
    req: ZiweiRequest,
    *,
    label: str | None = None,
    tz: str = "Asia/Shanghai",
) -> dict[str, Any]:
    """Map ZiweiRequest birth fields to relation person input."""
    minute = req.minute or 0
    birth = f"{req.year:04d}-{req.month:02d}-{req.day:02d}T{req.hour:02d}:{minute:02d}:00"
    gender = req.gender
    if gender not in ("男", "女"):
        gender = "男" if str(gender).lower() in ("male", "m") else "女"
    return {
        "birth_datetime": birth,
        "tz": tz,
        "longitude": float(req.longitude if req.longitude is not None else 116.41),
        "gender": gender,
        "label": label or gender,
    }


def enrich_pair_with_relation_dims(
    person_a: ZiweiRequest,
    person_b: ZiweiRequest,
    *,
    relation_type: RelationTypeEnum,
    label_a: str | None,
    label_b: str | None,
    ziwei_score: int,
    max_score: int,
    level: str,
    person_a_idx: int,
    person_b_idx: int,
    supervisor_id: str | None = None,
) -> MultiCompatPairResponse:
    """Attach relation/full dual-engine scores alongside legacy ziwei matrix score."""
    pa = ziwei_request_to_person(person_a, label=label_a or f"成员{person_a_idx + 1}")
    pb = ziwei_request_to_person(person_b, label=label_b or f"成员{person_b_idx + 1}")
    relation = compute_relation_full(
        relation_type=relation_type,
        person_a=pa,
        person_b=pb,
        options={"include_bazi": True, "include_ziwei": True},
        supervisor_id=supervisor_id,
    )
    bazi_block = relation.get("bazi") or {}
    ziwei_block = relation.get("ziwei") or {}
    highlights: list[str] = []
    for dim in (relation.get("dimensions") or [])[:4]:
        highlights.append(f"{dim.get('label')} {dim.get('score')}/{dim.get('max_score')} ({dim.get('engine')})")
    return MultiCompatPairResponse(
        person_a_idx=person_a_idx,
        person_b_idx=person_b_idx,
        total_score=ziwei_score,
        max_score=max_score,
        level=level,
        combined_score=float(relation.get("combined_score") or 0),
        bazi_score=bazi_block.get("score"),
        ziwei_score=ziwei_block.get("score"),
        grade=relation.get("grade"),
        dimension_highlights=highlights,
    )
