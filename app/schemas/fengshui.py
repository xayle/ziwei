"""app/schemas/fengshui.py — §15 风水方位助手 Pydantic 模型。"""

from __future__ import annotations

from pydantic import BaseModel, Field


class FurnitureTipResponse(BaseModel):
    item: str = Field(description="家具/位置名称，如 '床头朝向'")
    direction: str = Field(description="方向代码，如 'SE'")
    direction_zh: str = Field(description="方向中文，如 '东南'")
    label: str = Field(description="能量标签，如 '生气'")
    reason: str = Field(description="建议理由")


class DirectionItemResponse(BaseModel):
    direction: str = Field(description="方向代码，如 'N'")
    direction_zh: str = Field(description="方向中文，如 '北'")
    label: str = Field(description="能量标签，如 '生气'")
    level: str = Field(description="吉凶级别，如 '最吉'")
    level_css: str = Field(description="CSS 类名，如 'ji1'")
    desc: str = Field(description="描述说明")


class BaguaResponse(BaseModel):
    """八宅命卦分析完整响应。"""

    life_gua: int = Field(description="命卦数（1/2/3/4/6/7/8/9）")
    gua_name: str = Field(description="卦名，如 '坎'")
    gua_element: str = Field(description="五行，如 '水'")
    group: str = Field(description="命组：东四命 / 西四命")
    birth_year: int
    gender: str

    auspicious: list[DirectionItemResponse] = Field(description="四吉方（生气/天医/延年/伏位）")
    inauspicious: list[DirectionItemResponse] = Field(description="四凶方（绝命/五鬼/六煞/祸害）")

    bed_tip: FurnitureTipResponse | None = Field(default=None, description="床头方位建议")
    desk_tip: FurnitureTipResponse | None = Field(default=None, description="书桌/工位方位建议")
    door_tip: FurnitureTipResponse | None = Field(default=None, description="大门方位建议")

    house_facing: str | None = Field(default=None, description="房屋朝向代码")
    house_gua: int | None = Field(default=None, description="房屋卦数")
    house_gua_name: str | None = Field(default=None, description="房屋卦名")
    house_group: str | None = Field(default=None, description="房屋组：东四宅 / 西四宅")
    compatibility: str | None = Field(default=None, description="人宅相合：相合 / 不合")
    compatibility_note: str | None = Field(default=None, description="相合说明")

    disclaimer: str = Field(description="免责声明")


# ─────────────────────────────────────────────────────────────
# v8.8.0 房间布局评估
# ─────────────────────────────────────────────────────────────


class RoomLayoutRequest(BaseModel):
    """房间布局评估请求。"""

    birth_year: int = Field(..., ge=1900, le=2100, description="出生公历年份")
    gender: str = Field(..., description="性别：男 / 女")
    house_facing: str | None = Field(default=None, description="房屋朝向（可选）：N/NE/E/SE/S/SW/W/NW")
    rooms: dict[str, str] = Field(
        ...,
        description='方位→房间类型映射，如 {"N": "kitchen", "E": "master_bedroom"}。'
        "支持的方位：N/NE/E/SE/S/SW/W/NW。"
        "支持的房间类型：empty/master_bedroom/bedroom/study/child_room/"
        "living_room/entrance/dining_room/kitchen/bathroom/storage",
    )


class ZoneAssessmentResponse(BaseModel):
    """单个方位的房间布局评估结果。"""

    direction: str = Field(description="方向代码，如 'N'")
    direction_zh: str = Field(description="方向中文，如 '北'")
    label: str = Field(description="风水标签，如 '生气'")
    level_css: str = Field(description="CSS 类名，如 'ji1'")
    room_type: str = Field(description="房间类型英文")
    room_zh: str = Field(description="房间类型中文")
    assess_level: str = Field(description="评估等级：excellent/good/ok/caution/warning/skip")
    assess_score: int = Field(description="评估分数 0~100")
    assess_note: str = Field(description="评估说明文字")


class RoomLayoutResponse(BaseModel):
    """房间布局整体评估响应。"""

    life_gua: int = Field(description="命卦数（1-9，无5）")
    gua_name: str = Field(description="卦名，如 '坎'")
    score: int = Field(description="加权整体评分 0~100")
    grade: str = Field(description="等级文字：优秀/良好/一般/较差/待改善")
    grade_css: str = Field(description="等级 CSS 类：excellent/good/ok/caution/warning")
    cells: list[ZoneAssessmentResponse] = Field(description="各方位评估详情")
    suggestions: list[str] = Field(description="改善建议列表")
    disclaimer: str = Field(description="免责声明")
