"""Case and Snapshot models."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import ClassVar, Optional
from uuid import uuid4

from sqlalchemy import Column, Index, JSON
from sqlmodel import Field, SQLModel


class Case(SQLModel, table=True):
    """案例表 - 存储八字命理案例"""
    __tablename__: ClassVar[str] = "cases"
    __table_args__ = (Index("idx_cases_updated_at", "updated_at"),)

    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    owner_id: Optional[int] = Field(default=None, foreign_key="users.id", index=True)  # 1.18: 案例归属用户
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
    """快照表 - 存储计算结果的快照"""
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
