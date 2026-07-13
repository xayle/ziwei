"""Map Case rows to bazi/ziwei chart requests (archive-bundle · profile summary)."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from app.models import Case
from app.schemas import BaziFullRequest
from app.schemas.ziwei import ZiweiRequest
from services.case_fusheng_tags import case_late_zishi
from services.relation_engine.composer import _normalize_gender


def bazi_gender(case: Case) -> Literal["male", "female"]:
    raw = (case.gender or "male").lower()
    if raw in ("female", "f", "女"):
        return "female"
    return "male"


def case_to_bazi_request(case: Case, dt: datetime) -> BaziFullRequest:
    precision = case.birth_time_precision or "exact"
    if precision not in ("exact", "hour", "approximate", "unknown"):
        precision = "exact"
    return BaziFullRequest(
        dt=dt,
        lon=float(case.lon),
        tz=case.tz or "Asia/Shanghai",
        gender=bazi_gender(case),
        solar_time_enabled=bool(case.solar_time_enabled),
        zi_day_rule=case.zi_day_rule or "sxtwl",
        birth_time_precision=precision,  # type: ignore[arg-type]
        include_liuri=True,
    )


def case_to_ziwei_request(case: Case, dt: datetime) -> ZiweiRequest:
    sihua_stem_indices = None
    if (case.ziwei_sihua_method or "quanshu") == "zhongzhou":
        sihua_stem_indices = {"庚": 1, "辛": 1}

    return ZiweiRequest(
        year=dt.year,
        month=dt.month,
        day=dt.day,
        hour=dt.hour,
        minute=dt.minute,
        gender=_normalize_gender(case.gender or "male"),
        longitude=float(case.lon) if case.solar_time_enabled else None,
        template_version=case.ziwei_template_version or "standard",
        leap_month_method="same" if case.is_leap_month else "mid",
        year_divide=case.year_divide or "lichun",
        day_divide=case.day_divide or "solar_next",
        late_zishi=case_late_zishi(case),
        brightness_method=case.ziwei_brightness_method or "standard",
        youbi_method=case.ziwei_youbi_method or "month",
        liunian_sihua_method=case.ziwei_liunian_sihua_method or "year_stem",
        kuiyue_method=case.ziwei_kuiyue_method or "standard",
        tianma_method=case.ziwei_tianma_method or "year",
        sihua_stem_indices=sihua_stem_indices,
        include_flow_liuri=True,
    )
