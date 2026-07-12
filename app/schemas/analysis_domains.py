"""Domain analysis schemas extracted from app.schemas.analysis."""

from __future__ import annotations

from typing import Literal, Self

from pydantic import BaseModel, Field, model_validator


class WealthAnalysisModel(BaseModel):
    """财运分析 §4.11-A"""

    wealth_score: int = Field(..., ge=0, le=100)
    wealth_tier: Literal["上", "中", "下"]
    annual_range: str
    industries: list[str]
    strategy: str
    dayun_forecast: list[dict]
    inference_tags: list[str]
    interpretation_text: str
    disclaimer: str = "仅供学术研究参考"
    fact_data: dict | None = None
    investment_preference: str | None = None
    financial_taboos: str | None = None
    wealth_accumulation_phases: str | None = None

    @model_validator(mode="after")  # type: ignore[misc]
    def _fill_fact_data(self) -> Self:
        if self.fact_data is None:
            self.fact_data = {
                "wealth_score": self.wealth_score,
                "wealth_tier": self.wealth_tier,
                "annual_range": self.annual_range,
                "industries": self.industries,
                "strategy": self.strategy,
                "dayun_forecast": self.dayun_forecast,
            }
        return self


class CareerAnalysisModel(BaseModel):
    """事业分析 §4.11-B"""

    career_score: int = Field(..., ge=0, le=100)
    career_directions: list[str]
    suitable_industries: list[str]
    leadership_potential: bool
    development_advice: str
    optimal_move_timing: str
    inference_tags: list[str]
    interpretation_text: str
    disclaimer: str = "仅供学术研究参考"
    fact_data: dict | None = None
    entrepreneurship_assessment: str | None = None
    five_year_roadmap: str | None = None
    collaboration_style: str | None = None

    @model_validator(mode="after")  # type: ignore[misc]
    def _fill_fact_data(self) -> Self:
        if self.fact_data is None:
            self.fact_data = {
                "career_score": self.career_score,
                "career_directions": self.career_directions,
                "suitable_industries": self.suitable_industries,
                "leadership_potential": self.leadership_potential,
                "development_advice": self.development_advice,
                "optimal_move_timing": self.optimal_move_timing,
            }
        return self


class MarriageAnalysisModel(BaseModel):
    """婚姻分析 §4.11-C"""

    marriage_score: int = Field(..., ge=0, le=100)
    peach_blossom: Literal["旺", "中", "弱"]
    partner_wuxing: str
    partner_profile: str
    partner_direction: str
    optimal_marriage_age: str
    marriage_windows: list[str]
    children_outlook: str
    children_timing: str | None = None
    inference_tags: list[str]
    interpretation_text: str
    disclaimer: str = "仅供学术研究参考"
    fact_data: dict | None = None
    emotional_pitfalls: str | None = None
    second_marriage_indicator: str | None = None

    @model_validator(mode="after")  # type: ignore[misc]
    def _fill_fact_data(self) -> Self:
        if self.fact_data is None:
            self.fact_data = {
                "marriage_score": self.marriage_score,
                "peach_blossom": self.peach_blossom,
                "partner_wuxing": self.partner_wuxing,
                "partner_direction": self.partner_direction,
                "optimal_marriage_age": self.optimal_marriage_age,
                "marriage_windows": self.marriage_windows,
                "children_outlook": self.children_outlook,
                "children_timing": self.children_timing,
            }
        return self


class HealthAnalysisModel(BaseModel):
    """健康分析 §4.11-D"""

    health_score: int = Field(..., ge=0, le=100)
    risk_organs: list[str]
    risk_level: Literal["高", "中", "低"]
    health_advice: str
    exercise: list[str]
    diet: list[str]
    peak_period: str
    inference_tags: list[str]
    interpretation_text: str
    disclaimer: str = "仅供学术研究参考"
    fact_data: dict | None = None
    seasonal_health: str | None = None
    mental_health_advice: str | None = None
    constitution_type: str | None = None

    @model_validator(mode="after")  # type: ignore[misc]
    def _fill_fact_data(self) -> Self:
        if self.fact_data is None:
            self.fact_data = {
                "health_score": self.health_score,
                "risk_organs": self.risk_organs,
                "risk_level": self.risk_level,
                "health_advice": self.health_advice,
                "exercise": self.exercise,
                "diet": self.diet,
                "peak_period": self.peak_period,
            }
        return self


class RelationshipAnalysisModel(BaseModel):
    """人际分析 §4.11-E"""

    relationship_score: int = Field(..., ge=0, le=100)
    liu_qin: dict[str, str]
    noble_people: list[str]
    petty_people: list[str]
    social_strategy: str
    inference_tags: list[str]
    interpretation_text: str
    disclaimer: str = "仅供学术研究参考"
    fact_data: dict | None = None

    @model_validator(mode="after")  # type: ignore[misc]
    def _fill_fact_data(self) -> Self:
        if self.fact_data is None:
            self.fact_data = {
                "relationship_score": self.relationship_score,
                "liu_qin": self.liu_qin,
                "noble_people": self.noble_people,
                "petty_people": self.petty_people,
                "social_strategy": self.social_strategy,
            }
        return self


class PersonalityModel(BaseModel):
    """性格分析 §4.11-F"""

    day_stem: str
    day_stem_trait: str
    strength_modifier: str
    advantages: list[str]
    disadvantages: list[str]
    growth_advice: str
    inference_tags: list[str]
    interpretation_text: str
    disclaimer: str = "仅供学术研究参考"
    fact_data: dict | None = None
    communication_style: str | None = None
    stress_coping_mode: str | None = None
    potential_activation: str | None = None

    @model_validator(mode="after")  # type: ignore[misc]
    def _fill_fact_data(self) -> Self:
        if self.fact_data is None:
            self.fact_data = {
                "day_stem": self.day_stem,
                "day_stem_trait": self.day_stem_trait,
                "strength_modifier": self.strength_modifier,
                "advantages": self.advantages,
                "disadvantages": self.disadvantages,
                "growth_advice": self.growth_advice,
            }
        return self
