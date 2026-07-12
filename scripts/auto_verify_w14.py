"""W14 automation bundle (R084 / R106). Runs verifiable checks and writes JSON summary."""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "reports" / "w14-auto-verify-latest.json"


def run(cmd: list[str], cwd: Path | None = None) -> dict:
    proc = subprocess.run(
        cmd,
        cwd=cwd or ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return {
        "cmd": " ".join(cmd),
        "exit_code": proc.returncode,
        "stdout_tail": proc.stdout[-2000:] if proc.stdout else "",
        "stderr_tail": proc.stderr[-1000:] if proc.stderr else "",
    }


def main() -> int:
    checks: list[dict] = []

    checks.append({"id": "scorecard", **run([sys.executable, "scripts/audit_scorecard.py"])})
    checks.append({"id": "quality_gate_backend", **run([sys.executable, "scripts/quality_gate.py", "--section", "backend", "--with-scorecard"])})
    checks.append({"id": "verify_volume_names", **run([sys.executable, "scripts/verify_volume_names.py"])})
    checks.append({"id": "r007_fe_be", **run([sys.executable, "scripts/auto_verify_r007.py"])})
    checks.append({"id": "r103_auto", **run([sys.executable, "scripts/auto_verify_r103.py"])})
    checks.append({"id": "r060_trial", **run([sys.executable, "scripts/auto_verify_r060.py"])})
    checks.append({
        "id": "pytest_w14_core",
        **run([
            sys.executable, "-m", "pytest", "-q",
            "tests/test_explain_batch.py",
            "tests/test_explain_section_map.py",
            "tests/test_zw18_trust.py",
            "tests/test_life_volume_schema_contract.py",
            "tests/test_life_volumes_api.py",
            "tests/test_import_desktop_content.py",
            "tests/test_openapi_sync.py",
            "tests/test_auto_verify_r007.py",
            "tests/test_auto_verify_r103.py",
            "tests/test_auto_verify_r060.py",
        ]),
    })

    passed = all(c["exit_code"] == 0 for c in checks)
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "pass": passed,
        "checks": checks,
    }
    OUT.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"pass": passed, "checks": [c["id"] for c in checks]}, ensure_ascii=False))
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
