"""Compute-related schemas."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel

from .case import SnapshotOut


class ComputeRequest(BaseModel):
    """计算请求"""

    compute_bazi: bool = True
    do_verify: bool = True
    mode: Literal["dual", "single"] = "dual"
    solar_time_enabled: bool | None = False
    liunian_years: list[int] | None = None


class ComputeTaskStatus(BaseModel):
    """单个计算任务的状态"""

    status: Literal["success", "failed", "skipped"]
    snapshot_id: str | None
    message: str | None = None


class ComputeResponse(BaseModel):
    """计算响应"""

    compute_batch_id: str
    case_id: str
    input_effective: dict[str, Any]
    tasks: dict[str, ComputeTaskStatus]
    snapshots_created: list[SnapshotOut]
