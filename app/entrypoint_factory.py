from __future__ import annotations

import logging

from fastapi import FastAPI

from app.bootstrap import create_app
from app.docs_routes_setup import configure_docs_routes
from app.lifecycle import APP_START_TIME, create_lifespan


def create_application(*, logger: logging.Logger, app_start_time: float = APP_START_TIME) -> FastAPI:
    lifespan = create_lifespan(logger)
    app = create_app(logger=logger, lifespan=lifespan, app_start_time=app_start_time)
    configure_docs_routes(app)
    return app
