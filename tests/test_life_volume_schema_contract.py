"""Life-volume schema contract (R025 co-sign automation)."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "docs" / "contracts" / "life-volume.schema.json"


def _load_schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def test_schema_requires_core_fields():
    schema = _load_schema()
    required = set(schema["required"])
    assert "schema_version" in required
    assert "volumes" in required
    assert "colophon" in required
    assert "content_versions" in required


def test_colophon_def_includes_wenmo_advisory():
    schema = _load_schema()
    props = schema["$defs"]["Colophon"]["properties"]
    assert "wenmo_advisory" in props
    assert "summary_lines" in props


def test_minimal_fixture_matches_contract_shape():
    """Minimal document satisfies required keys and colophon ≤3 lines."""
    fixture = {
        "schema_version": "life-volume@1.0",
        "case_id": "case-contract",
        "chart_hash": "hash-contract",
        "content_versions": {"classics": "classics.json"},
        "disclaimer_block": {
            "text": "仅供文化研究",
            "version": "2026-07-12",
            "jurisdiction": "CN",
        },
        "volumes": [
            {"id": vid, "title": vid, "locked": False, "sections": []}
            for vid in (
                "preface",
                "vol1",
                "vol2",
                "vol3",
                "vol4",
                "vol5",
                "vol6",
                "colophon",
            )
        ],
        "colophon": {
            "summary_lines": ["引擎 bazi+ziwei", "字段齐备"],
            "expandable": True,
            "wenmo_advisory": "文墨对照轨",
        },
    }
    schema = _load_schema()
    for key in schema["required"]:
        assert key in fixture, f"missing required key: {key}"
    assert len(fixture["colophon"]["summary_lines"]) <= 3
    assert len(fixture["volumes"]) == 8
