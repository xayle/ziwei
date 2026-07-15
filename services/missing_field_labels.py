"""Shared human labels for engine missing_fields (UI / colophon / export markdown)."""

from __future__ import annotations

MISSING_FIELD_LABELS: dict[str, str] = {
    "clash_summary": "刑冲摘要",
    "combine_summary": "合化摘要",
    "harm_summary": "害破摘要",
    "palace_ten_gods": "宫位十神（对照）",
    "youbi_month_vs_iztro_hour": "右弼 month/hour 口径差（对照）",
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


def missing_field_label(field: str) -> str:
    key = (field or "").strip()
    return MISSING_FIELD_LABELS.get(key, key.replace("_", " ") or "—")


def is_advisory_missing_field(field: str) -> bool:
    return (field or "").strip() in ADVISORY_MISSING_FIELDS


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
