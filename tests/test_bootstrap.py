from __future__ import annotations

from logging import getLogger
from unittest.mock import MagicMock, patch

from app.bootstrap import create_app
from constants import API_VERSION


def test_create_app_builds_fastapi_and_delegates_assembly():
    logger = getLogger("test")
    lifespan = MagicMock()
    assembled_app = MagicMock()

    with patch("app.bootstrap.FastAPI", return_value=assembled_app) as fastapi_cls, \
         patch("app.bootstrap.assemble_app", return_value=assembled_app) as assemble_app:
        result = create_app(logger=logger, lifespan=lifespan, app_start_time=123.0)

    fastapi_cls.assert_called_once_with(
        title="BaZi v8.0",
        version=API_VERSION,
        lifespan=lifespan,
        docs_url=None,
        redoc_url=None,
    )
    assemble_app.assert_called_once_with(assembled_app, logger=logger, app_start_time=123.0)
    assert result is assembled_app
