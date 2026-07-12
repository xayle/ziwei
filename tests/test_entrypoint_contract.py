from __future__ import annotations

import os

from fastapi.testclient import TestClient

os.environ.setdefault("SECRET_KEY", "test-secret-key-for-entrypoint-contract")

from run import app  # noqa: E402
from constants import API_VERSION  # noqa: E402


def test_run_app_exposes_key_operational_routes():
    client = TestClient(app, raise_server_exceptions=False)

    for path in ("/health", "/ready", "/docs", "/redoc", "/openapi.json", "/metrics"):
        response = client.get(path)
        assert response.status_code in (200, 403, 404, 500), path

    docs_html = client.get("/docs")
    assert docs_html.status_code == 200
    assert "swagger-ui" in docs_html.text.lower()

    redoc_html = client.get("/redoc")
    assert redoc_html.status_code == 200
    assert "redoc" in redoc_html.text.lower()

    openapi_json = client.get("/openapi.json")
    assert openapi_json.status_code == 200
    schema = openapi_json.json()
    assert schema["info"]["title"] == "BaZi v8.0"
    assert schema["info"]["version"] == API_VERSION


def test_run_app_routes_include_core_entrypoints():
    route_map = {}
    for route in app.routes:
        methods = getattr(route, "methods", None)
        if methods:
            route_map.setdefault(route.path, set()).update(methods)

    assert "GET" in route_map["/health"]
    assert "GET" in route_map["/ready"]
    assert "GET" in route_map["/docs"]
    assert "GET" in route_map["/redoc"]
    assert "GET" in route_map["/openapi.json"]
    assert "GET" in route_map["/metrics"]
    assert "GET" in route_map["/verify"]
    assert "POST" in route_map["/api/v1/verify"]
