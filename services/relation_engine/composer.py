"""Compose RelationCompatResponse from dual charts."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import uuid4
from zoneinfo import ZoneInfo

from app.schemas import BaziFullRequest
from app.schemas.ziwei import ZiweiRequest
from constants import RULE_VERSION
from services.chart_snapshot_service import build_bazi_snapshot, build_ziwei_snapshot
from services.content_policy import default_disclaimer_block
from services.relation_engine.bazi_scorer import load_pillar_data, score_bazi_dimensions
from services.relation_engine.copy_templates import (
    build_action_items,
    build_summary,
    check_forbidden,
    sanitize_text,
    score_to_grade,
)
from services.relation_engine.registry import get_type_config
from services.relation_engine.tensions import detect_tensions
from services.relation_engine.timeline import build_timeline
from services.relation_engine.ziwei_scorer import collect_harmony_conflicts, score_ziwei_dimensions


def _normalize_gender(g: str) -> str:
    if g in ("男", "女"):
        return g
    return "男" if g == "male" else "女"


def _gender_literal(g: str) -> str:
    return "male" if _normalize_gender(g) == "男" else "female"


def _parse_birth(dt_str: str, tz: str) -> datetime:
    dt = datetime.fromisoformat(dt_str)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=ZoneInfo(tz))
    return dt.astimezone(ZoneInfo(tz)).replace(tzinfo=None)


def _weighted_score(dimensions: list[dict[str, Any]]) -> float:
    if not dimensions:
        return 0.0
    total_w = sum(d.get("weight", 0.1) for d in dimensions)
    if total_w <= 0:
        return 0.0
    acc = 0.0
    for d in dimensions:
        mx = d.get("max_score") or 1
        ratio = (d.get("score") or 0) / mx if mx else 0
        acc += ratio * d.get("weight", 0.1)
    return round(acc / total_w * 100, 1)


def _build_person_ref(
    label: str,
    gender: str,
    birth_solar: str,
    pillars: dict,
    *,
    case_id: str | None = None,
    life_palace_gz: str | None = None,
    wuxing_ju_name: str | None = None,
) -> dict[str, Any]:
    ref: dict[str, Any] = {
        "label": label,
        "gender": gender,
        "birth_solar": birth_solar,
        "pillars_primary": {k: {"stem": v["stem"], "branch": v["branch"]} for k, v in pillars.items()},
    }
    if case_id:
        ref["case_id"] = case_id
    if life_palace_gz:
        ref["life_palace_gz"] = life_palace_gz
    if wuxing_ju_name:
        ref["wuxing_ju_name"] = wuxing_ju_name
    return ref


def _build_summary_cards(
    dimensions: list[dict[str, Any]],
    harmony: list[str],
    conflicts: list[str],
    relation_type: str,
    forbidden: list[str],
) -> list[dict[str, Any]]:
    cards: list[dict[str, Any]] = []
    day_branch = next((d for d in dimensions if d.get("id") == "day_branch"), None)
    if day_branch and "冲" in day_branch.get("description", ""):
        text = sanitize_text(day_branch["description"], forbidden)
        cards.append({"id": "card-day-branch", "tone": "conflict", "text": text[:120]})
    elif day_branch:
        cards.append(
            {
                "id": "card-day-branch",
                "tone": "neutral",
                "text": day_branch["description"][:120],
            }
        )

    for i, h in enumerate(harmony[:2]):
        cards.append(
            {
                "id": f"card-harmony-{i}",
                "tone": "support",
                "text": sanitize_text(h, forbidden)[:120],
            }
        )

    for i, c in enumerate(conflicts[:2]):
        if len(cards) >= 5:
            break
        cards.append(
            {
                "id": f"card-conflict-{i}",
                "tone": "conflict",
                "text": sanitize_text(c, forbidden)[:120],
            }
        )

    if len(cards) < 3:
        cards.append(
            {
                "id": "card-action-default",
                "tone": "action",
                "text": "建议定期对齐预期，记录可执行的下一步。",
            }
        )

    tones = {c["tone"] for c in cards}
    if "support" not in tones and harmony:
        cards.insert(
            0,
            {
                "id": "card-support-fill",
                "tone": "support",
                "text": sanitize_text(harmony[0], forbidden)[:120],
            },
        )
    if "conflict" not in tones and conflicts:
        cards.append(
            {
                "id": "card-conflict-fill",
                "tone": "conflict",
                "text": sanitize_text(conflicts[0], forbidden)[:120],
            }
        )
    if "action" not in tones:
        cards.append(
            {
                "id": "card-action-fill",
                "tone": "action",
                "text": "列出本周一件可执行的小目标，并约定复盘时间。",
            }
        )

    return cards[:5]


def _extract_yongshen(bazi_response) -> tuple[list[str], list[str]]:
    favor: list[str] = []
    avoid: list[str] = []
    try:
        ys = getattr(bazi_response, "yongshen", None)
        if ys:
            favor = list(getattr(ys, "favor", None) or getattr(ys, "engine_favor", None) or [])
            avoid = list(getattr(ys, "avoid", None) or [])
    except Exception:
        pass
    return favor, avoid


def compute_relation_full(
    *,
    relation_type: str,
    person_a: dict[str, Any],
    person_b: dict[str, Any],
    options: dict[str, Any] | None = None,
    supervisor_id: str | None = None,
) -> dict[str, Any]:
    opts = options or {}
    include_bazi = opts.get("include_bazi", True)
    include_ziwei = opts.get("include_ziwei", True)
    liunian_year = opts.get("liunian_year")
    timeline_span = opts.get("timeline_years") or [-1, 2]
    span_before = abs(timeline_span[0]) if timeline_span else 1
    span_after = timeline_span[1] if len(timeline_span) > 1 else 2

    type_cfg = get_type_config(relation_type)
    if type_cfg.get("requires_role") and not supervisor_id:
        raise ValueError("supervisor_subordinate requires supervisor_id ('a' or 'b')")

    forbidden = list(type_cfg.get("forbidden_copy") or [])
    bazi_specs = list(type_cfg.get("bazi_dimensions") or [])
    palace_pairs = list(type_cfg.get("ziwei_palace_pairs") or [])

    def _resolve(person: dict[str, Any], default_label: str) -> tuple[datetime, float, str, str, str]:
        tz = person.get("tz") or "Asia/Shanghai"
        lon = float(person.get("longitude", 116.41))
        gender = person.get("gender") or "male"
        label = person.get("label") or default_label
        dt = _parse_birth(person["birth_datetime"], tz)
        return dt, lon, tz, gender, label

    dt_a, lon_a, tz_a, gender_a, label_a = _resolve(person_a, "甲方")
    dt_b, lon_b, tz_b, gender_b, label_b = _resolve(person_b, "乙方")

    a_pillar = load_pillar_data(dt_a, lon_a, tz_a)
    b_pillar = load_pillar_data(dt_b, lon_b, tz_b)

    bazi_snap_a = bazi_snap_b = None
    favor_a = favor_b = avoid_a = avoid_b = []
    if include_bazi:
        bazi_snap_a = build_bazi_snapshot(
            BaziFullRequest(
                dt=dt_a.replace(tzinfo=ZoneInfo(tz_a)),
                lon=lon_a,
                tz=tz_a,
                mode="single",
                gender=_gender_literal(gender_a),
            )
        )
        bazi_snap_b = build_bazi_snapshot(
            BaziFullRequest(
                dt=dt_b.replace(tzinfo=ZoneInfo(tz_b)),
                lon=lon_b,
                tz=tz_b,
                mode="single",
                gender=_gender_literal(gender_b),
            )
        )
        favor_a, avoid_a = _extract_yongshen(bazi_snap_a.response)
        favor_b, avoid_b = _extract_yongshen(bazi_snap_b.response)

    chart_a = chart_b = None
    if include_ziwei:

        def _ziwei_req(dt, lon, gender):
            return ZiweiRequest(
                year=dt.year,
                month=dt.month,
                day=dt.day,
                hour=dt.hour,
                minute=dt.minute,
                gender=_normalize_gender(gender),
                liunian_year=liunian_year,
                longitude=lon,
            )

        chart_a = build_ziwei_snapshot(_ziwei_req(dt_a, lon_a, gender_a)).chart
        chart_b = build_ziwei_snapshot(_ziwei_req(dt_b, lon_b, gender_b)).chart

    dimensions: list[dict[str, Any]] = []
    if include_bazi:
        dimensions.extend(
            score_bazi_dimensions(
                a_pillar,
                b_pillar,
                bazi_specs,
                favor_a=favor_a,
                avoid_a=avoid_a,
                favor_b=favor_b,
                avoid_b=avoid_b,
            )
        )

    palace_cross: list[dict[str, Any]] = []
    harmony: list[str] = []
    conflicts: list[str] = []
    if include_ziwei and chart_a and chart_b:
        zw_dims, palace_cross = score_ziwei_dimensions(
            chart_a,
            chart_b,
            bazi_specs,
            palace_pairs,
        )
        dimensions.extend(zw_dims)
        harmony, conflicts = collect_harmony_conflicts(chart_a, chart_b)

    combined = _weighted_score(dimensions)
    grade = score_to_grade(combined)

    conflict_hint = ""
    db_dim = next((d for d in dimensions if d.get("id") == "day_branch"), None)
    if db_dim and "冲" in db_dim.get("description", ""):
        conflict_hint = "日支冲需重点调和。"

    summary = build_summary(relation_type, combined, conflict_hint)
    violations = check_forbidden(summary, forbidden)
    if violations:
        summary = sanitize_text(summary, forbidden)

    summary_cards = _build_summary_cards(
        dimensions,
        harmony,
        conflicts,
        relation_type,
        forbidden,
    )

    timeline = build_timeline(
        year_a=a_pillar["pillars"]["year"]["branch"],
        year_b=b_pillar["pillars"]["year"]["branch"],
        liunian_year=liunian_year or datetime.now().year,
        span_before=span_before,
        span_after=span_after,
        relation_type=relation_type,
    )

    action_items = build_action_items(relation_type, conflicts)
    missing: list[str] = []
    if not include_bazi:
        missing.append("bazi")
    if not include_ziwei:
        missing.append("ziwei")

    bazi_dims = [d for d in dimensions if d.get("engine") == "bazi"]
    ziwei_dims = [d for d in dimensions if d.get("engine") == "ziwei"]
    bazi_score = _weighted_score(bazi_dims) if bazi_dims else None
    ziwei_score = _weighted_score(ziwei_dims) if ziwei_dims else None

    bazi_raw_a = bazi_snap_a.response.model_dump(mode="json") if bazi_snap_a else None
    bazi_raw_b = bazi_snap_b.response.model_dump(mode="json") if bazi_snap_b else None
    tensions = detect_tensions(bazi_raw_a, bazi_raw_b)

    person_a_ref = _build_person_ref(
        label_a,
        gender_a,
        person_a["birth_datetime"],
        a_pillar["pillars"],
        case_id=person_a.get("case_id"),
        life_palace_gz=chart_a.life_palace_gz if chart_a else None,
        wuxing_ju_name=chart_a.wuxing_ju_name if chart_a else None,
    )
    person_b_ref = _build_person_ref(
        label_b,
        gender_b,
        person_b["birth_datetime"],
        b_pillar["pillars"],
        case_id=person_b.get("case_id"),
        life_palace_gz=chart_b.life_palace_gz if chart_b else None,
        wuxing_ju_name=chart_b.wuxing_ju_name if chart_b else None,
    )

    inference_sections = [
        {
            "id": "advice",
            "heading": "相处建议",
            "blocks": [{"text": item["text"]} for item in action_items[:5]],
        }
    ]

    from services.explain_relation import build_relation_cite_layers

    cite_sections = build_relation_cite_layers(
        relation_type=relation_type,
        relation_type_label=type_cfg.get("label", relation_type),
        combined_score=combined,
        grade=grade,
    )

    return {
        "schema_version": "relation-compat@1.0",
        "request_id": str(uuid4()),
        "relation_type": relation_type,
        "relation_type_label": type_cfg.get("label", relation_type),
        "person_a": person_a_ref,
        "person_b": person_b_ref,
        "combined_score": combined,
        "grade": grade,
        "summary": summary,
        "summary_cards": summary_cards,
        "disclaimer_block": default_disclaimer_block(),
        "layers": {
            "fact": {"collapsed_default": False, "sections": []},
            "cite": {"collapsed_default": True, "sections": cite_sections},
            "inference": {"collapsed_default": True, "sections": inference_sections},
        },
        "dimensions": dimensions,
        "bazi": {
            "score": bazi_score,
            "max_score": 100,
            "dimensions": bazi_dims,
            "harmony_points": [],
            "conflict_points": [d["description"] for d in bazi_dims if "冲" in d.get("description", "")],
        }
        if include_bazi
        else None,
        "ziwei": {
            "score": ziwei_score,
            "max_score": 100,
            "dimensions": ziwei_dims,
            "harmony_points": harmony,
            "conflict_points": conflicts,
        }
        if include_ziwei
        else None,
        "palace_cross": palace_cross,
        "timeline": timeline,
        "action_items": action_items,
        "tensions": tensions,
        "missing_fields": missing,
        "meta": {
            "chart_hash_a": bazi_snap_a.chart_hash if bazi_snap_a else None,
            "chart_hash_b": bazi_snap_b.chart_hash if bazi_snap_b else None,
            "rule_version": RULE_VERSION,
            "layer": "heuristic",
        },
    }
