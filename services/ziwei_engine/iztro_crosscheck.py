"""Optional iztro cross-check for live ziwei charts (subprocess to Node)."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "iztro_compare_birth.mjs"
IZTRO_DIR = ROOT / "scripts" / "iztro"


def iztro_available() -> bool:
    return (IZTRO_DIR / "node_modules" / "iztro").exists() and SCRIPT.is_file()


def compare_chart_to_iztro(
    *,
    year: int,
    month: int,
    day: int,
    hour: int,
    minute: int,
    gender: str,
    engine_main: dict[str, str],
    engine_life_palace_gz: str,
    year_divide: str = "lichun",
    day_divide: str = "solar_next",
) -> dict[str, Any] | None:
    """Return cross-check dict or None if iztro unavailable."""
    if not iztro_available():
        return None
    payload = {
        "year": year,
        "month": month,
        "day": day,
        "hour": hour,
        "minute": minute,
        "gender": gender,
        "engine_main": engine_main,
        "engine_life_palace_gz": engine_life_palace_gz,
        "year_divide": year_divide,
        "day_divide": day_divide,
    }
    try:
        proc = subprocess.run(
            ["node", str(SCRIPT)],
            input=json.dumps(payload, ensure_ascii=False),
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=30,
            check=False,
        )
        stdout = (proc.stdout or "").strip()
        if proc.returncode != 0 or not stdout:
            return None
        data = json.loads(stdout)
        if not data.get("available"):
            return None
        return data
    except (subprocess.TimeoutExpired, json.JSONDecodeError, OSError):
        return None
