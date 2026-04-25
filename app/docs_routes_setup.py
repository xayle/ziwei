from __future__ import annotations

from fastapi import FastAPI
from fastapi.openapi.docs import get_redoc_html, get_swagger_ui_html
from fastapi.responses import HTMLResponse

from app.openapi_docs import setup_openapi_docs


def configure_docs_routes(app: FastAPI) -> None:
    setup_openapi_docs(app)

    @app.get("/docs", include_in_schema=False, response_class=HTMLResponse)
    async def custom_swagger_ui() -> HTMLResponse:
        return get_swagger_ui_html(
            openapi_url="/openapi.json",
            title="BaZi v8.0 - API Docs",
            swagger_js_url="/static/swagger-ui/swagger-ui-bundle.js",
            swagger_css_url="/static/swagger-ui/swagger-ui.css",
            swagger_favicon_url="/static/swagger-ui/favicon.png",
            oauth2_redirect_url="/static/swagger-ui/oauth2-redirect.html",
        )

    @app.get("/redoc", include_in_schema=False, response_class=HTMLResponse)
    async def custom_redoc() -> HTMLResponse:
        return get_redoc_html(
            openapi_url="/openapi.json",
            title="BaZi v8.0 - ReDoc",
            redoc_favicon_url="/static/swagger-ui/favicon.png",
        )
