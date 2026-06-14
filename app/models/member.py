"""Member model - stores BaZi profile information."""

from __future__ import annotations

from datetime import UTC, date, datetime
from typing import ClassVar

from sqlalchemy import CheckConstraint, Index
from sqlmodel import Field, Relationship, SQLModel

from .base import User


class Member(SQLModel, table=True):
    """成员表 - 存储八字信息对象"""

    __tablename__: ClassVar[str] = "members"
    __table_args__ = (
        Index("idx_members_owner", "owner_id"),
        Index("idx_members_owner_created", "owner_id", "created_at"),
        Index("idx_members_created", "created_at"),
        CheckConstraint("gender IN ('M', 'F', 'U')", name="ck_member_gender"),
        CheckConstraint(
            "birth_time_hour IS NULL OR (birth_time_hour >= 0 AND birth_time_hour <= 23)", name="ck_member_birth_hour"
        ),
        CheckConstraint(
            "birth_time_minute IS NULL OR (birth_time_minute >= 0 AND birth_time_minute <= 59)",
            name="ck_member_birth_minute",
        ),
    )

    id: int | None = Field(default=None, primary_key=True)
    owner_id: int = Field(foreign_key="users.id", index=True)
    name: str
    birth_date: date
    gender: str  # M, F, U
    birth_time_hour: int | None = None
    birth_time_minute: int | None = None
    birth_city: str | None = None
    birth_longitude: float | None = None
    solar_time_enabled: bool = Field(default=False)
    notes: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    deleted_at: datetime | None = None

    # ORM Relationship (S3)
    owner: User = Relationship()
