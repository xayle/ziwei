"""API iztro_crosscheck 字段（/full 与 /demo?crosscheck=true）。"""

from __future__ import annotations

from unittest.mock import patch

import pytest


@pytest.fixture
def mock_iztro_compare():
    payload = {
        "status": "main_match",
        "main_match": 14,
        "main_total": 14,
        "life_palace_match": True,
        "iztro_life_palace_gz": "丁未",
        "advisory": None,
    }
    with patch(
        "routers.ziwei.compare_chart_to_iztro",
        return_value=payload,
    ) as mocked:
        yield mocked, payload


def test_full_includes_iztro_crosscheck(client, mock_iztro_compare):
    mocked, payload = mock_iztro_compare
    resp = client.post(
        "/api/v1/ziwei/full",
        json={
            "year": 2002,
            "month": 3,
            "day": 13,
            "hour": 14,
            "minute": 55,
            "gender": "女",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["iztro_crosscheck"] is not None
    assert data["iztro_crosscheck"]["status"] == payload["status"]
    assert data["iztro_crosscheck"]["main_match"] == 14
    mocked.assert_called_once()
    call_kw = mocked.call_args.kwargs
    assert call_kw["year"] == 2002
    assert call_kw["year_divide"] == "lichun"
    assert call_kw["day_divide"] == "solar_next"


def test_demo_crosscheck_optional(client, mock_iztro_compare):
    mocked, _payload = mock_iztro_compare
    resp = client.get("/api/v1/ziwei/demo?crosscheck=true")
    assert resp.status_code == 200
    assert resp.json()["iztro_crosscheck"] is not None
    mocked.assert_called_once()


def test_full_includes_iztro_dual_track(client, mock_iztro_compare):
    mocked, _payload = mock_iztro_compare
    dual_payload = {
        "status": "life_palace_mismatch",
        "main_match": 0,
        "main_total": 14,
        "life_palace_match": False,
        "engine_life_palace_gz": "乙丑",
        "iztro_life_palace_gz": "癸丑",
        "advisory": "ZW03 双轨",
        "dual_track": {
            "label": "iztro 对照轨",
            "year_divide": "normal",
            "day_divide": "forward",
            "life_palace_gz": "癸丑",
            "main_match": 0,
            "main_total": 14,
            "note": "边界",
        },
    }
    mocked.return_value = dual_payload
    resp = client.post(
        "/api/v1/ziwei/full",
        json={
            "year": 1988,
            "month": 2,
            "day": 4,
            "hour": 23,
            "minute": 45,
            "gender": "男",
        },
    )
    assert resp.status_code == 200
    cc = resp.json()["iztro_crosscheck"]
    assert cc["status"] == "life_palace_mismatch"
    assert cc["dual_track"]["life_palace_gz"] == "癸丑"
    assert cc["engine_life_palace_gz"] == "乙丑"


def test_demo_without_crosscheck(client, mock_iztro_compare):
    mocked, _payload = mock_iztro_compare
    resp = client.get("/api/v1/ziwei/demo")
    assert resp.status_code == 200
    assert resp.json().get("iztro_crosscheck") is None
    mocked.assert_not_called()
