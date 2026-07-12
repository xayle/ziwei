"""FE explain section IDs align with docs/contracts/explain-section-map.json."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAP_PATH = ROOT / "docs" / "contracts" / "explain-section-map.json"

# Keep in sync with frontend/src/constants/feBeContract.ts
REPORT_BAZI = {"geju", "relations", "domains", "summary"}
REPORT_ZIWEI = {"palaces", "fortune"}


def test_report_explain_sections_in_contract_map():
    data = json.loads(MAP_PATH.read_text(encoding="utf-8"))
    batch = data.get("batch_recommended", {})
    assert set(batch.get("report_page", [])) == REPORT_BAZI
    assert set(batch.get("report_page_ziwei", [])) == REPORT_ZIWEI
