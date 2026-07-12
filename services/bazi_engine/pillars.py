"""
services/bazi_engine/pillars.py — ENGINE_V2 四柱层（权威入口）

四柱仍使用 sxtwl / cnlunar 后端（精度优先），真太阳时走 solar_time_v2（含 EoT）。
v1 路径经 app.core.verify 兼容 shim；v2 路径直接调用本模块 compute_pillars()。
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Literal, cast
from zoneinfo import ZoneInfo

from backends import BackendUnavailable, CnlunarBackend, get_sxtwl_backend
from boundary import Pillars, RiskFlags, Validation, compute_risk_flags, compute_validation
from constants import MAX_LON, MIN_LON
from services.bazi_engine.solar_time_v2 import compute_solar_correction_minutes
from services.normalize_input import normalize_birth_datetime

PILLARS_LAYER = "bazi_engine.pillars.v2"

ZiDayRule = Literal["sxtwl", "early_zi_prev_day", "early_zi_same_day"]


@dataclass
class VerifyOutput:
    validation: Validation
    pillars_primary: Pillars
    pillars_secondary: Pillars | None
    risk_flags: RiskFlags
    mode_requested: str
    mode_effective: str
    solar_time_offset_minutes: float
    backend_source: str = "sxtwl"
    pillars_layer: str = PILLARS_LAYER
    zi_day_rule: ZiDayRule = "sxtwl"


def _ensure_tz(dt_utc8: datetime) -> datetime:
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


def _pin_same_calendar_day_pillars(primary: Pillars, anchor: Pillars) -> Pillars:
    """Keep hour pillar from primary; pin year/month/day to anchor (calendar same-day)."""
    return Pillars(
        year=anchor.year,
        month=anchor.month,
        day=anchor.day,
        hour=primary.hour,
    )


def _apply_early_zi_same_day(
    primary_backend,
    dt_effective: datetime,
    pillars_primary: Pillars,
) -> Pillars:
    """
    早子时算当天日柱（不换日）：23:00–00:59 年/月/日柱锚定公历当日中午，时柱仍按实际时刻。
    """
    anchor = dt_effective.replace(hour=12, minute=0, second=0, microsecond=0)
    anchor_pillars = primary_backend.get_pillars(anchor)
    return _pin_same_calendar_day_pillars(pillars_primary, anchor_pillars)


def compute_pillars(
    dt_utc8: datetime,
    lon: float,
    use_solar: bool,
    mode: Literal["dual", "single"] = "dual",
    zi_day_rule: ZiDayRule = "sxtwl",
    standard_meridian: float = 120.0,
) -> VerifyOutput:
    """
    ENGINE_V2 四柱层：归一化输入 → 真太阳时 → 双后端取柱 → 边界校验。

    与 app.core.verify.verify_full 逻辑等价，但归属 bazi_engine 包并标记 pillars_layer。
    """
    dt_local = _ensure_tz(dt_utc8)
    _validate_lon(lon)
    normalized_birth = normalize_birth_datetime(
        dt_local,
        "Asia/Shanghai",
        auto_dst=True,
    )

    correction_minutes = compute_solar_correction_minutes(dt_local, lon, standard_meridian=standard_meridian)
    dt_effective = (
        normalized_birth.local_dt + timedelta(minutes=correction_minutes) if use_solar else normalized_birth.local_dt
    )
    # 早子时换日口径（可选，默认 sxtwl 后端行为）
    if zi_day_rule == "early_zi_prev_day" and dt_effective.hour == 23:
        dt_effective = dt_effective - timedelta(days=1)

    _, secondary_name = _pick_backends(mode)

    primary = None
    secondary = None
    try:
        primary = get_sxtwl_backend()
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
        mode_effective = "single"
        primary = primary or secondary
        secondary = None

    if primary is None:
        raise BackendUnavailable("No available backend (sxtwl/cnlunar)")

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
            primary = _fallback
        except (BackendUnavailable, Exception):
            raise BackendUnavailable(f"sxtwl 断言失败且 cnlunar 降级也失败: {_b3_err}") from _b3_err

    pillars_secondary: Pillars | None = secondary.get_pillars(dt_effective) if secondary else None

    if pillars_secondary is not None and pillars_primary.day.ganzhi != pillars_secondary.day.ganzhi:
        pillars_primary = pillars_secondary
        backend_source = "cnlunar_fallback"
        _sxtwl_fallback_warnings.append("sxtwl_day_pillar_mismatch")

    if zi_day_rule == "early_zi_same_day" and dt_effective.hour in (23, 0):
        pillars_primary = _apply_early_zi_same_day(primary, dt_effective, pillars_primary)
        if pillars_secondary is not None and secondary is not None:
            pillars_secondary = _apply_early_zi_same_day(secondary, dt_effective, pillars_secondary)

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
        pillars_layer=PILLARS_LAYER,
        zi_day_rule=zi_day_rule,
    )
