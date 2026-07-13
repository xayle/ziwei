"""Tests for relation explain batch (BE-R15) and case_resolver longitude."""

from __future__ import annotations

from fastapi.testclient import TestClient
import pytest

from services.chart_snapshot_service import reset_snapshot_cache_for_tests
from services.explain_relation import RELATION_SECTIONS, build_relation_section
from services.relation_engine.case_resolver import resolve_person_input
from tests.test_relation_compat_contract import COUPLE_PAYLOAD


@pytest.fixture(autouse=True)
def _reset_cache():
    reset_snapshot_cache_for_tests()
    yield
    reset_snapshot_cache_for_tests()


def test_relation_sections_registry():
    assert "relation_reading" in RELATION_SECTIONS


def test_build_relation_reading_section_layers():
    section = build_relation_section(
        {
            "relation_type": "couple",
            "relation_type_label": "情侣合盘",
            "combined_score": 72.5,
            "grade": "上",
            "summary": "综合 72.5 分（上）。有缘相聚。",
            "tensions": [{"code": "day_branch_clash", "message": "日支冲需重点调和。"}],
        },
        "relation_reading",
    )
    assert section.section_id == "relation_reading"
    layers = {b.layer for b in section.blocks}
    assert "fact" in layers
    assert "inference" in layers


def test_relation_explain_batch_endpoint(client: TestClient):
    payload = {**COUPLE_PAYLOAD, "sections": ["relation_reading"]}
    resp = client.post("/api/v1/relation/explain/batch", json=payload)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["chart_hash"].startswith("relation:couple:")
    assert len(data["sections"]) == 1
    assert data["sections"][0]["section_id"] == "relation_reading"
    assert len(data["sections"][0]["blocks"]) >= 2
    assert data.get("disclaimer_block", {}).get("text")


def test_relation_explain_batch_unknown_section(client: TestClient):
    payload = {**COUPLE_PAYLOAD, "sections": ["geju"]}
    resp = client.post("/api/v1/relation/explain/batch", json=payload)
    assert resp.status_code == 422


def test_resolve_person_longitude_override():
    person = resolve_person_input(
        {
            "birth_datetime": "1990-07-17T12:25:00",
            "longitude": 121.5,
            "tz": "Asia/Shanghai",
            "gender": "female",
            "label": "测试",
        },
        user=None,
        session=None,
        default_label="甲方",
    )
    assert person["longitude"] == 121.5
