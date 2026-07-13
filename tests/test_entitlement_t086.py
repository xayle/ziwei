"""T086 · BE-GTM-05 entitlement model tests."""

from __future__ import annotations

import pytest
from fastapi import HTTPException

from services.quota_service import (
    build_entitlement_info,
    enforce_entitlement,
    entitlement_satisfies,
    is_volume_unlocked,
    resolve_entitlement,
    unlocked_volume_ids,
)


class _User:
    def __init__(self, *, entitlement="free", role="editor", is_admin=False, id=1):
        self.entitlement = entitlement
        self.role = role
        self.is_admin = is_admin
        self.id = id


class _Req:
    def __init__(self, user=None):
        self.state = type("S", (), {"user": user})()


def test_resolve_entitlement_defaults_free(monkeypatch):
    monkeypatch.delenv("AUTH_BYPASS", raising=False)
    assert resolve_entitlement(request=_Req()) == "free"
    assert resolve_entitlement(user=_User()) == "free"


def test_resolve_entitlement_from_user_field(monkeypatch):
    monkeypatch.delenv("AUTH_BYPASS", raising=False)
    assert resolve_entitlement(user=_User(entitlement="volume_pass")) == "volume_pass"
    assert resolve_entitlement(user=_User(entitlement="full_book")) == "full_book"
    assert resolve_entitlement(user=_User(entitlement="bogus")) == "free"


def test_resolve_entitlement_admin_and_bypass(monkeypatch):
    monkeypatch.delenv("AUTH_BYPASS", raising=False)
    assert resolve_entitlement(user=_User(is_admin=True)) == "full_book"
    assert resolve_entitlement(user=_User(role="owner")) == "full_book"
    monkeypatch.setenv("AUTH_BYPASS", "true")
    assert resolve_entitlement(user=_User(entitlement="free")) == "full_book"


def test_volume_unlock_q2_map():
    assert is_volume_unlocked("free", "preface")
    assert is_volume_unlocked("free", "vol1")
    assert not is_volume_unlocked("free", "vol2")
    assert is_volume_unlocked("volume_pass", "vol4")
    assert not is_volume_unlocked("volume_pass", "vol5")
    assert is_volume_unlocked("full_book", "vol6")
    assert is_volume_unlocked("free", "colophon")


def test_entitlement_satisfies_rank():
    assert entitlement_satisfies("full_book", "free")
    assert entitlement_satisfies("volume_pass", "free")
    assert not entitlement_satisfies("free", "volume_pass")


def test_enforce_entitlement_middleware(monkeypatch):
    monkeypatch.delenv("AUTH_BYPASS", raising=False)
    req = _Req(_User(entitlement="free"))
    with pytest.raises(HTTPException) as exc:
        enforce_entitlement(req, "volume_pass")
    assert exc.value.status_code == 403

    assert enforce_entitlement(_Req(_User(entitlement="volume_pass")), "volume_pass") == "volume_pass"


def test_build_entitlement_info_lists_volumes(monkeypatch):
    monkeypatch.delenv("AUTH_BYPASS", raising=False)
    info = build_entitlement_info(user=_User(entitlement="volume_pass"))
    assert info.tier == "volume_pass"
    assert "vol1" in info.unlocked_volume_ids
    assert "vol3" in info.unlocked_volume_ids
    assert "vol5" not in info.unlocked_volume_ids
    free_ids = unlocked_volume_ids("free")
    assert free_ids == ["preface", "vol1", "colophon"]


def test_auth_me_includes_entitlement(client_with_auth):
    resp = client_with_auth.get("/api/v1/auth/me")
    assert resp.status_code == 200
    data = resp.json()
    assert data["entitlement"] in {"free", "volume_pass", "full_book"}
    assert data["entitlement_info"]["schema_version"] == "entitlement@1.0"
    assert isinstance(data["entitlement_info"]["unlocked_volume_ids"], list)
