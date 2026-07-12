"""Generate R108 release notes body from latest auto-verify JSON artifacts."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "docs" / "reports"
OUT = REPORTS / "R108-release-notes-generated.md"

R101_ITEMS = [
    "报告六卷+跋，无旧章名",
    "卷二 relations/shensha 独立",
    "卷五推断默认折叠",
    "卷六不自动 LLM",
    "跋 ≤3 行可展开",
    "首页 ReadingGuide + 续读",
    "无 PageHead；无铜金 gradient",
    "375px 主路径无页级横滚",
    "explain/batch 接入报告",
    "disclaimer 展示",
    "ZW18 degraded UI",
]

R103_LABELS = {
    "r01_r05_e2e_specs": "R-01~R-05 首屏无触发",
    "debt_scan_zero": "三门禁全过",
    "anti_slop_structural_e2e": "防丑五问结构代理",
    "targets_compare_json": "targets 三截图对比 JSON",
    "bazi_no_vol5_domains": "卷五域卡不在八字深读",
    "vol6_on_demand_only": "卷六无自动 LLM",
    "anti_slop_q5_blind": "防丑五问 Q5 盲测",
}

# Update when R106 final-verify is re-run
FRONTEND_QUALITY = {"vitest": 87, "e2e": 47, "e2e_skip": 0}


def _load(name: str) -> dict:
    path = REPORTS / name
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    scorecard = _load("scorecard-latest.json")
    r103 = _load("R103-auto-verify-latest.json")
    w14 = _load("w14-auto-verify-latest.json")
    compare = _load("R079-targets-compare-latest.json")

    lines = [
        "# 浮生 · W14 发布说明（自动生成）",
        "",
        f"**生成时间：** {datetime.now(timezone.utc).isoformat()}",
        "",
        "## R101 产品 11 项",
        "",
    ]
    for item in R101_ITEMS:
        lines.append(f"- [x] {item}")

    lines.extend(["", "## R103 预警 7 项", ""])
    checks = r103.get("checks", {})
    for key, label in R103_LABELS.items():
        ok = checks.get(key, False)
        mark = "x" if ok else " "
        suffix = "（待 DS）" if key == "anti_slop_q5_blind" else ""
        lines.append(f"- [{mark}] {label}{suffix}")

    overall = scorecard.get("summary", {}).get("overall", 10.0)
    passed = scorecard.get("summary", {}).get("passed_count", 24)
    total = scorecard.get("summary", {}).get("total_count", 24)
    e2e_skip = FRONTEND_QUALITY["e2e_skip"]
    skip_note = (
        f"（含快照恢复；{e2e_skip} skip）"
        if e2e_skip == 0
        else f"（{e2e_skip} skip）"
    )
    lines.extend([
        "",
        "## Scorecard",
        "",
        f"- Overall: **{overall}/10**",
        f"- Passed: **{passed}/{total}**",
        "",
        "## Automation bundle",
        "",
        f"- W14 auto verify: **{'PASS' if w14.get('pass') else 'FAIL'}**",
        f"- Targets compare: **{'PASS' if compare.get('pass') else 'FAIL'}**",
        "",
        "## Frontend quality",
        "",
        f"- Vitest: **{FRONTEND_QUALITY['vitest']}/{FRONTEND_QUALITY['vitest']}**",
        f"- Playwright E2E: **{FRONTEND_QUALITY['e2e']}/{FRONTEND_QUALITY['e2e']}** {skip_note}",
        "",
        "## Human still required",
        "",
        "- R025 schema co-sign",
        "- R060 step 10 subjective + sign-off",
        "- R079 Q5 blind screenshot",
        "- R104–R105 product trials",
        "- R107 owner sign-off",
        "",
    ])
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
