"""Shared human labels for engine missing_fields (UI / colophon / export markdown)."""

from __future__ import annotations

from typing import Any

MISSING_FIELD_LABELS: dict[str, str] = {
    "clash_summary": "刑冲摘要",
    "combine_summary": "合化摘要",
    "harm_summary": "害破摘要",
    "palace_ten_gods": "宫位十神（对照·非故障）",
    "youbi_month_vs_iztro_hour": "右弼按月/按时口径差（对照）",
    "palace_stems_partial": "宫干部分（对照）",
    "geju_detail": "格局细目",
    "hour_pillar": "时柱",
    "flow_score": "流日联动分",
    "flow_score_dayun": "流日·大运维",
    "flow_score_liunian": "流日·流年维",
    "flow_score_geju": "流日·格局维",
    "flow_tone": "流日顺逆",
    "flow_summary": "流日摘要",
    "dayun_context": "流日大运上下文",
    "liunian_context": "流日流年上下文",
    "forecast": "运限预测",
    "tongxian_horoscope": "童限（起运前，对照）",
}

ADVISORY_MISSING_FIELDS: frozenset[str] = frozenset(
    {
        "palace_ten_gods",
        "youbi_month_vs_iztro_hour",
        "palace_stems_partial",
        "tongxian_horoscope",
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
    "modern_convention": "现代约定",
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


CROSSCHECK_STATUS_LABELS: dict[str, str] = {
    "ok": "主星一致",
    "main_match": "主星一致",
    "degraded": "降级",
    "life_palace_mismatch": "命宫不一致",
    "life_palace_only": "仅命宫可对照",
    "unknown": "未核验",
}

VALIDATION_LEVEL_LABELS: dict[str, str] = {
    "L0": "双轨一致",
    "L1": "基础",
    "L2": "标准",
    "L3": "严格",
}


def format_crosscheck_status_label(status: Any) -> str:
    key = str(status or "").strip()
    if not key:
        return "未核验"
    if key.startswith("partial_main_"):
        return "主星部分一致"
    return CROSSCHECK_STATUS_LABELS.get(key, "未核验" if key.isascii() else key)


def format_validation_level_label(level: Any) -> str:
    key = str(level or "").strip()
    if not key:
        return "未分级"
    return VALIDATION_LEVEL_LABELS.get(key, "未分级" if key.isascii() else key)


def sanitize_user_facing_text(text: Any) -> str:
    """Strip engine brand / internal codes from user-visible strings."""
    if text is None:
        return ""
    s = str(text)
    if not s.strip():
        return ""
    import re

    s = re.sub(r"\biztro\b", "开源对照轨", s, flags=re.IGNORECASE)
    s = re.sub(r"\bsolar_next\b", "公历次日换日", s)
    s = re.sub(r"\bforward\b", "农历日+1安星", s)
    s = re.sub(r"\bcurrent\b", "当日子时", s)
    s = re.sub(r"\blichun\b", "立春换年", s)
    s = re.sub(r"\bmain_match\b", "主星一致", s)
    s = re.sub(r"\bL0\b", "双轨一致", s)
    s = re.sub(r"\bL1\b", "基础", s)
    s = re.sub(r"\bL2\b", "标准", s)
    s = re.sub(r"\bL3\b", "严格", s)
    s = re.sub(r"\s*vs\.?\s*", "与", s, flags=re.IGNORECASE)
    s = re.sub(r"开源对照轨\s*对照轨", "开源对照轨", s)
    s = re.sub(r"[ \t]{2,}", " ", s).strip()
    return s


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
