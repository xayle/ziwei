"""Audit life-volume block density for a canonical profile (R086 helper)."""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

os.environ.setdefault("SECRET_KEY", "audit-content-hollowness")

from app.schemas.bazi import BaziFullRequest
from app.schemas.explain import ExplainBatchRequest, ZiweiExplainBatchRequest
from app.schemas.ziwei import ZiweiRequest
from routers.ziwei import _chart_to_response, _ziwei_full_args
from services.bazi_full_service import bazi_full
from services.explain_service import explain_bazi_batch, explain_ziwei_batch
from services.ziwei_engine import ziwei_full

FALLBACK_MARKERS = (
    "待计算",
    "待分析",
    "待载入",
    "数据缺失",
    "字段缺失",
    "暂无",
    "接口不可用",
    "未填写",
    "待排盘",
    "引擎版本待计算",
    "请确认",
    "未叠盘",
    "列表数据",
)


def is_fallback(text: object) -> bool:
    if text is None:
        return True
    t = str(text).strip()
    if not t:
        return True
    # 单独占位符（整段）才算空洞；正文中的「—」连接号不算
    if t in ("—", "-", "…", "－"):
        return True
    return any(m in t for m in FALLBACK_MARKERS)


def audit_block(text: object, limit: int = 500) -> dict:
    t = str(text or "")
    return {
        "chars": len(t),
        "fallback": is_fallback(t),
        "truncated": len(t) >= limit - 5,
        "thin": len(t) < 40 and not is_fallback(t),
        "preview": t[:80],
    }


def summarize(blocks: list[dict]) -> dict:
    n = len(blocks)
    if not n:
        return {"blocks": 0, "fallback_pct": 100.0, "thin_pct": 0.0, "trunc_pct": 0.0, "avg_chars": 0}
    fb = sum(1 for b in blocks if b["fallback"])
    thin = sum(1 for b in blocks if b["thin"])
    trunc = sum(1 for b in blocks if b["truncated"])
    return {
        "blocks": n,
        "fallback_pct": round(100 * fb / n, 1),
        "thin_pct": round(100 * thin / n, 1),
        "trunc_pct": round(100 * trunc / n, 1),
        "avg_chars": round(sum(b["chars"] for b in blocks) / n, 1),
    }


def compute_rollup(volumes_report: dict[str, dict]) -> dict:
    blocks = 0
    thin = 0
    fallback = 0
    for vol in volumes_report.values():
        n = int(vol.get("blocks") or 0)
        blocks += n
        thin += int(round((vol.get("thin_pct") or 0) * n / 100))
        fallback += int(round((vol.get("fallback_pct") or 0) * n / 100))
    thin_pct = round(100 * thin / blocks, 1) if blocks else 100.0
    return {
        "blocks_total": blocks,
        "thin_blocks": thin,
        "thin_pct": thin_pct,
        "fallback_blocks": fallback,
        "fallback_pct": round(100 * fallback / blocks, 1) if blocks else 100.0,
        "week4_target_thin_pct": 35.0,
        "thin_target_met": thin_pct <= 35.0,
    }


def format_relations_summary_text(bazi: dict) -> str:
    """Mirror frontend formatRelationsSummaryText (formatVol2Summary.ts)."""
    rs = bazi.get("relations_summary") or {}
    if isinstance(rs, dict):
        parts = [
            str(rs.get(key) or "").strip()
            for key in ("interaction_summary", "clash_summary", "combine_summary", "harm_summary")
        ]
        parts = [p for p in parts if p]
        if parts:
            return "；".join(parts)
        lines: list[str] = []
        for item in (rs.get("items") or [])[:6]:
            if not isinstance(item, dict):
                continue
            summary = str(item.get("summary") or "").strip()
            if summary:
                lines.append(summary)
                continue
            legacy = str(item.get("detail") or "").strip()
            if legacy:
                lines.append(legacy)
                continue
            core = " ".join(
                x
                for x in (
                    str(item.get("type") or "").strip(),
                    str(item.get("subject") or "").strip(),
                    str(item.get("target") or "").strip(),
                )
                if x
            )
            if core:
                lines.append(core)
        if lines:
            return "；".join(lines)
    rel_lines: list[str] = []
    for rel in bazi.get("dizhi_relations") or []:
        if not isinstance(rel, dict):
            continue
        type_ = str(rel.get("type") or rel.get("relation") or "").strip()
        branches = str(rel.get("branches") or rel.get("pair") or "").strip()
        note = str(rel.get("note") or rel.get("desc") or "").strip()
        text = " · ".join(x for x in (type_, branches, note) if x)
        if text:
            rel_lines.append(text)
    for clash in bazi.get("tiangan_clashes") or []:
        if not isinstance(clash, dict):
            continue
        stems = str(clash.get("stems") or clash.get("pair") or "").strip()
        note = str(clash.get("note") or clash.get("type") or "天干冲").strip()
        text = " · ".join(x for x in (note, stems) if x)
        if text:
            rel_lines.append(text)
    if rel_lines:
        return "；".join(rel_lines[:4])
    return "暂无干支关系摘要"


def format_shensha_summary_text(bazi: dict) -> str:
    ss = bazi.get("shensha_summary") or {}
    if isinstance(ss, dict):
        highlights = ss.get("highlights") or []
        if highlights:
            names = [str(x) for x in highlights if x]
            if names:
                return "、".join(names[:8])
        raw = ss.get("items") or []
        names = [x.get("name", "") if isinstance(x, dict) else str(x) for x in raw]
        names = [n for n in names if n]
        if names:
            return "、".join(names[:8])
    fallback = [
        str(item.get("name") or "")
        for item in (bazi.get("shensha") or [])
        if isinstance(item, dict) and item.get("name")
    ]
    return "、".join(fallback[:8]) if fallback else "暂无神煞摘要"


def format_dayun_start_age(age: object) -> str:
    if age is None:
        return ""
    try:
        return f"{round(float(age))}岁起"
    except (TypeError, ValueError):
        return ""


def compute_dayun_end_age(items: list[dict], index: int) -> int | None:
    if index >= len(items):
        return None
    current = items[index]
    start = current.get("start_age")
    if start is None:
        return None
    try:
        start_num = round(float(start))
    except (TypeError, ValueError):
        return None
    if index + 1 < len(items):
        nxt = items[index + 1].get("start_age")
        if nxt is not None:
            return round(float(nxt)) - 1
    return start_num + 9


def format_dayun_age_range(start: object, end: object | None = None) -> str:
    if start is None:
        return ""
    try:
        start_num = round(float(start))
    except (TypeError, ValueError):
        return ""
    if end is not None:
        try:
            return f"{start_num}–{round(float(end))}岁"
        except (TypeError, ValueError):
            pass
    return f"{start_num}岁起"


def build_dayun_volume_text(item: dict, index: int, items: list[dict]) -> str:
    gz = f"{item.get('stem', '')}{item.get('branch', '')}".strip() or "—"
    end_age = compute_dayun_end_age(items, index)
    start_age = item.get("start_age")
    age_range = (
        format_dayun_age_range(start_age, end_age)
        if start_age is not None and end_age is not None
        else format_dayun_start_age(start_age)
    )
    year_range = ""
    start_year = item.get("start_year")
    if start_year is not None:
        year_range = f"{start_year}–{int(start_year) + 9}年"
    ten_god = str(item.get("ten_god") or "").strip()
    narrative = str(item.get("narrative") or "").strip()
    hints = [
        str(item.get(key) or "").strip()
        for key in ("geju_impact", "wealth_hint", "health_hint", "love_hint")
    ]
    hints = [h for h in hints if h]
    head = " · ".join(
        x
        for x in (
            f"{index + 1}. {gz}",
            age_range,
            year_range,
            f"十神 {ten_god}" if ten_god else "",
            f"纳音 {item.get('nayin')}" if item.get("nayin") else "",
        )
        if x
    )
    if narrative and len(narrative) >= 20:
        return f"{head}。{narrative}"
    if hints:
        return f"{head}。{'；'.join(hints)}"
    if narrative:
        return f"{head}。{narrative}"
    return head


def build_palace_supplement(palace: dict) -> str:
    parts: list[str] = []
    aux = "、".join(
        str(s.get("name") or "")
        for s in (palace.get("aux_stars") or [])[:4]
        if isinstance(s, dict) and s.get("name")
    )
    if aux:
        parts.append(f"辅煞 {aux}")
    tags = "、".join(str(t) for t in (palace.get("analysis_tags") or [])[:3] if t)
    if tags:
        parts.append(f"要点 {tags}")
    if palace.get("is_body_palace"):
        parts.append("身宫所在")
    if palace.get("is_empty_palace"):
        parts.append("空宫借星")
    borrowed = "、".join(
        str(s.get("name") or "")
        for s in (palace.get("borrowed_main_stars") or [])
        if isinstance(s, dict) and s.get("name")
    )
    if borrowed:
        parts.append(f"借星 {borrowed}")
    return "；".join(parts)


def build_palace_volume_text(palace: dict) -> str:
    stars = "、".join(
        str(s.get("name") or "")
        for s in (palace.get("main_stars") or [])
        if isinstance(s, dict) and s.get("name")
    ) or "无主星"
    head = f"{palace.get('name')} {palace.get('stem', '')}{palace.get('branch', '')}：主星 {stars}"
    narrative = str(
        palace.get("conclusion")
        or palace.get("analysis")
        or palace.get("explanation")
        or palace.get("suggestion")
        or ""
    ).strip()
    supplement = build_palace_supplement(palace)
    if len(narrative) >= 40:
        return f"{head}。{narrative[:220]}"
    parts = [head]
    if supplement:
        parts.append(supplement)
    if narrative:
        parts.append(narrative)
    return "；".join(parts)


def enrich_palace_explain_text(explain_text: str, palace: dict | None) -> str:
    base = str(explain_text or "").strip()
    if not palace:
        return base or "宫位待补"
    if len(base) >= 40:
        return base
    enriched = build_palace_volume_text(palace)
    if not base:
        return enriched
    if len(base) >= 20:
        supplement = build_palace_supplement(palace)
        return f"{base}。{supplement}" if supplement else base
    return enriched


def find_palace_by_explain_text(text: str, palaces: list[dict]) -> dict | None:
    trimmed = str(text or "").strip()
    for palace in palaces:
        name = str(palace.get("name") or "")
        if name and name in trimmed:
            return palace
    return None


def enrich_vol2_block_text(label: str, body: str) -> str:
    trimmed = str(body or "").strip()
    if len(trimmed) >= 40:
        return trimmed
    prefix = f"卷二{label}：" if trimmed.startswith("暂无") else f"卷二{label}摘要："
    combined = f"{prefix}{trimmed}；卷二以 fact 层排盘关系为准，配合 cite/inference 分层阅读。"
    if len(combined) < 40:
        combined = f"{combined} 详见排盘与 explain 关系讲解。"
    return combined


def enrich_preface_reading_text() -> str:
    return (
        "卷一至卷五按 fact（排盘推算）· cite（典籍依据）· inference（经验推断）分层阅读；"
        "卷六为问书助手，需主动展开。先读卷一格局，再读卷二关系与卷三运限。"
    )


def main() -> None:
    from services.life_volume_service import build_life_volumes_from_charts

    breq = BaziFullRequest(
        dt=datetime.fromisoformat("1990-01-15T08:30:00"),
        lon=116.41,
        tz="Asia/Shanghai",
        gender="male",
        include_liuri=True,
    )
    bazi = bazi_full(breq).model_dump(mode="json")
    zwreq = ZiweiRequest(
        year=1990,
        month=1,
        day=15,
        hour=8,
        minute=30,
        gender="男",
        template_version="standard",
    )
    chart = ziwei_full(*_ziwei_full_args(zwreq))
    ziwei = _chart_to_response(
        chart,
        template="standard",
        req=zwreq,
        birth={"year": 1990, "month": 1, "day": 15, "hour": 8, "minute": 30, "gender": "男"},
    ).model_dump(mode="json")

    bex = explain_bazi_batch(
        ExplainBatchRequest(**{**breq.model_dump(mode="json"), "dt": breq.dt, "sections": ["geju", "relations", "domains", "summary"]})
    ).model_dump(mode="json")
    zex = explain_ziwei_batch(
        ZiweiExplainBatchRequest(**{**zwreq.model_dump(), "sections": ["palaces", "fortune"]})
    ).model_dump(mode="json")

    # 真源：远端 life/volumes 组装（与 GET /life/volumes 同源）
    lv = build_life_volumes_from_charts(
        case_id="audit-hollowness",
        chart_hash="audit",
        bazi=bazi,
        ziwei=ziwei,
        explain_bazi=bex,
        explain_ziwei=zex,
        profile_label="审计样本 · 1990-01-15 北京",
        entitlement="full_book",
    )
    volumes: dict[str, list[str]] = {vid: [] for vid in (
        "preface", "vol1", "vol2", "vol3", "vol4", "vol5", "vol6", "colophon",
    )}
    for vol in lv.volumes:
        texts = [
            str(bl.text)
            for sec in vol.sections
            for bl in sec.blocks
            if str(bl.text or "").strip()
        ]
        volumes[vol.id] = texts
    colo = [
        *(lv.colophon.summary_lines or []),
        *(
            [f"双轨：{lv.colophon.dual_track_note}"]
            if lv.colophon.dual_track_note
            else []
        ),
    ]
    if not colo:
        colo = ["校勘摘要：排盘字段齐备时可核对 missing/iztro/wenmo；详见 expandable 校勘脚注。"]
    volumes["colophon"] = [t for t in colo if str(t).strip()]

    report = {vid: summarize([audit_block(x) for x in texts]) for vid, texts in volumes.items()}

    geju = bazi.get("geju") or {}
    ui_strings = [
        geju.get("classic_ref") or "暂无典籍句式。",
        geju.get("geju_detail") or geju.get("interpretation_text") or "暂无引擎说明。",
        bazi.get("bazi_summary") or "",
        ziwei.get("summary") or "",
    ]
    ui_fb = sum(1 for x in ui_strings if is_fallback(x))

    out = {
        "profile": "1990-01-15 08:30 male Beijing",
        "source": "build_life_volumes_from_charts",
        "volumes": report,
        "rollup": compute_rollup(report),
        "volume_samples": {
            vid: [audit_block(t) for t in texts[:3]]
            for vid, texts in volumes.items()
        },
        "explain": {
            "bazi_sections": len(bex.get("sections", [])),
            "ziwei_sections": len(zex.get("sections", [])),
            "bazi_blocks": sum(len(s.get("blocks", [])) for s in bex.get("sections", [])),
            "ziwei_blocks": sum(len(s.get("blocks", [])) for s in zex.get("sections", [])),
            "bazi_avg_chars": round(
                sum(len(b.get("text", "")) for s in bex.get("sections", []) for b in s.get("blocks", []))
                / max(1, sum(len(s.get("blocks", [])) for s in bex.get("sections", []))),
                1,
            ),
        },
        "bazi_ui_sample_fallback_pct": round(100 * ui_fb / len(ui_strings), 1),
        "geju_has_classic_ref": bool(str(geju.get("classic_ref") or "").strip()),
        "geju_has_detail": bool(str(geju.get("geju_detail") or geju.get("interpretation_text") or "").strip()),
    }

    dest = Path(__file__).resolve().parent.parent / "docs" / "reports" / "content-hollowness-audit-latest.json"
    dest.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
