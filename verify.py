"""Validation and boundary integration (stub)."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from typing import Optional, Literal, Any, cast
from zoneinfo import ZoneInfo

from backends import BackendUnavailable, CnlunarBackend, SxtwlBackend
from boundary import Pillars, RiskFlags, Validation, compute_risk_flags, compute_validation
from constants import MAX_LON, MIN_LON
from solar_time import compute_solar_correction_minutes


def _ensure_tz(dt_utc8):
    if dt_utc8.tzinfo is None or dt_utc8.utcoffset() is None:
        raise ValueError("dt_utc8 must be timezone-aware (Asia/Shanghai)")
    return dt_utc8.astimezone(ZoneInfo("Asia/Shanghai"))


def _validate_lon(lon: float) -> float:
    if not (MIN_LON <= lon <= MAX_LON):
        raise ValueError(f"Longitude {lon} outside supported range {MIN_LON}..{MAX_LON}")
    return lon


def _pick_backends(mode: Literal["dual", "single"]) -> tuple[str, Optional[str]]:
    if mode not in {"dual", "single"}:
        raise ValueError("mode must be 'dual' or 'single'")
    return ("sxtwl", "cnlunar") if mode == "dual" else ("sxtwl", None)


@dataclass
class VerifyOutput:
    validation: Validation
    pillars_primary: Pillars
    pillars_secondary: Optional[Pillars]
    risk_flags: RiskFlags
    mode_requested: str
    mode_effective: str
    solar_time_offset_minutes: float


def verify(dt_utc8, lon: float, use_solar: bool, mode: Literal["dual", "single"] = "dual") -> Validation:
    """Perform verification and return Validation object.

    Pipeline:
    1) Normalize datetime and optional solar correction
    2) Choose backends (dual vs single); gracefully degrade if unavailable
    3) Fetch pillars and optional jieqi context
    4) Delegate to boundary for risk flags and validation
    """

    return verify_full(dt_utc8, lon, use_solar, mode).validation


def verify_full(dt_utc8, lon: float, use_solar: bool, mode: Literal["dual", "single"] = "dual") -> VerifyOutput:
    dt_local = _ensure_tz(dt_utc8)
    _validate_lon(lon)

    _, correction_minutes = compute_solar_correction_minutes(lon)
    dt_effective = dt_local + timedelta(minutes=correction_minutes) if use_solar else dt_local

    _, secondary_name = _pick_backends(mode)

    primary = None
    secondary = None
    try:
        primary = SxtwlBackend()
    except BackendUnavailable:
        primary = None

    if primary is None and mode == "single":
        try:
            primary = CnlunarBackend()
        except BackendUnavailable:
            primary = None

    if secondary_name:
        try:
            secondary = CnlunarBackend()
        except BackendUnavailable:
            secondary = None

    mode_effective: Literal["dual", "single"] = mode
    if mode == "dual" and (primary is None or secondary is None):
        # Fall back to single if any side missing
        mode_effective = "single"
        primary = primary or secondary
        secondary = None

    if primary is None:
        raise BackendUnavailable("No available backend (sxtwl/cnlunar)")

    pillars_primary = primary.get_pillars(dt_effective)
    pillars_secondary: Optional[Pillars] = secondary.get_pillars(dt_effective) if secondary else None

    jieqi_ctx = None
    if hasattr(primary, "get_jieqi_context"):
        jieqi_ctx = cast(Any, primary).get_jieqi_context(dt_effective)

    risk_flags: RiskFlags = compute_risk_flags(
        dt_effective,
        lon=lon,
        solar_time_enabled=use_solar,
        jieqi_ctx=jieqi_ctx,
    )

    validation = compute_validation(
        pillars_primary=pillars_primary,
        pillars_secondary=pillars_secondary,
        risk_flags=risk_flags,
        mode=mode_effective,
    )

    return VerifyOutput(
        validation=validation,
        pillars_primary=pillars_primary,
        pillars_secondary=pillars_secondary,
        risk_flags=risk_flags,
        mode_requested=mode,
        mode_effective=mode_effective,
        solar_time_offset_minutes=correction_minutes if use_solar else 0.0,
    )
