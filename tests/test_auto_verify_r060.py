"""R060 trial-read E2E pytest wrapper."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_r060_trial_read_e2e():
    proc = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "auto_verify_r060.py")],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
