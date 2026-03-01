"""Member model - stores BaZi profile information."""
from __future__ import annotations

from datetime import datetime, date, timezone
from typing import ClassVar, Optional

from sqlalchemy import CheckConstraint, Index
from sqlmodel import Field, SQLModel


class Member(SQLModel, table=True):
    """成员表 - 存储八字信息对象"""
    __tablename__: ClassVar[str] = "members"
    __table_args__ = (
        Index("idx_members_owner", "owner_id"),
        Index("idx_members_owner_created", "owner_id", "created_at"),
        Index("idx_members_created", "created_at"),
        CheckConstraint("gender IN ('M', 'F', 'U')", name="ck_member_gender"),
        CheckConstraint("birth_time_hour IS NULL OR (birth_time_hour >= 0 AND birth_time_hour <= 23)", name="ck_member_birth_hour"),
        CheckConstraint("birth_time_minute IS NULL OR (birth_time_minute >= 0 AND birth_time_minute <= 59)", name="ck_member_birth_minute"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    owner_id: int = Field(foreign_key="users.id", index=True)
    name: str
    birth_date: date
    gender: str  # M, F, U
    birth_time_hour: Optional[int] = None
    birth_time_minute: Optional[int] = None
    birth_city: Optional[str] = None
    birth_longitude: Optional[float] = None
    solar_time_enabled: bool = Field(default=False)
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    deleted_at: Optional[datetime] = None
