"""Relation compatibility schemas."""
from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import BaseModel, Field

RelationType = Literal[
    "couple",
    "parent_child",
    "colleague",
    "friend",
    "supervisor_subordinate",
]


class RelationPoint(BaseModel):
    tag: str
    detail: str
    weight: float = Field(0.0, ge=-100.0, le=100.0)


class RelationProfile(BaseModel):
    case_id: str
    name: Optional[str] = None
    dominant_element: Optional[str] = None
    yongshen_favor: list[str] = Field(default_factory=list)
    yongshen_avoid: list[str] = Field(default_factory=list)
    wuxing_score: dict[str, float] = Field(default_factory=dict)


class RelationResult(BaseModel):
    relation_type: RelationType
    compatibility_score: float = Field(..., ge=0.0, le=100.0)
    summary: str
    support_points: list[RelationPoint] = Field(default_factory=list)
    conflict_points: list[RelationPoint] = Field(default_factory=list)
    advice: Optional[str] = None
    meta: dict[str, Any] = Field(default_factory=dict)


class RelationComputeRequest(BaseModel):
    case_a_id: str
    case_b_id: str
    relation_type: RelationType = Field(
        "couple",
        description="Relationship template to apply for compatibility",
    )


class RelationComputeResponse(BaseModel):
    case_a: RelationProfile
    case_b: RelationProfile
    result: RelationResult
    snapshots_created: list[str] = Field(default_factory=list)
