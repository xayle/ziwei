from __future__ import annotations

from datetime import datetime
from functools import lru_cache

from app.core.boundary import _KNOWN_LEAP_MONTH_WINDOWS


@lru_cache(maxsize=2048)
def infer_case_leap_month(
    birth_dt_local: str | None,
    calendar_mode: str | None,
) -> bool | None:
    """Infer leap-month flag for a case from its local birth datetime.

    This is a best-effort helper for Gregorian-born archive inputs that should
    not rely on user-entered booleans. It only returns a deterministic result
    when the calendar mode is lunar and the local birth date lands inside a
    known leap-month window. Otherwise it returns None.
    """

    if not birth_dt_local:
        return None

    try:
        dt = datetime.fromisoformat(birth_dt_local)
    except ValueError:
        return None

    # Prefer exact backend inference when available.
    try:
        import sxtwl  # type: ignore

        lunar = sxtwl.fromSolar(dt.year, dt.month, dt.day)
        if hasattr(lunar, "isLunarLeap"):
            return bool(lunar.isLunarLeap())
    except Exception:
        pass

    try:
        import cnlunar  # type: ignore

        lunar = cnlunar.Lunar(dt)
        if hasattr(lunar, "isLunarLeapMonth"):
            return bool(lunar.isLunarLeapMonth)
    except Exception:
        pass

    for year, month_start, month_end in _KNOWN_LEAP_MONTH_WINDOWS:
        if dt.year == year and month_start <= dt.month <= month_end:
            return True

    return False
