"""Build YongShenModel with classical dual-track metadata."""

from __future__ import annotations

from app.schemas.bazi import YongShenModel

from .dual_track import lookup_yongshen_dual_track


def build_yongshen_model(
    favor: list[str],
    avoid: list[str],
    rationale: str | None,
    *,
    year: str = "",
    month: str = "",
    day: str = "",
    hour: str = "",
) -> YongShenModel:
    dual = lookup_yongshen_dual_track(year, month, day, hour) if all((year, month, day, hour)) else None
    recorded = list(dual.get("recorded_favor") or []) if dual else []
    engine_favor = list(favor or [])
    dual_note = str(dual.get("note") or "") if dual else None
    dual_id = str(dual.get("id") or "") if dual else None

    parts = [rationale or ""]
    if dual_note:
        parts.append(dual_note)

    return YongShenModel(
        favor=engine_favor,
        avoid=list(avoid or []),
        rationale="；".join(p for p in parts if p) or None,
        recorded_favor=recorded,
        engine_favor=engine_favor,
        dual_track_note=dual_note,
        dual_track_id=dual_id,
    )
