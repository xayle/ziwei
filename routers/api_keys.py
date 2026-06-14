"""
routers/api_keys.py — §12 API Key 管理端点

端点列表：
    POST   /api/v1/api-keys          — 创建新 Key（仅当前用户）
    GET    /api/v1/api-keys          — 列出当前用户所有 Key（含已撤销）
    GET    /api/v1/api-keys/{key_id} — 查看单个 Key 详情
    DELETE /api/v1/api-keys/{key_id} — 撤销 Key（软撤销，设 revoked_at）
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from app.dependencies.auth import RequiredUser
from app.models.api_key import ApiKey
from app.schemas.api_key import (
    ApiKeyCreate,
    ApiKeyCreateResponse,
    ApiKeyListResponse,
    ApiKeyResponse,
)
from db import get_session
from services.api_key_service import generate_key

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/api-keys",
    tags=["API Key 管理"],
)

DbSession = Annotated[Session, Depends(get_session)]

# 每个用户最多持有多少个有效（未撤销）Key
_MAX_ACTIVE_KEYS_PER_USER = 20


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _get_key_or_404(
    key_id: int,
    user_id: int,
    session: Session,
) -> ApiKey:
    """查询 Key，不存在或不属于当前用户时抛 404。"""
    key = session.get(ApiKey, key_id)
    if key is None or key.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"API Key #{key_id} 不存在",
        )
    return key


def _to_response(key: ApiKey) -> ApiKeyResponse:
    return ApiKeyResponse(
        id=key.id,  # type: ignore[arg-type]
        name=key.name,
        key_prefix=key.key_prefix,
        scopes=key.scopes,
        rate_limit_per_min=key.rate_limit_per_min,
        last_used_at=key.last_used_at,
        expires_at=key.expires_at,
        revoked_at=key.revoked_at,
        created_at=key.created_at,
    )


# ---------------------------------------------------------------------------
# POST /api/v1/api-keys — 创建
# ---------------------------------------------------------------------------


@router.post(
    "",
    response_model=ApiKeyCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="创建 API Key",
    description=(
        "为当前登录用户生成一个新的 API Key。\n\n"
        "**⚠️ 注意**：完整密钥仅在响应的 `plaintext_key` 字段中出现一次，"
        "请立即保存。后续查询只显示前缀（如 `zw_a1b2c3d4…`）。"
    ),
)
def create_api_key(
    body: ApiKeyCreate,
    current_user: RequiredUser,
    session: DbSession,
) -> ApiKeyCreateResponse:
    # 限制每用户有效 Key 数量
    active_count = session.exec(
        select(ApiKey).where(
            ApiKey.user_id == current_user.id,
            ApiKey.revoked_at.is_(None),  # type: ignore[union-attr]
        )
    ).all()
    if len(active_count) >= _MAX_ACTIVE_KEYS_PER_USER:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"每个用户最多持有 {_MAX_ACTIVE_KEYS_PER_USER} 个有效 API Key，请先撤销不用的密钥",
        )

    plaintext, prefix, key_hash = generate_key()

    expires_at: datetime | None = None
    if body.expires_in_days is not None:
        expires_at = datetime.now(UTC) + timedelta(days=body.expires_in_days)

    assert current_user.id is not None
    api_key = ApiKey(
        user_id=current_user.id,
        name=body.name,
        key_hash=key_hash,
        key_prefix=prefix,
        scopes=body.scopes,
        rate_limit_per_min=body.rate_limit_per_min,
        expires_at=expires_at,
    )
    session.add(api_key)
    session.commit()
    session.refresh(api_key)

    logger.info(
        "API Key 已创建: id=%s user=%s name=%r scopes=%s",
        api_key.id,
        current_user.id,
        api_key.name,
        api_key.scopes,
    )

    return ApiKeyCreateResponse(
        id=api_key.id,  # type: ignore[arg-type]
        name=api_key.name,
        key_prefix=api_key.key_prefix,
        scopes=api_key.scopes,
        rate_limit_per_min=api_key.rate_limit_per_min,
        expires_at=api_key.expires_at,
        created_at=api_key.created_at,
        plaintext_key=plaintext,
    )


# ---------------------------------------------------------------------------
# GET /api/v1/api-keys — 列表
# ---------------------------------------------------------------------------


@router.get(
    "",
    response_model=ApiKeyListResponse,
    summary="列出我的 API Keys",
)
def list_api_keys(
    current_user: RequiredUser,
    session: DbSession,
    skip: int = 0,
    limit: int = 50,
) -> ApiKeyListResponse:
    all_keys = session.exec(
        select(ApiKey)
        .where(ApiKey.user_id == current_user.id)
        .order_by(ApiKey.created_at.desc())  # type: ignore[arg-type]
        .offset(skip)
        .limit(limit)
    ).all()

    total = session.exec(select(ApiKey).where(ApiKey.user_id == current_user.id))
    total_count = len(list(total))

    return ApiKeyListResponse(
        total=total_count,
        items=[_to_response(k) for k in all_keys],
    )


# ---------------------------------------------------------------------------
# GET /api/v1/api-keys/{key_id} — 详情
# ---------------------------------------------------------------------------


@router.get(
    "/{key_id}",
    response_model=ApiKeyResponse,
    summary="查看 API Key 详情",
)
def get_api_key(
    key_id: int,
    current_user: RequiredUser,
    session: DbSession,
) -> ApiKeyResponse:
    assert current_user.id is not None
    key = _get_key_or_404(key_id, current_user.id, session)
    return _to_response(key)


# ---------------------------------------------------------------------------
# DELETE /api/v1/api-keys/{key_id} — 撤销
# ---------------------------------------------------------------------------


@router.delete(
    "/{key_id}",
    status_code=status.HTTP_200_OK,
    summary="撤销 API Key",
    description="软撤销：设置 `revoked_at` 时间戳，不物理删除记录。撤销后该 Key 立即失效。",
)
def revoke_api_key(
    key_id: int,
    current_user: RequiredUser,
    session: DbSession,
) -> dict:
    assert current_user.id is not None
    key = _get_key_or_404(key_id, current_user.id, session)

    if key.revoked_at is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该 API Key 已被撤销",
        )

    key.revoked_at = datetime.now(UTC)
    session.add(key)
    session.commit()

    logger.info(
        "API Key 已撤销: id=%s user=%s name=%r",
        key.id,
        current_user.id,
        key.name,
    )

    return {"message": f"API Key #{key_id} 已撤销", "revoked_at": key.revoked_at.isoformat()}
