from __future__ import annotations

from datetime import datetime
import re
from typing import Any, Literal
from uuid import uuid4
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, Response
from pydantic import BaseModel, Field
from sqlmodel import Session

from app.dependencies import RequiredUser
from app.models import Case
from app.schemas import BaziFullRequest, BaziFullResponse, LiuriLiushiEndpointResponse, LiuriLiushiRequest, WarningModel
from app.schemas.explain import ExplainBatchRequest, ExplainBatchResponse
from db import get_session
from services.bazi_full_service import apply_profile_slim, bazi_full, compute_liuri_liushi
from services.normalize_input import normalize_birth_datetime
from services.quota_service import enforce_quota
from services.rate_limit import limiter
from services.structured_export_service import build_bazi_structured_export

router = APIRouter(prefix="/api/v1/bazi", tags=["bazi"])
# ✅ 0.14: /bazi/full 速率限制 20 req/min

_REQUEST_ID_PATTERN = re.compile(r"^[A-Za-z0-9._-]+$")


def _sanitize_request_id(candidate: str | None, warnings: list[WarningModel]) -> str:
    if candidate is None:
        return str(uuid4())
    rid = candidate.strip()
    if not rid:
        return str(uuid4())
    if not _REQUEST_ID_PATTERN.match(rid):
        warnings.append(WarningModel(code="request_id_invalid_chars", message="request id replaced with uuid"))
        return str(uuid4())
    if len(rid) > 128:
        warnings.append(WarningModel(code="request_id_truncated", message="request id truncated to 128 chars"))
        rid = rid[:128]
    return rid


def _normalize_birth_dt_text(
    dt_text: str,
    tz_name: str,
    *,
    precision: str = "exact",
    unknown_time_fallback: str = "midday",
) -> datetime:
    """把字符串出生时间统一解析成后端标准的本地时间。"""
    try:
        dt = datetime.fromisoformat(dt_text)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=f"birth_dt 格式无效: {dt_text}") from exc

    if dt.tzinfo is None or dt.utcoffset() is None:
        try:
            dt = dt.replace(tzinfo=ZoneInfo(tz_name or "Asia/Shanghai"))
        except Exception as exc:
            raise HTTPException(status_code=422, detail=f"tz 格式无效: {tz_name}") from exc

    return normalize_birth_datetime(
        dt,
        tz_name or "Asia/Shanghai",
        auto_dst=True,
        precision=precision,
        unknown_time_fallback=unknown_time_fallback,
    ).local_dt


@router.post("/full", response_model=BaziFullResponse)
@limiter.limit("20/minute")  # 0.14: /bazi/full 速率限制 20 req/min
def api_bazi_full(
    request: Request,
    payload: BaziFullRequest,
    profile: Literal["full", "slim"] = Query("full", description="slim: 省略域分析长文与大运叙事"),
    x_request_id: str | None = Header(None, alias="X-Request-Id"),
):
    warnings: list[WarningModel] = []
    request_id = _sanitize_request_id(x_request_id, warnings)
    result = bazi_full(payload, request_id=request_id)
    if profile == "slim":
        data = result.model_dump(mode="json")
        apply_profile_slim(data)
        result = BaziFullResponse.model_validate(data)
    if warnings:
        result.warnings.extend(warnings)
    return result


class StructuredTextResponse(BaseModel):
    format: str
    markdown: str
    json_payload: dict = Field(..., alias="json")

    model_config = {"populate_by_name": True}


@router.post(
    "/structured-text",
    response_model=StructuredTextResponse,
    summary="结构化命盘导出（Markdown+JSON，供 LLM/第三方）",
)
@limiter.limit("30/minute")
def api_bazi_structured_text(
    request: Request,
    payload: BaziFullRequest,
    x_request_id: str | None = Header(None, alias="X-Request-Id"),
):
    """
    文墨式工作流：将 /bazi/full 结果转为 Markdown + JSON 双格式。
    含 provenance 脚注与 missing_fields。
    流年默认窗口：当前年±2；目标年流日见 liuri_liushi.target_date（BE-A07）。
    """
    enforce_quota(request, "structured_text")
    warnings: list[WarningModel] = []
    request_id = _sanitize_request_id(x_request_id, warnings)
    result = bazi_full(payload, request_id=request_id)
    if warnings:
        result.warnings.extend(warnings)
    export = build_bazi_structured_export(result.model_dump(mode="json"))
    return StructuredTextResponse(**export)


@router.post("/liuri-liushi", response_model=LiuriLiushiEndpointResponse)
@limiter.limit("30/minute")
def api_bazi_liuri_liushi(
    request: Request,
    payload: LiuriLiushiRequest,
    x_request_id: str | None = Header(None, alias="X-Request-Id"),
):
    """独立流日/流时计算：干支、十神、大运/流年联动评分与换运提醒。"""
    warnings: list[WarningModel] = []
    request_id = _sanitize_request_id(x_request_id, warnings)
    return compute_liuri_liushi(payload, request_id=request_id)


# ─────────────────────────────────────────────────────────────────────────────
# A1  流年分域预测  POST /api/v1/bazi/liunian-domain
# ─────────────────────────────────────────────────────────────────────────────


class LiunianDomainRequest(BaseModel):
    case_id: str
    year: int


class LiunianDomainResponse(BaseModel):
    year: int
    year_ganzhi: str
    domains: dict[str, str]  # 财运 / 事业 / 婚恋 / 健康 / 综合


@router.post("/liunian-domain", response_model=LiunianDomainResponse)
def api_liunian_domain(
    payload: LiunianDomainRequest,
    current_user: RequiredUser,
    session: Session = Depends(get_session),
):
    """
    A1 流年分域预测：指定 case_id + year，返回该年财运/事业/婚恋/健康四域预测。

    调用链：
      Case(birth_dt_local, lon, tz, gender)
        → calculate()  → VerifyResponse(pillars, yongshen, wuxing_score)
        → compute_shishen_scores()
        → compute_liunian_domain_forecasts(year=N, ...)
        → {财运, 事业, 婚恋, 健康}
    """
    case = session.get(Case, payload.case_id)
    if not case:
        raise HTTPException(status_code=404, detail="case not found")

    # 解析出生时间
    dt = _normalize_birth_dt_text(case.birth_dt_local, case.tz or "Asia/Shanghai")

    # 运行完整计算（已有 TTLCache，重复请求不会重新算）
    from services.bazi_engine_service import calculate

    result = calculate(dt, case.lon, case.tz, False, "single", case.gender)
    vr = result.verify_response
    rp = vr.pillars_primary

    # 提取用神与五行评分
    favor: list[str] = list(vr.yongshen.favor) if vr.yongshen and vr.yongshen.favor else []
    wx = vr.wuxing_score
    wx_scores: dict[str, float] = (
        {e: float(getattr(wx, e, 0.0)) for e in ("wood", "fire", "earth", "metal", "water")} if wx else {}
    )

    # 重新计算十神得分（shishen_scores 不存储在 VerifyResponse 中）
    from services.bazi_engine.wuxing import compute_shishen_scores

    shishen_scores = compute_shishen_scores(
        day_stem=rp.day.stem,
        year_stem=rp.year.stem,
        month_stem=rp.month.stem,
        hour_stem=rp.hour.stem,
        year_branch=rp.year.branch,
        month_branch=rp.month.branch,
        day_branch=rp.day.branch,
        hour_branch=rp.hour.branch,
    )

    # 流年天干地支
    _STEMS = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
    _BRANCHES = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
    y = payload.year
    year_stem = _STEMS[(y - 4) % 10]
    year_branch = _BRANCHES[(y - 4) % 12]

    from services.bazi_engine.analysis.liunian_domain import compute_liunian_domain_forecasts

    domain = compute_liunian_domain_forecasts(
        year=y,
        year_stem=year_stem,
        year_branch=year_branch,
        day_stem=rp.day.stem,
        day_branch=rp.day.branch,
        shishen_scores=shishen_scores,
        yongshen_favor=favor,
        wuxing_scores=wx_scores,
        gender=case.gender or "male",
    )

    return LiunianDomainResponse(
        year=y,
        year_ganzhi=f"{year_stem}{year_branch}",
        domains=domain,
    )


# ─────────────────────────────────────────────────────────────────────────────
# A2  大运叙述报告  POST /api/v1/bazi/dayun-report
# ─────────────────────────────────────────────────────────────────────────────


class DayunReportRequest(BaseModel):
    case_id: str


class DayunReportClassic(BaseModel):
    source: str
    text: str


class DayunReportSections(BaseModel):
    core: str = ""
    career: str = ""
    wealth: str = ""
    love: str = ""
    health: str = ""
    trend_note: str | None = None
    classics: list[DayunReportClassic] = Field(default_factory=list)
    disclaimer: str = ""


class DayunReportItem(BaseModel):
    ganzhi: str
    start_age: int | None = None
    end_age: int | None = None
    ten_god: str | None = None
    narrative: str
    narrative_sections: DayunReportSections | None = None


class DayunReportResponse(BaseModel):
    items: list[DayunReportItem]
    narrative_total_chars: int


def _sections_from_dict(raw: dict | None) -> DayunReportSections | None:
    if not raw:
        return None
    classics = [
        DayunReportClassic(source=str(c.get("source", "")), text=str(c.get("text", "")))
        for c in (raw.get("classics") or [])
        if isinstance(c, dict)
    ]
    return DayunReportSections(
        core=str(raw.get("core") or ""),
        career=str(raw.get("career") or ""),
        wealth=str(raw.get("wealth") or ""),
        love=str(raw.get("love") or ""),
        health=str(raw.get("health") or ""),
        trend_note=raw.get("trend_note"),
        classics=classics,
        disclaimer=str(raw.get("disclaimer") or ""),
    )


def _build_dayun_report_items(vr) -> list[DayunReportItem]:
    """从 VerifyResponse 提取大运叙事列表（case / inline 共用）。"""
    items: list[DayunReportItem] = []
    if not vr.dayun or not vr.dayun.items:
        return items

    dayun_list = vr.dayun.items
    for i, it in enumerate(dayun_list):
        ganzhi = (it.stem or "") + (it.branch or "")
        if i + 1 < len(dayun_list):
            end_age = int(dayun_list[i + 1].start_age or 0) - 1
        else:
            end_age = int(it.start_age or 0) + 9

        narrative = it.narrative or ""
        sections_model = getattr(it, "narrative_sections", None)
        sections_dict = sections_model.model_dump() if sections_model is not None else None
        if not narrative or not sections_dict:
            try:
                favor: list[str] = list(vr.yongshen.favor) if vr.yongshen and vr.yongshen.favor else []
                geju_name = vr.geju.geju_name if vr.geju and vr.geju.geju_name else "普通格"
                strength_tier = (vr.day_master_strength.tier if vr.day_master_strength else "中和") or "中和"
                from services.bazi_engine.analysis.dayun_narrative import (
                    build_dayun_narrative_sections,
                    format_dayun_narrative,
                )

                sections_dict = build_dayun_narrative_sections(
                    stem=it.stem or "",
                    branch=it.branch or "",
                    ganzhi=ganzhi,
                    ten_god=it.ten_god or "",
                    start_age=int(it.start_age or 0),
                    end_age=end_age,
                    yongshen_favor=favor,
                    geju_name=geju_name,
                    strength_tier=strength_tier,
                    wealth_tier="中格",
                    is_favorable=(it.flow_wuxing or "") in favor,
                    day_stem=vr.pillars_primary.day.stem if vr.pillars_primary else "",
                )
                if not narrative:
                    narrative = format_dayun_narrative(sections_dict)
            except Exception:
                narrative = narrative or f"{ganzhi}大运（{it.start_age}–{end_age}岁）"
                sections_dict = None

        items.append(
            DayunReportItem(
                ganzhi=ganzhi,
                start_age=int(it.start_age) if it.start_age is not None else None,
                end_age=end_age,
                ten_god=it.ten_god,
                narrative=narrative,
                narrative_sections=_sections_from_dict(sections_dict),
            )
        )
    return items


@router.post("/dayun-report", response_model=DayunReportResponse)
def api_dayun_report(
    payload: DayunReportRequest,
    current_user: RequiredUser,
    session: Session = Depends(get_session),
):
    """
    A2 大运叙述报告：返回全部大运步骤的 400-600 字叙事段落。

    调用链：
      Case(birth_dt_local, lon, tz, gender)
        → calculate()  → VerifyResponse(dayun.items[i].narrative)
        → 每步大运已在 M3.02 中通过 generate_dayun_narrative() 填充
        → 直接提取 narrative 字段返回
    """
    case = session.get(Case, payload.case_id)
    if not case:
        raise HTTPException(status_code=404, detail="case not found")

    dt = _normalize_birth_dt_text(case.birth_dt_local, case.tz or "Asia/Shanghai")

    from services.bazi_engine_service import calculate

    result = calculate(dt, case.lon, case.tz, False, "single", case.gender)
    vr = result.verify_response

    items = _build_dayun_report_items(vr)
    total_chars = sum(len(it.narrative) for it in items)
    return DayunReportResponse(items=items, narrative_total_chars=total_chars)


@router.post("/dayun-report/inline", response_model=DayunReportResponse)
@limiter.limit("20/minute")
def api_dayun_report_inline(
    request: Request,
    payload: BaziFullRequest,
):
    """
    档案驱动大运叙述：无需 case_id / 登录，入参与 /bazi/full 一致。
    """
    dt = _normalize_birth_dt_text(payload.dt.isoformat(), payload.tz or "Asia/Shanghai")

    from services.bazi_engine_service import calculate

    result = calculate(
        dt,
        payload.lon,
        payload.tz,
        payload.solar_time_enabled,
        payload.mode,
        payload.gender,
    )
    vr = result.verify_response
    items = _build_dayun_report_items(vr)
    total_chars = sum(len(it.narrative) for it in items)
    return DayunReportResponse(items=items, narrative_total_chars=total_chars)


# ─────────────────────────────────────────────────────────────────────────────
# A3  无状态八字合盘  POST /api/v1/bazi/compatibility
# ─────────────────────────────────────────────────────────────────────────────


class CompatibilitySubject(BaseModel):
    birth_dt: str  # ISO 8601
    lon: float = Field(116.4, ge=73.0, le=135.0)
    tz: str = "Asia/Shanghai"
    gender: str | None = None


class CompatibilityRequest(BaseModel):
    person_a: CompatibilitySubject
    person_b: CompatibilitySubject


class CompatibilityResponse(BaseModel):
    score: int = Field(description="合盘综合分 0-100")
    wuxing_match: dict[str, str] = Field(description="五行互补情况")
    branch_clash: list[str] = Field(description="地支六冲列表")
    born_year_he: list[str] = Field(description="年支六合/三合")
    summary: str = Field(description="100字以内总结")


_BRANCH_CHONG: dict[str, str] = {
    "子": "午",
    "午": "子",
    "丑": "未",
    "未": "丑",
    "寅": "申",
    "申": "寅",
    "卯": "酉",
    "酉": "卯",
    "辰": "戌",
    "戌": "辰",
    "巳": "亥",
    "亥": "巳",
}
_BRANCH_HE: dict[str, str] = {
    "子": "丑",
    "丑": "子",
    "寅": "亥",
    "亥": "寅",
    "卯": "戌",
    "戌": "卯",
    "辰": "酉",
    "酉": "辰",
    "巳": "申",
    "申": "巳",
    "午": "未",
    "未": "午",
}
_BRANCH_SANHE = [
    frozenset(["申", "子", "辰"]),
    frozenset(["寅", "午", "戌"]),
    frozenset(["亥", "卯", "未"]),
    frozenset(["巳", "酉", "丑"]),
]
_WUXING_ZH: dict[str, str] = {
    "wood": "木",
    "fire": "火",
    "earth": "土",
    "metal": "金",
    "water": "水",
}
_WUXING_SHENG: dict[str, str] = {
    "wood": "fire",
    "fire": "earth",
    "earth": "metal",
    "metal": "water",
    "water": "wood",
}


def _build_profile(subj: CompatibilitySubject):
    """无状态计算单人命盘基础信息（不写 DB）。"""
    from services.bazi_engine_service import calculate

    try:
        dt = _normalize_birth_dt_text(subj.birth_dt, subj.tz or "Asia/Shanghai")
    except HTTPException:
        raise
    result = calculate(dt, subj.lon, subj.tz, False, "single", subj.gender)
    vr = result.verify_response
    rp = vr.pillars_primary
    wx = vr.wuxing_score
    favor = list(vr.yongshen.favor) if vr.yongshen and vr.yongshen.favor else []
    wx_dict = {}
    if wx:
        for el in ("wood", "fire", "earth", "metal", "water"):
            wx_dict[el] = float(getattr(wx, el, 0.0))
    return rp, favor, wx_dict


@router.post("/compatibility", response_model=CompatibilityResponse, deprecated=True)
def api_compatibility(
    payload: CompatibilityRequest,
    response: Response,
    current_user: RequiredUser,
):
    """
    A3 无状态八字合盘 [已弃用 → POST /api/v1/relation/full]
    """
    response.headers["Deprecation"] = "true"
    response.headers["Link"] = '</api/v1/relation/full>; rel="successor-version"'
    rp_a, favor_a, wx_a = _build_profile(payload.person_a)
    rp_b, favor_b, wx_b = _build_profile(payload.person_b)

    # ── 地支六冲检测 ─────────────────────────────────────────
    branches_a = [rp_a.year.branch, rp_a.month.branch, rp_a.day.branch, rp_a.hour.branch]
    branches_b = [rp_b.year.branch, rp_b.month.branch, rp_b.day.branch, rp_b.hour.branch]
    clashes = []
    for ba in branches_a:
        for bb in branches_b:
            if _BRANCH_CHONG.get(ba) == bb and f"{ba}-{bb} 相冲" not in clashes:
                clashes.append(f"{ba}-{bb} 相冲")
    clash_penalty = min(len(clashes) * 10, 40)
    clash_score = 40 - clash_penalty

    # ── 五行互补 ─────────────────────────────────────────────
    match_info: dict[str, str] = {}
    wuxing_bonus = 0
    for el in ("wood", "fire", "earth", "metal", "water"):
        va, vb = wx_a.get(el, 0.0), wx_b.get(el, 0.0)
        if va > 0.3 and vb < 0.15:
            match_info[_WUXING_ZH[el]] = "甲方旺，补乙方"
            wuxing_bonus += 8
        elif vb > 0.3 and va < 0.15:
            match_info[_WUXING_ZH[el]] = "乙方旺，补甲方"
            wuxing_bonus += 8
        else:
            match_info[_WUXING_ZH.get(el, el)] = "均衡"
    wuxing_score = min(wuxing_bonus, 40)

    # ── 用神互助 ─────────────────────────────────────────────
    yongshen_bonus = 0
    for el in favor_a:
        if el in favor_b:
            yongshen_bonus += 10  # 用神相同，目标一致
        sheng = _WUXING_SHENG.get(el, "")
        if sheng in favor_b:
            yongshen_bonus += 5
    yongshen_score = min(yongshen_bonus, 20)

    total = clash_score + wuxing_score + yongshen_score

    # ── 年支六合 / 三合 ─────────────────────────────────────
    ya, yb = rp_a.year.branch, rp_b.year.branch
    born_he = []
    if _BRANCH_HE.get(ya) == yb:
        born_he.append(f"{ya}-{yb} 年支六合")
    for group in _BRANCH_SANHE:
        if ya in group and yb in group:
            born_he.append(f"{ya}-{yb} 年支三合")

    summary_parts = []
    if total >= 80:
        summary_parts.append("命盘高度契合，五行相补，用神相助，合婚吉象")
    elif total >= 60:
        summary_parts.append("整体和谐，略有冲克，需注意化解")
    elif total >= 40:
        summary_parts.append("存在一定五行冲克，建议多方化解")
    else:
        summary_parts.append("五行相克较多，需谨慎相处")
    if clashes:
        summary_parts.append(f"主要冲克：{'、'.join(clashes[:2])}")
    if born_he:
        summary_parts.append(f"{'、'.join(born_he)}")

    return CompatibilityResponse(
        score=max(0, min(100, total)),
        wuxing_match=match_info,
        branch_clash=clashes,
        born_year_he=born_he,
        summary="；".join(summary_parts) + "。",
    )


# ─────────────────────────────────────────────────────────────────────────────
# A4  年度月历运势  POST /api/v1/bazi/monthly
# ─────────────────────────────────────────────────────────────────────────────


class MonthlyRequest(BaseModel):
    case_id: str
    year: int = Field(description="公历年份，如 2025")


class MonthlyItemOut(BaseModel):
    month: int
    month_ganzhi: str
    month_dizhi: str
    luck_level: str
    color_hint: str
    tip: str
    clash_with: str | None = None


class MonthlyResponse(BaseModel):
    year: int
    year_ganzhi: str
    items: list[MonthlyItemOut]


@router.post("/monthly", response_model=MonthlyResponse)
def api_monthly(
    payload: MonthlyRequest,
    current_user: RequiredUser,
    session: Session = Depends(get_session),
):
    """
    A4 年度月历运势：返回指定年份 12 个月的运势数据（用于前端日历组件着色）。

    调用链：Case → calculate() → compute_monthly()
    """
    case = session.get(Case, payload.case_id)
    if not case:
        raise HTTPException(status_code=404, detail="case not found")

    dt = _normalize_birth_dt_text(case.birth_dt_local, case.tz or "Asia/Shanghai")

    from services.bazi_engine_service import calculate

    result = calculate(dt, case.lon, case.tz, False, "single", case.gender)
    vr = result.verify_response
    rp = vr.pillars_primary

    favor = list(vr.yongshen.favor) if vr.yongshen and vr.yongshen.favor else []
    avoid = list(vr.yongshen.avoid) if vr.yongshen and vr.yongshen.avoid else []

    # 构建12个月干支
    _STEMS12 = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
    _BRANCHES12 = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
    y = payload.year
    year_stem = _STEMS12[(y - 4) % 10]
    year_branch = _BRANCHES12[(y - 4) % 12]

    # 五虎遁年起月干：甲己→丙、乙庚→戊、丙辛→庚、丁壬→壬、戊癸→甲
    _MONTH_START: dict[str, int] = {
        "甲": 2,
        "己": 2,
        "乙": 4,
        "庚": 4,
        "丙": 6,
        "辛": 6,
        "丁": 8,
        "壬": 8,
        "戊": 0,
        "癸": 0,
    }
    start_idx = _MONTH_START.get(year_stem, 2)
    month_ganzhis = [
        _STEMS12[(start_idx + i) % 10] + _BRANCHES12[(2 + i) % 12]  # 寅월=February
        for i in range(12)
    ]

    from services.bazi_engine.analysis.monthly import compute_monthly

    monthly_list = compute_monthly(
        day_branch=rp.day.branch,
        yongshen_favor=favor,
        yongshen_avoid=avoid,
        year_branch=year_branch,
        mode="dual",
        month_ganzhis=month_ganzhis,
        day_stem=rp.day.stem,
    )

    items: list[MonthlyItemOut] = []
    for i, m in enumerate(monthly_list):
        gz = month_ganzhis[i] if i < len(month_ganzhis) else ""
        items.append(
            MonthlyItemOut(
                month=m.month,
                month_ganzhi=gz,
                month_dizhi=m.month_dizhi,
                luck_level=m.luck_level,
                color_hint=m.color_hint or "",
                tip=m.tip or "",
                clash_with=m.clash_with,
            )
        )

    return MonthlyResponse(
        year=y,
        year_ganzhi=f"{year_stem}{year_branch}",
        items=items,
    )


# ─────────────────────────────────────────────────────────────────────────────
# A5  模块化按需分析  POST /api/v1/bazi/analyze
# ─────────────────────────────────────────────────────────────────────────────

_ALLOWED_TABS = frozenset(
    [
        "pillars",
        "geju",
        "yongshen",
        "wuxing",
        "dayun",
        "life_arc",
        "lucky",
        "wealth",
        "career",
        "marriage",
        "health",
        "personality",
        "monthly",
        "liunian",
    ]
)


class AnalyzeRequest(BaseModel):
    birth_dt: str  # ISO 8601
    lon: float = Field(116.4, ge=73.0, le=135.0)
    tz: str = "Asia/Shanghai"
    gender: str | None = None
    tabs: list[str] = Field(
        default_factory=lambda: ["life_arc", "lucky"],
        description=f"需要的字段子集，可选值: {sorted(_ALLOWED_TABS)}",
    )


@router.post("/analyze")
def api_analyze(
    payload: AnalyzeRequest,
    current_user: RequiredUser,
) -> dict:
    """
    A5 模块化按需分析：calculate() 全量计算，只返回 tabs 指定字段。

    默认 ["life_arc", "lucky"] 约 1KB，完整集约 12KB。
    """
    unknown = set(payload.tabs) - _ALLOWED_TABS
    if unknown:
        raise HTTPException(status_code=422, detail=f"不支持的 tab: {sorted(unknown)}")

    from services.bazi_engine_service import calculate

    try:
        dt = _normalize_birth_dt_text(payload.birth_dt, payload.tz or "Asia/Shanghai")
    except HTTPException:
        raise

    result = calculate(dt, payload.lon, payload.tz, False, "single", payload.gender)
    vr = result.verify_response

    _tab_map: dict[str, Any] = {
        "pillars": vr.pillars_primary,
        "geju": vr.geju,
        "yongshen": vr.yongshen,
        "wuxing": vr.wuxing_score,
        "dayun": vr.dayun,
        "life_arc": vr.life_arc,
        "lucky": vr.lucky,
        "wealth": vr.wealth_analysis,
        "career": vr.career,  # VerifyResponse 字段名为 career（非 career_analysis）
        "marriage": vr.marriage_analysis,
        "health": vr.health,  # VerifyResponse 字段名为 health（非 health_analysis）
        "personality": vr.personality,
        "monthly": vr.monthly_fortune,
        "liunian": vr.liunian_detail,
    }

    out: dict[str, Any] = {}
    for tab in payload.tabs:
        val = _tab_map.get(tab)
        if val is None:
            out[tab] = None
        elif hasattr(val, "model_dump"):
            out[tab] = val.model_dump()
        else:
            out[tab] = val

    return out


# ─────────────────────────────────────────────────────────────────────────────
# A7  节气精准时刻  GET /api/v1/calendar/jieqi
# ─────────────────────────────────────────────────────────────────────────────


# 注：A7 挂在 bazi router 中，但通过 app.include_router 时 prefix 可改
# 对外路径：GET /api/v1/bazi/jieqi?year=2025
class JieqiItemOut(BaseModel):
    name: str
    dt_local: str  # ISO 8601 Asia/Shanghai


class JieqiResponse(BaseModel):
    year: int
    items: list[JieqiItemOut]
    backend: str


@router.get("/jieqi", response_model=JieqiResponse)
def api_jieqi(
    year: int,
    current_user: RequiredUser,
):
    """
    A7 节气精准时刻：sxtwl 精算指定年份 24 节气的精确时分秒。
    命理师判断月柱必用，精度到秒。
    """
    from backends import BackendUnavailable, SxtwlBackend

    try:
        backend = SxtwlBackend()
    except BackendUnavailable:
        raise HTTPException(status_code=503, detail="sxtwl 后端不可用，无法计算节气")

    all_items: list[JieqiItemOut] = []
    try:
        infos = backend.sxtwl.getJieQiByYear(year)
        for info in infos:
            idx = int(info.jqIndex)
            if 0 <= idx < len(backend.JIE_NAMES):
                dd = backend.sxtwl.JD2DD(info.jd)
                from datetime import datetime
                from zoneinfo import ZoneInfo

                dt = datetime(
                    dd.Y,
                    dd.M,
                    dd.D,
                    int(dd.h),
                    int(dd.m),
                    int(dd.s),
                    tzinfo=ZoneInfo("Asia/Shanghai"),
                )
                all_items.append(
                    JieqiItemOut(
                        name=backend.JIE_NAMES[idx],
                        dt_local=dt.isoformat(),
                    )
                )
        # 按时间排序
        all_items.sort(key=lambda x: x.dt_local)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"节气计算失败: {exc}")

    return JieqiResponse(year=year, items=all_items, backend="sxtwl")


# ─────────────────────────────────────────────────────────────────────────────
# A8  格局专项接口  POST /api/v1/bazi/geju
# ─────────────────────────────────────────────────────────────────────────────


class GejuSubjectRequest(BaseModel):
    birth_dt: str
    lon: float = Field(116.4, ge=73.0, le=135.0)
    tz: str = "Asia/Shanghai"
    gender: str | None = None


class GejuLightResponse(BaseModel):
    geju_name: str
    confidence: float
    is_broken: bool
    note: str
    classic_ref: str = ""
    ten_god: str = ""


@router.post("/geju", response_model=GejuLightResponse)
def api_geju(
    payload: GejuSubjectRequest,
    current_user: RequiredUser,
):
    """
    A8 格局专项接口：轻量接口，只返回 geju_name / confidence / is_broken。
    不走数据库，直接无状态计算。
    """
    from services.bazi_engine_service import calculate

    try:
        dt = _normalize_birth_dt_text(payload.birth_dt, payload.tz or "Asia/Shanghai")
    except HTTPException:
        raise

    result = calculate(dt, payload.lon, payload.tz, False, "single", payload.gender)
    vr = result.verify_response
    g = vr.geju
    if g is None:
        return GejuLightResponse(
            geju_name="普通格",
            confidence=0.0,
            is_broken=False,
            note="格局未能判断",
            classic_ref="",
            ten_god="",
        )
    return GejuLightResponse(
        geju_name=g.geju_name,
        confidence=g.confidence,
        is_broken=g.is_broken,
        note=g.interpretation_text[:80] if g.interpretation_text else "",
        classic_ref=g.classic_ref or "",
        ten_god=g.month_stem_shishen or "",
    )


# ─────────────────────────────────────────────────────────────────────────────
# 农历 → 公历（档案录入辅助）
# ─────────────────────────────────────────────────────────────────────────────


class LunarToSolarRequest(BaseModel):
    lunar_year: int = Field(..., ge=1800, le=2200)
    lunar_month: int = Field(..., ge=1, le=12)
    lunar_day: int = Field(..., ge=1, le=30)
    hour: int = Field(0, ge=0, le=23)
    minute: int = Field(0, ge=0, le=59)
    is_leap_month: bool = False


class LunarToSolarResponse(BaseModel):
    solar_dt: str
    solar_year: int
    solar_month: int
    solar_day: int
    lunar_label: str
    warnings: list[str] = Field(default_factory=list)


@router.post("/lunar-to-solar", response_model=LunarToSolarResponse)
def api_lunar_to_solar(payload: LunarToSolarRequest) -> LunarToSolarResponse:
    """将农历日期时间转换为公历 naive ISO（供 Fusheng 档案农历模式使用）。"""
    import sxtwl  # type: ignore[import]

    warnings: list[str] = []
    try:
        day = sxtwl.fromLunar(
            payload.lunar_year,
            payload.lunar_month,
            payload.lunar_day,
            payload.is_leap_month,
        )
        y = int(day.getSolarYear())
        m = int(day.getSolarMonth())
        d = int(day.getSolarDay())
        solar_dt = f"{y:04d}-{m:02d}-{d:02d}T{payload.hour:02d}:{payload.minute:02d}:00"
        leap = "闰" if payload.is_leap_month else ""
        lunar_label = f"农历{payload.lunar_year}年{leap}{payload.lunar_month}月{payload.lunar_day}日"
        return LunarToSolarResponse(
            solar_dt=solar_dt,
            solar_year=y,
            solar_month=m,
            solar_day=d,
            lunar_label=lunar_label,
            warnings=warnings,
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"lunar_to_solar_failed: {exc}") from exc


# ─────────────────────────────────────────────────────────────────────────────
# A9  多历法精度对比  POST /api/v1/bazi/calendar-compare  [ADMIN]
# ─────────────────────────────────────────────────────────────────────────────


class CalendarCompareRequest(BaseModel):
    birth_dt: str
    lon: float = Field(116.4, ge=73.0, le=135.0)
    tz: str = "Asia/Shanghai"


class PillarOut(BaseModel):
    year: str
    month: str
    day: str
    hour: str


class CalendarCompareResponse(BaseModel):
    sxtwl: PillarOut | None = None
    cnlunar: PillarOut | None = None
    diff_fields: list[str]
    warnings: list[str]


@router.post("/calendar-compare", response_model=CalendarCompareResponse)
def api_calendar_compare(
    payload: CalendarCompareRequest,
    current_user: RequiredUser,
):
    """
    A9 多历法精度对比（ADMIN 工具）：sxtwl vs cnlunar 四柱并排对比。
    """
    from app.exceptions import AuthorizationException, ErrorCode

    if not current_user.is_admin:
        raise AuthorizationException(
            code=ErrorCode.AUTHZ_PERMISSION_DENIED,
            message="calendar-compare 仅限管理员使用",
        )

    from backends import CnlunarBackend, get_sxtwl_backend

    dt = _normalize_birth_dt_text(payload.birth_dt, payload.tz, precision="exact")

    warnings_out: list[str] = []
    sxtwl_out: PillarOut | None = None
    cnlunar_out: PillarOut | None = None

    # sxtwl
    try:
        sx = get_sxtwl_backend()
        px = sx.get_pillars(dt)
        sxtwl_out = PillarOut(
            year=px.year.ganzhi,
            month=px.month.ganzhi,
            day=px.day.ganzhi,
            hour=px.hour.ganzhi,
        )
    except Exception as exc:
        warnings_out.append(f"sxtwl_error: {exc}")

    # cnlunar
    try:
        cn = CnlunarBackend()
        pc = cn.get_pillars(dt)
        cnlunar_out = PillarOut(
            year=pc.year.ganzhi,
            month=pc.month.ganzhi,
            day=pc.day.ganzhi,
            hour=pc.hour.ganzhi,
        )
    except Exception as exc:
        warnings_out.append(f"cnlunar_error: {exc}")

    # diff
    diff: list[str] = []
    if sxtwl_out and cnlunar_out:
        for field_name in ("year", "month", "day", "hour"):
            va = getattr(sxtwl_out, field_name)
            vb = getattr(cnlunar_out, field_name)
            if va != vb:
                diff.append(f"{field_name}: sxtwl={va} cnlunar={vb}")

    return CalendarCompareResponse(
        sxtwl=sxtwl_out,
        cnlunar=cnlunar_out,
        diff_fields=diff,
        warnings=warnings_out,
    )


# ─────────────────────────────────────────────────────────────────────────────
# W2  批量命盘对比  POST /api/v1/bazi/batch-compare
# ─────────────────────────────────────────────────────────────────────────────


class BatchCompareRequest(BaseModel):
    """W2 批量命盘对比请求：最多 10 个 case_id，并排对比关键字段。"""

    case_ids: list[str] = Field(..., min_length=2, max_length=10)


class BatchCaseProfile(BaseModel):
    case_id: str
    name: str = ""
    geju_name: str = ""
    yongshen_favor: list[str] = []
    yongshen_avoid: list[str] = []
    wuxing_scores: dict[str, float] = {}
    error: str = ""


class BatchCompareResponse(BaseModel):
    count: int
    profiles: list[BatchCaseProfile]
    common_favor: list[str]  # 所有人共同喜用神
    common_avoid: list[str]  # 所有人共同忌神


@router.post(
    "/batch-compare",
    response_model=BatchCompareResponse,
    summary="W2 批量命盘对比",
    description="并排对比最多 10 个案例的格局/用忌神/五行分布，快速发现家庭/团队命盘特征。",
)
def api_bazi_batch_compare(
    payload: BatchCompareRequest,
    current_user: RequiredUser,
    session=Depends(get_session),
):
    """W2: 批量读取 Case 并并排对比关键字段。"""
    from sqlmodel import select as _select

    from app.models import Case as _Case

    profiles: list[BatchCaseProfile] = []
    all_favors: list[set[str]] = []
    all_avoids: list[set[str]] = []

    for cid in payload.case_ids:
        case = session.exec(_select(_Case).where(_Case.id == cid, _Case.deleted_at.is_(None))).first()
        if not case:
            profiles.append(BatchCaseProfile(case_id=cid, error="案例不存在"))
            continue
        if case.owner_id is not None and case.owner_id != current_user.id:
            profiles.append(BatchCaseProfile(case_id=cid, error="无权访问"))
            continue
        try:
            import zoneinfo as _zi

            from services.bazi_engine_service import calculate

            lon = float(case.longitude or 116.4)
            tz_name = case.timezone or "Asia/Shanghai"
            try:
                _zi.ZoneInfo(tz_name)
            except Exception:
                tz_name = "Asia/Shanghai"
            birth_dt = _normalize_birth_dt_text(case.birth_dt_local, tz_name)
            result = calculate(birth_dt, lon, tz_name, gender=case.gender)
            vr = result.verify_response
            favor = list(getattr(vr.yongshen, "favor", []))
            avoid = list(getattr(vr.yongshen, "avoid", []))
            geju = getattr(vr.geju, "geju_name", "") if vr.geju else ""
            wx_raw = getattr(vr, "wuxing", None)
            wx_scores: dict[str, float] = {}
            if wx_raw:
                for el in ("wood", "fire", "earth", "metal", "water"):
                    v = getattr(wx_raw, el, None)
                    if v is not None:
                        wx_scores[el] = float(v)
            profiles.append(
                BatchCaseProfile(
                    case_id=cid,
                    name=case.name or "",
                    geju_name=geju,
                    yongshen_favor=favor,
                    yongshen_avoid=avoid,
                    wuxing_scores=wx_scores,
                )
            )
            all_favors.append(set(favor))
            all_avoids.append(set(avoid))
        except Exception as exc:
            profiles.append(BatchCaseProfile(case_id=cid, error=str(exc)))

    # 所有人共同喜/忌取交集
    common_favor = sorted(set.intersection(*all_favors)) if all_favors else []
    common_avoid = sorted(set.intersection(*all_avoids)) if all_avoids else []

    return BatchCompareResponse(
        count=len(profiles),
        profiles=profiles,
        common_favor=common_favor,
        common_avoid=common_avoid,
    )


# ─────────────────────────── D7: 黄金案例公开查阅 ────────────────────────────────
from functools import lru_cache as _lru_cache  # noqa: E402
import json as _json  # noqa: E402
from pathlib import Path as _Path  # noqa: E402

_GROUND_TRUTH_PATH = _Path(__file__).resolve().parent.parent / "data" / "ground_truth_cases.json"


@_lru_cache(maxsize=1)
def _load_golden_cases() -> list[dict]:
    """启动时一次性加载黄金案例至内存（data/ground_truth_cases.json）"""
    if not _GROUND_TRUTH_PATH.exists():
        return []
    raw = _json.loads(_GROUND_TRUTH_PATH.read_text(encoding="utf-8"))
    return raw.get("cases", [])


@router.get(
    "/golden-cases",
    summary="黄金案例公开查阅",
    description="返回预置命理黄金案例，可按格局名称或标签过滤。无需认证。",
)
def get_golden_cases(
    geju: str | None = None,
    tag: str | None = None,
    limit: int = 50,
):
    """
    D7: 返回 data/ground_truth_cases.json 中的公开命理案例。
    - ?geju=七杀  — 按格局名模糊过滤 computed_pattern.geju_name
    - ?tag=GT     — 按 id 前缀过滤（GT/CLS 等）
    - ?limit=N    — 最多返回 N 条（默认 50）
    """
    cases = _load_golden_cases()
    if tag:
        cases = [c for c in cases if c.get("id", "").upper().startswith(tag.upper())]
    if geju:
        geju_lower = geju.lower()
        cases = [c for c in cases if geju_lower in str(c.get("computed_pattern", {}).get("geju_name", "")).lower()]
    limit = max(1, min(limit, 200))
    return {"total": len(cases), "cases": cases[:limit]}


# ─────────────────────────── D4: 流年年度报告（异步 202 · DB 持久化） ────────────────────────────────
from services.liunian_report_service import (
    build_liunian_report as _run_liunian_report_task,
)
from services.liunian_report_service import (
    create_liunian_task,
    get_liunian_task,
    task_to_response_dict,
)


class LiunianReportRequest(BaseModel):
    case_id: str
    year: int = Field(..., ge=1900, le=2100, description="流年年份")
    include_months: bool = Field(default=False, description="是否包含各月流月预测")


class LiunianReportResponse(BaseModel):
    task_id: str
    status: str  # queued / running / done / failed
    year: int
    case_id: str
    submitted_at: str
    finished_at: str | None = None
    result: dict | None = None
    error: str | None = None
    queue_backend: str | None = Field(
        default=None,
        description="T075：redis（多实例队列）或 asyncio（单进程回退）",
    )


@router.post(
    "/liunian-report",
    summary="提交流年年度报告生成任务（异步 202）",
    status_code=202,
)
@limiter.limit("20/minute")
async def submit_liunian_report(
    request: Request,
    payload: LiunianReportRequest,
    user: RequiredUser,
    session: Session = Depends(get_session),
):
    """
    D4 / T075: 异步生成流年年度报告（DB 持久化，进程重启可恢复轮询）。
    - 立即返回 202 Accepted + task_id（含 queue_backend=redis|asyncio）
    - 有 REDIS_URL / LIUNIAN_REDIS_URL 时入队，由 ``scripts/run_liunian_worker.py`` 消费
    - 无 Redis 时回退 asyncio.create_task（单进程开发）
    - 轮询 GET /api/v1/bazi/liunian-report/{task_id} 获取结果
    """
    from app.models import Case as _Case2

    case = session.get(_Case2, payload.case_id)
    if case is None or case.deleted_at is not None:
        raise HTTPException(status_code=404, detail=f"案例 {payload.case_id!r} 不存在")

    task = create_liunian_task(
        session,
        case_id=payload.case_id,
        user_id=int(user.id),
        year=payload.year,
        include_months=payload.include_months,
    )
    from services.liunian_queue import dispatch_liunian_job

    backend = dispatch_liunian_job(
        task_id=task.id,
        case_id=payload.case_id,
        year=payload.year,
        include_months=payload.include_months,
        runner=_run_liunian_report_task,
    )
    out = task_to_response_dict(task)
    out["queue_backend"] = backend
    return out


@router.get(
    "/liunian-report/{task_id}",
    response_model=LiunianReportResponse,
    summary="查询流年报告生成状态（轮询）",
)
def get_liunian_report(
    task_id: str,
    _user: RequiredUser,
    session: Session = Depends(get_session),
):
    """
    D4: 轮询流年报告任务状态（DB 持久化）。
    - status=queued/running → 继续轮询
    - status=done → result 中含完整报告
    - status=failed → error 中含错误信息
    """
    task = get_liunian_task(session, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail=f"任务 {task_id!r} 不存在或已过期")
    return task_to_response_dict(task)


@router.post("/explain/batch", summary="八字讲解 batch（≤4 sections）")
@limiter.limit("30/minute")
def api_bazi_explain_batch(
    request: Request,
    payload: ExplainBatchRequest,
    x_request_id: str | None = Header(None, alias="X-Request-Id"),
) -> ExplainBatchResponse:
    """一次请求最多 4 个 explain section，供报告/八字页填充 cite/fact 层。"""
    from services.explain_service import explain_bazi_batch

    enforce_quota(request, "bazi_explain_batch")
    warnings: list[WarningModel] = []
    request_id = _sanitize_request_id(x_request_id, warnings)
    return explain_bazi_batch(payload, request_id=request_id)
