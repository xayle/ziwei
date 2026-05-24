from __future__ import annotations

from collections.abc import AsyncIterator, Callable
import contextlib
import logging
import os
import time

from fastapi import FastAPI

from db import init_db

APP_START_TIME: float = time.time()

_WEAK_KEYS = {
    "your-secret-key-change-in-production",
    "dev-secret-key",
    "secret",
    "changeme",
    "",
}


def create_lifespan(logger: logging.Logger) -> Callable[[FastAPI], AsyncIterator[None]]:
    @contextlib.asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        _ = app

        secret = os.environ.get("SECRET_KEY", "")
        if not secret or secret in _WEAK_KEYS:
            raise RuntimeError(
                "[STARTUP] SECRET_KEY 未设置或使用了默认弱密钥！"
                "请在 .env 中配置强随机密钥，可用："
                "python -c \"import secrets; print(secrets.token_urlsafe(32))\" 生成"
            )

        environment = os.environ.get("ENVIRONMENT", "development")
        if environment == "production" and os.environ.get("AUTH_BYPASS", "false").lower() == "true":
            raise RuntimeError("[STARTUP] 生产环境严禁开启 AUTH_BYPASS=true！")

        logger.info(
            "[STARTUP] 安全检查通过 (env=%s, auth_bypass=%s)",
            environment,
            os.environ.get("AUTH_BYPASS", "false"),
        )

        init_db()
        logger.info("[STARTUP] 数据库初始化完成")

        try:
            from sqlmodel import Session as _Session

            from db import get_engine
            from services.auth_service import load_revoked_jtis_from_db

            with _Session(get_engine()) as session:
                count = load_revoked_jtis_from_db(session)
                logger.info("[STARTUP] 已加载 %d 个 revoked JTI 到内存黑名单", count)
        except Exception as exc:  # pragma: no cover - 启动兼容分支
            logger.warning("[STARTUP] revoked JTI 加载失败（无阻断）: %s", exc)

        backup_scheduler = None
        try:
            from services.db_backup import schedule_backup

            backup_scheduler = schedule_backup()
            logger.info("[STARTUP] 数据库定时备份已启动（每日 03:00）")
        except Exception as exc:  # pragma: no cover - 启动兼容分支
            logger.warning("[STARTUP] 数据库定时备份注册失败（无阻断）: %s", exc)

        if backup_scheduler is not None:
            try:
                from sqlmodel import Session as _DelegSession

                from db import get_engine as _get_engine_o12
                from services.permission_cascade_service import auto_revoke_expired_delegations as _auto_revoke

                def _revoke_expired_delegations() -> None:
                    with _DelegSession(_get_engine_o12()) as session:
                        revoked = _auto_revoke(session)
                        session.commit()
                        if revoked:
                            logger.info("[O12] 自动撤销过期委托 %d 个", revoked)

                backup_scheduler.add_job(
                    _revoke_expired_delegations,
                    "interval",
                    hours=1,
                    id="expire_delegations",
                    replace_existing=True,
                )
                logger.info("[STARTUP] 委托过期清理任务已启动（每小时触发）")
            except Exception as exc:  # pragma: no cover - 启动兼容分支
                logger.warning("[STARTUP] 委托过期清理任务注册失败（无阻断）: %s", exc)

        yield

        if backup_scheduler is not None:
            try:
                backup_scheduler.shutdown(wait=False)
            except Exception:
                pass

    return lifespan