"""Unified provenance / confidence layer for API responses."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

ProvenanceLayerType = Literal["classical", "engine", "heuristic", "modern_convention"]


class ProvenanceLayer(BaseModel):
    """Credibility metadata for a response block or whole payload."""

    layer: ProvenanceLayerType = "engine"
    confidence: float = Field(default=0.75, ge=0.0, le=1.0)
    method_registry_id: str | None = None
    note: str | None = None


class ResponseProvenance(BaseModel):
    """Root-level provenance for bazi_full / ziwei_full."""

    pillars: ProvenanceLayer = Field(
        default_factory=lambda: ProvenanceLayer(layer="engine", confidence=0.9, method_registry_id="B-P0-pillars")
    )
    geju: ProvenanceLayer = Field(
        default_factory=lambda: ProvenanceLayer(layer="engine", confidence=0.85, method_registry_id="B-P3-geju")
    )
    yongshen: ProvenanceLayer = Field(
        default_factory=lambda: ProvenanceLayer(layer="engine", confidence=0.8, method_registry_id="B-P3-yongshen")
    )
    dayun: ProvenanceLayer = Field(
        default_factory=lambda: ProvenanceLayer(layer="engine", confidence=0.85, method_registry_id="B-P2-dayun")
    )
    narrative: ProvenanceLayer = Field(
        default_factory=lambda: ProvenanceLayer(layer="classical", confidence=0.7, method_registry_id="B-P4-narrative")
    )
    analysis: ProvenanceLayer = Field(
        default_factory=lambda: ProvenanceLayer(
            layer="heuristic", confidence=0.5, method_registry_id="B-heuristic-analysis"
        )
    )
    scoring: ProvenanceLayer = Field(
        default_factory=lambda: ProvenanceLayer(
            layer="modern_convention",
            confidence=0.4,
            method_registry_id="B-scoring-modern",
            note="现代六维评分，非典籍断语",
        )
    )
    forecast: ProvenanceLayer = Field(
        default_factory=lambda: ProvenanceLayer(
            layer="heuristic",
            confidence=0.45,
            method_registry_id="Z-forecast-heuristic",
            note="叠宫/关键词参考，非铁口直断",
        )
    )
    compatibility: ProvenanceLayer = Field(
        default_factory=lambda: ProvenanceLayer(
            layer="heuristic",
            confidence=0.4,
            method_registry_id="Z-compat-heuristic",
            note="合盘仅供参考",
        )
    )
    patterns: ProvenanceLayer = Field(
        default_factory=lambda: ProvenanceLayer(layer="engine", confidence=0.75, method_registry_id="Z-P2-patterns")
    )
    stars: ProvenanceLayer = Field(
        default_factory=lambda: ProvenanceLayer(layer="engine", confidence=0.92, method_registry_id="Z-P0-stars")
    )
