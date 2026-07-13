"""GET /life/snippets/{case_id} — T076 BOOK-GTM §5.3."""

from __future__ import annotations

from services.chart_snapshot_service import reset_snapshot_cache_for_tests
from services.life_snippets_service import build_hooks_from_bazi


def test_life_snippets_shape(client_with_auth, test_case):
    reset_snapshot_cache_for_tests()
    resp = client_with_auth.get(f"/api/v1/life/snippets/{test_case.id}")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["schema_version"] == "life-snippets@0.1"
    assert data["case_id"] == test_case.id
    assert 3 <= len(data["hooks"]) <= 5
    for hook in data["hooks"]:
        assert hook["tag"]
        assert hook["text"]
        assert len(hook["text"]) <= 80
        assert hook["layer"] in ("engine", "classical")
    assert data["vertical_title"]
    assert data["disclaimer"]


def test_life_snippets_limit(client_with_auth, test_case):
    reset_snapshot_cache_for_tests()
    resp = client_with_auth.get(f"/api/v1/life/snippets/{test_case.id}?limit=3")
    assert resp.status_code == 200
    assert len(resp.json()["hooks"]) == 3


def test_life_snippets_not_found(client_with_auth):
    resp = client_with_auth.get("/api/v1/life/snippets/nonexistent-case-id")
    assert resp.status_code == 404


def test_build_hooks_from_bazi_unit():
    hooks = build_hooks_from_bazi(
        {
            "pillars_primary": {"day": {"stem": "戊", "branch": "午"}},
            "geju": {
                "geju_name": "正官格",
                "classic_ref": "《子平真诠》：官格贵印。",
            },
            "yongshen": {"favor": ["earth", "fire"]},
            "liunian": {
                "items": [{"year": 2026, "stem": "丙", "branch": "午", "ten_god": "食神"}],
            },
        },
        limit=5,
    )
    assert 3 <= len(hooks) <= 5
    assert any(h.layer == "classical" for h in hooks)
    assert any("2026" in h.text for h in hooks)
