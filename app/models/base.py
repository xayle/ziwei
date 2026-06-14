"""Base models - User, RefreshToken, etc."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import ClassVar

from sqlalchemy import Index
from sqlmodel import Field, Relationship, SQLModel


class User(SQLModel, table=True):
    """用户表 - 支持多用户系统"""

    __tablename__: ClassVar[str] = "users"
    __table_args__ = (
        Index("idx_users_username", "username"),
        Index("idx_users_email_active", "email", "is_active"),
    )

    id: int | None = Field(default=None, primary_key=True)
    username: str = Field(unique=True, index=True)
    email: str = Field(unique=True, index=True)
    password_hash: str
    is_active: bool = Field(default=True)
    role: str = Field(default="editor")
    is_admin: bool = Field(default=False)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    deleted_at: datetime | None = None


class RefreshToken(SQLModel, table=True):
    """刷新令牌表 - 支持token刷新机制"""

    __tablename__: ClassVar[str] = "refresh_tokens"
    __table_args__ = (
        Index("idx_refresh_tokens_user_id", "user_id"),
        Index("idx_refresh_tokens_token", "token"),
    )

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    token: str = Field(unique=True, index=True)
    expires_at: datetime
    is_revoked: bool = Field(default=False)

    ip_address: str | None = None
    user_agent: str | None = None

    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    refreshed_at: datetime | None = None
    deleted_at: datetime | None = None

    # ORM Relationship (S3)
    user: User = Relationship()


class RevokedJti(SQLModel, table=True):
    """Access Token JTI 黑名单 — 持久化确保重启后撤销不丢失"""

    __tablename__: ClassVar[str] = "revoked_jtis"
    __table_args__ = (
        Index("idx_revoked_jtis_jti", "jti"),
        Index("idx_revoked_jtis_expires_at", "expires_at"),
    )

    id: int | None = Field(default=None, primary_key=True)
    jti: str = Field(unique=True, index=True)
    expires_at: datetime  # 用于定期清理过期记录
    revoked_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
