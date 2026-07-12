"""Life-volume@1.0 response schema (P3 draft · R096)."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.disclaimer import DisclaimerBlockModel

ContentLayer = Literal["fact", "cite", "inference"]
LifeVolumeId = Literal["preface", "vol1", "vol2", "vol3", "vol4", "vol5", "vol6", "colophon"]

LIFE_VOLUME_LABELS: dict[str, str] = {
    "preface": "卷首",
    "vol1": "卷一·命之根",
    "vol2": "卷二·业之象",
    "vol3": "卷三·运之波",
    "vol4": "卷四·宫之图",
    "vol5": "卷五·事之理",
    "vol6": "卷六·问书",
    "colophon": "跋·校勘",
}


class AnalysisBlockModel(BaseModel):
    text: str
    layer: ContentLayer = "fact"
    classic_id: str | None = None
    evidence_ids: list[str] = Field(default_factory=list)


class VolumeSectionModel(BaseModel):
    id: str
    heading: str
    layer: ContentLayer
    collapsed_default: bool = False
    blocks: list[AnalysisBlockModel] = Field(default_factory=list)


class LifeVolumeModel(BaseModel):
    id: LifeVolumeId
    title: str
    locked: bool = False
    sections: list[VolumeSectionModel] = Field(default_factory=list)


class ColophonModel(BaseModel):
    summary_lines: list[str] = Field(default_factory=list, max_length=3)
    missing_fields: list[str] | None = None
    iztro_advisory: str | None = None
    wenmo_advisory: str | None = None
    dual_track_note: str | None = None
    expandable: bool = True


class LifeVolumeResponseModel(BaseModel):
    schema_version: Literal["life-volume@1.0"] = "life-volume@1.0"
    case_id: str
    chart_hash: str
    rule_version: str | None = None
    content_versions: dict[str, str] = Field(default_factory=dict)
    disclaimer_block: DisclaimerBlockModel
    trust_level: Literal["full", "degraded"] | None = None
    volumes: list[LifeVolumeModel]
    colophon: ColophonModel
