"""Shared disclaimer block schema."""

from __future__ import annotations

from pydantic import BaseModel, Field


class DisclaimerBlockModel(BaseModel):
    text: str
    version: str
    jurisdiction: str | None = Field(default="CN")
