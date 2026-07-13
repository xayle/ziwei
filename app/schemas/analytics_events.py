"""Schemas for POST /api/v1/analytics/events (BE-GTM-01 / T089)."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

AnalyticsEventType = Literal[
    "volume_view",
    "volume_dwell",
    "volume_unlock_prompt",
    "glossary_click",
    "term_click",
    "funnel_step",
    "share_card_export",
    "landing_cta_click",
]

# T090 对齐：payload 禁止姓名/生日等 PII 键
_PII_KEYS = frozenset(
    {
        "name",
        "username",
        "real_name",
        "full_name",
        "email",
        "phone",
        "mobile",
        "password",
        "birthday",
        "birthdate",
        "birth_dt",
        "birth_dt_local",
        "birth_year",
        "birth_month",
        "birth_day",
        "lon",
        "lat",
        "latitude",
        "longitude",
        "address",
        "id_card",
    }
)


def scrub_properties(raw: dict[str, Any] | None) -> tuple[dict[str, Any], list[str]]:
    """Drop PII keys; return (cleaned, dropped_keys)."""
    if not raw:
        return {}, []
    cleaned: dict[str, Any] = {}
    dropped: list[str] = []
    for key, value in raw.items():
        low = str(key).strip().lower()
        if low in _PII_KEYS or low.startswith("birth_"):
            dropped.append(str(key))
            continue
        if isinstance(value, str | int | float | bool) or value is None:
            if isinstance(value, str) and len(value) > 500:
                cleaned[str(key)] = value[:500]
            else:
                cleaned[str(key)] = value
        # skip nested objects / lists (avoid accidental PII dumps)
    return cleaned, dropped


class AnalyticsEventItem(BaseModel):
    event_type: AnalyticsEventType
    session_id: str | None = Field(default=None, max_length=100)
    case_id: str | None = Field(default=None, max_length=64, description="不透明 case UUID，可有")
    volume_id: str | None = Field(default=None, max_length=32)
    ts: datetime | None = Field(default=None, description="客户端事件时间")
    properties: dict[str, Any] = Field(default_factory=dict)

    @field_validator("session_id", "case_id", "volume_id", mode="before")
    @classmethod
    def _blank_to_none(cls, v: object) -> str | None:
        if v is None:
            return None
        if isinstance(v, str):
            s = v.strip()
            return s or None
        raise ValueError("must be a string or null")


class AnalyticsEventsBatchRequest(BaseModel):
    events: list[AnalyticsEventItem] = Field(..., min_length=1, max_length=50)


class AnalyticsEventsBatchResponse(BaseModel):
    accepted: int
    rejected: int = 0
    scrubbed_pii_keys: list[str] = Field(default_factory=list)
    schema_version: Literal["analytics-events@1.0"] = "analytics-events@1.0"
