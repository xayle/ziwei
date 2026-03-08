"""
services/ziwei_engine/transforms.py — 四化表（化禄/化权/化科/化忌）

来源：《紫微斗数全书》十天干四化
经典版本（台湾正统）
"""
from __future__ import annotations

# 四化类型
SIHUA_TYPES = ("禄", "权", "科", "忌")

# 十天干四化表
# key = 天干名，value = {化类型: 星名}
SIHUA_TABLE: dict[str, dict[str, str]] = {
    "甲": {"禄": "廉贞", "权": "破军", "科": "武曲", "忌": "太阳"},
    "乙": {"禄": "天机", "权": "天梁", "科": "紫微", "忌": "太阴"},
    "丙": {"禄": "天同", "权": "天机", "科": "文昌", "忌": "廉贞"},
    "丁": {"禄": "太阴", "权": "天同", "科": "天机", "忌": "巨门"},
    "戊": {"禄": "贪狼", "权": "太阴", "科": "右弼", "忌": "天机"},
    "己": {"禄": "武曲", "权": "贪狼", "科": "天梁", "忌": "文曲"},
    "庚": {"禄": "太阳", "权": "武曲", "科": "太阴", "忌": "天同"},
    "辛": {"禄": "巨门", "权": "太阳", "科": "文曲", "忌": "文昌"},
    "壬": {"禄": "天梁", "权": "紫微", "科": "左辅", "忌": "武曲"},
    "癸": {"禄": "破军", "权": "巨门", "科": "太阴", "忌": "贪狼"},
}

# 辅助：通过天干索引（甲=0…癸=9）快速查表
STEMS = list("甲乙丙丁戊己庚辛壬癸")

def get_sihua_by_stem_idx(stem_idx: int) -> dict[str, str]:
    """根据天干索引返回四化映射。"""
    return SIHUA_TABLE[STEMS[stem_idx % 10]]


def apply_sihua(star_branches: dict[str, int], stem_name: str) -> dict[str, str]:
    """
    给定当前盘面主星位置字典和天干名，
    返回 {宫位_key: 化xxx} 标注。
    star_branches: {"紫微": 4, "天机": 3, ...}
    stem_name: "壬" 等
    返回: {"紫微": "化权", "天梁": "化禄", ...}
    """
    table = SIHUA_TABLE.get(stem_name, {})
    result: dict[str, str] = {}
    for hua_type, star in table.items():
        if star in star_branches:
            result[star] = f"化{hua_type}"
    return result
