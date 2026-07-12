"""ChartSnapshot: compute bazi/ziwei once per chart input hash."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Any
from uuid import uuid4

from app.schemas import BaziFullRequest, BaziFullResponse
from app.schemas.ziwei import ZiweiRequest
from services.bazi_full_service import bazi_full
from services.ziwei_engine import ZiweiChart, ziwei_full

_bazi_cache: dict[str, BaziChartSnapshot] = {}
_ziwei_cache: dict[str, ZiweiChartSnapshot] = {}
_build_counts = {"bazi": 0, "ziwei": 0}


def reset_snapshot_cache_for_tests() -> None:
    _bazi_cache.clear()
    _ziwei_cache.clear()
    _build_counts["bazi"] = 0
    _build_counts["ziwei"] = 0


def get_build_counts() -> dict[str, int]:
    return dict(_build_counts)


def _stable_hash(payload: dict[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:32]


@dataclass
class BaziChartSnapshot:
    chart_hash: str
    request_id: str
    response: BaziFullResponse


@dataclass
class ZiweiChartSnapshot:
    chart_hash: str
    chart: ZiweiChart
    request: ZiweiRequest


def build_bazi_snapshot(
    request: BaziFullRequest,
    *,
    request_id: str | None = None,
) -> BaziChartSnapshot:
    key = _stable_hash(request.model_dump(mode="json"))
    cached = _bazi_cache.get(key)
    if cached is not None:
        return cached
    _build_counts["bazi"] += 1
    rid = request_id or str(uuid4())
    response = bazi_full(request, request_id=rid)
    snap = BaziChartSnapshot(chart_hash=key, request_id=rid, response=response)
    _bazi_cache[key] = snap
    return snap


def build_ziwei_snapshot(request: ZiweiRequest) -> ZiweiChartSnapshot:
    key = _stable_hash(request.model_dump(mode="json"))
    cached = _ziwei_cache.get(key)
    if cached is not None:
        return cached
    _build_counts["ziwei"] += 1
    chart = ziwei_full(
        request.year,
        request.month,
        request.day,
        request.hour,
        request.minute,
        request.gender or "男",
        youbi_method=request.youbi_method or "month",
        leap_month_method=request.leap_month_method or "mid",
        year_divide=request.year_divide or "lichun",
        day_divide=request.day_divide or "solar_next",
        late_zishi=request.late_zishi if request.late_zishi is not None else True,
        brightness_method=request.brightness_method or "standard",
        kuiyue_method=request.kuiyue_method or "standard",
        tianma_method=request.tianma_method or "year",
        liunian_year=request.liunian_year,
        longitude=request.longitude,
    )
    snap = ZiweiChartSnapshot(chart_hash=key, chart=chart, request=request)
    _ziwei_cache[key] = snap
    return snap
