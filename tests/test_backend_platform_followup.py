"""Backend platform follow-up tests (BE-P2/P3)."""

from __future__ import annotations

import json

import pytest
from sqlmodel import Session, select

from app.models import LiunianReportTask, User
from app.models.llm import LlmDraft
from services.liunian_report_service import create_liunian_task, task_to_response_dict
from services.llm_provenance import build_draft_evidence_refs
from services.quota_service import enforce_quota, reset_quota_counters, resolve_quota_tier
from services.structured_export_service import build_bazi_structured_export


@pytest.fixture(autouse=True)
def bypass_rate_limit(monkeypatch):
    monkeypatch.setenv("AUTH_BYPASS", "true")


def test_build_draft_evidence_refs_has_layer():
    refs = build_draft_evidence_refs(
        use_bazi_path=True,
        geju_name="正官格",
        yongshen_favor=["水", "木"],
        evidence_snippets=["《子平真诠》：官星清纯"],
    )
    assert refs
    assert all(r.get("layer") in {"classical", "engine", "heuristic"} for r in refs)


def test_structured_export_markdown():
    payload = {
        "pillars_primary": {
            "year": {"stem": "甲", "branch": "子"},
            "month": {"stem": "丙", "branch": "寅"},
            "day": {"stem": "戊", "branch": "午"},
            "hour": {"stem": "庚", "branch": "申"},
        },
        "geju": {"geju_name": "正官格", "geju_level": "正格"},
        "yongshen": {"favor": ["水"], "avoid": ["火"]},
        "shensha_summary": {"items": [{"name": "天乙贵人"}]},
    }
    out = build_bazi_structured_export(payload)
    assert out["format"] == "bazi_structured@1.0"
    assert "正官格" in out["markdown"]
    assert out["json"]["geju"]["geju_name"] == "正官格"


def test_liunian_task_db_persistence(db_session, test_case, test_user):
    task = create_liunian_task(
        db_session,
        case_id=test_case.id,
        user_id=test_user.id,
        year=2026,
        include_months=False,
    )
    loaded = db_session.get(LiunianReportTask, task.id)
    assert loaded is not None
    assert loaded.status == "queued"
    resp = task_to_response_dict(loaded)
    assert resp["task_id"] == task.id


def test_quota_tier_pro_when_auth_bypass(monkeypatch):
    monkeypatch.setenv("AUTH_BYPASS", "true")
    reset_quota_counters()

    class _Client:
        host = "127.0.0.1"

    class _Req:
        state = type("S", (), {"user": None})()
        client = _Client()

    enforce_quota(_Req(), "batch")


def test_bazi_structured_text_endpoint(client):
    resp = client.post(
        "/api/v1/bazi/structured-text",
        json={
            "dt": "1990-01-15T08:00:00+08:00",
            "lon": 121.47,
            "tz": "Asia/Shanghai",
            "gender": "male",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["format"] == "bazi_structured@1.0"
    assert "markdown" in data and "json" in data


def test_notifications_subscribe_stub(client_with_auth):
    resp = client_with_auth.post(
        "/api/v1/notifications/subscribe",
        json={"channel": "email", "event_type": "dayun_transition"},
    )
    assert resp.status_code == 201
    assert resp.json()["status"] == "stub_active"


def test_seed_data_script_runs(db_session):
    from scripts.seed_data import _ensure_admin

    admin = _ensure_admin(db_session)
    assert admin.username == "admin"
    again = _ensure_admin(db_session)
    assert again.id == admin.id


def test_llm_draft_evidence_refs_roundtrip(db_session):
    refs = [{"layer": "classical", "field": "geju_name", "value": "正官格"}]
    draft = LlmDraft(
        chart_hash="hash-test-001",
        draft_text="测试草稿",
        evidence_refs_json=json.dumps(refs, ensure_ascii=False),
    )
    db_session.add(draft)
    db_session.commit()
    db_session.refresh(draft)
    loaded = db_session.exec(select(LlmDraft).where(LlmDraft.chart_hash == "hash-test-001")).first()
    assert loaded and loaded.evidence_refs_json
    assert json.loads(loaded.evidence_refs_json)[0]["layer"] == "classical"
