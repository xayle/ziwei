"""Bazi full disclaimer_block field."""

from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from app.schemas import BaziFullRequest
from services.bazi_full_service import bazi_full


def test_bazi_full_includes_disclaimer_block():
    req = BaziFullRequest(
        dt=datetime(1990, 5, 15, 10, 30, tzinfo=ZoneInfo("Asia/Shanghai")),
        lon=116.4,
        mode="single",
        gender="male",
    )
    resp = bazi_full(req, request_id="disclaimer-test")
    assert resp.disclaimer_block is not None
    assert resp.disclaimer_block.text
    assert resp.disclaimer_block.version
