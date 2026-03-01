from __future__ import annotations

from datetime import datetime, date, timezone
from typing import ClassVar, Optional
from uuid import uuid4

from sqlalchemy import Column, Index, JSON, CheckConstraint
from sqlmodel import Field, SQLModel


class Case(SQLModel, table=True):
    __tablename__: ClassVar[str] = "cases"
    __table_args__ = (Index("idx_cases_updated_at", "updated_at"),)

    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    # owner_id: 持有者 FK，内容隔离基础（指向 users.id）
    # 当前设为 Optional 小平失兼容老数据；M1 任务 1.18 执行 Alembic 迁移后可改为必填
    owner_id: Optional[int] = Field(default=None, foreign_key="users.id", index=True)
    name: str
    gender: Optional[str] = None
    birth_dt_local: str
    tz: str
    birth_dt: Optional[str] = None
    city: Optional[str] = None
    lon: float
    solar_time_enabled: bool = False
    notes: Optional[str] = None
    tags: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_snapshot_at: Optional[datetime] = None
    api_version_last: Optional[str] = None
    rule_version_last: Optional[str] = None
    schema_version: Optional[str] = "case@5.0"
    deleted_at: Optional[datetime] = None


class Snapshot(SQLModel, table=True):
    __tablename__: ClassVar[str] = "snapshots"
    __table_args__ = (Index("idx_snapshots_case_created", "case_id", "created_at"),)

    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    case_id: str = Field(index=True, foreign_key="cases.id")
    kind: str
    compute_flags: Optional[dict] = Field(default=None, sa_column=Column(JSON))
    input_json: Optional[dict] = Field(default=None, sa_column=Column(JSON))
    output_json: Optional[dict] = Field(default=None, sa_column=Column(JSON))
    backend_json: Optional[dict] = Field(default=None, sa_column=Column(JSON))
    api_version: Optional[str] = None
    rule_version: Optional[str] = None
    schema_version: Optional[str] = "snapshot@5.0"
    summary_level: Optional[str] = None
    summary_warning_count: Optional[int] = None
    summary_diff_count: Optional[int] = None
    summary_engine_primary: Optional[str] = None
    note: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    deleted_at: Optional[datetime] = None


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
    gender: str
    birth_time_hour: Optional[int] = None
    birth_time_minute: Optional[int] = None
    birth_city: Optional[str] = None
    birth_longitude: Optional[float] = None
    solar_time_enabled: bool = Field(default=False)
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    deleted_at: Optional[datetime] = None


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

