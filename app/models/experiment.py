"""Experiment 与 ExperimentEvent 模型 — §9 A/B 测试平台。"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import ClassVar

from sqlalchemy import Column, Index, Text
from sqlmodel import Field, SQLModel


class Experiment(SQLModel, table=True):
    """
    A/B 测试实验表。

    每条实验记录定义一个可控随机实验：
      - variants: JSON 数组，每项含 { name, description, weight }
      - status: draft → running → paused / completed
      - traffic_split: JSON，{variant_name: 百分比整数}
    """

    __tablename__: ClassVar[str] = "experiments"
    __table_args__ = (
        Index("idx_experiments_status", "status"),
        Index("idx_experiments_name", "name"),
        Index("idx_experiments_created", "created_at"),
    )

    id: int | None = Field(default=None, primary_key=True)

    # 实验基本信息
    name: str = Field(max_length=100)
    description: str = Field(default="", sa_column=Column(Text))

    # 实验状态: draft / running / paused / completed
    status: str = Field(default="draft", max_length=20)

    # 变体定义（JSON 数组）
    # 例：[{"name":"control","description":"原版","weight":50},
    #      {"name":"variant_a","description":"新按钮文案","weight":50}]
    variants: str = Field(default="[]", sa_column=Column(Text))

    # 流量分割（JSON 对象，key=variant_name, value=百分比）
    # 例：{"control":50,"variant_a":50}
    traffic_split: str = Field(default="{}", sa_column=Column(Text))

    # 目标指标名称（用于结果分析）
    target_metric: str = Field(default="chart_generated", max_length=100)

    # 假设与最小样本量
    hypothesis: str = Field(default="", sa_column=Column(Text))
    min_sample_size: int = Field(default=100)

    # 时间戳
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    started_at: datetime | None = None
    ended_at: datetime | None = None
    deleted_at: datetime | None = None


class ExperimentEvent(SQLModel, table=True):
    """
    实验事件记录表。

    每条记录代表某个会话（session_id）在某个变体下触发的一个事件：
      event_type: assigned / chart_generated / form_submitted / batch_uploaded / ...
    """

    __tablename__: ClassVar[str] = "experiment_events"
    __table_args__ = (
        Index("idx_exp_events_exp_id", "experiment_id"),
        Index("idx_exp_events_variant", "experiment_id", "variant"),
        Index("idx_exp_events_session", "session_id"),
        Index("idx_exp_events_created", "created_at"),
    )

    id: int | None = Field(default=None, primary_key=True)

    # 关联实验
    experiment_id: int = Field(foreign_key="experiments.id", index=True)

    # 变体名称（例：control / variant_a）
    variant: str = Field(max_length=50)

    # 事件类型
    event_type: str = Field(max_length=50)

    # 会话标识（前端生成的 UUID，同一次浏览会话保持一致）
    session_id: str = Field(default="", max_length=100)

    # 附加元数据（JSON 字符串，例如 {"gender":"女","score":82}）
    meta: str = Field(default="{}", sa_column=Column(Text))

    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
