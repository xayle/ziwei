"""Explain API schemas (batch + disclaimer)."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from app.schemas import BaziFullRequest
from app.schemas.disclaimer import DisclaimerBlockModel
from app.schemas.ziwei import ZiweiRequest

ContentLayer = Literal["fact", "cite", "inference"]


class ExplainBlockModel(BaseModel):
    text: str
    layer: ContentLayer = "fact"
    classic_id: str | None = None
    evidence_ids: list[str] = Field(default_factory=list)


class ExplainSectionResultModel(BaseModel):
    section_id: str
    blocks: list[ExplainBlockModel] = Field(default_factory=list)
    verified: bool = False


class ExplainBatchRequest(BaziFullRequest):
    sections: list[str] = Field(..., min_length=1, max_length=4)


class ZiweiExplainBatchRequest(ZiweiRequest):
    sections: list[str] = Field(..., min_length=1, max_length=4)


class ExplainBatchResponse(BaseModel):
    chart_hash: str
    disclaimer_block: DisclaimerBlockModel
    content_versions: dict[str, str] = Field(default_factory=dict)
    wenmo_advisory: str | None = Field(
        None,
        description="文墨对照轨说明（advisory only，供 colophon 展示）",
    )
    sections: list[ExplainSectionResultModel] = Field(default_factory=list)
