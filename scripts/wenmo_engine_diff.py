#!/usr/bin/env python3
"""Compare engine output vs 文墨天机 reference cases (advisory only)."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from services.ziwei_engine import ziwei_full

CASES_PATH = ROOT / "data" / "imported" / "wenmo_reference_cases.json"
LIFE_OUT_PATH = ROOT / "docs" / "reports" / "wenmo-engine-diff-latest.json"
HOROSCOPE_OUT_PATH = ROOT / "docs" / "reports" / "wenmo-horoscope-diff-latest.json"
BAZI_OUT_PATH = ROOT / "docs" / "reports" / "wenmo-bazi-diff-latest.json"

RANGE_RE = re.compile(r"(\d+)\s*~\s*(\d+)")


def _gender_label(case: dict) -> str:
    gender = case.get("gender", "male")
    return "女" if gender in ("female", "女") else "男"


def _engine_chart(case: dict):
    return ziwei_full(
        case["birth_year"],
        case["birth_month"],
        case["birth_day"],
        case["birth_hour"],
        case.get("birth_minute", 0),
        _gender_label(case),
    )


def _engine_life_palace(case: dict) -> str:
    return _engine_chart(case).life_palace_gz


def _palace_for_branch(chart, branch_idx: int) -> str | None:
    for palace in chart.palaces:
        if palace.branch_idx == branch_idx:
            return palace.name
    return None


def _parse_dayun_range(raw: str | None) -> tuple[int, int] | None:
    if not raw:
        return None
    match = RANGE_RE.search(str(raw))
    if not match:
        return None
    return int(match.group(1)), int(match.group(2))


def _engine_bazi_pillars(case: dict) -> str:
    from datetime import datetime

    from app.schemas.bazi import BaziFullRequest
    from services.bazi_full_service import bazi_full

    gender = _gender_label(case)
    body = BaziFullRequest(
        dt=datetime(
            case["birth_year"],
            case["birth_month"],
            case["birth_day"],
            case["birth_hour"],
            case.get("birth_minute", 0),
        ),
        lon=case.get("longitude", 121.47),
        gender="female" if gender == "女" else "male",
        tz="Asia/Shanghai",
        mode="dual",
    )
    resp = bazi_full(body)
    pillars = resp.pillars_primary
    return " ".join(
        f"{p.stem}{p.branch}"
        for p in (pillars.year, pillars.month, pillars.day, pillars.hour)
    )


def build_bazi_diff_report() -> dict:
    if not CASES_PATH.exists():
        return {"available": False, "reason": "wenmo_reference_cases.json missing", "cases": []}
    data = json.loads(CASES_PATH.read_text(encoding="utf-8"))
    rows = []
    for case in data.get("cases", []):
        wm_pillars = case.get("pillars")
        eng_pillars = _engine_bazi_pillars(case) if wm_pillars else None
        rows.append(
            {
                "id": case.get("id"),
                "wenmo_pillars": wm_pillars,
                "engine_pillars": eng_pillars,
                "pillars_match": wm_pillars == eng_pillars if wm_pillars and eng_pillars else None,
                "trust_level": "advisory",
            }
        )
    return {
        "available": True,
        "trust_level": "advisory",
        "note": "Bazi pillar diffs are advisory; engine canonical for product.",
        "count": len(rows),
        "cases": rows,
    }


def build_diff_report() -> dict:
    if not CASES_PATH.exists():
        return {"available": False, "reason": "wenmo_reference_cases.json missing", "cases": []}
    data = json.loads(CASES_PATH.read_text(encoding="utf-8"))
    rows = []
    for case in data.get("cases", []):
        wm_life = case.get("life_palace_gz") or case.get("recorded_life_palace_gz")
        eng_life = _engine_life_palace(case)
        rows.append(
            {
                "id": case.get("id"),
                "wenmo_life_palace_gz": wm_life,
                "engine_life_palace_gz": eng_life,
                "life_palace_match": wm_life == eng_life if wm_life else None,
                "trust_level": "advisory",
            }
        )
    return {
        "available": True,
        "trust_level": "advisory",
        "count": len(rows),
        "cases": rows,
    }


def build_horoscope_diff_report() -> dict:
    if not CASES_PATH.exists():
        return {"available": False, "reason": "wenmo_reference_cases.json missing", "cases": []}

    data = json.loads(CASES_PATH.read_text(encoding="utf-8"))
    case_rows = []
    for case in data.get("cases", []):
        chart = _engine_chart(case)
        engine_by_age: dict[tuple[int, int], dict] = {}
        for item in chart.dayun.items:
            engine_by_age[(item.start_age, item.end_age)] = {
                "ganzhi": item.ganzhi,
                "palace_name": _palace_for_branch(chart, item.branch_idx),
                "branch_idx": item.branch_idx,
            }

        palace_rows = []
        for palace in case.get("palaces", []):
            parsed = _parse_dayun_range(palace.get("dayun_range"))
            if not parsed:
                continue
            start_age, end_age = parsed
            engine = engine_by_age.get((start_age, end_age))
            engine_palace = engine["palace_name"] if engine else None
            wenmo_palace = palace.get("palace")
            palace_rows.append(
                {
                    "wenmo_palace": wenmo_palace,
                    "wenmo_branch": palace.get("branch"),
                    "wenmo_range": palace.get("dayun_range"),
                    "start_age": start_age,
                    "end_age": end_age,
                    "engine_ganzhi": engine["ganzhi"] if engine else None,
                    "engine_palace": engine_palace,
                    "palace_match": engine_palace == wenmo_palace if engine_palace and wenmo_palace else None,
                    "age_range_match": engine is not None,
                }
            )

        age_matches = sum(1 for row in palace_rows if row["age_range_match"])
        palace_matches = sum(1 for row in palace_rows if row["palace_match"] is True)
        case_rows.append(
            {
                "id": case.get("id"),
                "trust_level": "advisory",
                "dayun_ranges_found": len(palace_rows),
                "age_range_matches": age_matches,
                "palace_name_matches": palace_matches,
                "palaces": palace_rows,
            }
        )

    return {
        "available": True,
        "trust_level": "advisory",
        "note": "Palace overlay diffs are advisory; age-range agreement is primary signal.",
        "count": len(case_rows),
        "cases": case_rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Wenmo vs engine advisory diff")
    parser.add_argument("--write", action="store_true", help="Write JSON report")
    parser.add_argument("--horoscope", action="store_true", help="Compare wenmo palace dayun_range vs engine")
    parser.add_argument("--bazi", action="store_true", help="Compare wenmo bazi pillars vs engine")
    args = parser.parse_args()
    if args.horoscope:
        report = build_horoscope_diff_report()
        out_path = HOROSCOPE_OUT_PATH
    elif args.bazi:
        report = build_bazi_diff_report()
        out_path = BAZI_OUT_PATH
    else:
        report = build_diff_report()
        out_path = LIFE_OUT_PATH
    if args.write:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Wrote {out_path}")
    else:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
