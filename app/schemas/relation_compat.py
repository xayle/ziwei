"""Relation compatibility API schemas (relation-compat@1.0)."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator

from app.schemas.disclaimer import DisclaimerBlockModel

RelationTypeEnum = Literal[
    "couple",
    "friend",
    "parent_child",
    "colleague",
    "business_partner",
    "supervisor_subordinate",
]


class RelationPersonInput(BaseModel):
    case_id: str | None = Field(None, description="Optional case UUID; requires auth")
    birth_datetime: str | None = Field(None, description="Local birth time ISO 8601")
    tz: str = Field("Asia/Shanghai")
    longitude: float = Field(116.41, ge=-180, le=180)
    latitude: float | None = Field(None, ge=-90, le=90)
    gender: str = Field("male", description="male/female/男/女")
    label: str | None = Field(None, description="Display name")

    @model_validator(mode="after")
    def require_birth_or_case(self):
        if not self.case_id and not self.birth_datetime:
            raise ValueError("birth_datetime or case_id required")
        return self


class RelationFullOptions(BaseModel):
    include_bazi: bool = True
    include_ziwei: bool = True
    timeline_years: list[int] = Field(default_factory=lambda: [-1, 2])
    liunian_year: int | None = None


class RelationFullRequest(BaseModel):
    relation_type: RelationTypeEnum = "couple"
    supervisor_id: Literal["a", "b"] | None = None
    person_a: RelationPersonInput
    person_b: RelationPersonInput
    options: RelationFullOptions = Field(default_factory=RelationFullOptions)


class SummaryCardModel(BaseModel):
    id: str
    tone: Literal["support", "conflict", "neutral", "action"]
    text: str


class DimensionScoreModel(BaseModel):
    id: str
    label: str
    score: float
    max_score: float
    weight: float = 0.1
    description: str
    layer: Literal["fact", "cite", "inference"] = "fact"
    engine: Literal["bazi", "ziwei", "fusion"] | None = None


class PalaceCrossModel(BaseModel):
    pair_id: str
    a_palace: str
    b_palace: str
    relation_tag: str
    summary: str
    layer: Literal["fact", "inference"] = "fact"


class TimelineNodeModel(BaseModel):
    year: int
    label: str
    summary: str
    risk_level: Literal["低", "中", "高"] | None = None
    month: int | None = None


class ActionItemModel(BaseModel):
    id: str
    text: str
    priority: Literal["P0", "P1", "P2"] | None = None


class TensionNoteModel(BaseModel):
    code: str
    message: str


class PersonRefModel(BaseModel):
    case_id: str | None = None
    label: str
    gender: str
    birth_solar: str
    pillars_primary: dict[str, Any]
    life_palace_gz: str | None = None
    wuxing_ju_name: str | None = None


class LayerBlockModel(BaseModel):
    collapsed_default: bool = False
    sections: list[dict[str, Any]] = Field(default_factory=list)


class RelationFullResponse(BaseModel):
    schema_version: Literal["relation-compat@1.0"] = "relation-compat@1.0"
    request_id: str | None = None
    relation_type: RelationTypeEnum
    relation_type_label: str | None = None
    person_a: PersonRefModel
    person_b: PersonRefModel
    combined_score: float
    grade: Literal["上上", "上", "中", "下", "下下", "N/A"] | None = None
    summary: str
    summary_cards: list[SummaryCardModel] = Field(default_factory=list)
    disclaimer_block: DisclaimerBlockModel
    layers: dict[str, LayerBlockModel]
    dimensions: list[DimensionScoreModel]
    bazi: dict[str, Any] | None = None
    ziwei: dict[str, Any] | None = None
    palace_cross: list[PalaceCrossModel] = Field(default_factory=list)
    timeline: list[TimelineNodeModel]
    action_items: list[ActionItemModel] = Field(default_factory=list)
    tensions: list[TensionNoteModel] = Field(default_factory=list)
    missing_fields: list[str] = Field(default_factory=list)
    meta: dict[str, Any] | None = None


class RelationSnapshotSummary(BaseModel):
    """BE-R16: relation_v1 snapshot list item."""

    id: str
    case_id: str
    partner_case_id: str
    relation_type: RelationTypeEnum
    combined_score: float | None = None
    grade: Literal["上上", "上", "中", "下", "下下", "N/A"] | None = None
    person_a_label: str | None = None
    person_b_label: str | None = None
    created_at: datetime


class RelationSnapshotDetail(BaseModel):
    """BE-R16: full relation-compat payload restored from snapshot."""

    snapshot_id: str
    case_id: str
    partner_case_id: str
    relation_type: RelationTypeEnum
    output: RelationFullResponse


class ProfileSummaryResponse(BaseModel):
    schema_version: Literal["profile-summary@1.0"] = "profile-summary@1.0"
    case_id: str | None = None
    pillars_primary: dict[str, Any]
    geju_one_liner: str | None = None
    yongshen_favor: list[str] = Field(default_factory=list)
    strength_tier: str | None = None
    ziwei_ming_one_liner: str | None = None
    current_dayun: str | None = None
    liunian_2026_tag: str | None = None
    disclaimer_block: DisclaimerBlockModel
