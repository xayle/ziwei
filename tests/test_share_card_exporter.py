"""Tests for share card PNG export (BE-T01)."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest


@pytest.fixture(autouse=True)
def bypass_rate_limit(monkeypatch):
    monkeypatch.setenv("AUTH_BYPASS", "true")


def test_share_card_exporter_returns_png(client_with_auth, test_case):
    dummy_png = b"\x89PNG\r\n\x1a\nfake"
    with patch("services.pdf_exporter.generate_share_card", new=AsyncMock(return_value=dummy_png)):
        resp = client_with_auth.get(f"/api/v1/cases/{test_case.id}/export/card")
    assert resp.status_code == 200
    assert resp.headers.get("content-type", "").startswith("image/png")
    assert resp.content == dummy_png


def test_share_card_exporter_404_unknown_case(client_with_auth):
    resp = client_with_auth.get("/api/v1/cases/nonexistent-case-id/export/card")
    assert resp.status_code == 404
