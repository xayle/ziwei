from __future__ import annotations

import importlib.metadata
import importlib.util
import logging
from ipaddress import ip_address as _parse_ip
from ipaddress import ip_network as _parse_network
from typing import Callable, cast

from fastapi import FastAPI, Request, Response
from slowapi import _rate_limit_exceeded_handler

from constants import API_VERSION
from app.health_routes_setup import configure_health_routes
from app.http_middleware_setup import configure_http_middlewares
from app.middleware_setup import configure_base_middlewares
from app.router_setup import include_all_routers
from app.static_routes_setup import configure_static_routes
from services.rate_limit import limiter


_METRICS_ALLOWED_CIDRS = [
    _parse_network(net) for net in
    ("127.0.0.1/32", "10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16")
]


def is_metrics_allowed(client_host: str) -> bool:
    """允许 localhost + 私网段访问 /metrics。"""
    try:
        ip = _parse_ip(client_host)
        return any(ip in net for net in _METRICS_ALLOWED_CIDRS)
    except ValueError:
        return False


def backend_status(name: str) -> tuple[bool, str]:
    spec = importlib.util.find_spec(name)
    available = spec is not None
    version = "unavailable"
    if available:
        try:
            version = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            version = "unknown"
    return available, version


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
    return app