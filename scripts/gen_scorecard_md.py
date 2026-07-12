#!/usr/bin/env python3
"""Generate docs/reports/SCORECARD-2026-11-28.md from audit_scorecard."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.audit_scorecard import build_scorecard

JSON_PATH = ROOT / "docs" / "reports" / "scorecard-latest.json"
MD_PATH = ROOT / "docs" / "reports" / "SCORECARD-2026-11-28.md"


def main() -> None:
    report = build_scorecard()
    JSON_PATH.parent.mkdir(parents=True, exist_ok=True)
    JSON_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    s = report["summary"]
    lines = [
        "# 9.5 Scorecard — Phase F 审计报告",
        "",
        "**日期**：2026-11-28  ",
        "**生成**：`python scripts/audit_scorecard.py`  ",
        "**JSON**：docs/reports/scorecard-latest.json",
        "",
        "---",
        "",
        "## 1. 总览",
        "",
        "| 指标 | 值 |",
        "|------|-----|",
        f"| Overall | **{s['overall']}** / 10 (target {report['target_score']}) |",
        f"| 八字均值 | {s['bazi_avg']} |",
        f"| 紫微均值 | {s['ziwei_avg']} |",
        f"| 交叉项均值 | {s['cross_avg']} |",
        f"| 达标项 | {s['passed_count']} / {s['total_count']} |",
        f"| GT 用例 | {s['gt_cases']} |",
        f"| ZW 用例 | {s['zw_cases']} |",
        f"| recorded==engine | {s['gt_align_rate']:.0%} |",
        f"| 核心 pytest | {'PASS' if s['pytest_core_ok'] else 'FAIL'} |",
        "",
        "---",
        "",
        "## 2. 24 项明细",
        "",
        "| ID | 名称 | 分数 | 达标 | 缺口 |",
        "|----|------|------|------|------|",
    ]
    for item in report["items"]:
        flag = "PASS" if item["passed"] else "FAIL"
        gaps = "; ".join(item.get("gaps") or []) or "-"
        lines.append(f"| {item['id']} | {item['name']} | {item['score']} | {flag} | {gaps} |")

    lines.extend(
        [
            "",
            "---",
            "",
            "## 3. Phase E–F 交付核对",
            "",
            "- [x] FushengZiweiPlate：四化图例 / 身宫 badge / 借星虚线",
            "- [x] `/new/ziwei/timeline` 路由与简化时间轴",
            "- [x] solarTime → ziwei longitude 条件传入",
            "- [x] 八字页：classic_ref / 用神主副盘 / 真太阳时与日界提示",
            "- [x] dual_verify_cases.json（3 人）",
            "- [x] PRODUCT.md 执业声明",
            "- [x] ZIP17–ZIP22 merge",
            "- [x] GT03/05/07/08 recorded 对齐 engine",
            "- [x] 本报告 + ziwei 项目总览修正",
            "",
        ]
    )
    MD_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {MD_PATH.relative_to(ROOT)}")
    print(f"Overall {s['overall']} passed {s['passed_count']}/{s['total_count']}")


if __name__ == "__main__":
    main()
