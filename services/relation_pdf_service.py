"""Relation compatibility PDF — HTML from relation-compat@1.0 response."""

from __future__ import annotations

from datetime import UTC, datetime
from html import escape
from typing import Any

from services.pdf_font_styles import pdf_body_font_family, pdf_song_font_face_css

_LAYER_LABEL = {"fact": "格物", "cite": "引经", "inference": "余论"}


def _layers_cite_html(payload: dict[str, Any]) -> str:
    cite_block = (payload.get("layers") or {}).get("cite") or {}
    sections = cite_block.get("sections") or []
    if not sections:
        return ""
    rows = ""
    for section in sections:
        heading = section.get("heading") or "引经"
        for block in section.get("blocks") or []:
            text = block.get("text") or ""
            if text:
                rows += f"<li><strong>{_esc(heading)}</strong> · {_esc(text)}</li>"
    if not rows:
        return ""
    return f"""
  <section class="sheet inference">
    <h2>典籍引证（引经 · 默认折叠）</h2>
    <ul class="cards">{rows}</ul>
  </section>"""


def _esc(value: Any) -> str:
    return escape(str(value if value is not None else ""))


def _pillars_line(person: dict[str, Any]) -> str:
    pillars = person.get("pillars_primary") or {}
    if not pillars:
        return "—"
    order = ("year", "month", "day", "hour")
    parts = [str(pillars.get(k, "—")) for k in order]
    return " · ".join(parts)


def render_relation_compat_html(payload: dict[str, Any]) -> str:
    """Build printable HTML for RelationFullResponse dict."""
    pa = payload.get("person_a") or {}
    pb = payload.get("person_b") or {}
    disclaimer = (payload.get("disclaimer_block") or {}).get("text") or ""
    generated = datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")
    request_id = payload.get("request_id") or "—"
    rel_label = payload.get("relation_type_label") or payload.get("relation_type") or "合盘"
    score = payload.get("combined_score")
    grade = payload.get("grade") or "—"
    bazi_block = payload.get("bazi") or {}
    ziwei_block = payload.get("ziwei") or {}
    bazi_score = bazi_block.get("score")
    ziwei_score = ziwei_block.get("score")
    dual_engine_html = ""
    if bazi_score is not None and ziwei_score is not None:
        dual_engine_html = (
            f'<p class="meta">双引擎：八字 {_esc(bazi_score)} · 紫微 {_esc(ziwei_score)}' f" · 综合 {_esc(score)}</p>"
        )
    elif bazi_score is not None:
        dual_engine_html = f'<p class="meta">八字引擎 {_esc(bazi_score)} · 综合 {_esc(score)}</p>'
    elif ziwei_score is not None:
        dual_engine_html = f'<p class="meta">紫微引擎 {_esc(ziwei_score)} · 综合 {_esc(score)}</p>'

    dim_rows = ""
    for dim in payload.get("dimensions") or []:
        layer = dim.get("layer") or "fact"
        engine = dim.get("engine") or "—"
        dim_rows += f"""
        <tr>
          <td>{_esc(dim.get("label"))}</td>
          <td>{_esc(dim.get("score"))}/{_esc(dim.get("max_score"))}</td>
          <td>{_esc(_LAYER_LABEL.get(layer, layer))}</td>
          <td>{_esc(engine)}</td>
          <td>{_esc(dim.get("description", ""))}</td>
        </tr>"""

    timeline_rows = ""
    for node in payload.get("timeline") or []:
        timeline_rows += f"""
        <tr>
          <td>{_esc(node.get("year"))}</td>
          <td>{_esc(node.get("label"))}</td>
          <td>{_esc(node.get("risk_level") or "—")}</td>
          <td>{_esc(node.get("summary", ""))}</td>
        </tr>"""

    palace_rows = ""
    for cross in payload.get("palace_cross") or []:
        palace_rows += f"""
        <tr>
          <td>{_esc(cross.get("a_palace"))} × {_esc(cross.get("b_palace"))}</td>
          <td>{_esc(cross.get("relation_tag"))}</td>
          <td>{_esc(cross.get("summary", ""))}</td>
        </tr>"""

    cards_html = ""
    for card in payload.get("summary_cards") or []:
        tone = card.get("tone") or "neutral"
        if tone not in ("support", "conflict", "neutral", "action"):
            tone = "neutral"
        cards_html += f'<li class="card card--{tone}">{_esc(card.get("text"))}</li>'

    actions_html = ""
    for item in payload.get("action_items") or []:
        actions_html += (
            f'<li><span class="prio">{_esc(item.get("priority") or "")}</span> {_esc(item.get("text"))}</li>'
        )

    cite_html = _layers_cite_html(payload)
    font_face_css = pdf_song_font_face_css()
    body_font = pdf_body_font_family()

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <title>{_esc(pa.get("label"))} × {_esc(pb.get("label"))} · 关系合盘</title>
  <style>
    {font_face_css}
    @page {{
      margin: 12mm 10mm 16mm;
      @bottom-center {{
        content: counter(page) " / " counter(pages);
        font-size: 9pt;
        color: #9a8b7a;
      }}
    }}
    body {{
      font-family: {body_font};
      color: #1a1410;
      background: #f5f0e6;
      font-size: 11pt;
      line-height: 1.65;
    }}
    .sheet {{
      background: #fffaf5;
      border: 1px solid #d4c4a8;
      padding: 28px 32px;
      margin-bottom: 16px;
    }}
    h1 {{ font-size: 20pt; letter-spacing: 0.12em; margin: 0 0 8px; }}
    h2 {{ font-size: 13pt; margin: 24px 0 12px; border-left: 3px solid #b8894d; padding-left: 10px; }}
    .meta {{ color: #6b5d4f; font-size: 9pt; }}
    .score {{ font-size: 28pt; color: #b8894d; margin: 12px 0; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 10pt; }}
    th, td {{ border-bottom: 1px solid #e5dcc8; padding: 8px 6px; text-align: left; vertical-align: top; }}
    th {{ color: #6b5d4f; font-weight: 600; }}
    .cards {{ list-style: none; padding: 0; margin: 0; }}
    .card {{ padding: 8px 0; border-bottom: 1px solid #e5dcc8; }}
    .disclaimer {{ font-size: 9pt; color: #9a8b7a; margin-top: 24px; }}
    .inference {{ background: #f5f0e6; padding: 12px; margin-top: 12px; }}
    .prio {{ color: #8b3a2a; font-size: 9pt; }}
  </style>
</head>
<body>
  <section class="sheet">
    <p class="meta">浮生 · relation-compat@1.0 · {_esc(request_id)} · {_esc(generated)}</p>
    <h1>{_esc(rel_label)}</h1>
    <p><strong>{_esc(pa.get("label"))}</strong> × <strong>{_esc(pb.get("label"))}</strong></p>
    <p class="meta">甲方四柱：{_esc(_pillars_line(pa))}<br />
       乙方四柱：{_esc(_pillars_line(pb))}<br />
       命宫：{_esc(pa.get("life_palace_gz") or "—")} · {_esc(pb.get("life_palace_gz") or "—")}</p>
    <div class="score">{_esc(score)} <span style="font-size:14pt">/ 100 · {_esc(grade)}</span></div>
    {dual_engine_html}
    <p>{_esc(payload.get("summary", ""))}</p>
    <ul class="cards">{cards_html}</ul>
  </section>

  <section class="sheet">
    <h2>维度评分</h2>
    <table>
      <thead><tr><th>维度</th><th>得分</th><th>分层</th><th>引擎</th><th>说明</th></tr></thead>
      <tbody>{dim_rows or "<tr><td colspan='5'>—</td></tr>"}</tbody>
    </table>
  </section>

  <section class="sheet">
    <h2>宫位对照</h2>
    <table>
      <thead><tr><th>宫位</th><th>关系</th><th>摘要</th></tr></thead>
      <tbody>{palace_rows or "<tr><td colspan='3'>—</td></tr>"}</tbody>
    </table>
  </section>

  <section class="sheet">
    <h2>时间轴</h2>
    <table>
      <thead><tr><th>年</th><th>标签</th><th>风险</th><th>摘要</th></tr></thead>
      <tbody>{timeline_rows or "<tr><td colspan='4'>—</td></tr>"}</tbody>
    </table>
  </section>

  <section class="sheet inference">
    <h2>行动建议（余论）</h2>
    <ul>{actions_html or "<li>—</li>"}</ul>
  </section>

  {cite_html}

  <p class="disclaimer">{_esc(disclaimer)}</p>
</body>
</html>"""


def render_multi_compat_html(payload: dict[str, Any], labels: list[str] | None = None) -> str:
    """Matrix PDF for MultiCompatResponse."""
    n = int(payload.get("person_count") or 0)
    names = labels or [f"成员{i + 1}" for i in range(n)]
    matrix = payload.get("matrix") or []
    generated = datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")

    header = "".join(f"<th>{_esc(names[i] if i < len(names) else i + 1)}</th>" for i in range(n))
    body_rows = ""
    for i, row in enumerate(matrix):
        cells = "".join(f"<td>{_esc(v)}</td>" for v in row)
        label = names[i] if i < len(names) else f"成员{i + 1}"
        body_rows += f"<tr><th>{_esc(label)}</th>{cells}</tr>"

    pair_rows = ""
    for pair in payload.get("pairs") or []:
        ai = int(pair.get("person_a_idx", 0))
        bi = int(pair.get("person_b_idx", 0))
        la = names[ai] if ai < len(names) else f"成员{ai + 1}"
        lb = names[bi] if bi < len(names) else f"成员{bi + 1}"
        pair_rows += f"""
        <tr>
          <td>{_esc(la)} × {_esc(lb)}</td>
          <td>{_esc(pair.get("total_score"))}/{_esc(pair.get("max_score"))}</td>
          <td>{_esc(pair.get("level"))}</td>
          <td>{_esc(pair.get("combined_score") or "—")}</td>
        </tr>"""

    harmony = payload.get("team_harmony_score")

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <title>多人合盘矩阵</title>
  <style>
    body {{ font-family: "Noto Serif SC", STSong, serif; color: #1a1410; background: #f5f0e6; font-size: 11pt; }}
    .sheet {{ background: #fffaf5; border: 1px solid #d4c4a8; padding: 24px; margin-bottom: 16px; }}
    h1 {{ font-size: 18pt; margin: 0 0 16px; }}
    table {{ width: 100%; border-collapse: collapse; }}
    th, td {{ border: 1px solid #e5dcc8; padding: 8px; text-align: center; }}
    .meta {{ color: #6b5d4f; font-size: 9pt; }}
  </style>
</head>
<body>
  <section class="sheet">
    <p class="meta">浮生 · multi_compat · {_esc(generated)}</p>
    <h1>多人缘分矩阵（{n} 人）</h1>
    <p>团队和谐指数：<strong>{_esc(harmony)}</strong> / 100</p>
    <table>
      <thead><tr><th></th>{header}</tr></thead>
      <tbody>{body_rows}</tbody>
    </table>
  </section>
  <section class="sheet">
    <h2>两两组合</h2>
    <table>
      <thead><tr><th>组合</th><th>紫微分</th><th>等级</th><th>综合分</th></tr></thead>
      <tbody>{pair_rows or "<tr><td colspan='3'>—</td></tr>"}</tbody>
    </table>
  </section>
</body>
</html>"""
