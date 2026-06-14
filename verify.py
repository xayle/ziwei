"""Validation and boundary integration (stub)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from typing import Any, Literal, cast
from zoneinfo import ZoneInfo

from backends import BackendUnavailable, CnlunarBackend, get_sxtwl_backend
from boundary import Pillars, RiskFlags, Validation, compute_risk_flags, compute_validation
from constants import MAX_LON, MIN_LON
from services.bazi_engine.solar_time_v2 import compute_solar_correction_minutes


def _ensure_tz(dt_utc8):
    if dt_utc8.tzinfo is None or dt_utc8.utcoffset() is None:
        raise ValueError("dt_utc8 must be timezone-aware (Asia/Shanghai)")
    return dt_utc8.astimezone(ZoneInfo("Asia/Shanghai"))


def _validate_lon(lon: float) -> float:
    if not (MIN_LON <= lon <= MAX_LON):
        raise ValueError(f"Longitude {lon} outside supported range {MIN_LON}..{MAX_LON}")
    return lon


def _pick_backends(mode: Literal["dual", "single"]) -> tuple[str, str | None]:
    if mode not in {"dual", "single"}:
        raise ValueError("mode must be 'dual' or 'single'")
    return ("sxtwl", "cnlunar") if mode == "dual" else ("sxtwl", None)


@dataclass
class VerifyOutput:
    validation: Validation
    pillars_primary: Pillars
    pillars_secondary: Pillars | None
    risk_flags: RiskFlags
    mode_requested: str
    mode_effective: str
    solar_time_offset_minutes: float
    backend_source: str = "sxtwl"  # "sxtwl" | "cnlunar_fallback"


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

    correction_minutes = compute_solar_correction_minutes(dt_local, lon)
    dt_effective = dt_local + timedelta(minutes=correction_minutes) if use_solar else dt_local

    _, secondary_name = _pick_backends(mode)

    primary = None
    secondary = None
    try:
        primary = get_sxtwl_backend()  # B1: 复用单例，避免每请求重建 C 库对象
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

    # B3: sxtwl 合理性断言 — 失败时降级 cnlunar 并记 warning
    _sxtwl_fallback_warnings: list[str] = []
    backend_source = "sxtwl"
    try:
        pillars_primary = primary.get_pillars(dt_effective)
    except (ValueError, IndexError, AssertionError) as _b3_err:
        _sxtwl_fallback_warnings.append("sxtwl_fallback")
        backend_source = "cnlunar_fallback"
        try:
            _fallback = CnlunarBackend()
            pillars_primary = _fallback.get_pillars(dt_effective)
            primary = _fallback  # 后续 jieqi_ctx 也用 fallback（CnlunarBackend 不支持，返回 None）
        except (BackendUnavailable, Exception):
            raise BackendUnavailable(f"sxtwl 断言失败且 cnlunar 降级也失败: {_b3_err}") from _b3_err

    pillars_secondary: Pillars | None = secondary.get_pillars(dt_effective) if secondary else None

    # 日柱一致性校验（晚子时/立春边界最易产生 sxtwl vs cnlunar 不一致）
    # 若两库日柱冲突，整体 fallback 到 cnlunar，不做单柱替换（避免四柱体系混用）
    if pillars_secondary is not None and pillars_primary.day.ganzhi != pillars_secondary.day.ganzhi:
        pillars_primary = pillars_secondary
        backend_source = "cnlunar_fallback"
        _sxtwl_fallback_warnings.append("sxtwl_day_pillar_mismatch")

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
    # B3: 追加降级警告
    if _sxtwl_fallback_warnings:
        validation.warnings.extend(_sxtwl_fallback_warnings)

    return VerifyOutput(
        validation=validation,
        pillars_primary=pillars_primary,
        pillars_secondary=pillars_secondary,
        risk_flags=risk_flags,
        mode_requested=mode,
        mode_effective=mode_effective,
        solar_time_offset_minutes=correction_minutes if use_solar else 0.0,
        backend_source=backend_source,
    )
