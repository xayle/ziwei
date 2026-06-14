"""
routers/ziwei.py — 紫微斗数 API 路由

POST /api/v1/ziwei/full  → 完整命盘计算
GET  /api/v1/ziwei/demo  → 演示命盘（用黄金测试案例）
"""

from __future__ import annotations

import asyncio
import time as _time

from fastapi import APIRouter, HTTPException
from starlette.requests import Request

from app.schemas.ziwei import (
    CompatibilityDimensionResponse,
    CompatibilityRequest,
    CompatibilityResponse,
    DayunItemResponse,
    DayunResponse,
    EventTagResponse,
    FlyingChartResponse,
    FlyingPalaceResponse,
    ForecastResultResponse,
    LifeSuggestionResponse,
    LiunianResponse,
    LiuyueItem,
    LunarResponse,
    MultiCompatPairResponse,
    MultiCompatRequest,
    MultiCompatResponse,
    PalaceResponse,
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
from services.rate_limit import limiter
from services.ziwei_engine import ZiweiChart, ziwei_full

# 限制并发计算线程数，防止 ThreadPoolExecutor 耐尽
# asyncio.to_thread 默认线程池大小=min(32, cpu+4)，每个请求占用该线程 1-4 秒。
# Semaphore 确保最多 8 个请求同时进入线程池（其余在协程层排队）。
_CALC_SEM = asyncio.Semaphore(8)

router = APIRouter(prefix="/api/v1/ziwei", tags=["紫微斗数"])

# 模板档位常量
_TPL_SIMPLE = "simple"
_TPL_STANDARD = "standard"
_TPL_PRO = "pro"


def _chart_to_response(
    chart: ZiweiChart,
    template: str = _TPL_STANDARD,
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
            analysis=p.analysis,
            analysis_tags=p.analysis_tags,
            xiaoxian_ages=p.xiaoxian_ages,
            opposition_name=p.opposition_name,
            conclusion=p.conclusion,
            explanation=p.explanation,
            suggestion=p.suggestion,
            tooltip=p.tooltip,
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
            month=d["month"],
            month_name=d["month_name"],
            month_gz=d["month_gz"],
            life_palace_branch=d["life_palace_branch"],
            palace_name=d["palace_name"],
            sihua=d.get("sihua", {}),
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
            )

        forecast_resp = ForecastResultResponse(
            year=fc.year,
            yearly=_map_period(fc.yearly),
            monthly=[_map_period(m) for m in fc.monthly],
            current_month=_map_period(fc.current_month) if fc.current_month else None,
        )

    patterns_resp = [
        PatternResponse(
            name=pt.name,
            level=pt.level,
            description=pt.description,
            palaces=pt.palaces,
            stars=pt.stars,
            # pro 模板始终保留出典；其他模板也保留（出典默认为空时无影响）
            source=getattr(pt, "source", ""),
        )
        for pt in chart.patterns
    ]

    # ── 模板过滤：simple 档位隐藏重运算字段 ──────────────────
    # simple：跳过 forecast/飞星/流月/详分析/建议（减少响应体积，加快前端渲染）
    # standard/pro：保持完整内容
    _flying_out = None if _is_simple else flying_resp
    _forecast_out = None if _is_simple else forecast_resp
    _liuyue_out = [] if _is_simple else liuyue_resp
    _analysis_out = {} if _is_simple else chart.analysis
    _remedies_out = [] if _is_simple else (chart.remedies or [])
    _ls_out = [] if _is_simple else (chart.life_suggestions or [])

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
        summary=chart.summary,
        analysis=_analysis_out,
        life_ruler_star=chart.life_ruler_star,
        body_ruler_star=chart.body_ruler_star,
        true_solar_time=chart.true_solar_time,
        body_palace_branch_name=getattr(chart, "body_palace_branch_name", ""),
        laiyin_palace=getattr(chart, "laiyin_palace", ""),
        forecast=_forecast_out,
        patterns=patterns_resp,
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
            chart = await asyncio.to_thread(
                ziwei_full,
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
                req.kuiyue_method,
                req.tianma_method,
                req.tiankong_method,
                req.brightness_method,
                req.jiukong_method,
                req.tianshang_method,
                req.mingzhu_method,
                req.liunian_sihua_method,
                req.changsheng_method,
            )
    except Exception as exc:
        record_ziwei_calc(req.gender, _time.monotonic() - _t0, success=False)
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    record_ziwei_calc(req.gender, _time.monotonic() - _t0, success=True)
    return _chart_to_response(chart, template=req.template_version)


@router.get("/demo", response_model=ZiweiResponse, summary="演示命盘（壬午年正月三十未时女）")
@limiter.limit("60/minute")
async def demo_ziwei(request: Request) -> ZiweiResponse:
    """
    黄金测试案例：2002-03-13 14:55 女
    预期：水二局，命宫丁未，紫微在辰宫，天府在子宫。
    """
    try:
        async with _CALC_SEM:
            chart = await asyncio.to_thread(ziwei_full, 2002, 3, 13, 14, 55, "女")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return _chart_to_response(chart)


@router.post("/compatibility", response_model=CompatibilityResponse, summary="合盘六合度分析")
@limiter.limit("20/minute")
@api_response_cache(prefix="ziwei:compat")
async def compute_compatibility(request: Request, req: CompatibilityRequest) -> CompatibilityResponse:
    """
    输入两人出生信息，返回紫微斗数合盘六合度分析。

    维度包括：命宫相合、五行相生、年支缘分、夸妻宫缘、阴阳互补。
    总分 100 分，输出各维度得分与详细说明。
    """
    try:
        async with _CALC_SEM:
            chart_a = await asyncio.to_thread(
                ziwei_full,
                req.person_a.year,
                req.person_a.month,
                req.person_a.day,
                req.person_a.hour,
                req.person_a.minute,
                req.person_a.gender,
                req.person_a.liunian_year,
                req.person_a.longitude,
            )
        async with _CALC_SEM:
            chart_b = await asyncio.to_thread(
                ziwei_full,
                req.person_b.year,
                req.person_b.month,
                req.person_b.day,
                req.person_b.hour,
                req.person_b.minute,
                req.person_b.gender,
                req.person_b.liunian_year,
                req.person_b.longitude,
            )
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

    矩阵对角线固定为 100（自身），非对角线为两人合盘总分。
    团队和谐指数为所有两两组合均值。
    """
    from services.ziwei_engine.compatibility import calc_compatibility

    n = len(req.person_list)

    # 并发计算所有人的命盘
    async def _calc(p: ZiweiRequest) -> ZiweiChart:
        async with _CALC_SEM:
            return await asyncio.to_thread(
                ziwei_full,
                p.year,
                p.month,
                p.day,
                p.hour,
                p.minute,
                p.gender,
                p.liunian_year,
                p.longitude,
            )

    try:
        charts: list[ZiweiChart] = await asyncio.gather(*[_calc(p) for p in req.person_list])
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    # 两两合盘
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
            pairs.append(
                MultiCompatPairResponse(
                    person_a_idx=i,
                    person_b_idx=j,
                    total_score=result.total_score,
                    max_score=result.max_score,
                    level=result.level,
                )
            )

    # N×N 矩阵（对角线=100）
    matrix: list[list[int]] = []
    for i in range(n):
        row = []
        for j in range(n):
            if i == j:
                row.append(100)
            else:
                row.append(raw_scores.get((i, j), 0))
        matrix.append(row)

    # 团队和谐指数
    team_harmony_score = round(sum(pair_scores) / len(pair_scores)) if pair_scores else 100

    return MultiCompatResponse(
        person_count=n,
        pairs=pairs,
        matrix=matrix,
        team_harmony_score=team_harmony_score,
    )


# ──────────────────────────────────────────────────────────────
# §6 批量排盘  POST /api/v1/ziwei/batch
# ──────────────────────────────────────────────────────────────

import csv  # noqa: E402
import io  # noqa: E402
import json  # noqa: E402
import zipfile  # noqa: E402

from fastapi import File, UploadFile  # noqa: E402
from fastapi.responses import Response  # noqa: E402

_BATCH_MAX_ROWS = 200  # 单次最多 200 行


@router.post(
    "/batch",
    summary="批量排盘",
    description=(
        "上传 CSV 文件（列：name,year,month,day,hour,minute,gender，"
        "可选列：liunian_year,longitude），返回 ZIP 压缩包，"
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

    可选列：liunian_year（流年，默认当年），longitude（经度）。

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
                year = int(row["year"].strip())
                month = int(row["month"].strip())
                day = int(row["day"].strip())
                hour = int(row["hour"].strip())
                minute = int(row.get("minute", "0").strip() or "0")
                gender = row["gender"].strip()
                liunian_year_str = row.get("liunian_year", "").strip()
                liunian_year = int(liunian_year_str) if liunian_year_str else None
                longitude_str = row.get("longitude", "").strip()
                longitude = float(longitude_str) if longitude_str else None

                async with _CALC_SEM:
                    chart = await asyncio.to_thread(
                        ziwei_full,
                        year,
                        month,
                        day,
                        hour,
                        minute,
                        gender,
                        liunian_year,
                        longitude,
                    )

                tpl = template_version if template_version in (_TPL_SIMPLE, _TPL_STANDARD, _TPL_PRO) else _TPL_STANDARD
                resp = _chart_to_response(chart, template=tpl)
                chart_json = resp.model_dump()
                # 注入 input 快照
                chart_json["_input"] = {
                    "name": name,
                    "year": year,
                    "month": month,
                    "day": day,
                    "hour": hour,
                    "minute": minute,
                    "gender": gender,
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

from pydantic import BaseModel as _BaseModel  # noqa: E402


class ZiweiFlyingRequest(_BaseModel):
    """A6 飞星请求：出生信息，返回飞星四化盘。"""

    year: int
    month: int
    day: int
    hour: int
    minute: int = 0
    gender: str
    longitude: float | None = None


@router.post(
    "/flying",
    response_model=FlyingChartResponse,
    summary="A6 飞星四化盘（轻量）",
    description="仅返回飞星四化分析，不含完整命盘，速度更快。",
)
async def api_ziwei_flying(payload: ZiweiFlyingRequest):
    """
    A6 飞星专项端点。

    输入出生年月日时分和性别，返回 12 宫飞星四化汇总：
    - palaces: 每宫飞出四化
    - received: 每宫接收到的飞化（其他宫飞入）
    - chonged: 被对冲宫位
    - self_transforms: 全盘自化列表
    """
    async with _CALC_SEM:
        chart: ZiweiChart = await asyncio.to_thread(
            ziwei_full,
            payload.year,
            payload.month,
            payload.day,
            payload.hour,
            payload.minute,
            payload.gender,
            None,  # liunian_year
            payload.longitude,
        )

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
