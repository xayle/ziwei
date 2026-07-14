"""Creator stats schemas (BE-GTM-08 / T099)."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class CreatorStatsTotals(BaseModel):
    users: int = 0
    attributed_users: int = 0
    paid_users: int = 0
    landing_cta_clicks: int = 0
    share_card_exports: int = 0
    volume_views: int = 0


class CreatorTopicCohort(BaseModel):
    """topic（content_id / campaign）→ 注册 → 付费转化。"""

    topic_key: str = Field(..., description="utm_source|utm_campaign|content_id")
    utm_source: str | None = None
    utm_campaign: str | None = None
    content_id: str | None = None
    registrations: int = 0
    paid_conversions: int = 0
    conversion_rate: float = Field(0.0, ge=0.0, le=1.0)


class CreatorFunnelStep(BaseModel):
    step: str
    count: int = 0


class CreatorStatsResponse(BaseModel):
    schema_version: Literal["creator-stats@0.1"] = "creator-stats@0.1"
    generated_at: datetime
    window_days: int
    totals: CreatorStatsTotals
    topics: list[CreatorTopicCohort] = Field(default_factory=list)
    funnel: list[CreatorFunnelStep] = Field(default_factory=list)
