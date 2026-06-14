"""
services/ziwei_engine/remedies.py — 破局建议引擎

根据命盘格局与宫位四化，从规则库（data/remedies_rules.json）中
匹配并返回有针对性的化解建议。

公开接口：
    from .remedies import calc_remedies, RemedyResult
    remedies = calc_remedies(chart)
"""

from __future__ import annotations

from dataclasses import dataclass, field
import json
import pathlib
from typing import Any

# 规则文件路径（相对于项目根目录的 data/）
_RULES_PATH = pathlib.Path(__file__).parent.parent.parent / "data" / "remedies_rules.json"

# 全局缓存（模块级，避免重复读取）
_RULES: list[dict] | None = None


def _load_rules() -> list[dict]:
    """延迟加载规则文件，读取后缓存。"""
    global _RULES
    if _RULES is None:
        with open(_RULES_PATH, encoding="utf-8") as f:
            _RULES = json.load(f)
    return _RULES


# ──────────────────────────────────────────────────────────────
# 数据结构
# ──────────────────────────────────────────────────────────────


@dataclass
class RemedyResult:
    """单条破局建议。"""

    id: str  # 规则 ID
    name: str  # 建议标题
    priority: int  # 优先级（1=最高，3=参考）
    cost_level: str  # 成本分级：低 / 中 / 高
    valid_scope: str  # 有效期：流年 / 大运 / 长期
    actions: list[str] = field(default_factory=list)  # 具体行动步骤
    evidence: str = ""  # 触发依据（宫位/格局/大运节点）
    disclaimer: str = ""  # 免责声明


# ──────────────────────────────────────────────────────────────
# 内部辅助
# ──────────────────────────────────────────────────────────────


def _get_palace(palaces: list, name: str):
    """按名称查找宫位对象，未找到返回 None。"""
    return next((p for p in palaces if p.name == name), None)


def _stars_with_hua_in_palace(p, hua: str) -> list[str]:
    """返回宫位中携带指定四化的主星名列表。"""
    if p is None:
        return []
    return [s["name"] for s in p.main_stars if hua in s.get("transforms", [])]


def _pattern_names(chart) -> set[str]:
    """返回命盘已检测到的格局名集合。"""
    return {pt.name for pt in (chart.patterns or [])}


def _fill_template(template: str, context: dict[str, Any]) -> str:
    """简单模板填充，用 {key} 替换 context 中的值。"""
    try:
        return template.format_map(context)
    except (KeyError, ValueError):
        return template


# ──────────────────────────────────────────────────────────────
# 主函数
# ──────────────────────────────────────────────────────────────


def calc_remedies(chart) -> list[RemedyResult]:
    """
    根据命盘格局与宫位四化，从规则库匹配破局建议。

    参数
    ----
    chart : ZiweiChart
        来自 services/ziwei_engine 的完整命盘对象。

    返回
    ----
    list[RemedyResult]
        按优先级升序（数字越小越紧要）排列的建议列表。
        无匹配时返回空列表。
    """
    results: list[RemedyResult] = []
    rules = _load_rules()
    palaces = chart.palaces
    detected_patterns = _pattern_names(chart)

    # 当前流年（用于模板填充）
    liunian_year: int = getattr(chart, "liunian_year", 0) or 0

    # 当前大运（用于模板填充）
    cur_dayun_gz = ""
    if hasattr(chart, "dayun") and chart.dayun and chart.dayun.items:
        import datetime

        cy = datetime.date.today().year
        for d in chart.dayun.items:
            if cy >= d.start_year and cy < d.start_year + 10:
                cur_dayun_gz = d.ganzhi
                break

    for rule in rules:
        trigger = rule.get("trigger", {})
        ttype = trigger.get("type", "")
        matched = False

        # ── 触发类型 1：宫位化忌 ──
        if ttype == "palace_hua":
            palace_name = trigger.get("palace", "")
            hua = trigger.get("hua", "化忌")
            p = _get_palace(palaces, palace_name)
            if p and _stars_with_hua_in_palace(p, hua):
                matched = True
                stars = _stars_with_hua_in_palace(p, hua)
                context = {
                    "stars": "、".join(stars),
                    "palace": palace_name,
                    "liunian_year": liunian_year,
                    "dayun": cur_dayun_gz,
                }
            else:
                context = {}

        # ── 触发类型 2：格局名匹配 ──
        elif ttype == "pattern":
            pattern_name = trigger.get("pattern_name", "")
            if pattern_name in detected_patterns:
                matched = True
                context = {"liunian_year": liunian_year, "dayun": cur_dayun_gz}
            else:
                context = {}

        # ── 触发类型 3：格局 + 流年叠加 ──
        elif ttype == "pattern_and_liunian":
            pattern_name = trigger.get("pattern_name", "")
            if pattern_name in detected_patterns and liunian_year:
                matched = True
                context = {"liunian_year": liunian_year, "dayun": cur_dayun_gz}
            else:
                context = {}

        else:
            context = {}

        if not matched:
            continue

        evidence = _fill_template(rule.get("evidence_template", ""), context)

        results.append(
            RemedyResult(
                id=rule["id"],
                name=rule["name"],
                priority=rule.get("priority", 3),
                cost_level=rule.get("cost_level", "低"),
                valid_scope=rule.get("valid_scope", "长期"),
                actions=rule.get("actions", []),
                evidence=evidence,
                disclaimer=rule.get("disclaimer", "以上为参考性建议，请结合自身情况理性评估。"),
            )
        )

    # 按优先级升序、再按名称字母序稳定排序
    results.sort(key=lambda r: (r.priority, r.name))
    return results
