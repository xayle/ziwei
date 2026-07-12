"""R002/R004 lightweight environment auto-check (non-blocking advisory)."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "frontend"
OUT = ROOT / "docs" / "reports" / "env-auto-verify-latest.json"


def _ok(cmd: list[str], *, cwd: Path | None = None) -> bool:
    try:
        subprocess.run(cmd, cwd=cwd or ROOT, check=True, capture_output=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def main() -> int:
    checks = {
        "python": shutil.which("python") is not None,
        "node": shutil.which("node") is not None,
        "npm": shutil.which("npm") is not None,
        "frontend_node_modules": (FRONTEND / "node_modules").exists(),
        "playwright_cli": (FRONTEND / "node_modules" / "@playwright" / "test").exists(),
        "vitest_bin": (FRONTEND / "node_modules" / "vitest").exists(),
        "requirements_txt": (ROOT / "requirements.txt").exists(),
    }

    passed = all(checks.values())
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "pass": passed,
        "checks": checks,
        "note": "R001/R003/R005/R006 remain human; this script covers R002/R004 machine checks only.",
    }
    OUT.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"pass": passed, "checks": checks}, ensure_ascii=False))
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
