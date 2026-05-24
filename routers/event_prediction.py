"""
routers/event_prediction.py — 年份事件预测 API

提供 3 个端点：
  POST /api/v1/bazi/year-events         — 单年事件分析
  POST /api/v1/bazi/multi-year-trend    — 多年趋势
  POST /api/v1/bazi/year-event-consult  — AI 咨询式解读
"""
from __future__ import annotations

import logging
from datetime import datetime
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from app.dependencies import RequiredUser
from app.models import Case
from db import get_session

from app.schemas.event_prediction import (
    YearEventRequest,
    YearEventResponse,
    MultiYearTrendRequest,
    MultiYearTrendResponse,
    YearEventConsultRequest,
    YearEventConsultResponse,
)
from services.event_signal_engine import (
    analyze_year_events,
    analyze_multi_year_trend,
    compute_overall_year_score,
)
from services.followup_service import get_followup_questions

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/bazi", tags=["年份事件预测"])

# ─── 工具函数 ─────────────────────────────────────────────────────────────────

def _load_case_and_calculate(case_id: str, session: Session):
    """加载 Case 并运行完整命盘计算，返回 (case, verify_response, birth_dt)。"""
    case = session.get(Case, case_id)
    if not case:
        raise HTTPException(status_code=404, detail="case not found")

    try:
        birth_dt = datetime.fromisoformat(case.birth_dt_local)
        # 若 birth_dt_local 为 naive datetime，用 case.tz 添加时区
        if birth_dt.tzinfo is None:
            tz_name = case.tz or "Asia/Shanghai"
            birth_dt = birth_dt.replace(tzinfo=ZoneInfo(tz_name))
    except (ValueError, TypeError, KeyError):
        raise HTTPException(status_code=422, detail="case.birth_dt_local 格式无效")

    from services.bazi_engine_service import calculate
    result = calculate(birth_dt, case.lon, case.tz, False, "single", case.gender)
    return case, result.verify_response, birth_dt


_STEMS    = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
_BRANCHES = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]


def _year_ganzhi(year: int) -> str:
    return _STEMS[(year - 4) % 10] + _BRANCHES[(year - 4) % 12]


# ─── Endpoint 1: 单年事件分析 ──────────────────────────────────────────────────

@router.post("/year-events", response_model=YearEventResponse)
def api_year_events(
    payload: YearEventRequest,
    current_user: RequiredUser,
    session: Session = Depends(get_session),
):
    """
    P0 核心端点：分析某人某年五大事件（婚姻、财运、置业、事业、健康）。

    调用链：
      Case → calculate() → analyze_year_events() → YearEventResponse
    """
    case, vr, birth_dt = _load_case_and_calculate(payload.case_id, session)

    events = analyze_year_events(
        verify_response=vr,
        birth_dt=birth_dt,
        year=payload.year,
        event_types=list(payload.event_types),
        gender=case.gender or "male",
    )
    overall_score = compute_overall_year_score(events)

    return YearEventResponse(
        case_id=payload.case_id,
        year=payload.year,
        year_ganzhi=_year_ganzhi(payload.year),
        events=events,
        overall_year_score=overall_score,
    )


# ─── Endpoint 2: 多年趋势 ──────────────────────────────────────────────────────

@router.post("/multi-year-trend", response_model=MultiYearTrendResponse)
def api_multi_year_trend(
    payload: MultiYearTrendRequest,
    current_user: RequiredUser,
    session: Session = Depends(get_session),
):
    """
    多年趋势分析：返回指定年份列表的年际对比摘要与 timeline_summary。

    前端默认传入：[当前年-1, 当前年, 当前年+1, 当前年+2, 当前年+3]
    """
    case, vr, birth_dt = _load_case_and_calculate(payload.case_id, session)

    years = sorted(set(payload.years))
    if len(years) > 10:
        raise HTTPException(status_code=422, detail="years 最多支持 10 年")

    trend_resp = analyze_multi_year_trend(
        verify_response=vr,
        birth_dt=birth_dt,
        years=years,
        gender=case.gender or "male",
    )
    # 回填 case_id（signal engine 内部不持有请求信息）
    trend_resp.case_id = payload.case_id
    return trend_resp


# ─── Endpoint 3: AI 咨询式解读 ────────────────────────────────────────────────

@router.post("/year-event-consult", response_model=YearEventConsultResponse)
async def api_year_event_consult(
    payload: YearEventConsultRequest,
    current_user: RequiredUser,
    session: Session = Depends(get_session),
):
    """
    AI 咨询式解读：针对用户提问，用 LLM 深入解读事件结果。

    LLM 角色约束：仅解释引擎结论，不重新预测，不凭空添加新事件。
    """
    case, vr, birth_dt = _load_case_and_calculate(payload.case_id, session)

    # 先跑信号引擎，拿到该事件的结构化结果
    events = analyze_year_events(
        verify_response=vr,
        birth_dt=birth_dt,
        year=payload.year,
        event_types=[payload.event_type],
        gender=case.gender or "male",
    )

    event_result = events.get(payload.event_type)
    if not event_result:
        raise HTTPException(status_code=404, detail=f"事件类型 '{payload.event_type}' 分析结果为空")

    # 从 event_rules.json 取该事件的所有被触发规则素材
    from services.event_rule_matcher import get_materials_for_signals
    rule_ids = [s.rule_id for s in (event_result.signals or []) if s.rule_id]
    materials = get_materials_for_signals(rule_ids)

    # 调用 LLM 解读
    from services.llm_service import generate_event_interpretation
    try:
        llm_resp = await generate_event_interpretation(
            event_result=event_result,
            user_question=payload.user_question,
            materials=materials,
        )
        interpretation = llm_resp.text
    except Exception as exc:
        logger.warning("LLM event consult failed: %s", exc)
        # 降级：用结构化字段拼接兜底文本
        interpretation = _fallback_interpretation(event_result, payload.user_question)

    followups = get_followup_questions(payload.event_type)

    return YearEventConsultResponse(
        case_id=payload.case_id,
        year=payload.year,
        event_type=payload.event_type,
        interpretation=interpretation,
        followup_questions=followups,
    )


def _fallback_interpretation(event_result, user_question: str) -> str:
    """LLM 不可用时的降级兜底文本。"""
    et = event_result
    lines = [
        f"关于你的问题「{user_question}」：",
        "",
        f"【{et.event_type}】{et.year}年综合研判：{et.main_judgment or ''}",
        f"触发信号概要：{et.trigger_summary or ''}",
        "",
    ]
    if et.possible_manifestations:
        lines.append("可能的现实表现：")
        lines.extend(f"  · {m}" for m in et.possible_manifestations[:4])
        lines.append("")
    if et.key_months:
        months_str = "、".join(str(m) for m in et.key_months)
        lines.append(f"关键月份：{months_str}月")
        lines.append("")
    if et.advice:
        lines.append("应对建议：")
        lines.extend(f"  · {a}" for a in et.advice[:3])
    return "\n".join(lines)
