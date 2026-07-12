from __future__ import annotations

import os
from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch

import pytest
from sqlmodel import Session

from app.dependencies.auth import _get_or_create_bypass_user
from app.models.case import Case, Snapshot


def _set_auth_bypass(enabled: bool) -> str | None:
    prev = os.environ.get("AUTH_BYPASS")
    if enabled:
        os.environ["AUTH_BYPASS"] = "true"
    else:
        os.environ.pop("AUTH_BYPASS", None)
    return prev


def _restore_auth_bypass(prev: str | None) -> None:
    if prev is None:
        os.environ.pop("AUTH_BYPASS", None)
    else:
        os.environ["AUTH_BYPASS"] = prev


def test_export_pdf_uses_new_pdf_generator(client, db_session: Session, test_user):
    prev = _set_auth_bypass(True)
    try:
        bypass_user = _get_or_create_bypass_user(db_session)
        case = Case(
            owner_id=bypass_user.id,
            name="张三",
            gender="male",
            birth_dt_local="1990-01-15T08:30:00",
            tz="Asia/Shanghai",
            lon=116.41,
            solar_time_enabled=True,
        )
        db_session.add(case)
        db_session.commit()
        db_session.refresh(case)

        snapshot = Snapshot(
            case_id=case.id,
            kind="bazi",
            output_json={"ok": True},
            api_version="1.0",
            rule_version="1.0",
            schema_version="1.0",
            created_at=datetime.now(UTC),
        )
        db_session.add(snapshot)
        db_session.commit()
        db_session.refresh(snapshot)

        dummy_pdf = b"%PDF-1.4\n%EOF"

        with patch("services.pdf_exporter.generate_pdf", new=AsyncMock(return_value=dummy_pdf)) as mocked:
            response = client.get(f"/api/v1/cases/{case.id}/export/pdf")

        assert response.status_code == 200
        assert response.headers["content-type"].startswith("application/pdf")
        assert 'filename*=UTF-8\'\'' in response.headers["content-disposition"]
        assert response.content == dummy_pdf
        mocked.assert_awaited_once()
        call_args = mocked.await_args.args
        assert call_args[0].id == case.id
        assert isinstance(call_args[1], Snapshot)
        assert call_args[1].id == snapshot.id
    finally:
        _restore_auth_bypass(prev)


def test_export_case_json_includes_archive_fields(client, db_session: Session, test_user):
    prev = _set_auth_bypass(True)
    try:
        bypass_user = _get_or_create_bypass_user(db_session)
        case = Case(
            owner_id=bypass_user.id,
            name="张三",
            gender="male",
            birth_dt_local="1990-01-15T08:30:00",
            tz="Asia/Shanghai",
            lon=116.41,
            current_city="北京",
            current_province="北京市",
            current_lon=116.41,
            current_tz="Asia/Shanghai",
            calendar_mode="lunar",
            is_leap_month=True,
            birth_time_precision="hour",
            unknown_time_fallback="noon",
            solar_time_enabled=True,
        )
        db_session.add(case)
        db_session.commit()
        db_session.refresh(case)

        snapshot = Snapshot(
            case_id=case.id,
            kind="bazi",
            output_json={"ok": True},
            api_version="1.0",
            rule_version="1.0",
            schema_version="1.0",
            created_at=datetime.now(UTC),
        )
        db_session.add(snapshot)
        db_session.commit()

        response = client.get(f"/api/v1/cases/{case.id}/export")

        assert response.status_code == 200
        payload = response.json()
        input_snapshot = payload["input_snapshot"]
        assert input_snapshot["current_city"] == "北京"
        assert input_snapshot["current_province"] == "北京市"
        assert input_snapshot["current_lon"] == 116.41
        assert input_snapshot["current_tz"] == "Asia/Shanghai"
        assert input_snapshot["calendar_mode"] == "lunar"
        assert input_snapshot["is_leap_month"] is True
        assert input_snapshot["birth_time_precision"] == "hour"
        assert input_snapshot["unknown_time_fallback"] == "noon"
    finally:
        _restore_auth_bypass(prev)


def test_export_case_card_uses_utf8_content_disposition(client, db_session: Session, test_user):
    pytest.skip("legacy share card export removed; use fusheng report PDF instead")
    prev = _set_auth_bypass(True)
    try:
        bypass_user = _get_or_create_bypass_user(db_session)
        case = Case(
            owner_id=bypass_user.id,
            name="张三",
            gender="male",
            birth_dt_local="1990-01-15T08:30:00",
            tz="Asia/Shanghai",
            lon=116.41,
        )
        db_session.add(case)
        db_session.commit()
        db_session.refresh(case)

        snapshot = Snapshot(
            case_id=case.id,
            kind="bazi",
            output_json={"ok": True},
            api_version="1.0",
            rule_version="1.0",
            schema_version="1.0",
            created_at=datetime.now(UTC),
        )
        db_session.add(snapshot)
        db_session.commit()

        dummy_png = b"\x89PNG\r\n\x1a\n"

        with patch("services.pdf_exporter.generate_share_card", new=AsyncMock(return_value=dummy_png)):
            response = client.get(f"/api/v1/cases/{case.id}/export/card")

        assert response.status_code == 200
        assert response.headers["content-type"].startswith("image/png")
        assert 'filename*=UTF-8\'' in response.headers["content-disposition"]
        assert response.content == dummy_png
    finally:
        _restore_auth_bypass(prev)
