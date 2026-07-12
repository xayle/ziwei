from __future__ import annotations

from logging import getLogger
from unittest.mock import MagicMock, patch

from app.entrypoint_factory import create_application


def test_create_application_wires_lifespan_app_and_docs():
    logger = getLogger("test")
    app = MagicMock()

    with patch("app.entrypoint_factory.create_lifespan", return_value="lifespan") as create_lifespan, \
         patch("app.entrypoint_factory.create_app", return_value=app) as create_app, \
         patch("app.entrypoint_factory.configure_docs_routes") as configure_docs_routes:
        result = create_application(logger=logger, app_start_time=123.0)

    create_lifespan.assert_called_once_with(logger)
    create_app.assert_called_once_with(logger=logger, lifespan="lifespan", app_start_time=123.0)
    configure_docs_routes.assert_called_once_with(app)
    assert result is app
