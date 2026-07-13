"""Persist GTM analytics events (BE-GTM-01)."""

from __future__ import annotations

from datetime import UTC, datetime
import json

from sqlmodel import Session

from app.models.analytics_event import AnalyticsEvent
from app.schemas.analytics_events import (
    AnalyticsEventItem,
    AnalyticsEventsBatchResponse,
    scrub_properties,
)


def ingest_analytics_events(
    session: Session,
    events: list[AnalyticsEventItem],
    *,
    user_id: int | None,
) -> AnalyticsEventsBatchResponse:
    accepted = 0
    rejected = 0
    scrubbed: list[str] = []
    now = datetime.now(UTC)

    for item in events:
        props, dropped = scrub_properties(item.properties)
        scrubbed.extend(dropped)
        try:
            row = AnalyticsEvent(
                user_id=user_id,
                session_id=(item.session_id or "")[:100],
                event_type=item.event_type,
                case_id=item.case_id,
                volume_id=item.volume_id,
                client_ts=item.ts,
                properties_json=json.dumps(props, ensure_ascii=False),
                created_at=now,
            )
            session.add(row)
            accepted += 1
        except Exception:
            rejected += 1

    if accepted:
        session.commit()
    else:
        session.rollback()

    seen: set[str] = set()
    unique_scrubbed: list[str] = []
    for key in scrubbed:
        if key not in seen:
            seen.add(key)
            unique_scrubbed.append(key)

    return AnalyticsEventsBatchResponse(
        accepted=accepted,
        rejected=rejected,
        scrubbed_pii_keys=unique_scrubbed,
    )
