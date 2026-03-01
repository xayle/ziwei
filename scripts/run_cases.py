"""Regression runner for golden cases.

Fill `GOLDEN_CASES` with your curated dt/lon/mode examples. The runner will
bucket results by level and mode, and skip cases if backends are unavailable.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
import hashlib
from importlib import metadata
from typing import Dict, List, Tuple, Literal
from zoneinfo import ZoneInfo

from backends import BackendUnavailable, SxtwlBackend
from constants import (
    API_VERSION,
    JIEQI_THRESHOLD_MIN,
    RULE_VERSION,
    SHICHEN_THRESHOLD_MIN,
    SUPPORTED_YEAR_RANGE,
)
from verify import verify


@dataclass
class Case:
    name: str
    dt_utc8: datetime
    lon: float
    mode: Literal["dual", "single"] = "dual"
    use_solar: bool = False


tz = ZoneInfo("Asia/Shanghai")


# Seed with a minimal interpretable baseline; adjust/expand as needed.
GOLDEN_CASES: List[Case] = [
    Case("normal_dual_midday", datetime(2026, 2, 24, 12, 34, tzinfo=tz), 120.0, mode="dual"),
    Case("normal_single_midday", datetime(2026, 2, 24, 12, 34, tzinfo=tz), 120.0, mode="single"),
    Case("early_zi_start", datetime(2026, 2, 24, 23, 0, tzinfo=tz), 120.0, mode="dual"),
    Case("early_zi_end", datetime(2026, 2, 25, 0, 0, tzinfo=tz), 120.0, mode="dual"),
    Case("shichen_boundary", datetime(2026, 2, 24, 22, 59, tzinfo=tz), 120.0, mode="dual"),
    Case("jieqi_near_lichun_minus", datetime(2026, 2, 4, 16, 20, tzinfo=tz), 120.0, mode="dual"),
    Case("jieqi_near_lichun_plus", datetime(2026, 2, 4, 16, 40, tzinfo=tz), 120.0, mode="dual"),
]


def add_jieqi_window_cases(
    center_dt: datetime, lon: float, mode: Literal["dual", "single"] = "dual", use_solar: bool = False
) -> List[Case]:
    """Generate ±61/59/0 minute windows around a nearby jieqi using sxtwl ctx."""
    try:
        backend = SxtwlBackend()
    except BackendUnavailable:
        return []

    ctx = backend.get_jieqi_context(center_dt)
    if ctx is None:
        return []

    # Choose next if in future else prev as center; avoids hardcoded timestamps.
    center = ctx.next_jie_dt if ctx.next_jie_dt >= center_dt else ctx.prev_jie_dt
    offsets = [-61, -59, 0, 59, 61]
    cases: List[Case] = []
    for off in offsets:
        label = f"jieqi_window_{off:+d}"
        cases.append(Case(label, center + timedelta(minutes=off), lon, mode=mode, use_solar=use_solar))
    return cases


def _pkg_version(name: str) -> str:
    try:
        return metadata.version(name)
    except metadata.PackageNotFoundError:
        return "unavailable"


def _input_hash(case: Case) -> str:
    raw = f"{case.name}|{case.dt_utc8.isoformat()}|{case.lon}|{case.mode}|{case.use_solar}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:12]


def _aggregate(level: str, mode: str, buckets: Dict[str, Dict[str, int]]) -> None:
    buckets.setdefault(mode, {})
    buckets[mode][level] = buckets[mode].get(level, 0) + 1


def main():
    if not GOLDEN_CASES:
        print("No golden cases defined; add entries to GOLDEN_CASES.")
        return

    cases: List[Case] = list(GOLDEN_CASES)
    # Mirror the 5-point jieqi window from tests for human-readable regression.
    if GOLDEN_CASES:
        lichun_anchor = datetime(2026, 2, 4, 16, 20, tzinfo=tz)
        cases.extend(add_jieqi_window_cases(lichun_anchor, lon=120.0, mode="dual", use_solar=False))

    print("== Regression Baseline ==")
    print(
        f"api_version={API_VERSION} rule_version={RULE_VERSION} sxtwl_version={_pkg_version('sxtwl')} "
        f"cnlunar_version={_pkg_version('cnlunar')}"
    )
    print(
        f"thresholds: shichen={SHICHEN_THRESHOLD_MIN}min jieqi={JIEQI_THRESHOLD_MIN}min jieqi_set=12jie "
        f"supported_year_range={SUPPORTED_YEAR_RANGE} run_ts={datetime.now(tz).isoformat()}"
    )

    buckets: Dict[str, Dict[str, int]] = {}
    skipped: List[Tuple[str, str]] = []
    failures: List[Tuple[str, str]] = []
    passes: List[str] = []
    jie_window_near = 0
    jie_window_total = 0

    for case in cases:
        input_digest = _input_hash(case)
        try:
            result = verify(case.dt_utc8, lon=case.lon, use_solar=case.use_solar, mode=case.mode)
            _aggregate(result.level, result.mode, buckets)
            passes.append(case.name)

            rf = result.risk_flags
            print(
                f"[PASS] {case.name} hash={input_digest} mode={result.mode} "
                f"recommended={result.recommended} interp={result.interpretation_enabled} level={result.level}"
            )
            print(f"  diff_fields={result.diff_fields} reasons={result.reasons}")
            print(
                f"  risk near_shi={rf.near_shichen_boundary} min_shi={rf.minutes_to_shichen_boundary} "
                f"near_jie={rf.near_jieqi_boundary} min_jie={rf.minutes_to_jieqi_boundary} "
                f"jie_status={rf.jieqi_boundary_status}"
            )

            if case.name.startswith("jieqi_window_"):
                jie_window_total += 1
                if rf.near_jieqi_boundary:
                    jie_window_near += 1
        except BackendUnavailable as exc:
            skipped.append((case.name, f"hash={input_digest} reason={exc}"))
        except Exception as exc:  # pragma: no cover - debug aid for ad-hoc runs
            failures.append((case.name, f"hash={input_digest} reason={exc}"))

    print("Summary (level x mode):")
    for mode, levels in buckets.items():
        print(f"  {mode}: " + ", ".join(f"{lvl}={count}" for lvl, count in sorted(levels.items())))

    if jie_window_total:
        print(f"Jieqi window near count: {jie_window_near}/{jie_window_total} (threshold={JIEQI_THRESHOLD_MIN}m)")

    if passes:
        print(f"Passed cases: {', '.join(passes)}")

    if skipped:
        print("Skipped cases (backend unavailable):")
        for name, reason in skipped:
            print(f"  {name}: {reason}")

    if failures:
        print("Failed cases:")
        for name, reason in failures:
            print(f"  {name}: {reason}")


if __name__ == "__main__":
    main()
