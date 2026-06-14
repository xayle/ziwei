"""
routers/fengshui.py — §15 风水方位助手端点

端点：
    GET  /api/v1/fengshui/bagua          — 八宅命卦计算与方位推荐
    GET  /api/v1/fengshui/options        — 返回前端所需的可选项（朝向列表等）
    POST /api/v1/fengshui/room-layout    — 九宫格房间布局评估（v8.8.0）
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, Query, status

from app.schemas.fengshui import (
    BaguaResponse,
    DirectionItemResponse,
    FurnitureTipResponse,
    RoomLayoutRequest,
    RoomLayoutResponse,
    ZoneAssessmentResponse,
)
from services.fengshui_engine.bagua import (
    DIRECTIONS_ZH,
    HOUSE_FACING_OPTIONS,
    calc_bagua,
)
from services.fengshui_engine.room_layout import (
    ROOM_TYPE_ZH,
    assess_room_layout,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/fengshui",
    tags=["风水方位助手"],
)

_VALID_GENDERS = {"男", "女"}
_VALID_FACINGS = set(HOUSE_FACING_OPTIONS.keys()) | {""}


# ─────────────────────────────────────────────────────────────
# GET /api/v1/fengshui/options
# ─────────────────────────────────────────────────────────────


@router.get(
    "/options",
    summary="获取风水助手可选项（朝向列表等）",
    response_model=dict,
)
def get_options() -> dict:
    """返回房屋朝向列表，供前端下拉菜单使用。"""
    return {
        "house_facing_options": HOUSE_FACING_OPTIONS,
        "directions_zh": DIRECTIONS_ZH,
        "room_type_options": ROOM_TYPE_ZH,
    }


# ─────────────────────────────────────────────────────────────
# GET /api/v1/fengshui/bagua
# ─────────────────────────────────────────────────────────────


@router.get(
    "/bagua",
    response_model=BaguaResponse,
    summary="八宅命卦计算与方位推荐",
    description=(
        "根据出生年份与性别计算**命卦**，并返回四吉方、四凶方、"
        "床头/书桌/大门方位建议。\n\n"
        "可选传入房屋朝向（`house_facing`），额外返回人宅相合判断。\n\n"
        "**无需登录**。\n\n"
        "| 参数 | 说明 | 示例 |\n"
        "|------|------|---------|\n"
        "| `birth_year` | 出生公历年份 | `1990` |\n"
        "| `gender` | 性别 | `男` 或 `女` |\n"
        "| `house_facing` | 房屋朝向（可选） | `S`（朝南）|\n\n"
        "> ⚠ 本分析仅供参考，不构成专业风水建议。涉及结构改动请咨询专业人士。"
    ),
)
def get_bagua(
    birth_year: int = Query(..., ge=1900, le=2100, description="出生公历年份"),
    gender: str = Query(..., description="性别：男 / 女"),
    house_facing: str | None = Query(default=None, description="房屋朝向（可选）：N/NE/E/SE/S/SW/W/NW"),
) -> BaguaResponse:
    # 参数校验
    if gender not in _VALID_GENDERS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"gender 必须为 '男' 或 '女'，收到 '{gender}'",
        )
    if house_facing and house_facing not in HOUSE_FACING_OPTIONS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"house_facing 必须为 N/NE/E/SE/S/SW/W/NW 之一，或不传，收到 '{house_facing}'",
        )

    try:
        result = calc_bagua(
            birth_year=birth_year,
            gender=gender,
            house_facing=house_facing or None,
        )
    except Exception as exc:
        logger.exception("风水计算异常: birth_year=%s gender=%s", birth_year, gender)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"风水计算失败：{exc}",
        ) from exc

    # 构造响应
    auspicious = [
        DirectionItemResponse(
            direction=d.direction,
            direction_zh=d.direction_zh,
            label=d.label,
            level=d.level,
            level_css=d.level_css,
            desc=d.desc,
        )
        for d in result.auspicious
    ]
    inauspicious = [
        DirectionItemResponse(
            direction=d.direction,
            direction_zh=d.direction_zh,
            label=d.label,
            level=d.level,
            level_css=d.level_css,
            desc=d.desc,
        )
        for d in result.inauspicious
    ]

    def _tip_resp(t) -> FurnitureTipResponse | None:
        if t is None:
            return None
        return FurnitureTipResponse(
            item=t.item,
            direction=t.direction,
            direction_zh=t.direction_zh,
            label=t.label,
            reason=t.reason,
        )

    return BaguaResponse(
        life_gua=result.life_gua,
        gua_name=result.gua_name,
        gua_element=result.gua_element,
        group=result.group,
        birth_year=result.birth_year,
        gender=result.gender,
        auspicious=auspicious,
        inauspicious=inauspicious,
        bed_tip=_tip_resp(result.bed_tip),
        desk_tip=_tip_resp(result.desk_tip),
        door_tip=_tip_resp(result.door_tip),
        house_facing=result.house_facing,
        house_gua=result.house_gua,
        house_gua_name=result.house_gua_name,
        house_group=result.house_group,
        compatibility=result.compatibility,
        compatibility_note=result.compatibility_note,
        disclaimer=result.disclaimer,
    )


# ─────────────────────────────────────────────────────────────
# POST /api/v1/fengshui/room-layout  (v8.8.0)
# ─────────────────────────────────────────────────────────────

_VALID_DIRECTIONS = {"N", "NE", "E", "SE", "S", "SW", "W", "NW"}
_VALID_ROOM_TYPES = set(ROOM_TYPE_ZH.keys())


@router.post(
    "/room-layout",
    response_model=RoomLayoutResponse,
    summary="九宫格房间布局风水评估",
    description=(
        "根据命卦结果，对用户提交的**九宫格房间布局**进行逐区评估。\n\n"
        "每个方位可分配一种房间类型，引擎依据八宅法吉凶标签打分，"
        "并返回整体评分、改善建议。\n\n"
        "**支持的方位**：N / NE / E / SE / S / SW / W / NW\n\n"
        "**支持的房间类型**：empty / master_bedroom / bedroom / study / "
        "child_room / living_room / entrance / dining_room / kitchen / bathroom / storage\n\n"
        "> ⚠ 本分析仅供参考，不构成专业风水建议。涉及结构改动请咨询专业人士。"
    ),
)
def room_layout_assess(payload: RoomLayoutRequest) -> RoomLayoutResponse:
    """对九宫格房间布局进行风水评估，返回逐区得分与整体建议。"""
    # 参数校验
    if payload.gender not in _VALID_GENDERS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"gender 必须为 '男' 或 '女'，收到 '{payload.gender}'",
        )
    if payload.house_facing and payload.house_facing not in HOUSE_FACING_OPTIONS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"house_facing 必须为 N/NE/E/SE/S/SW/W/NW 之一，收到 '{payload.house_facing}'",
        )
    for d, rt in payload.rooms.items():
        if d not in _VALID_DIRECTIONS:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"不支持的方位 '{d}'，有效值：{sorted(_VALID_DIRECTIONS)}",
            )
        if rt not in _VALID_ROOM_TYPES:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"不支持的房间类型 '{rt}'，有效值：{sorted(_VALID_ROOM_TYPES)}",
            )
    if not payload.rooms:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="rooms 不能为空，请至少提供一个方位的房间类型",
        )

    try:
        result = assess_room_layout(
            birth_year=payload.birth_year,
            gender=payload.gender,
            rooms=payload.rooms,
            house_facing=payload.house_facing or None,
        )
    except Exception as exc:
        logger.exception("房间布局评估异常: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"房间布局评估失败：{exc}",
        ) from exc

    cells = [
        ZoneAssessmentResponse(
            direction=c.direction,
            direction_zh=c.direction_zh,
            label=c.label,
            level_css=c.level_css,
            room_type=c.room_type,
            room_zh=c.room_zh,
            assess_level=c.assess_level,
            assess_score=c.assess_score,
            assess_note=c.assess_note,
        )
        for c in result.cells
    ]

    return RoomLayoutResponse(
        life_gua=result.life_gua,
        gua_name=result.gua_name,
        score=result.score,
        grade=result.grade,
        grade_css=result.grade_css,
        cells=cells,
        suggestions=result.suggestions,
        disclaimer=result.disclaimer,
    )
