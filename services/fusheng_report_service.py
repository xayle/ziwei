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


def _render_dual_track_appendix(bazi: dict[str, Any], ziwei: dict[str, Any]) -> str:
    """BE-P2-02：双轨对照附录表（八字格局 × 紫微命宫）。"""
    geju = bazi.get("geju") or {}
    recorded = geju.get("recorded_geju") or geju.get("recorded_geju_name") or "—"
    engine = geju.get("engine_geju") or geju.get("geju_name") or "—"
    dual_id = geju.get("dual_track_id") or bazi.get("dual_track_id") or "—"
    note = geju.get("dual_track_note") or bazi.get("dual_track_note") or "—"
    rows = [
        ("八字格局", _esc(recorded), _esc(engine), _esc(note)),
        (
            "紫微命宫",
            "—",
            _esc(ziwei.get("life_palace_gz") or "—"),
            _esc(ziwei.get("wuxing_ju_name") or "—"),
        ),
        (
            "双轨档案 ID",
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


def _render_explain_section(
    explain_bazi: dict[str, Any] | None,
    explain_ziwei: dict[str, Any] | None,
) -> str:
    parts: list[str] = []
    for label, explain in (("八字", explain_bazi), ("紫微", explain_ziwei)):
        if not explain:
            continue
        for section in explain.get("sections") or []:
            if not isinstance(section, dict):
                continue
            sid = section.get("section_id", "")
            title = _EXPLAIN_SECTION_TITLES.get(sid, sid)
            blocks = section.get("blocks") or []
            if not blocks:
                continue
            block_html = "".join(
                f"<p class='explain-{block.get('layer', 'fact')}'>{_esc(block.get('text', ''))}</p>"
                for block in blocks
                if isinstance(block, dict) and block.get("text")
            )
            parts.append(f"<h3>{_esc(label)} · {_esc(title)}</h3>{block_html}")

    disclaimer = (explain_bazi or explain_ziwei or {}).get("disclaimer_block") or {}
    disclaimer_text = disclaimer.get("text")
    if disclaimer_text:
        version = disclaimer.get("version", "")
        version_txt = f"（v{_esc(version)}）" if version else ""
        parts.append(f"<p class='meta disclaimer'>{_esc(disclaimer_text)}{version_txt}</p>")

    if not parts:
        return ""
    return f"<section class='page'><h2>解读草案</h2>{''.join(parts)}</section>"


def _render_trust_section(bazi: dict[str, Any], ziwei: dict[str, Any]) -> str:
    parts: list[str] = []
    missing = list(dict.fromkeys((bazi.get("missing_fields") or []) + (ziwei.get("missing_fields") or [])))
    if missing:
        parts.append(f"<p><strong>未覆盖字段</strong>：{_esc('、'.join(missing))}</p>")

    geju = bazi.get("geju") or {}
    if geju.get("recorded_geju") or geju.get("engine_geju"):
        parts.append(
            "<p><strong>双轨格局</strong>："
            f"古籍 {_esc(geju.get('recorded_geju') or '—')} · "
            f"引擎 {_esc(geju.get('engine_geju') or geju.get('geju_name') or '—')}</p>"
        )
    if geju.get("dual_track_note"):
        parts.append(f"<p>{_esc(geju.get('dual_track_note'))}</p>")

    prov_bits: list[str] = []
    for source, payload in (("八字", bazi.get("provenance") or {}), ("紫微", ziwei.get("provenance") or {})):
        if not isinstance(payload, dict):
            continue
        for key, layer in payload.items():
            if not isinstance(layer, dict) or not layer.get("layer"):
                continue
            conf = layer.get("confidence")
            conf_txt = f" {int(conf * 100)}%" if isinstance(conf, int | float) else ""
            prov_bits.append(f"{source}·{key}={layer.get('layer')}{conf_txt}")
    if prov_bits:
        parts.append(f"<p><strong>可信度分层</strong>：{_esc(' · '.join(prov_bits[:8]))}</p>")

    if bazi.get("confidence_level"):
        score = bazi.get("confidence_score")
        score_txt = f"（{score}）" if score is not None else ""
        parts.append(f"<p><strong>置信度</strong>：{_esc(bazi.get('confidence_level'))}{score_txt}</p>")

    bazi_classics = bazi.get("classic_refs") or []
    if bazi_classics:
        bits = [
            f"{_esc(c.get('category', ''))}·{_esc((c.get('text') or '')[:48])}"
            for c in bazi_classics[:4]
            if isinstance(c, dict)
        ]
        if bits:
            parts.append(f"<p><strong>八字典籍提示</strong>：{_esc(' · '.join(bits))}</p>")

    ziwei_classics = ziwei.get("classic_refs") or []
    if ziwei_classics:
        bits = [
            f"{_esc(c.get('category', ''))}·{_esc((c.get('text') or '')[:48])}"
            for c in ziwei_classics[:4]
            if isinstance(c, dict)
        ]
        if bits:
            parts.append(f"<p><strong>紫微典籍提示</strong>：{_esc(' · '.join(bits))}</p>")

    validation = bazi.get("validation") or {}
    if validation.get("level"):
        parts.append(
            f"<p><strong>校验层级</strong>：{_esc(validation.get('level'))} · "
            f"解读{'允许' if validation.get('interpretation_enabled') else '受限'}</p>"
        )

    liuri = bazi.get("liuri_liushi") or {}
    if liuri.get("day_ganzhi"):
        parts.append(
            f"<p><strong>流日/流时</strong>：{_esc(liuri.get('date', ''))} "
            f"日柱 {_esc(liuri.get('day_ganzhi', ''))} · 时柱 {_esc(liuri.get('hour_ganzhi', ''))}</p>"
        )

    cc = ziwei.get("iztro_crosscheck") or {}
    if cc:
        parts.append(
            f"<p><strong>iztro 交叉核验</strong>：{_esc(cc.get('status', ''))} · "
            f"主星 {cc.get('main_match', '—')}/{cc.get('main_total', '—')}</p>"
        )
        if cc.get("advisory"):
            parts.append(f"<p>{_esc(cc.get('advisory'))}</p>")

    warnings = ziwei.get("engine_warnings") or []
    if warnings:
        parts.append(f"<p><strong>引擎提示</strong>：{_esc('；'.join(warnings[:4]))}</p>")

    if not parts:
        return ""
    return f"<section class='page'><h2>引擎可信度</h2>{''.join(parts)}</section>"


def render_fusheng_report_html(payload: dict[str, Any]) -> str:
    meta = payload["meta"]
    bazi = payload["bazi"]
    ziwei = payload["ziwei"]
    name = payload.get("name")

    pillars = bazi.get("pillars_primary") or {}
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
        "current": "不换日",
    }.get(meta.get("day_divide") or "solar_next", "公历换日")
    late_zishi_label = "晚子时换日" if meta.get("late_zishi", True) else "晚子不换日"
    precision_labels = {
        "exact": "精确到分",
        "hour": "整点/时辰",
        "approximate": "约略时辰",
        "unknown": "时辰未详",
    }
    precision_label = precision_labels.get(meta.get("birth_time_precision") or "exact", "精确到分")
    fallback_labels = {
        "midday": "默认午时",
        "noon": "正午",
        "start_of_hour": "时辰起点",
    }
    fallback = meta.get("unknown_time_fallback")
    fallback_label = fallback_labels.get(fallback) if fallback else None

    dayun_rows = "".join(
        f"<tr><td>{_esc(item.get('start_year', '—'))}</td>"
        f"<td>{_esc((item.get('stem') or '') + (item.get('branch') or ''))}</td>"
        f"<td>{_esc(item.get('ten_god', '—'))}</td></tr>"
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
        <section class="page">
          <h2>姓名分析</h2>
          <p>{_esc(name.get('summary'))}</p>
          <table><thead><tr><th>格局</th><th>数理</th><th>五行</th><th>吉凶</th><th>得分</th></tr></thead>
          <tbody>{grid_rows}</tbody></table>
          <p>三才：{_esc(name['sancai']['pattern'])} · {_esc(name['sancai']['lucky'])}</p>
          <p class="accent">{_esc(cross)}</p>
        </section>
        """

    notes_block = f"<pre class='notes'>{_esc(meta.get('notes') or '（无批注）')}</pre>"
    trust_section = _render_trust_section(bazi, ziwei)
    dual_track_appendix = _render_dual_track_appendix(bazi, ziwei)
    explain_section = _render_explain_section(payload.get("explain_bazi"), payload.get("explain_ziwei"))

    from services.pdf_font_styles import pdf_body_font_family, pdf_song_font_face_css

    font_face_css = pdf_song_font_face_css()
    body_font = pdf_body_font_family()

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <title>{_esc(meta.get('label'))}</title>
  <style>
    {font_face_css}
    @page {{ size: A4; margin: 14mm; }}
    body {{ font-family: {body_font}; color: #2b2118; font-size: 12px; line-height: 1.7; }}
    h1 {{ font-size: 24px; margin: 0 0 8px; }}
    h2 {{ font-size: 16px; margin: 0 0 10px; color: #5c3d2e; border-bottom: 1px solid #d4b896; padding-bottom: 4px; }}
    .page {{ page-break-after: always; padding: 8px 0 16px; }}
    .page:last-child {{ page-break-after: auto; }}
    .cover {{ text-align: center; padding-top: 80px; }}
    .meta, .accent {{ color: #7a5c3a; }}
    table {{ width: 100%; border-collapse: collapse; margin-top: 8px; }}
    th, td {{ border: 1px solid #e8dcc8; padding: 6px 8px; text-align: left; }}
    th {{ background: #faf6ef; }}
    .notes {{ white-space: pre-wrap; background: #faf6ef; padding: 12px; border-radius: 8px; border: 1px solid #e8dcc8; }}
  </style>
</head>
<body>
  <section class="page cover">
    <h1>浮生 · 命理个人档案</h1>
    <p class="meta">浮生若寄，知命知心</p>
    <p><strong>{_esc(meta.get('label'))}</strong></p>
    <p>{_esc(meta.get('birth_dt'))} · {_esc(meta.get('city_name') or '出生地未填')}</p>
    <p class="meta">浮生报告 v2.5 · {_esc(meta.get('generated_at', '')[:10])}</p>
  </section>

  <section class="page">
    <h2>基础档案</h2>
    <p>历法：{_esc(meta.get('calendar_mode'))} · 关注：{_esc(meta.get('focus_topic') or '未填写')}</p>
    <p>紫微年界：{_esc(year_divide_label)} · 晚子换日：{_esc(day_divide_label)} · 晚子时：{_esc(late_zishi_label)}</p>
    <p>子时规则：{_esc(meta.get('zi_day_rule') or 'sxtwl')} · 时辰精度：{_esc(precision_label)}{f' · 未知默认：{_esc(fallback_label)}' if fallback_label else ''}</p>
    <p>用神：{favor_cn} · 忌神：{avoid_cn}</p>
    <p>{_esc(bazi.get('bazi_summary') or (bazi.get('geju') or {}).get('interpretation_text') or '')}</p>
  </section>

  <section class="page">
    <h2>八字总览</h2>
    <p>格局：{geju_line} · 强弱：{_esc((bazi.get('day_master_strength') or {}).get('tier', '—'))}</p>
    {dual_html}
    <table>
      <thead><tr><th>柱</th><th>干支</th></tr></thead>
      <tbody>
        <tr><td>年</td><td>{_esc((pillars.get('year') or {}).get('stem', ''))}{_esc((pillars.get('year') or {}).get('branch', ''))}</td></tr>
        <tr><td>月</td><td>{_esc((pillars.get('month') or {}).get('stem', ''))}{_esc((pillars.get('month') or {}).get('branch', ''))}</td></tr>
        <tr><td>日</td><td>{_esc((pillars.get('day') or {}).get('stem', ''))}{_esc((pillars.get('day') or {}).get('branch', ''))}</td></tr>
        <tr><td>时</td><td>{_esc((pillars.get('hour') or {}).get('stem', ''))}{_esc((pillars.get('hour') or {}).get('branch', ''))}</td></tr>
      </tbody>
    </table>
  </section>

  <section class="page">
    <h2>运势时间轴（大运）</h2>
    <table><thead><tr><th>起始年</th><th>干支</th><th>十神</th></tr></thead><tbody>{dayun_rows or '<tr><td colspan="3">暂无</td></tr>'}</tbody></table>
  </section>

  <section class="page">
    <h2>紫微总览</h2>
    <p>{_esc(ziwei.get('summary') or '')}</p>
    <p>五行局：{_esc(ziwei.get('wuxing_ju_name', '—'))} · 命宫：{_esc(ziwei.get('life_palace_gz', '—'))}</p>
    <table><thead><tr><th>宫位</th><th>宫干</th><th>主星</th></tr></thead><tbody>{palace_rows or '<tr><td colspan="3">暂无</td></tr>'}</tbody></table>
  </section>

  {name_section}

  {dual_track_appendix}

  {trust_section}

  {explain_section}

  <section class="page">
    <h2>综合总结</h2>
    <p>{_esc(bazi.get('bazi_summary') or '')}</p>
    <p>{_esc(ziwei.get('summary') or '')}</p>
    <p class="meta">本报告仅供个人参考，不构成医疗、法律或投资建议。</p>
  </section>

  <section class="page">
    <h2>人工批注区</h2>
    {notes_block}
  </section>
</body>
</html>"""
