"""Explain section map contract tests."""

from __future__ import annotations

import json
from pathlib import Path

from services.explain_bazi import BAZI_SECTIONS
from services.explain_ziwei import ZIWEI_SECTIONS

ROOT = Path(__file__).resolve().parents[1]
MAP_PATH = ROOT / "docs" / "contracts" / "explain-section-map.json"


def test_explain_section_map_loads():
    data = json.loads(MAP_PATH.read_text(encoding="utf-8"))
    assert data["version"] == "1.0"
    assert "bazi" in data and "ziwei" in data


def test_bazi_map_keys_match_service():
    data = json.loads(MAP_PATH.read_text(encoding="utf-8"))
    mapped = set(data["bazi"].keys())
    assert BAZI_SECTIONS.issubset(mapped)


def test_ziwei_map_keys_match_service():
    data = json.loads(MAP_PATH.read_text(encoding="utf-8"))
    mapped = set(data["ziwei"].keys())
    assert ZIWEI_SECTIONS.issubset(mapped)


def test_report_batch_recommended_within_limit():
    data = json.loads(MAP_PATH.read_text(encoding="utf-8"))
    bazi = data["batch_recommended"]["report_page"]
    ziwei = data["batch_recommended"]["report_page_ziwei"]
    assert len(bazi) <= 4
    assert len(ziwei) <= 4
