from __future__ import annotations

from datetime import datetime

from app.schemas.bazi import BaziFullRequest
from services.bazi_engine.classic_refs import shensha_candidates
from services.bazi_full_service import bazi_full


def test_shensha_candidates_returns_refs():
    refs = shensha_candidates("天乙贵人", limit=2)
    assert isinstance(refs, list)


def test_bazi_full_includes_classic_refs_and_shensha_refs():
    body = BaziFullRequest(
        dt=datetime(1990, 1, 15, 8, 30),
        lon=116.4,
        gender="male",
        zi_day_rule="early_zi_same_day",
    )
    resp = bazi_full(body)
    assert resp.classic_refs is not None
    if resp.shensha:
        assert any(getattr(s, "classic_refs", None) for s in resp.shensha)
