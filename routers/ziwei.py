"""
routers/ziwei.py — 紫微斗数 API 路由

POST /api/v1/ziwei/full  → 完整命盘计算
GET  /api/v1/ziwei/demo  → 演示命盘（用黄金测试案例）
"""

from __future__ import annotations

import asyncio
import time as _time

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from starlette.requests import Request
from starlette.responses import Response

from app.schemas.explain import ExplainBatchResponse, ZiweiExplainBatchRequest
from app.schemas.provenance import ResponseProvenance
from app.schemas.ziwei import (
    BorrowedStarSourceModel,
    CompatibilityDimensionResponse,
    CompatibilityRequest,
    CompatibilityResponse,
    DayunItemResponse,
    DayunResponse,
    EventTagResponse,
    EvidenceItemModel,
    FlyingChartResponse,
    FlyingPalaceResponse,
    ForecastResultResponse,
    IztroCrosscheckResponse,
    IztroDualTrackResponse,
    LifeSuggestionResponse,
    LiunianResponse,
    LiuriItem,
    LiuriLiushiResponse,
    LiushiItem,
    LiuyueItem,
    LunarResponse,
    MultiCompatPairResponse,
    MultiCompatRequest,
    MultiCompatResponse,
    PalaceResponse,
    PalaceStructuredAnalysis,
    PalaceWeightModel,
    PatternResponse,
    PeriodForecastResponse,
    RemedyResponse,
    StarInfo,
    ZiweiRequest,
    ZiweiResponse,
)
from services.api_cache import api_response_cache
from services.prometheus_monitoring import (
    record_ziwei_batch,
    record_ziwei_calc,
)
from services.quota_service import enforce_quota
from services.rate_limit import limiter
from services.structured_export_service import build_ziwei_structured_export
from services.ziwei_classic_refs import build_chart_classic_refs, pattern_candidates
from services.ziwei_engine import ZiweiChart, ziwei_full
from services.ziwei_engine.iztro_crosscheck import compare_chart_to_iztro
from services.ziwei_engine.structural_summary import (
    build_chart_structural_summary,
    build_key_months,
    build_key_years,
    build_sanfang_structure,
    build_sihua_trace_entries,
    build_ziwei_structural_summary,
)
from services.ziwei_provenance import build_ziwei_provenance

# 限制并发计算线程数，防止 ThreadPoolExecutor 耐尽
# asyncio.to_thread 默认线程池大小=min(32, cpu+4)，每个请求占用该线程 1-4 秒。
# Semaphore 确保最多 8 个请求同时进入线程池（其余在协程层排队）。
_CALC_SEM = asyncio.Semaphore(8)

router = APIRouter(prefix="/api/v1/ziwei", tags=["紫微斗数"])

# 模板档位常量
_TPL_SIMPLE = "simple"
_TPL_STANDARD = "standard"
_TPL_PRO = "pro"
_PALACE_TEXT_MAX = 80


def _trim_palace_text(text: str | None) -> str:
    if not text:
        return ""
    if len(text) <= _PALACE_TEXT_MAX:
        return text
    return text[:_PALACE_TEXT_MAX].rstrip() + "…"


# 黄金演示案例（与 GET /demo 一致）
_DEMO_REQUEST = ZiweiRequest(
    year=2002,
    month=3,
    day=13,
    hour=14,
    minute=55,
    gender="女",
)

_CSV_INT_OPTIONAL = (
    "liunian_year",
    "flow_lunar_day",
    "flow_liuyue_month",
    "flow_hour_branch",
)
_CSV_FLOAT_OPTIONAL = ("longitude",)
_CSV_STR_METHOD_OPTIONAL = (
    "leap_month_method",
    "year_divide",
    "day_divide",
    "kuiyue_method",
    "tianma_method",
    "tiankong_method",
    "brightness_method",
    "jiukong_method",
    "tianshang_method",
    "mingzhu_method",
    "liunian_sihua_method",
    "changsheng_method",
    "wenchang_method",
    "youbi_method",
    "liunian_life_method",
    "liuyue_method",
    "xiaoxian_start_method",
)


def _normalize_csv_row(row: dict) -> dict[str, str]:
    return {str(k).strip().lower(): (v.strip() if isinstance(v, str) else str(v).strip()) for k, v in row.items()}


def _ziwei_request_from_csv_row(row: dict, template_version: str = _TPL_STANDARD) -> ZiweiRequest:
    """Build ZiweiRequest from a CSV row (supports optional method columns)."""
    r = _normalize_csv_row(row)
    payload: dict = {
        "year": int(r["year"]),
        "month": int(r["month"]),
        "day": int(r["day"]),
        "hour": int(r["hour"]),
        "minute": int(r.get("minute") or "0"),
        "gender": r["gender"],
        "template_version": (
            template_version if template_version in (_TPL_SIMPLE, _TPL_STANDARD, _TPL_PRO) else _TPL_STANDARD
        ),
    }
    for key in _CSV_INT_OPTIONAL:
        if r.get(key):
            payload[key] = int(r[key])
    for key in _CSV_FLOAT_OPTIONAL:
        if r.get(key):
            payload[key] = float(r[key])
    for key in _CSV_STR_METHOD_OPTIONAL:
        if r.get(key):
            payload[key] = r[key]
    if r.get("late_zishi"):
        payload["late_zishi"] = r["late_zishi"].lower() not in {"0", "false", "no", "n"}
    return ZiweiRequest(**payload)


def _ziwei_full_args(req: ZiweiRequest) -> tuple:
    """Unpack ZiweiRequest into ziwei_full() positional args."""
    from services.ziwei_engine.flow_defaults import resolve_flow_params

    flow_day, flow_month, flow_hour = resolve_flow_params(
        template_version=req.template_version,
        include_flow_liuri=req.include_flow_liuri,
        liunian_year=req.liunian_year,
        birth_year=req.year,
        birth_month=req.month,
        birth_day=req.day,
        birth_hour=req.hour,
        birth_minute=req.minute,
        leap_month_method=req.leap_month_method,
        flow_lunar_day=req.flow_lunar_day,
        flow_liuyue_month=req.flow_liuyue_month,
        flow_hour_branch=req.flow_hour_branch,
    )
    return (
        req.year,
        req.month,
        req.day,
        req.hour,
        req.minute,
        req.gender,
        req.liunian_year,
        req.longitude,
        req.late_zishi,
        req.sihua_stem_indices,
        req.leap_month_method,
        req.year_divide,
        req.day_divide,
        req.kuiyue_method,
        req.tianma_method,
        req.tiankong_method,
        req.brightness_method,
        req.jiukong_method,
        req.tianshang_method,
        req.mingzhu_method,
        req.liunian_sihua_method,
        req.changsheng_method,
        req.wenchang_method,
        req.youbi_method,
        req.liunian_life_method,
        req.liuyue_method,
        req.xiaoxian_start_method,
        flow_day,
        flow_month,
        flow_hour,
    )


def _chart_to_response(
    chart: ZiweiChart,
    template: str = _TPL_STANDARD,
    birth: dict | None = None,
    req: ZiweiRequest | None = None,
) -> ZiweiResponse:
    """将 ZiweiChart 数据对象转换为 Pydantic 响应模型。

    Parameters
    ----------
    chart    : ZiweiChart — 计算完毕的命盘数据
    template : "simple" | "standard" | "pro"
        - simple   : 仅核心字段（宫位/星曜/摘要/格局），跳过 forecast/flying/liuyue/详分析/建议
        - standard : 完整命盘（历史默认行为）
        - pro      : 等同 standard，格局 PatternResponse.source 始终保留
    """
    _is_simple = template == _TPL_SIMPLE
    lunar_resp = LunarResponse(
        lunar_year=chart.lunar.lunar_year,
        lunar_month=chart.lunar.lunar_month,
        lunar_day=chart.lunar.lunar_day,
        is_leap_month=chart.lunar.is_leap_month,
        year_gz=chart.lunar.year_gz,
        month_gz=chart.lunar.month_gz,
        hour_branch=chart.lunar.hour_branch,
        jieqi_month_gz=chart.lunar.jieqi_month_gz,
        day_gz=chart.lunar.day_gz,
        hour_gz=chart.lunar.hour_gz,
        year_divide=getattr(chart.lunar, "year_divide", "lichun"),
        day_divide=getattr(chart.lunar, "day_divide", "solar_next"),
    )

    palaces_resp = [
        PalaceResponse(
            index=p.index,
            name=p.name,
            branch=p.branch,
            stem=p.stem,
            main_stars=[
                StarInfo(
                    name=s["name"],
                    brightness=s["brightness"],
                    brightness_val=s["brightness_val"],
                    transforms=s["transforms"],
                )
                for s in p.main_stars
            ],
            aux_stars=[
                StarInfo(
                    name=s["name"],
                    brightness=s["brightness"],
                    brightness_val=s["brightness_val"],
                    transforms=s.get("transforms", []),
                )
                for s in p.aux_stars
            ],
            flying_out=p.flying_out,
            borrowed_main_stars=[
                {
                    "name": s["name"],
                    "brightness": s["brightness"],
                    "brightness_val": s["brightness_val"],
                    "transforms": s.get("transforms", []),
                }
                for s in (next((opp.main_stars for opp in chart.palaces if opp.name == p.opposition_name), []))
            ]
            if not p.main_stars and p.opposition_name
            else [],
            borrowed_from_palace=p.opposition_name if not p.main_stars and p.opposition_name else None,
            borrowed_reason="空宫借对宫主星论命" if not p.main_stars and p.opposition_name else None,
            is_empty_palace=not bool(p.main_stars),
            analysis=_trim_palace_text(p.analysis) if not _is_simple else p.analysis,
            analysis_tags=p.analysis_tags,
            xiaoxian_ages=p.xiaoxian_ages,
            opposition_name=p.opposition_name,
            conclusion=_trim_palace_text(p.conclusion) if not _is_simple else p.conclusion,
            explanation=_trim_palace_text(p.explanation) if not _is_simple else p.explanation,
            suggestion=_trim_palace_text(p.suggestion) if not _is_simple else p.suggestion,
            tooltip=_trim_palace_text(p.tooltip) if not _is_simple else p.tooltip,
            dayun_boshi=p.dayun_boshi,
            changsheng=p.changsheng,
            jiangqian_star=p.jiangqian_star,
            suiqian_star=p.suiqian_star,
        )
        for p in chart.palaces
    ]

    dayun_resp = DayunResponse(
        forward=chart.dayun.forward,
        start_age=chart.dayun.start_age,
        start_age_exact=chart.dayun.start_age_exact,
        start_age_text=chart.dayun.start_age_text,
        items=[
            DayunItemResponse(
                index=d.index,
                ganzhi=d.ganzhi,
                branch_idx=d.branch_idx,
                start_age=d.start_age,
                end_age=d.end_age,
                start_year=d.start_year,
                sihua=d.sihua,
                boshi_stars=d.boshi_stars,
            )
            for d in chart.dayun.items
        ],
    )

    liunian_resp = None
    if chart.liunian:
        liunian_resp = LiunianResponse(
            year=chart.liunian.year,
            year_gz=chart.liunian.year_gz,
            life_palace_branch=chart.liunian.life_palace_branch,
            sihua=chart.liunian.sihua,
        )

    flying_resp = None
    if chart.flying:
        flying_resp = FlyingChartResponse(
            palaces=[
                FlyingPalaceResponse(
                    palace_name=fp.palace_name,
                    stem_name=fp.stem_name,
                    flying_out=fp.flying_out,
                    opposition_palace=fp.opposition_palace,
                    self_transforms=fp.self_transforms,
                )
                for fp in chart.flying.palaces
            ],
            received=chart.flying.received,
            chonged=chart.flying.chonged,
            self_transforms=chart.flying.self_transforms,
        )

    liuyue_resp = [
        LiuyueItem(
            month=d.month,
            month_name=d.month_name,
            month_gz=d.month_gz,
            life_palace_branch=d.life_palace_branch,
            palace_name=d.palace_name,
            sihua=d.sihua,
        )
        for d in chart.liuyue_data
    ]

    # ── forecast 映射 ────────────────────────────────────────
    forecast_resp = None
    if chart.forecast:
        fc = chart.forecast

        def _map_events(events) -> list[EventTagResponse]:
            return [
                EventTagResponse(
                    category=e.category,
                    level=e.level,
                    description=e.description,
                    source=e.source,
                )
                for e in events
            ]

        def _map_period(p) -> PeriodForecastResponse:
            return PeriodForecastResponse(
                period=p.period,
                ganzhi=p.ganzhi,
                palace_name=p.palace_name,
                overall=p.overall,
                details=p.details,
                events=_map_events(p.events),
                advice=p.advice,
                score=p.score,
                tier=getattr(p, "tier", "neutral"),
                layer=getattr(p, "layer", "heuristic"),
            )

        forecast_resp = ForecastResultResponse(
            year=fc.year,
            yearly=_map_period(fc.yearly),
            monthly=[_map_period(m) for m in fc.monthly],
            current_month=_map_period(fc.current_month) if fc.current_month else None,
            layer=getattr(fc, "layer", "heuristic"),
        )

    patterns_resp = []
    for pt in chart.patterns:
        refs = pattern_candidates(pt.name, limit=2)
        patterns_resp.append(
            PatternResponse(
                name=pt.name,
                level=pt.level,
                description=pt.description,
                palaces=pt.palaces,
                stars=pt.stars,
                source=getattr(pt, "source", ""),
                rule_id=getattr(pt, "rule_id", "") or "",
                tier=getattr(pt, "tier", "heuristic") or "heuristic",
                classic_ref=refs[0].get("text", "") if refs else "",
                classic_refs=refs,
            )
        )

    # ── 报告层摘要：三方四正 / 四化追踪 / 关键年份 / 关键月份 ──────────
    life_palace = next((p for p in chart.palaces if p.index == 0), chart.palaces[0] if chart.palaces else None)
    life_name = life_palace.name if life_palace else "命宫"
    life_branch = life_palace.branch if life_palace else ""
    opposite = next((p for p in chart.palaces if p.index == (0 + 6) % 12), None)
    sanfang = build_sanfang_structure(chart)
    chart_structural_summary = build_chart_structural_summary(chart)
    sihua_trace = build_sihua_trace_entries(chart)
    key_years = build_key_years(chart)
    key_months = build_key_months(chart)

    palace_weights = [
        PalaceWeightModel(
            palace_name=p.name,
            weight=1.0
            if p.branch_idx == chart.life_palace_branch
            else (0.78 if p.branch_idx == chart.body_palace_branch else 0.55),
            reason="命宫/身宫主轴"
            if p.branch_idx in {chart.life_palace_branch, chart.body_palace_branch}
            else "普通宫位",
        )
        for p in chart.palaces[:6]
    ]

    def _star_field(star: object, field: str, default: str = "") -> str:
        if isinstance(star, dict):
            value = star.get(field, default)
        else:
            value = getattr(star, field, default)
        return value if isinstance(value, str) else str(value)

    brightness_map: dict[str, str] = {}
    strong_stars: list[str] = []
    weak_stars: list[str] = []
    for palace in chart.palaces:
        for star in palace.main_stars:
            star_name = _star_field(star, "name")
            brightness = _star_field(star, "brightness")
            brightness_map[star_name] = brightness
            if brightness in {"庙", "旺"} and star_name not in strong_stars:
                strong_stars.append(star_name)
            if brightness in {"陷", "不"} and star_name not in weak_stars:
                weak_stars.append(star_name)

    evidence_chain = [
        EvidenceItemModel(title="命宫", value=chart.life_palace_gz, source="life_palace", confidence="high"),
        EvidenceItemModel(title="身宫", value=chart.body_palace_gz, source="body_palace", confidence="high"),
        EvidenceItemModel(title="五行局", value=chart.wuxing_ju_name, source="wuxing_ju", confidence="high"),
    ]
    for pt in chart.patterns[:6]:
        evidence_chain.append(
            EvidenceItemModel(
                title=pt.name,
                value=pt.description,
                source=getattr(pt, "rule_id", "") or getattr(pt, "source", "") or "patterns",
                confidence="high" if pt.level in ("大吉", "吉") else "medium",
            )
        )

    has_empty_palace = any(not p.main_stars for p in chart.palaces)
    borrowed_palace_rows = [
        {
            "palace": p.name,
            "borrowed_from": p.opposition_name,
            "borrowed_reason": "空宫借对宫主星论命",
            "borrowed_main_stars": [
                {
                    "name": s["name"],
                    "brightness": s["brightness"],
                    "brightness_val": s["brightness_val"],
                    "transforms": s.get("transforms", []),
                }
                for s in (next((opp.main_stars for opp in chart.palaces if opp.name == p.opposition_name), []))
            ],
        }
        for p in chart.palaces
        if not p.main_stars and p.opposition_name
    ]
    borrowed_source_rows = [
        BorrowedStarSourceModel(
            palace_name=row["borrowed_from"],
            branch=next((pp.branch for pp in chart.palaces if pp.name == row["borrowed_from"]), None),
            stem=next((pp.stem for pp in chart.palaces if pp.name == row["borrowed_from"]), None),
            main_stars=row["borrowed_main_stars"],
            analysis_tags=next((pp.analysis_tags for pp in chart.palaces if pp.name == row["borrowed_from"]), []),
            conclusion=next((pp.conclusion for pp in chart.palaces if pp.name == row["borrowed_from"]), None),
            explanation=next((pp.explanation for pp in chart.palaces if pp.name == row["borrowed_from"]), None),
            suggestion=next((pp.suggestion for pp in chart.palaces if pp.name == row["borrowed_from"]), None),
        )
        for row in borrowed_palace_rows
    ]

    _branch_palace_map = {p.branch_idx: p for p in chart.palaces}
    _body_palace = _branch_palace_map.get(chart.body_palace_branch)
    _body_palace_name = _body_palace.name if _body_palace else chart.body_palace_branch_name or ""
    _opposite_name = opposite.name if opposite else ""

    ziwei_structural_summary = build_ziwei_structural_summary(
        chart,
        life_name=life_name,
        sanfang=sanfang,
        opposite_name=_opposite_name,
        body_palace_name=_body_palace_name,
        palace_weights=palace_weights,
        borrowed_palace_rows=borrowed_palace_rows,
        borrowed_source_rows=borrowed_source_rows,
        patterns_resp=patterns_resp,
        sihua_trace=sihua_trace,
        key_years=key_years,
        key_months=key_months,
        evidence_chain=evidence_chain,
        strong_stars=strong_stars,
        weak_stars=weak_stars,
        brightness_map=brightness_map,
        has_empty_palace=has_empty_palace,
    )

    # ── 模板过滤：simple 档位隐藏重运算字段 ──────────────────
    # simple：跳过 forecast/飞星/流月/详分析/建议（减少响应体积，加快前端渲染）
    # standard/pro：保持完整内容
    _flying_out = None if _is_simple else flying_resp
    _forecast_out = None if _is_simple else forecast_resp
    _liuyue_out = [] if _is_simple else liuyue_resp
    _analysis_out = {} if _is_simple else chart.analysis
    _analysis_structured_out: list[PalaceStructuredAnalysis] = []
    if not _is_simple:
        _analysis_structured_out = [
            PalaceStructuredAnalysis(
                palace_index=p.index,
                palace_name=p.name,
                conclusion=p.conclusion,
                explanation=p.explanation,
                suggestion=p.suggestion,
                tooltip=p.tooltip,
                analysis_tags=p.analysis_tags,
                is_empty_palace=not bool(p.main_stars),
            )
            for p in chart.palaces
        ]
    _remedies_out = [] if _is_simple else (chart.remedies or [])
    _ls_out = [] if _is_simple else (chart.life_suggestions or [])

    _liuri_out = None
    if chart.liuri_liushi is not None:
        bundle = chart.liuri_liushi
        _liuri_out = LiuriLiushiResponse(
            liuri=LiuriItem(
                lunar_day=bundle.liuri.lunar_day,
                life_palace_branch=bundle.liuri.life_palace_branch,
                branch=bundle.liuri.branch,
                palace_name=bundle.liuri.palace_name,
                liuyue_month=bundle.liuri.liuyue_month,
            ),
            liushi=LiushiItem(
                hour_branch_idx=bundle.liushi.hour_branch_idx,
                life_palace_branch=bundle.liushi.life_palace_branch,
                branch=bundle.liushi.branch,
                palace_name=bundle.liushi.palace_name,
                hour_label=bundle.liushi.hour_label,
            ),
            missing_fields=bundle.missing_fields,
        )

    _iztro_out = None
    if birth:
        _main_pos: dict[str, str] = {}
        for p in chart.palaces:
            for s in p.main_stars:
                _main_pos[s["name"]] = p.branch
        _raw = compare_chart_to_iztro(
            year=birth["year"],
            month=birth["month"],
            day=birth["day"],
            hour=birth["hour"],
            minute=birth.get("minute", 0),
            gender=birth["gender"],
            engine_main=_main_pos,
            engine_life_palace_gz=chart.life_palace_gz,
            year_divide=birth.get("year_divide", "lichun"),
            day_divide=birth.get("day_divide", "solar_next"),
        )
        if _raw:
            _dual = _raw.get("dual_track")
            _iztro_out = IztroCrosscheckResponse(
                status=_raw.get("status", "unknown"),
                main_match=_raw.get("main_match", 0),
                main_total=_raw.get("main_total", 14),
                life_palace_match=bool(_raw.get("life_palace_match", True)),
                iztro_life_palace_gz=_raw.get("iztro_life_palace_gz"),
                engine_life_palace_gz=_raw.get("engine_life_palace_gz"),
                advisory=_raw.get("advisory"),
                dual_track=IztroDualTrackResponse(**_dual) if _dual else None,
            )

    return ZiweiResponse(
        template_version=template,
        birth_solar=chart.birth_solar,
        gender=chart.gender,
        lunar=lunar_resp,
        life_palace_gz=chart.life_palace_gz,
        body_palace_gz=chart.body_palace_gz,
        life_palace_branch_idx=chart.life_palace_branch,
        body_palace_branch_idx=chart.body_palace_branch,
        wuxing_ju=chart.wuxing_ju,
        wuxing_ju_name=chart.wuxing_ju_name,
        palaces=palaces_resp,
        dayun=dayun_resp,
        liunian=liunian_resp,
        flying=_flying_out,
        liuyue=_liuyue_out,
        liuri_liushi=_liuri_out,
        missing_fields=getattr(chart, "missing_fields", []) or [],
        engine_warnings=getattr(chart, "engine_warnings", []) or [],
        iztro_crosscheck=_iztro_out,
        summary=chart.summary,
        analysis=_analysis_out,
        analysis_structured=_analysis_structured_out,
        life_ruler_star=chart.life_ruler_star,
        body_ruler_star=chart.body_ruler_star,
        true_solar_time=chart.true_solar_time,
        body_palace_branch_name=getattr(chart, "body_palace_branch_name", ""),
        laiyin_palace=getattr(chart, "laiyin_palace", ""),
        forecast=_forecast_out,
        patterns=patterns_resp,
        chart_summary=(
            f"命宫{life_name}，对宫{_opposite_name or '—'}，"
            f"五行局{chart.wuxing_ju_name}；"
            f"命宫地支{life_branch}，三合宫{', '.join(p.name for p in sanfang.triad_palaces) or '—'}。"
        ),
        structural_summary=chart_structural_summary,
        sihua_trace=sihua_trace,
        key_years=key_years,
        key_months=key_months,
        confidence_level="high" if chart.forecast or chart.patterns else "medium",
        confidence_score=81 if chart.forecast else 72,
        evidence_chain=evidence_chain,
        ziwei_structural_summary=ziwei_structural_summary,
        remedies=[
            RemedyResponse(
                id=r.id,
                name=r.name,
                priority=r.priority,
                cost_level=r.cost_level,
                valid_scope=r.valid_scope,
                actions=r.actions,
                evidence=r.evidence,
                disclaimer=r.disclaimer,
            )
            for r in _remedies_out
        ],
        life_suggestions=[
            LifeSuggestionResponse(
                id=s.id,
                category=s.category,
                category_label=s.category_label,
                name=s.name,
                priority=s.priority,
                cost_level=s.cost_level,
                valid_scope=s.valid_scope,
                short_desc=s.short_desc,
                actions=s.actions,
                evidence=s.evidence,
                notes=s.notes,
                disclaimer=s.disclaimer,
            )
            for s in _ls_out
        ],
        provenance=build_ziwei_provenance(chart, req) if req else ResponseProvenance(),
        classic_refs=build_chart_classic_refs(chart),
    )


@router.post("/full", response_model=ZiweiResponse, summary="计算完整紫微命盘")
@limiter.limit("30/minute")
@api_response_cache(prefix="ziwei:full")
async def compute_ziwei(request: Request, req: ZiweiRequest) -> ZiweiResponse:
    """
    输入公历出生时间和性别，返回完整紫微斗数命盘。

    包含：农历信息、命宫身宫、五行局、14主星亮度、
    辅星杂曜、四化、大运、流年、飞星盘、逐宫解读。

    `template_version` 控制返回字段量级：
    - **simple**   — 仅核心命盘（宫位/格局/摘要），响应最小，适合快速预览
    - **standard** — 完整命盘（默认）
    - **pro**      — 与 standard 相同，格局来源字段始终可见
    """
    _t0 = _time.monotonic()
    try:
        async with _CALC_SEM:
            chart = await asyncio.to_thread(ziwei_full, *_ziwei_full_args(req))
    except Exception as exc:
        record_ziwei_calc(req.gender, _time.monotonic() - _t0, success=False)
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    record_ziwei_calc(req.gender, _time.monotonic() - _t0, success=True)
    response = _chart_to_response(
        chart,
        template=req.template_version,
        req=req,
        birth={
            "year": req.year,
            "month": req.month,
            "day": req.day,
            "hour": req.hour,
            "minute": req.minute or 0,
            "gender": req.gender,
            "year_divide": req.year_divide,
            "day_divide": req.day_divide,
        },
    )
    from services.content_policy import (
        content_versions_meta,
        default_disclaimer_block,
        default_wenmo_advisory,
    )
    from services.ziwei_trust import apply_trust_level

    return apply_trust_level(
        response.model_copy(
            update={
                "disclaimer_block": default_disclaimer_block(),
                "content_versions": content_versions_meta(),
                "wenmo_advisory": default_wenmo_advisory(),
            }
        ),
    )


class ZiweiStructuredTextResponse(BaseModel):
    format: str
    markdown: str
    json_payload: dict = Field(..., alias="json")

    model_config = {"populate_by_name": True}


@router.post(
    "/structured-text",
    response_model=ZiweiStructuredTextResponse,
    summary="结构化紫微导出（Markdown+JSON）",
)
@limiter.limit("30/minute")
async def ziwei_structured_text(request: Request, req: ZiweiRequest) -> ZiweiStructuredTextResponse:
    enforce_quota(request, "structured_text")
    async with _CALC_SEM:
        chart = await asyncio.to_thread(ziwei_full, *_ziwei_full_args(req))
    resp = _chart_to_response(chart, template=req.template_version, req=req)
    export = build_ziwei_structured_export(resp.model_dump(mode="json"))
    return ZiweiStructuredTextResponse(**export)


@router.get("/demo", response_model=ZiweiResponse, summary="演示命盘（壬午年正月三十未时女）")
@limiter.limit("60/minute")
async def demo_ziwei(request: Request, crosscheck: bool = False) -> ZiweiResponse:
    """
    黄金测试案例：2002-03-13 14:55 女
    预期：水二局，命宫丁未，紫微在辰宫，天府在子宫。

    查询参数 `crosscheck=true` 时附带 iztro 交叉核验（需本地 iztro 依赖）。
    """
    try:
        async with _CALC_SEM:
            chart = await asyncio.to_thread(ziwei_full, *_ziwei_full_args(_DEMO_REQUEST))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    birth = None
    if crosscheck:
        birth = {
            "year": _DEMO_REQUEST.year,
            "month": _DEMO_REQUEST.month,
            "day": _DEMO_REQUEST.day,
            "hour": _DEMO_REQUEST.hour,
            "minute": _DEMO_REQUEST.minute or 0,
            "gender": _DEMO_REQUEST.gender,
            "year_divide": _DEMO_REQUEST.year_divide,
            "day_divide": _DEMO_REQUEST.day_divide,
        }
    return _chart_to_response(chart, req=_DEMO_REQUEST, birth=birth)


@router.post(
    "/compatibility",
    response_model=CompatibilityResponse,
    summary="合盘六合度分析 [已弃用 → POST /api/v1/relation/full]",
    deprecated=True,
)
@limiter.limit("20/minute")
@api_response_cache(prefix="ziwei:compat")
async def compute_compatibility(
    request: Request,
    req: CompatibilityRequest,
    response: Response,
) -> CompatibilityResponse:
    """
    输入两人出生信息，返回紫微斗数合盘六合度分析 [已弃用]。
    """
    response.headers["Deprecation"] = "true"
    response.headers["Link"] = '</api/v1/relation/full>; rel="successor-version"'
    try:
        async with _CALC_SEM:
            chart_a = await asyncio.to_thread(ziwei_full, *_ziwei_full_args(req.person_a))
        async with _CALC_SEM:
            chart_b = await asyncio.to_thread(ziwei_full, *_ziwei_full_args(req.person_b))
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    from services.ziwei_engine.compatibility import calc_compatibility

    result = calc_compatibility(chart_a, chart_b)

    return CompatibilityResponse(
        total_score=result.total_score,
        max_score=result.max_score,
        level=result.level,
        summary=result.summary,
        dimensions=[
            CompatibilityDimensionResponse(
                name=d.name,
                score=d.score,
                max_score=d.max_score,
                description=d.description,
            )
            for d in result.dimensions
        ],
        person_a_info=result.person_a_info,
        person_b_info=result.person_b_info,
        harmony_points=result.harmony_points,
        conflict_points=result.conflict_points,
        complement_points=result.complement_points,
        palace_compare=result.palace_compare,
    )


@router.post("/multi_compat", response_model=MultiCompatResponse, summary="多人合盘（2-4人）")
@limiter.limit("10/minute")
@api_response_cache(prefix="ziwei:multi_compat")
async def multi_compat(request: Request, req: MultiCompatRequest) -> MultiCompatResponse:
    """
    输入 2-4 人出生信息，返回所有两两组合的合盘分析，
    以及 N×N 缘分矩阵和整体团队和谐指数。
    """
    return await _compute_multi_compat(req)


async def _compute_multi_compat(req: MultiCompatRequest) -> MultiCompatResponse:
    from services.multi_compat_service import enrich_pair_with_relation_dims
    from services.ziwei_engine.compatibility import calc_compatibility

    n = len(req.person_list)
    labels = req.labels

    async def _calc(p: ZiweiRequest) -> ZiweiChart:
        async with _CALC_SEM:
            return await asyncio.to_thread(ziwei_full, *_ziwei_full_args(p))

    try:
        charts: list[ZiweiChart] = await asyncio.gather(*[_calc(p) for p in req.person_list])
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    pairs: list[MultiCompatPairResponse] = []
    pair_scores: list[int] = []
    raw_scores: dict[tuple[int, int], int] = {}

    for i in range(n):
        for j in range(i + 1, n):
            try:
                result = await asyncio.to_thread(calc_compatibility, charts[i], charts[j])
            except Exception as exc:
                raise HTTPException(status_code=400, detail=f"合盘 {i + 1}-{j + 1} 失败: {exc}") from exc
            score = result.total_score
            raw_scores[(i, j)] = score
            raw_scores[(j, i)] = score
            pair_scores.append(score)
            label_a = labels[i] if labels else None
            label_b = labels[j] if labels else None
            if req.include_relation_dims:
                pair = await asyncio.to_thread(
                    enrich_pair_with_relation_dims,
                    req.person_list[i],
                    req.person_list[j],
                    relation_type=req.relation_type,
                    label_a=label_a,
                    label_b=label_b,
                    ziwei_score=result.total_score,
                    max_score=result.max_score,
                    level=result.level,
                    person_a_idx=i,
                    person_b_idx=j,
                    supervisor_id=req.supervisor_id,
                )
            else:
                pair = MultiCompatPairResponse(
                    person_a_idx=i,
                    person_b_idx=j,
                    total_score=result.total_score,
                    max_score=result.max_score,
                    level=result.level,
                )
            pairs.append(pair)

    matrix: list[list[int]] = []
    for i in range(n):
        row = []
        for j in range(n):
            if i == j:
                row.append(100)
            else:
                row.append(raw_scores.get((i, j), 0))
        matrix.append(row)

    team_harmony_score = round(sum(pair_scores) / len(pair_scores)) if pair_scores else 100
    schema_version = "multi-compat@1.1" if req.include_relation_dims else "multi-compat@1.0"

    return MultiCompatResponse(
        schema_version=schema_version,
        person_count=n,
        relation_type=req.relation_type if req.include_relation_dims else None,
        pairs=pairs,
        matrix=matrix,
        team_harmony_score=team_harmony_score,
    )


@router.post(
    "/multi_compat/export/pdf",
    summary="多人合盘矩阵 PDF 导出",
    response_class=Response,
)
@limiter.limit("10/minute")
async def multi_compat_export_pdf(request: Request, req: MultiCompatRequest) -> Response:
    """R086 P1：multi_compat 矩阵走 render_html_to_pdf 正式管线。"""
    from services.pdf_exporter import render_html_to_pdf
    from services.relation_pdf_service import render_multi_compat_html

    result = await _compute_multi_compat(req)
    labels = [getattr(p, "gender", None) or f"成员{i + 1}" for i, p in enumerate(req.person_list)]
    html = render_multi_compat_html(result.model_dump(mode="json"), labels=labels)
    try:
        pdf_bytes = await render_html_to_pdf(html)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"PDF 渲染失败: {exc}") from exc
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="multi-compat-matrix.pdf"'},
    )


# ──────────────────────────────────────────────────────────────
# §5 批量排盘  POST /api/v1/ziwei/batch
# ──────────────────────────────────────────────────────────────

import csv  # noqa: E402
import io  # noqa: E402
import json  # noqa: E402
import zipfile  # noqa: E402

from fastapi import File, UploadFile  # noqa: E402

_BATCH_MAX_ROWS = 200  # 单次最多 200 行


@router.post(
    "/batch",
    summary="批量排盘",
    description=(
        "上传 CSV 文件（列：name,year,month,day,hour,minute,gender，"
        "可选列：liunian_year,longitude 及全部 *_method / flow_* 参数），返回 ZIP 压缩包，"
        "内含每人命盘 JSON 文件和汇总 _summary.csv。\n\n"
        "查询参数 `template_version` 控制每份 JSON 的字段量级（simple/standard/pro，默认 standard）。"
    ),
    response_class=Response,
    responses={
        200: {
            "content": {"application/zip": {}},
            "description": "命盘 ZIP 包",
        }
    },
)
@limiter.limit("5/minute")
async def batch_ziwei(
    request: Request,
    file: UploadFile = File(..., description="CSV 文件，UTF-8 或 GB2312 编码"),
    template_version: str = "standard",
) -> Response:
    """
    CSV 格式示例（首行为表头）：

        name,year,month,day,hour,minute,gender
        张三,1990,5,20,8,30,男
        李四,1985,9,15,14,0,女

    可选列：liunian_year（流年，默认当年），longitude（经度），
    以及 wenchang_method / youbi_method / flow_lunar_day 等算法参数（同 ZiweiRequest）。

    返回：ZIP 压缩包，每人一个 `{name}_{idx}.json`，
    以及 `_summary.csv`（name, life_palace_gz, wuxing_ju_name, patterns, status, error）。
    """
    # 读取上传文件
    raw = await file.read()
    # 尝试 UTF-8，失败则 GB2312
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = raw.decode("gb2312", errors="replace")

    reader = csv.DictReader(io.StringIO(text))
    rows = list(reader)
    if not rows:
        raise HTTPException(status_code=400, detail="CSV 为空或无有效数据行")
    if len(rows) > _BATCH_MAX_ROWS:
        raise HTTPException(
            status_code=400,
            detail=f"CSV 行数超过上限 {_BATCH_MAX_ROWS}，请拆分后分批上传",
        )

    # 必要列检查
    required = {"year", "month", "day", "hour", "minute", "gender"}
    headers = {h.strip().lower() for h in (reader.fieldnames or [])}
    missing = required - headers
    if missing:
        raise HTTPException(
            status_code=400,
            detail=f"CSV 缺少必要列：{', '.join(sorted(missing))}。需要：name,year,month,day,hour,minute,gender",
        )

    # 构建 ZIP
    zip_buffer = io.BytesIO()
    summary_rows: list[dict] = []

    with zipfile.ZipFile(zip_buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        for idx, row in enumerate(rows):
            name = (row.get("name") or row.get("Name") or f"person_{idx + 1}").strip()
            safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in name)
            status = "ok"
            error_msg = ""
            chart_json: dict = {}

            try:
                req = _ziwei_request_from_csv_row(row, template_version=template_version)

                async with _CALC_SEM:
                    chart = await asyncio.to_thread(ziwei_full, *_ziwei_full_args(req))

                resp = _chart_to_response(chart, template=req.template_version, req=req)
                chart_json = resp.model_dump()
                # 注入 input 快照
                chart_json["_input"] = {
                    "name": name,
                    "year": req.year,
                    "month": req.month,
                    "day": req.day,
                    "hour": req.hour,
                    "minute": req.minute,
                    "gender": req.gender,
                }
                patterns_str = ", ".join(p.get("name", "") for p in (chart_json.get("patterns") or []))

            except Exception as exc:
                status = "error"
                error_msg = str(exc)
                patterns_str = ""

            summary_rows.append(
                {
                    "idx": idx + 1,
                    "name": name,
                    "life_palace_gz": chart_json.get("life_palace_gz", ""),
                    "body_palace_gz": chart_json.get("body_palace_gz", ""),
                    "wuxing_ju_name": chart_json.get("wuxing_ju_name", ""),
                    "patterns": patterns_str,
                    "birth_solar": chart_json.get("birth_solar", ""),
                    "status": status,
                    "error": error_msg,
                }
            )

            if status == "ok":
                zf.writestr(
                    f"{safe_name}_{idx + 1}.json",
                    json.dumps(chart_json, ensure_ascii=False, indent=2),
                )
            else:
                # 保留 error placeholder
                zf.writestr(
                    f"{safe_name}_{idx + 1}.error.txt",
                    f"排盘失败：{error_msg}\n原始数据：{dict(row)}",
                )

        # 写 summary CSV
        summary_io = io.StringIO()
        sum_writer = csv.DictWriter(
            summary_io,
            fieldnames=[
                "idx",
                "name",
                "birth_solar",
                "life_palace_gz",
                "body_palace_gz",
                "wuxing_ju_name",
                "patterns",
                "status",
                "error",
            ],
        )
        sum_writer.writeheader()
        sum_writer.writerows(summary_rows)
        zf.writestr("_summary.csv", "\ufeff" + summary_io.getvalue())  # BOM for Excel

    zip_buffer.seek(0)
    _ok_rows = sum(1 for r in summary_rows if r["status"] == "ok")
    _err_rows = sum(1 for r in summary_rows if r["status"] == "error")
    record_ziwei_batch(success_rows=_ok_rows, error_rows=_err_rows, req_success=True)
    return Response(
        content=zip_buffer.getvalue(),
        media_type="application/zip",
        headers={"Content-Disposition": "attachment; filename=ziwei_batch.zip"},
    )


# ─────────────────────────────────────────────────────────────────────────────
# A6: POST /api/v1/ziwei/flying  飞星专项端点（轻量）
# ─────────────────────────────────────────────────────────────────────────────


@router.post(
    "/flying",
    response_model=FlyingChartResponse,
    summary="A6 飞星四化盘（轻量）",
    description="仅返回飞星四化分析，不含完整命盘；接受与 /full 相同的 ZiweiRequest 参数。",
)
async def api_ziwei_flying(payload: ZiweiRequest):
    """
    A6 飞星专项端点。

    输入出生年月日时分和性别，返回 12 宫飞星四化汇总：
    - palaces: 每宫飞出四化
    - received: 每宫接收到的飞化（其他宫飞入）
    - chonged: 被对冲宫位
    - self_transforms: 全盘自化列表
    """
    async with _CALC_SEM:
        chart: ZiweiChart = await asyncio.to_thread(ziwei_full, *_ziwei_full_args(payload))

    flying = chart.flying
    if flying is None:
        raise HTTPException(status_code=500, detail="飞星数据不可用")

    palaces_out = [
        FlyingPalaceResponse(
            palace_name=p.palace_name,
            stem_name=p.stem_name,
            flying_out=p.flying_out if isinstance(p.flying_out, dict) else {},
            opposition_palace=getattr(p, "opposition_palace", ""),
            self_transforms=list(getattr(p, "self_transforms", [])),
        )
        for p in flying.palaces
    ]

    return FlyingChartResponse(
        palaces=palaces_out,
        received=dict(flying.received) if flying.received else {},
        chonged=dict(flying.chonged) if flying.chonged else {},
        self_transforms=list(flying.self_transforms) if flying.self_transforms else [],
    )


@router.post("/explain/batch", summary="紫微讲解 batch（≤4 sections）")
@limiter.limit("30/minute")
async def api_ziwei_explain_batch(request: Request, payload: ZiweiExplainBatchRequest) -> ExplainBatchResponse:
    """一次请求最多 4 个 explain section，供报告/紫微页填充 cite/fact 层。"""
    from services.explain_service import explain_ziwei_batch

    enforce_quota(request, "ziwei_explain_batch")
    return explain_ziwei_batch(payload)
