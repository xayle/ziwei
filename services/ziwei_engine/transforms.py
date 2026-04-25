"""
services/ziwei_engine/transforms.py — 四化表（化禄/化权/化科/化忌）

来源：《紫微斗数全书》十天干四化
支持多流派：standard（全书/台湾正统）及各天干可选替代方案

四化简称对照：
  廉破武阳 = 廉贞禄/破军权/武曲科/太阳忌
  贪阴右机 = 贪狼禄/太阴权/右弼科/天机忌  （戊干）
  阳武阴同 = 太阳禄/武曲权/太阴科/天同忌  （庚干标准）
  …以此类推
"""
from __future__ import annotations

# 四化类型
SIHUA_TYPES = ("禄", "权", "科", "忌")

# 辅助：通过天干索引（甲=0…癸=9）快速查表
STEMS = list("甲乙丙丁戊己庚辛壬癸")

# ─────────────────────────────────────────────────────────────────────────────
# 各天干可选方案列表（索引0=标准/默认；索引1,2,…=各流派替代）
# label 字段：显示名称（四字简称）
# ─────────────────────────────────────────────────────────────────────────────
SIHUA_STEM_OPTIONS: dict[str, list[dict]] = {
    "甲": [
        {"label": "廉破武阳", "禄": "廉贞", "权": "破军", "科": "武曲", "忌": "太阳"},   # 0 标准
        {"label": "廉破曲阳", "禄": "廉贞", "权": "破军", "科": "文曲", "忌": "太阳"},   # 1
    ],
    "乙": [
        {"label": "机梁紫阴", "禄": "天机", "权": "天梁", "科": "紫微", "忌": "太阴"},   # 0 仅一种
    ],
    "丙": [
        {"label": "同机昌廉", "禄": "天同", "权": "天机", "科": "文昌", "忌": "廉贞"},   # 0
    ],
    "丁": [
        {"label": "阴同机巨", "禄": "太阴", "权": "天同", "科": "天机", "忌": "巨门"},   # 0
    ],
    "戊": [
        {"label": "贪阴右机", "禄": "贪狼", "权": "太阴", "科": "右弼", "忌": "天机"},   # 0 标准
        {"label": "贪阴阳机", "禄": "贪狼", "权": "太阴", "科": "太阳", "忌": "天机"},   # 1
    ],
    "己": [
        {"label": "武贪梁曲", "禄": "武曲", "权": "贪狼", "科": "天梁", "忌": "文曲"},   # 0
    ],
    "庚": [
        {"label": "阳武阴同", "禄": "太阳", "权": "武曲", "科": "太阴", "忌": "天同"},   # 0 标准
        {"label": "阳武同阴", "禄": "太阳", "权": "武曲", "科": "天同", "忌": "太阴"},   # 1
        {"label": "阳武府同", "禄": "太阳", "权": "武曲", "科": "天府", "忌": "天同"},   # 2
        {"label": "阳武府相", "禄": "太阳", "权": "武曲", "科": "天府", "忌": "天相"},   # 3
        {"label": "阳武同相", "禄": "太阳", "权": "武曲", "科": "天同", "忌": "天相"},   # 4
    ],
    "辛": [
        {"label": "巨阳曲昌", "禄": "巨门", "权": "太阳", "科": "文曲", "忌": "文昌"},   # 0 标准
        {"label": "巨阳武昌", "禄": "巨门", "权": "太阳", "科": "武曲", "忌": "文昌"},   # 1
    ],
    "壬": [
        {"label": "梁紫辅武", "禄": "天梁", "权": "紫微", "科": "左辅", "忌": "武曲"},   # 0 标准
        {"label": "梁紫府武", "禄": "天梁", "权": "紫微", "科": "天府", "忌": "武曲"},   # 1
        {"label": "梁紫相武", "禄": "天梁", "权": "紫微", "科": "天相", "忌": "武曲"},   # 2
    ],
    "癸": [
        {"label": "破巨阴贪", "禄": "破军", "权": "巨门", "科": "太阴", "忌": "贪狼"},   # 0 标准
        {"label": "破巨阳贪", "禄": "破军", "权": "巨门", "科": "太阳", "忌": "贪狼"},   # 1
    ],
}

def build_sihua_table(
    stem_indices: "dict[str, int] | None" = None,
) -> dict[str, dict[str, str]]:
    """
    构建四化表，支持per-stem方案选择。

    参数 stem_indices: {天干名: 方案索引}，如 {"庚": 2, "壬": 1}
      - 缺省天干使用方案0（标准）
      - 索引越界时回退方案0
    返回构建好的 {天干: {化类型: 星名}} 映射。
    """
    overrides = stem_indices or {}
    table: dict[str, dict[str, str]] = {}
    for stem, options in SIHUA_STEM_OPTIONS.items():
        idx = overrides.get(stem, 0)
        if idx < 0 or idx >= len(options):
            idx = 0
        entry = options[idx]
        table[stem] = {k: entry[k] for k in ("禄", "权", "科", "忌")}
    return table


# 默认标准四化表（方案0）
SIHUA_TABLE: dict[str, dict[str, str]] = build_sihua_table()


def get_sihua_by_stem_idx(stem_idx: int) -> dict[str, str]:
    """根据天干索引返回标准四化映射。"""
    return SIHUA_TABLE[STEMS[stem_idx % 10]]


def apply_sihua(
    star_branches: dict[str, int],
    stem_name: str,
    sihua_table: "dict[str, dict[str, str]] | None" = None,
) -> dict[str, str]:
    """
    给定当前盘面主星位置字典和天干名，
    返回 {星名: 化xxx} 标注。

    star_branches: {"紫微": 4, "天机": 3, ...}
    stem_name: "壬" 等
    sihua_table: 自定义四化表（None=使用标准默认表）
    返回: {"紫微": "化权", "天梁": "化禄", ...}
    """
    tbl = sihua_table if sihua_table is not None else SIHUA_TABLE
    table = tbl.get(stem_name, {})
    result: dict[str, str] = {}
    for hua_type, star in table.items():
        if star in star_branches:
            result[star] = f"化{hua_type}"
    return result
