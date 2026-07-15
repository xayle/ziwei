#!/usr/bin/env python3
"""E-05 / T102：禁「改命 / 必中」等 GTM 违规文案扫描（产品路径）。

扫描前端源码、落地页常量、report disclaimer；典籍原文库除外。
退出码：0=无违规；1=发现命中。
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# 产品话术红线（BOOK-GTM §2.1）
FORBIDDEN = (
    "改命",
    "必中",
    "一百准",
    "化解法事",
)

# 明示合规否定句允许（如「勿以改命相称」）
ALLOW_PATTERNS = (
    re.compile(r"勿以[「\"']?改命"),
    re.compile(r"禁[「\"']?改命"),
    re.compile(r"严禁.{0,8}改命"),
    re.compile(r"禁止.{0,8}改命"),
)

SCAN_GLOBS = (
    "frontend/src/**/*.{vue,ts,tsx,js}",
    "docs/design/**/*.html",
)

EXCLUDE_PARTS = (
    "node_modules",
    "__tests__",
    ".spec.",
    "classics",
    "data/",
)


def _allowed(line: str, term: str) -> bool:
    if term != "改命":
        return False
    return any(p.search(line) for p in ALLOW_PATTERNS)


def scan(paths: list[Path]) -> list[tuple[str, int, str, str]]:
    hits: list[tuple[str, int, str, str]] = []
    for path in paths:
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        for i, line in enumerate(text.splitlines(), 1):
            for term in FORBIDDEN:
                if term in line and not _allowed(line, term):
                    hits.append((str(path.relative_to(ROOT)), i, term, line.strip()[:120]))
    return hits


def collect_files() -> list[Path]:
    out: list[Path] = []
    for pattern in ("frontend/src/**/*.vue", "frontend/src/**/*.ts", "docs/design/**/*.html"):
        for p in ROOT.glob(pattern):
            s = str(p).replace("\\", "/")
            if any(x in s for x in EXCLUDE_PARTS):
                continue
            out.append(p)
    return sorted(set(out))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()
    files = collect_files()
    hits = scan(files)
    if not args.quiet:
        print(f"扫描 {len(files)} 个文件；禁词：{', '.join(FORBIDDEN)}")
        if hits:
            for path, line, term, excerpt in hits:
                print(f"  FAIL {path}:{line} [{term}] {excerpt}")
        else:
            print("OK：产品路径未发现未豁免违规词")
    return 1 if hits else 0


if __name__ == "__main__":
    sys.exit(main())
