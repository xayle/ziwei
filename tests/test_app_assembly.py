from __future__ import annotations

from logging import getLogger
from unittest.mock import patch

from fastapi import FastAPI

from app.app_assembly import assemble_app


def test_assemble_app_calls_sections_in_order():
    app = FastAPI()
    calls: list[str] = []

    def mark(name: str):
        def _mark(*args, **kwargs):
            calls.append(name)
            return None

        return _mark

    with patch("app.app_assembly.configure_base_middlewares", side_effect=mark("middlewares")), \
         patch("app.app_assembly.configure_http_middlewares", side_effect=mark("http")), \
         patch("app.app_assembly.configure_static_routes", side_effect=mark("static")), \
         patch("app.app_assembly.include_all_routers", side_effect=mark("routers")), \
         patch("app.app_assembly.configure_health_routes", side_effect=mark("health")), \
         patch("app.app_assembly.configure_metrics_routes", side_effect=mark("metrics")), \
         patch("app.app_assembly._build_rate_limit_handler", return_value=lambda *_args, **_kwargs: None):
        result = assemble_app(app, logger=getLogger("test"), app_start_time=123.0)

    assert result is app
    assert calls == ["middlewares", "http", "static", "routers", "health", "metrics"]
