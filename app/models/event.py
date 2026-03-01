"""Event model - stores calculation results and recommendations."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import ClassVar, Optional

from sqlalchemy import CheckConstraint, Index
from sqlmodel import Field, SQLModel


class Event(SQLModel, table=True):
    """事件表 - 存储计算结果和推荐"""
    __tablename__: ClassVar[str] = "events"
    __table_args__ = (
        Index("idx_events_owner_member", "owner_id", "member_id"),
        Index("idx_events_owner_created", "owner_id", "created_at"),
        Index("idx_events_member_created", "member_id", "created_at"),
        CheckConstraint("L_level >= 0 AND L_level <= 3", name="ck_event_l_level"),
        CheckConstraint("confidence_score >= 0.0 AND confidence_score <= 1.0", name="ck_event_confidence_score"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    owner_id: int = Field(foreign_key="users.id", index=True)
    member_id: int = Field(foreign_key="members.id", index=True)
    name: str
    event_type: str

    bazi_json: str
    pillars_primary: Optional[str] = None
    ten_gods: Optional[str] = None
    five_elements: Optional[str] = None

    L_level: int = Field(default=0)
    confidence_score: float = Field(default=0.0)

    recommendation: Optional[str] = None
    recommendation_engine: Optional[str] = None

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    deleted_at: Optional[datetime] = None
