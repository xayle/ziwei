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
    "缺失",
    "暂无",
    "—",
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
    if len(t) <= 2 and t in ("—", "-", "…"):
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


def main() -> None:
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

    geju = bazi.get("geju") or {}
    day = (bazi.get("pillars_primary") or {}).get("day") or {}
    y = bazi.get("yongshen") or {}

    vol1: list[str] = [
        f"日主 {day.get('stem', '—')}{day.get('branch', '—')}；格局 {geju.get('geju_name', '待分析')}。",
    ]
    if geju.get("geju_detail") or geju.get("interpretation_text"):
        vol1.append(geju.get("geju_detail") or geju.get("interpretation_text") or "")
    if geju.get("classic_ref"):
        vol1.append(str(geju.get("classic_ref")))
    if y.get("favor") or y.get("avoid"):
        vol1.append(f"喜用 {'、'.join(y.get('favor') or []) or '—'}；忌 {'、'.join(y.get('avoid') or []) or '—'}")
    if bazi.get("bazi_summary"):
        vol1.append(str(bazi.get("bazi_summary")))
    for sec in bex.get("sections", []):
        for bl in sec.get("blocks", []):
            vol1.append(str(bl.get("text", ""))[:320])

    rels = bazi.get("relations") or []
    rel_line = "；".join(f"{r.get('type', '')} {r.get('subject', '')}" for r in rels[:6]) or "暂无干支关系摘要"
    ss = bazi.get("shensha_summary") or {}
    if isinstance(ss, dict):
        raw_names = ss.get("highlight_names") or ss.get("items") or []
        names = [x if isinstance(x, str) else x.get("name", "") for x in raw_names]
        ss_line = "、".join(n for n in names if n) or "暂无神煞摘要"
    else:
        ss_line = str(ss) or "暂无神煞摘要"
    vol2 = [rel_line, ss_line]
    for sec in bex.get("sections", []):
        if sec.get("section_id") == "relations":
            for bl in sec.get("blocks", []):
                vol2.append(str(bl.get("text", "")))

    vol3: list[str] = []
    items = (bazi.get("dayun") or {}).get("items") or (bazi.get("dayun") or {}).get("cycles") or []
    for i, item in enumerate(items[:8]):
        gz = f"{item.get('stem', '')}{item.get('branch', '')}".strip() or "—"
        age = item.get("start_age")
        vol3.append(f"{i + 1}. {gz} {f'{age}岁起' if age is not None else ''}".strip())
    zitems = (ziwei.get("dayun") or {}).get("items") or []
    if zitems:
        vol3.append(f"共 {len(zitems)} 步大运（列表数据）。")

    vol4: list[str] = []
    for sec in zex.get("sections", []):
        for bl in sec.get("blocks", []):
            vol4.append(str(bl.get("text", "")))
    if not vol4:
        vol4.append(
            f"五行局 {ziwei.get('wuxing_ju_name', '—')}；命宫 {ziwei.get('life_palace_gz', '—')}；身宫 {ziwei.get('body_palace_gz', '—')}"
        )
        for p in (ziwei.get("palaces") or [])[:6]:
            stars = "、".join(s.get("name", "") for s in p.get("main_stars") or []) or "无主星"
            vol4.append(f"{p.get('name')} {p.get('stem', '')}{p.get('branch', '')}：{stars}")

    vol5: list[str] = []
    for sec in bex.get("sections", []):
        if sec.get("section_id") == "domains":
            for bl in sec.get("blocks", []):
                vol5.append(str(bl.get("text", "")))
    if not vol5:
        for key, mod_key in [
            ("personality", "personality"),
            ("career", "career"),
            ("wealth", "wealth"),
            ("marriage", "marriage_analysis"),
            ("health", "health"),
            ("relationship", "relationship"),
        ]:
            m = bazi.get(mod_key) or bazi.get(key)
            if isinstance(m, dict):
                vol5.append(str(m.get("interpretation_text") or m.get("development_advice") or m.get("strategy") or "")[:80])

    volumes = {
        "preface": ["卷一至卷五按 fact·cite·inference 分层阅读。"],
        "vol1": vol1,
        "vol2": vol2,
        "vol3": vol3,
        "vol4": vol4,
        "vol5": vol5,
        "vol6": ["卷六需主动展开后提问；打磨期不自动调用 LLM。"],
        "colophon": ["校勘摘要（missing/iztro/wenmo）"],
    }

    report = {vid: summarize([audit_block(x) for x in texts]) for vid, texts in volumes.items()}

    ui_strings = [
        geju.get("classic_ref") or "暂无典籍句式。",
        geju.get("geju_detail") or geju.get("interpretation_text") or "暂无引擎说明。",
        bazi.get("bazi_summary") or "",
        ziwei.get("summary") or "",
    ]
    ui_fb = sum(1 for x in ui_strings if is_fallback(x))

    out = {
        "profile": "1990-01-15 08:30 male Beijing",
        "volumes": report,
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
        "geju_has_classic_ref": bool(geju.get("classic_ref", "").strip()),
        "geju_has_detail": bool((geju.get("geju_detail") or geju.get("interpretation_text") or "").strip()),
    }

    dest = Path(__file__).resolve().parent.parent / "docs" / "reports" / "content-hollowness-audit-latest.json"
    dest.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
