"""浮生报告 — 聚合排盘数据并渲染可打印 HTML。"""

from __future__ import annotations

import asyncio
from datetime import datetime
from html import escape
from typing import Any

from app.schemas.bazi import BaziFullRequest
from app.schemas.explain import ExplainBatchRequest, ZiweiExplainBatchRequest
from app.schemas.fusheng_report import FushengReportPdfRequest
from app.schemas.ziwei import ZiweiRequest
from routers.ziwei import _chart_to_response, _ziwei_full_args
from services.bazi_full_service import bazi_full
from services.explain_service import explain_bazi_batch, explain_ziwei_batch
from services.missing_field_labels import (
    confidence_level_label,
    format_crosscheck_status_label,
    format_validation_level_label,
    is_advisory_missing_field,
    missing_field_label,
    provenance_domain_label,
    provenance_layer_label,
    sanitize_user_facing_text,
)
from services.name_engine.engine import analyze_name
from services.ziwei_engine import ziwei_full

_EXPLAIN_SECTION_TITLES = {
    "geju": "格局解读",
    "relations": "关系解读",
    "summary": "综合解读",
    "palaces": "宫位解读",
    "fortune": "运限解读",
}

_ELEMENT_CN = {
    "metal": "金",
    "wood": "木",
    "water": "水",
    "fire": "火",
    "earth": "土",
}


def _esc(value: Any) -> str:
    return escape(str(value if value is not None else ""))


def _parse_birth_dt(raw: str) -> datetime:
    text = raw.strip()
    if len(text) == 16:
        text = f"{text}:00"
    return datetime.fromisoformat(text)


def _to_cn_elements(values: list[str] | None) -> list[str]:
    out: list[str] = []
    for value in values or []:
        key = value.strip().lower()
        out.append(_ELEMENT_CN.get(key, value))
    return out


def _build_name_cross_note(name: dict[str, Any], bazi: dict[str, Any]) -> str:
    ys = bazi.get("yongshen") or {}
    favor = set(_to_cn_elements(ys.get("favor")))
    avoid = set(_to_cn_elements(ys.get("avoid")))
    renke = ((name.get("renke") or {}).get("element")) or ""
    if not favor:
        return "八字用神未明确，姓名五行对照仅供参考。"
    if renke in favor:
        return f"人格「{renke}」与喜用「{'、'.join(favor)}」相合。"
    if renke in avoid:
        return f"人格「{renke}」落入忌避「{'、'.join(avoid)}」，宜结合后天调候。"
    return "姓名五行与八字喜用部分呼应，建议综合人格、地格取舍。"


def _format_birth_human(birth_dt: str, city_name: str | None, precision: str | None) -> str:
    prec = (precision or "exact").strip()
    try:
        dt = _parse_birth_dt(birth_dt)
        if prec == "unknown":
            base = f"{dt.year}年{dt.month}月{dt.day}日（时辰未知）"
        elif prec in {"hour", "approximate"}:
            base = f"{dt.year}年{dt.month}月{dt.day}日 {dt.hour:02d}时"
        else:
            base = f"{dt.year}年{dt.month}月{dt.day}日 {dt.hour:02d}:{dt.minute:02d}"
    except Exception:
        base = str(birth_dt or "").replace("T", " ").strip() or "生辰未填"
    city = (city_name or "").strip()
    return f"{base}（{city}）" if city else base


def _has_dual_track_content(bazi: dict[str, Any], ziwei: dict[str, Any]) -> bool:
    geju = bazi.get("geju") or {}
    recorded = str(geju.get("recorded_geju") or geju.get("recorded_geju_name") or "").strip()
    engine = str(geju.get("engine_geju") or geju.get("geju_name") or "").strip()
    dual_id = str(geju.get("dual_track_id") or bazi.get("dual_track_id") or "").strip()
    note = str(geju.get("dual_track_note") or bazi.get("dual_track_note") or "").strip()
    if note and note != "—":
        return True
    if dual_id and dual_id != "—":
        return True
    if recorded and engine and recorded != engine:
        return True
    # 紫微双轨有对照才算有内容（单纯命宫干支不算「双轨附录」）
    cc = ziwei.get("iztro_crosscheck") or {}
    if isinstance(cc, dict) and cc.get("dual_track"):
        return True
    return False


def _wuxing_line(bazi: dict[str, Any]) -> str:
    score = bazi.get("wuxing_score") or {}
    if isinstance(score, dict) and score:
        order = (("wood", "木"), ("fire", "火"), ("earth", "土"), ("metal", "金"), ("water", "水"))
        bits = []
        for key, label in order:
            val = score.get(key)
            if val is None:
                val = score.get(label)
            if val is not None:
                bits.append(f"{label}{val}")
        if bits:
            return " · ".join(bits)
    breakdown = bazi.get("wuxing_breakdown") or {}
    if isinstance(breakdown, dict) and breakdown:
        bits = [f"{k}{v}" for k, v in breakdown.items() if v is not None]
        if bits:
            return " · ".join(bits[:5])
    return ""


def _render_closing_section(bazi: dict[str, Any], ziwei: dict[str, Any], meta: dict[str, Any]) -> str:
    """综合总结：行动建议 + 本年焦点 + 回看索引（付费收据）。"""
    from services.fusheng_report_paid_bridges import closing_rich_html

    return closing_rich_html(bazi, ziwei, meta)


async def build_fusheng_report_payload(req: FushengReportPdfRequest) -> dict[str, Any]:
    birth = _parse_birth_dt(req.birth_dt)
    gender = req.gender or "male"

    bazi_req = BaziFullRequest(
        dt=birth,
        lon=req.lon,
        tz=req.tz,
        mode=req.mode,
        solar_time_enabled=req.solar_time_enabled,
        gender=gender,
        include_liuri=req.include_liuri,
        zi_day_rule=req.zi_day_rule,
        birth_time_precision=req.birth_time_precision,
    )
    bazi_resp = bazi_full(bazi_req)
    bazi = bazi_resp.model_dump(mode="json")

    ziwei_req = ZiweiRequest(
        year=birth.year,
        month=birth.month,
        day=birth.day,
        hour=birth.hour,
        minute=birth.minute,
        gender="女" if gender == "female" else "男",
        longitude=req.lon if req.solar_time_enabled else None,
        leap_month_method="same" if req.is_leap_month else "mid",
        year_divide=req.year_divide,
        day_divide=req.day_divide,
        late_zishi=req.late_zishi,
    )
    chart = await asyncio.to_thread(ziwei_full, *_ziwei_full_args(ziwei_req))
    ziwei = _chart_to_response(
        chart,
        template=ziwei_req.template_version,
        req=ziwei_req,
        birth={
            "year": ziwei_req.year,
            "month": ziwei_req.month,
            "day": ziwei_req.day,
            "hour": ziwei_req.hour,
            "minute": ziwei_req.minute or 0,
            "gender": ziwei_req.gender,
            "year_divide": ziwei_req.year_divide,
            "day_divide": ziwei_req.day_divide,
        },
    ).model_dump(mode="json")

    name: dict[str, Any] | None = None
    if req.surname.strip() and req.given_name.strip():
        result = analyze_name(req.surname.strip(), req.given_name.strip())
        name = {
            "surname": result.surname,
            "given_name": result.given_name,
            "overall_score": result.overall_score,
            "summary": result.summary,
            "sancai": {
                "pattern": result.sancai.pattern,
                "lucky": result.sancai.lucky,
                "desc": result.sancai.desc,
            },
            "tianke": result.tianke.__dict__,
            "renke": result.renke.__dict__,
            "dike": result.dike.__dict__,
            "waike": result.waike.__dict__,
            "zonge": result.zonge.__dict__,
        }

    explain_bazi = explain_bazi_batch(
        ExplainBatchRequest(**bazi_req.model_dump(), sections=["geju", "relations", "summary"]),
    ).model_dump(mode="json")
    explain_ziwei = explain_ziwei_batch(
        ZiweiExplainBatchRequest(**ziwei_req.model_dump(), sections=["palaces", "fortune"]),
    ).model_dump(mode="json")

    return {
        "meta": {
            "label": req.label,
            "birth_dt": req.birth_dt,
            "city_name": req.city_name,
            "calendar_mode": req.calendar_mode,
            "focus_topic": req.focus_topic,
            "notes": req.notes,
            "year_divide": req.year_divide,
            "day_divide": req.day_divide,
            "zi_day_rule": req.zi_day_rule,
            "late_zishi": req.late_zishi,
            "birth_time_precision": req.birth_time_precision,
            "unknown_time_fallback": req.unknown_time_fallback,
            "generated_at": datetime.now().isoformat(timespec="seconds"),
        },
        "bazi": bazi,
        "ziwei": ziwei,
        "name": name,
        "explain_bazi": explain_bazi,
        "explain_ziwei": explain_ziwei,
    }


def _dual_track_empty_note(bazi: dict[str, Any]) -> str:
    geju = bazi.get("geju") or {}
    engine_name = geju.get("engine_geju") or geju.get("geju_name") or "—"
    return f"本命暂无古籍双轨样例；引擎主盘格局为「{engine_name}」。"


def _render_dual_track_appendix(bazi: dict[str, Any], ziwei: dict[str, Any]) -> str:
    """双轨对照附录：有内容才单独成页；空态不占页（并入基础档案一行）。"""
    if not _has_dual_track_content(bazi, ziwei):
        return ""
    geju = bazi.get("geju") or {}
    engine_name = geju.get("engine_geju") or geju.get("geju_name") or "—"
    recorded = geju.get("recorded_geju") or geju.get("recorded_geju_name") or "—"
    dual_id = geju.get("dual_track_id") or bazi.get("dual_track_id") or "—"
    note = geju.get("dual_track_note") or bazi.get("dual_track_note") or "—"
    rows = [
        ("八字格局", _esc(recorded), _esc(engine_name), _esc(sanitize_user_facing_text(note))),
        (
            "紫微命宫",
            "—",
            _esc(ziwei.get("life_palace_gz") or "—"),
            _esc(ziwei.get("wuxing_ju_name") or "—"),
        ),
        (
            "双轨档案",
            _esc(dual_id),
            "—",
            "ZIP/ZW 交叉索引",
        ),
    ]
    body = "".join(f"<tr><td>{dim}</td><td>{rec}</td><td>{eng}</td><td>{nt}</td></tr>" for dim, rec, eng, nt in rows)
    return (
        "<section class='page'><h2>双轨对照附录</h2>"
        "<table><thead><tr><th>维度</th><th>古籍/档案</th><th>引擎</th><th>备注</th></tr></thead>"
        f"<tbody>{body}</tbody></table></section>"
    )


_STEM_COLORS = {
    "甲": "#3d6b48",
    "乙": "#4a7a54",
    "丙": "#9a4a38",
    "丁": "#a65a42",
    "戊": "#7a6348",
    "己": "#8b7354",
    "庚": "#8b6924",
    "辛": "#9a7830",
    "壬": "#3d5a78",
    "癸": "#4a6890",
}
_BRANCH_COLORS = {
    "子": "#4a6890",
    "丑": "#8b7354",
    "寅": "#3d6b48",
    "卯": "#4a7a54",
    "辰": "#7a6348",
    "巳": "#a65a42",
    "午": "#9a4a38",
    "未": "#8b7354",
    "申": "#9a7830",
    "酉": "#8b6924",
    "戌": "#7a6348",
    "亥": "#3d5a78",
}


def _format_hidden_stems_html(hidden: list[Any] | None) -> str:
    bits: list[str] = []
    for item in hidden or []:
        if not isinstance(item, dict):
            continue
        stem = str(item.get("stem") or "").strip()
        if not stem:
            continue
        tg = str(item.get("ten_god") or "").strip()
        color = _STEM_COLORS.get(stem, "#2b2118")
        label = f"{stem}<span class='tg'>{_esc(tg)}</span>" if tg else stem
        bits.append(f"<span class='hid' style='color:{color}'>{label}</span>")
    return "<br/>".join(bits) if bits else "—"


def _format_kongwang(kongwang: Any) -> str:
    if not isinstance(kongwang, list) or not kongwang:
        return "—"
    items = [str(x).strip() for x in kongwang if str(x).strip()]
    return "、".join(dict.fromkeys(items)) if items else "—"


def _format_shensha_active(items: list[Any] | None) -> str:
    """只印亮起的神煞，不做灰名单占版。"""
    seen: set[str] = set()
    bits: list[str] = []
    for item in items or []:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name") or "").strip()
        if not name or name in seen or name == "缺失":
            continue
        seen.add(name)
        pol = str(item.get("polarity") or "").strip()
        cls = "ss-good" if pol == "+" else "ss-warn" if pol == "-" else "ss-neutral"
        bits.append(f"<span class='ss {cls}'>{_esc(name)}</span>")
    return "<br/>".join(bits) if bits else "—"


def _glyph(ch: str, *, kind: str = "stem") -> str:
    text = str(ch or "").strip() or "—"
    if text == "—":
        return text
    palette = _STEM_COLORS if kind == "stem" else _BRANCH_COLORS
    color = palette.get(text, "#2b2118")
    return f"<span class='glyph' style='color:{color}'>{_esc(text)}</span>"


def _find_current_dayun(bazi: dict[str, Any], year: int) -> dict[str, Any]:
    items = (bazi.get("dayun") or {}).get("items") or (bazi.get("dayun") or {}).get("cycles") or []
    for item in items:
        if not isinstance(item, dict):
            continue
        start = item.get("start_year")
        if isinstance(start, int) and start <= year <= start + 9:
            return item
    return items[0] if items and isinstance(items[0], dict) else {}


def _find_current_liunian(bazi: dict[str, Any], year: int) -> dict[str, Any]:
    for item in (bazi.get("liunian") or {}).get("items") or []:
        if isinstance(item, dict) and int(item.get("year") or 0) == year:
            return item
    return {}


def _chart_column_from_detail(
    *,
    key: str,
    label: str,
    main_star: str,
    detail: dict[str, Any],
    fallback_stem: str = "",
    fallback_branch: str = "",
) -> dict[str, Any]:
    stem = str(detail.get("stem") or fallback_stem or "").strip()
    branch = str(detail.get("branch") or fallback_branch or "").strip()
    return {
        "key": key,
        "label": label,
        "main_star": main_star or "—",
        "stem": stem or "—",
        "branch": branch or "—",
        "hidden_html": _format_hidden_stems_html(detail.get("hidden_stems")),
        "xingyun": str(detail.get("xingyun") or "—"),
        "self_seat": str(detail.get("self_seat") or "—"),
        "void": _format_kongwang(detail.get("kongwang")),
        "nayin": str(detail.get("nayin") or "—"),
        "shensha_html": _format_shensha_active(detail.get("shensha")),
    }


def _build_bazi_chart_columns(bazi: dict[str, Any], current_year: int | None = None) -> list[dict[str, Any]]:
    """对齐站内 buildBaziColumns：流年/大运/四柱。"""
    year = current_year or datetime.now().year
    details = bazi.get("pillar_details") if isinstance(bazi.get("pillar_details"), dict) else {}
    pillars = bazi.get("pillars_primary") or {}
    ten_gods = bazi.get("ten_gods") or {}
    liunian = _find_current_liunian(bazi, year)
    dayun = _find_current_dayun(bazi, year)

    def pillar(key: str, label: str, star: str) -> dict[str, Any]:
        d = details.get(key) if isinstance(details.get(key), dict) else {}
        p = pillars.get(key) if isinstance(pillars.get(key), dict) else {}
        return _chart_column_from_detail(
            key=key,
            label=label,
            main_star=star,
            detail=d,
            fallback_stem=str(p.get("stem") or ""),
            fallback_branch=str(p.get("branch") or ""),
        )

    return [
        _chart_column_from_detail(
            key="liunian",
            label=f"流年·{year}",
            main_star=str(liunian.get("ten_god") or "—"),
            detail=liunian,
        ),
        _chart_column_from_detail(
            key="dayun",
            label="大运",
            main_star=str(dayun.get("ten_god") or "—"),
            detail=dayun,
        ),
        pillar("year", "年柱", str(ten_gods.get("year") or "—")),
        pillar("month", "月柱", str(ten_gods.get("month") or "—")),
        pillar("day", "日柱", "日主"),
        pillar("hour", "时柱", str(ten_gods.get("hour") or "—")),
    ]


def _render_pillars_overview_table(bazi: dict[str, Any]) -> str:
    """八字满盘：流年/大运/四柱 × 主星·干·支·藏干·星运·自坐·空亡·纳音·神煞。"""
    cols = _build_bazi_chart_columns(bazi)
    header = (
        "<tr><th class='row-label'>项目</th>"
        + "".join(f"<th class='col-{c['key']}'>{_esc(c['label'])}</th>" for c in cols)
        + "</tr>"
    )

    def cells(render) -> str:
        return "".join(f"<td class='col-{c['key']}'>{render(c)}</td>" for c in cols)

    rows = [
        ("主星", lambda c: _esc(c["main_star"])),
        ("天干", lambda c: _glyph(c["stem"], kind="stem")),
        ("地支", lambda c: _glyph(c["branch"], kind="branch")),
        ("藏干", lambda c: c["hidden_html"]),
        ("星运", lambda c: _esc(c["xingyun"])),
        ("自坐", lambda c: _esc(c["self_seat"])),
        ("空亡", lambda c: _esc(c["void"])),
        ("纳音", lambda c: _esc(c["nayin"])),
        ("神煞", lambda c: c["shensha_html"]),
    ]
    body = "".join(
        f"<tr class='row-{idx}'><td class='row-label'>{label}</td>{cells(fn)}</tr>"
        for idx, (label, fn) in enumerate(rows)
    )
    from services.fusheng_report_paid_bridges import chart_row_legend_html

    return (
        "<p class='chart-legend'>核心顺序：流年 / 大运 / 年柱 / 月柱 / 日柱 / 时柱 · 神煞仅示亮起项 · 日柱为身</p>"
        f"{chart_row_legend_html()}"
        f"<table class='bazi-chart'><thead>{header}</thead><tbody>{body}</tbody></table>"
    )


def _compress_archive_summary(raw: str) -> str:
    """压缩基础档案复读：去综合收束，主线不重复用神句，段间去重。"""
    text = sanitize_user_facing_text(raw or "").strip()
    if not text:
        return ""
    import re

    # 按【标题】切段，保序
    parts = re.split(r"(【[^】]+】)", text)
    sections: list[tuple[str, str]] = []
    i = 0
    while i < len(parts):
        chunk = parts[i]
        if chunk.startswith("【") and chunk.endswith("】") and i + 1 < len(parts):
            sections.append((chunk, parts[i + 1].strip()))
            i += 2
        else:
            if chunk.strip():
                sections.append(("", chunk.strip()))
            i += 1

    drop_titles = {"【综合收束】", "【综合总结】"}
    out: list[str] = []
    seen_bodies: set[str] = set()
    for title, body in sections:
        if title in drop_titles:
            continue
        body = re.sub(r"（仅供学术研究参考[^）]*）\s*$", "", body).strip()
        if title == "【人生主线建议】":
            body = re.sub(r"^用神为[^，。]+，忌神为[^。]+。\s*", "", body)
        # 格局段若已含「以用神「…」为准」且与总评重复用神，保留制化说明即可
        key = re.sub(r"\s+", "", f"{title}{body}")
        if not key or key in seen_bodies:
            continue
        seen_bodies.add(key)
        out.append(f"{title}{body}" if title else body)

    # 若仍过长，只保留前四段
    if len(out) > 4:
        out = out[:4]
    brief = "".join(out).strip()
    if brief and not brief.endswith(("。", "）", ")")):
        brief += "。"
    if brief and "仅供" not in brief[-40:]:
        brief += "（仅供学术研究参考，不构成任何形式的预测或建议）"
    return brief


def _render_explain_section(
    explain_bazi: dict[str, Any] | None,
    explain_ziwei: dict[str, Any] | None,
) -> str:
    """解读裁剪：八字保留格局+关系；紫微宫位限流；去与档案复读的综合段。"""
    parts: list[str] = []
    for label, explain, keep in (
        ("八字", explain_bazi, {"geju", "relations"}),
        ("紫微", explain_ziwei, {"palaces"}),
    ):
        if not explain:
            continue
        for section in explain.get("sections") or []:
            if not isinstance(section, dict):
                continue
            sid = str(section.get("section_id") or "")
            if keep is not None and sid not in keep:
                continue
            title = _EXPLAIN_SECTION_TITLES.get(sid, sid)
            blocks = section.get("blocks") or []
            if not blocks:
                continue
            texts = [str(block.get("text") or "") for block in blocks if isinstance(block, dict) and block.get("text")]
            if sid == "palaces":
                # 命宫优先，其余最多再留 3 段
                preferred = [t for t in texts if t.startswith("命宫")]
                rest = [t for t in texts if not t.startswith("命宫")]
                texts = (preferred[:1] + rest)[:4]
            block_html = "".join(f"<p class='explain-fact'>{_esc(t)}</p>" for t in texts)
            parts.append(f"<h3>{_esc(label)} · {_esc(title)}</h3>{block_html}")

    # 运限：只留当前相关短句
    if explain_ziwei:
        for section in explain_ziwei.get("sections") or []:
            if section.get("section_id") != "fortune":
                continue
            blocks = section.get("blocks") or []
            texts = [str(b.get("text") or "") for b in blocks if isinstance(b, dict) and b.get("text")][:2]
            if texts:
                block_html = "".join(f"<p>{_esc(t)}</p>" for t in texts)
                parts.append(f"<h3>紫微 · 运限要点</h3>{block_html}")

    disclaimer = (explain_bazi or explain_ziwei or {}).get("disclaimer_block") or {}
    disclaimer_text = disclaimer.get("text")
    if disclaimer_text:
        version = disclaimer.get("version", "")
        version_txt = f"（v{_esc(version)}）" if version else ""
        parts.append(f"<p class='meta disclaimer'>{_esc(disclaimer_text)}{version_txt}</p>")

    if not parts:
        return ""
    return f"<section class='page sheet'><h2>解读要点</h2>{''.join(parts)}</section>"


def _render_trust_section(bazi: dict[str, Any], ziwei: dict[str, Any]) -> str:
    """正文三行人读；百分比/长引降级「校勘附录」。"""
    head: list[str] = []
    appendix: list[str] = []

    cc = ziwei.get("iztro_crosscheck") or {}
    if cc:
        status_label = format_crosscheck_status_label(cc.get("status"))
        main_n = cc.get("main_match", "—")
        main_t = cc.get("main_total", "—")
        head.append(
            f"<p><strong>对照结论</strong>：{_esc(status_label)} · 主星一致数 {_esc(main_n)}/{_esc(main_t)}</p>"
        )
        advisory = sanitize_user_facing_text(cc.get("advisory"))
        if advisory:
            appendix.append(f"<p>{_esc(advisory)}</p>")

    if bazi.get("confidence_level"):
        level = confidence_level_label(str(bazi.get("confidence_level")))
        head.append(
            f"<p><strong>置信度</strong>：{_esc(level)} · "
            "本报告供文化研究与自我认知参考，不构成医疗、法律或投资建议。</p>"
        )

    validation = bazi.get("validation") or {}
    if validation.get("level"):
        level_label = format_validation_level_label(validation.get("level"))
        head.append(f"<p><strong>校验</strong>：{_esc(level_label)} · 部分条目为对照/启发式校勘。</p>")

    if len(head) < 3:
        geju = bazi.get("geju") or {}
        head.append(
            "<p><strong>格局口径</strong>："
            f"引擎 {_esc(geju.get('engine_geju') or geju.get('geju_name') or '—')} · "
            f"古籍 {_esc(geju.get('recorded_geju') or '—')}</p>"
        )

    missing = [
        f
        for f in dict.fromkeys((bazi.get("missing_fields") or []) + (ziwei.get("missing_fields") or []))
        if isinstance(f, str) and f.strip()
    ]
    if missing:
        labels = [missing_field_label(f) for f in missing]
        title = "对照注记" if all(is_advisory_missing_field(f) for f in missing) else "字段注记"
        appendix.append(f"<p><strong>{title}</strong>：{_esc('、'.join(labels))}</p>")

    prov_bits: list[str] = []
    for source, payload in (("八字", bazi.get("provenance") or {}), ("紫微", ziwei.get("provenance") or {})):
        if not isinstance(payload, dict):
            continue
        for key, layer in payload.items():
            if not isinstance(layer, dict) or not layer.get("layer"):
                continue
            conf = layer.get("confidence")
            conf_txt = f" {int(conf * 100)}%" if isinstance(conf, int | float) else ""
            domain = provenance_domain_label(str(key))
            layer_label = provenance_layer_label(str(layer.get("layer")))
            prov_bits.append(f"{source}·{domain}={layer_label}{conf_txt}")
    if prov_bits:
        appendix.append(f"<p><strong>可信度分层</strong>：{_esc(' · '.join(prov_bits[:8]))}</p>")

    for label, refs in (("八字", bazi.get("classic_refs") or []), ("紫微", ziwei.get("classic_refs") or [])):
        bits = [f"{c.get('category', '')}·{(c.get('text') or '')[:40]}" for c in refs[:3] if isinstance(c, dict)]
        if bits:
            appendix.append(f"<p><strong>{label}典籍提示</strong>：{_esc(' · '.join(bits))}</p>")

    warnings = [
        sanitize_user_facing_text(w) for w in (ziwei.get("engine_warnings") or []) if sanitize_user_facing_text(w)
    ]
    if warnings:
        appendix.append(f"<p><strong>引擎提示</strong>：{_esc('；'.join(warnings[:4]))}</p>")

    if not head and not appendix:
        return ""
    appendix_html = (
        f"<div class='trust-appendix'><p class='bridge-k'>校勘附录（选读）</p>{''.join(appendix)}</div>"
        if appendix
        else ""
    )
    return (
        "<section class='page sheet'><h2>校勘与可信度</h2>"
        f"<div class='trust-summary'>{''.join(head[:3])}</div>"
        f"{appendix_html}"
        "</section>"
    )


def render_fusheng_report_html(payload: dict[str, Any]) -> str:
    meta = payload["meta"]
    bazi = payload["bazi"]
    ziwei = payload["ziwei"]
    name = payload.get("name")

    dayun_items = ((bazi.get("dayun") or {}).get("items") or (bazi.get("dayun") or {}).get("cycles") or [])[:10]
    palaces = (ziwei.get("palaces") or [])[:12]
    ys = bazi.get("yongshen") or {}
    favor_cn = "、".join(_to_cn_elements(ys.get("favor"))) or "—"
    avoid_cn = "、".join(_to_cn_elements(ys.get("avoid"))) or "—"
    geju = bazi.get("geju") or {}
    geju_line = _esc(geju.get("geju_name", "—"))
    dual_bits: list[str] = []
    if geju.get("recorded_geju") and geju.get("recorded_geju") != geju.get("geju_name"):
        dual_bits.append(f"古籍口径：{_esc(geju.get('recorded_geju'))}")
    if geju.get("engine_geju") and geju.get("engine_geju") != geju.get("geju_name"):
        dual_bits.append(f"引擎：{_esc(geju.get('engine_geju'))}")
    if geju.get("derived_geju"):
        dual_bits.append(f"衍生格：{_esc(geju.get('derived_geju'))}")
    if geju.get("dual_track_note"):
        dual_bits.append(_esc(geju.get("dual_track_note")))
    dual_html = f"<p class='accent'>{' · '.join(dual_bits)}</p>" if dual_bits else ""
    year_divide_label = "正月初一换年" if meta.get("year_divide") == "normal" else "立春换年"
    day_divide_label = {
        "forward": "农历日+1安星",
        "current": "当日不换日",
    }.get(meta.get("day_divide") or "solar_next", "公历次日换日")
    late_zishi_label = "晚子时换日" if meta.get("late_zishi", True) else "晚子不换日"
    precision_labels = {
        "exact": "精确到分",
        "hour": "整点/时辰",
        "approximate": "约略时辰",
        "unknown": "时辰未详",
    }
    precision_label = precision_labels.get(meta.get("birth_time_precision") or "exact", "精确到分")
    fallback_labels = {
        "midday": "日中 12:30",
        "noon": "正午 12:00",
        "start_of_hour": "时辰起点",
    }
    fallback = meta.get("unknown_time_fallback")
    fallback_label = fallback_labels.get(fallback) if fallback else None
    zi_day_rule_labels = {
        "sxtwl": "库默认",
        "early_zi_prev_day": "早子算前一日",
        "early_zi_same_day": "早子仍算当日",
    }
    zi_day_rule_label = zi_day_rule_labels.get(
        str(meta.get("zi_day_rule") or "sxtwl"),
        str(meta.get("zi_day_rule") or "库默认"),
    )

    current_year = datetime.now().year
    current_dayun = _find_current_dayun(bazi, current_year)
    current_dayun_gz = f"{current_dayun.get('stem') or ''}{current_dayun.get('branch') or ''}"
    dayun_rows = "".join(
        (
            "<tr class='is-current'>"
            if (
                isinstance(item.get("start_year"), int)
                and item.get("start_year") <= current_year <= item.get("start_year") + 9
            )
            else "<tr>"
        )
        + f"<td>{_esc(item.get('start_year', '—'))}</td>"
        f"<td>{_esc((item.get('stem') or '') + (item.get('branch') or ''))}</td>"
        f"<td>{_esc(item.get('ten_god', '—'))}</td>"
        f"<td>{'当前步' if (isinstance(item.get('start_year'), int) and item.get('start_year') <= current_year <= item.get('start_year') + 9) else ''}</td>"
        "</tr>"
        for item in dayun_items
    )

    palace_rows = "".join(
        f"<tr><td>{_esc(p.get('name'))}</td>"
        f"<td>{_esc((p.get('stem') or '') + (p.get('branch') or ''))}</td>"
        f"<td>{_esc('、'.join(s.get('name', '') for s in (p.get('main_stars') or [])) or '无主星')}</td></tr>"
        for p in palaces
    )

    name_section = ""
    if name:
        grids = [
            ("天格", name["tianke"]),
            ("人格", name["renke"]),
            ("地格", name["dike"]),
            ("外格", name["waike"]),
            ("总格", name["zonge"]),
        ]
        grid_rows = "".join(
            f"<tr><td>{label}</td><td>{_esc(g.get('number'))}</td><td>{_esc(g.get('element'))}</td>"
            f"<td>{_esc(g.get('lucky'))}</td><td>{_esc(g.get('score'))}</td></tr>"
            for label, g in grids
        )
        cross = _build_name_cross_note(name, bazi)
        name_section = f"""
        <section class="page sheet">
          <h2>姓名分析</h2>
          <p>{_esc(name.get("summary"))}</p>
          <table class="ruled"><thead><tr><th>格局</th><th>数理</th><th>五行</th><th>吉凶</th><th>得分</th></tr></thead>
          <tbody>{grid_rows}</tbody></table>
          <p>三才：{_esc(name["sancai"]["pattern"])} · {_esc(name["sancai"]["lucky"])}</p>
          <p class="accent">{_esc(cross)}</p>
          <p class="meta">姓名五行与命局用神冲突时，宜后天调候（环境/节奏），勿改名恐吓。</p>
        </section>
        """

    notes_raw = str(meta.get("notes") or "").strip()
    notes_section = (
        f"<section class='page'><h2>人工批注区</h2><pre class='notes'>{_esc(notes_raw)}</pre></section>"
        if notes_raw
        else ""
    )
    from services.fusheng_report_paid_bridges import (
        dayun_bridge_html,
        flying_star_plain_html,
        geju_tension_block,
        how_to_read_book_html,
        liunian_bridge_html,
        relations_short_list_html,
        yongshen_lifestyle_line,
        ziwei_topic_cards_html,
    )

    trust_section = _render_trust_section(bazi, ziwei)
    dual_track_appendix = _render_dual_track_appendix(bazi, ziwei)
    explain_section = _render_explain_section(payload.get("explain_bazi"), payload.get("explain_ziwei"))
    closing_section = _render_closing_section(bazi, ziwei, meta)
    geju_block = geju_tension_block(bazi, payload.get("explain_bazi"))
    liunian_block = liunian_bridge_html(bazi, current_year)
    dayun_block = dayun_bridge_html(bazi, current_year)
    topic_block = ziwei_topic_cards_html(ziwei, bazi)
    flying_block = flying_star_plain_html()
    how_to_read = how_to_read_book_html()
    relations_block = relations_short_list_html(bazi)
    lifestyle_line = yongshen_lifestyle_line(bazi)
    short_name = _esc((meta.get("label") or "档案")[:12])

    birth_human = _format_birth_human(
        str(meta.get("birth_dt") or ""),
        meta.get("city_name"),
        meta.get("birth_time_precision"),
    )
    strength_tier = (bazi.get("day_master_strength") or {}).get("tier", "—")
    cover_mingju = f"格局 {geju.get('geju_name') or '—'} · 强弱 {strength_tier} · 用神 {favor_cn} · 忌神 {avoid_cn}"
    wuxing_line = _wuxing_line(bazi)
    wuxing_html = f"<p>五行：{_esc(wuxing_line)}</p>" if wuxing_line else ""
    focus = str(meta.get("focus_topic") or "").strip()
    focus_html = f" · 关注：{_esc(focus)}" if focus else ""
    show_fallback = bool(fallback_label and (meta.get("birth_time_precision") in {"unknown", "approximate"}))
    fallback_html = f" · 未知默认：{_esc(fallback_label)}" if show_fallback else ""
    life_one_liner = sanitize_user_facing_text(ziwei.get("summary") or "")
    if not life_one_liner:
        life_one_liner = (
            f"命宫 {_esc(ziwei.get('life_palace_gz', '—'))} · 五行局 {_esc(ziwei.get('wuxing_ju_name', '—'))}"
        )
    else:
        life_one_liner = _esc(life_one_liner)

    archive_summary = _compress_archive_summary(
        str(bazi.get("bazi_summary") or (bazi.get("geju") or {}).get("interpretation_text") or "")
    )
    dual_inline = ""
    if not _has_dual_track_content(bazi, ziwei):
        dual_inline = f"<p class='meta inline-note'>双轨：{_esc(_dual_track_empty_note(bazi))}</p>"
    pillars_table = _render_pillars_overview_table(bazi)
    cal_label = {"gregorian": "公历", "lunar": "农历"}.get(
        str(meta.get("calendar_mode") or ""), str(meta.get("calendar_mode") or "—")
    )

    from services.pdf_font_styles import pdf_body_font_family, pdf_song_font_face_css

    font_face_css = pdf_song_font_face_css()
    body_font = pdf_body_font_family()

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <title>{_esc(meta.get("label"))}</title>
  <style>
    {font_face_css}
    @page {{
      size: A4;
      margin: 14mm 13mm 16mm;
      @bottom-center {{
        content: "浮生 · 命理个人档案 · {short_name} · " counter(page);
        font-size: 9px; color: #6b5d4f;
      }}
    }}
    :root {{
      --ink: #1a1410; --paper: #f5f0e6; --surface: #fffaf5;
      --gold: #b8894d; --gold-lt: #f0e0c7; --mist: #6b5d4f;
      --border: #d9cfb8; --cinnabar: #8b3a2a;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      font-family: {body_font}; color: var(--ink); font-size: 11.5px; line-height: 1.7;
      background: var(--paper); margin: 0;
    }}
    h1 {{ font-size: 26px; margin: 0 0 8px; letter-spacing: 0.12em; font-weight: 600; }}
    h2 {{
      font-size: 14.5px; margin: 0 0 12px; color: #5c3d2e; font-weight: 600;
      border-bottom: 1px solid var(--gold); padding-bottom: 6px; letter-spacing: 0.14em;
    }}
    h3 {{ font-size: 12.5px; margin: 12px 0 6px; color: #5c3d2e; letter-spacing: 0.08em; }}
    .page {{ page-break-after: always; padding: 2px 0 8px; }}
    .page:last-child {{ page-break-after: auto; }}
    .sheet {{
      border: 1px solid var(--gold);
      box-shadow: inset 0 0 0 3px var(--surface), inset 0 0 0 4px var(--border);
      padding: 14px 16px 16px; background: linear-gradient(180deg, #faf6ef 0%, var(--paper) 100%);
      min-height: 240mm;
    }}
    .meta, .accent {{ color: var(--mist); }}
    .eyebrow {{ font-size: 10px; letter-spacing: 0.22em; color: var(--gold); }}
    table, table.ruled {{
      width: 100%; border-collapse: collapse; margin-top: 8px; background: var(--surface);
    }}
    th, td {{ border: 1px solid var(--border); padding: 5px 6px; text-align: left; vertical-align: top; }}
    th {{ background: #f3ebe0; color: #5c3d2e; font-weight: 600; }}
    tr.is-current td {{ background: #f7efe2; font-weight: 600; }}
    .notes {{ white-space: pre-wrap; background: var(--surface); padding: 12px; border: 1px solid var(--border); }}
    ol.closing, ol.tight, ul.tight {{ margin: 8px 0 10px 1.2em; padding: 0; }}
    ol.closing li, ol.tight li, ul.tight li {{ margin: 5px 0; }}
    .cover-page {{ padding: 0; }}
    .cover {{
      text-align: center; padding: 22mm 14mm 18mm;
      min-height: 250mm;
      background: linear-gradient(180deg, #f8f2e8 0%, var(--paper) 48%, #efe6d6 100%);
      border: 1px solid var(--gold);
      box-shadow: inset 0 0 0 5px var(--surface), inset 0 0 0 6px var(--border);
    }}
    .cover .brand-mark {{
      width: 44px; height: 44px; margin: 0 auto 14px;
      border: 1px solid var(--gold); color: var(--gold);
      line-height: 44px; font-size: 20px; letter-spacing: 0;
    }}
    .cover .rule {{
      width: 42%; margin: 16px auto; border: none; border-top: 1px solid var(--gold); opacity: 0.75;
    }}
    .cover .name {{ font-size: 20px; margin: 10px 0 6px; letter-spacing: 0.16em; }}
    .cover .titqian {{
      display: inline-block; margin-top: 8px; padding: 8px 22px;
      border: 1px solid var(--border); background: rgba(255,250,245,0.95);
      letter-spacing: 0.08em;
    }}
    .cover .mingju {{
      margin: 18px auto 0; max-width: 86%; padding: 10px 14px;
      border-top: 1px solid var(--gold); border-bottom: 1px solid var(--gold);
      font-size: 12px; color: #5c3d2e; letter-spacing: 0.04em;
    }}
    .cover .toc {{
      margin: 22px auto 0; max-width: 70%; text-align: left; font-size: 11.5px; color: var(--mist);
      line-height: 1.9;
    }}
    .cover .toc .toc-k {{ color: #5c3d2e; letter-spacing: 0.12em; }}
    .cover .foot {{ margin-top: 20px; font-size: 11px; }}
    .identity {{
      display: flex; gap: 0; margin: 10px 0 12px; border: 1px solid var(--border); background: var(--surface);
    }}
    .identity .cell {{
      flex: 1; padding: 9px 10px; border-right: 1px solid var(--border);
    }}
    .identity .cell:last-child {{ border-right: none; }}
    .identity .k {{ font-size: 10px; color: var(--mist); letter-spacing: 0.1em; }}
    .identity .v {{ font-size: 12.5px; margin-top: 4px; font-weight: 600; color: #5c3d2e; }}
    .caliber {{
      border: 1px solid var(--border); padding: 8px 10px; margin-bottom: 8px;
      font-size: 10.5px; color: var(--mist); background: var(--surface);
    }}
    .summary-block {{
      border: 1px solid var(--border); padding: 10px 12px; margin-top: 8px; background: var(--surface);
    }}
    .inline-note {{ margin: 6px 0; }}
    .chart-legend {{ font-size: 10.5px; color: var(--mist); margin: 2px 0 6px; }}
    .legend-box, .bridge-card {{
      border: 1px solid var(--border); background: var(--surface);
      padding: 8px 10px; margin: 8px 0; font-size: 11px;
    }}
    .legend-title, .bridge-k {{
      font-size: 10.5px; color: #5c3d2e; letter-spacing: 0.12em; margin: 0 0 4px; font-weight: 600;
    }}
    .topic-grid {{ display: block; margin-top: 8px; }}
    .topic-card {{
      border: 1px solid var(--border); border-left: 2px solid var(--gold);
      background: var(--surface); padding: 8px 10px; margin: 8px 0; font-size: 11px;
    }}
    .bazi-chart {{ font-size: 10.5px; }}
    .bazi-chart th, .bazi-chart td {{ text-align: center; padding: 4px 3px; border-color: #cfc3a8; }}
    .bazi-chart .row-label, .bazi-chart th.row-label {{
      text-align: left; font-weight: 600; width: 11%; background: #faf6ef;
    }}
    .bazi-chart .col-day {{ background: #f7efe2; }}
    .bazi-chart .glyph {{ font-size: 15px; font-weight: 700; line-height: 1.2; }}
    .bazi-chart .hid {{ display: inline-block; font-size: 10px; line-height: 1.35; }}
    .bazi-chart .tg {{ font-size: 9px; color: var(--mist); margin-left: 1px; }}
    .bazi-chart .ss {{ display: inline-block; font-size: 9.5px; line-height: 1.35; }}
    .bazi-chart .ss-good {{ color: #5c3d2e; font-weight: 600; }}
    .bazi-chart .ss-warn {{ color: var(--cinnabar); }}
    .bazi-chart .ss-neutral {{ color: var(--mist); }}
    .bridge-stack {{ margin-top: 10px; }}
    .trust-summary p {{ margin: 6px 0; }}
    .trust-appendix {{
      margin-top: 12px; padding-top: 8px; border-top: 1px dashed var(--border);
      font-size: 10px; color: var(--mist);
    }}
    .page-foot, .page-foot-bar {{
      margin-top: 14px; padding-top: 8px; border-top: 1px solid var(--border);
      font-size: 10px; color: var(--mist);
    }}
  </style>
</head>
<body>
  <section class="page cover-page">
    <div class="cover">
      <div class="brand-mark">浮</div>
      <p class="eyebrow">FUSHENG ARCHIVE</p>
      <h1>浮生 · 命理个人档案</h1>
      <p class="meta">浮生若寄，知命知心</p>
      <hr class="rule" />
      <div class="titqian">
        <p class="name"><strong>{_esc(meta.get("label"))}</strong></p>
        <p>{_esc(birth_human)}</p>
      </div>
      <p class="mingju">{_esc(cover_mingju)}</p>
      <div class="toc">
        <p class="toc-k">本册目录</p>
        <p>一、基础档案与读法 · 二、八字满盘（定格 / 本年）</p>
        <p>三、大运叙事 · 四、紫微议题（桃花 / 田宅 / 慎点）</p>
        <p>五、校勘与解读要点 · 六、综合总结与回看</p>
      </div>
      <p class="foot meta">浮生报告 v2.7 · {_esc(meta.get("generated_at", "")[:10])}</p>
    </div>
  </section>

  <section class="page sheet">
    <h2>基础档案</h2>
    {how_to_read}
    <div class="caliber">
      历法：{_esc(cal_label)}{focus_html} · 紫微年界：{_esc(year_divide_label)} · 日界：{_esc(day_divide_label)} ·
      晚子时：{_esc(late_zishi_label)} · 子时规则：{_esc(zi_day_rule_label)} · 时辰精度：{_esc(precision_label)}{fallback_html}
    </div>
    <div class="identity">
      <div class="cell"><div class="k">格局 · 强弱</div><div class="v">{geju_line} · {_esc(strength_tier)}</div></div>
      <div class="cell"><div class="k">用神 · 忌神</div><div class="v">{favor_cn} / {avoid_cn}</div></div>
      <div class="cell"><div class="k">紫微命宫</div><div class="v">{_esc(ziwei.get("life_palace_gz", "—"))} · {_esc(ziwei.get("wuxing_ju_name", "—"))}</div></div>
    </div>
    <p class="meta">{_esc(lifestyle_line)}</p>
    {dual_inline}
    {relations_block}
    <div class="summary-block">{_esc(archive_summary)}</div>
    <p class="page-foot">本页为档案摘要；完整盘面见「八字满盘」。</p>
  </section>

  <section class="page sheet">
    <h2>八字满盘</h2>
    <p>格局：{geju_line} · 强弱：{_esc(strength_tier)} · 用神：{favor_cn} · 忌神：{avoid_cn}</p>
    {wuxing_html}
    {dual_html}
    {pillars_table}
    <div class="bridge-stack">
      {geju_block}
      {liunian_block}
      {dayun_block}
    </div>
    <p class="page-foot">当前大运参考：{_esc(current_dayun_gz or "—")} · 流年对齐导出年 {_esc(current_year)}</p>
  </section>

  <section class="page sheet">
    <h2>运势时间轴（大运）</h2>
    <p class="meta">「大运起始年」为每步约十年之起点；标「当前步」者为导出时步入之大运。</p>
    {dayun_block}
    <table class="ruled"><thead><tr><th>大运起始年</th><th>干支</th><th>十神</th><th>标记</th></tr></thead>
    <tbody>{dayun_rows or '<tr><td colspan="4">暂无</td></tr>'}</tbody></table>
  </section>

  <section class="page sheet">
    <h2>紫微总览 · 人生议题</h2>
    <p class="accent"><strong>命宫一句话</strong>：{life_one_liner}</p>
    <p>五行局：{_esc(ziwei.get("wuxing_ju_name", "—"))} · 命宫：{_esc(ziwei.get("life_palace_gz", "—"))}</p>
    {topic_block}
    {flying_block}
    <table class="ruled"><thead><tr><th>宫位</th><th>宫干</th><th>主星</th></tr></thead>
    <tbody>{palace_rows or '<tr><td colspan="3">暂无</td></tr>'}</tbody></table>
  </section>

  {name_section}

  {dual_track_appendix}

  {trust_section}

  {explain_section}

  {closing_section}

  {notes_section}
</body>
</html>"""
