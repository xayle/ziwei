from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from app.models import Case
from services.case_chart_requests import case_to_ziwei_request
from services.case_fusheng_tags import case_late_zishi, parse_fusheng_tags


def _make_case(**overrides) -> Case:
    base = {
        "id": str(uuid4()),
        "name": "Tag Case",
        "gender": "male",
        "birth_dt_local": "2000-01-01T12:00:00",
        "tz": "Asia/Shanghai",
        "lon": 121.47,
    }
    base.update(overrides)
    return Case(**base)


def test_parse_fusheng_tags_late_zishi():
    meta = parse_fusheng_tags("fusheng,lz:0,zbm:zhongzhou")
    assert meta["late_zishi"] is False
    assert meta["ziwei_brightness_method"] == "zhongzhou"


def test_case_late_zishi_from_tags():
    case = _make_case(tags="fusheng,lz:0")
    assert case_late_zishi(case) is False


def test_case_to_ziwei_request_uses_tag_late_zishi():
    case = _make_case(tags="fusheng,lz:0")
    req = case_to_ziwei_request(case, datetime(2000, 1, 1, 23, 30))
    assert req.late_zishi is False
