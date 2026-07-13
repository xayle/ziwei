"""Tests for relation / multi_compat PDF export (HTML layer + API wiring)."""

from __future__ import annotations

from fastapi.testclient import TestClient
import pytest

from services.relation_pdf_service import render_multi_compat_html, render_relation_compat_html
from tests.test_relation_compat_contract import COUPLE_PAYLOAD

pytestmark = pytest.mark.usefixtures("_reset_cache")


@pytest.fixture(autouse=True)
def _reset_cache():
    from services.chart_snapshot_service import reset_snapshot_cache_for_tests

    reset_snapshot_cache_for_tests()
    yield
    reset_snapshot_cache_for_tests()


def test_relation_full_cite_layer_in_pdf_html(client: TestClient):
    resp = client.post("/api/v1/relation/full", json=COUPLE_PAYLOAD)
    assert resp.status_code == 200
    data = resp.json()
    html = render_relation_compat_html(data)
    cite_sections = (data.get("layers") or {}).get("cite", {}).get("sections") or []
    if cite_sections:
        assert "典籍引证" in html or "引经" in html


def test_render_relation_compat_html_contains_trust_fields():
    html = render_relation_compat_html(
        {
            "schema_version": "relation-compat@1.0",
            "request_id": "req-test",
            "relation_type": "couple",
            "relation_type_label": "情侣合盘",
            "combined_score": 72.5,
            "grade": "上",
            "summary": "整体匹配良好。",
            "person_a": {
                "label": "甲",
                "pillars_primary": {"year": "甲子", "month": "乙丑", "day": "丙寅", "hour": "丁卯"},
                "life_palace_gz": "戊辰",
            },
            "person_b": {
                "label": "乙",
                "pillars_primary": {"year": "庚午", "month": "辛未", "day": "壬申", "hour": "癸酉"},
                "life_palace_gz": "己巳",
            },
            "dimensions": [
                {
                    "id": "day_branch",
                    "label": "日支",
                    "score": 12,
                    "max_score": 20,
                    "description": "相生",
                    "layer": "fact",
                    "engine": "bazi",
                }
            ],
            "disclaimer_block": {"text": "仅供观览，不构成决策建议。"},
            "timeline": [{"year": 2026, "label": "流年", "summary": "平稳", "risk_level": "低"}],
            "summary_cards": [{"id": "c1", "tone": "support", "text": "互补"}],
            "action_items": [{"id": "a1", "text": "多沟通", "priority": "P1"}],
            "bazi": {"score": 60.0, "max_score": 100},
            "ziwei": {"score": 71.0, "max_score": 100},
            "palace_cross": [
                {"pair_id": "p1", "a_palace": "命宫", "b_palace": "夫妻", "relation_tag": "合", "summary": "互见"}
            ],
        }
    )
    assert "relation-compat@1.0" in html
    assert "req-test" in html
    assert "维度评分" in html
    assert "格物" in html
    assert "双引擎" in html
    assert "仅供观览" in html
    assert "甲" in html and "乙" in html


def test_render_multi_compat_html_matrix():
    html = render_multi_compat_html(
        {
            "schema_version": "multi-compat@1.1",
            "request_id": "req-multi-test",
            "person_count": 2,
            "team_harmony_score": 66,
            "matrix": [[100, 66], [66, 100]],
            "pairs": [{"person_a_idx": 0, "person_b_idx": 1, "total_score": 66, "max_score": 100, "level": "中签"}],
        },
        labels=["黄", "路"],
    )
    assert "多人缘分矩阵" in html
    assert "黄" in html and "路" in html
    assert "66" in html
    assert "multi-compat@1.1" in html
    assert "req-multi-test" in html
    assert "@page" in html
    assert "counter(page)" in html


def test_relation_export_png_endpoint(client: TestClient, monkeypatch: pytest.MonkeyPatch):
    dummy_png = b"\x89PNG\r\n\x1a\nfake"

    async def _fake_png(payload: dict) -> bytes:
        assert payload.get("relation_type") == "couple"
        return dummy_png

    monkeypatch.setattr("routers.relation_compat.generate_relation_share_card", _fake_png)

    resp = client.post("/api/v1/relation/export/png", json=COUPLE_PAYLOAD)
    assert resp.status_code == 200, resp.text
    assert resp.headers.get("content-type", "").startswith("image/png")
    assert resp.content == dummy_png


def test_relation_export_pdf_endpoint(client: TestClient, monkeypatch: pytest.MonkeyPatch):
    async def _fake_pdf(html: str) -> bytes:
        assert "relation-compat@1.0" in html
        assert COUPLE_PAYLOAD["person_a"]["label"] in html
        return b"%PDF-1.4 fake"

    monkeypatch.setattr("services.pdf_exporter.render_html_to_pdf", _fake_pdf)

    resp = client.post("/api/v1/relation/export/pdf", json=COUPLE_PAYLOAD)
    assert resp.status_code == 200, resp.text
    assert resp.headers.get("content-type", "").startswith("application/pdf")
    assert resp.content.startswith(b"%PDF")


def test_multi_compat_export_pdf_endpoint(client: TestClient, monkeypatch: pytest.MonkeyPatch):
    import re

    async def _fake_pdf(html: str) -> bytes:
        assert "多人缘分矩阵" in html
        assert "multi-compat@" in html
        assert re.search(r"[0-9a-f]{8}-[0-9a-f]{4}-", html), "PDF meta should include request_id UUID"
        return b"%PDF-1.4 multi"

    monkeypatch.setattr("services.pdf_exporter.render_html_to_pdf", _fake_pdf)

    payload = {
        "person_list": [
            {
                "year": 1990,
                "month": 7,
                "day": 17,
                "hour": 12,
                "minute": 25,
                "gender": "女",
            },
            {
                "year": 1990,
                "month": 6,
                "day": 17,
                "hour": 20,
                "minute": 15,
                "gender": "男",
            },
        ]
    }
    resp = client.post("/api/v1/ziwei/multi_compat/export/pdf", json=payload)
    assert resp.status_code == 200, resp.text
    assert resp.content.startswith(b"%PDF")
