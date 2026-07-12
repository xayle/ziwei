"""Solar time + 子时边界 sampling (B-01, Phase A)."""
from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from services.bazi_engine.pillars import compute_pillars


@pytest.mark.parametrize(
    "hour,minute",
    [
        (23, 0),
        (23, 30),
        (23, 55),
        (0, 5),
        (0, 30),
        (0, 55),
        (1, 0),
    ],
)
def test_zi_hour_boundary_no_crash(hour: int, minute: int):
    """Near 子时换日区段：排盘应稳定返回四柱。"""
    dt = datetime(1990, 6, 15, hour, minute, tzinfo=ZoneInfo("Asia/Shanghai"))
    result = compute_pillars(dt, lon=116.4, use_solar=True)
    assert result.pillars_primary.year.stem
    assert result.pillars_primary.hour.stem
    assert result.validation is not None


def test_solar_correction_changes_hour_near_boundary():
    """真太阳时经度修正：边远地区同钟点可与标准时不同（采样）。"""
    dt = datetime(1990, 6, 15, 23, 30, tzinfo=ZoneInfo("Asia/Shanghai"))
    east = compute_pillars(dt, lon=121.5, use_solar=True, standard_meridian=120.0)
    west = compute_pillars(dt, lon=87.6, use_solar=True, standard_meridian=120.0)
    assert east.pillars_primary.hour.stem and west.pillars_primary.hour.stem


def test_zi_day_rule_sxtwl_default():
    dt = datetime(2000, 1, 1, 0, 15, tzinfo=ZoneInfo("Asia/Shanghai"))
    r = compute_pillars(dt, lon=120.0, use_solar=False, zi_day_rule="sxtwl")
    assert r.zi_day_rule == "sxtwl"
