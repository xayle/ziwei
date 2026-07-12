"""古籍语料导入结果 sanity check（不访问网络）。"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CLASSICS = ROOT / "data" / "classics.json"
GT = ROOT / "data" / "ground_truth_cases.json"


def _load_classics() -> list[dict]:
    return json.loads(CLASSICS.read_text(encoding="utf-8"))


def test_classics_json_minimum_size():
    items = _load_classics()
    assert len(items) >= 480


def test_ditian_chapter_count():
    items = _load_classics()
    ditian = [x for x in items if x.get("id", "").startswith("daizhige.ditian.")]
    assert len(ditian) >= 60


def test_ziping_corpus_present():
    items = _load_classics()
    ziping = [
        x
        for x in items
        if "ziping" in x.get("id", "")
        or "子平" in x.get("title", "")
        or "ziping" in "".join(x.get("tags") or [])
    ]
    assert len(ziping) >= 40


def test_zip_cases_in_ground_truth():
    data = json.loads(GT.read_text(encoding="utf-8"))
    ids = {c["id"] for c in data["cases"]}
    for zip_id in ("ZIP07", "ZIP08", "ZIP09", "ZIP10", "ZIP11"):
        assert zip_id in ids, f"missing {zip_id} in ground_truth_cases.json"


def test_ditian_mingli_cases_extracted():
    items = _load_classics()
    cases = [x for x in items if x.get("id", "").startswith("daizhige.ditian.case.")]
    assert len(cases) >= 8
    assert any("从杀" in x.get("passage", "") or "从财" in x.get("passage", "") for x in cases)


def test_zip10_engine_cong_guansha():
    data = json.loads(GT.read_text(encoding="utf-8"))
    by_id = {c["id"]: c for c in data["cases"]}
    z10 = by_id["ZIP10"]
    assert z10["recorded_geju"] == "从官杀格"
    assert z10["engine_geju"] == "从官杀格"


def test_zip09_engine_drift_documented():
    data = json.loads(GT.read_text(encoding="utf-8"))
    by_id = {c["id"]: c for c in data["cases"]}
    z9 = by_id["ZIP09"]
    assert z9["recorded_geju"] == "从官杀格"
    assert z9["engine_geju"] == "七杀格"
    note = z9.get("recorded_geju_classical_note") or ""
    assert "比肩" in note or "七杀格" in note
