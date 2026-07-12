from __future__ import annotations

import logging

from fastapi import FastAPI

from app.app_assembly import assemble_app
from constants import API_VERSION


def create_app(*, logger: logging.Logger, lifespan, app_start_time: float) -> FastAPI:
    app = FastAPI(
        title="BaZi v8.0",
        version=API_VERSION,
        lifespan=lifespan,
        docs_url=None,
        redoc_url=None,
    )
    return assemble_app(app, logger=logger, app_start_time=app_start_time)
