"""R086 P2 — relation_type template separation tests."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from services.chart_snapshot_service import reset_snapshot_cache_for_tests
from services.relation_engine.composer import compute_relation_full
from services.relation_engine.copy_templates import INFERENCE_HEADINGS
from services.relation_pdf_service import render_relation_compat_html, render_relation_share_card_html
from tests.test_relation_compat_contract import COUPLE_PAYLOAD

pytestmark = pytest.mark.usefixtures("_reset_cache")


@pytest.fixture(autouse=True)
def _reset_cache():
    reset_snapshot_cache_for_tests()
    yield
    reset_snapshot_cache_for_tests()


BIZ_PAYLOAD = {
    "relation_type": "business_partner",
    "person_a": {
        "birth_datetime": "1985-11-20T09:00:00",
        "tz": "Asia/Shanghai",
        "longitude": 121.47,
        "gender": "male",
        "label": "合伙人A",
    },
    "person_b": {
        "birth_datetime": "1988-02-14T16:00:00",
        "tz": "Asia/Shanghai",
        "longitude": 114.05,
        "gender": "male",
        "label": "合伙人B",
    },
    "options": {"include_bazi": True, "include_ziwei": True},
}


def _blob(data: dict) -> str:
    parts = [data.get("summary") or ""]
    for card in data.get("summary_cards") or []:
        parts.append(card.get("text") or "")
    for item in data.get("action_items") or []:
        parts.append(item.get("text") or "")
    for dim in data.get("dimensions") or []:
        parts.append(dim.get("description") or "")
    return " ".join(parts)


class TestRelationTypeTemplates:
    def test_couple_has_no_business_partner_copy(self, client: TestClient):
        resp = client.post("/api/v1/relation/full", json=COUPLE_PAYLOAD)
        assert resp.status_code == 200
        data = resp.json()
        blob = _blob(data)
        for word in ("合伙", "契约", "股权", "分红"):
            assert word not in blob
        assert data["meta"]["template_id"] == "couple"
        assert data["meta"]["inference_heading"] == INFERENCE_HEADINGS["couple"]

    def test_business_partner_has_dedicated_template(self, client: TestClient):
        resp = client.post("/api/v1/relation/full", json=BIZ_PAYLOAD)
        assert resp.status_code == 200
        data = resp.json()
        assert data["meta"]["template_id"] == "business_partner"
        assert data["meta"]["inference_heading"] == INFERENCE_HEADINGS["business_partner"]
        action_text = " ".join(i["text"] for i in data.get("action_items") or [])
        assert "契约" in action_text or "合伙" in (data.get("summary") or "")
        dim_ids = {d["id"] for d in data.get("dimensions") or []}
        assert "wealth_cross" in dim_ids

    def test_couple_pdf_uses_type_inference_heading(self):
        result = compute_relation_full(
            relation_type=COUPLE_PAYLOAD["relation_type"],
            person_a=COUPLE_PAYLOAD["person_a"],
            person_b=COUPLE_PAYLOAD["person_b"],
            options=COUPLE_PAYLOAD["options"],
        )
        html = render_relation_compat_html(result)
        assert INFERENCE_HEADINGS["couple"] in html
        assert "template:couple" in html
        for word in ("合伙", "契约"):
            assert word not in html

    def test_share_card_html_renders(self):
        result = compute_relation_full(
            relation_type=BIZ_PAYLOAD["relation_type"],
            person_a=BIZ_PAYLOAD["person_a"],
            person_b=BIZ_PAYLOAD["person_b"],
            options=BIZ_PAYLOAD["options"],
        )
        html = render_relation_share_card_html(result)
        assert "合作伙伴合盘" in html or "business_partner" in html
        assert "relation-compat@1.0" in html
        assert BIZ_PAYLOAD["person_a"]["label"] in html
