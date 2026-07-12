"""Tests for scripts/import_desktop_content.py outputs."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def test_wenmo_reference_cases_shape():
    path = ROOT / "data" / "imported" / "wenmo_reference_cases.json"
    assert path.exists(), "run scripts/import_desktop_content.py first"
    data = json.loads(path.read_text(encoding="utf-8"))
    cases = data["cases"]
    assert len(cases) >= 3
    for case in cases:
        assert case["id"].startswith("WM")
        assert case["trust_level"] == "advisory"
        assert case["life_palace_gz"]
        assert len(case["palaces"]) == 12
        ming = next(p for p in case["palaces"] if p["palace"] == "命宫")
        assert ming["branch"]


def test_star_profiles_has_major_stars():
    path = ROOT / "data" / "ziwei" / "star_profiles.json"
    assert path.exists()
    data = json.loads(path.read_text(encoding="utf-8"))
    keys = {s["key"] for s in data["stars"]}
    for star in ("紫微", "天机", "太阳", "武曲", "廉贞", "天府", "太阴", "贪狼"):
        assert star in keys


def test_glossary_has_ziwei_terms():
    glossary = json.loads((ROOT / "data" / "glossary.json").read_text(encoding="utf-8"))
    terms = {g["term"] for g in glossary}
    assert "紫微斗数" in terms
    assert "三方四正" in terms


def test_source_manifest_exists():
    path = ROOT / "data" / "imported" / "source_manifest.json"
    assert path.exists()
    manifest = json.loads(path.read_text(encoding="utf-8"))
    assert "sources" in manifest
    assert "文墨天机" in manifest["sources"]
