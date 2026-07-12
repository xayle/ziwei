"""R007 automation: FE-BE-DECISIONS Q1–Q20 all resolved."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs" / "plan" / "FE-BE-DECISIONS.md"


def main() -> int:
    text = DOC.read_text(encoding="utf-8")
    rows = re.findall(
        r"^\| Q(\d+) \| .+? \| (.+?) \| [^|]+ \|",
        text,
        flags=re.MULTILINE,
    )
    if len(rows) != 20:
        print(f"FAIL: expected 20 decision rows, found {len(rows)}")
        return 1
    for qid, decision in rows:
        if not decision.strip() or decision.strip() in {"—", "-", "TBD", "待定"}:
            print(f"FAIL: Q{qid} unresolved")
            return 1
    print("PASS: R007 — FE-BE-DECISIONS Q1–Q20 all resolved")
    return 0


if __name__ == "__main__":
    sys.exit(main())
