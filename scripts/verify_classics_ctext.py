#!/usr/bin/env python3
"""Verify classics / ziwei corpus ctext metadata (P2 gate, advisory)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main() -> int:
    classics_path = ROOT / "data" / "classics.json"
    classics_n = 0
    ctext_tag_n = 0
    verified_n = 0
    unverified_n = 0
    if classics_path.exists():
        classics = json.loads(classics_path.read_text(encoding="utf-8"))
        classics_n = len(classics)
        ctext_tag_n = sum(
            1
            for c in classics
            if "ctext" in (c.get("notes") or "").lower() or c.get("source_page")
        )
        verified_n = sum(1 for c in classics if c.get("verification_status") == "verified")
        unverified_n = sum(1 for c in classics if c.get("verification_status") == "unverified")

    from services.ziwei_classic_refs import catalog_self_check

    zw = catalog_self_check()
    ratio = (verified_n / classics_n) if classics_n else 0.0
    ok_classics = classics_n >= 480 and ctext_tag_n >= 40
    ok_ziwei = zw.get("ok", False)
    print(f"classics: {classics_n} entries, ctext-tagged: {ctext_tag_n}")
    print(f"verification_status: verified={verified_n} unverified={unverified_n} ratio={ratio:.1%}")
    print(f"ziwei_refs: {zw}")
    if ok_classics and ok_ziwei:
        print("verify_classics_ctext: OK (advisory)")
        if ratio < 0.05:
            print("advisory: verified ratio below 5% — expand spotcheck batch", file=sys.stderr)
        return 0
    print("verify_classics_ctext: FAIL", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
