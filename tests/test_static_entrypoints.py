from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.static_entrypoints import resolve_page_url
from app.static_routes_setup import configure_static_routes


def _make_client() -> TestClient:
    app = FastAPI()
    configure_static_routes(app)
    return TestClient(app)


client = _make_client()


class TestStaticEntrypoints:
    def test_resolve_page_url_prefers_spa_when_index_exists(self):
        with patch("app.static_entrypoints.spa_index_exists", return_value=True):
            assert resolve_page_url("bazi") == "/static/app/new/bazi"
            assert resolve_page_url("ziwei") == "/static/app/new/ziwei"
            assert resolve_page_url("cases") == "/static/app/"

    def test_resolve_page_url_falls_back_to_legacy_when_spa_missing(self):
        with patch("app.static_entrypoints.spa_index_exists", return_value=False), \
             patch("app.static_entrypoints.legacy_page_url", return_value="/static/bazi.html"):
            assert resolve_page_url("bazi") == "/static/bazi.html"

    def test_root_redirects_to_spa_when_index_exists(self):
        with patch("app.static_routes_setup.spa_index_exists", return_value=True), \
                patch("app.static_routes_setup.spa_entry_url", return_value="/static/app/"):
            resp = client.get("/", follow_redirects=False)
        assert resp.status_code == 302
        assert resp.headers["location"] == "/static/app/"

    def test_verify_redirects_to_legacy_when_spa_missing(self):
        with patch("app.static_routes_setup.spa_index_exists", return_value=False), \
             patch("app.static_routes_setup.legacy_page_path", return_value=Path("D:/fake/ziwei.html")), \
             patch("app.static_routes_setup.legacy_page_url", return_value="/static/ziwei.html"):
            resp = client.get("/verify", follow_redirects=False)
        assert resp.status_code == 301
        assert resp.headers["location"] == "/static/ziwei.html"

    def test_bazi_redirects_to_legacy_when_spa_missing(self):
        with patch("app.static_routes_setup.spa_index_exists", return_value=False), \
             patch("app.static_routes_setup.legacy_page_path", return_value=Path("D:/fake/bazi.html")), \
             patch("app.static_routes_setup.legacy_page_url", return_value="/static/bazi.html"):
            resp = client.get("/bazi", follow_redirects=False)
        assert resp.status_code == 301
        assert resp.headers["location"] == "/static/bazi.html"

    def test_bazi_redirects_to_spa_bazi_when_spa_exists(self):
        with patch("app.static_routes_setup.spa_index_exists", return_value=True), \
             patch("app.static_routes_setup.resolve_page_url", return_value="/static/app/new/bazi"):
            resp = client.get("/bazi", follow_redirects=False)
        assert resp.status_code == 301
        assert resp.headers["location"] == "/static/app/new/bazi"

    def test_ziwei_redirects_to_spa_ziwei_when_spa_exists(self):
        with patch("app.static_routes_setup.spa_index_exists", return_value=True), \
             patch("app.static_routes_setup.resolve_page_url", return_value="/static/app/new/ziwei"):
            resp = client.get("/ziwei", follow_redirects=False)
        assert resp.status_code == 301
        assert resp.headers["location"] == "/static/app/new/ziwei"

    def test_admin_redirects_to_legacy_when_spa_missing(self):
        with patch("app.static_routes_setup.spa_index_exists", return_value=False), \
             patch("app.static_routes_setup.legacy_page_path", return_value=Path("D:/fake/admin.html")), \
             patch("app.static_routes_setup.legacy_page_url", return_value="/static/admin.html"):
            resp = client.get("/admin", follow_redirects=False)
        assert resp.status_code == 301
        assert resp.headers["location"] == "/static/admin.html"
