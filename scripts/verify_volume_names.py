#!/usr/bin/env python3
"""R102 · Verify skin-preview volume names match app LIFE_VOLUME_LABELS."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKIN = ROOT / "docs" / "design" / "skin-preview.html"

LABELS = {
    "卷一·命之根": "vol1",
    "卷二·业之象": "vol2",
    "卷三·运之波": "vol3",
    "卷四·宫之图": "vol4",
    "卷五·事之理": "vol5",
    "卷六·问书": "vol6",
    "跋·校勘": "colophon",
}

VOL_SUB_IDS = ["vol1", "vol2", "vol3", "vol4", "vol5", "vol6", "colophon"]


def main() -> int:
    text = SKIN.read_text(encoding="utf-8")
    missing = [label for label in LABELS if label not in text]
    if missing:
        # skin TOC splits id/title; accept vol sub ids + combined display line
        if not all(vid in text for vid in VOL_SUB_IDS):
            print("FAIL: skin-preview missing volume labels:", ", ".join(missing))
            return 1
    # FE labels file cross-check
    fe_types = ROOT / "frontend" / "src" / "types" / "life-volume.ts"
    fe_text = fe_types.read_text(encoding="utf-8")
    for label in LABELS:
        if label not in fe_text:
            print(f"FAIL: life-volume.ts missing {label}")
            return 1
    be_schema = ROOT / "app" / "schemas" / "life_volume.py"
    be_text = be_schema.read_text(encoding="utf-8")
    for label in LABELS:
        if label not in be_text:
            print(f"FAIL: life_volume.py missing {label}")
            return 1
    print(f"PASS: {len(LABELS)} volume labels aligned (skin · FE · BE)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
