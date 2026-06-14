"""Scenario, Delegation, and AuditLog models."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import ClassVar

from sqlalchemy import Column, Index, Text
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

    id: int | None = Field(default=None, primary_key=True)
    owner_id: int = Field(foreign_key="users.id", index=True)
    base_member_id: int = Field(foreign_key="members.id")
    name: str
    description: str | None = None
    variations: str | None = None
    scenario_type: str
    results: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    deleted_at: datetime | None = None


class Delegation(SQLModel, table=True):
    """权限委托表 - 用户间的权限授予"""

    __tablename__: ClassVar[str] = "delegations"
    __table_args__ = (Index("idx_delegations_from_to", "from_user_id", "to_user_id"),)

    id: int | None = Field(default=None, primary_key=True)
    from_user_id: int = Field(foreign_key="users.id", index=True)
    to_user_id: int = Field(foreign_key="users.id", index=True)
    permission_type: str
    member_scope: int | None = Field(default=None, foreign_key="members.id")
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    expires_at: datetime | None = None
    deleted_at: datetime | None = None
    # ── N3.00 工作流状态字段 ─────────────────────────────────────────────────
    # status 取值：pending / approved / rejected / revoked
    # ⚠️ 默认 pending：所有新建委托须经工作流审批；直接授权端点需显式传 status="approved"
    status: str = Field(default="pending", max_length=20)
    requested_by: int | None = Field(default=None, foreign_key="users.id")
    approved_by: int | None = Field(default=None, foreign_key="users.id")
    approved_at: datetime | None = None
    reject_reason: str | None = Field(default=None, sa_column=Column(Text))


class AuditLog(SQLModel, table=True):
    """审计日志表 - 记录所有重要操作"""

    __tablename__: ClassVar[str] = "audit_logs"
    __table_args__ = (Index("idx_audit_logs_user_time", "user_id", "created_at"),)

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    action: str
    resource_type: str
    resource_id: str | None = None
    details: str | None = None
    ip_address: str | None = None
    user_agent: str | None = None
    status: str = Field(default="success")
    error_message: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    deleted_at: datetime | None = None

    # ORM Relationship (S3)
    user: User = Relationship()
