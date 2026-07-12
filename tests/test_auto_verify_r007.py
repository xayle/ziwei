"""Auto-verify R007 FE-BE decisions."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_r007_fe_be_decisions_resolved():
    proc = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "auto_verify_r007.py")],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
