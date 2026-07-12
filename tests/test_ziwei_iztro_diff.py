"""Optional iztro cross-check for ZW golden cases (CI: make verify-iztro)."""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "verify_ziwei_iztro.mjs"
IZTRO_DIR = ROOT / "scripts" / "iztro"
REPORT = ROOT / "docs" / "reports" / "ziwei-iztro-diff-latest.json"


def _iztro_ready() -> bool:
    return (IZTRO_DIR / "node_modules" / "iztro").exists()


@pytest.mark.skipif(not _iztro_ready(), reason="iztro not installed (make verify-iztro-install)")
def test_ziwei_iztro_diff_produces_report():
    """Advisory diff: records mismatches but does not block CI (流派/辅煞差异常见)."""
    proc = subprocess.run(
        ["node", str(SCRIPT)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert REPORT.exists(), proc.stderr or proc.stdout
    data = json.loads(REPORT.read_text(encoding="utf-8"))
    assert len(data.get("report", [])) >= 8
    # ZW01 主星应与 iztro 高度一致（允许 1–2 辅煞差异）
    zw01 = next(r for r in data["report"] if r["id"] == "ZW01")
    main_diffs = [m for m in zw01.get("mismatches", []) if m.startswith("主星")]
    assert zw01.get("mainMatch") == 14, f"ZW01 main match: {zw01.get('mainMatch')}"
    assert zw01.get("lpOk") is True
    assert len(main_diffs) == 0, f"ZW01 main star drift: {main_diffs}"
    # 脚本 exit 1 表示有 diff，但本测试只验证报告与 ZW01 主星
    assert proc.returncode in (0, 1)


@pytest.mark.skipif(not _iztro_ready(), reason="iztro not installed (make verify-iztro-install)")
def test_ziwei_iztro_hour_mode_aux_aligned():
    """R044: youbi_method=hour should align 右弼 with iztro (--youbi=hour)."""
    proc = subprocess.run(
        ["node", str(SCRIPT), "--youbi=hour"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=120,
        env={**dict(os.environ), "PYTHONIOENCODING": "utf-8"},
    )
    assert REPORT.exists(), proc.stderr or proc.stdout
    data = json.loads(REPORT.read_text(encoding="utf-8"))
    assert data.get("youbi_mode") == "hour"
    zw01 = next(r for r in data["report"] if r["id"] == "ZW01")
    assert zw01.get("auxOk") is True, zw01.get("mismatches")
    assert proc.returncode in (0, 1)
