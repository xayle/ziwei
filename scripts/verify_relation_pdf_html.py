"""R086 T123 — relation-compat PDF HTML structure gate (CI blocking)."""

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

_BIZ_SAMPLE = {
    "relation_type": "business_partner",
    "person_a": {
        "birth_datetime": "1985-11-20T09:00:00",
        "tz": "Asia/Shanghai",
        "longitude": 121.47,
        "gender": "male",
        "label": "合伙人A",
    },
    "person_b": {
        "birth_datetime": "1988-02-14T16:00:00",
        "tz": "Asia/Shanghai",
        "longitude": 114.05,
        "gender": "male",
        "label": "合伙人B",
    },
    "options": {"include_bazi": True, "include_ziwei": True},
}


def _check_type_sample(
    *,
    relation_type: str,
    person_a: dict,
    person_b: dict,
    options: dict,
    required_markers: tuple[str, ...],
    forbidden_in_html: list[str],
    required_in_html: list[str],
) -> tuple[bool, dict]:
    from services.relation_engine.composer import compute_relation_full
    from services.relation_pdf_service import render_relation_compat_html

    result = compute_relation_full(
        relation_type=relation_type,
        person_a=person_a,
        person_b=person_b,
        options=options,
    )
    html = render_relation_compat_html(result)
    missing = [m for m in required_markers if m not in html]
    leaked = [w for w in forbidden_in_html if w in html]
    absent = [w for w in required_in_html if w not in html]

    cite_sections = (result.get("layers") or {}).get("cite", {}).get("sections") or []
    has_cite_layer = bool(cite_sections)
    if has_cite_layer and "引经" not in html and "典籍引证" not in html:
        missing.append("cite-section-in-pdf")

    inference_heading = (result.get("meta") or {}).get("inference_heading") or ""
    if inference_heading and inference_heading not in html:
        missing.append(f"inference-heading:{inference_heading}")

    issues = missing + [f"forbidden:{w}" for w in leaked] + [f"required:{w}" for w in absent]
    ok = not issues
    return ok, {
        "relation_type": relation_type,
        "schema_version": result.get("schema_version"),
        "combined_score": result.get("combined_score"),
        "template_id": (result.get("meta") or {}).get("template_id"),
        "inference_heading": inference_heading,
        "has_cite_layer": has_cite_layer,
        "html_length": len(html),
        "issues": issues,
        "status": "pass" if ok else "fail",
    }


def verify_relation_pdf_html() -> tuple[bool, dict]:
    couple_ok, couple_report = _check_type_sample(
        relation_type=_COUPLE_SAMPLE["relation_type"],
        person_a=_COUPLE_SAMPLE["person_a"],
        person_b=_COUPLE_SAMPLE["person_b"],
        options=_COUPLE_SAMPLE["options"],
        required_markers=_REQUIRED_MARKERS + ("感情相处建议",),
        forbidden_in_html=["合伙", "契约", "股权", "分红"],
        required_in_html=[],
    )
    biz_ok, biz_report = _check_type_sample(
        relation_type=_BIZ_SAMPLE["relation_type"],
        person_a=_BIZ_SAMPLE["person_a"],
        person_b=_BIZ_SAMPLE["person_b"],
        options=_BIZ_SAMPLE["options"],
        required_markers=_REQUIRED_MARKERS + ("合作与风控建议", "template:business_partner"),
        forbidden_in_html=["感情保鲜", "婚嫁"],
        required_in_html=["契约", "合伙"],
    )
    ok = couple_ok and biz_ok
    report = {
        "checked_at": datetime.now(UTC).isoformat(),
        "status": "pass" if ok else "fail",
        "couple": couple_report,
        "business_partner": biz_report,
    }
    return ok, report


def main() -> int:
    ok, report = verify_relation_pdf_html()
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    if ok:
        print(f"PASS: relation PDF HTML gate — report {REPORT_PATH.relative_to(ROOT)}")
        return 0
    print("FAIL: relation PDF HTML gate:")
    for key in ("couple", "business_partner"):
        block = report.get(key) or {}
        for item in block.get("issues") or []:
            print(f"  [{key}] {item}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
