from __future__ import annotations

import re
from uuid import uuid4

from fastapi import APIRouter, Header, Request

from app.schemas import BaziFullRequest, BaziFullResponse, WarningModel
from services.bazi_full_service import bazi_full
from services.rate_limit import limiter

router = APIRouter(prefix="/api/v1/bazi", tags=["bazi"])
# ✅ 0.14: /bazi/full 速率限制 20 req/min

_REQUEST_ID_PATTERN = re.compile(r"^[A-Za-z0-9._-]+$")


def _sanitize_request_id(candidate: str | None, warnings: list[WarningModel]) -> str:
    if candidate is None:
        return str(uuid4())
    rid = candidate.strip()
    if not rid:
        return str(uuid4())
    if not _REQUEST_ID_PATTERN.match(rid):
        warnings.append(WarningModel(code="request_id_invalid_chars", message="request id replaced with uuid"))
        return str(uuid4())
    if len(rid) > 128:
        warnings.append(WarningModel(code="request_id_truncated", message="request id truncated to 128 chars"))
        rid = rid[:128]
    return rid


@router.post("/full", response_model=BaziFullResponse)
@limiter.limit("20/minute")  # 0.14: /bazi/full 速率限制 20 req/min
def api_bazi_full(
    request: Request,
    payload: BaziFullRequest,
    x_request_id: str | None = Header(None, alias="X-Request-Id"),
):
    warnings: list[WarningModel] = []
    request_id = _sanitize_request_id(x_request_id, warnings)
    result = bazi_full(payload, request_id=request_id)
    if warnings:
        result.warnings.extend(warnings)
    return result
