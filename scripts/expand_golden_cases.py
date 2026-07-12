#!/usr/bin/env python3
"""Append engine-verified GT/ZW/DV golden cases (BE-P1-04)."""
from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from services.bazi_engine_service import calculate
from services.ziwei_engine import ziwei_full

BRANCHES = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
MAIN_STARS = [
    "紫微", "天机", "太阳", "武曲", "天同", "廉贞", "天府", "太阴",
    "贪狼", "巨门", "天相", "天梁", "七杀", "破军",
]
AUX_STARS = ["文昌", "文曲", "左辅", "右弼", "擎羊", "陀罗"]
EXTENDED_AUX = ["天魁", "天钺", "火星", "铃星"]

GT_SPECS = [
    ("GT09", "1995-08-22T16:00:00", 116.4, "female", "夏末申时"),
    ("GT10", "1982-12-01T09:30:00", 121.5, "male", "冬月初巳时"),
    ("GT11", "2005-04-18T21:00:00", 113.3, "male", "春暮亥时"),
    ("GT12", "1978-09-09T11:00:00", 104.1, "female", "秋巳午时"),
]

ZW_SPECS = [
    ("ZW17", 1987, 7, 7, 11, 0, "男", "engine snapshot 1987-7-7"),
    ("ZW18", 1998, 1, 28, 8, 0, "女", "engine snapshot 1998-1-28"),
    ("ZW19", 2013, 9, 9, 14, 0, "女", "engine snapshot 2013-9-9"),
    ("ZW20", 1972, 5, 5, 6, 0, "女", "engine snapshot 1972-5-5"),
]

DV_SPECS = [
    (
        "DV09",
        "GT09 + ZW17 双验",
        "GT09",
        "ZW17",
        {"year": 1987, "month": 7, "day": 7, "hour": 11, "minute": 0, "gender": "男", "lon": 116.4, "tz": "Asia/Shanghai"},
        {"ziwei_life_palace_gz": None, "bazi_engine_geju": None},
    ),
    (
        "DV10",
        "GT10 + ZW18 双验",
        "GT10",
        "ZW18",
        {"year": 1998, "month": 1, "day": 28, "hour": 8, "minute": 0, "gender": "女", "lon": 121.5, "tz": "Asia/Shanghai"},
        {"ziwei_life_palace_gz": None, "bazi_engine_geju": None},
    ),
]


def _bazi_case(case_id: str, dt_s: str, lon: float, gender: str, note: str) -> dict:
    dt = datetime.fromisoformat(dt_s).replace(tzinfo=ZoneInfo("Asia/Shanghai"))
    vr = calculate(dt, lon, "Asia/Shanghai", use_solar=False, mode="single", gender=gender).verify_response
    pillars = vr.pillars_primary
    computed = {
        k: f"{getattr(getattr(pillars, k), 'stem', '')}{getattr(getattr(pillars, k), 'branch', '')}"
        for k in ("year", "month", "day", "hour")
    }
    geju = vr.geju.geju_name if vr.geju else ""
    favor = sorted(vr.yongshen.favor or []) if vr.yongshen else []
    return {
        "id": case_id,
        "description": f"BE-P1-04 Golden — {note}",
        "birth_calendar": "solar",
        "birth_year": dt.year,
        "birth_month": dt.month,
        "birth_day": dt.day,
        "birth_hour_range": f"{dt.hour}:00",
        "birth_dt_solar": dt_s,
        "longitude": lon,
        "gender": gender,
        "computed_pillars": computed,
        "recorded_geju": geju,
        "recorded_yongshen": favor,
        "source_type": "system",
        "source_book": "BACKEND-FOLLOWUP BE-P1-04 engine snapshot",
        "verified_pillars": True,
        "engine_geju": geju,
        "engine_yongshen_favor": favor,
        "verified_geju": True,
        "verified_yongshen": True,
        "notes": note,
    }


def _zw_positions(chart) -> tuple[dict[str, str], dict[str, str], dict[str, str]]:
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


def _zw_case(case_id: str, y: int, m: int, d: int, h: int, mi: int, gender: str, note: str) -> dict:
    chart = ziwei_full(y, m, d, h, mi, gender)
    main, aux, ext = _zw_positions(chart)
    return {
        "id": case_id,
        "birth": {"year": y, "month": m, "day": d, "hour": h, "minute": mi, "gender": gender},
        "life_palace_gz": chart.life_palace_gz,
        "body_palace_gz": chart.body_palace_gz,
        "wuxing_ju_name": chart.wuxing_ju_name,
        "main_stars": main,
        "aux_stars": aux,
        "extended_aux": ext,
        "verified": True,
        "verified_pillars": True,
        "notes": note,
        "verification_method": "engine_snapshot",
        "iztro_status": "pending",
    }


def _append_unique(path: Path, key: str, new_items: list[dict]) -> int:
    data = json.loads(path.read_text(encoding="utf-8"))
    cases: list[dict] = data.get(key, data if isinstance(data, list) else [])
    existing = {c["id"] for c in cases}
    added = 0
    for item in new_items:
        if item["id"] in existing:
            continue
        cases.append(item)
        existing.add(item["id"])
        added += 1
    if key in data:
        data[key] = cases
    else:
        data = cases
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return added


def main() -> int:
    gt_new = [_bazi_case(*spec) for spec in GT_SPECS]
    zw_new = [_zw_case(*spec) for spec in ZW_SPECS]

    zw_by_id = {c["id"]: c for c in zw_new}
    gt_by_id = {c["id"]: c for c in gt_new}
    dv_new: list[dict] = []
    for dv_id, label, gt_ref, zw_ref, birth, expect_tpl in DV_SPECS:
        zw = zw_by_id[zw_ref]
        gt = gt_by_id[gt_ref]
        expect = {
            "ziwei_life_palace_gz": zw["life_palace_gz"],
            "bazi_engine_geju": gt["engine_geju"],
        }
        dv_new.append(
            {
                "id": dv_id,
                "label": label,
                "bazi_ref": gt_ref,
                "ziwei_ref": zw_ref,
                "birth": birth,
                "expect": expect,
                "notes": "BE-P1-04 dual-verify expansion",
            }
        )

    gt_path = ROOT / "data" / "ground_truth_cases.json"
    zw_path = ROOT / "data" / "ziwei_ground_truth.json"
    dv_path = ROOT / "data" / "dual_verify_cases.json"

    gt_added = _append_unique(gt_path, "cases", gt_new)
    zw_added = _append_unique(zw_path, "cases", zw_new)
    dv_added = _append_unique(dv_path, "cases", dv_new)

    print(f"GT +{gt_added}  ZW +{zw_added}  DV +{dv_added}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
