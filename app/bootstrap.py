from __future__ import annotations

from collections.abc import Callable
import logging
from typing import cast

from fastapi import FastAPI, Request, Response
from slowapi import _rate_limit_exceeded_handler

from app.health_routes_setup import configure_health_routes
from app.http_middleware_setup import configure_http_middlewares
from app.metrics_routes_setup import configure_metrics_routes
from app.middleware_setup import configure_base_middlewares
from app.pkg_utils import backend_status
from app.router_setup import include_all_routers
from app.static_routes_setup import configure_static_routes
from constants import API_VERSION
from services.rate_limit import limiter


def create_app(*, logger: logging.Logger, lifespan, app_start_time: float) -> FastAPI:
    app = FastAPI(
        title="BaZi v8.0",
        version=API_VERSION,
        lifespan=lifespan,
        docs_url=None,
        redoc_url=None,
    )

    rate_limit_handler: Callable[[Request, Exception], Response] = cast(
        Callable[[Request, Exception], Response],
        _rate_limit_exceeded_handler,
    )
    configure_base_middlewares(app, limiter, rate_limit_handler)
    configure_http_middlewares(app)
    configure_static_routes(app)
    include_all_routers(app)
    configure_health_routes(app, backend_status, app_start_time, logger)
    configure_metrics_routes(app, logger)
    return app
