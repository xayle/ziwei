from __future__ import annotations

from datetime import datetime

from app.schemas.bazi import BaziFullRequest
from services.bazi_full_service import bazi_full


def test_bazi_full_echoes_zi_day_rule_and_provenance():
    body = BaziFullRequest(
        dt=datetime(1990, 1, 15, 8, 30),
        lon=116.4,
        gender="male",
        zi_day_rule="early_zi_prev_day",
    )
    resp = bazi_full(body)
    assert resp.methods.zi_day_rule == "early_zi_prev_day"
    assert resp.raw.day_boundary_rule_used == "early_zi_prev_day"
    assert resp.provenance is not None
    assert resp.provenance.geju.note and "early_zi_prev_day" in resp.provenance.geju.note
    assert resp.provenance.pillars.confidence >= 0.5
