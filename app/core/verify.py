"""Validation and boundary integration — 兼容 shim，实现见 services.bazi_engine.pillars。"""

from __future__ import annotations

from typing import Literal

from services.bazi_engine.pillars import VerifyOutput, compute_pillars


def verify(dt_utc8, lon: float, use_solar: bool, mode: Literal["dual", "single"] = "dual"):
    """Perform verification and return Validation object."""
    return verify_full(dt_utc8, lon, use_solar, mode).validation


def verify_full(dt_utc8, lon: float, use_solar: bool, mode: Literal["dual", "single"] = "dual") -> VerifyOutput:
    """Legacy entry — delegates to bazi_engine.pillars.compute_pillars."""
    return compute_pillars(dt_utc8, lon, use_solar, mode)
