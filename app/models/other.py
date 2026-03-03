"""Scenario, Delegation, and AuditLog models."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import ClassVar, Optional

from sqlalchemy import Index
from sqlmodel import Field, Relationship, SQLModel

from .base import User


class Scenario(SQLModel, table=True):
    """场景表 - 支持假设推演"""
    __tablename__: ClassVar[str] = "scenarios"
    __table_args__ = (
        Index("idx_scenarios_owner", "owner_id"),
        Index("idx_scenarios_owner_created", "owner_id", "created_at"),
        Index("idx_scenarios_created", "created_at"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    owner_id: int = Field(foreign_key="users.id", index=True)
    base_member_id: int = Field(foreign_key="members.id")
    name: str
    description: Optional[str] = None
    variations: Optional[str] = None
    scenario_type: str
    results: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    deleted_at: Optional[datetime] = None


class Delegation(SQLModel, table=True):
    """权限委托表 - 用户间的权限授予"""
    __tablename__: ClassVar[str] = "delegations"
    __table_args__ = (
        Index("idx_delegations_from_to", "from_user_id", "to_user_id"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    from_user_id: int = Field(foreign_key="users.id", index=True)
    to_user_id: int = Field(foreign_key="users.id", index=True)
    permission_type: str
    member_scope: Optional[int] = Field(default=None, foreign_key="members.id")
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None


class AuditLog(SQLModel, table=True):
    """审计日志表 - 记录所有重要操作"""
    __tablename__: ClassVar[str] = "audit_logs"
    __table_args__ = (Index("idx_audit_logs_user_time", "user_id", "created_at"),)

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    action: str
    resource_type: str
    resource_id: Optional[str] = None
    details: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    status: str = Field(default="success")
    error_message: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    deleted_at: Optional[datetime] = None

    # ORM Relationship (S3)
    user: User = Relationship()
