"""app/schemas/v2/verify.py — API v2 专属 Schema 定义.

⚠️ v1 VerifyResponse 不继承/修改——v2 Schema 完全独立演进。
   VerifyResponseFull 仅在 v2 内部局部继承以实现 discriminator，
   不暴露给 /api/v1/* 客户端。
"""

from __future__ import annotations

from typing import Annotated, Literal, Union

from pydantic import BaseModel, Field

from app.schemas.bazi import (
    GejuModel,
    VerifyRequest,
    VerifyResponse,
    WuXingScoreModel,
    YongShenModel,
)

# ─────────────────────────────────────────────────────────────────────────────
# v2 请求 Schema
# ─────────────────────────────────────────────────────────────────────────────


class VerifyRequestV2(VerifyRequest):
    """v2 排盘请求：继承 v1 VerifyRequest，追加 output_format。"""

    output_format: Literal["full", "minimal"] = Field(
        "full",
        description=(
            "响应格式：full=完整响应（等同 v1 VerifyResponse + meta）；"
            "minimal=精简5字段（geju/yongshen/dayun_current/wuxing_score/score）"
        ),
    )


# ─────────────────────────────────────────────────────────────────────────────
# v2 响应 Meta（R38：三字段缺一不可）
# ─────────────────────────────────────────────────────────────────────────────


class ResponseMeta(BaseModel):
    """API v2 响应元信息（满足红线 R38）."""

    api_version: str = Field(..., description="API 版本字符串，例如 v2.0")
    engine_version: str = Field(..., description="引擎版本字符串，例如 v8.0")
    calc_ms: float = Field(..., description="本次计算耗时（毫秒）")


# ─────────────────────────────────────────────────────────────────────────────
# v2 响应体 —— VerifyResponseFull（v2 内部，继承 v1，仅添加 discriminator）
# ─────────────────────────────────────────────────────────────────────────────


class VerifyResponseFull(VerifyResponse):
    """完整响应体，在 v1 VerifyResponse 基础上追加 response_type discriminator 字段。

    仅供 v2 内部 discriminated union 使用，不影响 /api/v1/verify 响应结构。
    """

    response_type: Literal["full"] = Field(
        "full",
        description="Discriminator 字段（Pydantic v2 discriminated union 要求）",
    )


# ─────────────────────────────────────────────────────────────────────────────
# v2 响应体 —— VerifyResponseMinimal（output_format="minimal" 时使用）
# ─────────────────────────────────────────────────────────────────────────────


class VerifyResponseMinimal(BaseModel):
    """精简响应体——仅保留5个核心字段（output_format='minimal'）。

    省略字段（节省计算与带宽）：
      palace / shensha / classic_ref_list / monthly_fortune / lifestyle / milestone
    """

    response_type: Literal["minimal"] = Field(
        "minimal",
        description="Discriminator 字段",
    )
    geju: GejuModel | None = Field(None, description="格局分析")
    yongshen: YongShenModel | None = Field(None, description="用神五行")
    dayun_current: dict | None = Field(
        None,
        description="当前大运条目（DaYunItemModel 的 JSON 序列化，由引擎判断当前年份所在大运）",
    )
    wuxing_score: WuXingScoreModel | None = Field(None, description="五行得分")
    score: float | None = Field(
        None,
        description="日主强弱评分 [0-100]，来自 day_master_strength.score",
    )


# ─────────────────────────────────────────────────────────────────────────────
# v2 外层信封（meta + data）
# ─────────────────────────────────────────────────────────────────────────────


class VerifyResponseV2(BaseModel):
    """API v2 响应外层信封：meta + data（discriminated union）.

    - data 类型由 response_type 字段区分（Pydantic v2 discriminated union）
    - v2 外层用组合而非继承，保证 v2/v1 可独立演进
    """

    meta: ResponseMeta = Field(..., description="API 元信息（R38 三字段）")
    data: Annotated[
        Union[VerifyResponseFull, VerifyResponseMinimal],
        Field(discriminator="response_type"),
    ] = Field(..., description="排盘响应体，类型由 output_format 决定")
