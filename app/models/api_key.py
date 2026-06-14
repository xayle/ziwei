"""
app/models/api_key.py — API Key 模型

API Key 生命周期：
  • 创建：生成 `zw_<32位随机hex>` 明文密钥，只展示一次；
          存储 SHA-256(key) 哈希 + prefix（前12字符，用于列表显示）。
  • 鉴权：每次请求时 SHA-256(Bearer token) 与 key_hash 对比，O(n) 扫描。
  • 撤销：设置 revoked_at，不物理删除。
  • 过期：可选 expires_at，鉴权时同步检查。
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import ClassVar

from sqlalchemy import Index
from sqlmodel import Field, SQLModel


class ApiKey(SQLModel, table=True):
    __tablename__: ClassVar[str] = "api_keys"
    __table_args__ = (
        Index("idx_api_keys_hash", "key_hash"),
        Index("idx_api_keys_user_id", "user_id"),
    )

    id: int | None = Field(default=None, primary_key=True)

    # 关联用户（拥有者）
    user_id: int = Field(foreign_key="users.id", index=True)

    # 展示用名称（用户自定义）
    name: str = Field(max_length=64)

    # SHA-256(plaintext_key) — 鉴权比对
    key_hash: str = Field(unique=True, max_length=64)

    # 前缀用于列表显示，如 "zw_a1b2c3d4…"
    key_prefix: str = Field(max_length=16)

    # 权限范围，逗号分隔：read / write / admin
    scopes: str = Field(default="read", max_length=128)

    # 每分钟请求上限（0 = 继承全局限制）
    rate_limit_per_min: int = Field(default=60)

    # 最后使用时间（异步更新，允许稍有延迟）
    last_used_at: datetime | None = Field(default=None)

    # 过期时间（None = 永不过期）
    expires_at: datetime | None = Field(default=None)

    # 撤销时间（None = 未撤销）
    revoked_at: datetime | None = Field(default=None)

    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
