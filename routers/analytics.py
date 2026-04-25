"""
W6 命理师仪表盘  GET /api/v1/analytics/dashboard
────────────────────────────────────────────────
汇总当前用户（或全局 ADMIN）的关键业务指标：
  - 案例数量（总量 / 本月新增）
  - 快照数量（总量 / 本月新增）
  - 审核队列概况（pending / approved / rejected）
  - 最近 7 天每天的请求量（从 AuditLog 统计）
  - 最近创建的 5 个案例
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlmodel import Session, select

from db import get_session
from app.dependencies import RequiredUser
from app.error_handling import handle_exceptions
from app.exceptions import ErrorCode
from app.models import AuditLog, Case, ChartReview, Snapshot

router = APIRouter(prefix="/api/v1/analytics", tags=["analytics"])


# ── Response models ────────────────────────────────────────────────────────

class DailyActivity(BaseModel):
    date: str        # ISO date string, e.g. "2026-03-23"
    count: int


class CaseSummary(BaseModel):
    case_id: str
    name: str
    created_at: datetime


class DashboardResponse(BaseModel):
    # 案例
    cases_total: int
    cases_this_month: int
    # 快照
    snapshots_total: int
    snapshots_this_month: int
    # 审核（全局可见）
    reviews_pending: int
    reviews_approved: int
    reviews_rejected: int
    reviews_revised: int
    # 操作活跃度（最近 7 天）
    daily_activity: List[DailyActivity]
    # 最近案例
    recent_cases: List[CaseSummary]
    # 元信息
    generated_at: datetime
    owner_id: Optional[int]


# ── Endpoint ───────────────────────────────────────────────────────────────

@router.get(
    "/dashboard",
    response_model=DashboardResponse,
    summary="W6 命理师仪表盘",
    description="返回当前用户的案例/快照/审核概况及最近 7 天操作活跃度。",
)
@handle_exceptions(ErrorCode.SYSTEM_INTERNAL_ERROR)
def get_dashboard(
    current_user: RequiredUser,
    session: Session = Depends(get_session),
) -> DashboardResponse:
    """W6: 实时聚合统计，单次 SQL 批量查询，避免 N+1。"""
    now = datetime.now(timezone.utc)
    month_start = datetime(now.year, now.month, 1, tzinfo=timezone.utc)
    uid = current_user.id

    # ── 案例统计 ────────────────────────────────────────────────────────────
    cases_q = select(Case).where(Case.owner_id == uid, Case.deleted_at.is_(None))  # type: ignore
    all_cases = session.exec(cases_q).all()
    cases_total = len(all_cases)
    cases_this_month = sum(
        1 for c in all_cases
        if c.created_at and _make_aware(c.created_at) >= month_start
    )

    # ── 快照统计 ────────────────────────────────────────────────────────────
    # 只统计属于当前用户 Case 的快照
    case_ids = [c.id for c in all_cases]
    if case_ids:
        snaps = session.exec(
            select(Snapshot).where(
                Snapshot.case_id.in_(case_ids),  # type: ignore
                Snapshot.deleted_at.is_(None),   # type: ignore
            )
        ).all()
    else:
        snaps = []
    snapshots_total = len(snaps)
    snapshots_this_month = sum(
        1 for s in snaps
        if s.created_at and _make_aware(s.created_at) >= month_start
    )

    # ── 审核统计（全局，不限用户）──────────────────────────────────────────
    review_counts: Dict[str, int] = {"pending": 0, "approved": 0, "rejected": 0, "revised": 0}
    for r in session.exec(
        select(ChartReview).where(ChartReview.deleted_at.is_(None))  # type: ignore
    ).all():
        if r.status in review_counts:
            review_counts[r.status] += 1

    # ── 最近 7 天操作活跃度（AuditLog 按 created_at 分组）────────────────
    seven_days_ago = now - timedelta(days=7)
    audit_rows = session.exec(
        select(AuditLog).where(
            AuditLog.user_id == uid,
            AuditLog.created_at >= seven_days_ago.replace(tzinfo=None),  # type: ignore
        )
    ).all()

    day_counts: Dict[str, int] = {}
    for i in range(7):
        d = (now - timedelta(days=6 - i)).date().isoformat()
        day_counts[d] = 0
    for row in audit_rows:
        if row.created_at:
            d = row.created_at.date().isoformat()
            if d in day_counts:
                day_counts[d] += 1
    daily_activity = [DailyActivity(date=d, count=c) for d, c in sorted(day_counts.items())]

    # ── 最近 5 个案例 ───────────────────────────────────────────────────────
    recent_cases = [
        CaseSummary(
            case_id=c.id,
            name=c.name or "",
            created_at=_make_aware(c.created_at) if c.created_at else now,
        )
        for c in sorted(all_cases, key=lambda x: x.created_at or datetime.min, reverse=True)[:5]
    ]

    return DashboardResponse(
        cases_total=cases_total,
        cases_this_month=cases_this_month,
        snapshots_total=snapshots_total,
        snapshots_this_month=snapshots_this_month,
        reviews_pending=review_counts["pending"],
        reviews_approved=review_counts["approved"],
        reviews_rejected=review_counts["rejected"],
        reviews_revised=review_counts["revised"],
        daily_activity=daily_activity,
        recent_cases=recent_cases,
        generated_at=now,
        owner_id=uid,
    )


def _make_aware(dt: datetime) -> datetime:
    """确保 datetime 带 UTC tzinfo。"""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt
