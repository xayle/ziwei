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
from services.rate_limit import limiter


def _build_rate_limit_handler() -> Callable[[Request, Exception], Response]:
    return cast(Callable[[Request, Exception], Response], _rate_limit_exceeded_handler)


def _configure_middlewares(app: FastAPI) -> None:
    rate_limit_handler = _build_rate_limit_handler()
    configure_base_middlewares(app, limiter, rate_limit_handler)
    configure_http_middlewares(app)


def _configure_routes(app: FastAPI) -> None:
    configure_static_routes(app)
    include_all_routers(app)


def _configure_observability(app: FastAPI, logger: logging.Logger, app_start_time: float) -> None:
    configure_health_routes(app, backend_status, app_start_time, logger)
    configure_metrics_routes(app, logger)


def assemble_app(app: FastAPI, *, logger: logging.Logger, app_start_time: float) -> FastAPI:
    _configure_middlewares(app)
    _configure_routes(app)
    _configure_observability(app, logger, app_start_time)
    return app
