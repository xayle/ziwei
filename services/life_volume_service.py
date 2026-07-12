"""Build life-volume@1.0 responses (R096 draft · W16 authority path)."""

from __future__ import annotations

import asyncio
from typing import Any

from app.models import Case
from app.schemas import BaziFullRequest
from app.schemas.disclaimer import DisclaimerBlockModel
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


def _relations_text(bazi: dict[str, Any]) -> str:
    rs = bazi.get("relations_summary") or {}
    items = rs.get("items") or []
    if not items:
        return "干支关系摘要待补全。"
    parts = []
    for item in items[:6]:
        if isinstance(item, dict):
            parts.append(item.get("label") or item.get("type") or str(item))
        else:
            parts.append(str(item))
    return "；".join(p for p in parts if p) or "干支关系摘要待补全。"


def _shensha_text(bazi: dict[str, Any]) -> str:
    ss = bazi.get("shensha_summary") or {}
    highlights = ss.get("highlights") or []
    if highlights:
        return "、".join(str(h) for h in highlights[:8])
    items = ss.get("items") or bazi.get("shensha") or []
    names = [str(i.get("name")) for i in items if isinstance(i, dict) and i.get("name")]
    return "、".join(names[:8]) if names else "神煞摘要待补全。"


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
            blocks.append(
                AnalysisBlockModel(
                    text=_clip(raw.get("text", "")),
                    layer=raw.get("layer", "fact"),
                    classic_id=raw.get("classic_id"),
                )
            )
        return blocks
    return []


def _build_colophon(
    *,
    missing_fields: list[str],
    iztro_advisory: str | None,
    wenmo_advisory: str | None,
    engine_label: str,
) -> ColophonModel:
    lines: list[str] = [f"引擎 {engine_label}"]
    if missing_fields:
        lines.append(f"缺失字段：{'、'.join(missing_fields[:4])}")
    else:
        lines.append("排盘字段齐备，可核对卷内 fact/cite/inference 分层。")
    if iztro_advisory:
        lines.append(_clip(iztro_advisory, 72))
    return ColophonModel(
        summary_lines=lines[:3],
        missing_fields=missing_fields or None,
        iztro_advisory=iztro_advisory,
        wenmo_advisory=wenmo_advisory,
        expandable=True,
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

    preface_sections: list[VolumeSectionModel] = []
    if profile_label:
        preface_sections.append(_section("archive-label", "辑录对象", "fact", [_block(profile_label)]))
    preface_sections.append(
        _section(
            "reading-guide",
            "读法导览",
            "fact",
            [_block("卷一至卷五按 fact·cite·inference 分层；卷六问书需主动展开。", "fact")],
        )
    )

    vol1_sections = [
        _section(
            "pillars",
            "四柱根气",
            "fact",
            [_block(f"日主 {day.get('stem', '—')}{day.get('branch', '—')}；格局 {geju.get('geju_name', '待分析')}。")],
        ),
    ]
    geju_blocks = _explain_sections(explain_bazi, "geju")
    if geju_blocks:
        vol1_sections.append(_section("geju-explain", "格局讲解", "cite", geju_blocks))

    vol2_sections = [
        _section("relations", "干支关系", "fact", [_block(_relations_text(bazi))]),
        _section("shensha", "神煞摘要", "fact", [_block(_shensha_text(bazi))]),
    ]
    rel_blocks = _explain_sections(explain_bazi, "relations")
    if rel_blocks:
        vol2_sections.append(_section("relations-explain", "关系讲解", "fact", rel_blocks))

    vol3_sections: list[VolumeSectionModel] = []
    dayun_items = ((bazi.get("dayun") or {}).get("items") or [])[:5]
    if dayun_items:
        vol3_sections.append(
            _section(
                "dayun",
                "大运序列",
                "fact",
                [
                    _block(
                        f"{item.get('start_age', '—')}–{item.get('end_age', '—')}岁 "
                        f"{item.get('stem', '')}{item.get('branch', '')}".strip()
                    )
                    for item in dayun_items
                    if isinstance(item, dict)
                ],
            )
        )
    else:
        vol3_sections.append(_section("dayun-empty", "运限", "fact", [_block("大运序列待载入。")]))

    vol4_sections: list[VolumeSectionModel] = []
    if ziwei:
        vol4_sections.append(
            _section(
                "life-palace",
                "命宫",
                "fact",
                [_block(f"命宫 {ziwei.get('life_palace_gz', '—')} · {ziwei.get('wuxing_ju_name', '—')}")],
            )
        )
        palace_blocks = _explain_sections(explain_ziwei, "palaces")
        if palace_blocks:
            vol4_sections.append(_section("palaces-explain", "宫位讲解", "fact", palace_blocks))
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
            [_block("卷六叙事与 LLM 解读需用户主动展开，不在首屏自动加载。", "fact")],
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

    volumes = [
        LifeVolumeModel(id="preface", title=LIFE_VOLUME_LABELS["preface"], sections=preface_sections),
        LifeVolumeModel(id="vol1", title=LIFE_VOLUME_LABELS["vol1"], sections=vol1_sections),
        LifeVolumeModel(id="vol2", title=LIFE_VOLUME_LABELS["vol2"], sections=vol2_sections),
        LifeVolumeModel(id="vol3", title=LIFE_VOLUME_LABELS["vol3"], sections=vol3_sections),
        LifeVolumeModel(id="vol4", title=LIFE_VOLUME_LABELS["vol4"], sections=vol4_sections),
        LifeVolumeModel(id="vol5", title=LIFE_VOLUME_LABELS["vol5"], sections=vol5_sections),
        LifeVolumeModel(id="vol6", title=LIFE_VOLUME_LABELS["vol6"], sections=vol6_sections),
        LifeVolumeModel(id="colophon", title=LIFE_VOLUME_LABELS["colophon"], sections=colophon_vol_sections),
    ]

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


async def build_life_volumes_for_case(case: Case, *, request_id: str | None = None) -> LifeVolumeResponseModel:
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
                "disclaimer_block": default_disclaimer_block(),
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
    )
