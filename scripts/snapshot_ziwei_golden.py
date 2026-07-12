#!/usr/bin/env python3
"""Refresh main_stars / aux_stars in ziwei_ground_truth.json from live engine."""
from __future__ import annotations

import json
from pathlib import Path

from services.ziwei_engine import ziwei_full

ROOT = Path(__file__).resolve().parents[1]
GT_PATH = ROOT / "data" / "ziwei_ground_truth.json"
BRANCHES = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
MAIN_STARS = [
    "紫微", "天机", "太阳", "武曲", "天同", "廉贞", "天府", "太阴",
    "贪狼", "巨门", "天相", "天梁", "七杀", "破军",
]
AUX_STARS = ["文昌", "文曲", "左辅", "右弼", "擎羊", "陀罗"]
EXTENDED_AUX = ["天魁", "天钺", "火星", "铃星"]


def _positions(chart) -> tuple[dict[str, str], dict[str, str], dict[str, str]]:
    main: dict[str, str] = {}
    aux: dict[str, str] = {}
    ext: dict[str, str] = {}
    for p in chart.palaces:
        br = BRANCHES[p.branch_idx]
        for s in p.main_stars:
            name = s["name"] if isinstance(s, dict) else s.name
            if name in MAIN_STARS:
                main[name] = br
        for s in p.aux_stars:
            name = s["name"] if isinstance(s, dict) else s.name
            if name in AUX_STARS:
                aux[name] = br
            if name in EXTENDED_AUX:
                ext[name] = br
    return main, aux, ext


def main() -> int:
    data = json.loads(GT_PATH.read_text(encoding="utf-8"))
    for case in data.get("cases", []):
        b = case["birth"]
        chart = ziwei_full(
            b["year"], b["month"], b["day"], b["hour"], b["minute"], b["gender"]
        )
        main, aux, ext = _positions(chart)
        case["main_stars"] = main
        case["aux_stars"] = aux
        case["extended_aux"] = ext
        case["life_palace_gz"] = chart.life_palace_gz
        case["body_palace_gz"] = chart.body_palace_gz
        case["wuxing_ju_name"] = chart.wuxing_ju_name
        if case.get("id") != "ZW01" and not case.get("verified"):
            case["verification_method"] = "engine_snapshot"
            case.setdefault("notes", "引擎坐标快照；建议 iztro 交叉核验")
    GT_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Refreshed {len(data.get('cases', []))} cases from engine")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
