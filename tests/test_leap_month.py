"""
B4: 闰月边界测试 — 已知闰月窗口内的日期应设置 leap_month_ambiguous=True

boundary._KNOWN_LEAP_MONTH_WINDOWS 共 9 个已知闰月区间。
测试覆盖：
  - 窗口内日期 → leap_month_ambiguous=True，warnings 含 "leap_month_ambiguous"
  - 窗口外日期 → leap_month_ambiguous=False，warnings 为空
  - 相邻边界（窗口前一天/后一天）→ False
  - compute_validation 最终 Validation.warnings 正确传播

验证命令：pytest tests/test_leap_month.py -v
"""
from __future__ import annotations

import pytest
from datetime import datetime, timezone, timedelta

from boundary import (
    RiskFlags,
    _KNOWN_LEAP_MONTH_WINDOWS,
    compute_risk_flags,
    compute_validation,
    Pillars,
    Pillar,
)

# ─────────────────────────────────────────────────────────────────────────────
# helpers
# ─────────────────────────────────────────────────────────────────────────────
_CST = timezone(timedelta(hours=8))


def _dt(year: int, month: int, day: int, hour: int = 12) -> datetime:
    """已知时区 +8（北京时间）的 datetime，对应 compute_risk_flags 的 dt_utc8 参数。"""
    return datetime(year, month, day, hour, 0, 0, tzinfo=_CST)


def _flags_for(dt: datetime) -> RiskFlags:
    """用 None jieqi_ctx（单库模式）调用 compute_risk_flags。"""
    return compute_risk_flags(dt, lon=116.4, solar_time_enabled=False, jieqi_ctx=None)


def _dummy_pillars() -> Pillars:
    return Pillars(
        year=Pillar("甲", "子", "甲子"),
        month=Pillar("丙", "寅", "丙寅"),
        day=Pillar("戊", "辰", "戊辰"),
        hour=Pillar("壬", "午", "壬午"),
    )


# ─────────────────────────────────────────────────────────────────────────────
# 窗口内 — 9 个已知闰月，每个取窗口最早一天和最晚一天各测一次
# ─────────────────────────────────────────────────────────────────────────────
INSIDE_CASES: list[tuple[int, int, int]] = []
for _year, _m_start, _m_end in _KNOWN_LEAP_MONTH_WINDOWS:
    # 取窗口开始月第 1 天 和 结束月 15 日
    INSIDE_CASES.append((_year, _m_start, 1))
    INSIDE_CASES.append((_year, _m_end, 15))


@pytest.mark.parametrize("year,month,day", INSIDE_CASES)
def test_in_window_leap_ambiguous(year: int, month: int, day: int) -> None:
    """闰月窗口内的日期 → leap_month_ambiguous=True"""
    flags = _flags_for(_dt(year, month, day))
    assert flags.leap_month_ambiguous is True, (
        f"{year}-{month:02d}-{day:02d} 应在闰月窗口内，但 leap_month_ambiguous=False"
    )


# ─────────────────────────────────────────────────────────────────────────────
# 窗口外 — 普通日期（非闰月年份/月份）
# ─────────────────────────────────────────────────────────────────────────────
OUTSIDE_CASES: list[tuple[int, int, int]] = [
    (1990, 7, 17),   # 普通日期
    (2000, 1, 1),    # 普通元旦
    (2025, 6, 15),   # 当前年份
    (1957, 7, 31),   # 窗口 (1957,8,9) 的前一天（7月31日）
    (1957, 10, 1),   # 窗口结束后（月份已超过9）
    (1976, 7, 31),   # 窗口 (1976,8,9) 前一天
    (1976, 10, 1),   # 窗口结束后
    (1984, 9, 30),   # 窗口 (1984,10,11) 前一天
    (1984, 12, 1),   # 窗口结束后
    (2004, 1, 31),   # 窗口 (2004,2,3) 前一天
    (2004, 4, 1),    # 窗口结束后
    (2023, 1, 31),   # 窗口 (2023,2,3) 前一天
    (2023, 4, 1),    # 窗口结束后
]


@pytest.mark.parametrize("year,month,day", OUTSIDE_CASES)
def test_outside_window_not_ambiguous(year: int, month: int, day: int) -> None:
    """非闰月窗口日期 → leap_month_ambiguous=False"""
    flags = _flags_for(_dt(year, month, day))
    assert flags.leap_month_ambiguous is False, (
        f"{year}-{month:02d}-{day:02d} 应在窗口外，但 leap_month_ambiguous=True"
    )


# ─────────────────────────────────────────────────────────────────────────────
# warnings 传播：compute_validation 应把 leap_month_ambiguous 写入 warnings
# ─────────────────────────────────────────────────────────────────────────────
def test_validation_warnings_contain_leap_ambiguous() -> None:
    """闰月窗口内日期的 Validation.warnings 应含 'leap_month_ambiguous'"""
    dt = _dt(1976, 8, 15)  # 1976年农历闰八月窗口内
    flags = _flags_for(dt)
    assert flags.leap_month_ambiguous is True

    pillars = _dummy_pillars()
    validation = compute_validation(
        pillars_primary=pillars,
        pillars_secondary=None,
        risk_flags=flags,
        mode="single",
    )
    assert "leap_month_ambiguous" in validation.warnings, (
        f"Validation.warnings={validation.warnings} 缺少 'leap_month_ambiguous'"
    )


def test_validation_warnings_empty_outside_window() -> None:
    """普通日期的 Validation.warnings 不含 'leap_month_ambiguous'"""
    dt = _dt(1990, 7, 17)
    flags = _flags_for(dt)
    assert flags.leap_month_ambiguous is False

    pillars = _dummy_pillars()
    validation = compute_validation(
        pillars_primary=pillars,
        pillars_secondary=None,
        risk_flags=flags,
        mode="single",
    )
    assert "leap_month_ambiguous" not in validation.warnings


# ─────────────────────────────────────────────────────────────────────────────
# 窗口覆盖完整性：确认 _KNOWN_LEAP_MONTH_WINDOWS 恰好 9 条
# ─────────────────────────────────────────────────────────────────────────────
def test_known_windows_count() -> None:
    """_KNOWN_LEAP_MONTH_WINDOWS 应包含 9 个已知闰月区间"""
    assert len(_KNOWN_LEAP_MONTH_WINDOWS) == 9, (
        f"期望 9 条闰月记录，实际 {len(_KNOWN_LEAP_MONTH_WINDOWS)}"
    )


def test_all_windows_have_valid_months() -> None:
    """所有闰月窗口的月份范围应在 1-12 内，且 m_start <= m_end"""
    for year, m_start, m_end in _KNOWN_LEAP_MONTH_WINDOWS:
        assert 1 <= m_start <= 12, f"year={year} m_start={m_start} 越界"
        assert 1 <= m_end <= 12,   f"year={year} m_end={m_end} 越界"
        assert m_start <= m_end,   f"year={year} 窗口反向 m_start={m_start} > m_end={m_end}"
