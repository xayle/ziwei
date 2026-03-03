"""
app/dependencies/permissions.py — 细粒度资源权限依赖（N3.04 + N3.05）

N3.04: require_resource_permission(resource_type, action) → Depends
N3.05: 独立 PermissionCache，与引擎 QueryCache 物理隔离，TTL=300s
"""
from __future__ import annotations

import time
from typing import Any, Callable, Optional

from fastapi import Depends
from sqlmodel import Session, select

from db import get_session
from app.models import User
from app.models.other import Delegation
from app.dependencies.auth import get_current_user
from app.exceptions import AuthorizationException, ErrorCode


# ══════════════════════════════════════════════════════════════════════════════
# N3.05 — 独立权限缓存（禁止与引擎 QueryCache 共用）
# ══════════════════════════════════════════════════════════════════════════════

class PermissionCache:
    """
    本地内存权限缓存。与引擎 QueryCache 物理隔离：
      - 引擎缓存清空不影响权限缓存
      - Cache key 空间不同，无命名冲突风险
    TTL 默认 300 秒（5 分钟）。
    """
    def __init__(self, ttl: int = 300) -> None:
        self._cache: dict[str, tuple[Any, float]] = {}
        self._ttl = ttl

    def get(self, key: str) -> Optional[Any]:
        """返回缓存值；已过期或不存在则返回 None。"""
        entry = self._cache.get(key)
        if entry is None:
            return None
        value, expire_at = entry
        if time.monotonic() > expire_at:
            del self._cache[key]
            return None
        return value

    def set(self, key: str, value: Any) -> None:
        """写入缓存，TTL 从当前时刻起算。"""
        self._cache[key] = (value, time.monotonic() + self._ttl)

    def invalidate(self, key: str) -> None:
        """主动删除缓存条目（approve/reject/revoke 后调用）。"""
        self._cache.pop(key, None)

    def invalidate_user(self, user_id: int) -> None:
        """删除该用户的所有权限缓存条目。"""
        prefix = f"perm:{user_id}:"
        keys = [k for k in self._cache if k.startswith(prefix)]
        for k in keys:
            self._cache.pop(k, None)


# 模块级单例—仅此文件可见，禁止跨模块复用
_permission_cache = PermissionCache(ttl=300)


def get_permission_cache() -> PermissionCache:
    """暴露给测试使用（不对外公开单例）。"""
    return _permission_cache


# ══════════════════════════════════════════════════════════════════════════════
# N3.04 — 细粒度资源权限依赖
# ══════════════════════════════════════════════════════════════════════════════

def require_resource_permission(
    resource_type: str,
    action: str,
) -> Callable:
    """
    工厂函数：返回检查细粒度资源权限的 FastAPI Depends。

    内部查询 Delegation 表 status='approved' 记录。
    先查缓存（TTL=5min），命中则跳过 DB 查询。

    用法：
        @router.get("/cases/{case_id}")
        def get_case(
            case_id: str,
            current_user: RequiredUser,
            _: None = Depends(require_resource_permission("case", "read")),
        ): ...
    """
    permission_type = f"{action}_{resource_type}"

    def _check(
        current_user: Optional[User] = Depends(get_current_user),
        session: Session = Depends(get_session),
    ) -> None:
        if current_user is None:
            raise AuthorizationException(
                code=ErrorCode.AUTHZ_PERMISSION_DENIED,
                message="Authentication required",
            )

        user_id = current_user.id or 0

        # 管理员直接放行
        if current_user.is_admin:
            return

        # 缓存 key
        cache_key = f"perm:{user_id}:{permission_type}"
        cached = _permission_cache.get(cache_key)
        if cached is True:
            return
        if cached is False:
            raise AuthorizationException(
                code=ErrorCode.AUTHZ_PERMISSION_DENIED,
                message=f"No approved permission: {permission_type}",
            )

        # 查 DB
        delegation = session.exec(
            select(Delegation).where(
                Delegation.to_user_id == user_id,
                Delegation.permission_type == permission_type,
                Delegation.status == "approved",
                Delegation.is_active.is_(True),  # type: ignore[union-attr]
                Delegation.deleted_at.is_(None),  # type: ignore[union-attr]
            )
        ).first()

        has_perm = delegation is not None
        _permission_cache.set(cache_key, has_perm)

        if not has_perm:
            raise AuthorizationException(
                code=ErrorCode.AUTHZ_PERMISSION_DENIED,
                message=f"No approved permission: {permission_type}",
            )

    return _check
