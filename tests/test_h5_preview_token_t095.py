"""T095 / BE-GTM-07：H5 短 token 免登录读卷一摘要。"""

from __future__ import annotations

import pytest

from app.schemas.disclaimer import DisclaimerBlockModel
from app.schemas.life_volume import (
    AnalysisBlockModel,
    ColophonModel,
    LifeVolumeModel,
    LifeVolumeResponseModel,
    VolumeSectionModel,
)
from services.auth_service import (
    H5_PREVIEW_SCOPE,
    create_access_token,
    create_h5_preview_token,
    verify_h5_preview_token,
    verify_token,
)
from services.chart_snapshot_service import reset_snapshot_cache_for_tests
from services.life_volume_service import project_h5_vol1_preview


def test_h5_preview_token_rejects_as_access_token():
    minted = create_h5_preview_token(user_id=1, case_id="case-a")
    with pytest.raises(Exception):
        verify_token(minted["access_token"])


def test_h5_preview_token_verify_roundtrip():
    minted = create_h5_preview_token(user_id=42, case_id="abc-case")
    assert minted["scope"] == H5_PREVIEW_SCOPE
    assert minted["expires_in"] > 0
    claims = verify_h5_preview_token(minted["access_token"])
    assert claims.user_id == 42
    assert claims.case_id == "abc-case"
    assert claims.scope == H5_PREVIEW_SCOPE


def test_h5_preview_token_rejects_wrong_use():
    access = create_access_token(1, "u")["access_token"]
    with pytest.raises(Exception):
        verify_h5_preview_token(access)


def test_project_h5_vol1_preview_keeps_only_preface_vol1():
    resp = LifeVolumeResponseModel(
        case_id="c1",
        chart_hash="h",
        disclaimer_block=DisclaimerBlockModel(text="免责", version="1"),
        volumes=[
            LifeVolumeModel(
                id="preface",
                title="卷首",
                sections=[
                    VolumeSectionModel(
                        id="p1",
                        heading="读法",
                        layer="fact",
                        blocks=[AnalysisBlockModel(text="x" * 400)],
                    )
                ],
            ),
            LifeVolumeModel(id="vol1", title="卷一", sections=[]),
            LifeVolumeModel(id="vol2", title="卷二", locked=True, sections=[]),
        ],
        colophon=ColophonModel(summary_lines=["a", "b", "c"]),
    )
    slim = project_h5_vol1_preview(resp)
    assert [v.id for v in slim.volumes] == ["preface", "vol1"]
    assert len(slim.volumes[0].sections[0].blocks[0].text) <= 200
    assert slim.relation_appendix is None
    assert slim.colophon.expandable is False


def test_mint_and_preview_without_login(client_with_auth, client, test_case, auth_headers):
    reset_snapshot_cache_for_tests()
    mint = client_with_auth.post(
        "/api/v1/auth/h5-preview-token",
        json={"case_id": test_case.id},
    )
    assert mint.status_code == 200, mint.text
    body = mint.json()
    assert body["case_id"] == test_case.id
    assert body["scope"] == H5_PREVIEW_SCOPE
    token = body["access_token"]

    guest_headers = {"Authorization": ""}

    bare = client.get(
        f"/api/v1/life/preview/{test_case.id}",
        params={"token": token},
        headers=guest_headers,
    )
    assert bare.status_code == 200, bare.text
    data = bare.json()
    ids = [v["id"] for v in data["volumes"]]
    assert ids == ["preface", "vol1"]
    assert "vol2" not in ids
    assert data["disclaimer_block"]["text"]

    bearer = client.get(
        f"/api/v1/life/preview/{test_case.id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert bearer.status_code == 200, bearer.text

    bad = client.get(
        "/api/v1/life/preview/other-case",
        params={"token": token},
        headers=guest_headers,
    )
    assert bad.status_code == 403

    missing = client.get(f"/api/v1/life/preview/{test_case.id}", headers=guest_headers)
    assert missing.status_code == 401

    login_tok = auth_headers["Authorization"].split()[1]
    wrong = client.get(
        f"/api/v1/life/preview/{test_case.id}",
        params={"token": login_tok},
        headers=guest_headers,
    )
    assert wrong.status_code == 401


def test_mint_rejects_foreign_case(client_with_auth):
    resp = client_with_auth.post(
        "/api/v1/auth/h5-preview-token",
        json={"case_id": "nonexistent-case"},
    )
    assert resp.status_code in (404, 422, 400)
