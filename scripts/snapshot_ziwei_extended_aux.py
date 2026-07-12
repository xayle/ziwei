#!/usr/bin/env python3
"""Snapshot extended aux stars (魁钺火铃) into ziwei_ground_truth.json from engine."""
from __future__ import annotations

import json
from pathlib import Path

from services.ziwei_engine import ziwei_full

ROOT = Path(__file__).resolve().parents[1]
GT_PATH = ROOT / "data" / "ziwei_ground_truth.json"
BRANCHES = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
EXTENDED_AUX = ["天魁", "天钺", "火星", "铃星"]


def _aux_positions(chart) -> dict[str, str]:
    out: dict[str, str] = {}
    for p in chart.palaces:
        br = BRANCHES[p.branch_idx]
        for s in p.aux_stars:
            name = s["name"] if isinstance(s, dict) else s.name
            if name in EXTENDED_AUX:
                out[name] = br
    return out


def main() -> int:
    data = json.loads(GT_PATH.read_text(encoding="utf-8"))
    for case in data.get("cases", []):
        b = case["birth"]
        chart = ziwei_full(
            b["year"], b["month"], b["day"], b["hour"], b["minute"], b["gender"]
        )
        case["extended_aux"] = _aux_positions(chart)
        if case.get("id") != "ZW01":
            case["verification_method"] = "engine_snapshot_extended_aux"
            case["verified"] = False
            case.setdefault(
                "notes",
                "引擎坐标+扩展辅煞快照；建议 iztro/人工复核后设 verified:true",
            )
    GT_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Updated {len(data.get('cases', []))} cases with extended_aux")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
