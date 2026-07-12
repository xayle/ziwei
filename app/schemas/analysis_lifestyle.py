"""Lifestyle analysis schemas extracted from app.schemas.analysis."""

from __future__ import annotations

from pydantic import BaseModel


class JewelryItemModel(BaseModel):
    """单件饰品"""

    material: str
    gemstone: str
    position: str
    wuxing: str


class JewelryModel(BaseModel):
    """饰品建议"""

    primary: JewelryItemModel
    secondary: JewelryItemModel
    combination: str
    taboo: list[str]
    interpretation_text: str
    disclaimer: str = "仅供学术研究参考"


class FengshuiModel(BaseModel):
    """风水建议"""

    auspicious_directions: list[str]
    decor: list[str]
    plants: list[str]
    lucky_colors: list[str]
    taboo: list[str]
    interpretation_text: str
    disclaimer: str = "仅供学术研究参考"


class LifestyleModel(BaseModel):
    """生活建议"""

    exercise: list[str]
    best_times: str
    diet: list[str]
    travel_direction: str
    sleep_advice: str
    interpretation_text: str
    disclaimer: str = "仅供学术研究参考"


class LuckyModel(BaseModel):
    """开运数据"""

    lucky_colors: list[str]
    lucky_numbers: list[int]
    lucky_direction: str
    lucky_item: str
    interpretation_text: str
    avoid_colors: list[str] = []
    avoid_direction: str = ""
    disclaimer: str = "仅供学术研究参考"
