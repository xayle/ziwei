#!/usr/bin/env python3
"""E-03：五书可验覆盖率报表（五书战役计划书 §7.1）。

用法:
  python scripts/report_five_classics_coverage.py
  python scripts/report_five_classics_coverage.py --json docs/reports/five-classics-coverage-latest.json
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CLASSICS = ROOT / "data" / "classics.json"
DEFAULT_JSON = ROOT / "docs" / "reports" / "five-classics-coverage-latest.json"

CANON = ("滴天髓", "子平真诠", "穷通宝鉴", "三命通会", "渊海子平")

# 计划书 §4 数字门禁
GATES: dict[str, int] = {
    "滴天髓": 80,
    "子平真诠": 45,
    "穷通宝鉴": 40,
    "三命通会": 30,
    "渊海子平": 20,
}
TOTAL_GATE = 215

# 类目 × 负责书（计划书 §3.2）
CATEGORY_OWNERS: dict[str, tuple[str, ...]] = {
    "C-格局": ("滴天髓", "子平真诠", "三命通会"),
    "C-用神": ("子平真诠", "三命通会"),
    "C-调候": ("穷通宝鉴", "三命通会"),
    "C-十神": ("子平真诠", "渊海子平", "三命通会"),
    "C-岁运": ("滴天髓", "渊海子平", "三命通会"),
    "C-神煞": ("渊海子平", "三命通会"),
    "C-日主": ("渊海子平", "三命通会", "滴天髓"),
}

CATEGORY_TAG_HINTS: dict[str, tuple[str, ...]] = {
    "C-格局": ("格局", "从象", "专旺", "正格"),
    "C-用神": ("用神", "取用"),
    "C-调候": ("调候", "寒", "暖", "燥", "湿", "季节", "月令"),
    "C-十神": ("十神", "正官", "七杀", "正印", "偏印", "财", "食神", "伤官"),
    "C-岁运": ("大运", "流年", "岁运"),
    "C-神煞": ("神煞", "空亡", "桃花", "驿马"),
    "C-日主": ("日主", "日干", "日支"),
}


def book_of(title: str | None) -> str | None:
    t = title or ""
    for b in CANON:
        if b in t:
            return b
    return None


def item_hits_category(item: dict, cat: str) -> bool:
    hints = CATEGORY_TAG_HINTS[cat]
    blob = " ".join(
        [
            str(item.get("title") or ""),
            str(item.get("passage") or "")[:200],
            " ".join(item.get("tags") or []),
        ]
    )
    return any(h in blob for h in hints)


def build_report(items: list[dict]) -> dict:
    by_book: dict[str, list[dict]] = defaultdict(list)
    for it in items:
        b = book_of(it.get("title"))
        if b:
            by_book[b].append(it)

    books = {}
    verified_total = 0
    for b in CANON:
        xs = by_book.get(b, [])
        v = sum(1 for x in xs if x.get("verification_status") == "verified")
        verified_total += v
        books[b] = {
            "total": len(xs),
            "verified": v,
            "unverified": sum(1 for x in xs if x.get("verification_status") != "verified"),
            "gate": GATES[b],
            "gate_met": v >= GATES[b],
            "deficit": max(0, GATES[b] - v),
        }

    matrix = {}
    for cat, owners in CATEGORY_OWNERS.items():
        cells = {}
        for b in owners:
            hit = any(
                item_hits_category(x, cat) and x.get("verification_status") == "verified"
                for x in by_book.get(b, [])
            )
            cells[b] = hit
        matrix[cat] = {
            "cells": cells,
            "complete": all(cells.values()),
        }

    return {
        "schema_version": "five-classics-coverage@1.0",
        "generated_at": datetime.now(UTC).isoformat(),
        "books": books,
        "verified_total_five": verified_total,
        "total_gate": TOTAL_GATE,
        "total_gate_met": verified_total >= TOTAL_GATE,
        "matrix": matrix,
        "matrix_complete": all(m["complete"] for m in matrix.values()),
        "milestones": {
            "M1_qiongtong": books["穷通宝鉴"]["gate_met"] and matrix["C-调候"]["cells"].get("穷通宝鉴", False),
            "M2_sanming_yuanhai": books["三命通会"]["gate_met"] and books["渊海子平"]["gate_met"],
            "M3_all_gates": verified_total >= TOTAL_GATE and all(m["complete"] for m in matrix.values())
            and all(books[b]["gate_met"] for b in CANON),
        },
    }


def render_text(report: dict) -> str:
    def box(ok: bool) -> str:
        return "[x]" if ok else "[ ]"

    lines = [
        f"五书覆盖率 · {report['generated_at']}",
        f"五书 verified 合计: {report['verified_total_five']} / 门禁 {report['total_gate']} → "
        f"{box(report['total_gate_met'])}",
        "",
        "书目:",
    ]
    for b, row in report["books"].items():
        lines.append(
            f"  {box(row['gate_met'])} {b}: verified={row['verified']} "
            f"(门禁 {row['gate']}, 差 {row['deficit']}) / total={row['total']}"
        )
    lines.append("")
    lines.append("类目矩阵（verified 命中）:")
    for cat, m in report["matrix"].items():
        cells = ", ".join(f"{k}:{'Y' if v else 'N'}" for k, v in m["cells"].items())
        lines.append(f"  {box(m['complete'])} {cat}: {cells}")
    lines.append("")
    ms = report["milestones"]
    lines.append(
        f"里程碑: M1={box(ms['M1_qiongtong'])} "
        f"M2={box(ms['M2_sanming_yuanhai'])} "
        f"M3={box(ms['M3_all_gates'])}"
    )
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", type=Path, default=DEFAULT_JSON)
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()
    items = json.loads(CLASSICS.read_text(encoding="utf-8"))
    report = build_report(items)
    args.json.parent.mkdir(parents=True, exist_ok=True)
    args.json.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    text = render_text(report)
    if not args.quiet:
        print(text)
        print(f"\nWrote {args.json}")
    return 0 if report["milestones"]["M3_all_gates"] else 1


if __name__ == "__main__":
    sys.exit(main())
