"""Build GejuModel from compute_geju() output for API layers."""

from __future__ import annotations

from app.schemas.analysis_core import GejuModel

from .classic_refs import geju_candidates as _geju_candidates
from .dual_track import lookup_dual_track


def _geju_level(name: str) -> str:
    if name in ("普通格",):
        return "无格"
    if any(k in name for k in ("从", "专旺", "曲直", "炎上", "稼穑", "从革", "润下", "化")):
        return "上格"
    if name.endswith("格"):
        return "中格"
    return "中格"


def build_geju_model(
    geju_raw: dict,
    *,
    year: str = "",
    month: str = "",
    day: str = "",
    hour: str = "",
    classic_ref: str = "",
) -> GejuModel:
    po = geju_raw.get("po_geju") or {}
    name = geju_raw.get("name", "普通格")
    derived = geju_raw.get("derived_geju") or None
    is_broken = bool(po.get("broken"))

    dual = lookup_dual_track(year, month, day, hour) if all((year, month, day, hour)) else None
    recorded = dual.get("recorded_geju") if dual else None
    dual_note = dual.get("note") if dual else None
    dual_id = dual.get("id") if dual else None

    candidates = _geju_candidates(name, limit=3)
    if recorded and recorded != name:
        extra = _geju_candidates(recorded, limit=2)
        seen = {c.get("id") for c in candidates}
        for item in extra:
            if item.get("id") not in seen:
                candidates.append(item)
                seen.add(item.get("id"))

    tags = [name]
    if derived and derived != name:
        tags.append(derived)
    if recorded and recorded != name:
        tags.append(f"古籍:{recorded}")

    detail_parts = [geju_raw.get("note", "")]
    if derived and derived != name:
        detail_parts.append(f"衍生格：{derived}")
    if po.get("broken"):
        detail_parts.append(f"破格：{po.get('reason', '')}")
        jiu = po.get("po_jiu") or {}
        if jiu.get("saved"):
            detail_parts.append(f"救应：{jiu.get('method', '')} — {jiu.get('note', '')}")
    if dual_note:
        detail_parts.append(dual_note)

    return GejuModel(
        geju_name=name,
        geju_level=_geju_level(name),  # type: ignore[arg-type]
        month_stem_shishen=geju_raw.get("ten_god", ""),
        is_broken=is_broken,
        inference_tags=tags,
        interpretation_text="",
        classic_ref=classic_ref,
        confidence=geju_raw.get("confidence", 0.0),
        geju_detail="；".join(p for p in detail_parts if p),
        derived_geju=derived,
        po_geju=po,
        geju_candidates=candidates,
        recorded_geju=recorded,
        engine_geju=name,
        dual_track_note=dual_note,
        dual_track_id=dual_id,
    )
