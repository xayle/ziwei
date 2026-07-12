#!/usr/bin/env python3
"""Manual spot-check helper for classics / CLS ctext page metadata (P2).

Outputs a CSV-style checklist for human verification against source books.
Run: python scripts/spotcheck_ctext_pages.py  (or make spotcheck-ctext)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "reports" / "ctext-spotcheck-latest.txt"
SPOTCHECK_MD = ROOT / "docs" / "reports" / "spotcheck-ctext.md"


def _load_classics() -> list[dict]:
    path = ROOT / "data" / "classics.json"
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


def _load_cls_cases() -> list[dict]:
    path = ROOT / "data" / "ground_truth_cases.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    cases = data.get("cases", data) if isinstance(data, dict) else data
    return [c for c in cases if c.get("pre_1900")]


def _top_classics(classics: list[dict], limit: int = 50) -> list[dict]:
    keywords = ("geju", "yongshen", "格局", "用神", "pattern", "overall", "strength")
    scored: list[tuple[int, dict]] = []
    for c in classics:
        tags = c.get("tags") or []
        text = " ".join([c.get("title", ""), c.get("passage", ""), " ".join(tags)])
        score = sum(1 for k in keywords if k in text.lower() or k in tags)
        if "geju" in tags or "yongshen" in tags or "格局" in text or "用神" in text:
            score += 3
        scored.append((score, c))
    scored.sort(key=lambda x: (-x[0], x[1].get("id", "")))
    return [c for _, c in scored[:limit]]


def main() -> int:
    classics = _load_classics()
    cls_cases = _load_cls_cases()
    top50 = _top_classics(classics, 50)

    ctext_classics = [
        c for c in classics
        if c.get("source_page") or "ctext" in (c.get("notes") or "").lower()
    ]
    sample_cls = [c for c in cls_cases if c.get("source_page")][:12]
    verified_top = sum(1 for c in top50 if c.get("verification_status") == "verified")

    lines = [
        "# ctext / CLS 页码人工抽检清单",
        f"# classics total: {len(classics)} | ctext-tagged: {len(ctext_classics)}",
        f"# top-50 template rows: {len(top50)} | verified sample: {verified_top}",
        f"# CLS pre_1900 with source_page: {sum(1 for c in cls_cases if c.get('source_page'))}",
        "",
        "## Top-50 classics (template rows)",
        "id\tsource\tsource_page\tverification_status\tverified_by\tnote_preview",
    ]
    for c in top50:
        notes = (c.get("notes") or "")[:60].replace("\n", " ")
        lines.append(
            f"{c.get('id', '—')}\t{c.get('source', '—')}\t{c.get('source_page', '—')}\t"
            f"{c.get('verification_status', 'unverified')}\t{c.get('verified_by', '—')}\t{notes}"
        )

    lines.extend(["", "## CLS sample (pre_1900)", "id\tsource_book\tsource_page\trecorded_geju"])
    for c in sample_cls:
        lines.append(
            f"{c.get('id')}\t{c.get('source_book', '—')}\t{c.get('source_page', '—')}\t{c.get('recorded_geju', '—')}"
        )

    lines.extend([
        "",
        "## Checklist",
        "[ ] 随机抽 5 条 classics source_page 与 ctext.org 章节一致",
        "[ ] 随机抽 3 条 CLS source_page 与原书页码/例号一致",
        "[ ] ZIP01/04/05 用神双轨 notes 与千里命稿一致",
        f"[x] top-50 模板行已生成（见 {SPOTCHECK_MD.name}）",
    ])

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {OUT}")
    print(f"top50 verified sample: {verified_top}/{len(top50)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
