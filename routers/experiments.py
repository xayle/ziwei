"""
A/B 测试实验路由 (§9)

POST   /api/v1/experiments                   — 创建实验
GET    /api/v1/experiments                   — 列出实验
GET    /api/v1/experiments/{id}              — 获取单条实验
PUT    /api/v1/experiments/{id}              — 更新实验
DELETE /api/v1/experiments/{id}              — 软删除实验
POST   /api/v1/experiments/{id}/assign       — 将会话分配到变体
POST   /api/v1/experiments/{id}/event        — 上报实验事件
GET    /api/v1/experiments/{id}/results      — 获取实验结果统计
"""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import UTC, datetime
import hashlib
import json

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select

from app.dependencies import RequiredUser
from app.models.experiment import Experiment, ExperimentEvent
from app.schemas.experiment import (
    AssignRequest,
    AssignResponse,
    EventCreate,
    ExperimentCreate,
    ExperimentListResponse,
    ExperimentResponse,
    ExperimentResults,
    ExperimentUpdate,
    VariantDef,
    VariantStats,
)
from db import get_session
from services.prometheus_monitoring import (
    record_ab_experiment_assigned,
    record_ab_experiment_event,
)

router = APIRouter(prefix="/api/v1/experiments", tags=["A/B实验"])


# ─────────────────────────── helpers ───────────────────────────────────────


def _exp_to_resp(exp: Experiment) -> ExperimentResponse:
    try:
        variants_raw = json.loads(exp.variants or "[]")
        variants = [VariantDef(**v) for v in variants_raw]
    except Exception:
        variants = []
    try:
        traffic_split: dict = json.loads(exp.traffic_split or "{}")
    except Exception:
        traffic_split = {}
    assert exp.id is not None
    return ExperimentResponse(
        id=exp.id,
        name=exp.name,
        description=exp.description,
        status=exp.status,
        variants=variants,
        traffic_split=traffic_split,
        target_metric=exp.target_metric,
        hypothesis=exp.hypothesis,
        min_sample_size=exp.min_sample_size,
        created_at=exp.created_at,
        updated_at=exp.updated_at,
        started_at=exp.started_at,
        ended_at=exp.ended_at,
    )


def _build_traffic_split(variants: list[VariantDef]) -> dict:
    """按权重计算每个变体的百分比（保证总和 = 100）。"""
    total_weight = sum(v.weight for v in variants)
    split: dict = {}
    remainder = 100
    for i, v in enumerate(variants[:-1]):
        pct = round(v.weight / total_weight * 100)
        split[v.name] = pct
        remainder -= pct
    split[variants[-1].name] = remainder
    return split


def _assign_variant(variants: list[VariantDef], traffic_split: dict, session_id: str) -> str:
    """
    确定性地将 session_id 分配到变体（哈希取模 + 流量分割）。
    相同 session_id 始终获得相同变体。
    """
    hash_val = int(hashlib.md5(session_id.encode()).hexdigest(), 16) % 100
    cumulative = 0
    for variant in variants:
        cumulative += traffic_split.get(variant.name, 0)
        if hash_val < cumulative:
            return variant.name
    return variants[-1].name  # fallback


# ─────────────────────────── 实验 CRUD ──────────────────────────────────────


@router.post(
    "",
    response_model=ExperimentResponse,
    summary="创建 A/B 实验",
    status_code=201,
)
def create_experiment(
    payload: ExperimentCreate,
    _user: RequiredUser,
    session: Session = Depends(get_session),
) -> ExperimentResponse:
    traffic_split = _build_traffic_split(payload.variants)
    exp = Experiment(
        name=payload.name,
        description=payload.description,
        status="draft",
        variants=json.dumps([v.model_dump() for v in payload.variants], ensure_ascii=False),
        traffic_split=json.dumps(traffic_split),
        target_metric=payload.target_metric,
        hypothesis=payload.hypothesis,
        min_sample_size=payload.min_sample_size,
    )
    session.add(exp)
    session.commit()
    session.refresh(exp)
    return _exp_to_resp(exp)


@router.get(
    "",
    response_model=ExperimentListResponse,
    summary="列出 A/B 实验",
)
def list_experiments(
    _user: RequiredUser,
    status: str | None = Query(None, description="按状态筛选: draft/running/paused/completed"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    session: Session = Depends(get_session),
) -> ExperimentListResponse:
    stmt = select(Experiment).where(Experiment.deleted_at.is_(None))  # type: ignore[attr-defined]
    if status:
        stmt = stmt.where(Experiment.status == status)
    stmt = stmt.order_by(Experiment.created_at.desc())  # type: ignore[attr-defined]
    all_items = session.exec(stmt).all()
    total = len(all_items)
    items = [_exp_to_resp(e) for e in all_items[skip : skip + limit]]
    return ExperimentListResponse(total=total, items=items)


@router.get(
    "/{exp_id}",
    response_model=ExperimentResponse,
    summary="获取单条实验详情",
)
def get_experiment(
    exp_id: int,
    _user: RequiredUser,
    session: Session = Depends(get_session),
) -> ExperimentResponse:
    exp = session.get(Experiment, exp_id)
    if not exp or exp.deleted_at is not None:
        raise HTTPException(status_code=404, detail="实验不存在")
    return _exp_to_resp(exp)


@router.put(
    "/{exp_id}",
    response_model=ExperimentResponse,
    summary="更新实验（状态/描述/假设等）",
)
def update_experiment(
    exp_id: int,
    payload: ExperimentUpdate,
    _user: RequiredUser,
    session: Session = Depends(get_session),
) -> ExperimentResponse:
    exp = session.get(Experiment, exp_id)
    if not exp or exp.deleted_at is not None:
        raise HTTPException(status_code=404, detail="实验不存在")

    # 状态转换规则
    if payload.status:
        valid_transitions: dict = {
            "draft": {"running"},
            "running": {"paused", "completed"},
            "paused": {"running", "completed"},
            "completed": set(),
        }
        if payload.status not in valid_transitions.get(exp.status, set()):
            raise HTTPException(
                status_code=422,
                detail=f"不允许从 {exp.status} 切换至 {payload.status}",
            )
        now = datetime.now(UTC)
        if payload.status == "running" and exp.started_at is None:
            exp.started_at = now
        if payload.status == "completed":
            exp.ended_at = now
        exp.status = payload.status

    if payload.name is not None:
        exp.name = payload.name
    if payload.description is not None:
        exp.description = payload.description
    if payload.hypothesis is not None:
        exp.hypothesis = payload.hypothesis
    if payload.min_sample_size is not None:
        exp.min_sample_size = payload.min_sample_size
    if payload.target_metric is not None:
        exp.target_metric = payload.target_metric

    exp.updated_at = datetime.now(UTC)
    session.add(exp)
    session.commit()
    session.refresh(exp)
    return _exp_to_resp(exp)


@router.delete(
    "/{exp_id}",
    status_code=204,
    summary="软删除实验",
)
def delete_experiment(
    exp_id: int,
    _user: RequiredUser,
    session: Session = Depends(get_session),
) -> None:
    exp = session.get(Experiment, exp_id)
    if not exp or exp.deleted_at is not None:
        raise HTTPException(status_code=404, detail="实验不存在")
    if exp.status == "running":
        raise HTTPException(status_code=422, detail="运行中的实验无法删除，请先暂停或完成")
    exp.deleted_at = datetime.now(UTC)
    exp.updated_at = datetime.now(UTC)
    session.add(exp)
    session.commit()


# ─────────────────────────── 变体分配 ───────────────────────────────────────


@router.post(
    "/{exp_id}/assign",
    response_model=AssignResponse,
    summary="将会话分配到实验变体",
)
def assign_variant(
    exp_id: int,
    payload: AssignRequest,
    session: Session = Depends(get_session),
) -> AssignResponse:
    """
    无需登录。前端在页面加载时调用此接口，获取该会话所属变体。
    - 实验状态必须为 running，否则返回 control 变体。
    - 分配是确定性的（同一 session_id 始终返回同一变体）。
    - 若已有 assigned 事件则不重复记录（幂等）。
    """
    exp = session.get(Experiment, exp_id)
    if not exp or exp.deleted_at is not None:
        raise HTTPException(status_code=404, detail="实验不存在")

    if exp.status != "running":
        # 非运行状态：分配到 control 但不记录事件
        return AssignResponse(
            experiment_id=exp_id,
            session_id=payload.session_id,
            variant="control",
            is_new=False,
        )

    try:
        variants_raw = json.loads(exp.variants or "[]")
        variants = [VariantDef(**v) for v in variants_raw]
        traffic_split = json.loads(exp.traffic_split or "{}")
    except Exception:
        variants = [VariantDef(name="control", description="", weight=100)]
        traffic_split = {"control": 100}

    variant = _assign_variant(variants, traffic_split, payload.session_id)

    # 幂等：检查是否已有 assigned 事件
    existing = session.exec(
        select(ExperimentEvent)
        .where(ExperimentEvent.experiment_id == exp_id)
        .where(ExperimentEvent.session_id == payload.session_id)
        .where(ExperimentEvent.event_type == "assigned")
    ).first()

    is_new = existing is None
    if is_new:
        ev = ExperimentEvent(
            experiment_id=exp_id,
            variant=variant,
            event_type="assigned",
            session_id=payload.session_id,
            meta="{}",
        )
        session.add(ev)
        session.commit()
        record_ab_experiment_assigned(exp.name, variant)

    return AssignResponse(
        experiment_id=exp_id,
        session_id=payload.session_id,
        variant=variant,
        is_new=is_new,
    )


# ─────────────────────────── 事件上报 ───────────────────────────────────────


@router.post(
    "/{exp_id}/event",
    status_code=201,
    summary="上报实验事件",
)
def record_event(
    exp_id: int,
    payload: EventCreate,
    session: Session = Depends(get_session),
) -> dict:
    """无需登录。前端在用户执行关键操作时调用。"""
    exp = session.get(Experiment, exp_id)
    if not exp or exp.deleted_at is not None:
        raise HTTPException(status_code=404, detail="实验不存在")
    if exp.status not in ("running", "paused"):
        raise HTTPException(status_code=422, detail="只有 running/paused 状态的实验才能记录事件")

    meta_str = json.dumps(payload.meta, ensure_ascii=False) if payload.meta else "{}"
    ev = ExperimentEvent(
        experiment_id=exp_id,
        variant=payload.variant,
        event_type=payload.event_type,
        session_id=payload.session_id,
        meta=meta_str,
    )
    session.add(ev)
    session.commit()
    record_ab_experiment_event(exp.name, payload.variant, payload.event_type)
    return {"ok": True, "event_type": payload.event_type, "variant": payload.variant}


# ─────────────────────────── 结果分析 ───────────────────────────────────────


@router.get(
    "/{exp_id}/results",
    response_model=ExperimentResults,
    summary="获取实验结果统计",
)
def get_results(
    exp_id: int,
    _user: RequiredUser,
    session: Session = Depends(get_session),
) -> ExperimentResults:
    exp = session.get(Experiment, exp_id)
    if not exp or exp.deleted_at is not None:
        raise HTTPException(status_code=404, detail="实验不存在")

    events = session.exec(select(ExperimentEvent).where(ExperimentEvent.experiment_id == exp_id)).all()

    # 统计每个变体的 assigned 数量 + 转化数量 + 其他事件
    assigned_count: dict[str, int] = defaultdict(int)
    conversion_count: dict[str, int] = defaultdict(int)
    other_events_count: dict[str, Counter] = defaultdict(Counter)

    for ev in events:
        if ev.event_type == "assigned":
            assigned_count[ev.variant] += 1
        elif ev.event_type == exp.target_metric:
            conversion_count[ev.variant] += 1
        else:
            other_events_count[ev.variant][ev.event_type] += 1

    try:
        variants_raw = json.loads(exp.variants or "[]")
        variant_names = [v["name"] for v in variants_raw]
    except Exception:
        variant_names = list(assigned_count.keys())

    variant_stats: list[VariantStats] = []
    for vname in variant_names:
        n = assigned_count.get(vname, 0)
        c = conversion_count.get(vname, 0)
        rate = c / n if n > 0 else 0.0
        variant_stats.append(
            VariantStats(
                variant=vname,
                assigned=n,
                conversions=c,
                conversion_rate=round(rate, 4),
                other_events=dict(other_events_count.get(vname, {})),
            )
        )

    total_assigned = sum(s.assigned for s in variant_stats)

    # 仅在样本量足够时给出 winner
    winner = None
    note = f"当前总样本量 {total_assigned}，最小要求 {exp.min_sample_size}"
    if total_assigned >= exp.min_sample_size and variant_stats:
        best = max(variant_stats, key=lambda s: s.conversion_rate)
        winner = best.variant
        note = f"样本量已达标（{total_assigned}）。最高转化率变体: {best.variant}（{best.conversion_rate:.1%}）"

    return ExperimentResults(
        experiment_id=exp_id,
        experiment_name=exp.name,
        status=exp.status,
        target_metric=exp.target_metric,
        min_sample_size=exp.min_sample_size,
        total_assigned=total_assigned,
        variants=variant_stats,
        winner=winner,
        note=note,
    )
