"""Build life-volume@1.0 responses (R096 draft · W16 authority path)."""

from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Any

from app.models import Case
from app.schemas import BaziFullRequest
from app.schemas.disclaimer import DisclaimerBlockModel
from app.schemas.entitlement import EntitlementTier
from app.schemas.explain import ExplainBatchRequest, ZiweiExplainBatchRequest
from app.schemas.life_volume import (
    LIFE_VOLUME_LABELS,
    AnalysisBlockModel,
    ColophonModel,
    LifeVolumeModel,
    LifeVolumeResponseModel,
    VolumeSectionModel,
)
from app.schemas.ziwei import ZiweiRequest, ZiweiResponse
from services.chart_snapshot_service import build_bazi_snapshot
from services.content_policy import content_versions_meta, default_disclaimer_block
from services.explain_service import explain_bazi_batch, explain_ziwei_batch
from services.missing_field_labels import missing_field_label
from services.quota_service import is_volume_unlocked
from services.ziwei_engine import ziwei_full
from services.ziwei_trust import apply_trust_level


def _block(text: str, layer: str = "fact", classic_id: str | None = None) -> AnalysisBlockModel:
    return AnalysisBlockModel(text=text.strip() or "—", layer=layer, classic_id=classic_id)


def _section(
    sid: str,
    heading: str,
    layer: str,
    blocks: list[AnalysisBlockModel],
    *,
    collapsed_default: bool = False,
) -> VolumeSectionModel:
    return VolumeSectionModel(
        id=sid,
        heading=heading,
        layer=layer,
        blocks=blocks,
        collapsed_default=collapsed_default,
    )


def _clip(text: str, limit: int = 280) -> str:
    t = (text or "").strip()
    if len(t) <= limit:
        return t
    return f"{t[: limit - 1]}…"


def _pillar_line(label: str, pillar: dict[str, Any] | None) -> str:
    if not isinstance(pillar, dict):
        return f"{label} —"
    gz = (pillar.get("ganzhi") or f"{pillar.get('stem', '')}{pillar.get('branch', '')}").strip() or "—"
    return f"{label} {gz}"


def _dayun_block_text(item: dict[str, Any], index: int) -> str:
    gz = f"{item.get('stem', '')}{item.get('branch', '')}".strip() or "—"
    start_age = item.get("start_age")
    end_age = item.get("end_age")
    if start_age is not None and end_age is None and start_age is not None:
        try:
            end_age = int(float(start_age)) + 9
        except (TypeError, ValueError):
            end_age = None
    age = ""
    if start_age is not None:
        try:
            age = f"{int(float(start_age))}–{int(float(end_age)) if end_age is not None else '—'}岁"
        except (TypeError, ValueError):
            age = f"{start_age}岁起"
    year = ""
    if item.get("start_year") is not None:
        try:
            sy = int(item["start_year"])
            year = f"{sy}–{sy + 9}年"
        except (TypeError, ValueError):
            year = str(item.get("start_year"))
    ten = str(item.get("ten_god") or "").strip()
    head = " · ".join(x for x in (f"{index + 1}. {gz}", age, year, f"十神 {ten}" if ten else "") if x)
    narrative = str(item.get("narrative") or "").strip()
    if narrative:
        return f"{head}。{_clip(narrative, 360)}"
    hints = [
        str(item.get(k) or "").strip()
        for k in ("geju_impact", "wealth_hint", "health_hint", "love_hint")
        if item.get(k)
    ]
    if hints:
        return f"{head}。{'；'.join(hints[:3])}"
    return head


def _palace_block_text(palace: dict[str, Any]) -> str:
    stars = (
        "、".join(
            str(s.get("name") or "") for s in (palace.get("main_stars") or []) if isinstance(s, dict) and s.get("name")
        )
        or "无主星"
    )
    head = f"{palace.get('name')} {palace.get('stem', '')}{palace.get('branch', '')}：主星 {stars}"
    narrative = str(
        palace.get("conclusion")
        or palace.get("analysis")
        or palace.get("explanation")
        or palace.get("suggestion")
        or ""
    ).strip()
    aux = "、".join(
        str(s.get("name") or "") for s in (palace.get("aux_stars") or [])[:4] if isinstance(s, dict) and s.get("name")
    )
    tags = "、".join(str(t) for t in (palace.get("analysis_tags") or [])[:3] if t)
    extras = []
    if aux:
        extras.append(f"辅煞 {aux}")
    if tags:
        extras.append(f"要点 {tags}")
    if len(narrative) >= 40:
        return f"{head}。{_clip(narrative, 220)}"
    parts = [head]
    if extras:
        parts.append("；".join(extras))
    if narrative:
        parts.append(narrative)
    return "；".join(parts)


def _relations_text(bazi: dict[str, Any]) -> str:
    """对齐 FE formatRelationsSummaryText：优先 summary 字段，勿用 type/label。"""
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
            legacy = str(item.get("detail") or item.get("label") or "").strip()
            if legacy:
                lines.append(legacy)
        if lines:
            return "；".join(lines)
    return "干支关系摘要待补全。"


def _shensha_text(bazi: dict[str, Any]) -> str:
    ss = bazi.get("shensha_summary") or {}
    highlights = ss.get("highlights") or []
    if highlights:
        return "、".join(str(h) for h in highlights[:8])
    items = ss.get("items") or bazi.get("shensha") or []
    names = [str(i.get("name")) for i in items if isinstance(i, dict) and i.get("name")]
    return "、".join(names[:8]) if names else "神煞摘要待补全。"


def _enrich_vol_block(label: str, body: str, *, floor: int = 40) -> str:
    """短事实块补读法衬底，避免空洞审计误杀。"""
    trimmed = str(body or "").strip()
    if len(trimmed) >= floor:
        return trimmed
    combined = f"{label}：{trimmed}。以排盘事实为准，配合卷内典籍 / 推断分层阅读。"
    if len(combined) < floor:
        combined = f"{combined}详见本节与相邻讲解。"
    return combined


def _explain_sections(explain: dict[str, Any] | None, section_id: str) -> list[AnalysisBlockModel]:
    if not explain:
        return []
    for section in explain.get("sections") or []:
        if section.get("section_id") != section_id:
            continue
        blocks: list[AnalysisBlockModel] = []
        for raw in section.get("blocks") or []:
            if not isinstance(raw, dict):
                continue
            text = str(raw.get("text") or "").strip()
            if not text:
                continue
            if len(text) < 40 and section_id == "geju":
                text = _enrich_vol_block("格局讲解", text)
            blocks.append(
                AnalysisBlockModel(
                    text=_clip(text),
                    layer=raw.get("layer", "fact"),
                    classic_id=raw.get("classic_id"),
                )
            )
        return blocks
    return []


def _missing_field_label(field: str) -> str:
    return missing_field_label(field)


def _build_colophon(
    *,
    missing_fields: list[str],
    iztro_advisory: str | None,
    wenmo_advisory: str | None,
    engine_label: str,
) -> ColophonModel:
    lines: list[str] = [
        f"校勘：引擎 {engine_label}；排盘字段{'有注记见下行' if missing_fields else '齐备'}，可核对卷内事实 / 典籍 / 推断分层。"
    ]
    if missing_fields:
        labels = [_missing_field_label(f) for f in missing_fields[:4]]
        lines.append(f"字段注记：{'、'.join(labels)}（不影响已写出块；对照项非故障，展开脚注可核）。")
    if iztro_advisory:
        lines.append(_clip(iztro_advisory, 72))
    if len(lines) == 1 and not missing_fields:
        lines.append("双轨核验：可对照开源排盘 / 文墨对照（若有）。")
    return ColophonModel(
        summary_lines=lines[:3],
        missing_fields=missing_fields or None,
        iztro_advisory=iztro_advisory,
        wenmo_advisory=wenmo_advisory,
        expandable=True,
    )


def _locked_teaser(volume_id: str) -> list[VolumeSectionModel]:
    need = {
        "vol2": "读卷 Pass",
        "vol3": "读卷 Pass",
        "vol4": "读卷 Pass",
        "vol5": "全书权益",
        "vol6": "全书权益",
    }.get(volume_id, "更高权益")
    return [
        VolumeSectionModel(
            id="locked",
            heading="本卷未解锁",
            layer="fact",
            collapsed_default=False,
            blocks=[
                AnalysisBlockModel(
                    text=f"本卷需{need}后方可展开全文（当前档位不足）。",
                    layer="fact",
                )
            ],
        )
    ]


def _apply_volume_locks(
    volumes: list[LifeVolumeModel],
    entitlement: EntitlementTier,
) -> list[LifeVolumeModel]:
    """T087 / Q2：按 entitlement 写 locked，并替换锁定卷正文为占位节。"""
    out: list[LifeVolumeModel] = []
    for vol in volumes:
        if is_volume_unlocked(entitlement, vol.id):
            out.append(vol.model_copy(update={"locked": False}))
        else:
            out.append(
                vol.model_copy(
                    update={
                        "locked": True,
                        "sections": _locked_teaser(vol.id),
                    }
                )
            )
    return out


_H5_PREVIEW_VOLUME_IDS = frozenset({"preface", "vol1"})
_H5_PREVIEW_BLOCK_CHARS = 200
_H5_PREVIEW_MAX_SECTIONS = 2
_H5_PREVIEW_MAX_BLOCKS = 2


def project_h5_vol1_preview(response: LifeVolumeResponseModel) -> LifeVolumeResponseModel:
    """T095：落地页试读仅保留卷首 + 卷一，并裁剪为摘要长度。"""
    slim_volumes: list[LifeVolumeModel] = []
    for vol in response.volumes:
        if vol.id not in _H5_PREVIEW_VOLUME_IDS:
            continue
        sections: list[VolumeSectionModel] = []
        for section in vol.sections[:_H5_PREVIEW_MAX_SECTIONS]:
            blocks = [
                block.model_copy(update={"text": _clip(block.text, _H5_PREVIEW_BLOCK_CHARS)})
                for block in section.blocks[:_H5_PREVIEW_MAX_BLOCKS]
            ]
            sections.append(section.model_copy(update={"blocks": blocks}))
        slim_volumes.append(vol.model_copy(update={"locked": False, "sections": sections}))
    return response.model_copy(
        update={
            "volumes": slim_volumes,
            "relation_appendix": None,
            "colophon": ColophonModel(
                summary_lines=(response.colophon.summary_lines or [])[:1] or ["试读摘要 · 完整卷见建档后。"],
                missing_fields=None,
                iztro_advisory=None,
                wenmo_advisory=None,
                dual_track_note=None,
                expandable=False,
            ),
        }
    )


def build_life_volumes_from_charts(
    *,
    case_id: str,
    chart_hash: str,
    bazi: dict[str, Any],
    ziwei: dict[str, Any] | None,
    explain_bazi: dict[str, Any],
    explain_ziwei: dict[str, Any],
    profile_label: str | None = None,
    entitlement: EntitlementTier = "full_book",
) -> LifeVolumeResponseModel:
    missing: list[str] = list(bazi.get("missing_fields") or [])
    if ziwei:
        missing.extend(ziwei.get("missing_fields") or [])
    missing = sorted(set(missing))

    iztro = (ziwei or {}).get("iztro_crosscheck") or {}
    iztro_advisory = iztro.get("advisory") if isinstance(iztro, dict) else None
    wenmo_advisory = (ziwei or {}).get("wenmo_advisory") or explain_ziwei.get("wenmo_advisory")
    trust_level: str | None = "degraded" if iztro.get("life_palace_match") is False else "full"
    if ziwei and ziwei.get("trust_level") in ("degraded", "advisory"):
        trust_level = "degraded"

    day = (bazi.get("pillars_primary") or {}).get("day") or {}
    geju = bazi.get("geju") or {}
    pillars = bazi.get("pillars_primary") or {}

    preface_sections: list[VolumeSectionModel] = []
    if profile_label:
        preface_sections.append(
            _section(
                "archive-label",
                "辑录对象",
                "fact",
                [_block(_enrich_vol_block("辑录对象", str(profile_label)))],
            )
        )
    preface_sections.append(
        _section(
            "reading-guide",
            "读法导览",
            "fact",
            [
                _block(
                    "卷一至卷五按事实（排盘推算）· 典籍（典籍依据）· 推断（经验推断）分层阅读；"
                    "卷六为问书助手，需主动展开。先读卷一格局，再读卷二关系与卷三运限。",
                    "fact",
                )
            ],
        )
    )

    # CNT：远端 vol1 对齐 FE Adapter —— 四柱 / 格局 / 用神 / 强弱 / 运势
    pillar_text = _enrich_vol_block(
        "卷一四柱根气",
        "。".join(
            [
                _pillar_line("年柱", pillars.get("year") if isinstance(pillars.get("year"), dict) else None),
                _pillar_line("月柱", pillars.get("month") if isinstance(pillars.get("month"), dict) else None),
                _pillar_line("日柱", pillars.get("day") if isinstance(pillars.get("day"), dict) else None),
                _pillar_line("时柱", pillars.get("hour") if isinstance(pillars.get("hour"), dict) else None),
                f"日主 {day.get('stem', '—')}{day.get('branch', '—')}；格局 {geju.get('geju_name', '待分析')}",
            ]
        ),
    )
    vol1_sections = [
        _section("pillars", "四柱根气", "fact", [_block(pillar_text)]),
    ]
    geju_bits = [
        str(x).strip() for x in (geju.get("geju_detail"), geju.get("interpretation_text")) if str(x or "").strip()
    ]
    geju_uniq: list[str] = []
    for bit in geju_bits:
        if bit not in geju_uniq:
            geju_uniq.append(bit)
    geju_name = str(geju.get("geju_name") or "").strip()
    if geju_uniq or geju_name:
        parts = ([f"格局取「{geju_name}」"] if geju_name else []) + geju_uniq
        body = "。".join(parts)
        if geju.get("geju_level"):
            body = f"{body}（等级 {geju.get('geju_level')}）"
        vol1_sections.append(_section("geju", "格局", "fact", [_block(_enrich_vol_block("卷一格局", body))]))
    if str(geju.get("classic_ref") or "").strip():
        vol1_sections.append(_section("geju-cite", "典籍句式", "cite", [_block(str(geju.get("classic_ref")), "cite")]))
    yong = bazi.get("yongshen") or {}
    if isinstance(yong, dict) and (yong.get("favor") or yong.get("avoid")):
        vol1_sections.append(
            _section(
                "yongshen",
                "用神",
                "fact",
                [
                    _block(
                        _enrich_vol_block(
                            "卷一用神",
                            f"喜用 {'、'.join(yong.get('favor') or []) or '—'}；"
                            f"忌 {'、'.join(yong.get('avoid') or []) or '—'}",
                        )
                    )
                ],
            )
        )
    strength = bazi.get("day_master_strength") or {}
    if isinstance(strength, dict) and (strength.get("tier") is not None or strength.get("score") is not None):
        factor_bits = []
        for f in (strength.get("factors") or strength.get("strength_factors") or [])[:4]:
            if not isinstance(f, dict):
                continue
            name = str(f.get("name") or "").strip()
            reason = str(f.get("reason") or "").strip()
            if name and reason:
                factor_bits.append(f"{name}（{reason}）")
            elif name:
                factor_bits.append(name)
        strength_text = f"日主强弱：{strength.get('tier') or '—'}（评分 {strength.get('score', '—')}）"
        if factor_bits:
            strength_text = f"{strength_text}。主要因子：{'；'.join(factor_bits)}"
        vol1_sections.append(
            _section("strength", "日主强弱", "fact", [_block(_enrich_vol_block("卷一强弱", strength_text))])
        )
    fortune = bazi.get("current_fortune_summary") or {}
    if isinstance(fortune, dict):
        bits = [
            f"当前大运 {fortune['current_dayun']}" if fortune.get("current_dayun") else "",
            f"流年 {fortune['current_liunian']}" if fortune.get("current_liunian") else "",
            (
                f"大运余 {fortune['dayun_years_remaining']} 年"
                if fortune.get("dayun_years_remaining") is not None
                else ""
            ),
        ]
        bits = [b for b in bits if b]
        domains = fortune.get("this_year_domains") or {}
        if isinstance(domains, dict):
            for label, tip in domains.items():
                tip_s = _clip(str(tip or "").strip(), 120)
                if tip_s:
                    bits.append(f"{label}：{tip_s}")
        actions = [str(a).strip() for a in (fortune.get("top3_actions") or [])[:2] if str(a).strip()]
        if actions:
            bits.append("宜行： " + "；".join(_clip(a, 100) for a in actions))
        if bits:
            vol1_sections.append(_section("current-fortune", "当下运势摘要", "fact", [_block(" · ".join(bits))]))
    if str(bazi.get("bazi_summary") or "").strip():
        vol1_sections.append(
            _section(
                "summary-inference",
                "综合总评",
                "inference",
                [_block(_clip(str(bazi.get("bazi_summary")), 400), "inference")],
                collapsed_default=True,
            )
        )
    geju_blocks = _explain_sections(explain_bazi, "geju")
    if geju_blocks:
        vol1_sections.append(_section("geju-explain", "格局讲解", "cite", geju_blocks))

    vol2_sections = [
        _section(
            "relations",
            "干支关系",
            "fact",
            [_block(_enrich_vol_block("卷二干支关系摘要", _relations_text(bazi)))],
        ),
        _section(
            "shensha",
            "神煞摘要",
            "fact",
            [_block(_enrich_vol_block("卷二神煞摘要", _shensha_text(bazi)))],
        ),
    ]
    rel_blocks = _explain_sections(explain_bazi, "relations")
    if rel_blocks:
        vol2_sections.append(_section("relations-explain", "关系讲解", "fact", rel_blocks))

    vol3_sections: list[VolumeSectionModel] = []
    dayun_items = ((bazi.get("dayun") or {}).get("items") or (bazi.get("dayun") or {}).get("cycles") or [])[:8]
    if dayun_items:
        vol3_sections.append(
            _section(
                "dayun",
                "大运序列",
                "fact",
                [
                    _block(_dayun_block_text(item, idx))
                    for idx, item in enumerate(dayun_items)
                    if isinstance(item, dict)
                ],
            )
        )
    ziwei_dayun = ((ziwei or {}).get("dayun") or {}).get("items") or []
    if ziwei_dayun:
        z_blocks: list[AnalysisBlockModel] = []
        for idx, item in enumerate(ziwei_dayun[:8]):
            if not isinstance(item, dict):
                continue
            palace = str(item.get("palace_name") or "").strip()
            sihua = "、".join(f"{star}{trans}" for star, trans in (item.get("sihua") or {}).items())
            line = " · ".join(
                x
                for x in (
                    f"{idx + 1}. {item.get('ganzhi', '—')}",
                    (f"{item.get('start_age')}–{item.get('end_age')}岁" if item.get("start_age") is not None else ""),
                    f"应宫 {palace}" if palace else "",
                    f"四化 {sihua}" if sihua else "",
                )
                if x
            )
            z_blocks.append(_block(_enrich_vol_block("紫微大运节选", line)))
        if z_blocks:
            vol3_sections.append(_section("ziwei-dayun", "紫微大运", "fact", z_blocks))
    monthly = bazi.get("monthly_fortune") or []
    if isinstance(monthly, list) and monthly:
        vol3_sections.append(
            _section(
                "monthly-fortune",
                "月运（当年）",
                "fact",
                [
                    _block(
                        _enrich_vol_block(
                            "月运",
                            f"{m.get('month')}月"
                            f"{(' · ' + str(m.get('month_ganzhi') or m.get('month_dizhi') or '').strip()) if (m.get('month_ganzhi') or m.get('month_dizhi')) else ''}"
                            f" · {m.get('luck_level', '—')} · {_clip(str(m.get('tip') or '—'), 80)}",
                        )
                    )
                    for m in monthly[:12]
                    if isinstance(m, dict)
                ],
            )
        )
    liunian_items = (bazi.get("liunian") or {}).get("items") or []
    if isinstance(liunian_items, list) and liunian_items:
        year_now = datetime.now().year
        nearby = [
            it
            for it in liunian_items
            if isinstance(it, dict) and isinstance(it.get("year"), int) and abs(it["year"] - year_now) <= 2
        ][:5]
        pick = nearby or [it for it in liunian_items if isinstance(it, dict)][:5]
        vol3_sections.append(
            _section(
                "liunian",
                "流年节选",
                "fact",
                [
                    _block(
                        _enrich_vol_block(
                            "流年节选",
                            " · ".join(
                                x
                                for x in (
                                    str(it.get("year") or "—"),
                                    f"{it.get('stem', '')}{it.get('branch', '')}".strip() or "—",
                                    str(it.get("ten_god") or ""),
                                    f"星运 {it['xingyun']}" if it.get("xingyun") else "",
                                    _clip(str(it.get("summary") or it.get("tip") or ""), 60),
                                )
                                if x
                            ),
                        )
                    )
                    for it in pick
                ],
            )
        )
    if not vol3_sections:
        vol3_sections.append(_section("dayun-empty", "运限", "fact", [_block("大运序列待载入。")]))

    vol4_sections: list[VolumeSectionModel] = []
    if ziwei:
        vol4_sections.append(
            _section(
                "ziwei-meta",
                "命盘概要",
                "fact",
                [
                    _block(
                        f"卷四命盘概要：五行局 {ziwei.get('wuxing_ju_name', '—')}；"
                        f"命宫 {ziwei.get('life_palace_gz', '—')}；身宫 {ziwei.get('body_palace_gz', '—')}。"
                        f"阅读时先定命身轴，再对照十二宫主星与格局条文。"
                    )
                ],
            )
        )
        patterns = ziwei.get("patterns") or []
        if isinstance(patterns, list) and patterns:
            vol4_sections.append(
                _section(
                    "patterns",
                    "格局",
                    "fact",
                    [
                        _block(
                            _enrich_vol_block(
                                "紫微格局",
                                f"{p.get('name', '格局')}：{_clip(str(p.get('description') or ''), 200)}",
                            )
                        )
                        for p in patterns[:4]
                        if isinstance(p, dict)
                    ],
                )
            )
        palace_blocks = _explain_sections(explain_ziwei, "palaces")
        palaces = [p for p in (ziwei.get("palaces") or []) if isinstance(p, dict)]
        if palace_blocks:
            enriched: list[AnalysisBlockModel] = []
            for idx, blk in enumerate(palace_blocks):
                matched = palaces[idx] if idx < len(palaces) else None
                text = blk.text
                if matched and len(text) < 40:
                    text = _palace_block_text(matched)
                enriched.append(_block(_clip(text, 500), blk.layer, blk.classic_id))
            vol4_sections.append(_section("palaces-explain", "宫位讲解", "fact", enriched))
        elif palaces:
            vol4_sections.append(
                _section(
                    "palaces",
                    "十二宫（节选）",
                    "fact",
                    [_block(_palace_block_text(p)) for p in palaces[:8]],
                )
            )
        # 命身轴已并入 meta，避免重复短块；若尚无 meta（极端缺字段），回落单独节
        if not any(s.id == "ziwei-meta" for s in vol4_sections):
            vol4_sections.append(
                _section(
                    "palace-axis",
                    "命身轴",
                    "fact",
                    [
                        _block(
                            f"命宫干支 {ziwei.get('life_palace_gz', '—')}；"
                            f"身宫干支 {ziwei.get('body_palace_gz', '—')}；"
                            f"五行局 {ziwei.get('wuxing_ju_name', '—')}"
                        )
                    ],
                )
            )
    else:
        vol4_sections.append(_section("ziwei-empty", "紫微", "fact", [_block("紫微数据待载入。")]))

    vol5_sections: list[VolumeSectionModel] = []
    domain_blocks = _explain_sections(explain_bazi, "domains")
    if domain_blocks:
        vol5_sections.append(
            _section("domains-explain", "事之理推断", "inference", domain_blocks, collapsed_default=True)
        )
    for key, label in (
        ("personality", "性格"),
        ("career", "事业"),
        ("wealth_analysis", "财运"),
    ):
        block = bazi.get(key)
        if isinstance(block, dict) and block.get("interpretation_text"):
            vol5_sections.append(
                _section(
                    f"domain-{key}",
                    label,
                    "inference",
                    [_block(_clip(block["interpretation_text"], 120))],
                    collapsed_default=True,
                )
            )
    if not vol5_sections:
        vol5_sections.append(
            _section("vol5-empty", "事之理", "inference", [_block("域分析待 explain 接入。")], collapsed_default=True)
        )

    vol6_sections = [
        _section(
            "vol6-on-demand",
            "问书助手",
            "inference",
            [
                _block(
                    "卷六为问书助手：需用户主动展开后选择事业/婚恋等模块提问；"
                    "打磨期不自动调用 LLM，避免首屏静默消耗。展开后即可与排盘事实对照追问。",
                    "fact",
                )
            ],
            collapsed_default=True,
        )
    ]

    colophon_vol_sections = [
        _section(
            "colophon-summary",
            "校勘摘要",
            "fact",
            [
                _block(line)
                for line in _build_colophon(
                    missing_fields=missing,
                    iztro_advisory=iztro_advisory,
                    wenmo_advisory=wenmo_advisory,
                    engine_label="bazi+ziwei",
                ).summary_lines
            ],
        )
    ]

    volumes = _apply_volume_locks(
        [
            LifeVolumeModel(id="preface", title=LIFE_VOLUME_LABELS["preface"], sections=preface_sections),
            LifeVolumeModel(id="vol1", title=LIFE_VOLUME_LABELS["vol1"], sections=vol1_sections),
            LifeVolumeModel(id="vol2", title=LIFE_VOLUME_LABELS["vol2"], sections=vol2_sections),
            LifeVolumeModel(id="vol3", title=LIFE_VOLUME_LABELS["vol3"], sections=vol3_sections),
            LifeVolumeModel(id="vol4", title=LIFE_VOLUME_LABELS["vol4"], sections=vol4_sections),
            LifeVolumeModel(id="vol5", title=LIFE_VOLUME_LABELS["vol5"], sections=vol5_sections),
            LifeVolumeModel(id="vol6", title=LIFE_VOLUME_LABELS["vol6"], sections=vol6_sections),
            LifeVolumeModel(id="colophon", title=LIFE_VOLUME_LABELS["colophon"], sections=colophon_vol_sections),
        ],
        entitlement,
    )

    disclaimer_raw = explain_bazi.get("disclaimer_block") or default_disclaimer_block()
    return LifeVolumeResponseModel(
        case_id=case_id,
        chart_hash=chart_hash,
        rule_version=bazi.get("rule_version"),
        content_versions=explain_bazi.get("content_versions") or content_versions_meta(),
        disclaimer_block=DisclaimerBlockModel(**disclaimer_raw),
        trust_level=trust_level,
        volumes=volumes,
        colophon=_build_colophon(
            missing_fields=missing,
            iztro_advisory=iztro_advisory,
            wenmo_advisory=wenmo_advisory,
            engine_label="bazi+ziwei",
        ),
    )


async def build_life_volumes_for_case(
    case: Case,
    *,
    request_id: str | None = None,
    entitlement: EntitlementTier = "full_book",
) -> LifeVolumeResponseModel:
    from routers.bazi import _normalize_birth_dt_text
    from routers.ziwei import _chart_to_response, _ziwei_full_args
    from services.content_policy import content_versions_meta, default_disclaimer_block, default_wenmo_advisory

    dt = _normalize_birth_dt_text(case.birth_dt_local, case.tz or "Asia/Shanghai")
    bazi_req = BaziFullRequest(
        dt=dt,
        lon=float(case.lon),
        tz=case.tz or "Asia/Shanghai",
        gender=case.gender or "male",
        solar_time_enabled=bool(case.solar_time_enabled),
    )
    snapshot = build_bazi_snapshot(bazi_req, request_id=request_id or f"life-volume-{case.id}")
    bazi_resp = snapshot.response
    bazi = bazi_resp.model_dump(mode="json")

    ziwei_req = ZiweiRequest(
        year=dt.year,
        month=dt.month,
        day=dt.day,
        hour=dt.hour,
        minute=dt.minute,
        gender="女" if (case.gender or "").lower() == "female" else "男",
        longitude=float(case.lon) if case.solar_time_enabled else None,
        year_divide=getattr(case, "year_divide", "lichun") or "lichun",
        day_divide=getattr(case, "day_divide", "solar_next") or "solar_next",
    )
    chart = await asyncio.to_thread(ziwei_full, *_ziwei_full_args(ziwei_req))
    ziwei_resp: ZiweiResponse = apply_trust_level(
        _chart_to_response(
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
            },
        ).model_copy(
            update={
                "disclaimer_block": DisclaimerBlockModel(**default_disclaimer_block()),
                "content_versions": content_versions_meta(),
                "wenmo_advisory": default_wenmo_advisory(),
            }
        )
    )
    ziwei = ziwei_resp.model_dump(mode="json")

    explain_bazi = explain_bazi_batch(
        ExplainBatchRequest(**bazi_req.model_dump(), sections=["geju", "relations", "domains"]),
    ).model_dump(mode="json")
    explain_ziwei = explain_ziwei_batch(
        ZiweiExplainBatchRequest(**ziwei_req.model_dump(), sections=["palaces", "fortune"]),
    ).model_dump(mode="json")

    return build_life_volumes_from_charts(
        case_id=case.id,
        chart_hash=snapshot.chart_hash,
        bazi=bazi,
        ziwei=ziwei,
        explain_bazi=explain_bazi,
        explain_ziwei=explain_ziwei,
        profile_label=case.name,
        entitlement=entitlement,
    )
