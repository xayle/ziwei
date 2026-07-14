"""T097 / BE-GTM-11：export/card?layout=douyin 9:16 分享卡。"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from services.pdf_exporter import (
    DOUYIN_CARD_HEIGHT,
    DOUYIN_CARD_WIDTH,
    render_douyin_share_card_html,
)


@pytest.fixture(autouse=True)
def bypass_rate_limit(monkeypatch):
    monkeypatch.setenv("AUTH_BYPASS", "true")


def test_douyin_share_card_html_is_9_16():
    html = render_douyin_share_card_html(
        brand="浮生",
        volume_title="卷一·命之根",
        fact_lines=["日主戊土，正官格透干。", "用神倾向：火、木。"],
        geju_line="正官格",
        disclaimer="传统文化与自我认知参考，非命运断言。",
        label="试读卡",
    )
    assert f"{DOUYIN_CARD_WIDTH}px" in html
    assert f"{DOUYIN_CARD_HEIGHT}px" in html
    assert DOUYIN_CARD_WIDTH / DOUYIN_CARD_HEIGHT == pytest.approx(9 / 16)
    assert "浮生" in html
    assert "卷一·命之根" in html
    assert "日主戊土" in html
    assert "非命运断言" in html
    # XSS escape
    evil = render_douyin_share_card_html(
        volume_title='<script>alert(1)</script>',
        fact_lines=['<img src=x onerror=1>'],
        disclaimer="ok",
    )
    assert "<script>" not in evil
    assert "&lt;script&gt;" in evil


def test_export_card_douyin_layout_passes_kwarg(client_with_auth, test_case):
    dummy_png = b"\x89PNG\r\n\x1a\ndouyin"
    with patch(
        "services.pdf_exporter.generate_share_card",
        new=AsyncMock(return_value=dummy_png),
    ) as mocked:
        resp = client_with_auth.get(
            f"/api/v1/cases/{test_case.id}/export/card",
            params={"layout": "douyin"},
        )
    assert resp.status_code == 200, resp.text
    assert resp.headers.get("content-type", "").startswith("image/png")
    assert resp.content == dummy_png
    assert "douyin" in (resp.headers.get("content-disposition") or "").lower()
    mocked.assert_awaited_once()
    assert mocked.await_args.kwargs.get("layout") == "douyin"


def test_export_card_invalid_layout_422(client_with_auth, test_case):
    resp = client_with_auth.get(
        f"/api/v1/cases/{test_case.id}/export/card",
        params={"layout": "tiktok"},
    )
    assert resp.status_code == 422


def test_export_card_default_still_works(client_with_auth, test_case):
    dummy_png = b"\x89PNG\r\n\x1a\ndefault"
    with patch(
        "services.pdf_exporter.generate_share_card",
        new=AsyncMock(return_value=dummy_png),
    ) as mocked:
        resp = client_with_auth.get(f"/api/v1/cases/{test_case.id}/export/card")
    assert resp.status_code == 200
    assert resp.content == dummy_png
    mocked.assert_awaited_once()
    assert mocked.await_args.kwargs.get("layout") == "default"
