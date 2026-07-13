"""Relation compatibility explain section builders (BE-R15)."""

from __future__ import annotations

from typing import Any

from app.schemas.explain import ExplainBlockModel, ExplainSectionResultModel
from services.content_policy import sanitize_explain_block
from services.explain_bazi import _clip, _verified_classic_for_query
from services.relation_engine.registry import get_type_config

RELATION_SECTIONS = frozenset({"relation_reading"})

_READING_FACT: dict[str, str] = {
    "couple": "情侣合盘：先读 fact 层维度分（日支、十神、夫妻/财帛宫），cite 典籍默认折叠，余论不构成决策依据。",
    "friend": "友人合盘：先看交友宫与迁移互动，再对照喜忌互补；推断层仅供观览。",
    "parent_child": "亲子合盘：子女宫与父母宫对照为主，代际差异宜规则清晰、耐心沟通。",
    "colleague": "同事合盘：官禄与协作维度优先，宜分工明确、减少内耗。",
    "business_partner": "合伙合盘：财帛与契约维度优先，宜账目清晰、风险共担。",
    "supervisor_subordinate": "上下级合盘：权责与官杀维度优先，宜目标对齐、反馈及时。",
}

_CLASSIC_TAGS: dict[str, list[str]] = {
    "couple": ["marriage", "relationship"],
    "friend": ["relationship"],
    "parent_child": ["relationship", "family"],
    "colleague": ["career", "relationship"],
    "business_partner": ["wealth", "relationship"],
    "supervisor_subordinate": ["career", "relationship"],
}


def _block(text: str, layer: str = "fact", classic_id: str | None = None) -> ExplainBlockModel:
    raw = {"text": _clip(text), "layer": layer, "classic_id": classic_id}
    cleaned = sanitize_explain_block(raw)
    return ExplainBlockModel(**cleaned)


def build_relation_cite_layers(
    *,
    relation_type: str,
    relation_type_label: str | None,
    combined_score: float,
    grade: str | None,
) -> list[dict[str, Any]]:
    """Build layers.cite sections for relation-compat (R086 Trust P0)."""
    type_cfg = get_type_config(relation_type)
    rel_label = relation_type_label or type_cfg.get("label") or relation_type
    blocks: list[dict[str, Any]] = []
    query = f"{rel_label} 合参"
    tags = _CLASSIC_TAGS.get(relation_type, ["relationship"])
    cid, passage = _verified_classic_for_query(query, tags=tags)
    if cid and passage:
        blocks.append(
            {
                "text": _clip(passage),
                "layer": "cite",
                "classic_id": cid,
            }
        )
    if not blocks:
        return []
    heading = f"{rel_label} · 典籍引证"
    if combined_score is not None:
        heading = f"{heading}（综合 {combined_score} · {grade or '—'}）"
    return [
        {
            "id": "relation_reading_cite",
            "heading": heading,
            "blocks": blocks,
        }
    ]


def build_relation_section(result: dict[str, Any], section_id: str) -> ExplainSectionResultModel:
    """Build one explain section from a relation-compat@1.0 payload."""
    blocks: list[ExplainBlockModel] = []
    relation_type = str(result.get("relation_type") or "couple")
    type_cfg = get_type_config(relation_type)
    rel_label = result.get("relation_type_label") or type_cfg.get("label") or relation_type
    combined = result.get("combined_score")
    grade = result.get("grade") or "—"

    if section_id == "relation_reading":
        blocks.append(_block(_READING_FACT.get(relation_type, _READING_FACT["couple"]), "fact"))
        if combined is not None:
            blocks.append(_block(f"当前综合 {combined} 分（{grade}），分维见 fact 层表格。", "fact"))

        query = f"{rel_label} 合参"
        tags = _CLASSIC_TAGS.get(relation_type, ["relationship"])
        cid, passage = _verified_classic_for_query(query, tags=tags)
        if cid and passage:
            blocks.append(_block(passage, "cite", classic_id=cid))

        summary = str(result.get("summary") or "").strip()
        if summary:
            blocks.append(_block(summary, "inference"))

        tensions = result.get("tensions") or []
        for note in tensions[:2]:
            msg = str(note.get("message") or note.get("code") or "").strip()
            if msg:
                blocks.append(_block(msg, "inference"))

    if not blocks:
        blocks.append(_block("本节暂无讲解内容。", "fact"))

    has_verified_cite = any(b.layer == "cite" and b.classic_id for b in blocks)
    return ExplainSectionResultModel(
        section_id=section_id,
        blocks=blocks,
        verified=has_verified_cite,
    )
