"""R060 steps 1-9 automation (step 10 subjective remains human)."""

from __future__ import annotations

import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "frontend"


def _playwright_chromium_installed() -> bool:
    roots = [
        Path.home() / ".cache" / "ms-playwright",
        FRONTEND / "node_modules" / "playwright-core" / ".local-browsers",
    ]
    alt = os.environ.get("PLAYWRIGHT_BROWSERS_PATH", "").strip()
    if alt:
        roots.append(Path(alt))
    for root in roots:
        if root.is_dir() and any(root.glob("chromium*")):
            return True
    return False


def _frontend_e2e_ready() -> bool:
    if os.environ.get("W14_SKIP_E2E", "").strip() in {"1", "true", "TRUE", "yes"}:
        return False
    if not (FRONTEND / "node_modules").is_dir():
        return False
    if not (shutil.which("npm") or shutil.which("npm.cmd")):
        return False
    # test job 常有 npm ci 但未 npx playwright install
    return _playwright_chromium_installed()


def main() -> int:
    if not _frontend_e2e_ready():
        print("SKIP: R060 trial-read E2E (npm/browsers unavailable or W14_SKIP_E2E)")
        return 0

    npm = "npm.cmd" if platform.system() == "Windows" else "npm"
    env = {**os.environ, "AUTOPILOT_E2E": "1", "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8"}
    proc = subprocess.run(
        [npm, "run", "test:e2e", "--", "fusheng-trial-read"],
        cwd=FRONTEND,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
    )
    ok = proc.returncode == 0
    tail = (proc.stdout or "")[-1500:]
    try:
        print(tail)
    except UnicodeEncodeError:
        print(tail.encode("ascii", errors="replace").decode("ascii"))
    if not ok and proc.stderr:
        err = proc.stderr[-500:]
        try:
            print(err, file=sys.stderr)
        except UnicodeEncodeError:
            print(err.encode("ascii", errors="replace").decode("ascii"), file=sys.stderr)
    print("PASS: R060 trial-read E2E 1/1" if ok else "FAIL: R060 trial-read E2E")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
