"""T089 · BE-GTM-01 analytics events batch."""

from __future__ import annotations

import json

from sqlmodel import select

from app.models import AnalyticsEvent
from app.schemas.analytics_events import scrub_properties


def test_scrub_properties_drops_pii():
    cleaned, dropped = scrub_properties(
        {
            "term_id": "geju",
            "name": "张三",
            "birth_dt_local": "1990-01-01",
            "dwell_ms": 1200,
        }
    )
    assert cleaned == {"term_id": "geju", "dwell_ms": 1200}
    assert "name" in dropped
    assert "birth_dt_local" in dropped


def test_post_analytics_events_batch(client_with_auth, db_session):
    resp = client_with_auth.post(
        "/api/v1/analytics/events",
        json={
            "events": [
                {
                    "event_type": "volume_view",
                    "session_id": "sess-1",
                    "volume_id": "vol1",
                    "case_id": "case-abc",
                    "properties": {"dwell_ms": 0},
                },
                {
                    "event_type": "glossary_click",
                    "session_id": "sess-1",
                    "properties": {"term_id": "七杀", "name": "泄漏姓名"},
                },
            ]
        },
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["accepted"] == 2
    assert data["schema_version"] == "analytics-events@1.0"
    assert "name" in data["scrubbed_pii_keys"]

    rows = db_session.exec(select(AnalyticsEvent)).all()
    assert len(rows) == 2
    glossary = next(r for r in rows if r.event_type == "glossary_click")
    props = json.loads(glossary.properties_json)
    assert props.get("term_id") == "七杀"
    assert "name" not in props


def test_post_analytics_events_anonymous(client):
    resp = client.post(
        "/api/v1/analytics/events",
        json={
            "events": [
                {
                    "event_type": "landing_cta_click",
                    "session_id": "anon-1",
                    "properties": {"cta": "register"},
                }
            ]
        },
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["accepted"] == 1


def test_post_analytics_rejects_unknown_event_type(client):
    resp = client.post(
        "/api/v1/analytics/events",
        json={"events": [{"event_type": "not_a_real_event", "properties": {}}]},
    )
    assert resp.status_code == 422
