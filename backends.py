"""Backend adapters for pillars and optional jieqi context.

This file intentionally contains no rule duplication. It only adapts upstream
libraries into the shared `Pillars` shape used by boundary/validation.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from zoneinfo import ZoneInfo

from boundary import Pillar, Pillars


class BackendUnavailable(RuntimeError):
    """Raised when a backend library is missing or cannot initialize."""


@dataclass
class JieqiContext:
    """Optional jieqi context returned by sxtwl (prev/next 12-jie markers)."""

    prev_jie_dt: datetime
    next_jie_dt: datetime
    prev_jie_name: str
    next_jie_name: str


def _ensure_tz(dt_utc8):
    if dt_utc8.tzinfo is None or dt_utc8.utcoffset() is None:
        raise ValueError("dt_utc8 must be timezone-aware (Asia/Shanghai)")
    return dt_utc8.astimezone(ZoneInfo("Asia/Shanghai"))


class SxtwlBackend:
    """Adapter for `sxtwl` library."""

    name = "sxtwl"

    STEMS = "甲乙丙丁戊己庚辛壬癸"
    BRANCHES = "子丑寅卯辰巳午未申酉戌亥"
    JIE_NAMES = [
        "冬至",
        "小寒",
        "大寒",
        "立春",
        "雨水",
        "惊蛰",
        "春分",
        "清明",
        "谷雨",
        "立夏",
        "小满",
        "芒种",
        "夏至",
        "小暑",
        "大暑",
        "立秋",
        "处暑",
        "白露",
        "秋分",
        "寒露",
        "霜降",
        "立冬",
        "小雪",
        "大雪",
    ]

    def __init__(self):
        try:
            import sxtwl  # type: ignore
        except ImportError as exc:  # pragma: no cover - depends on external lib
            raise BackendUnavailable("sxtwl is not installed") from exc
        self.sxtwl = sxtwl
        self._tz = ZoneInfo("Asia/Shanghai")

    def _build_jieqi_list(self, year: int):
        twelve_jie_idx = [3, 5, 7, 9, 11, 13, 15, 17, 19, 21, 23, 1]
        infos = self.sxtwl.getJieQiByYear(year)
        items = []
        for info in infos:
            idx = int(info.jqIndex)
            if idx not in twelve_jie_idx:
                continue
            dd = self.sxtwl.JD2DD(info.jd)
            dt = datetime(dd.Y, dd.M, dd.D, int(dd.h), int(dd.m), int(dd.s), tzinfo=self._tz)
            items.append((dt, self.JIE_NAMES[idx]))
        return items

    def _build_pillar(self, gz) -> Pillar:
        stem = self.STEMS[gz.tg]
        branch = self.BRANCHES[gz.dz]
        return Pillar(stem=stem, branch=branch, ganzhi=f"{stem}{branch}")

    def get_pillars(self, dt_utc8) -> Pillars:
        dt_local = _ensure_tz(dt_utc8)
        day = self.sxtwl.fromSolar(dt_local.year, dt_local.month, dt_local.day)

        gz_year = day.getYearGZ()
        gz_month = day.getMonthGZ()
        gz_day = day.getDayGZ()
        gz_hour = self.sxtwl.getShiGz(gz_day.tg, dt_local.hour)

        return Pillars(
            year=self._build_pillar(gz_year),
            month=self._build_pillar(gz_month),
            day=self._build_pillar(gz_day),
            hour=self._build_pillar(gz_hour),
        )

    def get_jieqi_context(self, dt_utc8) -> Optional[JieqiContext]:
        dt_local = _ensure_tz(dt_utc8)
        year = dt_local.year
        candidates = []
        for y in (year - 1, year, year + 1):
            candidates.extend(self._build_jieqi_list(y))

        # Deduplicate and sort
        seen = set()
        uniq = []
        for dt, name in candidates:
            key = (dt, name)
            if key in seen:
                continue
            seen.add(key)
            uniq.append((dt, name))
        uniq.sort(key=lambda x: x[0])

        prev_item = None
        next_item = None
        for dt, name in uniq:
            if dt <= dt_local:
                prev_item = (dt, name)
            if dt > dt_local and next_item is None:
                next_item = (dt, name)
        if prev_item is None:
            prev_item = uniq[0]
        if next_item is None:
            next_item = uniq[-1]

        return JieqiContext(
            prev_jie_dt=prev_item[0],
            next_jie_dt=next_item[0],
            prev_jie_name=prev_item[1],
            next_jie_name=next_item[1],
        )


class CnlunarBackend:
    """Adapter for `cnlunar` library."""

    name = "cnlunar"

    def __init__(self):
        try:
            import cnlunar  # type: ignore
        except ImportError as exc:  # pragma: no cover - depends on external lib
            raise BackendUnavailable("cnlunar is not installed") from exc
        self.cnlunar = cnlunar

    def get_pillars(self, dt_utc8) -> Pillars:
        dt_local = _ensure_tz(dt_utc8)
        dt_naive = dt_local.replace(tzinfo=None)
        lunar = self.cnlunar.Lunar(dt_naive)

        def split_gz(text: str) -> Pillar:
            stem, branch = text[0], text[1]
            return Pillar(stem=stem, branch=branch, ganzhi=text)

        # cnlunar exposes strings like "甲子"
        year = split_gz(lunar.get_year8Char())
        month = split_gz(lunar.get_month8Char())
        day = split_gz(lunar.get_day8Char())
        hour_list = lunar.get_twohour8CharList()
        assert len(hour_list) >= 13, (  # 0.20: P65 断言保护
            f"cnlunar.get_twohour8CharList() 返回 {len(hour_list)} 项，期望 ≥13"
        )
        hour_idx = min((dt_naive.hour + 1) // 2, len(hour_list) - 1)
        hour = split_gz(hour_list[hour_idx])

        return Pillars(year=year, month=month, day=day, hour=hour)


def get_pillars(dt_utc8, backend: str = "sxtwl") -> Pillars:
    """Return pillars from chosen backend (sxtwl|cnlunar)."""
    if backend == "sxtwl":
        return SxtwlBackend().get_pillars(dt_utc8)
    if backend == "cnlunar":
        return CnlunarBackend().get_pillars(dt_utc8)
    raise ValueError(f"Unsupported backend: {backend}")


def get_jieqi_context(dt_utc8) -> Optional[JieqiContext]:
    """Return jieqi context if backend supports it (sxtwl)."""
    try:
        return SxtwlBackend().get_jieqi_context(dt_utc8)
    except BackendUnavailable:
        return None
