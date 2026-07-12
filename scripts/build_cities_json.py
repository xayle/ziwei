#!/usr/bin/env python3
"""从 git 历史 CityPicker 提取城市列表，合并公开坐标数据，生成 data/cities.json。"""

from __future__ import annotations

import json
import re
import subprocess
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "cities.json"
GIT_COMMIT = "d9e68fa:frontend/src/components/CityPicker.vue"
GEO_URL = (
    "https://raw.githubusercontent.com/zhuyf8899/China_City_Geolocation_List/"
    "master/city_geo_list_utf8.json"
)

DIRECT = {"北京", "上海", "天津", "重庆"}
SPECIAL = {"大连", "宁波", "青岛", "厦门", "深圳"}
CAPITALS = {
    "石家庄", "太原", "呼和浩特", "沈阳", "长春", "哈尔滨",
    "南京", "杭州", "合肥", "福州", "南昌", "济南",
    "郑州", "武汉", "长沙", "广州", "南宁", "海口",
    "成都", "贵阳", "昆明", "拉萨", "西安", "兰州",
    "西宁", "银川", "乌鲁木齐",
}

NAME_FIX = {"揭州": "揭阳"}

# 上游坐标库已知错误条目（lng, lat）
MANUAL_COORDS: dict[str, tuple[float, float]] = {
    "大同": (113.30, 40.08),
    "中山": (113.38, 22.52),
    "甘南": (102.91, 34.99),
    "新北": (121.47, 31.84),
}

# 省份纬度合理区间（用于校验）
PROVINCE_LAT_RANGE: dict[str, tuple[float, float]] = {
    "北京市": (39.4, 41.1),
    "天津市": (38.6, 40.3),
    "上海市": (30.7, 31.9),
    "重庆市": (28.1, 32.5),
    "河北省": (36.0, 42.6),
    "山西省": (34.3, 40.8),
    "内蒙古自治区": (37.4, 53.3),
    "辽宁省": (38.7, 43.5),
    "吉林省": (41.4, 46.3),
    "黑龙江省": (43.4, 53.6),
    "江苏省": (30.7, 35.1),
    "浙江省": (27.1, 31.2),
    "安徽省": (29.4, 34.7),
    "福建省": (23.5, 28.4),
    "江西省": (24.5, 30.1),
    "山东省": (34.4, 38.4),
    "河南省": (31.4, 36.4),
    "湖北省": (29.0, 33.3),
    "湖南省": (24.6, 30.1),
    "广东省": (20.2, 25.5),
    "广西壮族自治区": (20.9, 26.4),
    "海南省": (18.1, 20.2),
    "四川省": (26.0, 34.3),
    "贵州省": (24.6, 29.2),
    "云南省": (21.1, 29.2),
    "西藏自治区": (26.8, 36.5),
    "陕西省": (31.7, 39.6),
    "甘肃省": (32.6, 42.8),
    "青海省": (31.6, 39.2),
    "宁夏回族自治区": (35.2, 39.5),
    "新疆维吾尔自治区": (34.3, 49.2),
}


def fetch_geo() -> dict[str, dict[str, float]]:
    with urllib.request.urlopen(GEO_URL, timeout=30) as resp:
        raw = resp.read().decode("utf-8")
    raw = re.sub(r",\s*}", "}", raw)
    return json.loads(raw)


def extract_citypicker() -> list[tuple[str, str, float]]:
    text = subprocess.check_output(
        ["git", "show", GIT_COMMIT],
        cwd=ROOT,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    pat = re.compile(r"\{ name: '([^']+)',\s*province: '([^']+)',\s*lng:\s*([0-9.]+) \}")
    return [(n, p, float(lng)) for n, p, lng in pat.findall(text)]


def classify(name: str) -> str:
    if name in DIRECT:
        return "直辖市"
    if name in SPECIAL:
        return "计划单列市"
    if name in CAPITALS:
        return "省会"
    return "地级市"


def lookup_geo_entry(geo: dict, name: str) -> dict[str, float] | None:
    for key in (name, f"{name}市"):
        if key in geo:
            return geo[key]
    for key, val in geo.items():
        if key.replace("市", "") == name:
            return val
    return None


def province_lat_ok(province: str, lat: float) -> bool:
    bounds = PROVINCE_LAT_RANGE.get(province)
    if not bounds:
        return 18.0 <= lat <= 54.0
    return bounds[0] - 1.5 <= lat <= bounds[1] + 1.5


def resolve_coords(
    geo: dict,
    name: str,
    province: str,
    picker_lng: float,
) -> tuple[float, float]:
    if name in MANUAL_COORDS:
        lng, lat = MANUAL_COORDS[name]
        return round(lng, 2), round(lat, 2)

    entry = lookup_geo_entry(geo, name)
    if entry:
        geo_lng = float(entry["lng"])
        geo_lat = float(entry["lat"])
        # 经纬成对采纳：与省份纬度一致，且经度差不太大
        if province_lat_ok(province, geo_lat) and abs(geo_lng - picker_lng) <= 3.0:
            return round(geo_lng, 2), round(geo_lat, 2)
        if province_lat_ok(province, geo_lat):
            return round(picker_lng, 2), round(geo_lat, 2)

    # 仅纬度可用且合理
    if entry and province_lat_ok(province, float(entry["lat"])):
        return round(picker_lng, 2), round(float(entry["lat"]), 2)

    # 省级中心兜底
    bounds = PROVINCE_LAT_RANGE.get(province, (30.0, 40.0))
    fallback_lat = round((bounds[0] + bounds[1]) / 2, 2)
    return round(picker_lng, 2), fallback_lat


def validate_city(city: dict) -> list[str]:
    issues: list[str] = []
    lng, lat = city["lng"], city["lat"]
    if not (73.0 <= lng <= 136.0):
        issues.append(f"lng out of range: {lng}")
    if not (18.0 <= lat <= 54.0):
        issues.append(f"lat out of range: {lat}")
    if not province_lat_ok(city["province"], lat):
        issues.append(f"lat {lat} inconsistent with {city['province']}")
    return issues


def main() -> None:
    geo = fetch_geo()
    rows = extract_citypicker()
    seen: set[tuple[str, str]] = set()
    cities: list[dict] = []
    warnings: list[str] = []

    for raw_name, province, picker_lng in rows:
        name = NAME_FIX.get(raw_name, raw_name)
        key = (name, province)
        if key in seen:
            continue
        seen.add(key)

        lng, lat = resolve_coords(geo, name, province, picker_lng)
        city = {
            "name": name,
            "province": province,
            "lng": lng,
            "lat": lat,
            "city_type": classify(name),
        }
        issues = validate_city(city)
        if issues:
            warnings.append(f"{name}/{province}: {', '.join(issues)}")
        cities.append(city)

    order = {"直辖市": 0, "省会": 1, "计划单列市": 2, "地级市": 3}
    cities.sort(key=lambda c: (order[c["city_type"]], c["province"], c["name"]))

    OUT.write_text(json.dumps(cities, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {len(cities)} cities to {OUT}")
    if warnings:
        print(f"Warnings ({len(warnings)}):")
        for item in warnings[:20]:
            print(f"  - {item}")
        if len(warnings) > 20:
            print(f"  ... and {len(warnings) - 20} more")
        sys.exit(1)


if __name__ == "__main__":
    main()
