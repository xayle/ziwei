"""P5: M2 enrich + liunian failures surface missing_fields and warnings."""

from __future__ import annotations

from datetime import datetime
from unittest.mock import MagicMock, patch
from zoneinfo import ZoneInfo

import pytest
from fastapi.testclient import TestClient

import run as run_module
from app.schemas import (
    BackendInfo,
    DaYunModel,
    DayMasterStrengthModel,
    PillarsModel,
    RiskFlagsModel,
    ValidationModel,
    VerifyResponse,
    WarningModel,
    WuXingScoreModel,
    YongShenModel,
)
from app.schemas.bazi import DaYunItemModel, PillarModel
from services.bazi_engine_service import _enrich_v2_analysis, calculate

_CLIENT = TestClient(run_module.app)

_BASE = {
    "dt": "1990-07-17T08:30:00+08:00",
    "lon": 120.0,
    "mode": "dual",
    "solar_time_enabled": False,
    "tz": "Asia/Shanghai",
    "gender": "male",
}


def _pillar(stem: str, branch: str) -> PillarModel:
    return PillarModel(stem=stem, branch=branch, ganzhi=f"{stem}{branch}")


def _minimal_verify_response() -> VerifyResponse:
    return VerifyResponse(
        api_version="test",
        rule_version="test",
        request_id="p5-test",
        backend=BackendInfo(primary="sxtwl", sxtwl_available=True, cnlunar_available=True),
        mode_requested="single",
        mode_effective="single",
        pillars_primary=PillarsModel(
            year=_pillar("甲", "子"),
            month=_pillar("丙", "寅"),
            day=_pillar("甲", "午"),
            hour=_pillar("壬", "申"),
        ),
        risk_flags=RiskFlagsModel(
            near_shichen_boundary=False,
            near_jieqi_boundary=False,
            jieqi_boundary_status="ok",
        ),
        validation=ValidationModel(
            level="L0",
            mode="single",
            recommended="beijing_time",
            interpretation_enabled=True,
            reasons=[],
            diff_fields=[],
            risk_flags=RiskFlagsModel(
                near_shichen_boundary=False,
                near_jieqi_boundary=False,
                jieqi_boundary_status="ok",
            ),
            boundary_risk_shichen=False,
            boundary_risk_jieqi=False,
            warnings=[],
        ),
        solar_time_offset_minutes=0.0,
        dt_input="1990-05-15T08:00:00+08:00",
        dt_effective_utc8="1990-05-15T08:00:00+08:00",
        tz="Asia/Shanghai",
        wuxing_score=WuXingScoreModel(wood=20, fire=10, earth=15, metal=30, water=25),
        day_master_strength=DayMasterStrengthModel(score=55.0, tier="中和"),
        yongshen=YongShenModel(favor=["water"], avoid=["fire"], rationale="test"),
        dayun=DaYunModel(
            items=[DaYunItemModel(stem="庚", branch="申", start_age=30, flow_wuxing="metal")],
            start_age=3,
            start_age_months=36,
        ),
    )


class TestEnrichMissingFields:
    def test_geju_failure_marks_missing_field(self):
        verify_response = _minimal_verify_response()
        with patch("services.bazi_engine.geju.compute_geju", side_effect=RuntimeError("geju boom")):
            _enrich_v2_analysis(
                verify_response=verify_response,
                rp=verify_response.pillars_primary,
                yongshen=verify_response.yongshen,
                strength=verify_response.day_master_strength,
                wuxing_score=verify_response.wuxing_score,
                dayun_model=verify_response.dayun,
                dt=datetime(1990, 5, 15, 8, 0, tzinfo=ZoneInfo("Asia/Shanghai")),
                gender="male",
                mode="single",
            )
        assert "geju" in verify_response.missing_fields
        codes = [w.code for w in verify_response.validation.warnings]
        assert "M2_GEJU_FAIL" in codes

    def test_wealth_engine_failure_marks_missing_field(self):
        verify_response = _minimal_verify_response()
        with patch("services.bazi_engine.analysis.wealth.compute_wealth", side_effect=RuntimeError("wealth fail")):
            _enrich_v2_analysis(
                verify_response=verify_response,
                rp=verify_response.pillars_primary,
                yongshen=verify_response.yongshen,
                strength=verify_response.day_master_strength,
                wuxing_score=verify_response.wuxing_score,
                dayun_model=verify_response.dayun,
                dt=datetime(1990, 5, 15, 8, 0, tzinfo=ZoneInfo("Asia/Shanghai")),
                gender="male",
                mode="single",
            )
        assert "wealth_analysis" in verify_response.missing_fields
        assert any(w.code == "M2_WEALTH_FAIL" for w in verify_response.validation.warnings)

    def test_calculate_outer_enrich_failure_marks_batch_missing(self):
        dt = datetime(1990, 7, 17, 8, 30, tzinfo=ZoneInfo("Asia/Shanghai"))
        from services.bazi_engine_service import _RESULT_CACHE

        _RESULT_CACHE.clear()
        with patch("services.bazi_engine_service._enrich_v2_analysis", side_effect=RuntimeError("total fail")):
            result = calculate(
                dt=dt,
                lon=120.0,
                tz="Asia/Shanghai",
                use_solar=False,
                mode="dual",
                gender="male",
                request_id="p5-outer",
            )
        missing = result.verify_response.missing_fields
        assert "geju" in missing
        assert "wealth_analysis" in missing
        assert any(w.code == "M2_ENRICH_FAIL" for w in result.verify_response.validation.warnings)


class TestBaziFullLiunianFailure:
    def test_build_liunian_failure_surfaces_missing_fields(self):
        from app.schemas import BaziFullRequest
        from services.bazi_full_service import bazi_full

        body = BaziFullRequest.model_validate(_BASE)
        with patch("services.bazi_full_service.build_liunian", side_effect=RuntimeError("liunian fail")):
            resp = bazi_full(body, request_id="p5-liunian")
        assert "liunian" in resp.missing_fields
        assert resp.validation is not None
        assert any(w.code == "LIUNIAN_BUILD_FAIL" for w in resp.validation.warnings)

    def test_verify_response_includes_enrich_missing_fields(self):
        resp = _CLIENT.post("/api/v1/verify", json=_BASE)
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert "missing_fields" in data
        assert isinstance(data["missing_fields"], list)
