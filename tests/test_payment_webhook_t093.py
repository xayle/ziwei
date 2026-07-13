"""T093 · BE-GTM-06 payment webhook → entitlement."""

from __future__ import annotations

from services.payment_entitlement_service import plan_to_entitlement


def test_plan_to_entitlement_aliases():
    assert plan_to_entitlement("volume_pass") == "volume_pass"
    assert plan_to_entitlement("pass") == "volume_pass"
    assert plan_to_entitlement("pro") == "full_book"
    assert plan_to_entitlement("full_book") == "full_book"
    assert plan_to_entitlement("free") == "free"


def test_payment_webhook_writes_entitlement(client, db_session, test_user):
    # owner 角色运行时升至 full_book；仍应持久化字段
    test_user.role = "editor"
    test_user.is_admin = False
    test_user.entitlement = "free"
    db_session.add(test_user)
    db_session.commit()
    db_session.refresh(test_user)

    resp = client.post(
        "/api/v1/payment/webhook",
        json={
            "provider": "stripe",
            "event_type": "checkout.completed",
            "user_id": test_user.id,
            "plan": "volume_pass",
        },
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["accepted"] is True
    assert data["entitlement_applied"] == "volume_pass"
    assert data["sandbox"] is True
    assert data["user_id"] == test_user.id

    db_session.refresh(test_user)
    assert test_user.entitlement == "volume_pass"


def test_payment_webhook_full_book_via_pro_alias(client, db_session, test_user):
    test_user.role = "editor"
    test_user.entitlement = "free"
    db_session.add(test_user)
    db_session.commit()

    resp = client.post(
        "/api/v1/payment/webhook",
        json={
            "event_type": "payment.success",
            "user_id": test_user.id,
            "plan": "pro",
        },
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["entitlement_applied"] == "full_book"
    db_session.refresh(test_user)
    assert test_user.entitlement == "full_book"


def test_payment_webhook_requires_user_id(client):
    resp = client.post(
        "/api/v1/payment/webhook",
        json={"event_type": "checkout.completed", "plan": "volume_pass"},
    )
    assert resp.status_code == 400


def test_payment_webhook_unknown_user(client):
    resp = client.post(
        "/api/v1/payment/webhook",
        json={"event_type": "checkout.completed", "user_id": 999999, "plan": "volume_pass"},
    )
    assert resp.status_code == 404


def test_payment_webhook_bad_event(client, test_user):
    resp = client.post(
        "/api/v1/payment/webhook",
        json={"event_type": "invoice.voided", "user_id": test_user.id, "plan": "volume_pass"},
    )
    assert resp.status_code == 400
