"""
LLM 辅助解读路由 (§10)

GET    /api/v1/llm/config              — 查询 provider 配置（无需登录）
POST   /api/v1/llm/interpret           — 同步生成草稿并保存（需登录，10/min）
GET    /api/v1/llm/stream              — SSE 流式生成（需登录，10/min）
GET    /api/v1/llm/drafts              — 列出草稿（需登录）
GET    /api/v1/llm/drafts/{id}         — 获取单条草稿（需登录）
PATCH  /api/v1/llm/drafts/{id}         — 审核草稿（approved/rejected）（需登录）
DELETE /api/v1/llm/drafts/{id}         — 软删除草稿（需登录）
POST   /api/v1/llm/interpret-bazi      — 完整八字→规则→模板→LLM 一键解读（D3，需登录）
"""

from __future__ import annotations

from datetime import UTC, datetime
import json
import logging
import threading

from cachetools import TTLCache
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlmodel import Session, select
from starlette.requests import Request

from app.dependencies import RequiredUser
from app.models.llm import LlmDraft
from app.schemas.llm import (
    LlmConfigResponse,
    LlmDraftListResponse,
    LlmDraftResponse,
    LlmDraftUpdate,
    LlmInterpretRequest,
)
from db import get_session
from services.evidence_retriever import fetch_evidence
from services.llm_service import (
    LlmProviderType,
    generate_bazi_interpretation,
    generate_interpretation,
    get_llm_config,
    stream_interpretation,
)
from services.prometheus_monitoring import record_llm_call, record_llm_draft_action
from services.rate_limit import limiter

router = APIRouter(prefix="/api/v1/llm", tags=["LLM辅助解读"])
logger = logging.getLogger(__name__)

# W4 修复：(case_id, module) → rendered_facts 中间结果缓存（30 分钟 TTL，最多 256 条）
_rendered_facts_cache: TTLCache[tuple[str, str], str] = TTLCache(maxsize=256, ttl=1800)
_rendered_facts_lock = threading.Lock()


# ─────────────────────────── helpers ────────────────────────────────────────


def _to_resp(d: LlmDraft) -> LlmDraftResponse:
    assert d.id is not None
    return LlmDraftResponse(
        id=d.id,
        chart_hash=d.chart_hash,
        provider=d.provider,
        model=d.model,
        prompt_version=d.prompt_version,
        draft_text=d.draft_text,
        status=d.status,
        reviewer=d.reviewer,
        reviewer_notes=d.reviewer_notes,
        input_tokens=d.input_tokens,
        output_tokens=d.output_tokens,
        cost_usd_estimate=d.cost_usd_estimate,
        created_at=d.created_at,
        reviewed_at=d.reviewed_at,
        deleted_at=d.deleted_at,
    )


# ─────────────────────────── endpoints ──────────────────────────────────────


@router.get(
    "/config",
    response_model=LlmConfigResponse,
    summary="查询当前 LLM provider 配置",
)
def get_config() -> LlmConfigResponse:
    """无需登录。返回当前检测到的 provider 及可用状态。"""
    cfg = get_llm_config()
    is_mock = cfg.provider == LlmProviderType.MOCK
    return LlmConfigResponse(
        provider=cfg.provider.value,
        model=cfg.model,
        available=True,
        note="当前为 Mock 模式（无真实 API Key），生成模板化草稿"
        if is_mock
        else f"已配置 {cfg.provider.value} / {cfg.model}",
    )


@router.post(
    "/interpret",
    response_model=LlmDraftResponse,
    summary="同步生成并保存命盘解读草稿",
    status_code=201,
)
@limiter.limit("10/minute")
async def interpret(
    request: Request,
    payload: LlmInterpretRequest,
    _user: RequiredUser,
    session: Session = Depends(get_session),
) -> LlmDraftResponse:
    """
    提交命盘参数，调用 LLM 生成解读草稿并持久化。
    若该 chart_hash 已有 pending_review 草稿，返回最新的已有记录（幂等）。
    """
    # 幂等：已有 pending_review 草稿直接返回
    existing = session.exec(
        select(LlmDraft)
        .where(LlmDraft.chart_hash == payload.chart_hash)
        .where(LlmDraft.status == "pending_review")
        .where(LlmDraft.deleted_at.is_(None))  # type: ignore[attr-defined]
        .order_by(LlmDraft.created_at.desc())  # type: ignore[attr-defined]
        .limit(1)
    ).first()
    if existing:
        return _to_resp(existing)

    # Phase A4: 构建关键词 → 检索古籍证据
    keywords: list[str] = []
    if payload.geju_name:
        keywords.append(payload.geju_name)
    if payload.yongshen_favor:
        keywords.extend(payload.yongshen_favor)
    # 从 pattern_summary 中补充关键词（取前 2 个空格分隔词）
    if payload.pattern_summary:
        keywords.extend(payload.pattern_summary.split()[:2])

    evidence: list[str] = []
    if keywords:
        raw_evidence = fetch_evidence(keywords, top_k=3)
        evidence = [f"《{e['title']}》：{e['passage']}" for e in raw_evidence]

    # 选择解读函数：有格局信息则走八字专用路径，否则走紫微路径
    use_bazi_path = bool(payload.geju_name or payload.yongshen_favor)

    # 调用 LLM
    try:
        if use_bazi_path:
            # 构建 rendered_facts 文本
            facts_lines = []
            if payload.geju_name:
                facts_lines.append(f"格局：{payload.geju_name}")
            if payload.yongshen_favor:
                facts_lines.append(f"用神喜用：{'、'.join(payload.yongshen_favor)}")
            if payload.pattern_summary:
                facts_lines.append(f"格局摘要：{payload.pattern_summary}")
            if payload.birth_info_summary:
                facts_lines.append(f"出生信息：{payload.birth_info_summary}")
            rendered_facts = "\n".join(facts_lines)
            result = await generate_bazi_interpretation(
                rendered_facts=rendered_facts,
                evidence_snippets=evidence,
            )
        else:
            result = await generate_interpretation(
                life_palace_gz=payload.life_palace_gz,
                wuxing_ju_name=payload.wuxing_ju_name,
                pattern_summary=payload.pattern_summary,
                birth_info_summary=payload.birth_info_summary,
            )
        record_llm_call(
            result.provider,
            result.duration_secs,
            success=True,
            input_tokens=result.usage.input_tokens,
            output_tokens=result.usage.output_tokens,
        )
    except Exception as exc:
        cfg = get_llm_config()
        record_llm_call(cfg.provider.value, 0.0, success=False)
        logger.error("LLM interpret failed: %s", exc)
        raise HTTPException(status_code=503, detail=f"LLM 调用失败: {exc}") from exc

    draft = LlmDraft(
        chart_hash=payload.chart_hash,
        provider=result.provider,
        model=result.model,
        prompt_version=result.prompt_version,
        draft_text=result.text,
        status="pending_review",
        input_tokens=result.usage.input_tokens,
        output_tokens=result.usage.output_tokens,
        cost_usd_estimate=result.usage.cost_usd,
    )
    session.add(draft)
    session.commit()
    session.refresh(draft)
    return _to_resp(draft)


@router.get(
    "/stream",
    summary="SSE 流式生成命盘解读草稿",
)
@limiter.limit("10/minute")
async def stream(
    request: Request,
    _user: RequiredUser,
    chart_hash: str = Query(..., max_length=64),
    life_palace_gz: str = Query(default="", max_length=10),
    wuxing_ju_name: str = Query(default="", max_length=10),
    pattern_summary: str = Query(default="", max_length=300),
    birth_info_summary: str = Query(default="", max_length=200),
    session: Session = Depends(get_session),
) -> StreamingResponse:
    """
    返回 SSE 事件流。
    生成完成后（event: done），调用方应再次 POST /api/v1/llm/interpret 保存草稿，
    或直接使用 done 事件 payload 中的 full_text 自行展示。
    """

    async def event_gen():
        full_text_buf = []
        usage_buf = {}
        async for sse_msg in stream_interpretation(life_palace_gz, wuxing_ju_name, pattern_summary, birth_info_summary):
            yield sse_msg
            # extract full_text from done event for DB save
            if sse_msg.startswith("event: done"):
                try:
                    data_line = [ln for ln in sse_msg.splitlines() if ln.startswith("data:")][0]
                    payload_obj = json.loads(data_line[5:].strip())
                    full_text_buf.append(payload_obj.get("full_text", ""))
                    usage_buf.update(payload_obj.get("usage", {}))
                except Exception:
                    pass

        # Auto-save to DB after stream completes
        if full_text_buf:
            try:
                cfg = get_llm_config()
                from services.llm_service import PROMPT_VERSION

                draft = LlmDraft(
                    chart_hash=chart_hash,
                    provider=cfg.provider.value,
                    model=cfg.model,
                    prompt_version=PROMPT_VERSION,
                    draft_text=full_text_buf[0],
                    status="pending_review",
                    input_tokens=usage_buf.get("input_tokens", 0),
                    output_tokens=usage_buf.get("output_tokens", 0),
                    cost_usd_estimate=usage_buf.get("cost_usd", 0.0),
                )
                session.add(draft)
                session.commit()
                session.refresh(draft)
                saved_id_msg = json.dumps({"saved_id": draft.id}, ensure_ascii=False)
                yield f"event: saved\ndata: {saved_id_msg}\n\n"
                record_llm_call(
                    cfg.provider.value,
                    0.0,
                    success=True,
                    input_tokens=usage_buf.get("input_tokens", 0),
                    output_tokens=usage_buf.get("output_tokens", 0),
                )
            except Exception as e:
                logger.error("Auto-save after stream failed: %s", e)

    return StreamingResponse(event_gen(), media_type="text/event-stream")


@router.get(
    "/drafts",
    response_model=LlmDraftListResponse,
    summary="列出 LLM 解读草稿",
)
def list_drafts(
    _user: RequiredUser,
    status: str | None = Query(None, description="pending_review / approved / rejected"),
    chart_hash: str | None = Query(None, max_length=64),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    session: Session = Depends(get_session),
) -> LlmDraftListResponse:
    stmt = select(LlmDraft).where(LlmDraft.deleted_at.is_(None))  # type: ignore[attr-defined]
    if status:
        stmt = stmt.where(LlmDraft.status == status)
    if chart_hash:
        stmt = stmt.where(LlmDraft.chart_hash == chart_hash)
    stmt = stmt.order_by(LlmDraft.created_at.desc())  # type: ignore[attr-defined]
    all_items = session.exec(stmt).all()
    total = len(all_items)
    return LlmDraftListResponse(
        total=total,
        items=[_to_resp(d) for d in all_items[skip : skip + limit]],
    )


@router.get(
    "/drafts/{draft_id}",
    response_model=LlmDraftResponse,
    summary="获取单条草稿详情",
)
def get_draft(
    draft_id: int,
    _user: RequiredUser,
    session: Session = Depends(get_session),
) -> LlmDraftResponse:
    d = session.get(LlmDraft, draft_id)
    if not d or d.deleted_at is not None:
        raise HTTPException(status_code=404, detail="草稿不存在")
    return _to_resp(d)


@router.patch(
    "/drafts/{draft_id}",
    response_model=LlmDraftResponse,
    summary="审核草稿（approved / rejected）",
)
def review_draft(
    draft_id: int,
    payload: LlmDraftUpdate,
    _user: RequiredUser,
    session: Session = Depends(get_session),
) -> LlmDraftResponse:
    d = session.get(LlmDraft, draft_id)
    if not d or d.deleted_at is not None:
        raise HTTPException(status_code=404, detail="草稿不存在")
    if d.status not in ("pending_review",):
        raise HTTPException(status_code=422, detail=f"草稿当前状态为 {d.status}，不可再次审核")

    d.status = payload.status
    d.reviewer = payload.reviewer
    d.reviewer_notes = payload.reviewer_notes
    d.reviewed_at = datetime.now(UTC)
    session.add(d)
    session.commit()
    session.refresh(d)
    record_llm_draft_action(payload.status)
    return _to_resp(d)


@router.delete(
    "/drafts/{draft_id}",
    status_code=204,
    summary="软删除草稿",
)
def delete_draft(
    draft_id: int,
    _user: RequiredUser,
    session: Session = Depends(get_session),
) -> None:
    d = session.get(LlmDraft, draft_id)
    if not d or d.deleted_at is not None:
        raise HTTPException(status_code=404, detail="草稿不存在")
    d.deleted_at = datetime.now(UTC)
    session.add(d)
    session.commit()


# ─────────────────────────── D1: 分模块 LLM 解读 ─────────────────────────────
from enum import Enum  # noqa: E402
import json as _json  # noqa: E402

from pydantic import BaseModel as _PydanticBase  # noqa: E402

from app.models.case import Case as _Case  # noqa: E402
from app.models.case import Snapshot as _Snapshot


class InterpretModule(str, Enum):
    dayun_narrative = "dayun_narrative"
    liunian_advice = "liunian_advice"
    career_detail = "career_detail"
    marriage_detail = "marriage_detail"
    wealth_detail = "wealth_detail"
    fengshui_suggestion = "fengshui_suggestion"


_MODULE_LABELS: dict[str, str] = {
    "dayun_narrative": "大运命运叙述（每步大运的性质与关键事件倾向）",
    "liunian_advice": "流年建议（当年行事建议与注意事项）",
    "career_detail": "事业详解（职业方向、晋升时机、行业选择）",
    "marriage_detail": "婚恋详解（感情走势、配偶特征、婚期建议）",
    "wealth_detail": "财富详解（财运趋势、投资建议、风险提示）",
    "fengshui_suggestion": "风水建议（居家方位、办公调整、色彩搭配）",
}

# Phase A4: 各模块对应古籍检索关键词
_MODULE_KEYWORDS: dict[str, list[str]] = {
    "career_detail": ["事业", "官星", "正官", "七杀"],
    "wealth_detail": ["财星", "偏财", "正财"],
    "marriage_detail": ["婚姻", "配偶", "夫妻"],
    "dayun_narrative": ["大运", "流年", "运势"],
    "liunian_advice": ["流年", "岁运"],
    "fengshui_suggestion": ["风水", "方位", "五行"],
}


class ModuleInterpretRequest(_PydanticBase):
    case_id: str
    module: InterpretModule
    context: dict | None = None


class ModuleInterpretResponse(_PydanticBase):
    case_id: str
    module: str
    interpretation: str
    generated_at: str


@router.post(
    "/interpret-module",
    response_model=ModuleInterpretResponse,
    status_code=200,
    summary="分模块 LLM 解读（D1）",
)
@limiter.limit("10/minute")
async def interpret_module(
    request: Request,
    payload: ModuleInterpretRequest,
    _user: RequiredUser,
    session: Session = Depends(get_session),
) -> ModuleInterpretResponse:
    """
    D1: 对指定案例的某一模块进行专项 LLM 解读。
    module 枚举：dayun_narrative / liunian_advice / career_detail /
               marriage_detail / wealth_detail / fengshui_suggestion
    """
    # 1. 读取案例
    case = session.get(_Case, payload.case_id)
    if case is None or case.deleted_at is not None:
        raise HTTPException(status_code=404, detail=f"案例 {payload.case_id!r} 不存在")

    # 2. 从最新快照提取真实计算数据
    latest_snap = session.exec(
        select(_Snapshot)
        .where(_Snapshot.case_id == payload.case_id)
        .where(_Snapshot.deleted_at.is_(None))  # type: ignore[attr-defined]
        .order_by(_Snapshot.created_at.desc())  # type: ignore[attr-defined]
        .limit(1)
    ).first()
    snap_data: dict = (latest_snap.output_json or {}) if latest_snap else {}

    module_label = _MODULE_LABELS.get(payload.module.value, payload.module.value)
    extra_ctx = ""
    if payload.context:
        extra_ctx = f"\n补充上下文：{_json.dumps(payload.context, ensure_ascii=False)}"

    # 从快照提取通用命盘字段
    geju = snap_data.get("geju") or {}
    yongshen = snap_data.get("yongshen") or {}
    strength = snap_data.get("day_master_strength") or {}
    geju_name_val = (geju.get("geju_name") or "").strip()
    geju_level_val = (geju.get("geju_level") or "").strip()
    favor_list = yongshen.get("favor") or []
    avoid_list = yongshen.get("avoid") or []
    rationale = (yongshen.get("rationale") or yongshen.get("advice") or "")[:120]
    strength_tier = (strength.get("tier") or "").strip()
    strength_score = strength.get("score", "")
    common_facts = (
        f"案例：{case.name}（{case.birth_dt_local}，{case.tz}）\n"
        f"格局：{geju_name_val or '待推断'} / {geju_level_val or '—'}\n"
        f"用神：{'、'.join(favor_list) or '待推断'}  忌神：{'、'.join(avoid_list) or '—'}\n"
        f"日主强弱：{strength_tier or '—'}（{strength_score}分）\n"
        f"用神推断依据：{rationale or '—'}\n"
    )

    # 按模块追加专属快照数据
    module_val = payload.module.value
    module_specific_facts = ""
    if module_val == "wealth_detail":
        w = snap_data.get("wealth_analysis") or {}
        if w:
            industries = "、".join(w.get("industries") or [])
            annual = w.get("annual_range", "")
            strategy = (w.get("strategy") or "")[:200]
            forecasts = (w.get("dayun_forecast") or [])[:4]
            forecast_txt = "\n".join(
                f"  · {f.get('ganzhi', '')}大运（{f.get('trend', '')}）：{(f.get('description') or '')[:80]}"
                for f in forecasts
            )
            module_specific_facts = (
                f"\n【财运专项数据】\n"
                f"财运评分：{w.get('score', '—')} / 层级：{w.get('tier', '—')} / 年收入区间估算：{annual}\n"
                f"推荐行业：{industries or '—'}\n"
                f"策略建议：{strategy or '—'}\n"
                f"大运财运走势：\n{forecast_txt}"
            )
    elif module_val == "career_detail":
        c = snap_data.get("career") or {}
        if c:
            milestone = (c.get("milestones") or c.get("five_year_roadmap") or [])[:3]
            milestone_txt = " | ".join(str(m)[:50] for m in milestone)
            module_specific_facts = (
                f"\n【事业专项数据】\n"
                f"事业评分：{c.get('score', '—')} / 主线方向：{(c.get('direction') or '')[:80]}\n"
                f"适合行业：{'、'.join(c.get('industries') or [])}\n"
                f"领导力：{(c.get('leadership') or '')[:80]}\n"
                f"创业vs打工：{(c.get('entrepreneurship_vs_employment') or '')[:100]}\n"
                f"关键里程碑：{milestone_txt}"
            )
    elif module_val == "marriage_detail":
        m = snap_data.get("marriage_analysis") or {}
        if m:
            module_specific_facts = (
                f"\n【婚恋专项数据】\n"
                f"婚恋评分：{m.get('score', '—')} / 桃花：{m.get('peach_blossom', '—')}\n"
                f"配偶五行：{m.get('spouse_element', '—')} / 配偶方位：{m.get('spouse_direction', '—')}\n"
                f"最佳婚龄窗口：{m.get('best_marriage_age', '—')}\n"
                f"感情雷区：{(m.get('emotional_red_flags') or '')[:120]}\n"
                f"再婚指标：{m.get('remarriage_indicator', '—')}"
            )
    elif module_val == "dayun_narrative":
        dayun_list = snap_data.get("dayun") or []
        if dayun_list:
            parts = []
            for dy in dayun_list[:5]:
                gz = (dy.get("ganzhi") or (dy.get("stem", "") + dy.get("branch", ""))).strip()
                tg = dy.get("ten_god", "")
                age = dy.get("start_age", "")
                narr = (dy.get("narrative") or "")[:120]
                parts.append(f"  · {gz}（{tg}，约{age}岁起）：{narr}")
            module_specific_facts = "\n【大运序列数据】\n" + "\n".join(parts)
    elif module_val == "liunian_advice":
        current_fs = snap_data.get("current_fortune_summary") or {}
        liunian = snap_data.get("liunian_detail") or []
        if current_fs:
            dayun_now = current_fs.get("current_dayun_ganzhi", "")
            year_pred = current_fs.get("yearly_prediction") or {}
            top3 = current_fs.get("top_3_focus") or []
            module_specific_facts = (
                f"\n【当前运势数据】\n"
                f"当前大运：{dayun_now} / 今年流年：{current_fs.get('current_liunian_gz', '')}\n"
                f"今年预测（财/事/婚/健）：{_json.dumps(year_pred, ensure_ascii=False)[:200]}\n"
                f"最值得关注3件事：{'；'.join(str(t) for t in top3)}"
            )
        elif liunian:
            parts2 = []
            for ly in liunian[:3]:
                parts2.append(
                    f"  {ly.get('year', '')}年（{ly.get('ganzhi', '')}）评分{ly.get('score', '')}：{(ly.get('best_action') or '')[:60]}"
                )
            module_specific_facts = "\n【流年数据】\n" + "\n".join(parts2)
    elif module_val == "fengshui_suggestion":
        fs = snap_data.get("fengshui") or {}
        lucky = snap_data.get("lucky") or {}
        if fs or lucky:
            module_specific_facts = (
                f"\n【风水·开运数据】\n"
                f"吉方：{fs.get('lucky_direction', '—')} / 凶方：{fs.get('unlucky_direction', '—')}\n"
                f"推荐装饰：{(fs.get('decor_suggestions') or '')[:80]}\n"
                f"推荐植物：{(fs.get('plant_suggestions') or '')[:60]}\n"
                f"幸运色：{lucky.get('lucky_color', '—')} / 幸运数字：{lucky.get('lucky_number', '—')}\n"
                f"开运物：{lucky.get('lucky_item', '—')} / 忌讳：{lucky.get('taboo', '—')}"
            )

    rendered_facts = common_facts + module_specific_facts + extra_ctx

    # Phase A4: 根据模块检索古籍证据
    module_keywords = _MODULE_KEYWORDS.get(payload.module.value, [])
    evidence: list[str] = []
    if module_keywords:
        raw_evidence = fetch_evidence(module_keywords, top_k=3)
        evidence = [f"《{e['title']}》：{e['passage']}" for e in raw_evidence]
    try:
        result = await generate_bazi_interpretation(
            rendered_facts=rendered_facts,
            evidence_snippets=evidence,
            module_type=payload.module.value,
        )
        record_llm_call(
            result.provider,
            result.duration_secs,
            success=True,
            input_tokens=result.usage.input_tokens,
            output_tokens=result.usage.output_tokens,
        )
    except Exception as exc:
        cfg = get_llm_config()
        record_llm_call(cfg.provider.value, 0.0, success=False)
        logger.error("LLM interpret-module failed: %s", exc)
        raise HTTPException(status_code=503, detail=f"LLM 调用失败: {exc}") from exc

    return ModuleInterpretResponse(
        case_id=payload.case_id,
        module=payload.module.value,
        interpretation=result.text,
        generated_at=datetime.now(UTC).isoformat(),
    )


# ─────────────────────────── D3: 完整八字一键解读 /interpret-bazi ────────────
import hashlib as _hashlib  # noqa: E402

from app.schemas.bazi import BaziFullRequest as _BaziFullRequest  # noqa: E402
from services.bazi_full_service import bazi_full as _bazi_full  # noqa: E402
from services.bazi_template_renderer import render_summary as _render_summary  # noqa: E402


class BaziInterpretRequest(_PydanticBase):
    """D3 请求体：通过案例 ID 触发完整八字 → 规则 → 模板 → LLM 解读链。"""

    case_id: str
    module: str | None = None  # 可选：聚焦某模块（career_detail 等）
    chart_hash: str | None = None  # 可选：客户端自定义 hash，默认按 case_id 派生


@router.post(
    "/interpret-bazi",
    response_model=LlmDraftResponse,
    status_code=201,
    summary="完整八字一键解读：case → bazi_full → 规则引擎 → Jinja2 → LLM（D3）",
)
@limiter.limit("10/minute")
async def interpret_bazi(
    request: Request,
    payload: BaziInterpretRequest,
    _user: RequiredUser,
    session: Session = Depends(get_session),
) -> LlmDraftResponse:
    """
    D3: 根据 case_id 完整走通八字解读链：

    1. 加载 Case → 构建 BaziFullRequest
    2. 调用 bazi_full() 计算八字（含 rule_matches）
    3. 提取关键词 → fetch_evidence() 检索古籍
    4. render_summary() 渲染 Jinja2 事实摘要
    5. generate_bazi_interpretation() 生成 LLM 解读文本
    6. 保存 LlmDraft 并返回
    """
    # 1. 读取案例
    case = session.get(_Case, payload.case_id)
    if case is None or case.deleted_at is not None:
        raise HTTPException(status_code=404, detail=f"案例 {payload.case_id!r} 不存在")

    # 2. 确定 chart_hash（幂等键）
    chart_hash = (
        payload.chart_hash
        or _hashlib.sha256(f"bazi:{payload.case_id}:{payload.module or ''}".encode()).hexdigest()[:24]
    )

    # 幂等：已有 pending_review 草稿直接返回
    existing = session.exec(
        select(LlmDraft)
        .where(LlmDraft.chart_hash == chart_hash)
        .where(LlmDraft.status == "pending_review")
        .where(LlmDraft.deleted_at.is_(None))  # type: ignore[attr-defined]
        .order_by(LlmDraft.created_at.desc())  # type: ignore[attr-defined]
        .limit(1)
    ).first()
    if existing:
        return _to_resp(existing)

    # 3. 构建 BaziFullRequest
    try:
        from datetime import datetime as _dt

        dt_obj = _dt.fromisoformat(case.birth_dt_local)
    except (ValueError, TypeError) as exc:
        raise HTTPException(
            status_code=422,
            detail=f"案例 birth_dt_local 格式无效：{case.birth_dt_local!r}",
        ) from exc

    bazi_req = _BaziFullRequest(
        dt=dt_obj,
        lon=case.lon or 116.4,
        tz=case.tz or "Asia/Shanghai",
        solar_time_enabled=bool(case.solar_time_enabled),
        mode="dual",
    )

    # 4. 计算八字（含规则引擎匹配）
    try:
        bazi_result = _bazi_full(bazi_req, request_id=f"interpret-bazi:{payload.case_id}")
    except Exception as exc:
        logger.error("bazi_full failed for case %s: %s", payload.case_id, exc)
        raise HTTPException(status_code=503, detail=f"八字计算失败：{exc}") from exc

    # 5. 构建检索关键词
    keywords: list[str] = []
    geju_name = ""
    if bazi_result.geju:
        geju_name = getattr(bazi_result.geju, "geju_name", "") or ""
        if geju_name:
            keywords.append(geju_name)
    if bazi_result.yongshen and bazi_result.yongshen.favor:
        keywords.extend(bazi_result.yongshen.favor)
    # 从 rule_matches 补充 flags 关键词
    for rm in (bazi_result.rule_matches or [])[:3]:
        flags = rm if isinstance(rm, dict) else {}
        for flag in (flags.get("flags") or [])[:2]:
            keywords.append(str(flag))
    if payload.module:
        keywords.extend(_MODULE_KEYWORDS.get(payload.module, []))

    # 6. 检索古籍证据
    evidence_snippets: list[dict] = []
    if keywords:
        evidence_snippets = fetch_evidence(list(dict.fromkeys(keywords))[:8], top_k=3)

    # 7. Jinja2 渲染事实摘要（W4：先查 TTLCache，命中则跳过重算）
    _cache_key = (payload.case_id, payload.module or "")
    with _rendered_facts_lock:
        _cached = _rendered_facts_cache.get(_cache_key)
    if _cached is not None:
        rendered_facts = _cached
        logger.debug("W4 cache hit: rendered_facts for case=%s module=%s", payload.case_id, payload.module)
    else:
        try:
            rendered_facts = _render_summary(bazi_result, evidence_snippets)
        except Exception as exc:
            logger.warning("render_summary error: %s — falling back to basic facts", exc)
            rendered_facts = (
                f"格局：{geju_name or '待推断'}\n"
                f"用神：{', '.join(bazi_result.yongshen.favor) if bazi_result.yongshen else '待推断'}\n"
                f"案例：{case.name}，出生：{case.birth_dt_local}"
            )
        with _rendered_facts_lock:
            _rendered_facts_cache[_cache_key] = rendered_facts

    # 8. 格式化 evidence 供 LLM prompt
    evidence_strs: list[str] = [
        f"《{e.get('title', '')}》：{e.get('passage', e.get('excerpt', ''))}" for e in evidence_snippets
    ]

    # 9. 调用 LLM 生成解读
    try:
        result = await generate_bazi_interpretation(
            rendered_facts=rendered_facts,
            evidence_snippets=evidence_strs,
        )
        record_llm_call(
            result.provider,
            result.duration_secs,
            success=True,
            input_tokens=result.usage.input_tokens,
            output_tokens=result.usage.output_tokens,
        )
    except Exception as exc:
        cfg = get_llm_config()
        record_llm_call(cfg.provider.value, 0.0, success=False)
        logger.error("interpret-bazi LLM call failed: %s", exc)
        raise HTTPException(status_code=503, detail=f"LLM 调用失败: {exc}") from exc

    # 10. 保存草稿
    draft = LlmDraft(
        chart_hash=chart_hash,
        provider=result.provider,
        model=result.model,
        prompt_version=result.prompt_version,
        draft_text=result.text,
        status="pending_review",
        input_tokens=result.usage.input_tokens,
        output_tokens=result.usage.output_tokens,
        cost_usd_estimate=result.usage.cost_usd,
    )
    session.add(draft)
    session.commit()
    session.refresh(draft)
    return _to_resp(draft)
