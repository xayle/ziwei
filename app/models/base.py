"""Base models - User, RefreshToken, etc."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import ClassVar, Optional

from sqlalchemy import Index
from sqlmodel import Field, Relationship, SQLModel


class User(SQLModel, table=True):
    """用户表 - 支持多用户系统"""
    __tablename__: ClassVar[str] = "users"
    __table_args__ = (
        Index("idx_users_username", "username"),
        Index("idx_users_email_active", "email", "is_active"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(unique=True, index=True)
    email: str = Field(unique=True, index=True)
    password_hash: str
    is_active: bool = Field(default=True)
    role: str = Field(default="editor")
    is_admin: bool = Field(default=False)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    deleted_at: Optional[datetime] = None


class RefreshToken(SQLModel, table=True):
    """刷新令牌表 - 支持token刷新机制"""
    __tablename__: ClassVar[str] = "refresh_tokens"
    __table_args__ = (
        Index("idx_refresh_tokens_user_id", "user_id"),
        Index("idx_refresh_tokens_token", "token"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    token: str = Field(unique=True, index=True)
    expires_at: datetime
    is_revoked: bool = Field(default=False)

    ip_address: Optional[str] = None
    user_agent: Optional[str] = None

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    refreshed_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None

    # ORM Relationship (S3)
    user: User = Relationship()
