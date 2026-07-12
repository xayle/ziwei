"""Build typed structural summaries for Ziwei API responses."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from services.ziwei_engine import PalaceInfo, ZiweiChart

from app.schemas.ziwei import (
    ChartRelationSummaryModel,
    ConfidenceSummaryModel,
    EvidenceItemModel,
    KeyMonthPointModel,
    KeyYearPointModel,
    PalaceRefModel,
    PatternSummaryBlockModel,
    ReportSummaryBlockModel,
    SanfangStructureModel,
    SihuaTraceEntryModel,
    SihuaTraceItemModel,
    StarBrightnessSummaryModel,
    TimelinePointModel,
    ZiweiChartStructuralSummaryModel,
    ZiweiCoreSnapshotModel,
    ZiweiStructuralSummaryModel,
)

_SOURCE = "routers.ziwei.build_response"


def _palace_ref(p: PalaceInfo) -> PalaceRefModel:
    return PalaceRefModel(
        index=p.index,
        name=p.name,
        branch=p.branch,
        branch_idx=p.branch_idx,
        stem=p.stem,
        ganzhi=f"{p.stem}{p.branch}",
        is_empty_palace=not bool(p.main_stars),
        is_body_palace=p.is_body_palace,
    )


def _palace_by_index(palaces: list[PalaceInfo], idx: int) -> PalaceInfo | None:
    return next((p for p in palaces if p.index == idx), None)


def _palace_by_branch(palaces: list[PalaceInfo], branch_idx: int) -> PalaceInfo | None:
    return next((p for p in palaces if p.branch_idx == branch_idx), None)


def build_sanfang_structure(chart: ZiweiChart, life_index: int = 0) -> SanfangStructureModel:
    life = _palace_by_index(chart.palaces, life_index)
    opposite = _palace_by_index(chart.palaces, (life_index + 6) % 12)
    triad = [p for p in chart.palaces if p.index in {(life_index + 4) % 12, (life_index + 8) % 12}]
    return SanfangStructureModel(
        life_palace=_palace_ref(life)
        if life
        else PalaceRefModel(index=life_index, name="命宫", branch="", branch_idx=chart.life_palace_branch),
        opposite_palace=_palace_ref(opposite) if opposite else None,
        triad_palaces=[_palace_ref(p) for p in triad],
    )


def build_chart_structural_summary(chart: ZiweiChart) -> ZiweiChartStructuralSummaryModel:
    life = _palace_by_index(chart.palaces, 0) or chart.palaces[0]
    body = next(
        (p for p in chart.palaces if p.is_body_palace or p.branch_idx == chart.body_palace_branch),
        _palace_by_branch(chart.palaces, chart.body_palace_branch),
    )
    opposite = _palace_by_index(chart.palaces, 6)
    missing: list[str] = []
    if not body:
        missing.append("body_palace")
    if not opposite:
        missing.append("opposite_palace")
    return ZiweiChartStructuralSummaryModel(
        life_palace=_palace_ref(life),
        body_palace=_palace_ref(body)
        if body
        else PalaceRefModel(
            index=-1,
            name=chart.body_palace_branch_name or "身宫",
            branch=chart.body_palace_branch_name or "",
            branch_idx=chart.body_palace_branch,
        ),
        opposite_palace=_palace_ref(opposite) if opposite else None,
        sanfang=build_sanfang_structure(chart),
        life_branch_idx=chart.life_palace_branch,
        body_branch_idx=chart.body_palace_branch,
        source=_SOURCE,
        missing=missing,
    )


def build_sihua_trace_entries(chart: ZiweiChart) -> list[SihuaTraceEntryModel]:
    entries: list[SihuaTraceEntryModel] = []
    for p in chart.palaces:
        if p.flying_out:
            entries.append(
                SihuaTraceEntryModel(
                    palace=p.name,
                    stem=p.stem,
                    flying_out=dict(p.flying_out),
                    conclusion=p.conclusion,
                    opposition=p.opposition_name,
                    source="services.ziwei_engine.flying",
                    missing=False,
                )
            )
        elif not p.main_stars:
            entries.append(
                SihuaTraceEntryModel(
                    palace=p.name,
                    stem=p.stem,
                    flying_out={},
                    conclusion=p.conclusion,
                    opposition=p.opposition_name,
                    source="services.ziwei_engine.analysis",
                    missing=True,
                )
            )
    return entries


def build_key_years(chart: ZiweiChart) -> list[KeyYearPointModel]:
    if not chart.forecast:
        return []
    points: list[KeyYearPointModel] = [
        KeyYearPointModel(
            label=f"{chart.forecast.year}年",
            ganzhi=chart.forecast.yearly.ganzhi,
            palace=chart.forecast.yearly.palace_name,
            score=chart.forecast.yearly.score,
            overall=chart.forecast.yearly.overall,
            events=[e.description for e in chart.forecast.yearly.events[:3]],
        )
    ]
    for item in chart.forecast.monthly[:3]:
        points.append(
            KeyYearPointModel(
                label=item.period,
                ganzhi=item.ganzhi,
                palace=item.palace_name,
                score=item.score,
                overall=item.overall,
                events=[e.description for e in item.events[:2]],
            )
        )
    return points


def build_key_months(chart: ZiweiChart) -> list[KeyMonthPointModel]:
    return [
        KeyMonthPointModel(
            month=d.month,
            month_name=d.month_name,
            month_gz=d.month_gz,
            palace_name=d.palace_name,
            sihua=dict(d.sihua or {}),
        )
        for d in chart.liuyue_data[:6]
    ]


def build_core_snapshot(chart: ZiweiChart) -> ZiweiCoreSnapshotModel:
    return ZiweiCoreSnapshotModel(
        life_palace_gz=chart.life_palace_gz,
        body_palace_gz=chart.body_palace_gz,
        life_palace_branch_idx=chart.life_palace_branch,
        body_palace_branch_idx=chart.body_palace_branch,
        wuxing_ju=chart.wuxing_ju,
        wuxing_ju_name=chart.wuxing_ju_name,
        life_ruler_star=chart.life_ruler_star,
        body_ruler_star=chart.body_ruler_star,
        laiyin_palace=getattr(chart, "laiyin_palace", "") or "",
    )


def build_ziwei_structural_summary(
    chart: ZiweiChart,
    *,
    life_name: str,
    sanfang: SanfangStructureModel,
    opposite_name: str,
    body_palace_name: str,
    palace_weights: list,
    borrowed_palace_rows: list[dict[str, Any]],
    borrowed_source_rows: list,
    patterns_resp: list,
    sihua_trace: list[SihuaTraceEntryModel],
    key_years: list[KeyYearPointModel],
    key_months: list[KeyMonthPointModel],
    evidence_chain: list[EvidenceItemModel],
    strong_stars: list[str],
    weak_stars: list[str],
    brightness_map: dict[str, str],
    has_empty_palace: bool,
) -> ZiweiStructuralSummaryModel:
    triad_labels = [p.name for p in sanfang.triad_palaces]
    return ZiweiStructuralSummaryModel(
        source=_SOURCE,
        missing=["borrowed_main_stars"] if has_empty_palace and not borrowed_palace_rows else [],
        core_snapshot=build_core_snapshot(chart),
        chart_relation_summary=ChartRelationSummaryModel(
            minggong=life_name,
            shengong=body_palace_name or None,
            wuxing_ju=chart.wuxing_ju_name,
            triad_tetrad=[
                f"命宫-{triad_labels[0]}" if triad_labels else "命宫—",
                f"命宫-{triad_labels[1]}" if len(triad_labels) > 1 else "命宫—",
            ],
            opposition=[f"命宫对{opposite_name}" if opposite_name else "命宫对宫未定"],
            palace_weights=palace_weights,
            key_palaces=[life_name, opposite_name, body_palace_name],
            palace_influence_notes=[
                "命宫为总纲",
                "身宫补充现实行为",
                "三方四正决定主轴",
            ],
            source=_SOURCE,
            missing=["borrowed_main_stars"] if has_empty_palace and not borrowed_palace_rows else [],
            borrowed_palaces=borrowed_palace_rows,
            borrowed_sources=borrowed_source_rows,
        ),
        sihua_summary=[
            SihuaTraceItemModel(
                phase="生年",
                target=str(item.palace or item.stem or ""),
                transform="、".join(sorted(item.flying_out.keys())) if item.flying_out else "",
                palace_name=item.palace,
                summary=item.conclusion,
                source=item.source,
                missing=item.missing,
            )
            for item in sihua_trace[:8]
        ],
        brightness_summary=StarBrightnessSummaryModel(
            strong=strong_stars,
            weak=weak_stars,
            details=brightness_map,
        ),
        timeline_summary={
            "key_years": [
                TimelinePointModel(
                    year=int(chart.forecast.year) if chart.forecast else 0,
                    label=item.label,
                    summary=item.overall or "流年重点",
                    tone="current" if "当前" in item.label else "warn",
                )
                for item in key_years[:4]
            ],
            "key_months": [
                TimelinePointModel(
                    year=int(chart.forecast.year) if chart.forecast else 0,
                    label=item.month_name or str(item.month),
                    summary=str(item.sihua),
                    tone="neutral",
                )
                for item in key_months[:4]
            ],
        },
        pattern_summary=PatternSummaryBlockModel(
            patterns=[p.model_dump() if hasattr(p, "model_dump") else dict(p) for p in patterns_resp],
            special_pattern_names=[p.name for p in patterns_resp[:3]],
            summary_text=chart.summary,
            confidence="medium",
        ),
        confidence_summary=ConfidenceSummaryModel(
            level="high" if chart.forecast or chart.patterns else "medium",
            score=81 if chart.forecast else 72,
            evidence=evidence_chain,
            risk_notes=[],
            inference_notes=[chart.summary],
            blocked_fields=[],
        ),
        report_summary=ReportSummaryBlockModel(
            title="紫微结构摘要",
            summary=chart.summary,
            highlights=[life_name, chart.wuxing_ju_name, opposite_name],
            warnings=["流年与大限需合看"] if chart.forecast else [],
            annotation_prompt="可在报告页补充四化链、重点宫位和时间轴注释。",
            source="services.ziwei_engine.analysis",
            missing=[
                field_name
                for field_name, value in {
                    "life_palace_gz": chart.life_palace_gz,
                    "body_palace_gz": chart.body_palace_gz,
                    "wuxing_ju_name": chart.wuxing_ju_name,
                }.items()
                if not value
            ],
        ),
    )
