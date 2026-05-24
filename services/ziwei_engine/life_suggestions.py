"""
services/ziwei_engine/life_suggestions.py — 生活化建议引擎

根据命盘信息（五行局、宫位星曜、四化、格局），从规则库
（data/life_suggestions_rules.json）中匹配并返回生活化建议。

支持五个类别：
    jewelry   — 饰品（材质/颜色/部位）
    plants    — 植物（种类/方位/养护）
    objects   — 家居摆件（铜铃/流水/貔貅等）
    bed       — 床位/书桌朝向布局
    timing    — 择日/吉时建议

公开接口：
    from .life_suggestions import calc_life_suggestions, LifeSuggestion
    suggestions = calc_life_suggestions(chart)
"""
from __future__ import annotations

from dataclasses import dataclass, field
import json
import pathlib
from typing import Any

_RULES_PATH = (
    pathlib.Path(__file__).parent.parent.parent / "data" / "life_suggestions_rules.json"
)

# 全局规则缓存
_RULES: list[dict] | None = None

CATEGORY_LABELS: dict[str, str] = {
    "jewelry": "饰品建议",
    "plants":  "植物摆放",
    "objects": "家居摆件",
    "bed":     "床位布局",
    "timing":  "择日时机",
}


def _load_rules() -> list[dict]:
    global _RULES
    if _RULES is None:
        with open(_RULES_PATH, encoding="utf-8") as f:
            _RULES = json.load(f)
    return _RULES


# ──────────────────────────────────────────────────────────────
# 数据结构
# ──────────────────────────────────────────────────────────────

@dataclass
class LifeSuggestion:
    """单条生活化建议。"""
    id: str
    category: str                          # jewelry / plants / objects / bed / timing
    category_label: str                    # 饰品建议 / 植物摆放 / …
    name: str                              # 建议标题
    priority: int                          # 1=立即, 2=次要, 3=可选
    cost_level: str                        # 低 / 中 / 高
    valid_scope: str                       # 流年 / 大运 / 长期
    short_desc: str = ""                   # 一句话简介
    actions: list[str] = field(default_factory=list)
    evidence: str = ""
    notes: str = ""
    disclaimer: str = ""


# ──────────────────────────────────────────────────────────────
# 内部辅助
# ──────────────────────────────────────────────────────────────

def _get_palace(palaces: list, name: str):
    return next((p for p in palaces if p.name == name), None)


def _stars_in_palace(p, star_set: list[str]) -> list[str]:
    """返回宫位中出现在 star_set 中的主星/辅星名称列表。"""
    if p is None:
        return []
    names: list[str] = []
    for s in getattr(p, "main_stars", []):
        if s["name"] in star_set:
            names.append(s["name"])
    for s in getattr(p, "minor_stars", []):
        if s["name"] in star_set:
            names.append(s["name"])
    return names


def _transform_in_palace(p, transform: str) -> bool:
    """判断宫位内是否有某四化（任意星携带该四化）。"""
    if p is None:
        return False
    for s in getattr(p, "main_stars", []):
        if transform in s.get("transforms", []):
            return True
    return False


def _pattern_names(chart) -> set[str]:
    return {pt.name for pt in (chart.patterns or [])}


def _fill_template(template: str, ctx: dict[str, Any]) -> str:
    try:
        return template.format_map(ctx)
    except (KeyError, ValueError):
        return template


# ──────────────────────────────────────────────────────────────
# 主函数
# ──────────────────────────────────────────────────────────────

def calc_life_suggestions(chart) -> list[LifeSuggestion]:
    """
    根据命盘匹配生活化建议规则，返回排序后的建议列表。

    Parameters
    ----------
    chart : ZiweiChart

    Returns
    -------
    list[LifeSuggestion]
        按优先级升序排列；同优先级内按类别、名称排序。
    """
    results: list[LifeSuggestion] = []
    rules = _load_rules()
    palaces = chart.palaces
    detected_patterns = _pattern_names(chart)
    wuxing_ju: str = getattr(chart, "wuxing_ju_name", "") or ""

    import datetime
    liunian_year: int = getattr(chart, "liunian_year", 0) or datetime.date.today().year

    for rule in rules:
        trigger = rule.get("trigger", {})
        ttype = trigger.get("type", "")
        matched = False
        ctx: dict[str, Any] = {"wuxing_ju": wuxing_ju, "liunian_year": liunian_year}

        # ── 触发类型 1：宫位含指定主星/辅星 ──────────────────
        if ttype == "palace_star":
            palace_name = trigger.get("palace", "")
            star_set = trigger.get("stars", [])
            p = _get_palace(palaces, palace_name)
            found = _stars_in_palace(p, star_set)
            if found:
                matched = True
                ctx.update({"palace": palace_name, "stars": "、".join(found)})

        # ── 触发类型 2：宫位含指定四化 ────────────────────────
        elif ttype == "palace_transform":
            palace_name = trigger.get("palace", "")
            transform = trigger.get("transform", "")
            p = _get_palace(palaces, palace_name)
            if _transform_in_palace(p, transform):
                matched = True
                ctx.update({"palace": palace_name, "transform": transform})

        # ── 触发类型 3：格局名包含关键字 ──────────────────────
        elif ttype == "pattern":
            keyword = trigger.get("pattern_name_contains", "")
            matched_pname = next(
                (pn for pn in detected_patterns if keyword in pn), None
            )
            if matched_pname:
                matched = True
                ctx.update({"pattern_name": matched_pname})

        # ── 触发类型 4：五行局匹配 ────────────────────────────
        elif ttype == "wuxing_ju":
            values = trigger.get("values", [])
            if wuxing_ju in values:
                matched = True
                # ctx 已有 wuxing_ju

        # ── 触发类型 5：宫位+格局联合触发 ────────────────────
        elif ttype == "palace_and_pattern":
            palace_name = trigger.get("palace", "")
            transform = trigger.get("transform", "")
            keyword = trigger.get("pattern_name_contains", "")
            p = _get_palace(palaces, palace_name)
            pat_match = next(
                (pn for pn in detected_patterns if keyword in pn), None
            )
            if _transform_in_palace(p, transform) and pat_match:
                matched = True
                ctx.update({"palace": palace_name, "transform": transform,
                            "pattern_name": pat_match})

        if not matched:
            continue

        evidence = _fill_template(rule.get("evidence_template", ""), ctx)
        cat = rule.get("category", "objects")

        results.append(LifeSuggestion(
            id=rule["id"],
            category=cat,
            category_label=CATEGORY_LABELS.get(cat, cat),
            name=rule["name"],
            priority=rule.get("priority", 3),
            cost_level=rule.get("cost_level", "低"),
            valid_scope=rule.get("valid_scope", "长期"),
            short_desc=rule.get("short_desc", ""),
            actions=rule.get("actions", []),
            evidence=evidence,
            notes=rule.get("notes", ""),
            disclaimer=rule.get(
                "disclaimer",
                "以上为传统命理参考性建议，请结合自身实际情况理性判断，不作为任何专业决策依据。",
            ),
        ))

    results.sort(key=lambda r: (r.priority, r.category, r.name))
    return results
