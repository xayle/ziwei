#!/usr/bin/env python3
"""Dev cycle: env + autopilot + content audit; optional git commit.

Writes docs/reports/dev-cycle-latest.json
Exit 0 when all *required* checks pass (product audit is advisory unless --strict-product).
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "docs" / "reports" / "dev-cycle-latest.json"
CONTENT_AUDIT = ROOT / "docs" / "reports" / "content-hollowness-audit-latest.json"

# Week4 targets (advisory)
THIN_TARGET = 0.35
VOL2_FALLBACK_TARGET = 0.0


def _run(cmd: list[str], *, cwd: Path | None = None) -> tuple[bool, str]:
    try:
        proc = subprocess.run(
            cmd,
            cwd=cwd or ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        out = (proc.stdout or "") + (proc.stderr or "")
        return proc.returncode == 0, out.strip()
    except OSError as exc:
        return False, str(exc)


def _section(name: str, cmd: list[str], *, required: bool = True) -> dict:
    ok, detail = _run(cmd)
    tail = detail[-2000:] if len(detail) > 2000 else detail
    return {
        "name": name,
        "command": " ".join(cmd),
        "ok": ok,
        "required": required,
        "detail_tail": tail,
    }


def _product_advisory() -> dict:
    if not CONTENT_AUDIT.is_file():
        return {"ok": False, "reason": "missing content-hollowness-audit-latest.json"}
    data = json.loads(CONTENT_AUDIT.read_text(encoding="utf-8"))
    volumes = data.get("volumes") or {}
    blocks = 0
    thin = 0
    for vol in volumes.values():
        n = int(vol.get("blocks") or 0)
        blocks += n
        thin += int(round((vol.get("thin_pct") or 0) * n / 100))
    thin_pct = (thin / blocks) if blocks else 1.0
    vol2 = volumes.get("vol2") or {}
    fallback_pct = float(vol2.get("fallback_pct") or 0) / 100.0
    ok = thin_pct <= THIN_TARGET and fallback_pct <= VOL2_FALLBACK_TARGET
    return {
        "ok": ok,
        "thin_pct": round(thin_pct, 4),
        "thin_target": THIN_TARGET,
        "vol2_fallback_pct": fallback_pct,
        "vol2_fallback_target": VOL2_FALLBACK_TARGET,
    }


def _git_commit(message: str, *, allow_advisory_fail: bool, advisory_ok: bool) -> dict:
    if not allow_advisory_fail and not advisory_ok:
        return {"ok": False, "detail": "product advisory fail; use --allow-advisory-commit or fix content"}
    status_ok, status_out = _run(["git", "status", "--porcelain"])
    if not status_ok:
        return {"ok": False, "detail": status_out}
    if not status_out.strip():
        return {"ok": True, "detail": "nothing to commit"}
    add_ok, add_out = _run(["git", "add", "-A"])
    if not add_ok:
        return {"ok": False, "detail": add_out}
    commit_ok, commit_out = _run(["git", "commit", "-m", message])
    return {"ok": commit_ok, "detail": commit_out}


def main() -> int:
    parser = argparse.ArgumentParser(description="Fusheng dev cycle: verify then optional commit")
    parser.add_argument("--commit", action="store_true", help="git commit after required checks pass")
    parser.add_argument("-m", "--message", default="", help="commit message (required with --commit)")
    parser.add_argument("--quick", action="store_true", help="skip full autopilot (env + audit-content only)")
    parser.add_argument(
        "--only",
        choices=("env", "autopilot", "audit-content"),
        help="run a single section",
    )
    parser.add_argument(
        "--strict-product",
        action="store_true",
        help="treat content audit thresholds as hard fail (exit 1)",
    )
    parser.add_argument(
        "--allow-advisory-commit",
        action="store_true",
        help="allow --commit when product advisory fails",
    )
    args = parser.parse_args()

    if args.commit and not args.message.strip():
        print("error: --commit requires -m/--message", file=sys.stderr)
        return 2

    sections: list[dict] = []
    py = sys.executable

    if args.only in (None, "env"):
        sections.append(_section("env", [py, "scripts/auto_verify_env.py"]))
    if args.only in (None, "autopilot") and not args.quick:
        sections.append(_section("autopilot", [py, "scripts/auto_verify_autopilot.py"]))
    if args.only in (None, "audit-content"):
        sections.append(
            _section(
                "audit-content",
                [py, "scripts/audit_content_hollowness.py"],
                required=False,
            )
        )

    advisory = _product_advisory()
    required_ok = all(s["ok"] for s in sections if s.get("required", True))
    commit_result = None
    if args.commit:
        commit_result = _git_commit(
            args.message.strip(),
            allow_advisory_fail=args.allow_advisory_commit,
            advisory_ok=advisory.get("ok", False),
        )
        if not commit_result["ok"]:
            required_ok = False

    payload = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "pass": required_ok,
        "quick": args.quick,
        "only": args.only,
        "sections": sections,
        "product_advisory": advisory,
        "commit": commit_result,
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(json.dumps({"pass": required_ok, "report": str(REPORT.relative_to(ROOT))}, ensure_ascii=False))

    if args.strict_product and not advisory.get("ok", False):
        return 1
    return 0 if required_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
