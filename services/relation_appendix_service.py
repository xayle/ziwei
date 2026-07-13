"""Build relation appendix volume for life/volumes extension (T113 · BE only)."""

from __future__ import annotations

from typing import Any

from sqlmodel import Session

from app.models import User
from app.schemas.disclaimer import DisclaimerBlockModel
from app.schemas.life_volume import AnalysisBlockModel, RelationAppendixResponse, VolumeSectionModel
from app.schemas.relation_compat import RelationTypeEnum
from services.content_policy import default_disclaimer_block
from services.relation_engine.case_resolver import case_to_person_dict, load_case_for_user
from services.relation_engine.composer import compute_relation_full

_LAYER_LABEL = {"fact": "格物", "cite": "引经", "inference": "余论"}


def _block(text: str, layer: str = "fact") -> AnalysisBlockModel:
    return AnalysisBlockModel(text=text.strip() or "—", layer=layer)


def build_relation_appendix_from_result(
    *,
    case_id: str,
    partner_case_id: str,
    relation_type: RelationTypeEnum,
    result: dict[str, Any],
) -> RelationAppendixResponse:
    """Format relation-compat@1.0 payload as appendix volume (outside six-volume IA)."""
    pa = result.get("person_a") or {}
    pb = result.get("person_b") or {}
    fact_blocks = [
        _block(
            f"{pa.get('label', '甲方')} × {pb.get('label', '乙方')} · "
            f"综合 {result.get('combined_score')} 分（{result.get('grade') or '—'}）",
            "fact",
        ),
        _block(str(result.get("summary") or ""), "fact"),
    ]
    bazi = result.get("bazi") or {}
    ziwei = result.get("ziwei") or {}
    if bazi.get("score") is not None and ziwei.get("score") is not None:
        fact_blocks.append(
            _block(
                f"双引擎：八字 {bazi.get('score')} · 紫微 {ziwei.get('score')}",
                "fact",
            )
        )
    for dim in (result.get("dimensions") or [])[:6]:
        layer = dim.get("layer") or "fact"
        fact_blocks.append(
            _block(
                f"{dim.get('label')} {dim.get('score')}/{dim.get('max_score')} "
                f"· {_LAYER_LABEL.get(layer, layer)} · {dim.get('description', '')}",
                layer if layer in ("fact", "cite", "inference") else "fact",
            )
        )

    inference_blocks: list[AnalysisBlockModel] = []
    for item in result.get("action_items") or []:
        inference_blocks.append(_block(str(item.get("text") or ""), "inference"))
    for card in result.get("summary_cards") or []:
        if card.get("tone") == "conflict":
            inference_blocks.append(_block(str(card.get("text") or ""), "inference"))

    sections = [
        VolumeSectionModel(
            id="relation_summary",
            heading="合盘摘要",
            layer="fact",
            blocks=fact_blocks,
            collapsed_default=False,
        ),
    ]
    if inference_blocks:
        sections.append(
            VolumeSectionModel(
                id="relation_advice",
                heading="相处建议（余论）",
                layer="inference",
                blocks=inference_blocks[:8],
                collapsed_default=True,
            )
        )

    disclaimer_raw = result.get("disclaimer_block") or default_disclaimer_block()
    return RelationAppendixResponse(
        case_id=case_id,
        partner_case_id=partner_case_id,
        relation_type=relation_type,
        relation_type_label=result.get("relation_type_label"),
        combined_score=float(result.get("combined_score") or 0),
        grade=result.get("grade"),
        person_a_label=pa.get("label"),
        person_b_label=pb.get("label"),
        sections=sections,
        disclaimer_block=DisclaimerBlockModel(**disclaimer_raw),
    )


def build_relation_appendix_for_cases(
    session: Session,
    user: User,
    *,
    case_id: str,
    partner_case_id: str,
    relation_type: RelationTypeEnum = "couple",
    supervisor_id: str | None = None,
) -> RelationAppendixResponse:
    case_a = load_case_for_user(session, case_id, user)
    case_b = load_case_for_user(session, partner_case_id, user)
    person_a = case_to_person_dict(case_a, label=case_a.name or "甲方")
    person_b = case_to_person_dict(case_b, label=case_b.name or "乙方")
    result = compute_relation_full(
        relation_type=relation_type,
        person_a=person_a,
        person_b=person_b,
        options={"include_bazi": True, "include_ziwei": True},
        supervisor_id=supervisor_id,
    )
    return build_relation_appendix_from_result(
        case_id=case_id,
        partner_case_id=partner_case_id,
        relation_type=relation_type,
        result=result,
    )
