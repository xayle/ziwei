from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

from fastapi import HTTPException, status

from constants import CN_MAX_LON, CN_MIN_LON, MAX_LON, MIN_LON


@dataclass(frozen=True)
class BirthTimeNormalization:
    """后端统一的出生时间归一化结果。"""

    input_dt: datetime
    local_dt: datetime
    utc_dt: datetime
    tz_name: str
    normalized_birth_dt_local: str
    normalized_birth_dt_utc: str
    is_potential_china_dst: bool
    dst_adjustment_minutes: int
    dst_label: str
    time_risk_label: str
    time_risk_hint: str


def validate_lon_strict(lon: float) -> float:
    if lon is None or not isinstance(lon, int | float):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"code": "lon_invalid"})
    if not (MIN_LON <= lon <= MAX_LON):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "lon_out_of_range", "message": f"lon must be between {MIN_LON} and {MAX_LON}"},
        )
    return lon


def warn_lon_cn_range(tz: str, lon: float) -> list[dict[str, Any]]:
    warnings: list[dict[str, Any]] = []
    if tz == "Asia/Shanghai" and (lon < CN_MIN_LON or lon > CN_MAX_LON):
        warnings.append(
            {
                "code": "lon_out_of_cn_range",
                "message": "tz=Asia/Shanghai but lon is outside China range [73,135]; calculation continues.",
                "meta": {"tz": tz, "lon": lon, "expected_range": [CN_MIN_LON, CN_MAX_LON]},
            }
        )
    return warnings


def _pad2(value: int) -> str:
    return str(value).zfill(2)


def _format_local_dt(dt: datetime) -> str:
    return f"{dt.year:04d}-{_pad2(dt.month)}-{_pad2(dt.day)}T" f"{_pad2(dt.hour)}:{_pad2(dt.minute)}:{_pad2(dt.second)}"


def _get_first_sunday_on_or_after(year: int, month: int, day: int) -> datetime:
    start = datetime(year, month, day)
    offset = (6 - start.weekday()) % 7
    return start + timedelta(days=offset)


def _china_dst_window(year: int) -> tuple[datetime, datetime] | None:
    if year < 1986 or year > 1991:
        return None
    if year == 1986:
        return (
            datetime(1986, 5, 4, 2, 0, 0),
            datetime(1986, 9, 14, 2, 0, 0),
        )
    if year == 1991:
        return (
            datetime(1991, 4, 14, 2, 0, 0),
            datetime(1991, 9, 15, 2, 0, 0),
        )
    start = _get_first_sunday_on_or_after(year, 4, 10).replace(hour=2, minute=0, second=0, microsecond=0)
    end = _get_first_sunday_on_or_after(year, 9, 10).replace(hour=2, minute=0, second=0, microsecond=0)
    return start, end


def _is_china_dst(dt: datetime) -> bool:
    window = _china_dst_window(dt.year)
    if window is None:
        return False
    start, end = window
    return start <= dt.replace(tzinfo=None) < end


def _describe_time_risk(precision: str = "exact", fallback: str = "midday", is_dst: bool = False) -> tuple[str, str]:
    if precision == "unknown":
        label = "未知时辰"
        hint = f"已启用兜底策略：{'按正午' if fallback == 'midday' else '按午时' if fallback == 'noon' else '按整点'}。"
        return label, hint
    if precision == "hour":
        return "仅知时辰", "当前只知道时辰，遇到时辰交界时建议补分钟级时间。"
    if precision == "approximate":
        return "大致时间", "当前时间为近似值，接近时辰边界时请优先核对原始记录。"
    if is_dst:
        return "精确时间，含夏令时风险", "该时间落在中国历史夏令时窗口内，系统会自动按历史夏令时识别。"
    return "精确时间", "当前时间可直接用于排盘。"


def normalize_birth_datetime(
    dt: datetime,
    tz_name: str,
    *,
    auto_dst: bool = True,
    precision: str = "exact",
    unknown_time_fallback: str = "midday",
) -> BirthTimeNormalization:
    """归一化任意出生时间到统一本地时区基准。"""

    try:
        tz = ZoneInfo(tz_name)
    except Exception as exc:  # pragma: no cover - 依赖输入合法性
        raise ValueError(f"Invalid timezone: {tz_name!r}") from exc

    if dt.tzinfo is None or dt.utcoffset() is None:
        local_dt = dt.replace(tzinfo=tz)
    else:
        local_dt = dt.astimezone(tz)

    is_dst = bool(auto_dst and tz_name == "Asia/Shanghai" and _is_china_dst(local_dt))
    normalized_local = local_dt - timedelta(hours=1) if is_dst else local_dt
    utc_dt = normalized_local.astimezone(ZoneInfo("UTC"))
    risk_label, risk_hint = _describe_time_risk(precision, unknown_time_fallback, is_dst)

    return BirthTimeNormalization(
        input_dt=dt,
        local_dt=normalized_local,
        utc_dt=utc_dt,
        tz_name=tz_name,
        normalized_birth_dt_local=_format_local_dt(normalized_local),
        normalized_birth_dt_utc=utc_dt.isoformat(),
        is_potential_china_dst=is_dst,
        dst_adjustment_minutes=-60 if is_dst else 0,
        dst_label="中国历史夏令时已自动回拨 1 小时" if is_dst else "未触发历史夏令时窗口",
        time_risk_label=risk_label,
        time_risk_hint=risk_hint,
    )
