"""A45 — paper surface levels: no --surface-2 backgrounds inside fs-card Vue files."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FRONTEND_SRC = ROOT / "frontend" / "src"


def _style_block(text: str) -> str:
    m = re.search(r"<style[^>]*>([\s\S]*?)</style>", text)
    return m.group(1) if m else ""


def check_surface_levels() -> tuple[bool, list[str]]:
    violations: list[str] = []
    for path in FRONTEND_SRC.rglob("*.vue"):
        text = path.read_text(encoding="utf-8")
        if "fs-card" not in text:
            continue
        style = _style_block(text)
        if re.search(r"surface-2", style) and re.search(r"background\s*:", style):
            violations.append(f"{path.relative_to(ROOT)}: surface-2 background in fs-card page")
    return len(violations) == 0, violations


def main() -> int:
    ok, violations = check_surface_levels()
    if ok:
        print("PASS: A45 surface levels — no surface-2 inside fs-card styles")
        return 0
    print("FAIL: A45 surface violations:")
    for v in violations:
        print(f"  - {v}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
