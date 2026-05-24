"""
app/schemas/event_prediction.py — 命理事件预测系统数据模型

事件预测系统：
  - 5类事件：婚姻 / 财运 / 买房 / 事业 / 健康
  - 每类含多个子事件类型（event_subtype）
  - 4层信号叠加算法（natal_base / dayun_trigger / liunian_trigger / month_trigger）
  - 结构化输出供 LLM 咨询式解读使用
"""
from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field

# ─────────────────────────────────────────────────────────────────────────────
# 枚举类型
# ─────────────────────────────────────────────────────────────────────────────

RiskLevel     = Literal["none", "low", "medium", "medium_high", "high"]
OpnLevel      = Literal["none", "low", "medium", "high"]
SignalLayer   = Literal["natal_base", "dayun_trigger", "liunian_trigger", "month_trigger"]
SignalSev     = Literal["primary", "secondary", "tertiary"]


# ─────────────────────────────────────────────────────────────────────────────
# 子模型
# ─────────────────────────────────────────────────────────────────────────────

class EventSignal(BaseModel):
    """单条命理信号"""
    signal_key:  str            # 信号标识，如 "day_branch_clashed"
    label:       str            # 展示文字，如 "夫妻宫被流年冲动"
    layer:       SignalLayer    # 所属层次
    severity:    SignalSev      # 信号强度
    rule_id:     Optional[str] = None  # 对应 event_rules.json 规则 id


class ClassicalNote(BaseModel):
    """古籍依据"""
    basis:  str     # 古籍原文/解读
    source: str     # 来源，如《子平真诠》


# ─────────────────────────────────────────────────────────────────────────────
# 核心事件结果
# ─────────────────────────────────────────────────────────────────────────────

class EventResult(BaseModel):
    """单类事件在某年的完整预测结果"""
    event_type:   str   # 事件类别：marriage / wealth / property / career / health
    year:         int

    # 风险与机会等级
    risk_level:         RiskLevel
    opportunity_level:  OpnLevel

    # 信号置信度 0.0-1.0
    confidence:  float = Field(default=0.5, ge=0.0, le=1.0)

    # 一句话结论（前端直接展示，给 LLM 作为"不能跑偏"的锚点）
    main_judgment:  str = ""

    # 信号摘要（给 LLM 用，防止 LLM 扩展出系统未判断的内容）
    trigger_summary: str = ""

    # 具体子事件类型列表
    event_subtypes: list[str] = Field(default_factory=list)

    # 命理信号列表（4层）
    signals: list[EventSignal] = Field(default_factory=list)

    # 可能的现实表现
    possible_manifestations: list[str] = Field(default_factory=list)

    # 关键月份（1-12）
    key_months: list[int] = Field(default_factory=list)

    # 现实预兆（"出现这些现象时风险可能加重"）
    omens: list[str] = Field(default_factory=list)

    # 应对建议
    advice: list[str] = Field(default_factory=list)

    # 古籍依据
    classical_notes: list[ClassicalNote] = Field(default_factory=list)

    # 明确告知 LLM 不能说什么（关键约束，防止过度断言）
    avoid_overclaim: Optional[str] = None


# ─────────────────────────────────────────────────────────────────────────────
# 年份事件请求/响应
# ─────────────────────────────────────────────────────────────────────────────

class YearEventRequest(BaseModel):
    """单年事件预测请求"""
    case_id:     str
    year:        int = Field(..., ge=1900, le=2200)
    event_types: list[str] = Field(
        default=["marriage", "wealth", "property", "career", "health"],
        description="要预测的事件类别，默认全部5类"
    )


class YearEventResponse(BaseModel):
    """单年事件预测响应"""
    case_id:           str
    year:              int
    year_ganzhi:       str
    events:            dict[str, EventResult]   # key: event_type
    overall_year_score: int = Field(..., ge=0, le=100)


# ─────────────────────────────────────────────────────────────────────────────
# 多年趋势
# ─────────────────────────────────────────────────────────────────────────────

class YearSummary(BaseModel):
    """某年摘要（用于时间线展示）"""
    year:             int
    year_ganzhi:      str
    main_theme:       str           # 该年主线，如"婚姻压力测试"
    top_events:       list[str]     # 最显著的子事件类型
    risk:             RiskLevel
    opportunity:      OpnLevel
    annual_score:     int = Field(..., ge=0, le=100)


class MultiYearTrendRequest(BaseModel):
    """多年趋势请求"""
    case_id: str
    years:   list[int] = Field(..., min_length=1, max_length=10)


class MultiYearTrendResponse(BaseModel):
    """多年趋势响应"""
    case_id:          str
    # 三年/多年主线综述（一句话，前端显著位置展示）
    timeline_summary: str = ""
    summaries:        list[YearSummary]


# ─────────────────────────────────────────────────────────────────────────────
# AI 咨询式解读
# ─────────────────────────────────────────────────────────────────────────────

class YearEventConsultRequest(BaseModel):
    """AI 咨询请求"""
    case_id:       str
    year:          int = Field(..., ge=1900, le=2200)
    event_type:    str     # marriage / wealth / property / career / health
    user_question: str = Field(..., min_length=2, max_length=500)


class YearEventConsultResponse(BaseModel):
    """AI 咨询响应"""
    case_id:            str
    year:               int
    event_type:         str
    interpretation:     str         # LLM 生成的咨询式解读文本
    followup_questions: list[str]   # 5个追问问题
