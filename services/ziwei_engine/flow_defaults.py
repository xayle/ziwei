"""Resolve default 流日/流时 parameters when include_flow_liuri is enabled."""

from __future__ import annotations

import datetime as _dt
from zoneinfo import ZoneInfo

from .lunar import solar_to_lunar


def resolve_flow_params(
    *,
    template_version: str,
    include_flow_liuri: bool | None,
    liunian_year: int | None,
    birth_year: int,
    birth_month: int,
    birth_day: int,
    birth_hour: int,
    birth_minute: int,
    leap_month_method: str,
    flow_lunar_day: int | None,
    flow_liuyue_month: int | None,
    flow_hour_branch: int | None,
) -> tuple[int | None, int | None, int | None]:
    """
    Return (flow_lunar_day, flow_liuyue_month, flow_hour_branch).

    When include is True and flow day/month are omitted, derive from the liunian
    reference solar date (today if liunian_year is current year, else mid-year).
    """
    include = include_flow_liuri
    if include is None:
        include = template_version in ("standard", "pro")

    if not include:
        return flow_lunar_day, flow_liuyue_month, flow_hour_branch

    if flow_lunar_day is not None and flow_liuyue_month is not None:
        return flow_lunar_day, flow_liuyue_month, flow_hour_branch

    tz = ZoneInfo("Asia/Shanghai")
    now = _dt.datetime.now(tz)
    ref_year = liunian_year if liunian_year is not None else now.year
    if ref_year == now.year:
        ref_date = now.date()
        ref_hour = now.hour
    else:
        ref_date = _dt.date(ref_year, 6, 15)
        ref_hour = birth_hour

    lunar = solar_to_lunar(
        ref_date.year,
        ref_date.month,
        ref_date.day,
        ref_hour,
        birth_minute,
        leap_month_method=leap_month_method,
    )
    resolved_day = lunar.lunar_day
    resolved_month = lunar.calc_lunar_month
    resolved_hour = flow_hour_branch if flow_hour_branch is not None else lunar.hour_branch_idx
    return resolved_day, resolved_month, resolved_hour
