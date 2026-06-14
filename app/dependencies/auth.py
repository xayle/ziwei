"""Shared authentication and dependency injection."""

from __future__ import annotations

from datetime import UTC, datetime
import os
from typing import Annotated

from fastapi import Depends, Request
from sqlmodel import Session, select

from app.exceptions import AuthenticationException, ErrorCode
from app.models import User
from db import get_session
from services.auth_service import verify_token


def _auth_bypass_enabled() -> bool:
    """本地开发模式下跳过认证。

    由环境变量 AUTH_BYPASS 控制，默认关闭。
    开发测试时可在 .env 中设置 AUTH_BYPASS=true。
    生产环境严禁设为 true。
    """
    return os.getenv("AUTH_BYPASS", "false").lower() == "true"


def _local_dummy_user() -> User:
    """提供本地绕过认证时的占位用户。"""
    now = datetime.now(UTC)
    return User(
        id=0,
        username="local",
        email="local@example.com",
        password_hash="",
        is_active=True,
        role="owner",
        is_admin=True,
        created_at=now,
        updated_at=now,
    )


def _get_or_create_bypass_user(session: Session) -> User:
    """返回可持久化写入的本地 bypass 用户（不存在则自动创建）。"""
    # 优先读取已存在账号，避免重复创建
    existing = session.exec(
        select(User).where(
            User.username == "local_bypass",
            User.deleted_at.is_(None),  # type: ignore
        )
    ).first()
    if existing:
        if not existing.is_active:
            existing.is_active = True
            session.add(existing)
            session.commit()
            session.refresh(existing)
        return existing

    now = datetime.now(UTC)
    user = User(
        username="local_bypass",
        email="local_bypass@example.com",
        password_hash="",
        is_active=True,
        role="owner",
        is_admin=True,
        created_at=now,
        updated_at=now,
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def get_current_user(request: Request, session: Session = Depends(get_session)) -> User | None:
    """
    从Bearer token获取当前用户（可选认证）

    如果token无效或不存在，返回None。
    需要强制认证的端点应该使用 require_user 装饰器。

    Args:
        request: FastAPI Request
        session: 数据库连接

    Returns:
        User 对象或 None（如果未认证）
    """
    auth_header = request.headers.get("Authorization")

    # 绕过鉴权：仅当 Authorization header 缺失时才启用（有真实 JWT 则正常验证）
    if not auth_header:
        if _auth_bypass_enabled():
            try:
                return _get_or_create_bypass_user(session)
            except Exception:
                # 兜底：极端情况下（例如数据库瞬时不可用）仍返回内存用户，避免开发流程完全阻断
                return _local_dummy_user()
        return None

    try:
        scheme, token = auth_header.split()
        if scheme.lower() != "bearer":
            return None
    except ValueError:
        return None
    payload = verify_token(token)
    if not payload:
        return None

    # 从数据库获取完整用户对象
    user = session.exec(
        select(User).where(
            User.id == payload.user_id,
            User.deleted_at.is_(None),  # type: ignore
        )
    ).first()

    if not user or not user.is_active:
        return None

    return user


def require_user(user: User | None = Depends(get_current_user)) -> User:
    """
    强制认证的依赖函数。如果user为None，抛出401错误。

    用于需要认证的endpoint。

    Args:
        user: 从 get_current_user 获取

    Returns:
        User 对象

    Raises:
        AuthenticationException: 如果未认证
    """
    # user is None only when no auth header was provided (get_current_user returns None or dummy)
    # _local_dummy_user() has id=0 - that dummy is already returned by get_current_user when bypassing
    if user is None:
        raise AuthenticationException(
            code=ErrorCode.AUTH_MISSING_TOKEN,
            message="Authentication required",
        )
    return user


# 类型注解快捷方式
CurrentUser = Annotated[User | None, Depends(get_current_user)]
RequiredUser = Annotated[User, Depends(require_user)]
