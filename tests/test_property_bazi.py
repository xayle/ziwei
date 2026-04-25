"""
O8: Hypothesis 属性测试 — calculate() 对任意日期/经度不应崩溃

验证：1900-2100 任意日期时间 + 大陆经度 → 年柱天干必须在 STEMS 内，且无未捕获异常。
"""
from __future__ import annotations

import pytest
from datetime import datetime
from zoneinfo import ZoneInfo

from hypothesis import given, settings, HealthCheck
from hypothesis import strategies as st

from constants import STEMS

_CST = ZoneInfo("Asia/Shanghai")


@given(
    dt=st.datetimes(
        min_value=datetime(1900, 1, 1),
        max_value=datetime(2100, 12, 31, 23, 59, 59),
    ),
    lon=st.floats(
        min_value=73.0, max_value=135.0,
        allow_nan=False, allow_infinity=False,
    ),
)
@settings(
    max_examples=200,
    suppress_health_check=[HealthCheck.too_slow],
    deadline=None,
)
def test_calculate_never_raises(dt: datetime, lon: float) -> None:
    """O8: 200 个随机日期 + 经度，calculate() 不抛出未预期异常，年柱天干合法。"""
    from services.bazi_engine_service import calculate

    # 将 Hypothesis 生成的 naive datetime 本地化为 Asia/Shanghai
    dt_cst = dt.replace(tzinfo=_CST)

    _ALLOWED_EXC = frozenset({
        "BackendUnavailable",
        "ValidationException",
        "ServiceException",
    })
    try:
        result = calculate(dt_cst, lon, "Asia/Shanghai")
        year_stem = result.verify_response.pillars_primary.year.stem
        assert year_stem in STEMS, (
            f"年柱天干 {year_stem!r} 不在 STEMS，dt={dt_cst}, lon={lon}"
        )
    except Exception as exc:
        exc_name = type(exc).__name__
        if exc_name not in _ALLOWED_EXC:
            raise
