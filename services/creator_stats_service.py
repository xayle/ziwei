"""Creator GTM stats aggregation (BE-GTM-08 / T099)."""

from __future__ import annotations

from collections import defaultdict
from datetime import UTC, datetime, timedelta

from sqlmodel import Session, select

from app.models import User
from app.models.analytics_event import AnalyticsEvent
from app.schemas.creator_stats import (
    CreatorFunnelStep,
    CreatorStatsResponse,
    CreatorStatsTotals,
    CreatorTopicCohort,
)

_PAID_TIERS = frozenset({"volume_pass", "full_book", "pro"})


def _aware(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt


def _is_paid(entitlement: str | None) -> bool:
    return (entitlement or "free").strip().lower() in _PAID_TIERS


def _topic_key(source: str | None, campaign: str | None, content_id: str | None) -> str:
    s = (source or "organic").strip() or "organic"
    c = (campaign or "").strip()
    v = (content_id or "").strip()
    return f"{s}|{c}|{v}"


def build_creator_stats(session: Session, *, window_days: int = 30) -> CreatorStatsResponse:
    """聚合注册归因 cohort + 漏斗埋点（管理员面板用）。"""
    days = max(1, min(365, int(window_days)))
    now = datetime.now(UTC)
    since = now - timedelta(days=days)

    users = session.exec(select(User).where(User.deleted_at.is_(None))).all()  # type: ignore[union-attr]
    in_window = [u for u in users if (created := _aware(u.created_at)) is not None and created >= since]

    topic_regs: dict[str, dict[str, int | str | None]] = {}
    attributed = 0
    paid_total = 0

    for u in in_window:
        key = _topic_key(u.utm_source, u.utm_campaign, u.content_id)
        has_attr = bool(u.utm_source or u.utm_campaign or u.content_id)
        if has_attr:
            attributed += 1
        paid = _is_paid(u.entitlement)
        if paid:
            paid_total += 1
        bucket = topic_regs.setdefault(
            key,
            {
                "utm_source": u.utm_source or ("organic" if not has_attr else None),
                "utm_campaign": u.utm_campaign,
                "content_id": u.content_id,
                "registrations": 0,
                "paid_conversions": 0,
            },
        )
        bucket["registrations"] = int(bucket["registrations"]) + 1
        if paid:
            bucket["paid_conversions"] = int(bucket["paid_conversions"]) + 1

    topics: list[CreatorTopicCohort] = []
    for key, bucket in topic_regs.items():
        regs = int(bucket["registrations"])
        paid = int(bucket["paid_conversions"])
        topics.append(
            CreatorTopicCohort(
                topic_key=key,
                utm_source=bucket["utm_source"] if isinstance(bucket["utm_source"], str) else None,
                utm_campaign=bucket["utm_campaign"] if isinstance(bucket["utm_campaign"], str) else None,
                content_id=bucket["content_id"] if isinstance(bucket["content_id"], str) else None,
                registrations=regs,
                paid_conversions=paid,
                conversion_rate=round(paid / regs, 4) if regs else 0.0,
            )
        )
    topics.sort(key=lambda t: (-t.registrations, t.topic_key))

    # Analytics funnel in window
    events = session.exec(
        select(AnalyticsEvent).where(AnalyticsEvent.created_at >= since)  # type: ignore[operator]
    ).all()
    type_counts: dict[str, int] = defaultdict(int)
    for ev in events:
        type_counts[ev.event_type] += 1

    funnel_order = [
        "landing_cta_click",
        "funnel_step",
        "volume_view",
        "volume_unlock_prompt",
        "share_card_export",
    ]
    funnel = [CreatorFunnelStep(step=step, count=type_counts.get(step, 0)) for step in funnel_order]

    totals = CreatorStatsTotals(
        users=len(in_window),
        attributed_users=attributed,
        paid_users=paid_total,
        landing_cta_clicks=type_counts.get("landing_cta_click", 0),
        share_card_exports=type_counts.get("share_card_export", 0),
        volume_views=type_counts.get("volume_view", 0),
    )

    return CreatorStatsResponse(
        generated_at=now,
        window_days=days,
        totals=totals,
        topics=topics,
        funnel=funnel,
    )
