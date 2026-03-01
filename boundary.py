"""Boundary logic interfaces (single source of truth).

Signatures are fixed per dev-start checklist v5.3.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from typing import Literal, Optional

from constants import JIEQI_THRESHOLD_MIN, SHICHEN_THRESHOLD_MIN


@dataclass
class Pillar:
    stem: str
    branch: str
    ganzhi: Optional[str] = None  # display-only


@dataclass
class Pillars:
    year: Pillar
    month: Pillar
    day: Pillar
    hour: Pillar


@dataclass
class RiskFlags:
    near_shichen_boundary: bool
    near_jieqi_boundary: bool
    jieqi_boundary_status: Literal["ok", "unavailable"]
    minutes_to_shichen_boundary: Optional[float]
    minutes_to_jieqi_boundary: Optional[float]


@dataclass
class Validation:
    level: Literal["L0", "L1", "L2", "L3"]
    mode: Literal["dual", "single"]
    recommended: Literal["beijing_time", "solar_time", "none"]
    interpretation_enabled: bool
    reasons: list[str]
    diff_fields: list[Literal["year", "month", "day", "hour"]]
    risk_flags: RiskFlags
    boundary_risk_shichen: bool
    boundary_risk_jieqi: bool
    warnings: list[str]


def compute_risk_flags(
    dt_utc8,
    lon: float,
    solar_time_enabled: bool,
    jieqi_ctx,
) -> RiskFlags:
    """Compute boundary risk flags.

    dt_utc8: timezone-aware datetime in Asia/Shanghai
    lon: decimal degrees, validated in caller
    solar_time_enabled: bool toggle
    jieqi_ctx: optional context from sxtwl (None in single-lib)
    """
    minutes_to_shi = minutes_to_shichen_boundary(dt_utc8)
    near_shi = minutes_to_shi <= SHICHEN_THRESHOLD_MIN

    if jieqi_ctx is None:
        jieqi_status: Literal["ok", "unavailable"] = "unavailable"
        minutes_to_jieqi = None
        near_jieqi = False
    else:
        jieqi_status = "ok"
        delta_prev = abs((dt_utc8 - jieqi_ctx.prev_jie_dt).total_seconds()) / 60.0
        delta_next = abs((jieqi_ctx.next_jie_dt - dt_utc8).total_seconds()) / 60.0
        minutes_to_jieqi = min(delta_prev, delta_next)
        near_jieqi = minutes_to_jieqi <= JIEQI_THRESHOLD_MIN

    return RiskFlags(
        near_shichen_boundary=near_shi,
        near_jieqi_boundary=near_jieqi,
        jieqi_boundary_status=jieqi_status,
        minutes_to_shichen_boundary=minutes_to_shi,
        minutes_to_jieqi_boundary=minutes_to_jieqi,
    )


def compute_validation(
    pillars_primary: Pillars,
    pillars_secondary: Optional[Pillars],
    risk_flags: RiskFlags,
    mode: Literal["dual", "single"],
) -> Validation:
    """Compute validation outcome (levels, reasons, diff_fields, recommended).

    pillars_primary: required pillars
    pillars_secondary: optional secondary pillars (None in single mode)
    mode: dual|single indicates whether cross-validation ran
    """
    reasons: list[str] = []
    diff_fields: list[Literal["year", "month", "day", "hour"]] = []

    def add_reason(r: str) -> None:
        if r not in reasons:
            reasons.append(r)

    if mode == "single":
        add_reason("sxtwl_unavailable_single_mode")
    if risk_flags.jieqi_boundary_status == "unavailable":
        add_reason("jieqi_unavailable_single_mode")
    if risk_flags.near_shichen_boundary:
        add_reason("near_shichen_boundary")
    if risk_flags.near_jieqi_boundary:
        add_reason("near_jieqi_boundary")

    if pillars_secondary is not None:
        diff_fields = diff_pillars(pillars_primary, pillars_secondary)
        for field in diff_fields:
            add_reason(f"diff_{field}")

    boundary_risk_shi = risk_flags.near_shichen_boundary
    boundary_risk_jie = risk_flags.near_jieqi_boundary

    interpretation_enabled = (
        mode == "dual"
        and not boundary_risk_shi
        and not boundary_risk_jie
        and len(diff_fields) == 0
    )

    if boundary_risk_shi or boundary_risk_jie:
        recommended: Literal["beijing_time", "solar_time", "none"] = "none"
    else:
        recommended = "solar_time" if interpretation_enabled else "beijing_time"

    # ★ 0.22 修正: boundary_risk 不改变 L（仅写入 reasons 且禁解读）
    # 正确含义: L0=dual+无差异 / L1=single或仅时柱差异 / L2=含月柱差异 / L3=含日/年柱
    level: Literal["L0", "L1", "L2", "L3"]
    if mode == "single":
        # single 模式无对比数据，禁给最高级
        level = "L1"
    elif len(diff_fields) == 0:
        # dual + 双库完全一致 → L0（边界风险不影响 level）
        level = "L0"
    elif set(diff_fields) == {"hour"}:
        # 仅时柱差异
        level = "L1"
    elif set(diff_fields) <= {"month", "hour"}:
        # 含月柱差异（{month} 或 {hour, month}），不含日/年
        level = "L2"
    else:
        # 含日柱或年柱差异
        level = "L3"

    return Validation(
        level=level,
        mode=mode,
        recommended=recommended,
        interpretation_enabled=interpretation_enabled,
        reasons=reasons,
        diff_fields=diff_fields,
        risk_flags=risk_flags,
        boundary_risk_shichen=boundary_risk_shi,
        boundary_risk_jieqi=boundary_risk_jie,
        warnings=[],
    )


def same_pillar(a: Pillar, b: Pillar) -> bool:
    return a.stem == b.stem and a.branch == b.branch


def diff_pillars(p1: Pillars, p2: Pillars) -> list[Literal["year", "month", "day", "hour"]]:
    diffs = []
    for key in ["year", "month", "day", "hour"]:
        if not same_pillar(getattr(p1, key), getattr(p2, key)):
            diffs.append(key)
    return diffs


def minutes_to_shichen_boundary(dt_utc8) -> float:
    """Distance in minutes to nearest shichen boundary (odd hours starting 23)."""
    # Expect dt_utc8 tz-aware. Prev boundary is nearest past odd hour, with 23 from previous day.
    hour = dt_utc8.hour
    if hour == 0:
        prev_boundary = dt_utc8.replace(hour=23, minute=0, second=0, microsecond=0) - timedelta(days=1)
    elif hour % 2 == 1:
        prev_boundary = dt_utc8.replace(hour=hour, minute=0, second=0, microsecond=0)
    else:
        prev_boundary = dt_utc8.replace(hour=hour - 1, minute=0, second=0, microsecond=0)

    next_boundary = prev_boundary + timedelta(hours=2)
    minutes_since_prev = (dt_utc8 - prev_boundary).total_seconds() / 60.0
    minutes_to_next = (next_boundary - dt_utc8).total_seconds() / 60.0
    return min(minutes_since_prev, minutes_to_next)
