"""P3 follow-ups: liuri API, flow defaults, structured analysis."""

from __future__ import annotations

import datetime

import pytest

from app.schemas.bazi import LiuriLiushiRequest
from services.bazi_full_service import compute_liuri_liushi
from services.ziwei_engine.flow_defaults import resolve_flow_params


GOLDEN = {
    "year": 2002,
    "month": 3,
    "day": 13,
    "hour": 14,
    "minute": 55,
    "gender": "女",
}


class TestFlowDefaults:
    def test_standard_includes_flow_by_default(self):
        day, month, hour = resolve_flow_params(
            template_version="standard",
            include_flow_liuri=None,
            liunian_year=2026,
            birth_year=2002,
            birth_month=3,
            birth_day=13,
            birth_hour=14,
            birth_minute=55,
            leap_month_method="mid",
            flow_lunar_day=None,
            flow_liuyue_month=None,
            flow_hour_branch=None,
        )
        assert day is not None and 1 <= day <= 30
        assert month is not None and 1 <= month <= 12
        assert hour is not None and 0 <= hour <= 11

    def test_simple_skips_flow_by_default(self):
        day, month, hour = resolve_flow_params(
            template_version="simple",
            include_flow_liuri=None,
            liunian_year=2026,
            birth_year=2002,
            birth_month=3,
            birth_day=13,
            birth_hour=14,
            birth_minute=55,
            leap_month_method="mid",
            flow_lunar_day=None,
            flow_liuyue_month=None,
            flow_hour_branch=None,
        )
        assert day is None and month is None

    def test_explicit_flow_preserved(self):
        day, month, hour = resolve_flow_params(
            template_version="simple",
            include_flow_liuri=False,
            liunian_year=2026,
            birth_year=2002,
            birth_month=3,
            birth_day=13,
            birth_hour=14,
            birth_minute=55,
            leap_month_method="mid",
            flow_lunar_day=5,
            flow_liuyue_month=2,
            flow_hour_branch=3,
        )
        assert (day, month, hour) == (5, 2, 3)


class TestBaziLiuriEndpoint:
    def test_standalone_liuri(self):
        body = LiuriLiushiRequest(
            dt=datetime.datetime(2002, 3, 13, 14, 55),
            lon=116.4,
            gender="female",
            target_date=datetime.datetime(1900, 1, 1, 12, 0),
            target_hour=14,
        )
        resp = compute_liuri_liushi(body, request_id="test-req")
        assert resp.liuri_liushi.day_ganzhi == "甲戌"
        assert resp.liuri_liushi.flow_score is not None
        assert resp.dayun_transition is not None


class TestZiweiFollowupsApi:
    def test_standard_has_liuri_by_default(self, client):
        r = client.post("/api/v1/ziwei/full", json={**GOLDEN, "template_version": "standard"})
        assert r.status_code == 200
        assert r.json().get("liuri_liushi") is not None

    def test_simple_no_liuri_by_default(self, client):
        r = client.post("/api/v1/ziwei/full", json={**GOLDEN, "template_version": "simple"})
        assert r.status_code == 200
        assert r.json().get("liuri_liushi") is None

    def test_analysis_structured(self, client):
        r = client.post("/api/v1/ziwei/full", json={**GOLDEN, "template_version": "standard"})
        assert r.status_code == 200
        structured = r.json().get("analysis_structured") or []
        assert len(structured) == 12
        assert structured[0]["conclusion"]
        assert structured[0]["palace_name"]

    def test_bazi_liuri_endpoint(self, client):
        r = client.post(
            "/api/v1/bazi/liuri-liushi",
            json={
                "dt": "2002-03-13T14:55:00",
                "lon": 116.4,
                "gender": "female",
                "target_date": "1900-01-01T12:00:00",
                "target_hour": 14,
            },
        )
        assert r.status_code == 200
        data = r.json()
        assert data["liuri_liushi"]["day_ganzhi"] == "甲戌"

    def test_bazi_full_liuri_default_on(self, client):
        r = client.post(
            "/api/v1/bazi/full",
            json={
                "dt": "2002-03-13T14:55:00",
                "lon": 116.4,
                "mode": "single",
                "gender": "female",
                "include_liuri": True,
            },
        )
        assert r.status_code == 200
        assert r.json().get("liuri_liushi") is not None

    def test_verify_liuri_opt_in(self, client):
        r = client.post(
            "/api/v1/verify",
            json={
                "dt": "2002-03-13T14:55:00",
                "lon": 116.4,
                "mode": "single",
                "gender": "female",
                "include_liuri": True,
                "target_date": "1900-01-01T12:00:00",
            },
        )
        assert r.status_code == 200
        data = r.json()
        assert data.get("liuri_liushi") is not None
        assert data["liuri_liushi"]["day_ganzhi"] == "甲戌"
