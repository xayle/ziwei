"""Structured chart export for LLM / third-party workflows (BE-P3-03)."""

from __future__ import annotations

from typing import Any

from services.missing_field_labels import (
    format_missing_fields_markdown,
    format_provenance_markdown,
    provenance_layer_label,
)


def build_bazi_structured_export(payload: dict[str, Any]) -> dict[str, Any]:
    pillars = payload.get("pillars_primary") or {}
    geju = payload.get("geju") or {}
    yongshen = payload.get("yongshen") or {}
    rel = (
        (payload.get("bazi_structural_summary") or {}).get("relation_summary") or payload.get("relations_summary") or {}
    )
    shensha = payload.get("shensha_summary") or payload.get("shensha") or []
    provenance = payload.get("provenance") or {}
    classic_refs = payload.get("classic_refs") or []

    md_lines = [
        "# 八字命盘结构化导出",
        "",
        "## 四柱",
        f"- 年：{_pillar_line(pillars.get('year'))}",
        f"- 月：{_pillar_line(pillars.get('month'))}",
        f"- 日：{_pillar_line(pillars.get('day'))}",
        f"- 时：{_pillar_line(pillars.get('hour'))}",
        "",
        "## 格局与用神",
        f"- 格局：{geju.get('geju_name', '—')}（{geju.get('geju_level', '—')}）",
        f"- 用神喜：{', '.join(yongshen.get('favor') or []) or '—'}",
        f"- 用神忌：{', '.join(yongshen.get('avoid') or []) or '—'}",
        "",
        "## 关系摘要",
        f"- 冲：{rel.get('clash_summary') or '—'}",
        f"- 合：{rel.get('combine_summary') or '—'}",
        f"- 害：{rel.get('harm_summary') or '—'}",
        f"- 互动：{rel.get('interaction_summary') or '—'}",
        "",
        "## 神煞",
    ]
    if isinstance(shensha, dict):
        items = shensha.get("items") or []
    else:
        items = shensha if isinstance(shensha, list) else []
    for item in items[:12]:
        if isinstance(item, dict):
            md_lines.append(f"- {item.get('name', '—')}：{item.get('note') or item.get('topic') or ''}")
    if not items:
        md_lines.append("- （无神煞或未计算）")

    md_lines.extend(["", "## 典籍脚注"])
    for ref in classic_refs[:8]:
        if isinstance(ref, dict):
            layer = provenance_layer_label(str(ref.get("layer") or "classical"))
            md_lines.append(f"- [{layer}] {ref.get('title') or ref.get('id', '')}")

    missing = payload.get("missing_fields") or []
    md_lines.extend(format_missing_fields_markdown(missing if isinstance(missing, list) else []))

    return {
        "format": "bazi_structured@1.0",
        "markdown": "\n".join(md_lines),
        "json": {
            "pillars_primary": pillars,
            "geju": geju,
            "yongshen": yongshen,
            "relations_summary": rel,
            "shensha": shensha,
            "provenance": provenance,
            "classic_refs": classic_refs,
            "missing_fields": missing,
            "bazi_summary": payload.get("bazi_summary", ""),
        },
    }


def build_ziwei_structured_export(payload: dict[str, Any]) -> dict[str, Any]:
    md_lines = [
        "# 紫微命盘结构化导出",
        "",
        f"- 命宫：{payload.get('life_palace_gz', '—')}",
        f"- 身宫：{payload.get('body_palace_gz', '—')}",
        f"- 五行局：{payload.get('wuxing_ju_name', '—')}",
        "",
        "## 格局",
    ]
    patterns = payload.get("patterns") or []
    for p in patterns[:8]:
        if isinstance(p, dict):
            layer = provenance_layer_label(str(p.get("layer") or "engine"))
            md_lines.append(f"- {p.get('name', '—')} [{p.get('tier', '—')}] · {layer}")
    if not patterns:
        md_lines.append("- （无格局或未计算）")

    provenance = payload.get("provenance") or {}
    md_lines.extend(format_provenance_markdown(provenance))
    missing = payload.get("missing_fields") or []
    md_lines.extend(format_missing_fields_markdown(missing if isinstance(missing, list) else []))

    return {
        "format": "ziwei_structured@1.0",
        "markdown": "\n".join(md_lines),
        "json": {
            "life_palace_gz": payload.get("life_palace_gz"),
            "body_palace_gz": payload.get("body_palace_gz"),
            "wuxing_ju_name": payload.get("wuxing_ju_name"),
            "patterns": patterns,
            "palaces": payload.get("palaces"),
            "provenance": provenance,
            "missing_fields": missing if isinstance(missing, list) else [],
            "summary": payload.get("summary", ""),
        },
    }


def _pillar_line(pillar: Any) -> str:
    if not isinstance(pillar, dict):
        return "—"
    stem = pillar.get("stem") or pillar.get("heavenly_stem") or "—"
    branch = pillar.get("branch") or pillar.get("earthly_branch") or "—"
    return f"{stem}{branch}"
