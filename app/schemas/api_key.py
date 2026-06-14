"""
app/schemas/api_key.py — API Key 请求与响应 Schema（§12）
"""

from __future__ import annotations

from datetime import UTC, datetime

from pydantic import BaseModel, Field, field_validator

# ---------------------------------------------------------------------------
# 创建请求
# ---------------------------------------------------------------------------


class ApiKeyCreate(BaseModel):
    """创建新 API Key 的请求体。"""

    name: str = Field(..., max_length=64, description='自定义标签，如 "生产环境集成"')
    scopes: str = Field(
        default="read",
        description="权限范围，逗号分隔：read / write / admin",
    )
    rate_limit_per_min: int = Field(
        default=60,
        ge=0,
        le=10000,
        description="每分钟最大请求数，0 = 继承全局限制",
    )
    expires_in_days: int | None = Field(
        default=None,
        ge=1,
        le=3650,
        description="有效天数（从创建时起），None = 永不过期",
    )

    @field_validator("scopes")
    @classmethod
    def validate_scopes(cls, v: str) -> str:
        allowed = {"read", "write", "admin"}
        parts = [s.strip() for s in v.split(",") if s.strip()]
        if not parts:
            raise ValueError("scopes 不能为空")
        bad = [p for p in parts if p not in allowed]
        if bad:
            raise ValueError(f"无效的 scope: {bad}，允许值为 read/write/admin")
        return ",".join(parts)


# ---------------------------------------------------------------------------
# 响应模型
# ---------------------------------------------------------------------------


class ApiKeyCreateResponse(BaseModel):
    """创建成功后返回——含一次性明文密钥。"""

    id: int
    name: str
    key_prefix: str
    scopes: str
    rate_limit_per_min: int
    expires_at: datetime | None
    created_at: datetime
    plaintext_key: str = Field(description="完整 API Key，仅此一次展示，请立即保存")


class ApiKeyResponse(BaseModel):
    """列表 / 详情响应——不含明文密钥。"""

    id: int
    name: str
    key_prefix: str
    scopes: str
    rate_limit_per_min: int
    last_used_at: datetime | None
    expires_at: datetime | None
    revoked_at: datetime | None
    created_at: datetime

    @property
    def is_active(self) -> bool:
        if self.revoked_at is not None:
            return False
        if self.expires_at is not None:
            now = datetime.now(UTC)
            exp = self.expires_at
            if exp.tzinfo is None:
                exp = exp.replace(tzinfo=UTC)
            return now <= exp
        return True


class ApiKeyListResponse(BaseModel):
    """分页列表响应。"""

    total: int
    items: list[ApiKeyResponse]
