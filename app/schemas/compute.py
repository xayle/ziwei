"""Compute-related schemas."""
from __future__ import annotations

from typing import Any, Dict, Literal, Optional

from pydantic import BaseModel

from .case import SnapshotOut


class ComputeRequest(BaseModel):
    """计算请求"""
    compute_bazi: bool = True
    do_verify: bool = True
    mode: Literal["dual", "single"] = "dual"
    solar_time_enabled: Optional[bool] = False
    liunian_years: Optional[list[int]] = None


class ComputeTaskStatus(BaseModel):
    """单个计算任务的状态"""
    status: Literal["success", "failed", "skipped"]
    snapshot_id: Optional[str]
    message: Optional[str] = None


class ComputeResponse(BaseModel):
    """计算响应"""
    compute_batch_id: str
    case_id: str
    input_effective: Dict[str, Any]
    tasks: Dict[str, ComputeTaskStatus]
    snapshots_created: list[SnapshotOut]
