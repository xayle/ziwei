from __future__ import annotations

from datetime import datetime
from uuid import uuid4

import pytest
from sqlmodel import Session

from app.models import Case, User
from routers.fusheng_archive import _case_to_bazi_request, _case_to_ziwei_request


def _make_case(**overrides) -> Case:
    base = {
        "id": str(uuid4()),
        "name": "Archive Case",
        "gender": "male",
        "birth_dt_local": "2000-01-01T12:00:00",
        "tz": "Asia/Shanghai",
        "lon": 121.47,
        "solar_time_enabled": False,
        "year_divide": "normal",
        "day_divide": "forward",
        "zi_day_rule": "early_zi_prev_day",
        "birth_time_precision": "hour",
        "is_leap_month": True,
        "ziwei_brightness_method": "zhongzhou",
        "ziwei_youbi_method": "hour",
        "ziwei_sihua_method": "zhongzhou",
        "ziwei_liunian_sihua_method": "life_palace_stem",
        "ziwei_kuiyue_method": "gengxin_mahu",
        "ziwei_tianma_method": "month",
        "ziwei_template_version": "pro",
    }
    base.update(overrides)
    return Case(**base)


def test_case_to_ziwei_request_maps_male_to_nan():
    case = _make_case(gender="male")
    dt = datetime(2000, 1, 1, 12, 0)
    req = _case_to_ziwei_request(case, dt)
    assert req.gender == "男"


def test_case_to_ziwei_request_maps_female_to_nv():
    case = _make_case(gender="female")
    dt = datetime(2000, 1, 1, 12, 0)
    req = _case_to_ziwei_request(case, dt)
    assert req.gender == "女"


def test_case_to_ziwei_request_aligns_algo_fields():
    case = _make_case(solar_time_enabled=True)
    dt = datetime(2000, 1, 1, 12, 30)
    req = _case_to_ziwei_request(case, dt)

    assert req.year_divide == "normal"
    assert req.day_divide == "forward"
    assert req.leap_month_method == "same"
    assert req.longitude == pytest.approx(121.47)
    assert req.brightness_method == "zhongzhou"
    assert req.youbi_method == "hour"
    assert req.liunian_sihua_method == "life_palace_stem"
    assert req.kuiyue_method == "gengxin_mahu"
    assert req.tianma_method == "month"
    assert req.template_version == "pro"
    assert req.sihua_stem_indices == {"庚": 1, "辛": 1}


def test_case_to_bazi_request_aligns_algo_fields():
    case = _make_case(gender="female")
    dt = datetime(2000, 1, 1, 12, 0)
    req = _case_to_bazi_request(case, dt)

    assert req.gender == "female"
    assert req.zi_day_rule == "early_zi_prev_day"
    assert req.birth_time_precision == "hour"
    assert req.include_liuri is True


def test_archive_bundle_returns_bazi_and_ziwei(client_with_auth, test_case):
    resp = client_with_auth.post(
        "/api/v1/fusheng/archive-bundle",
        json={"case_id": test_case.id, "include_ziwei": True},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["case_id"] == test_case.id
    assert data["bazi"]
    assert data["ziwei"]
    assert not any(m.startswith("ziwei_bundle:") for m in data["missing_fields"])


def test_archive_bundle_female_case(db_session: Session, test_user: User, client_with_auth):
    case = Case(
        id=str(uuid4()),
        name="Female Archive Case",
        gender="female",
        birth_dt_local="1990-05-15T08:30:00",
        tz="Asia/Shanghai",
        lon=116.41,
        owner_id=test_user.id,
    )
    db_session.add(case)
    db_session.commit()

    resp = client_with_auth.post(
        "/api/v1/fusheng/archive-bundle",
        json={"case_id": case.id},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["ziwei"] is not None
    assert data["ziwei"].get("summary") is not None or data["ziwei"].get("palaces")
