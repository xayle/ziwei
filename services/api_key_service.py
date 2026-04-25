"""
services/api_key_service.py — API Key 生成、哈希与鉴权

公开接口：
    generate_key()        → (plaintext: str, prefix: str, key_hash: str)
    hash_key(key: str)    → str  (SHA-256 hex 摘要)
    verify_key(key, hash) → bool
    authenticate_api_key(token, session) → ApiKey | None
"""
from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Session, select

from app.models.api_key import ApiKey

_PREFIX = "zw_"
_KEY_BYTES = 24   # 24 bytes → 48 hex chars；总长度 = 3 + 48 = 51 chars


def generate_key() -> tuple[str, str, str]:
    """
    生成一个新的 API key。

    Returns
    -------
    (plaintext, prefix, key_hash)
        plaintext : 完整密钥（仅展示一次，不存数据库）
        prefix    : 前 12 字符（含 "zw_" 前缀），用于列表展示
        key_hash  : SHA-256(plaintext) hex，存入数据库
    """
    raw = secrets.token_hex(_KEY_BYTES)
    plain: str = _PREFIX + raw
    prefix: str = plain[:12] + "…"
    return plain, prefix, hash_key(plain)


def hash_key(key: str) -> str:
    """返回 SHA-256(key) 的十六进制摘要（64字符）。"""
    return hashlib.sha256(key.encode()).hexdigest()


def verify_key(plaintext: str, stored_hash: str) -> bool:
    """安全比对（防时序攻击）。"""
    return secrets.compare_digest(hash_key(plaintext), stored_hash)


def authenticate_api_key(
    token: str,
    session: Session,
) -> Optional[ApiKey]:
    """
    从数据库中查找与 token 匹配的有效 ApiKey。

    有效条件：
      • key_hash 匹配
      • revoked_at 为 None
      • expires_at 为 None 或未过期
    """
    h = hash_key(token)
    key = session.exec(
        select(ApiKey).where(ApiKey.key_hash == h)
    ).first()
    if key is None:
        return None
    if key.revoked_at is not None:
        return None
    if key.expires_at is not None:
        now = datetime.now(timezone.utc)
        exp = key.expires_at
        # 兼容 naive datetime（SQLite 不保存 tz）
        if exp.tzinfo is None:
            exp = exp.replace(tzinfo=timezone.utc)
        if now > exp:
            return None
    return key
