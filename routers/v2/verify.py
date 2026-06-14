"""routers/v2/verify.py — API v2 /verify 端点.

设计要点：
- ENGINE_V2=false 时立即返回 501 Not Implemented（满足红线 R40）
- output_format='minimal' 时只返回 5 个核心字段（节省计算+带宽）
- 响应外层携带 meta（api_version / engine_version / calc_ms，满足 R38）
- 不导入 run.py，所有依赖直接来自 services/ 层
"""

from __future__ import annotations

import datetime as _dt
import logging
import uuid
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from fastapi import APIRouter, Header, HTTPException, Response
from starlette.requests import Request

from app.schemas.v2.verify import (
    ResponseMeta,
    VerifyRequestV2,
    VerifyResponseFull,
    VerifyResponseMinimal,
    VerifyResponseV2,
)
import services.bazi_engine_service as _bazi_engine_service
from services.normalize_input import validate_lon_strict
from services.prometheus_monitoring import record_verify_metrics
from services.rate_limit import limiter

logger = logging.getLogger(__name__)

router = APIRouter()

_ENGINE_VERSION = "v8.0"  # 与 static/sw.js CACHE_VERSION 对应


# ─── 工具函数 ─────────────────────────────────────────────────────────────────


def _validate_tz(tz_name: str) -> None:
    """校验 IANA 时区字符串，无效时抛 400."""
    try:
        ZoneInfo(tz_name)
    except (ZoneInfoNotFoundError, KeyError):
        raise HTTPException(status_code=400, detail=f"Invalid timezone: {tz_name!r}")


def _attach_tz(dt: _dt.datetime, tz_name: str) -> _dt.datetime:
    """为 naive datetime 附加时区；aware datetime 转换到目标时区."""
    tz = ZoneInfo(tz_name)
    if dt.tzinfo is None or dt.utcoffset() is None:
        return dt.replace(tzinfo=tz)
    return dt.astimezone(tz)


def _find_current_dayun(dayun_model) -> dict | None:
    """从 DaYunModel 中找出当前年份所在大运，返回序列化 dict."""
    if not dayun_model or not dayun_model.items:
        return None
    cur_year = _dt.datetime.now().year
    for item in dayun_model.items:
        start = item.start_year or 0
        if start <= cur_year < start + 10:
            return item.model_dump(mode="json")
    # 兜底：返回第一条
    return dayun_model.items[0].model_dump(mode="json")


# ─── 端点 ─────────────────────────────────────────────────────────────────────


@router.post(
    "/verify",
    summary="八字排盘 v2",
    description=(
        "API v2 主排盘端点。\n\n"
        "- `ENGINE_V2=false` 时返回 **501 Not Implemented**（R40）\n"
        "- `output_format=minimal` 时仅返回 geju/yongshen/dayun_current/wuxing_score/score\n"
        "- 响应包含 `meta`（api_version / engine_version / calc_ms，R38）"
    ),
    response_model=VerifyResponseV2,
    tags=["v2"],
)
@limiter.limit("30/minute")
def v2_verify(
    request: Request,
    body: VerifyRequestV2,
    response: Response,
    x_request_id: str | None = Header(None, alias="X-Request-Id"),
) -> VerifyResponseV2:
    # ── R40: ENGINE_V2 开关检查 ───────────────────────────────────────────────
    if not _bazi_engine_service._engine_v2_enabled():
        raise HTTPException(
            status_code=501,
            detail="v2 engine not enabled (set ENGINE_V2=true to activate)",
        )

    # ── 请求准备 ──────────────────────────────────────────────────────────────
    import time

    _start = time.time()

    req_id = (x_request_id or uuid.uuid4().hex)[:128]
    response.headers["X-Request-Id"] = req_id

    _validate_tz(body.tz)
    if not (1900 <= body.dt.year <= 2100):
        raise HTTPException(
            status_code=400,
            detail=f"dt.year {body.dt.year} 超出支持范围 [1900, 2100]",
        )

    dt = _attach_tz(body.dt, body.tz)
    lon = validate_lon_strict(body.lon)

    # ── 调用引擎 ──────────────────────────────────────────────────────────────
    try:
        calc = _bazi_engine_service.calculate(
            dt=dt,
            lon=lon,
            tz=body.tz,
            use_solar=body.solar_time_enabled,
            mode=body.mode,
            gender=getattr(body, "gender", None),
            request_id=req_id,
            extra_warnings=[],
            city_tier=getattr(body, "city_tier", None),
            industry=getattr(body, "industry", None),
        )
    except HTTPException:
        raise
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception:
        logger.exception("v2 verify unexpected error", extra={"request_id": req_id})
        raise HTTPException(status_code=500, detail="Internal server error")

    calc_ms = round((time.time() - _start) * 1000, 2)

    # ── 构建 meta（R38）─────────────────────────────────────────────────────────
    meta = ResponseMeta(
        api_version="v2.0",
        engine_version=_ENGINE_VERSION,
        calc_ms=calc_ms,
    )

    # ── 构建 data（full / minimal）────────────────────────────────────────────
    vr = calc.verify_response

    # Prometheus 自定义业务指标
    try:
        _boundary_level = getattr(getattr(vr, "validation", None), "level", "") or "unknown"
        record_verify_metrics(
            mode=body.mode,
            boundary_level=_boundary_level,
            duration_secs=calc_ms / 1000.0,
            success=True,
        )
    except Exception:
        logger.debug("[metrics] record_verify_metrics skipped", exc_info=True)

    if body.output_format == "minimal":
        data: VerifyResponseFull | VerifyResponseMinimal = VerifyResponseMinimal(  # type: ignore[call-overload]
            geju=vr.geju,
            yongshen=vr.yongshen,
            dayun_current=_find_current_dayun(vr.dayun),
            wuxing_score=vr.wuxing_score,
            score=vr.day_master_strength.score if vr.day_master_strength else None,
        )
    else:
        full_dict = vr.model_dump(mode="json")
        data = VerifyResponseFull(**full_dict)

    return VerifyResponseV2(meta=meta, data=data)
