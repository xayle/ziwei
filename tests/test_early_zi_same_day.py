from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from services.bazi_engine.pillars import compute_pillars


def test_early_zi_same_day_pins_calendar_day_at_23h():
    """23:30 当日不换日：日柱应与当日中午锚定一致。"""
    dt = datetime(2000, 6, 15, 23, 30, tzinfo=ZoneInfo("Asia/Shanghai"))
    same_day = compute_pillars(dt, lon=116.4, use_solar=False, zi_day_rule="early_zi_same_day")
    default = compute_pillars(dt, lon=116.4, use_solar=False, zi_day_rule="sxtwl")
    anchor = compute_pillars(
        datetime(2000, 6, 15, 12, 0, tzinfo=ZoneInfo("Asia/Shanghai")),
        lon=116.4,
        use_solar=False,
        zi_day_rule="sxtwl",
    )
    assert same_day.pillars_primary.day.ganzhi == anchor.pillars_primary.day.ganzhi
    assert same_day.pillars_primary.hour.branch == "子"
    if default.pillars_primary.day.ganzhi != anchor.pillars_primary.day.ganzhi:
        assert same_day.pillars_primary.day.ganzhi != default.pillars_primary.day.ganzhi


def test_early_zi_same_day_at_midnight():
    dt = datetime(2000, 6, 16, 0, 15, tzinfo=ZoneInfo("Asia/Shanghai"))
    same_day = compute_pillars(dt, lon=116.4, use_solar=False, zi_day_rule="early_zi_same_day")
    anchor = compute_pillars(
        datetime(2000, 6, 16, 12, 0, tzinfo=ZoneInfo("Asia/Shanghai")),
        lon=116.4,
        use_solar=False,
    )
    assert same_day.pillars_primary.day.ganzhi == anchor.pillars_primary.day.ganzhi
