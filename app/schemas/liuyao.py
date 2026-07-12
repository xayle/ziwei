"""六爻 API Schema"""

from __future__ import annotations

from pydantic import BaseModel, Field


class YaoDetail(BaseModel):
    position: int
    value: int
    text: str
    is_yang: bool
    is_dong: bool
    is_shi: bool
    is_ying: bool
    najia_stem: str
    najia_branch: str
    najia: str
    wuxing: str
    liuqin: str


class LiuyaoCastResponse(BaseModel):
    gua_name: str
    gua_bian: str
    gua_hu: str
    palace: str
    palace_element: str
    ben_yao: list[int]
    bian_yao: list[int]
    dong_yao: list[int]
    shi_yao: int
    ying_yao: int
    yao_details: list[YaoDetail]


class LiuyaoTimeRequest(BaseModel):
    year: int = Field(ge=1900, le=2100)
    month: int = Field(ge=1, le=12)
    day: int = Field(ge=1, le=31)
    hour: int = Field(ge=0, le=23)
