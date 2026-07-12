"""双验档案 data/dual_verify_cases.json 与 GT 对齐率回归。"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_dual_verify_cases_file():
    path = ROOT / "data" / "dual_verify_cases.json"
    assert path.exists()
    data = json.loads(path.read_text(encoding="utf-8"))
    cases = data.get("cases", [])
    assert len(cases) >= 10
    ids = {c["id"] for c in cases}
    assert "DV01" in ids and "DV03" in ids and "DV05" in ids
    assert "DV06" in ids and "DV07" in ids and "DV08" in ids
    assert "DV09" in ids and "DV10" in ids


def test_gt_align_rate_at_least_95_percent():
    path = ROOT / "data" / "ground_truth_cases.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    cases = data.get("cases", data)
    keywords = ("双轨", "漂移", "引擎取", "古籍注")
    total = aligned = 0
    for c in cases:
        rec = c.get("recorded_geju")
        eng = c.get("engine_geju")
        if not (rec and eng):
            continue
        total += 1
        note = (c.get("recorded_geju_classical_note") or "") + (c.get("notes") or "")
        if rec == eng or any(k in note for k in keywords):
            aligned += 1
    assert total >= 40
    assert aligned / total >= 0.95, f"align {aligned}/{total}={aligned/total:.1%}"
