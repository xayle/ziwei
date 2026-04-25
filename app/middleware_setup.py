from __future__ import annotations

from typing import Callable

from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from starlette.requests import Request

from app.config import settings
from app.error_handling import ExceptionHandlingMiddleware
from services.request_validation import RequestValidationMiddleware


def configure_base_middlewares(
    app: FastAPI,
    limiter,
    rate_limit_handler: Callable[[Request, Exception], Response],
) -> None:
    app.add_middleware(ExceptionHandlingMiddleware)

    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, rate_limit_handler)
    app.add_middleware(SlowAPIMiddleware)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=settings.allow_credentials,
        allow_methods=settings.allow_methods,
        allow_headers=settings.allow_headers,
    )

    app.add_middleware(GZipMiddleware, minimum_size=1000)
    app.add_middleware(RequestValidationMiddleware)

    try:
        from services.slo_middleware import SLOMiddleware

        app.add_middleware(SLOMiddleware)
    except Exception:
        pass

    try:
        from services.sandbox_middleware import SandboxMiddleware

        app.add_middleware(SandboxMiddleware, sandbox_enabled=settings.sandbox_enabled)
    except Exception:
        pass
