"""
app/schemas/analysis.py — M2 新增 19 个分析模型 (任务 2.08)

包含:
  LifeArcModel            — 一生运势总论
  GejuModel               — 格局模型
  PalaceItemModel         — 单宫位模型
  PalaceModel             — 十二宫模型
  ShenshaModel            — 单神煞条目
  WealthAnalysisModel     — 财运分析 (§4.11-A)
  CareerAnalysisModel     — 事业分析 (§4.11-B)
  MarriageAnalysisModel   — 婚姻分析 (§4.11-C)
  HealthAnalysisModel     — 健康分析 (§4.11-D)
  RelationshipAnalysisModel — 人际分析 (§4.11-E)
  PersonalityModel        — 性格分析 (§4.11-F)
  MonthlyFortuneModel     — 月运 (§4.11-G)
  JewelryItemModel        — 单件饰品
  JewelryModel            — 饰品建议
  FengshuiModel           — 风水建议
  LifestyleModel          — 生活建议
  LuckyModel              — 开运数据
  MilestoneModel          — 人生节点
  LiuNianDetailModel      — 流年四维详情
"""
from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field


# ─────────────────────────────────────────────────────────────────────────────
# 一生运势总论
# ─────────────────────────────────────────────────────────────────────────────

class LifeArcModel(BaseModel):
    """一生运势总论（Tab 0 总览精简卡片 + Tab 5 摘要完整展示）"""
    overall_tier:    Literal["局高", "局中", "局小"]
    early_fortune:   str          # 幼年/少年（0-20岁）运势（2-3句）
    mid_fortune:     str          # 青年/中年运势（2-3句）
    late_fortune:    str          # 晚年运势（2-3句）
    peak_periods:    list[str]    # 一生最旺1-2步大运
    caution_periods: list[str]    # 需小心的大运
    life_motto:      str          # 古籍旗面一句
    inference_tags:  list[str]
    interpretation_text: str      # 100-200字综述
    disclaimer:      str = "仅供学术研究参考"
    optimal_action:  Optional[str] = None


# ─────────────────────────────────────────────────────────────────────────────
# 核心计算组
# ─────────────────────────────────────────────────────────────────────────────

class GejuModel(BaseModel):
    """格局模型"""
    geju_name:           str
    geju_level:          Literal["上格", "中格", "下格", "无格"]
    month_stem_shishen:  str
    is_broken:           bool = False
    inference_tags:      list[str]
    interpretation_text: str
    classic_ref:         str
    disclaimer:          str = "仅供学术研究参考"


class PalaceItemModel(BaseModel):
    """单宫位"""
    palace_name: str
    dizhi:       str
    tiangan:     Optional[str] = None
    strength:    Literal["旺", "相", "休", "囚", "死"]
    shishen:     Optional[str] = None
    note:        str = ""


class PalaceModel(BaseModel):
    """十二宫模型"""
    ming_gong:       PalaceItemModel
    shen_gong:       PalaceItemModel
    twelve_palaces:  list[PalaceItemModel]    # 固定12项
    inference_tags:  list[str]
    interpretation_text: str
    disclaimer:      str = "仅供学术研究参考"


class ShenshaModel(BaseModel):
    """单神煞条目"""
    name:           str
    dizhi:          str
    pillar:         Literal["year", "month", "day", "hour"]
    is_beneficial:  bool
    is_star:        bool = False     # ≥3条相关关系时置True [P69]
    meaning:        str
    classic_source: str


# ─────────────────────────────────────────────────────────────────────────────
# 分析引擎组
# ─────────────────────────────────────────────────────────────────────────────

class WealthAnalysisModel(BaseModel):
    """财运分析 §4.11-A"""
    wealth_score:    int = Field(..., ge=0, le=100)
    wealth_tier:     Literal["上", "中", "下"]
    annual_range:    str                       # 如"30-80万/年"
    industries:      list[str]                 # 推荐行业（≤5项）
    strategy:        str
    dayun_forecast:  list[dict]                # [{"ganzhi":"甲子","trend":"上升/平稳/下降"}]
    inference_tags:      list[str]
    interpretation_text: str
    disclaimer:          str = "仅供学术研究参考"


class CareerAnalysisModel(BaseModel):
    """事业分析 §4.11-B"""
    career_score:         int = Field(..., ge=0, le=100)
    career_directions:    list[str]
    suitable_industries:  list[str]
    leadership_potential: bool
    development_advice:   str
    optimal_move_timing:  str
    inference_tags:       list[str]
    interpretation_text:  str
    disclaimer:           str = "仅供学术研究参考"


class MarriageAnalysisModel(BaseModel):
    """婚姻分析 §4.11-C"""
    marriage_score:       int = Field(..., ge=0, le=100)
    peach_blossom:        Literal["旺", "中", "弱"]
    partner_wuxing:       str
    partner_profile:      str
    partner_direction:    str
    optimal_marriage_age: str
    marriage_windows:     list[str]
    children_outlook:     str
    children_timing:      Optional[str] = None
    inference_tags:       list[str]
    interpretation_text:  str
    disclaimer:           str = "仅供学术研究参考"


class HealthAnalysisModel(BaseModel):
    """健康分析 §4.11-D"""
    health_score:    int = Field(..., ge=0, le=100)
    risk_organs:     list[str]
    risk_level:      Literal["高", "中", "低"]
    health_advice:   str
    exercise:        list[str]
    diet:            list[str]
    peak_period:     str
    inference_tags:  list[str]
    interpretation_text: str
    disclaimer:      str = "仅供学术研究参考"


class RelationshipAnalysisModel(BaseModel):
    """人际分析 §4.11-E"""
    relationship_score: int = Field(..., ge=0, le=100)
    liu_qin:     dict[str, str]    # {"父":...,"母":...,"配偶":...,"子女":...}
    noble_people: list[str]
    petty_people: list[str]
    social_strategy: str
    inference_tags:  list[str]
    interpretation_text: str
    disclaimer:      str = "仅供学术研究参考"


class PersonalityModel(BaseModel):
    """性格分析 §4.11-F"""
    day_stem:          str
    day_stem_trait:    str
    strength_modifier: str
    advantages:        list[str]     # 3-5条
    disadvantages:     list[str]     # 3-5条
    growth_advice:     str
    inference_tags:    list[str]
    interpretation_text: str
    disclaimer:        str = "仅供学术研究参考"


class MonthlyFortuneModel(BaseModel):
    """月运模型 §4.11-G"""
    month:       int = Field(..., ge=1, le=12)
    month_dizhi: str
    luck_level:  Literal["吉", "平", "凶"]
    color_hint:  str    # CSS色值
    tip:         str
    clash_with:  Optional[str] = None
    disclaimer:  str = "仅供学术研究参考"


# ─────────────────────────────────────────────────────────────────────────────
# 生活应用组
# ─────────────────────────────────────────────────────────────────────────────

class JewelryItemModel(BaseModel):
    """单件饰品"""
    material:  str
    gemstone:  str
    position:  str
    wuxing:    str


class JewelryModel(BaseModel):
    """饰品建议"""
    primary:    JewelryItemModel
    secondary:  JewelryItemModel
    combination: str
    taboo:      list[str]
    interpretation_text: str
    disclaimer: str = "仅供学术研究参考"


class FengshuiModel(BaseModel):
    """风水建议"""
    auspicious_directions: list[str]
    decor:        list[str]
    plants:       list[str]
    lucky_colors: list[str]
    taboo:        list[str]
    interpretation_text: str
    disclaimer:   str = "仅供学术研究参考"


class LifestyleModel(BaseModel):
    """生活建议"""
    exercise:         list[str]
    best_times:       str
    diet:             list[str]
    travel_direction: str
    sleep_advice:     str
    interpretation_text: str
    disclaimer:       str = "仅供学术研究参考"


class LuckyModel(BaseModel):
    """开运数据"""
    lucky_colors:    list[str]
    lucky_numbers:   list[int]
    lucky_direction: str
    lucky_item:      str
    interpretation_text: str
    disclaimer:      str = "仅供学术研究参考"


# ─────────────────────────────────────────────────────────────────────────────
# 时间线组
# ─────────────────────────────────────────────────────────────────────────────

class MilestoneModel(BaseModel):
    """人生里程碑节点"""
    age:            int
    year:           int
    milestone_type: Literal["犯太岁", "岁运并临", "大运交接", "社会节点"]
    ganzhi_context: str
    description:    str
    risk_level:     Literal["高", "中", "低"]
    advice:         str


class LiuNianDetailModel(BaseModel):
    """流年四维详情"""
    year:              int
    ganzhi:            str
    tai_sui_relations: list[str]
    clash_pillars:     list[str]
    notable_months:    list[int]
    annual_score:      int = Field(..., ge=0, le=100)
    domain_forecasts:  dict[str, str]    # 必含 财运/事业/婚恋/健康
    optimal_action:    Optional[str] = None
    inference_tags:    list[str]
    interpretation_text: str
    disclaimer:        str = "仅供学术研究参考"


# ─────────────────────────────────────────────────────────────────────────────
# current_fortune_summary 内嵌模型
# ─────────────────────────────────────────────────────────────────────────────

class CurrentFortuneSummaryModel(BaseModel):
    """当前运势摘要（Tab 0 精简卡片）"""
    current_dayun:         str          # 当前大运干支，如"甲子"
    dayun_years_remaining: int          # 当前大运剩余年数
    current_liunian:       str          # 当前流年干支
    this_year_domains:     dict[str, str]   # 同 domain_forecasts 结构
    top3_actions:          list[str]    # 今年最值得关注的3件事
