"""UTM / Douyin attribution helpers (BE-GTM-02 / T088)."""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator

_MAX_UTM = 128
_MAX_CONTENT_ID = 64


def clean_optional(value: str | None, *, max_len: int) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    if not cleaned:
        return None
    if len(cleaned) > max_len:
        raise ValueError(f"must be at most {max_len} characters")
    return cleaned


class UtmAttributionFields(BaseModel):
    """Optional first-touch attribution (douyin video → register / case)."""

    utm_source: str | None = Field(default=None, description="渠道，如 douyin")
    utm_campaign: str | None = Field(default=None, description="活动/话题，如 geju_hook")
    content_id: str | None = Field(default=None, description="抖音视频 ID 等素材 ID")

    @field_validator("utm_source", "utm_campaign", mode="before")
    @classmethod
    def _utm_fields(cls, v: object) -> str | None:
        if v is None or isinstance(v, str):
            return clean_optional(v if isinstance(v, str) else None, max_len=_MAX_UTM)
        raise ValueError("must be a string or null")

    @field_validator("content_id", mode="before")
    @classmethod
    def _content_id(cls, v: object) -> str | None:
        if v is None or isinstance(v, str):
            return clean_optional(v if isinstance(v, str) else None, max_len=_MAX_CONTENT_ID)
        raise ValueError("must be a string or null")
