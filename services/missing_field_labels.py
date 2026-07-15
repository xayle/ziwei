"""Shared human labels for engine missing_fields (UI / colophon / export markdown)."""

from __future__ import annotations

from typing import Any

MISSING_FIELD_LABELS: dict[str, str] = {
    "clash_summary": "刑冲摘要",
    "combine_summary": "合化摘要",
    "harm_summary": "害破摘要",
    "palace_ten_gods": "宫位十神（对照）",
    "youbi_month_vs_iztro_hour": "右弼按月/按时口径差（对照）",
    "palace_stems_partial": "宫干部分（对照）",
    "geju_detail": "格局细目",
    "hour_pillar": "时柱",
    "flow_score": "流日联动分",
    "forecast": "运限预测",
}

ADVISORY_MISSING_FIELDS: frozenset[str] = frozenset(
    {
        "palace_ten_gods",
        "youbi_month_vs_iztro_hour",
        "palace_stems_partial",
    }
)

PROVENANCE_DOMAIN_LABELS: dict[str, str] = {
    "pillars": "四柱",
    "geju": "格局",
    "yongshen": "用神",
    "dayun": "大运",
    "narrative": "叙事",
    "analysis": "分析",
    "scoring": "评分",
    "forecast": "运限",
    "compatibility": "合盘",
    "patterns": "格局检测",
    "stars": "安星",
}

PROVENANCE_LAYER_LABELS: dict[str, str] = {
    "classical": "典籍",
    "engine": "引擎",
    "heuristic": "启发式",
}

CONFIDENCE_LEVEL_LABELS: dict[str, str] = {
    "high": "高",
    "medium": "中等",
    "low": "低",
}


def missing_field_label(field: str) -> str:
    key = (field or "").strip()
    return MISSING_FIELD_LABELS.get(key, key.replace("_", " ") or "—")


def is_advisory_missing_field(field: str) -> bool:
    return (field or "").strip() in ADVISORY_MISSING_FIELDS


def provenance_domain_label(domain: str) -> str:
    key = (domain or "").strip()
    return PROVENANCE_DOMAIN_LABELS.get(key, key.replace("_", " ") or "—")


def provenance_layer_label(layer: str) -> str:
    key = (layer or "").strip()
    return PROVENANCE_LAYER_LABELS.get(key, key or "—")


def confidence_level_label(level: str) -> str:
    key = (level or "").strip()
    return CONFIDENCE_LEVEL_LABELS.get(key, key or "—")


def format_missing_fields_markdown(fields: list[str] | None) -> list[str]:
    """Markdown bullet lines for human export; empty if no fields."""
    cleaned = [f.strip() for f in (fields or []) if isinstance(f, str) and f.strip()]
    if not cleaned:
        return []
    labels = [missing_field_label(f) for f in cleaned]
    heading = "## 字段注记" if all(is_advisory_missing_field(f) for f in cleaned) else "## 字段注记（含缺口）"
    lines = ["", heading]
    for label in labels:
        lines.append(f"- {label}")
    return lines


def format_provenance_markdown(provenance: Any) -> list[str]:
    """Human provenance lines for markdown export."""
    if not isinstance(provenance, dict) or not provenance:
        return []
    lines = ["", "## 可信度分层"]
    wrote = False
    for domain, layer_info in provenance.items():
        if not isinstance(layer_info, dict):
            continue
        layer = layer_info.get("layer")
        if not layer:
            continue
        conf = layer_info.get("confidence")
        conf_txt = f" {int(conf * 100)}%" if isinstance(conf, int | float) else ""
        lines.append(f"- {provenance_domain_label(str(domain))}：{provenance_layer_label(str(layer))}{conf_txt}")
        wrote = True
    return lines if wrote else []
