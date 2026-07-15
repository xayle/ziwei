"""Build ziwei_full response provenance from chart + request."""

from __future__ import annotations

from app.schemas.provenance import ProvenanceLayer, ResponseProvenance
from app.schemas.ziwei import ZiweiRequest
from services.ziwei_engine import ZiweiChart

_YEAR_DIVIDE_LABELS = {
    "lichun": "立春换年",
    "normal": "正月初一换年",
}

_DAY_DIVIDE_LABELS = {
    "forward": "农历日+1安星",
    "current": "当日子时",
    "solar_next": "公历次日换日",
}


def _year_divide_label(value: str | None) -> str:
    key = (value or "").strip()
    return _YEAR_DIVIDE_LABELS.get(key, "年界规则")


def _day_divide_label(value: str | None) -> str:
    key = (value or "").strip()
    return _DAY_DIVIDE_LABELS.get(key, "日界规则")


def build_ziwei_provenance(chart: ZiweiChart, req: ZiweiRequest) -> ResponseProvenance:
    """Attach method-aware provenance notes for frontend trust panel."""
    warnings = list(getattr(chart, "engine_warnings", None) or [])
    missing = list(getattr(chart, "missing_fields", None) or [])

    stars_note = None
    if warnings:
        stars_note = "；".join(warnings[:3])

    forecast_conf = 0.45 if chart.forecast else 0.35
    patterns_conf = 0.75 if chart.patterns else 0.5
    if missing:
        patterns_conf = max(0.35, patterns_conf - 0.1 * min(len(missing), 3))

    return ResponseProvenance(
        stars=ProvenanceLayer(
            layer="engine",
            confidence=0.92 if not warnings else 0.86,
            method_registry_id="Z-P0-stars",
            note=stars_note,
        ),
        patterns=ProvenanceLayer(
            layer="engine",
            confidence=patterns_conf,
            method_registry_id="Z-P2-patterns",
            note=(f"年界：{_year_divide_label(req.year_divide)}" f" · 晚子换日：{_day_divide_label(req.day_divide)}"),
        ),
        narrative=ProvenanceLayer(
            layer="classical",
            confidence=0.68 if chart.patterns else 0.55,
            method_registry_id="Z-P4-classic-refs",
            note="典籍软提示，非硬覆盖格局判定",
        ),
        forecast=ProvenanceLayer(
            layer="heuristic",
            confidence=forecast_conf,
            method_registry_id="Z-forecast-heuristic",
            note="叠宫/关键词参考，非铁口直断",
        ),
        analysis=ProvenanceLayer(
            layer="heuristic",
            confidence=0.5,
            method_registry_id="Z-heuristic-analysis",
            note="宫位断语含组合表与单星回退",
        ),
    )
