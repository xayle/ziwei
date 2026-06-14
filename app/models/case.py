"""Case and Snapshot models."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import ClassVar
from uuid import uuid4

from sqlalchemy import JSON, Column, Index
from sqlmodel import Field, Relationship, SQLModel


class Case(SQLModel, table=True):
    """案例表 - 存储八字命理案例"""

    __tablename__: ClassVar[str] = "cases"
    __table_args__ = (Index("idx_cases_updated_at", "updated_at"),)

    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    owner_id: int | None = Field(default=None, foreign_key="users.id", index=True)  # 1.18: 案例归属用户
    name: str
    gender: str | None = None
    birth_dt_local: str
    tz: str
    birth_dt: str | None = None
    city: str | None = None
    lon: float
    solar_time_enabled: bool = False
    notes: str | None = None
    tags: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    last_snapshot_at: datetime | None = None
    api_version_last: str | None = None
    rule_version_last: str | None = None
    schema_version: str | None = "case@5.0"
    deleted_at: datetime | None = None
    # B6: 隐私分享 token
    share_token: str | None = Field(default=None, index=True)  # UUID 一次性分享凭证
    share_expires_at: datetime | None = None  # 过期时间，None=未开启


class Snapshot(SQLModel, table=True):
    """快照表 - 存储计算结果的快照"""

    __tablename__: ClassVar[str] = "snapshots"
    __table_args__ = (Index("idx_snapshots_case_created", "case_id", "created_at"),)

    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    case_id: str = Field(index=True, foreign_key="cases.id")
    kind: str
    compute_flags: dict | None = Field(default=None, sa_column=Column(JSON))
    input_json: dict | None = Field(default=None, sa_column=Column(JSON))
    output_json: dict | None = Field(default=None, sa_column=Column(JSON))
    backend_json: dict | None = Field(default=None, sa_column=Column(JSON))
    api_version: str | None = None
    rule_version: str | None = None
    schema_version: str | None = "snapshot@5.0"
    summary_level: str | None = None
    summary_warning_count: int | None = None
    summary_diff_count: int | None = None
    summary_engine_primary: str | None = None
    note: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    deleted_at: datetime | None = None

    # ORM Relationship (S3)
    case: Case = Relationship()
