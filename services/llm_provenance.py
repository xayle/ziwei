"""Build provenance evidence refs for LLM drafts (BE-P2-03)."""

from __future__ import annotations

from typing import Any


def build_draft_evidence_refs(
    *,
    use_bazi_path: bool,
    geju_name: str = "",
    yongshen_favor: list[str] | None = None,
    evidence_snippets: list[str] | None = None,
    raw_evidence: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    refs: list[dict[str, Any]] = []
    layer = "classical" if use_bazi_path else "engine"

    if geju_name:
        refs.append(
            {
                "layer": layer,
                "field": "geju_name",
                "value": geju_name,
                "rule_id": "bazi_engine.geju",
                "source": "services/bazi_engine/geju.py",
            }
        )
    if yongshen_favor:
        refs.append(
            {
                "layer": "engine",
                "field": "yongshen_favor",
                "value": yongshen_favor,
                "rule_id": "bazi_engine.yongshen",
                "source": "services/bazi_engine/yongshen.py",
            }
        )

    for item in raw_evidence or []:
        refs.append(
            {
                "layer": "classical",
                "field": "classic_ref",
                "classic_id": item.get("id") or item.get("classic_id"),
                "title": item.get("title"),
                "passage": (item.get("passage") or "")[:200],
                "verification_status": item.get("verification_status", "unverified"),
            }
        )

    if not raw_evidence and evidence_snippets:
        for idx, snippet in enumerate(evidence_snippets[:5]):
            refs.append(
                {
                    "layer": "classical",
                    "field": "evidence_snippet",
                    "index": idx,
                    "value": snippet[:300],
                    "rule_id": "evidence_retriever.fetch_evidence",
                }
            )

    return refs
