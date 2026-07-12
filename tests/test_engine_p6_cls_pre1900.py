"""P6: CLS pre_1900 HTTP verify path + extended year range."""

from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

import run as run_module
from constants import BAZI_VERIFY_YEAR_MIN

_CLIENT = TestClient(run_module.app)
_GT_PATH = Path(__file__).parent.parent / "data" / "ground_truth_cases.json"


def _cls01_payload() -> dict:
    case = next(c for c in json.loads(_GT_PATH.read_text(encoding="utf-8"))["cases"] if c["id"] == "CLS01")
    return {
        "dt": case["birth_dt_solar"] + "+08:00",
        "lon": case["longitude"],
        "mode": "single",
        "solar_time_enabled": False,
        "tz": "Asia/Shanghai",
        "gender": case["gender"],
    }


class TestPre1900VerifyHttp:
    def test_verify_accepts_cls01_birth_year(self):
        resp = _CLIENT.post("/api/v1/verify", json=_cls01_payload())
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["pillars_primary"]["day"]["ganzhi"] == "己酉"
        assert data.get("geju", {}).get("geju_name") == case_engine_geju("CLS01")
        assert "geju" not in (data.get("missing_fields") or [])

    def test_verify_rejects_year_before_historical_min(self):
        payload = _cls01_payload()
        payload["dt"] = "1699-01-01T12:00:00+08:00"
        resp = _CLIENT.post("/api/v1/verify", json=payload)
        assert resp.status_code == 400
        assert str(BAZI_VERIFY_YEAR_MIN) in resp.json()["detail"]


def case_engine_geju(case_id: str) -> str:
    cases = json.loads(_GT_PATH.read_text(encoding="utf-8"))["cases"]
    case = next(c for c in cases if c["id"] == case_id)
    return case["engine_geju"]
