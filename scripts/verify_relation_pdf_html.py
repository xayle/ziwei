"""R086 T123 — relation-compat PDF HTML structure gate (CI advisory)."""

from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = ROOT / "docs" / "reports" / "relation-pdf-html-check-latest.json"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

_REQUIRED_MARKERS = (
    "relation-compat@1.0",
    "维度评分",
    "格物",
    "双引擎",
    "行动建议",
)

_COUPLE_SAMPLE = {
    "relation_type": "couple",
    "person_a": {
        "birth_datetime": "1990-07-17T12:25:00",
        "tz": "Asia/Shanghai",
        "longitude": 117.18,
        "gender": "female",
        "label": "刘博",
    },
    "person_b": {
        "birth_datetime": "1990-06-17T20:15:00",
        "tz": "Asia/Shanghai",
        "longitude": 117.49,
        "gender": "male",
        "label": "程安东",
    },
    "options": {"include_bazi": True, "include_ziwei": True, "liunian_year": 2026},
}


def verify_relation_pdf_html() -> tuple[bool, dict]:
    from services.relation_engine.composer import compute_relation_full
    from services.relation_pdf_service import render_relation_compat_html

    result = compute_relation_full(
        relation_type=_COUPLE_SAMPLE["relation_type"],
        person_a=_COUPLE_SAMPLE["person_a"],
        person_b=_COUPLE_SAMPLE["person_b"],
        options=_COUPLE_SAMPLE["options"],
    )
    html = render_relation_compat_html(result)
    missing = [m for m in _REQUIRED_MARKERS if m not in html]
    cite_sections = (result.get("layers") or {}).get("cite", {}).get("sections") or []
    has_cite_layer = bool(cite_sections)
    if has_cite_layer and "引经" not in html and "典籍引证" not in html:
        missing.append("cite-section-in-pdf")

    ok = not missing
    report = {
        "checked_at": datetime.now(UTC).isoformat(),
        "schema_version": result.get("schema_version"),
        "combined_score": result.get("combined_score"),
        "has_cite_layer": has_cite_layer,
        "html_length": len(html),
        "missing_markers": missing,
        "status": "pass" if ok else "fail",
    }
    return ok, report


def main() -> int:
    ok, report = verify_relation_pdf_html()
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    if ok:
        print(f"PASS: relation PDF HTML gate — report {REPORT_PATH.relative_to(ROOT)}")
        return 0
    print("FAIL: relation PDF HTML missing markers:")
    for item in report["missing_markers"]:
        print(f"  - {item}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
