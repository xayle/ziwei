"""Tests for services.bazi_engine.pillars — ENGINE_V2 四柱层."""

from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from services.bazi_engine.pillars import PILLARS_LAYER, VerifyOutput, compute_pillars


def _dt(y: int, m: int, d: int, h: int, mi: int = 0) -> datetime:
    return datetime(y, m, d, h, mi, tzinfo=ZoneInfo("Asia/Shanghai"))


class TestComputePillars:
    def test_returns_verify_output_with_layer_tag(self):
        out = compute_pillars(_dt(1990, 5, 15, 10), lon=116.4, use_solar=False, mode="single")
        assert isinstance(out, VerifyOutput)
        assert out.pillars_layer == PILLARS_LAYER
        assert out.pillars_primary.year.ganzhi
        assert out.pillars_primary.month.ganzhi
        assert out.pillars_primary.day.ganzhi
        assert out.pillars_primary.hour.ganzhi

    def test_v1_shim_matches_v2_layer(self):
        from app.core.verify import verify_full

        dt = _dt(2002, 3, 13, 14, 55)
        lon = 120.0
        v1 = verify_full(dt, lon=lon, use_solar=False, mode="dual")
        v2 = compute_pillars(dt, lon=lon, use_solar=False, mode="dual")
        assert v1.pillars_primary.day.ganzhi == v2.pillars_primary.day.ganzhi
        assert v1.pillars_primary.hour.ganzhi == v2.pillars_primary.hour.ganzhi
        assert v1.mode_effective == v2.mode_effective

    def test_engine_v2_calculate_uses_pillars_layer(self):
        from unittest.mock import patch

        import services.bazi_engine_service as svc
        from services.bazi_engine.pillars import PILLARS_LAYER
        from services.bazi_engine_service import calculate

        with patch.object(svc.settings, "engine_v2", True):
            result = calculate(
                _dt(1990, 1, 1, 12),
                lon=116.4,
                tz="Asia/Shanghai",
                use_solar=False,
                mode="single",
                gender="男",
                request_id="pillars-test",
            )
        assert result.engine_version == "v2"
        assert result.pillars_layer == PILLARS_LAYER
        assert result.verify_response.pillars_primary.day.ganzhi
