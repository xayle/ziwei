"""Event model - stores calculation results and recommendations."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import ClassVar

from sqlalchemy import CheckConstraint, Index
from sqlmodel import Field, Relationship, SQLModel

from .base import User
from .member import Member


class Event(SQLModel, table=True):
    """事件表 - 存储计算结果和推荐"""

    __tablename__: ClassVar[str] = "events"
    __table_args__ = (
        Index("idx_events_owner_member", "owner_id", "member_id"),
        Index("idx_events_owner_created", "owner_id", "created_at"),
        Index("idx_events_member_created", "member_id", "created_at"),
        CheckConstraint('"L_level" >= 0 AND "L_level" <= 3', name="ck_event_l_level"),
        CheckConstraint("confidence_score >= 0.0 AND confidence_score <= 1.0", name="ck_event_confidence_score"),
    )

    id: int | None = Field(default=None, primary_key=True)
    owner_id: int = Field(foreign_key="users.id", index=True)
    member_id: int = Field(foreign_key="members.id", index=True)
    name: str
    event_type: str

    bazi_json: str
    pillars_primary: str | None = None
    ten_gods: str | None = None
    five_elements: str | None = None

    L_level: int = Field(default=0)
    confidence_score: float = Field(default=0.0)

    recommendation: str | None = None
    recommendation_engine: str | None = None

    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    deleted_at: datetime | None = None

    # ORM Relationships (S3)
    owner: User = Relationship()
    member: Member = Relationship()
