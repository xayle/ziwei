#!/usr/bin/env python3
"""Engine horoscope snapshot for advisory iztro/wenmo cross-check scripts."""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from services.ziwei_engine import ziwei_full
from services.ziwei_engine.dayun import resolve_current_dayun_item

RANGE_RE = re.compile(r"(\d+)\s*~\s*(\d+)")


def _gender_label(raw: str) -> str:
    if raw in ("female", "女"):
        return "女"
    return "男"


def _virtual_age(birth_year: int, query: date, birth_month: int, birth_day: int) -> int:
    """虚岁：出生当年为 1，生日后加 1。"""
    age = query.year - birth_year + 1
    if (query.month, query.day) < (birth_month, birth_day):
        age -= 1
    return max(1, age)


def _palace_for_branch(chart, branch_idx: int) -> str | None:
    for palace in chart.palaces:
        if palace.branch_idx == branch_idx:
            return palace.name
    return None


def engine_horoscope_snapshot(case: dict, query_dates: list[str]) -> dict:
    gender = _gender_label(case.get("gender", "male"))
    chart = ziwei_full(
        case["birth_year"],
        case["birth_month"],
        case["birth_day"],
        case["birth_hour"],
        case.get("birth_minute", 0),
        gender,
    )
    dayun_rows = []
    for item in chart.dayun.items:
        dayun_rows.append(
            {
                "index": item.index,
                "ganzhi": item.ganzhi,
                "start_age": item.start_age,
                "end_age": item.end_age,
                "branch_idx": item.branch_idx,
                "palace_name": _palace_for_branch(chart, item.branch_idx),
            }
        )

    samples = []
    for raw_date in query_dates:
        parts = [int(x) for x in raw_date.split("-")]
        query = date(parts[0], parts[1], parts[2])
        age = _virtual_age(
            case["birth_year"],
            query,
            case["birth_month"],
            case["birth_day"],
        )
        current = resolve_current_dayun_item(chart.dayun, age)
        samples.append(
            {
                "query_date": raw_date,
                "virtual_age": age,
                "decadal_ganzhi": current.ganzhi if current else None,
                "decadal_palace": _palace_for_branch(chart, current.branch_idx) if current else None,
                "decadal_start_age": current.start_age if current else None,
                "decadal_end_age": current.end_age if current else None,
            }
        )

    return {
        "id": case.get("id"),
        "birth": {
            "year": case["birth_year"],
            "month": case["birth_month"],
            "day": case["birth_day"],
            "hour": case["birth_hour"],
            "minute": case.get("birth_minute", 0),
            "gender": gender,
        },
        "dayun_start_age": chart.dayun.start_age,
        "dayun_forward": chart.dayun.forward,
        "dayun_items": dayun_rows,
        "samples": samples,
    }


def wenmo_dayun_ranges(case: dict) -> list[dict]:
    rows = []
    for palace in case.get("palaces", []):
        raw = palace.get("dayun_range")
        if not raw:
            continue
        match = RANGE_RE.search(str(raw))
        if not match:
            continue
        start_age, end_age = int(match.group(1)), int(match.group(2))
        rows.append(
            {
                "palace_name": palace.get("palace"),
                "branch": palace.get("branch"),
                "wenmo_start_age": start_age,
                "wenmo_end_age": end_age,
                "wenmo_range_text": raw,
            }
        )
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description="Engine horoscope JSON snapshot")
    parser.add_argument("--case-json", required=True, help="JSON object for one birth case")
    parser.add_argument(
        "--query-dates",
        default="",
        help="Comma-separated ISO dates, e.g. 2026-7-12,2018-6-29",
    )
    args = parser.parse_args()
    case = json.loads(args.case_json)
    query_dates = [d.strip() for d in args.query_dates.split(",") if d.strip()]
    if not query_dates:
        birth_year = case["birth_year"]
        query_dates = [
            f"{birth_year + 14}-6-15",
            f"{birth_year + 25}-6-29",
            f"{birth_year + 33}-7-12",
        ]
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps(engine_horoscope_snapshot(case, query_dates), ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
