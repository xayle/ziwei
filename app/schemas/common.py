"""Common schemas used across the application."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class WarningModel(BaseModel):
    """统一的警告模型"""

    code: str
    message: str
    meta: dict[str, Any] | None = None


class RangeModel(BaseModel):
    """flexible numeric range with multiple key formats."""

    min: float | None = None
    max: float | None = None
    low: float | None = None
    high: float | None = None
    from_: float | None = Field(default=None, alias="from")
    to: float | None = None
    currency: str | None = None

    model_config = ConfigDict(populate_by_name=True, extra="allow")


class BackendInfo(BaseModel):
    """后端服务信息"""

    primary: str = Field(..., description="Primary backend requested")
    secondary: str | None = Field(None, description="Secondary backend when mode=dual")
    sxtwl_available: bool = Field(..., description="sxtwl availability at request time")
    cnlunar_available: bool = Field(..., description="cnlunar availability at request time")
