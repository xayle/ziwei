"""Explain batch orchestration."""

from __future__ import annotations

from fastapi import HTTPException

from app.schemas.explain import (
    DisclaimerBlockModel,
    ExplainBatchRequest,
    ExplainBatchResponse,
    ExplainSectionResultModel,
    ZiweiExplainBatchRequest,
)
from services.chart_snapshot_service import build_bazi_snapshot, build_ziwei_snapshot
from services.content_policy import content_versions_meta, default_disclaimer_block, default_wenmo_advisory
from services.explain_bazi import BAZI_SECTIONS, build_bazi_section
from services.explain_ziwei import ZIWEI_SECTIONS, build_ziwei_section

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
