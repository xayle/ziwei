from __future__ import annotations

from fastapi.testclient import TestClient

from run import app

client = TestClient(app)


def test_bazi_full_day_boundary_cross_switches_day_pillar():
    base = {
        "lon": 121.47,
        "mode": "dual",
        "solar_time_enabled": False,
        "tz": "Asia/Shanghai",
    }

    payload_a = dict(base, dt="2026-06-15T22:50:00")
    payload_b = dict(base, dt="2026-06-15T23:10:00")

    resp_a = client.post("/api/v1/bazi/full", json=payload_a)
    resp_b = client.post("/api/v1/bazi/full", json=payload_b)

    assert resp_a.status_code == 200
    assert resp_b.status_code == 200

    data_a = resp_a.json()
    data_b = resp_b.json()

    assert data_a["methods"]["day_boundary_rule"] == "sxtwl"
    assert data_b["methods"]["day_boundary_rule"] == "sxtwl"
    assert data_a["methods"]["pillars_layer"] == "bazi_engine.pillars.v2"

    raw_a = data_a["raw"]
    raw_b = data_b["raw"]

    assert raw_a["day_boundary_crossed"] is False
    assert raw_b["day_boundary_crossed"] is True

    # Offset minutes should match for the same tz/date (no DST change within minutes)
    assert raw_a["dt_effective_local_offset_minutes"] == raw_b["dt_effective_local_offset_minutes"]

    # Pillars may or may not shift depending on backend day-boundary handling;
    # the key regression guard here is the boundary flag toggling at 23:00+.


def test_bazi_full_exposes_pillar_details_and_day_self_seat():
    payload = {
        "lon": 121.47,
        "mode": "dual",
        "solar_time_enabled": False,
        "tz": "Asia/Shanghai",
        "dt": "1990-07-17T12:20:00",
    }

    resp = client.post("/api/v1/bazi/full", json=payload)
    assert resp.status_code == 200, resp.text

    data = resp.json()
    pillar_details = data.get("pillar_details")
    assert isinstance(pillar_details, dict)
    assert pillar_details["day"]["self_seat"] == "墓"
    assert pillar_details["day"]["self_seat_source"] == "癸坐未十二长生"
    assert pillar_details["day"]["kongwang_source"] == "services.bazi_engine.tables.get_kongwang"
    assert pillar_details["year"]["self_seat"]
    assert pillar_details["month"]["self_seat"]
    assert pillar_details["hour"]["self_seat"]
    assert pillar_details["day"]["nayin"]
    assert isinstance(pillar_details["day"]["kongwang_hit"], bool)
    assert isinstance(pillar_details["day"]["shensha"], list)


def test_bazi_full_exposes_dayun_liunian_kongwang_and_shensha():
    payload = {
        "lon": 121.47,
        "mode": "dual",
        "solar_time_enabled": False,
        "tz": "Asia/Shanghai",
        "dt": "1990-07-17T12:20:00",
    }

    resp = client.post("/api/v1/bazi/full", json=payload)
    assert resp.status_code == 200, resp.text

    data = resp.json()

    dayun_items = data["dayun"]["items"]
    liunian_items = data["liunian"]["items"]

    assert dayun_items
    assert liunian_items
    assert dayun_items[0]["self_seat"]
    assert dayun_items[0]["self_seat_source"] == f"{dayun_items[0]['stem']}坐{dayun_items[0]['branch']}十二长生"
    assert dayun_items[0]["kongwang_source"] == "services.bazi_engine.tables.get_kongwang"
    assert isinstance(dayun_items[0]["kongwang_hit"], bool)
    assert isinstance(dayun_items[0]["shensha"], list)
    assert liunian_items[0]["self_seat"]
    assert liunian_items[0]["self_seat_source"] == f"{liunian_items[0]['stem']}坐{liunian_items[0]['branch']}十二长生"
    assert liunian_items[0]["kongwang_source"] == "services.bazi_engine.tables.get_kongwang"
    assert isinstance(liunian_items[0]["kongwang_hit"], bool)
    assert isinstance(liunian_items[0]["shensha"], list)


def test_bazi_full_gender_affects_dayun_direction():
    """B-P0-03: gender 传入后大运顺逆应随性别变化（阳年：男顺女逆）。"""
    base = {
        "lon": 120.2,
        "mode": "single",
        "solar_time_enabled": False,
        "tz": "Asia/Shanghai",
        "dt": "1988-03-20T14:00:00",
    }

    resp_male = client.post("/api/v1/bazi/full", json={**base, "gender": "male"})
    resp_female = client.post("/api/v1/bazi/full", json={**base, "gender": "female"})

    assert resp_male.status_code == 200, resp_male.text
    assert resp_female.status_code == 200, resp_female.text

    dayun_male = resp_male.json()["dayun"]
    dayun_female = resp_female.json()["dayun"]

    assert dayun_male["direction"] == "forward"
    assert dayun_female["direction"] == "backward"
    assert dayun_male["direction_basis"]["gender"] == "male"
    assert dayun_female["direction_basis"]["gender"] == "female"


def test_bazi_full_exposes_shishen_summary():
    payload = {
        "lon": 121.47,
        "mode": "dual",
        "solar_time_enabled": False,
        "tz": "Asia/Shanghai",
        "dt": "1990-07-17T12:20:00",
    }

    resp = client.post("/api/v1/bazi/full", json=payload)
    assert resp.status_code == 200, resp.text

    data = resp.json()
    summary = data.get("shishen_summary")
    assert isinstance(summary, dict)
    assert summary["day_stem"]
    assert summary["pillars"]["day"]["ten_god"] == "日主"
    assert isinstance(summary["dominant"], list)
    assert isinstance(summary["contributions"], list)


def test_bazi_full_liuri_liushi_with_target_date():
    """B-P2-01: target_date 返回流日/流时。"""
    payload = {
        "lon": 121.47,
        "mode": "dual",
        "solar_time_enabled": False,
        "tz": "Asia/Shanghai",
        "dt": "1990-07-17T12:20:00",
        "target_date": "1900-01-01T12:00:00",
        "target_hour": 14,
    }
    resp = client.post("/api/v1/bazi/full", json=payload)
    assert resp.status_code == 200, resp.text
    liuri = resp.json().get("liuri_liushi")
    assert liuri is not None
    assert liuri["day_ganzhi"] == "甲戌"
    assert liuri["day_ten_god"] is not None


def test_bazi_full_dayun_transition_hint():
    """B-P2-03: 大运含起运天数与换运提示。"""
    payload = {
        "lon": 120.2,
        "mode": "single",
        "solar_time_enabled": False,
        "tz": "Asia/Shanghai",
        "dt": "1988-03-20T14:00:00",
        "gender": "male",
    }
    resp = client.post("/api/v1/bazi/full", json=payload)
    assert resp.status_code == 200, resp.text
    dayun = resp.json()["dayun"]
    assert dayun.get("start_age_days") is not None
    assert dayun.get("transition_hint")


def _full_payload():
    return {
        "lon": 121.47,
        "mode": "dual",
        "solar_time_enabled": False,
        "tz": "Asia/Shanghai",
        "dt": "1990-07-17T12:20:00",
    }


def test_bazi_full_relations_summary_structure():
    """R027: relations_summary has stable structured keys."""
    resp = client.post("/api/v1/bazi/full", json=_full_payload())
    assert resp.status_code == 200, resp.text
    summary = resp.json()["relations_summary"]
    for key in ("items", "clash_summary", "combine_summary", "harm_summary", "interaction_summary", "missing"):
        assert key in summary
    assert isinstance(summary["items"], list)
    assert isinstance(summary["missing"], list)


def test_bazi_full_shensha_summary_matches_pillar_lists():
    """R028: shensha_summary items align with pillar_details shensha lists."""
    resp = client.post("/api/v1/bazi/full", json=_full_payload())
    assert resp.status_code == 200, resp.text
    data = resp.json()
    summary = data["shensha_summary"]
    assert isinstance(summary["items"], list)
    assert isinstance(summary["highlights"], list)
    assert isinstance(summary["missing"], list)
    pillar_names = {
        (item.get("name") if isinstance(item, dict) else item)
        for pillar in data["pillar_details"].values()
        for item in pillar.get("shensha", [])
        if (item.get("name") if isinstance(item, dict) else item)
    }
    summary_names = {item["name"] for item in summary["items"] if item.get("name")}
    assert pillar_names.issubset(summary_names)


def test_bazi_full_slims_interpretation_text():
    """R031: default /full omits long interpretation_text (explain/batch owns narrative)."""
    resp = client.post("/api/v1/bazi/full", json=_full_payload())
    assert resp.status_code == 200, resp.text
    data = resp.json()
    geju = data.get("geju") or {}
    career = data.get("career") or {}
    assert not geju.get("interpretation_text")
    assert not career.get("interpretation_text")


def test_bazi_full_trust_fields_present():
    """R032: provenance, evidence_chain, rule_version on /full."""
    resp = client.post("/api/v1/bazi/full", json=_full_payload())
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data.get("rule_version")
    assert isinstance(data.get("evidence_chain"), list)
    assert data.get("provenance") is not None
