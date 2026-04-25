from __future__ import annotations

from fastapi import FastAPI
from starlette.requests import Request

from services.prometheus_monitoring import prometheus_middleware


def configure_http_middlewares(app: FastAPI) -> None:
    @app.middleware("http")
    async def monitoring_middleware(request: Request, call_next):
        """Prometheus 性能监控中间件"""
        return await prometheus_middleware(request, call_next)

    @app.middleware("http")
    async def add_v1_deprecation_headers(request: Request, call_next):
        """对所有 /api/v1/* 响应追加废弃声明头（R45）."""
        response = await call_next(request)
        if request.url.path.startswith("/api/v1/"):
            response.headers["Deprecation"] = "true"
            response.headers["Sunset"] = "2026-12-31"
            response.headers["Link"] = '<https://api.example.com/api/v2>; rel="successor-version"'
        return response

    @app.middleware("http")
    async def add_security_headers(request: Request, call_next):
        """添加安全响应头 - CSP, Cache-Control 等"""
        _req_path = request.url.path
        response = await call_next(request)

        _is_docs_path = _req_path in ("/docs", "/redoc", "/openapi.json")
        _is_static_html = (
            (_req_path.startswith("/static/") and _req_path.endswith(".html"))
            or _req_path in ("/dashboard", "/")
        )
        _is_spa_app = _req_path.startswith("/static/app/")
        if _is_docs_path or _is_static_html or _is_spa_app:
            response.headers["Content-Security-Policy"] = (
                "default-src 'self'; "
                "connect-src 'self'; "
                "style-src 'self' 'unsafe-inline'; "
                "script-src 'self' 'unsafe-inline'; "
                "img-src 'self' data:; "
                "font-src 'self'; "
                "object-src 'none'; "
                "frame-ancestors 'self';"
            )
        else:
            response.headers["Content-Security-Policy"] = (
                "default-src 'self'; "
                "connect-src 'self'; "
                "style-src 'self' 'unsafe-inline'; "
                "script-src 'self'; "
                "img-src 'self' data:; "
                "font-src 'self'; "
                "object-src 'none'; "
                "frame-ancestors 'self';"
            )

        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        if request.url.path == "/static/sw.js":
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
        elif _req_path in ["/", "/dashboard", "/verify"]:
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
            response.headers["Clear-Site-Data"] = '"cache"'
        elif _req_path.startswith("/static/") and _req_path.endswith(".html"):
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
            response.headers["Clear-Site-Data"] = '"cache"'
        elif _req_path.startswith("/static/"):
            response.headers["Cache-Control"] = "public, max-age=2592000, immutable"
        elif _req_path in ["/docs", "/redoc", "/openapi.json"]:
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
        elif _req_path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, private"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
        else:
            response.headers["Cache-Control"] = "public, max-age=86400"

        return response
