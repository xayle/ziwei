"""P4: unified /verify path + BaziFullResponse.missing_fields."""

from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

import pytest
from fastapi.testclient import TestClient

import run as run_module

_CLIENT = TestClient(run_module.app)

_BASE = {
    "dt": "1990-07-17T08:30:00+08:00",
    "lon": 120.0,
    "mode": "dual",
    "solar_time_enabled": False,
    "tz": "Asia/Shanghai",
    "gender": "male",
    "city_tier": "一线",
    "industry": "金融IT",
}


class TestVerifyUnifiedPath:
    def test_verify_and_full_share_core_metrics(self):
        verify_resp = _CLIENT.post("/api/v1/verify", json=_BASE)
        assert verify_resp.status_code == 200, verify_resp.text
        full_resp = _CLIENT.post("/api/v1/bazi/full", json=_BASE)
        assert full_resp.status_code == 200, full_resp.text

        verify_data = verify_resp.json()
        full_data = full_resp.json()
        assert verify_data["pillars_primary"] == full_data["pillars_primary"]
        assert verify_data.get("yongshen") == full_data.get("yongshen")
        if verify_data.get("geju") and full_data.get("geju"):
            assert verify_data["geju"]["geju_name"] == full_data["geju"]["geju_name"]

    def test_verify_uses_calculate_not_legacy_wealth_formula(self):
        """Legacy formula (_favor_total * 1.8) diverges from calculate(); unified path must match calculate()."""
        from services.bazi_engine_service import calculate

        dt = datetime(1990, 7, 17, 8, 30, tzinfo=ZoneInfo("Asia/Shanghai"))
        calc = calculate(
            dt=dt,
            lon=120.0,
            tz="Asia/Shanghai",
            use_solar=False,
            mode="dual",
            gender="male",
            request_id="p4-test",
            city_tier="一线",
            industry="金融IT",
        )
        expected = calc.verify_response.wealth.wealth_score if calc.verify_response.wealth else None

        resp = _CLIENT.post("/api/v1/verify", json=_BASE)
        assert resp.status_code == 200
        actual = resp.json().get("wealth", {}).get("wealth_score")
        assert actual == expected


class TestBaziFullMissingFields:
    def test_bazi_full_response_includes_missing_fields(self):
        resp = _CLIENT.post("/api/v1/bazi/full", json=_BASE)
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert "missing_fields" in data
        assert isinstance(data["missing_fields"], list)
