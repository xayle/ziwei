"""GET /life/snippets — BOOK-GTM §5.3 抖音钩子句草案（P3-02 / T076）。"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

SnippetLayer = Literal["engine", "classical"]


class LifeSnippetHookModel(BaseModel):
    tag: str = Field(..., description="展示标签：事实 / 典籍 / 推算 …")
    text: str = Field(..., description="≤80 字钩子句，适合竖屏字幕")
    layer: SnippetLayer = Field(..., description="engine=排盘事实；classical=典籍句")


class LifeSnippetsResponseModel(BaseModel):
    schema_version: Literal["life-snippets@0.1"] = "life-snippets@0.1"
    case_id: str
    hooks: list[LifeSnippetHookModel] = Field(
        ...,
        min_length=1,
        max_length=5,
        description="3–5 条钩子句（草案默认取满可用事实）",
    )
    vertical_title: str = Field(..., description="竖版分享卡卷目标题")
    disclaimer: str = Field(..., description="短免责声明（抖音口播用）")
