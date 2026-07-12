"""六爻周易 API Router"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.schemas.liuyao import LiuyaoCastResponse, LiuyaoTimeRequest
from services.liuyao_engine import cast_by_time, cast_coins, get_gua_info

router = APIRouter(prefix="/api/v1/liuyao", tags=["liuyao"])


@router.post("/cast/coins", response_model=LiuyaoCastResponse)
async def cast_with_coins():
    """铜钱起卦 — 随机六爻"""
    try:
        result = cast_coins()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cast/time", response_model=LiuyaoCastResponse)
async def cast_with_time(body: LiuyaoTimeRequest):
    """时间起卦 — 年月日时"""
    try:
        result = cast_by_time(body.year, body.month, body.day, body.hour)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/gua/{gua_name}")
async def get_gua(gua_name: str):
    """查询卦信息"""
    try:
        return get_gua_info(gua_name)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))
