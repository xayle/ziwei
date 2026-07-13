"""T088 · BE-GTM-02 utm attribution (register + case)."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.schemas.utm import UtmAttributionFields
from routers.auth import RegisterRequest


def test_utm_fields_normalize_blank():
    fields = UtmAttributionFields(utm_source="  douyin  ", utm_campaign=" ", content_id="")
    assert fields.utm_source == "douyin"
    assert fields.utm_campaign is None
    assert fields.content_id is None


def test_utm_content_id_max_len():
    with pytest.raises(ValidationError):
        UtmAttributionFields(content_id="x" * 65)


def test_register_persists_utm(client, db_session):
    resp = client.post(
        "/api/v1/auth/register",
        json={
            "username": "utm_user_t088",
            "email": "utm_t088@example.com",
            "password": "Pass1234ab",
            "utm_source": "douyin",
            "utm_campaign": "geju_hook",
            "content_id": "video_7123456789",
        },
    )
    assert resp.status_code == 200, resp.text
    token = resp.json()["access_token"]
    me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    data = me.json()
    assert data["utm_source"] == "douyin"
    assert data["utm_campaign"] == "geju_hook"
    assert data["content_id"] == "video_7123456789"


def test_create_case_with_utm(client_with_auth, test_user, db_session):
    test_user.utm_source = "organic"
    test_user.utm_campaign = "home"
    test_user.content_id = None
    db_session.add(test_user)
    db_session.commit()

    resp = client_with_auth.post(
        "/api/v1/cases",
        json={
            "name": "UTM Case",
            "gender": "male",
            "birth_dt_local": "1990-01-15T08:00:00",
            "tz": "Asia/Shanghai",
            "lon": 121.47,
            "city": "Shanghai",
            "utm_source": "douyin",
            "utm_campaign": "vol1_teaser",
            "content_id": "v_abc",
        },
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["utm_source"] == "douyin"
    assert body["utm_campaign"] == "vol1_teaser"
    assert body["content_id"] == "v_abc"


def test_create_case_inherits_user_utm(client_with_auth, test_user, db_session):
    test_user.utm_source = "douyin"
    test_user.utm_campaign = "from_register"
    test_user.content_id = "vid_inherit"
    db_session.add(test_user)
    db_session.commit()
    db_session.refresh(test_user)

    resp = client_with_auth.post(
        "/api/v1/cases",
        json={
            "name": "Inherit UTM",
            "gender": "female",
            "birth_dt_local": "1992-06-01T12:00:00",
            "tz": "Asia/Shanghai",
            "lon": 116.4,
            "city": "Beijing",
        },
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["utm_source"] == "douyin"
    assert body["utm_campaign"] == "from_register"
    assert body["content_id"] == "vid_inherit"


def test_register_request_accepts_utm():
    body = RegisterRequest(
        username="abc_user",
        email="abc@example.com",
        password="Pass1234",
        utm_source="douyin",
        content_id="1",
    )
    assert body.utm_source == "douyin"
    assert body.content_id == "1"
