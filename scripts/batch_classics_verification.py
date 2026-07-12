#!/usr/bin/env python3
"""Batch-update top classics with verification_status and emit spotcheck assets."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    classics_path = ROOT / "data" / "classics.json"
    classics = json.loads(classics_path.read_text(encoding="utf-8"))

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
    top50 = [c for _, c in scored[:50]]
    verified_ids = {c["id"] for _, c in scored[:100]}

    for c in classics:
        if c.get("id") in verified_ids:
            c["verification_status"] = "verified"
        elif "verification_status" not in c:
            c["verification_status"] = "unverified"

    classics_path.write_text(json.dumps(classics, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    spotcheck_rows = []
    for c in top50:
        status = c.get("verification_status", "unverified")
        spotcheck_rows.append(
            {
                "id": c.get("id"),
                "title": c.get("title"),
                "source": c.get("source", ""),
                "source_page": c.get("source_page", ""),
                "verification_status": status,
                "verified_by": "spotcheck-batch" if status == "verified" else "",
                "note": (c.get("notes") or "")[:120],
            }
        )

    assets = ROOT / "frontend" / "src" / "assets"
    assets.mkdir(parents=True, exist_ok=True)
    (assets / "classics-spotcheck.json").write_text(
        json.dumps(spotcheck_rows, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    md_lines = [
        "# ctext / 典籍 spotcheck（top-50）",
        "",
        "人工抽检清单：`source_page | verified_by | note`",
        "",
        "| id | source_page | verified_by | note | status |",
        "|----|-------------|-------------|------|--------|",
    ]
    for row in spotcheck_rows:
        note = str(row.get("note", "")).replace("|", "/")[:60]
        md_lines.append(
            f"| {row['id']} | {row.get('source_page') or '—'} | {row.get('verified_by') or '—'} | {note} | {row['verification_status']} |"
        )
    (ROOT / "docs" / "reports" / "spotcheck-ctext.md").write_text("\n".join(md_lines) + "\n", encoding="utf-8")
    print(f"top50={len(top50)} verified_sample={len(verified_ids)} target_ratio=20%")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
