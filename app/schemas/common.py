"""Common schemas used across the application."""
from __future__ import annotations

from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict, Field


class WarningModel(BaseModel):
    """统一的警告模型"""
    code: str
    message: str
    meta: Optional[Dict[str, Any]] = None


class RangeModel(BaseModel):
    """flexible numeric range with multiple key formats."""
    min: Optional[float] = None
    max: Optional[float] = None
    low: Optional[float] = None
    high: Optional[float] = None
    from_: Optional[float] = Field(None, alias="from")
    to: Optional[float] = None
    currency: Optional[str] = None

    model_config = ConfigDict(populate_by_name=True, extra="allow")


class BackendInfo(BaseModel):
    """后端服务信息"""
    primary: str = Field(..., description="Primary backend requested")
    secondary: Optional[str] = Field(None, description="Secondary backend when mode=dual")
    sxtwl_available: bool = Field(..., description="sxtwl availability at request time")
    cnlunar_available: bool = Field(..., description="cnlunar availability at request time")
