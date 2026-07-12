"""Async background task models (DB-backed, survives process restart)."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import ClassVar

from sqlalchemy import Column, Text
from sqlmodel import Field, SQLModel


class LiunianReportTask(SQLModel, table=True):
    """流年年度报告异步任务（替代进程内 _liunian_tasks dict）。"""

    __tablename__: ClassVar[str] = "liunian_report_tasks"
    __table_args__ = ()

    id: str = Field(primary_key=True, max_length=36, description="UUID task_id")
    case_id: str = Field(index=True, max_length=36)
    user_id: int = Field(index=True, foreign_key="users.id")
    year: int
    include_months: bool = Field(default=False)
    status: str = Field(default="queued", max_length=20)  # queued|running|done|failed
    submitted_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    finished_at: datetime | None = None
    result_json: str | None = Field(default=None, sa_column=Column(Text))
    error: str | None = Field(default=None, sa_column=Column(Text))
