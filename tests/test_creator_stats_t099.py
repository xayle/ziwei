"""T099 / BE-GTM-08：创作者统计 API（管理员 RBAC）。"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from services.auth_service import create_access_token
from app.models import User
from app.models.analytics_event import AnalyticsEvent
from services.creator_stats_service import build_creator_stats, _topic_key


def _admin_headers(admin_user: User) -> dict[str, str]:
    tok = create_access_token(
        user_id=admin_user.id,  # type: ignore[arg-type]
        username=admin_user.username,
        role=admin_user.role,
    )["access_token"]
    return {"Authorization": f"Bearer {tok}"}


def test_topic_key_organic_default():
    assert _topic_key(None, None, None) == "organic||"


def test_build_creator_stats_cohort(db_session, admin_user):
    now = datetime.now(UTC)
    u1 = User(
        username="douyin_reg",
        email="d1@example.com",
        password_hash="x",
        role="editor",
        entitlement="volume_pass",
        utm_source="douyin",
        utm_campaign="geju_hook",
        content_id="v_topic_1",
        created_at=now - timedelta(days=2),
        updated_at=now,
    )
    u2 = User(
        username="organic_reg",
        email="o1@example.com",
        password_hash="x",
        role="editor",
        entitlement="free",
        created_at=now - timedelta(days=1),
        updated_at=now,
    )
    db_session.add(u1)
    db_session.add(u2)
    db_session.add(
        AnalyticsEvent(
            event_type="landing_cta_click",
            session_id="s1",
            properties_json="{}",
            created_at=now - timedelta(hours=3),
        )
    )
    db_session.add(
        AnalyticsEvent(
            event_type="share_card_export",
            session_id="s2",
            properties_json="{}",
            created_at=now - timedelta(hours=1),
        )
    )
    db_session.commit()

    stats = build_creator_stats(db_session, window_days=30)
    assert stats.schema_version == "creator-stats@0.1"
    assert stats.totals.users >= 2
    assert stats.totals.attributed_users >= 1
    assert stats.totals.paid_users >= 1
    assert stats.totals.landing_cta_clicks >= 1
    assert stats.totals.share_card_exports >= 1

    topic = next(t for t in stats.topics if t.content_id == "v_topic_1")
    assert topic.utm_source == "douyin"
    assert topic.registrations >= 1
    assert topic.paid_conversions >= 1
    assert topic.conversion_rate > 0


def test_creator_stats_admin_only(client, admin_user, client_with_auth):
    # 普通用户 403
    denied = client_with_auth.get("/api/v1/creator/stats")
    assert denied.status_code == 403

    ok = client.get("/api/v1/creator/stats", headers=_admin_headers(admin_user), params={"window_days": 14})
    assert ok.status_code == 200, ok.text
    data = ok.json()
    assert data["schema_version"] == "creator-stats@0.1"
    assert data["window_days"] == 14
    assert "totals" in data
    assert "topics" in data
    assert "funnel" in data


def test_creator_stats_requires_auth_when_bypass_off(client, monkeypatch):
    monkeypatch.setenv("AUTH_BYPASS", "false")
    # 清掉可能残留的默认 Authorization（client_with_auth 会污染同实例）
    client.headers.pop("Authorization", None)
    resp = client.get("/api/v1/creator/stats")
    assert resp.status_code == 401
