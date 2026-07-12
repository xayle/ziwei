from __future__ import annotations

import asyncio
from logging import getLogger
from unittest.mock import MagicMock, patch

from app.lifecycle import _shutdown_backup_scheduler, create_lifespan


def test_shutdown_backup_scheduler_ignores_none():
    _shutdown_backup_scheduler(None)


def test_shutdown_backup_scheduler_calls_shutdown():
    scheduler = MagicMock()
    _shutdown_backup_scheduler(scheduler)
    scheduler.shutdown.assert_called_once_with(wait=False)


def test_create_lifespan_runs_startup_helpers():
    logger = getLogger("test")
    lifespan = create_lifespan(logger)
    app = MagicMock()

    with patch("app.lifecycle._validate_startup_env") as validate_env, \
         patch("app.lifecycle.init_db") as init_db, \
         patch("app.lifecycle._load_revoked_jtis") as load_jtis, \
         patch("app.lifecycle._start_backup_scheduler", return_value="scheduler") as start_scheduler, \
         patch("app.lifecycle._shutdown_backup_scheduler") as shutdown_scheduler:
        async def _run() -> None:
            async with lifespan(app):
                pass

        asyncio.run(_run())

    validate_env.assert_called_once()
    init_db.assert_called_once()
    load_jtis.assert_called_once_with(logger)
    start_scheduler.assert_called_once_with(logger)
    shutdown_scheduler.assert_called_once_with("scheduler")
