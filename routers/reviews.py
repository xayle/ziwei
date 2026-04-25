"""
审核面板路由 (§3 + §8 + W1)

路由注册顺序说明：
  静态路径 (/reviews/stats, /reviews/queue, /reviews/my-queue, /reviews/bulk_action)
  必须在动态路径 (/reviews/{review_id}) 前注册，否则 FastAPI 会将静态段当
  作整数 path param 解析失败（返回 422）。

  POST   /api/v1/reviews              — 提交命盘进审核队列（无需登录）
  GET    /api/v1/reviews              — 列出审核记录（需登录）
  GET    /api/v1/reviews/stats        — 各状态数量统计（需登录）
  GET    /api/v1/reviews/queue        — 待审核 FIFO 队列（需登录）
  GET    /api/v1/reviews/my-queue     — 我的审核队列（需登录）
  POST   /api/v1/reviews/bulk_action  — 批量操作（需登录）
  GET    /api/v1/reviews/{id}         — 获取单条详情（需登录）
  PATCH  /api/v1/reviews/{id}         — 更新状态/备注（需登录）
  DELETE /api/v1/reviews/{id}         — 软删除（需登录）
  GET    /api/v1/reviews/{id}/history — 查看变更历史（需登录）
  POST   /api/v1/reviews/{id}/assign  — W1 分配审核员（需登录）
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlmodel import Session, select

from db import get_session
from app.models import ChartReview, User
from app.models.review_history import ChartReviewHistory
from app.schemas.review import (
    BulkReviewAction,
    BulkReviewResult,
    ChartReviewCreate,
    ChartReviewListResponse,
    ChartReviewResponse,
    ChartReviewUpdate,
    ReviewAssigneeItem,
    ReviewAssigneeListResponse,
    ReviewHistoryItem,
    ReviewHistoryResponse,
    ReviewStats,
)
from app.dependencies import RequiredUser
from services.prometheus_monitoring import record_review_submit, record_review_action

router = APIRouter(prefix="/api/v1", tags=["reviews"])

ALGORITHM_VERSION = "2.1.0"
REVIEW_ASSIGNEE_ROLE_PRIORITY = {
    "owner": 0,
    "admin": 1,
    "reviewer": 2,
    "qa": 3,
    "ops": 4,
    "editor": 5,
}


def _normalize_role(role: str | None) -> str:
    return (role or "").strip().lower()


def _is_review_assignee_candidate(user: User, current_username: str) -> bool:
    if user.username == current_username:
        return True
    if user.is_admin:
        return True
    return _normalize_role(user.role) in REVIEW_ASSIGNEE_ROLE_PRIORITY


def _review_assignee_sort_key(user: User, current_username: str) -> tuple[int, int, str]:
    normalized_role = _normalize_role(user.role)
    return (
        0 if user.username == current_username else 1,
        REVIEW_ASSIGNEE_ROLE_PRIORITY.get(normalized_role, 99 if not user.is_admin else -1),
        user.username.lower(),
    )


def _to_resp(r: ChartReview) -> ChartReviewResponse:
    return ChartReviewResponse(
        id=r.id,
        report_hash=r.report_hash,
        birth_info=r.birth_info,
        life_palace_gz=r.life_palace_gz,
        wuxing_ju_name=r.wuxing_ju_name,
        pattern_summary=r.pattern_summary,
        status=r.status,
        reviewer=r.reviewer,
        notes=r.notes,
        reject_reason=r.reject_reason,
        algorithm_version=r.algorithm_version,
        template_version=r.template_version,
        revision=r.revision,
        created_at=r.created_at,
        reviewed_at=r.reviewed_at,
        deleted_at=r.deleted_at,
    )


@router.post("/reviews", response_model=ChartReviewResponse, summary="提交命盘进审核队列", status_code=201)
def submit_review(payload: ChartReviewCreate, session: Session = Depends(get_session)) -> ChartReviewResponse:
    existing = session.exec(
        select(ChartReview)
        .where(ChartReview.report_hash == payload.report_hash)
        .where(ChartReview.status == "pending")
        .where(ChartReview.deleted_at.is_(None))
    ).first()
    if existing:
        record_review_submit(is_duplicate=True)
        return _to_resp(existing)
    review = ChartReview(
        report_hash=payload.report_hash,
        birth_info=payload.birth_info,
        life_palace_gz=payload.life_palace_gz,
        wuxing_ju_name=payload.wuxing_ju_name,
        pattern_summary=payload.pattern_summary,
        template_version=payload.template_version,
        algorithm_version=ALGORITHM_VERSION,
        status="pending",
        created_at=datetime.now(timezone.utc).replace(tzinfo=None),
    )
    session.add(review)
    session.commit()
    session.refresh(review)
    record_review_submit(is_duplicate=False)
    return _to_resp(review)


@router.get("/reviews", response_model=ChartReviewListResponse, summary="列出审核记录")
def list_reviews(
    current_user: RequiredUser,
    session: Session = Depends(get_session),
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> ChartReviewListResponse:
    stmt = select(ChartReview).where(ChartReview.deleted_at.is_(None)).order_by(ChartReview.created_at.desc())
    if status:
        stmt = stmt.where(ChartReview.status == status)
    all_records = session.exec(stmt).all()
    total = len(all_records)
    start = (page - 1) * page_size
    items = [_to_resp(r) for r in all_records[start : start + page_size]]
    return ChartReviewListResponse(total=total, items=items)


@router.get("/reviews/stats", response_model=ReviewStats, summary="审核记录统计")
def review_stats(current_user: RequiredUser, session: Session = Depends(get_session)) -> ReviewStats:
    all_records = session.exec(select(ChartReview).where(ChartReview.deleted_at.is_(None))).all()
    counts: dict[str, int] = {"pending": 0, "approved": 0, "rejected": 0, "revised": 0}
    for r in all_records:
        if r.status in counts:
            counts[r.status] += 1
    return ReviewStats(total=len(all_records), pending=counts["pending"], approved=counts["approved"],
                       rejected=counts["rejected"], revised=counts["revised"])


@router.get("/reviews/queue", response_model=ChartReviewListResponse, summary="W1 待审核队列")
def review_queue(
    current_user: RequiredUser,
    session: Session = Depends(get_session),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> ChartReviewListResponse:
    stmt = (select(ChartReview).where(ChartReview.status == "pending")
            .where(ChartReview.deleted_at.is_(None)).order_by(ChartReview.created_at.asc()))
    all_records = session.exec(stmt).all()
    total = len(all_records)
    start = (page - 1) * page_size
    return ChartReviewListResponse(total=total, items=[_to_resp(r) for r in all_records[start : start + page_size]])


@router.get("/reviews/my-queue", response_model=ChartReviewListResponse, summary="W1 我的审核队列")
def my_review_queue(
    current_user: RequiredUser,
    session: Session = Depends(get_session),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> ChartReviewListResponse:
    username = current_user.username if hasattr(current_user, "username") else str(current_user.id)
    stmt = (select(ChartReview).where(ChartReview.reviewer == username)
            .where(ChartReview.status == "pending").where(ChartReview.deleted_at.is_(None))
            .order_by(ChartReview.created_at.asc()))
    all_records = session.exec(stmt).all()
    total = len(all_records)
    start = (page - 1) * page_size
    return ChartReviewListResponse(total=total, items=[_to_resp(r) for r in all_records[start : start + page_size]])


@router.post("/reviews/bulk_action", response_model=BulkReviewResult, summary="批量审核操作")
def bulk_review_action(
    payload: BulkReviewAction, current_user: RequiredUser, session: Session = Depends(get_session)
) -> BulkReviewResult:
    allowed_actions = {"approved", "rejected", "revised", "delete"}
    if payload.action not in allowed_actions:
        raise HTTPException(status_code=422, detail=f"action 必须为 {sorted(allowed_actions)} 之一")
    succeeded: list[int] = []
    failed: list[int] = []
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    for rid in payload.ids:
        review = session.get(ChartReview, rid)
        if not review or review.deleted_at is not None:
            failed.append(rid)
            continue
        try:
            if payload.action == "delete":
                review.deleted_at = now
            else:
                review.status = payload.action
                review.reviewer = payload.reviewer or review.reviewer or ""
                if payload.notes:
                    review.notes = payload.notes
                if payload.reject_reason and payload.action == "rejected":
                    review.reject_reason = payload.reject_reason
                review.reviewed_at = now
                if payload.action == "revised":
                    review.revision = (review.revision or 1) + 1
            session.add(review)
            succeeded.append(rid)
            session.add(ChartReviewHistory(
                review_id=rid,
                status=payload.action if payload.action != "delete" else "deleted",
                reviewer=payload.reviewer or "",
                notes=payload.notes or "",
                reject_reason=payload.reject_reason or "",
                change_type="bulk_action",
                changed_at=now,
            ))
        except Exception:
            failed.append(rid)
    session.commit()
    if payload.action != "delete" and succeeded:
        record_review_action(payload.action)
    return BulkReviewResult(succeeded=succeeded, failed=failed, total=len(payload.ids), action=payload.action)


@router.get("/reviews/assignees", response_model=ReviewAssigneeListResponse, summary="审核员候选列表")
def review_assignees(current_user: RequiredUser, session: Session = Depends(get_session)) -> ReviewAssigneeListResponse:
    current_username = current_user.username if hasattr(current_user, "username") else str(current_user.id)
    users = session.exec(
        select(User)
        .where(User.deleted_at.is_(None))  # type: ignore[arg-type]
        .where(User.is_active.is_(True))  # type: ignore[arg-type]
        .order_by(User.is_admin.desc(), User.username.asc())
    ).all()
    items = [
        ReviewAssigneeItem(
            id=int(user.id or 0),
            username=user.username,
            email=user.email,
            role=user.role,
            is_admin=bool(user.is_admin),
            is_current_user=user.username == current_username,
        )
        for user in sorted(users, key=lambda user: _review_assignee_sort_key(user, current_username))
        if user.username and _is_review_assignee_candidate(user, current_username)
    ]
    return ReviewAssigneeListResponse(current_username=current_username, items=items)


@router.get("/reviews/{review_id}", response_model=ChartReviewResponse, summary="获取单条审核详情")
def get_review(review_id: int, current_user: RequiredUser, session: Session = Depends(get_session)) -> ChartReviewResponse:
    review = session.get(ChartReview, review_id)
    if not review or review.deleted_at is not None:
        raise HTTPException(status_code=404, detail="审核记录不存在")
    return _to_resp(review)


@router.patch("/reviews/{review_id}", response_model=ChartReviewResponse, summary="审核员更新状态/备注")
def update_review(
    review_id: int, payload: ChartReviewUpdate, current_user: RequiredUser, session: Session = Depends(get_session)
) -> ChartReviewResponse:
    review = session.get(ChartReview, review_id)
    if not review or review.deleted_at is not None:
        raise HTTPException(status_code=404, detail="审核记录不存在")
    review.status = payload.status
    if payload.reviewer:
        review.reviewer = payload.reviewer
    if payload.notes:
        review.notes = payload.notes
    if payload.reject_reason:
        review.reject_reason = payload.reject_reason
    review.reviewed_at = datetime.now(timezone.utc).replace(tzinfo=None)
    if payload.status == "revised":
        review.revision = (review.revision or 1) + 1
    session.add(review)
    session.add(ChartReviewHistory(
        review_id=review_id,
        status=payload.status,
        reviewer=payload.reviewer or "",
        notes=payload.notes or "",
        reject_reason=payload.reject_reason or "",
        change_type="status_change",
        changed_at=datetime.now(timezone.utc).replace(tzinfo=None),
    ))
    session.commit()
    session.refresh(review)
    record_review_action(payload.status)
    return _to_resp(review)


@router.delete("/reviews/{review_id}", status_code=204, summary="软删除审核记录")
def delete_review(review_id: int, current_user: RequiredUser, session: Session = Depends(get_session)) -> None:
    review = session.get(ChartReview, review_id)
    if not review or review.deleted_at is not None:
        raise HTTPException(status_code=404, detail="审核记录不存在")
    review.deleted_at = datetime.now(timezone.utc).replace(tzinfo=None)
    session.add(review)
    session.commit()


@router.get("/reviews/{review_id}/history", response_model=ReviewHistoryResponse, summary="获取审核变更历史")
def get_review_history(review_id: int, current_user: RequiredUser, session: Session = Depends(get_session)) -> ReviewHistoryResponse:
    review = session.get(ChartReview, review_id)
    if not review or review.deleted_at is not None:
        raise HTTPException(status_code=404, detail="审核记录不存在")
    history = session.exec(
        select(ChartReviewHistory).where(ChartReviewHistory.review_id == review_id)
        .order_by(ChartReviewHistory.changed_at)
    ).all()
    items = [
        ReviewHistoryItem(id=h.id, review_id=h.review_id, status=h.status, reviewer=h.reviewer,
                          notes=h.notes, reject_reason=h.reject_reason, change_type=h.change_type,
                          changed_at=h.changed_at)
        for h in history
    ]
    return ReviewHistoryResponse(review_id=review_id, items=items, total=len(items))


class AssignReviewRequest(BaseModel):
    assignee: str


@router.post("/reviews/{review_id}/assign", response_model=ChartReviewResponse, summary="W1 分配审核员")
def assign_review(
    review_id: int, payload: AssignReviewRequest, current_user: RequiredUser, session: Session = Depends(get_session)
) -> ChartReviewResponse:
    review = session.get(ChartReview, review_id)
    if not review or review.deleted_at is not None:
        raise HTTPException(status_code=404, detail="审核记录不存在")
    if review.status != "pending":
        raise HTTPException(status_code=422, detail=f"只能分配 pending 状态的记录，当前状态为 {review.status}")
    review.reviewer = payload.assignee
    session.add(review)
    session.commit()
    session.refresh(review)
    return _to_resp(review)
