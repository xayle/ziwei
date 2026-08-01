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


def _verified_cite_blocks_from_refs(refs: list[dict[str, Any]], *, limit: int = 2) -> list[AnalysisBlockModel]:
    """candidates 中 hint_type=verified 的条目 → cite 块（E-01）。"""
    out: list[AnalysisBlockModel] = []
    for ref in refs:
        if ref.get("hint_type") != "verified":
            continue
        src = str(ref.get("source") or "").strip()
        quote = str(ref.get("text") or "").strip()
        if not quote:
            continue
        body = f"典籍依据（{src}）：{quote}" if src else f"典籍依据：{quote}"
        out.append(_block(_clip(body, 220), "cite", str(ref.get("id") or "") or None))
        if len(out) >= limit:
            break
    return out


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
    """截断时优先落在句号/分号等边界，避免格局/用神类长句拦腰切断。"""
    t = (text or "").strip()
    if len(t) <= limit:
        return t
    window = t[:limit]
    min_keep = max(40, int(limit * 0.55))
    best = -1
    for sep in ("。", "！", "？", "；", "\n"):
        idx = window.rfind(sep)
        if idx >= min_keep and idx > best:
            best = idx
    if best >= 0:
        return window[: best + 1]
    trimmed = window.rstrip("，、；：,.; ")
    if len(trimmed) < max(20, int(limit * 0.4)):
        trimmed = window[: limit - 1]
    return f"{trimmed}…"


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


def _relations_impact_text(bazi: dict[str, Any]) -> str:
    """卷二关系读法：何意 / 对本命影响（约 110–180 字）。"""
    rs = bazi.get("relations_summary") if isinstance(bazi.get("relations_summary"), dict) else {}
    base = _relations_text(bazi)
    bits: list[str] = []
    clash = str((rs or {}).get("clash_summary") or "").strip()
    combine = str((rs or {}).get("combine_summary") or "").strip()
    harm = str((rs or {}).get("harm_summary") or "").strip()
    interaction = str((rs or {}).get("interaction_summary") or "").strip()
    if clash:
        bits.append(
            f"冲克见「{clash[:48]}」，对本命常表现为节奏冲突与立场拉扯："
            "行事宜避硬碰硬，先稳后进，重大表态前多留一步缓冲；"
            "冲突年份尤忌临时起意的重大签约。"
        )
    if combine or "合" in base or "拱" in base:
        bits.append(
            "会合或拱合提示人际与资源有牵绊：宜借合力成事，"
            "也忌纠缠不清、把人情债当成唯一路径；合多之时更要分清谁在借力、谁在消耗。"
        )
    if harm:
        bits.append(
            f"害破信号「{harm[:36]}」，协作、契约与口头承诺宜留余地，" "避免一次把话说满，也避免把误会拖成长期对立。"
        )
    if not bits and interaction:
        bits.append(
            f"干支互动要点：{interaction[:80]}。"
            "阅读时先认清主线，再对照神煞与卷三运限起伏，把关键词落到可观察的行事节奏。"
        )
    if not bits:
        bits.append(
            f"命局干支关系为「{base[:72]}」。" "阅读时先分清冲合主线，再对照神煞与运限起伏，勿以单次关系论断终身。"
        )
    text = "".join(bits)
    if len(text) < 120:
        text = f"{text}本节是排盘事实之上的读法提示，用来帮助串联卷一格局与卷三运限，" "不作绝对断语。"
    return _clip(text, 280)


def _iter_shensha_items(bazi: dict[str, Any]) -> list[dict[str, Any]]:
    ss = bazi.get("shensha_summary") or {}
    items = ss.get("items") if isinstance(ss, dict) else None
    if not items:
        items = bazi.get("shensha") or []
    return [i for i in items if isinstance(i, dict) and i.get("name")]


def _shensha_is_beneficial(item: dict[str, Any]) -> bool | None:
    if "is_beneficial" in item:
        return bool(item.get("is_beneficial"))
    pol = str(item.get("polarity") or "").strip().lower()
    if pol in {"+", "auspicious", "good", "吉", "beneficial"}:
        return True
    if pol in {"-", "inauspicious", "bad", "凶", "慎"}:
        return False
    return None


def _shensha_text(bazi: dict[str, Any]) -> str:
    ss = bazi.get("shensha_summary") or {}
    highlights = ss.get("highlights") or []
    if highlights:
        return "、".join(str(h) for h in highlights[:8])
    names = [str(i.get("name")) for i in _iter_shensha_items(bazi)]
    return "、".join(names[:8]) if names else "神煞摘要待补全。"


def _relations_classic_quote_blocks(bazi: dict[str, Any]) -> list[AnalysisBlockModel]:
    """挂载地支冲合刑害典籍；verified→cite，soft→inference（E-01）。"""
    from services.bazi_engine.classic_refs import relations_candidates

    rs = bazi.get("relations_summary") if isinstance(bazi.get("relations_summary"), dict) else {}
    blocks: list[AnalysisBlockModel] = []
    for ref in relations_candidates(rs, limit=3):
        src = str(ref.get("source") or "").strip()
        quote = str(ref.get("text") or "").strip()
        rid = str(ref.get("id") or "").strip()
        if not quote:
            continue
        src_bit = f"（{src}）" if src else ""
        hint = str(ref.get("hint_type") or "soft").strip().lower()
        verified = hint in {"verified", "hard", "cite"}
        if verified:
            body = f"典籍依据{src_bit}：{quote}"
            blocks.append(_block(_clip(body, 220), "cite", rid or None))
        else:
            body = f"关系典籍软提示{src_bit}：{quote}（软提示，待校勘升格前不作「典籍依据」。）"
            blocks.append(_block(_clip(body, 220), "inference", rid or None))
    return blocks


def _shensha_classic_quote_blocks(bazi: dict[str, Any]) -> list[AnalysisBlockModel]:
    """挂载神煞 classic_refs 正文；soft→inference，verified→cite（E-01）。"""
    blocks: list[AnalysisBlockModel] = []
    seen_ids: set[str] = set()
    for item in _iter_shensha_items(bazi)[:12]:
        name = str(item.get("name") or "").strip()
        picked: dict[str, Any] | None = None
        for ref in item.get("classic_refs") or []:
            if not isinstance(ref, dict):
                continue
            quote = str(ref.get("text") or "").strip()
            if not quote:
                continue
            rid = str(ref.get("id") or "").strip()
            if rid and rid in seen_ids:
                continue
            picked = ref
            break
        if not picked:
            continue
        rid = str(picked.get("id") or "").strip()
        if rid:
            seen_ids.add(rid)
        src = str(picked.get("source") or item.get("classic_source") or "").strip()
        quote = str(picked.get("text") or "").strip()
        hint = str(picked.get("hint_type") or "soft").strip().lower()
        layer = "cite" if hint in {"verified", "hard", "cite"} else "inference"
        src_bit = ""
        if src:
            src_bit = f"（{src}）" if src.startswith("《") else f"（《{src}》）"
        body = f"{name or '神煞'}{src_bit}：{quote}"
        if layer == "inference":
            body = f"{body}（软提示，待校勘升格前不作「典籍依据」。）"
        blocks.append(_block(_clip(body, 220), layer, rid or None))
        if len(blocks) >= 3:
            break
    return blocks


def _shensha_polarity_texts(bazi: dict[str, Any]) -> tuple[str, str]:
    """返回（吉神段, 慎神段）。"""
    good: list[str] = []
    caution: list[str] = []
    unknown: list[str] = []
    for item in _iter_shensha_items(bazi)[:16]:
        name = str(item.get("name") or "").strip()
        if not name:
            continue
        flag = _shensha_is_beneficial(item)
        if flag is True:
            good.append(name)
        elif flag is False:
            caution.append(name)
        else:
            unknown.append(name)
    if not good and not caution and unknown:
        joined = "、".join(unknown[:8])
        return (
            f"神煞见{joined}。吉凶未在摘要中分列，宜结合格局、用神与刑冲综合看，"
            "把神煞当作旁证而非结论；贵人类信号可主动借力，灾煞类信号则宜留余地。",
            "慎神分列待补：当前引擎未给出明确极性，阅读时以格局与刑冲为主、神煞为辅，" "勿因名单长短夸大吉凶。",
        )
    if not good and not caution:
        base = _shensha_text(bazi)
        return (
            f"神煞要点：{base}。宜视为格局旁证：有吉神不代表万事顺遂，" "仍须回到日主强弱与用神是否得力。",
            "暂无单独慎神分列；若后文出现灾煞、劫煞等，重大决策宜缓、契约宜细看，" "并把风险对照到卷三流年节点。",
        )
    ji = (
        f"吉神见{'、'.join(good[:8])}。提示贵人、文书、名望或护持机会："
        "宜主动借力、守信用，把贵人线索落到具体合作、引荐与学习场景，"
        "并与卷一用神对照；有吉神不等于万事顺遂，仍须看是否得令、是否被冲破。"
        if good
        else "本盘摘要未突出吉神；仍可从正印、贵人类格局与日主喜用中寻找护持线索，"
        "不必因名单偏短而气馁，也勿另造吉神叙事。"
    )
    shen = (
        f"慎神见{'、'.join(caution[:8])}。提示口舌、波动、损耗或刚愎风险："
        "重大决策宜缓、契约宜细看，情绪上头时少做不可逆承诺；"
        "把风险落到具体事项与卷三流年节点，比空谈凶神更有用；"
        "若与刑冲同现，优先处理关系张力再谈扩张。"
        if caution
        else "摘要未单列慎神；仍须对照刑冲、害破与流年再判风险，"
        "把谨慎落在具体月份与事项上，避免把名单长短当成命运判决。"
    )
    if unknown:
        ji = f"{ji}另有未分极性者：{'、'.join(unknown[:4])}，宜回看其落柱与十神再判。"
    return _clip(ji, 260), _clip(shen, 260)


def _enrich_vol_block(label: str, body: str, *, floor: int = 40) -> str:
    """短事实块补读法衬底；已够长则不再套话（V2-04）。"""
    trimmed = str(body or "").strip()
    if len(trimmed) >= floor:
        return trimmed
    combined = f"{label}：{trimmed}。详见本节与相邻讲解；以排盘事实为准，勿单句外推。"
    pad = "宜对照卷内相邻章节一并阅读。"
    while len(combined) < floor:
        combined = f"{combined}{pad}"
        pad = "。"
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
            # 格局讲解优先保完整句；其它 explain 节仍用默认上限
            limit = 500 if section_id == "geju" else 280
            blocks.append(
                AnalysisBlockModel(
                    text=_clip(text, limit),
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
    # E-02：summary 上限 3 行；语料行反映 verified 进度（非「核验中」空话）
    from services.content_policy import verified_engine_ref_count

    n_engine = verified_engine_ref_count()
    lines: list[str] = [
        f"校勘：引擎 {engine_label}；排盘字段{'有注记见下行' if missing_fields else '齐备'}，可核对卷内事实 / 典籍 / 推断分层。",
        (
            f"典籍语料：已核验引擎条 {n_engine} 条；仅 layer=cite 且 verified 标「典籍依据」，"
            "软提示见卷二；冲合会专条已挂宿主真子集。"
        ),
    ]
    if missing_fields:
        labels = [_missing_field_label(f) for f in missing_fields[:4]]
        lines.append(f"字段注记：{'、'.join(labels)}（不影响已写出块；对照项非故障，展开脚注可核）。")
    elif iztro_advisory:
        lines.append(_clip(iztro_advisory, 100))
    else:
        lines.append("双轨核验：可对照开源排盘与文墨对照盘（若有）；对照差异见脚注，不改写主卷事实。")
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
                    "全书按三层阅读：排盘推算（干支、宫星、运限等引擎事实）、"
                    "典籍依据（有出处的句式与校勘）、经验推断（可读建议，默认不代替事实）。"
                    "界面只用上述中文标签，不夹写英文层名。",
                    "fact",
                ),
                _block(
                    "建议顺序：卷一格局与用神 → 卷二关系与神煞 → 卷三大运流年 → "
                    "卷四命身轴与十二宫 → 卷五事理（默认折叠）→ 卷六问书（需主动展开）。"
                    "先立事实与读法，再追问具体事项；卷六不自动发起问书。",
                    "fact",
                ),
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
    # 格局典籍：仅 verified 进 cite；裸 classic_ref 字符串不得冒充 cite（E-01）
    from services.bazi_engine.classic_refs import geju_candidates

    geju_verified = [r for r in geju_candidates(geju_name, limit=2) if r.get("hint_type") == "verified"]
    if geju_verified:
        cite_blocks = []
        for ref in geju_verified:
            src = str(ref.get("source") or "").strip()
            quote = str(ref.get("text") or "").strip()
            if not quote:
                continue
            body = f"典籍依据（{src}）：{quote}" if src else f"典籍依据：{quote}"
            cite_blocks.append(_block(_clip(body, 220), "cite", str(ref.get("id") or "") or None))
        if cite_blocks:
            vol1_sections.append(_section("geju-cite", "典籍句式", "cite", cite_blocks))
    elif str(geju.get("classic_ref") or "").strip():
        vol1_sections.append(
            _section(
                "geju-classic-soft",
                "格局典籍软提示",
                "inference",
                [_block(_clip(str(geju.get("classic_ref")), 500), "inference")],
            )
        )
    yong = bazi.get("yongshen") or {}
    if isinstance(yong, dict) and (yong.get("favor") or yong.get("avoid")):
        favor = "、".join(str(x) for x in (yong.get("favor") or []) if str(x).strip()) or "—"
        avoid = "、".join(str(x) for x in (yong.get("avoid") or []) if str(x).strip()) or "—"
        yong_body = (
            f"喜用 {favor}；忌 {avoid}。"
            "用神须与格局、日主强弱同参：得令得助则宜顺用神拓展，"
            "失令受克则先避忌神、再谈进取。"
        )
        vol1_sections.append(
            _section(
                "yongshen",
                "用神",
                "fact",
                [_block(_enrich_vol_block("卷一用神", yong_body))],
            )
        )
        from services.bazi_engine.classic_refs import yongshen_candidates

        yong_cite = []
        for ref in yongshen_candidates(limit=2):
            if ref.get("hint_type") != "verified":
                continue
            src = str(ref.get("source") or "").strip()
            quote = str(ref.get("text") or "").strip()
            if not quote:
                continue
            body = f"典籍依据（{src}）：{quote}" if src else f"典籍依据：{quote}"
            yong_cite.append(_block(_clip(body, 220), "cite", str(ref.get("id") or "") or None))
        if yong_cite:
            vol1_sections.append(_section("yongshen-cite", "典籍句式", "cite", yong_cite))
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
        from services.bazi_engine.classic_refs import daymaster_candidates

        dm_cite = _verified_cite_blocks_from_refs(daymaster_candidates(limit=2))
        if dm_cite:
            vol1_sections.append(_section("daymaster-cite", "典籍句式", "cite", dm_cite))
    from services.bazi_engine.classic_refs import shishen_candidates, wuxing_candidates

    wuxing_cite = _verified_cite_blocks_from_refs(wuxing_candidates(limit=2))
    if wuxing_cite:
        vol1_sections.append(_section("wuxing-cite", "五行典籍句式", "cite", wuxing_cite))
    shishen_cite = _verified_cite_blocks_from_refs(shishen_candidates(limit=2))
    if shishen_cite:
        vol1_sections.append(_section("shishen-cite", "十神典籍句式", "cite", shishen_cite))
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
            # 控 vol1 trunc：域摘要节选，把篇幅留给格局/用神完整句
            for label, tip in list(domains.items())[:2]:
                tip_s = _clip(str(tip or "").strip(), 72)
                if tip_s:
                    bits.append(f"{label}：{tip_s}")
        actions = [str(a).strip() for a in (fortune.get("top3_actions") or [])[:2] if str(a).strip()]
        if actions:
            bits.append("宜行： " + "；".join(_clip(a, 72) for a in actions))
        if bits:
            fortune_text = _clip(" · ".join(bits), 360)
            vol1_sections.append(_section("current-fortune", "当下运势摘要", "fact", [_block(fortune_text)]))
    if str(bazi.get("bazi_summary") or "").strip():
        vol1_sections.append(
            _section(
                "summary-inference",
                "综合总评",
                "inference",
                [_block(_clip(str(bazi.get("bazi_summary")), 360), "inference")],
                collapsed_default=True,
            )
        )
    geju_blocks = _explain_sections(explain_bazi, "geju")
    geju_explain_fact = [b for b in geju_blocks if b.layer == "fact"]
    geju_explain_cite = [b for b in geju_blocks if b.layer == "cite"]
    geju_explain_soft = [b for b in geju_blocks if b.layer == "inference"]
    # 讲解正文（fact + explain cite 长文）进 geju-explain；verified 短句另见 geju-cite
    geju_guide = geju_explain_fact + geju_explain_cite
    if geju_guide:
        vol1_sections.append(_section("geju-explain", "格局讲解", "fact", geju_guide))
    if geju_explain_soft and not geju_verified:
        vol1_sections.append(_section("geju-classic-soft", "格局典籍软提示", "inference", geju_explain_soft[:2]))

    ji_text, shen_text = _shensha_polarity_texts(bazi)
    relations_fact = (
        f"干支关系摘要：{_relations_text(bazi)}。"
        "以上为排盘事实层要点（合冲刑害等），细读见下一节「关系读法」；"
        "勿将关键词名单直接等同于终身性格结论，也勿跳过格局与用神单独解读关系。"
        "有 explain 关系讲解时，以讲解与本摘要互参。"
    )
    vol2_sections = [
        _section(
            "relations",
            "干支关系",
            "fact",
            [_block(_enrich_vol_block("干支关系", relations_fact))],
        ),
        _section(
            "relations-reading",
            "关系读法",
            "inference",
            [_block(_relations_impact_text(bazi), "inference")],
        ),
        _section(
            "shensha-auspicious",
            "吉神",
            "fact",
            [_block(_enrich_vol_block("吉神", ji_text))],
        ),
        _section(
            "shensha-caution",
            "慎神",
            "fact",
            [_block(_enrich_vol_block("慎神", shen_text))],
        ),
    ]
    rel_blocks = _explain_sections(explain_bazi, "relations")
    # 仅 layer=cite 进典籍句式；带 classic_id 的 soft/inference 不得冒充 cite（E-01）
    cite_from_explain = [b for b in rel_blocks if b.layer == "cite"]
    explain_soft = [b for b in rel_blocks if b.layer == "inference"]
    explain_fact = [b for b in rel_blocks if b.layer not in {"cite", "inference"}]
    if explain_fact:
        vol2_sections.append(_section("relations-explain", "关系讲解", "fact", explain_fact))
    relations_cite_ok = bool(cite_from_explain)
    engine_rel_quotes = [] if explain_soft else _relations_classic_quote_blocks(bazi)
    engine_rel_cite = [b for b in engine_rel_quotes if b.layer == "cite"]
    engine_rel_soft = [b for b in engine_rel_quotes if b.layer != "cite"]
    if cite_from_explain:
        vol2_sections.append(_section("relations-cite", "典籍句式", "cite", cite_from_explain[:3]))
    else:
        # explain 未给出 verified cite 时，按冲合信号挂已核验篇章摘句
        from services.relations_classic_cite import pick_relations_verified_cites

        rs = bazi.get("relations_summary") if isinstance(bazi.get("relations_summary"), dict) else {}
        verified_cites = []
        for cite in pick_relations_verified_cites(rs, limit=2):
            body = f"典籍依据（{cite['title']}）：{cite['passage']}"
            if len(body) < 40:
                body = f"{body}宜与干支关系事实互参，不作单句断语。"
            verified_cites.append(_block(_clip(body, 220), "cite", cite["id"]))
        if verified_cites:
            relations_cite_ok = True
            vol2_sections.append(_section("relations-cite", "典籍句式", "cite", verified_cites))
        elif engine_rel_cite:
            relations_cite_ok = True
            vol2_sections.append(_section("relations-cite", "典籍句式", "cite", engine_rel_cite[:3]))
    # 关系软提示：优先 explain inference；否则仅未 verified 的地支候选
    rel_soft = explain_soft or engine_rel_soft
    if rel_soft:
        vol2_sections.append(_section("relations-classic-soft", "关系典籍软提示", "inference", rel_soft[:3]))
    quote_blocks = _shensha_classic_quote_blocks(bazi)
    if quote_blocks:
        cite_q = [b for b in quote_blocks if b.layer == "cite"]
        soft_q = [b for b in quote_blocks if b.layer != "cite"]
        if cite_q:
            vol2_sections.append(_section("shensha-cite", "典籍句式", "cite", cite_q))
        if soft_q:
            vol2_sections.append(_section("shensha-classic-soft", "神煞典籍软提示", "inference", soft_q))
    if not relations_cite_ok and not quote_blocks and not rel_soft:
        vol2_sections.append(
            _section(
                "vol2-cite-pending",
                "典籍句式",
                "cite",
                [
                    _block(
                        "卷二典籍句式待校勘：关系与神煞的古籍正文尚未挂载。"
                        "阅读时以排盘事实、关系读法与吉神/慎神分列为准，把神煞当旁证；"
                        "典籍句式补齐后再对照引用。在此之前，不作断语，也不用口语替代典籍。"
                        "校勘进度见卷末跋；若 explain 已挂 cite，本注会被典籍句式节替换。",
                        "cite",
                    )
                ],
            )
        )

    vol3_sections: list[VolumeSectionModel] = []
    from services.bazi_engine.classic_refs import dayun_candidates, liunian_candidates

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
        dayun_cite = _verified_cite_blocks_from_refs(dayun_candidates(limit=2))
        if dayun_cite:
            vol3_sections.append(_section("dayun-cite", "典籍句式", "cite", dayun_cite))
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
        liunian_cite = _verified_cite_blocks_from_refs(liunian_candidates(limit=2))
        if liunian_cite:
            vol3_sections.append(_section("liunian-cite", "典籍句式", "cite", liunian_cite))
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
                        "以下宫图与格局均围绕命身轴展开，勿先扫十二宫再回头找主轴。"
                    )
                ],
            )
        )
        vol4_sections.append(
            _section(
                "ziwei-reading",
                "宫图读法",
                "inference",
                [
                    _block(
                        "先看命身轴：命宫看主星气质与一生底色，身宫看行运着力与身心投注处；"
                        "两宫同参，才谈得上格局高低。"
                        "再看三方四正（命、财帛、官禄与对宫），把握事业、财帛与压力来源，"
                        "比逐宫平铺更易抓住主线。"
                        "然后才扫各宫主星、辅星与四化；格局条文用来印证命身轴，"
                        "不代替「先轴后方」的阅读顺序。",
                        "inference",
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
    from services.bazi_engine.classic_refs import health_candidates, marriage_candidates

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
    marriage_cite = _verified_cite_blocks_from_refs(marriage_candidates(limit=2))
    if marriage_cite:
        vol5_sections.append(_section("marriage-cite", "婚恋典籍句式", "cite", marriage_cite, collapsed_default=True))
    health_cite = _verified_cite_blocks_from_refs(health_candidates(limit=2))
    if health_cite:
        vol5_sections.append(_section("health-cite", "健康典籍句式", "cite", health_cite, collapsed_default=True))
    if not vol5_sections:
        vol5_sections.append(
            _section("vol5-empty", "事之理", "inference", [_block("域分析待 explain 接入。")], collapsed_default=True)
        )

    _vol6_modules = "大运叙述、流年建议、事业详解、婚恋详解、财富详解、风水建议"
    vol6_sections = [
        _section(
            "vol6-on-demand",
            "问书助手",
            "inference",
            [
                _block(
                    "卷六为问书助手：需主动展开后选择模块提问。"
                    "打磨期不自动调用问书，避免首屏静默消耗额度或打断阅读节奏；"
                    "展开后即可把排盘事实、卷二神煞读法与卷三运限对照追问，"
                    "把「怎么问」当作阅读延伸，而非另开玄学聊天。提问前请先确认已读卷一与卷三要点。",
                    "fact",
                )
            ],
            collapsed_default=True,
        ),
        _section(
            "vol6-how-to-ask",
            "怎么问",
            "inference",
            [
                _block(
                    "示例一（事业）：结合卷一格局与当前大运，今年事业宜进取还是守成？"
                    "若要换赛道或谈晋升，有哪些方向更贴用神、哪些宜暂缓？"
                    "请用可执行建议回答，并标明依据来自格局还是运限。",
                    "inference",
                ),
                _block(
                    "示例二（婚恋）：对照卷二神煞与配偶宫线索，近两年感情节奏如何把握？"
                    "沟通、承诺与边界上各要注意什么？"
                    "请避免把刑冲直接当成情绪标签，改成可观察的相处节奏。",
                    "inference",
                ),
                _block(
                    "示例三（流年）：根据卷三流年节选，明年关键节点在哪几个月？"
                    "宜推动什么、宜暂缓什么，如何与当前大运叙事对齐？"
                    "若只能抓两三个月份，请按优先级说明。",
                    "inference",
                ),
            ],
            collapsed_default=True,
        ),
        _section(
            "vol6-bridge",
            "与前卷衔接",
            "inference",
            [
                _block(
                    "建议先读完卷一格局与用神、卷二关系/神煞读法、卷三当前大运与流年节选，"
                    "再打开问书；带着具体年份、生活域或一件待决之事提问，回答更贴盘，"
                    "也更少空泛套话。若前卷尚未读完，可先记下问题，读完再展开本卷。",
                    "inference",
                )
            ],
            collapsed_default=True,
        ),
        _section(
            "vol6-access",
            "使用说明",
            "fact",
            [
                _block(
                    f"未登录时可先完成排盘与前五卷阅读，建立事实底稿；"
                    f"登录后展开本卷，可选择：{_vol6_modules}。"
                    f"各模块需主动发起，不会在首屏自动请求；"
                    f"未登录时也可先浏览示例问法，登录后再正式提问。",
                    "fact",
                )
            ],
            collapsed_default=True,
        ),
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
