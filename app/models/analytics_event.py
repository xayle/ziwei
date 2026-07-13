"""GTM product analytics events (BE-GTM-01 / T089)."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import ClassVar

from sqlalchemy import Column, Index, Text
from sqlmodel import Field, SQLModel


class AnalyticsEvent(SQLModel, table=True):
    """Product analytics事件表 — 卷目阅读 / 术语点击等（禁 PII）。"""

    __tablename__: ClassVar[str] = "analytics_events"
    __table_args__ = (
        Index("idx_analytics_events_type", "event_type"),
        Index("idx_analytics_events_user", "user_id"),
        Index("idx_analytics_events_session", "session_id"),
        Index("idx_analytics_events_created", "created_at"),
    )

    id: int | None = Field(default=None, primary_key=True)
    user_id: int | None = Field(default=None, index=True)
    session_id: str = Field(default="", max_length=100)
    event_type: str = Field(max_length=64)
    case_id: str | None = Field(default=None, max_length=64)
    volume_id: str | None = Field(default=None, max_length=32)
    client_ts: datetime | None = None
    properties_json: str = Field(default="{}", sa_column=Column(Text))
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
