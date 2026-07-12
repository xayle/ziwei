from __future__ import annotations

import argparse
import os
import shutil
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parent.parent
FRONTEND = ROOT / "frontend"


def _npm(*args: str) -> list[str]:
    npm = shutil.which("npm")
    if not npm:
        raise RuntimeError("npm not found in PATH")
    return [npm, *args]


def _run(command: list[str], cwd: Path) -> None:
    subprocess.run(command, cwd=cwd, check=True)


def run_backend_checks(*, with_scorecard: bool = False) -> None:
    _run([sys.executable, "-m", "pytest", "-q", "tests/test_entrypoint_contract.py"], ROOT)
    _run([sys.executable, "-m", "pytest", "-q", "tests/test_app_assembly.py", "tests/test_bootstrap.py", "tests/test_lifecycle.py"], ROOT)
    _run([sys.executable, "-m", "pytest", "-q", "tests/test_static_entrypoints.py"], ROOT)
    _run([sys.executable, "-m", "pytest", "-q", "tests/test_openapi_sync.py"], ROOT)
    if with_scorecard:
        _run([sys.executable, "scripts/audit_scorecard.py"], ROOT)


def run_frontend_checks() -> None:
    # Local dev: skip npm ci when node_modules exists (Windows file-lock EPERM).
    # CI always runs a clean install.
    if os.environ.get("CI") == "true" or not (FRONTEND / "node_modules").is_dir():
        _run(_npm("ci"), FRONTEND)
    _run(_npm("run", "type-check"), FRONTEND)
    _run(_npm("run", "lint"), FRONTEND)
    _run(_npm("run", "test"), FRONTEND)
    _run(_npm("run", "build"), FRONTEND)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run project quality gates.")
    parser.add_argument(
        "--section",
        choices=("all", "backend", "frontend"),
        default="all",
        help="Which gate section to run.",
    )
    parser.add_argument(
        "--with-scorecard",
        action="store_true",
        help="Also run audit_scorecard.py (24/24 regression gate).",
    )
    args = parser.parse_args()

    if args.section in ("all", "backend"):
        run_backend_checks(with_scorecard=args.with_scorecard)
    if args.section in ("all", "frontend"):
        run_frontend_checks()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
