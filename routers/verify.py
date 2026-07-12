"""routers/verify.py — POST /api/v1/verify endpoint and supporting helpers.

Extracted from run.py (Batch B-1 refactor, 2026-05-25).
Test patches for symbols in this module use the path ``routers.verify.*``.
Backward-compat re-exports in run.py keep ``from run import ...`` and
``patch("run.verify_full")`` etc. working for any callers that already used
the old ``run`` namespace bindings.
"""

from __future__ import annotations

from datetime import datetime, timedelta
import json
import logging
import re
import time
from uuid import uuid4
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from fastapi import APIRouter, Header, HTTPException, Response
from fastapi.responses import JSONResponse
from starlette.requests import Request

from app.schemas import VerifyRequest
from constants import BAZI_VERIFY_YEAR_MAX, BAZI_VERIFY_YEAR_MIN
import services.bazi_engine_service as _bazi_engine_service
from services.bazi_full_service import patch_verify_liuri
from services.normalize_input import validate_lon_strict, warn_lon_cn_range
from services.prometheus_monitoring import record_verify_metrics
from services.rate_limit import limiter

logger = logging.getLogger(__name__)
router = APIRouter()


# ── 自定义 JSONResponse（中文不转义）─────────────────────────────────────────


class UnescapedJSONResponse(JSONResponse):
    """JSONResponse that keeps Chinese characters unescaped."""

    def render(self, content):
        return json.dumps(
            content,
            ensure_ascii=False,
            allow_nan=False,
            indent=None,
            separators=(",", ":"),
        ).encode("utf-8")


# ── 辅助函数 ──────────────────────────────────────────────────────────────────


def _attach_tz(dt: datetime, tz_name: str) -> datetime:
    tz = ZoneInfo(tz_name)
    if dt.tzinfo is None or dt.utcoffset() is None:
        return dt.replace(tzinfo=tz)
    return dt.astimezone(tz)


def _format_offset(td: timedelta) -> str:
    seconds = int(td.total_seconds())
    sign = "+" if seconds >= 0 else "-"
    seconds = abs(seconds)
    hours, remainder = divmod(seconds, 3600)
    minutes = remainder // 60
    return f"{sign}{hours:02d}:{minutes:02d}"


def _safe_offset(td: timedelta | None) -> str:
    if td is None:
        return ""
    return _format_offset(td)


_REQUEST_ID_PATTERN = re.compile(r"^[A-Za-z0-9._-]+$")


def _sanitize_request_id(candidate: str | None, warnings: list[str]) -> str:
    if candidate is None:
        return str(uuid4())
    rid = candidate.strip()
    if not rid:
        return str(uuid4())
    if not _REQUEST_ID_PATTERN.match(rid):
        warnings.append("request_id_invalid_chars: action=replaced_with_uuid")
        return str(uuid4())
    if len(rid) > 128:
        warnings.append("request_id_truncated: max_len=128")
        rid = rid[:128]
    return rid


def _validate_tz(tz_name: str) -> None:
    """校验 IANA 时区字符串，无效时抛出 HTTPException 400 (0.17)"""
    try:
        ZoneInfo(tz_name)
    except (ZoneInfoNotFoundError, KeyError):
        raise HTTPException(status_code=400, detail=f"Invalid timezone: {tz_name!r}")


def _build_verify_http_response(body, dt, lon, req_id, warnings, verify_start: float):
    """Unified verify path: always delegate to bazi_engine_service.calculate()."""
    try:
        _calc = _bazi_engine_service.calculate(
            dt=dt,
            lon=lon,
            tz=body.tz,
            use_solar=body.solar_time_enabled,
            mode=body.mode,
            gender=getattr(body, "gender", None),
            request_id=req_id,
            extra_warnings=warnings,
            city_tier=getattr(body, "city_tier", None),
            industry=getattr(body, "industry", None),
        )
    except HTTPException:
        raise
    except ValueError as exc:
        record_verify_metrics(
            mode=body.mode, boundary_level="", duration_secs=time.time() - verify_start, success=False
        )
        logger.warning("Verify validation error", extra={"request_id": req_id, "error": str(exc)})
        raise HTTPException(status_code=400, detail="Invalid input parameters")
    except Exception as exc:
        record_verify_metrics(
            mode=body.mode, boundary_level="", duration_secs=time.time() - verify_start, success=False
        )
        logger.exception(
            "Unexpected error in verify",
            extra={"request_id": req_id, "error_type": type(exc).__name__},
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail="Internal server error")

    response_data = _calc.verify_response.model_dump(mode="json")
    # 缓存命中时 request_id 可能来自旧请求，用当前 req_id 覆盖以保证 header 与 body 一致
    response_data["request_id"] = req_id
    # 缓存命中时 extra_warnings（request_id_invalid_chars 等）未写入缓存结果，补充合并
    if warnings:
        _val = response_data.get("validation") or {}
        _existing_warns = _val.get("warnings") or []
        _extra_warns = [{"code": "legacy", "message": str(w)} for w in warnings]
        _val["warnings"] = _existing_warns + _extra_warns
        response_data["validation"] = _val
    boundary_level = (
        response_data.get("validation", {}).get("level", "")
        if isinstance(response_data.get("validation"), dict)
        else ""
    )
    record_verify_metrics(
        mode=body.mode, boundary_level=boundary_level, duration_secs=time.time() - verify_start, success=True
    )
    response_data = patch_verify_liuri(response_data, _calc.verify_response, body, dt, body.tz)
    return UnescapedJSONResponse(
        content=response_data,
        headers={"X-Request-Id": req_id},
    )


def _build_legacy_verify_response(body, dt, lon, req_id, warnings):
    """Deprecated wrapper kept for run.py re-export and legacy coverage tests.

    Production /api/v1/verify always routes through calculate(); this helper
    delegates to the same path so callers no longer hit divergent wealth/dayun logic.
    """
    _calc = _bazi_engine_service.calculate(
        dt=dt,
        lon=lon,
        tz=body.tz,
        use_solar=body.solar_time_enabled,
        mode=body.mode,
        gender=getattr(body, "gender", None),
        request_id=req_id,
        extra_warnings=warnings,
        city_tier=getattr(body, "city_tier", None),
        industry=getattr(body, "industry", None),
    )
    validation = _calc.verify_response.validation
    boundary_level = validation.level if validation is not None and hasattr(validation, "level") else ""
    return _calc.verify_response, boundary_level


# ── /api/v1/verify 端点 ───────────────────────────────────────────────────────


@router.post("/api/v1/verify")
@limiter.limit("30/minute")  # 0.14: /verify 速率限制 30 req/min
def api_verify(
    request: Request,
    body: VerifyRequest,
    response: Response,
    x_request_id: str | None = Header(None, alias="X-Request-Id"),
):
    warnings: list[str] = []
    req_id = _sanitize_request_id(x_request_id, warnings)
    response.headers["X-Request-Id"] = req_id
    _verify_start = time.time()  # M6.08: Prometheus 计时起点

    # 0.17: 校验时区字符串
    _validate_tz(body.tz)

    # 0.16: 校验年份范围（含 CLS pre_1900 古典命例）
    if not (BAZI_VERIFY_YEAR_MIN <= body.dt.year <= BAZI_VERIFY_YEAR_MAX):
        raise HTTPException(
            status_code=400,
            detail=f"dt.year {body.dt.year} 超出支持范围 [{BAZI_VERIFY_YEAR_MIN}, {BAZI_VERIFY_YEAR_MAX}]",
        )

    if body.dt.tzinfo is not None and body.dt.utcoffset() is not None:
        target_tz = ZoneInfo(body.tz)
        target_offset = target_tz.utcoffset(body.dt)
        dt_offset = body.dt.utcoffset()
        if target_offset is not None and target_offset != dt_offset:
            offset_str = _safe_offset(dt_offset)
            warnings.append(f"tz_mismatch: dt_offset={offset_str} tz={body.tz} action=tz_ignored_for_aware_dt")

    dt = _attach_tz(body.dt, body.tz)
    lon = validate_lon_strict(body.lon)

    # soft warning for CN range when tz=Asia/Shanghai
    for w in warn_lon_cn_range(body.tz, lon):
        warnings.append(str(w))

    try:
        return _build_verify_http_response(body, dt, lon, req_id, warnings, _verify_start)
    except HTTPException:
        record_verify_metrics(
            mode=body.mode, boundary_level="", duration_secs=time.time() - _verify_start, success=False
        )
        raise
