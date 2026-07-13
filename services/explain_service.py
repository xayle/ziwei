"""Explain batch orchestration."""

from __future__ import annotations

from typing import Any

from fastapi import HTTPException

from app.schemas.explain import (
    DisclaimerBlockModel,
    ExplainBatchRequest,
    ExplainBatchResponse,
    ExplainSectionResultModel,
    RelationExplainBatchRequest,
    ZiweiExplainBatchRequest,
)
from services.chart_snapshot_service import build_bazi_snapshot, build_ziwei_snapshot
from services.content_policy import content_versions_meta, default_disclaimer_block, default_wenmo_advisory
from services.explain_bazi import BAZI_SECTIONS, build_bazi_section
from services.explain_relation import RELATION_SECTIONS, build_relation_section
from services.explain_ziwei import ZIWEI_SECTIONS, build_ziwei_section
from services.relation_engine.case_resolver import resolve_person_input
from services.relation_engine.composer import compute_relation_full

MAX_SECTIONS = 4


def _validate_sections(section_ids: list[str], allowed: frozenset[str]) -> list[str]:
    if len(section_ids) > MAX_SECTIONS:
        raise HTTPException(status_code=422, detail=f"sections max {MAX_SECTIONS}")
    unknown = [s for s in section_ids if s not in allowed]
    if unknown:
        raise HTTPException(status_code=422, detail=f"unknown sections: {', '.join(unknown)}")
    return section_ids


def explain_bazi_batch(request: ExplainBatchRequest, *, request_id: str | None = None) -> ExplainBatchResponse:
    sections = _validate_sections(request.sections, BAZI_SECTIONS)
    snapshot = build_bazi_snapshot(request, request_id=request_id)
    results: list[ExplainSectionResultModel] = [build_bazi_section(snapshot, section_id) for section_id in sections]
    return ExplainBatchResponse(
        chart_hash=snapshot.chart_hash,
        disclaimer_block=DisclaimerBlockModel(**default_disclaimer_block()),
        content_versions=content_versions_meta(),
        wenmo_advisory=None,
        sections=results,
    )


def explain_ziwei_batch(request: ZiweiExplainBatchRequest) -> ExplainBatchResponse:
    sections = _validate_sections(request.sections, ZIWEI_SECTIONS)
    snapshot = build_ziwei_snapshot(request)
    results: list[ExplainSectionResultModel] = [build_ziwei_section(snapshot, section_id) for section_id in sections]
    return ExplainBatchResponse(
        chart_hash=snapshot.chart_hash,
        disclaimer_block=DisclaimerBlockModel(**default_disclaimer_block()),
        content_versions=content_versions_meta(),
        wenmo_advisory=default_wenmo_advisory(),
        sections=results,
    )


def explain_relation_batch(
    request: RelationExplainBatchRequest,
    *,
    user: Any | None = None,
    session: Any | None = None,
) -> ExplainBatchResponse:
    """Explain batch for relation-compat — sections e.g. relation_reading (cite layer)."""
    sections = _validate_sections(request.sections, RELATION_SECTIONS)
    person_a = resolve_person_input(
        request.person_a.model_dump(),
        user=user,
        session=session,
        default_label="甲方",
    )
    person_b = resolve_person_input(
        request.person_b.model_dump(),
        user=user,
        session=session,
        default_label="乙方",
    )
    result = compute_relation_full(
        relation_type=request.relation_type,
        person_a=person_a,
        person_b=person_b,
        options=request.options.model_dump(),
        supervisor_id=request.supervisor_id,
    )
    results = [build_relation_section(result, section_id) for section_id in sections]
    meta = result.get("meta") or {}
    ha = meta.get("chart_hash_a") or "na"
    hb = meta.get("chart_hash_b") or "nb"
    chart_hash = f"relation:{request.relation_type}:{ha[:16]}:{hb[:16]}"
    return ExplainBatchResponse(
        chart_hash=chart_hash,
        disclaimer_block=DisclaimerBlockModel(**default_disclaimer_block()),
        content_versions=content_versions_meta(),
        wenmo_advisory=None,
        sections=results,
    )
