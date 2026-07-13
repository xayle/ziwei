"""Optional horoscope cross-check (iztro + wenmo advisory)."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
IZTRO_SCRIPT = ROOT / "scripts" / "verify_ziwei_horoscope_iztro.mjs"
IZTRO_REPORT = ROOT / "docs" / "reports" / "ziwei-horoscope-iztro-diff-latest.json"
WENMO_SCRIPT = ROOT / "scripts" / "wenmo_engine_diff.py"
WENMO_REPORT = ROOT / "docs" / "reports" / "wenmo-horoscope-diff-latest.json"
IZTRO_DIR = ROOT / "scripts" / "iztro"


def _iztro_ready() -> bool:
    return (IZTRO_DIR / "node_modules" / "iztro").exists()


@pytest.mark.skipif(not _iztro_ready(), reason="iztro not installed (make verify-iztro-install)")
def test_ziwei_horoscope_iztro_produces_wm01_report():
    proc = subprocess.run(
        ["node", str(IZTRO_SCRIPT), "--case", "WM01"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=120,
    )
    assert proc.returncode == 0, proc.stderr or proc.stdout
    assert IZTRO_REPORT.exists()
    data = json.loads(IZTRO_REPORT.read_text(encoding="utf-8"))
    wm01 = next(r for r in data["report"] if r["id"] == "WM01")
    assert wm01["decadal_total"] >= 3
    assert len(wm01["engine_dayun_items"]) >= 5
    assert data["trust_level"] == "advisory"


def test_wenmo_bazi_diff_produces_report():
    proc = subprocess.run(
        [sys.executable, str(WENMO_SCRIPT), "--bazi", "--write"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=180,
    )
    assert proc.returncode == 0, proc.stderr or proc.stdout
    bazi_report = ROOT / "docs" / "reports" / "wenmo-bazi-diff-latest.json"
    assert bazi_report.exists()
    data = json.loads(bazi_report.read_text(encoding="utf-8"))
    assert data.get("count", 0) >= 1
    assert data["trust_level"] == "advisory"


def test_wenmo_horoscope_diff_produces_report():
    proc = subprocess.run(
        [sys.executable, str(WENMO_SCRIPT), "--horoscope", "--write"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=120,
    )
    assert proc.returncode == 0, proc.stderr or proc.stdout
    assert WENMO_REPORT.exists()
    data = json.loads(WENMO_REPORT.read_text(encoding="utf-8"))
    wm01 = next(c for c in data["cases"] if c["id"] == "WM01")
    assert wm01["dayun_ranges_found"] >= 5
    assert wm01["age_range_matches"] >= 5
    assert data["trust_level"] == "advisory"
