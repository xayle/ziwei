"""Build bazi_full response provenance from verify output + request."""

from __future__ import annotations

from typing import Any

from app.schemas.bazi import BaziFullRequest
from app.schemas.provenance import ProvenanceLayer, ResponseProvenance

_ANALYSIS_FIELD_NAMES = frozenset(
    {
        "geju",
        "yongshen",
        "shensha",
        "palace",
        "wealth_analysis",
        "career",
        "marriage_analysis",
        "health",
        "relationship",
        "personality",
        "monthly_fortune",
        "jewelry",
        "fengshui",
        "lucky",
        "lifestyle",
        "milestones",
        "liunian",
        "life_arc",
        "liunian_detail",
        "current_fortune_summary",
        "bazi_summary",
        "shishen_summary",
        "yearly_fortune",
    }
)


def day_boundary_crossed(zi_day_rule: str, hour: int) -> bool:
    """Whether the effective birth hour triggers a zi-hour day-boundary notice."""
    if hour not in (23, 0):
        return False
    if zi_day_rule == "early_zi_prev_day":
        return hour == 23
    if zi_day_rule == "early_zi_same_day":
        return False
    # sxtwl / default backend behavior
    return True


def build_bazi_provenance(
    verify_response: Any,
    body: BaziFullRequest,
    *,
    missing_fields: list[str] | None = None,
) -> ResponseProvenance:
    """Attach method-aware provenance for the frontend trust panel."""
    missing = set(missing_fields or [])
    geju = getattr(verify_response, "geju", None)

    geju_bits: list[str] = [f"子时规则={body.zi_day_rule}"]
    if geju:
        if getattr(geju, "recorded_geju", None) and geju.recorded_geju != geju.geju_name:
            geju_bits.append(f"古籍={geju.recorded_geju}")
        if getattr(geju, "engine_geju", None) and geju.engine_geju != geju.geju_name:
            geju_bits.append(f"引擎={geju.engine_geju}")
        if getattr(geju, "dual_track_note", None):
            geju_bits.append(geju.dual_track_note)

    geju_conf = 0.85 if geju else 0.4
    if "geju" in missing:
        geju_conf = 0.35

    pillars = getattr(verify_response, "pillars_primary", None)
    pillars_conf = 0.92 if pillars else 0.5

    yongshen = getattr(verify_response, "yongshen", None)
    yongshen_conf = 0.82 if yongshen and getattr(yongshen, "favor", None) else 0.45
    if "yongshen" in missing:
        yongshen_conf = 0.35

    dayun = getattr(verify_response, "dayun", None)
    dayun_items = getattr(dayun, "items", None) or getattr(dayun, "cycles", None) or []
    dayun_conf = 0.86 if dayun_items else 0.5
    if "dayun" in missing:
        dayun_conf = 0.35

    classic_ref = getattr(geju, "classic_ref", None) if geju else None
    interpretation = getattr(geju, "interpretation_text", None) if geju else None
    bazi_summary = getattr(verify_response, "bazi_summary", None) or ""
    narrative_conf = 0.72 if classic_ref or interpretation or bazi_summary else 0.5
    narrative_note = classic_ref or (interpretation[:80] if interpretation else None)

    analysis_missing = missing & _ANALYSIS_FIELD_NAMES
    analysis_conf = 0.52
    if analysis_missing:
        analysis_conf = max(0.32, 0.52 - 0.04 * min(len(analysis_missing), 5))
    analysis_note = None
    if missing:
        analysis_note = f"未计算：{'、'.join(sorted(missing)[:4])}"

    yearly = getattr(verify_response, "yearly_fortune", None)
    scoring_conf = 0.42 if yearly else 0.38

    return ResponseProvenance(
        pillars=ProvenanceLayer(
            layer="engine",
            confidence=pillars_conf,
            method_registry_id="B-P0-pillars",
            note=f"mode={body.mode} · solar={body.solar_time_enabled}",
        ),
        geju=ProvenanceLayer(
            layer="engine",
            confidence=geju_conf,
            method_registry_id="B-P3-geju",
            note=" · ".join(geju_bits) if geju_bits else None,
        ),
        yongshen=ProvenanceLayer(
            layer="engine",
            confidence=yongshen_conf,
            method_registry_id="B-P3-yongshen",
        ),
        dayun=ProvenanceLayer(
            layer="engine",
            confidence=dayun_conf,
            method_registry_id="B-P2-dayun",
            note=f"gender={body.gender or '—'}",
        ),
        narrative=ProvenanceLayer(
            layer="classical" if classic_ref else "heuristic",
            confidence=narrative_conf,
            method_registry_id="B-P4-narrative",
            note=narrative_note,
        ),
        analysis=ProvenanceLayer(
            layer="heuristic",
            confidence=analysis_conf,
            method_registry_id="B-heuristic-analysis",
            note=analysis_note,
        ),
        scoring=ProvenanceLayer(
            layer="modern_convention",
            confidence=scoring_conf,
            method_registry_id="B-scoring-modern",
            note="现代六维评分，非典籍断语",
        ),
    )
