"""Core tests for boundary and solar time helpers."""
from __future__ import annotations

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pytest

from backends import BackendUnavailable, CnlunarBackend, JieqiContext, SxtwlBackend
from boundary import (
    Pillar,
    Pillars,
    compute_risk_flags,
    compute_validation,
    diff_pillars,
    minutes_to_shichen_boundary,
)
from verify import verify
from solar_time import compute_solar_correction_minutes


tz = ZoneInfo("Asia/Shanghai")


def test_minutes_to_shichen_boundary():
    assert minutes_to_shichen_boundary(datetime(2024, 1, 1, 23, 0, tzinfo=tz)) == 0
    assert minutes_to_shichen_boundary(datetime(2024, 1, 1, 23, 14, tzinfo=tz)) == 14
    assert minutes_to_shichen_boundary(datetime(2024, 1, 1, 23, 16, tzinfo=tz)) == 16
    assert minutes_to_shichen_boundary(datetime(2024, 1, 2, 0, 30, tzinfo=tz)) == 30
    assert minutes_to_shichen_boundary(datetime(2024, 1, 2, 0, 0, tzinfo=tz)) == 60
    assert minutes_to_shichen_boundary(datetime(2024, 1, 2, 0, 59, tzinfo=tz)) == 1
    assert minutes_to_shichen_boundary(datetime(2024, 1, 1, 22, 59, tzinfo=tz)) == 1
    assert minutes_to_shichen_boundary(datetime(2024, 1, 1, 23, 0, 30, tzinfo=tz)) == 0.5


def test_diff_ignores_ganzhi():
    p1 = Pillars(
        year=Pillar("甲", "子"),
        month=Pillar("乙", "丑", "乙丑"),
        day=Pillar("丙", "寅"),
        hour=Pillar("丁", "卯"),
    )
    p2 = Pillars(
        year=Pillar("甲", "子", "甲子"),
        month=Pillar("乙", "丑"),
        day=Pillar("丙", "寅"),
        hour=Pillar("丁", "卯"),
    )
    assert diff_pillars(p1, p2) == []


def test_diff_order_stable():
    p1 = Pillars(
        year=Pillar("甲", "子"),
        month=Pillar("乙", "丑"),
        day=Pillar("丙", "寅"),
        hour=Pillar("丁", "卯"),
    )
    p2 = Pillars(
        year=Pillar("庚", "申"),
        month=Pillar("乙", "丑"),
        day=Pillar("丙", "寅"),
        hour=Pillar("戊", "辰"),
    )
    assert diff_pillars(p1, p2) == ["year", "hour"]


def test_single_mode_jieqi_unavailable():
    dt = datetime(2024, 2, 4, 10, 0, tzinfo=tz)
    rf = compute_risk_flags(dt, lon=120.0, solar_time_enabled=False, jieqi_ctx=None)
    assert rf.jieqi_boundary_status == "unavailable"
    assert rf.minutes_to_jieqi_boundary is None
    assert rf.near_jieqi_boundary is False


def test_validation_gates():
    dt = datetime(2024, 2, 4, 10, 0, tzinfo=tz)
    # dual, no diff, no risks -> interpretation enabled
    far_ctx = JieqiContext(
        prev_jie_dt=dt - timedelta(days=5),
        next_jie_dt=dt + timedelta(days=5),
        prev_jie_name="立春",
        next_jie_name="惊蛰",
    )
    rf_ok = compute_risk_flags(dt, lon=120.0, solar_time_enabled=False, jieqi_ctx=far_ctx)
    p = Pillars(Pillar("甲", "子"), Pillar("乙", "丑"), Pillar("丙", "寅"), Pillar("丁", "卯"))
    v_ok = compute_validation(p, p, rf_ok, mode="dual")
    assert v_ok.interpretation_enabled is True
    assert v_ok.recommended == "solar_time"

    # diff present -> disabled
    p2 = Pillars(Pillar("甲", "子"), Pillar("乙", "丑"), Pillar("戊", "辰"), Pillar("丁", "卯"))
    v_diff = compute_validation(p, p2, rf_ok, mode="dual")
    assert v_diff.interpretation_enabled is False

    # near shichen -> disabled
    rf_near = rf_ok
    rf_near.near_shichen_boundary = True
    v_near = compute_validation(p, p, rf_near, mode="dual")
    assert v_near.interpretation_enabled is False

    # single mode always disabled
    v_single = compute_validation(p, None, rf_ok, mode="single")
    assert v_single.interpretation_enabled is False


def test_reason_dedup():
    dt = datetime(2024, 2, 4, 23, 0, tzinfo=tz)
    rf = compute_risk_flags(dt, lon=120.0, solar_time_enabled=False, jieqi_ctx=None)
    # force both near_shichen and single-mode reason
    v = compute_validation(
        pillars_primary=Pillars(Pillar("甲", "子"), Pillar("乙", "丑"), Pillar("丙", "寅"), Pillar("丁", "卯")),
        pillars_secondary=None,
        risk_flags=rf,
        mode="single",
    )
    assert v.reasons.count("near_shichen_boundary") == 1
    assert v.reasons.count("sxtwl_unavailable_single_mode") == 1


def test_longitude_correction():
    delta, corr = compute_solar_correction_minutes(121.0)
    assert delta == 1.0
    assert corr == 4.0
    delta, corr = compute_solar_correction_minutes(119.0)
    assert delta == -1.0
    assert corr == -4.0


def test_jieqi_boundary_window():
    T = datetime(2026, 2, 4, 4, 1, tzinfo=tz)
    ctx = JieqiContext(prev_jie_dt=T, next_jie_dt=T, prev_jie_name="立春", next_jie_name="立春")

    offsets = [-61, -59, 0, 59, 61]
    expected_minutes = [61, 59, 0, 59, 61]
    expected_near = [False, True, True, True, False]

    for off, exp_min, exp_near in zip(offsets, expected_minutes, expected_near):
        dt = T + timedelta(minutes=off)
        rf = compute_risk_flags(dt, lon=120.0, solar_time_enabled=False, jieqi_ctx=ctx)
        assert pytest.approx(rf.minutes_to_jieqi_boundary, rel=0, abs=0.1) == exp_min
        assert rf.near_jieqi_boundary is exp_near


def test_force_sxtwl_unavailable_downgrades(monkeypatch):
    class Boom(Exception):
        pass

    from backends import SxtwlBackend

    def boom_init(*args, **kwargs):
        raise BackendUnavailable("forced missing")

    monkeypatch.setattr(SxtwlBackend, "__init__", boom_init)

    dt = datetime(2026, 2, 24, 12, 34, tzinfo=tz)
    v = verify(dt, lon=120.0, use_solar=False, mode="dual")
    assert v.mode == "single"
    assert "sxtwl_unavailable_single_mode" in v.reasons
    assert v.risk_flags.jieqi_boundary_status == "unavailable"
    assert v.interpretation_enabled is False

@pytest.mark.sxtwl
@pytest.mark.cnlunar
def test_backends_smoke():
    dt = datetime(2026, 2, 24, 12, 34, tzinfo=tz)
    try:
        p1 = SxtwlBackend().get_pillars(dt)
    except BackendUnavailable:
        pytest.skip("sxtwl not installed")
    assert all(getattr(p1, field).stem and getattr(p1, field).branch for field in ["year", "month", "day", "hour"])

    try:
        p2 = CnlunarBackend().get_pillars(dt)
    except BackendUnavailable:
        pytest.skip("cnlunar not installed")
    assert all(getattr(p2, field).stem and getattr(p2, field).branch for field in ["year", "month", "day", "hour"])


@pytest.mark.sxtwl
def test_jieqi_context_prev_next():
    dt = datetime(2026, 2, 24, 12, 34, tzinfo=tz)
    try:
        backend = SxtwlBackend()
    except BackendUnavailable:
        pytest.skip("sxtwl not installed")
    ctx = backend.get_jieqi_context(dt)
    assert ctx is not None
    assert ctx.prev_jie_dt.tzinfo is not None
    assert ctx.next_jie_dt.tzinfo is not None
    assert ctx.prev_jie_dt < dt < ctx.next_jie_dt
    allowed_names = {"小寒", "大寒", "立春", "雨水", "惊蛰", "春分", "清明", "谷雨", "立夏", "小满", "芒种", "夏至", "小暑", "大暑", "立秋", "处暑", "白露", "秋分", "寒露", "霜降", "立冬", "小雪", "大雪", "冬至"}
    assert ctx.prev_jie_name in allowed_names
    assert ctx.next_jie_name in allowed_names


def test_boundary_uses_jieqi_minutes():
    dt = datetime(2024, 2, 4, 10, 0, tzinfo=tz)
    ctx = JieqiContext(
        prev_jie_dt=dt - timedelta(minutes=10),
        next_jie_dt=dt + timedelta(minutes=70),
        prev_jie_name="立春",
        next_jie_name="惊蛰",
    )
    rf = compute_risk_flags(dt, lon=120.0, solar_time_enabled=False, jieqi_ctx=ctx)
    assert rf.minutes_to_jieqi_boundary == 10
    assert rf.near_jieqi_boundary is True
