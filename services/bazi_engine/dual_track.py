"""Classical vs engine dual-track registry (格局 ZIP09/21/22、用神 ZIP01/04/05 等)。"""

from __future__ import annotations

# pillars key: 年|月|日|时 干支

_GEJU_DUAL_BY_PILLARS: dict[str, dict[str, str | list[str]]] = {
    "辛巳|辛丑|乙酉|乙酉": {
        "id": "ZIP09",
        "recorded_geju": "从官杀格",
        "note": "滴天髓·从象：支全金局、干透两辛，古籍取从杀；引擎因时干乙木比肩助身取七杀格。",
        "source": "任铁樵《滴天髓阐微》",
    },
    "癸酉|丁酉|乙卯|丁亥": {
        "id": "ZIP21",
        "recorded_geju": "食神制杀格",
        "note": "衍生·食神制杀：古籍以制杀成格命名；引擎八正格取七杀格，derived_geju=食神制杀格。",
        "source": "子平/滴天髓衍生格回归",
    },
    "庚午|壬午|甲寅|丙寅": {
        "id": "ZIP22",
        "recorded_geju": "伤官佩印格",
        "note": "衍生·伤官佩印：古籍以佩印成格命名；引擎八正格取伤官格，derived_geju=伤官佩印格。",
        "source": "子平/滴天髓衍生格回归",
    },
}

_YONGSHEN_DUAL_BY_PILLARS: dict[str, dict[str, str | list[str]]] = {
    "己亥|丁卯|乙未|己卯": {
        "id": "ZIP01",
        "recorded_favor": ["earth", "fire"],
        "note": "用神双轨：千里注土火调候；引擎取水木扶曲直。",
        "source": "韦千里《千里命稿》例8",
    },
    "甲戌|丁卯|甲申|庚午": {
        "id": "ZIP04",
        "recorded_favor": ["metal"],
        "note": "用神双轨：千里注金；引擎取土火金（旺刃用杀制伤）。",
        "source": "韦千里《千里命稿》例58",
    },
    "癸未|辛酉|乙酉|丁亥": {
        "id": "ZIP05",
        "recorded_favor": ["fire"],
        "note": "用神双轨：千里注火制杀；引擎兼取水印化杀。",
        "source": "韦千里《千里命稿》例4",
    },
}


def pillars_key(year: str, month: str, day: str, hour: str) -> str:
    return f"{year}|{month}|{day}|{hour}"


def lookup_dual_track(
    year: str,
    month: str,
    day: str,
    hour: str,
) -> dict[str, str | list[str]] | None:
    return _GEJU_DUAL_BY_PILLARS.get(pillars_key(year, month, day, hour))


def lookup_yongshen_dual_track(
    year: str,
    month: str,
    day: str,
    hour: str,
) -> dict[str, str | list[str]] | None:
    return _YONGSHEN_DUAL_BY_PILLARS.get(pillars_key(year, month, day, hour))


def registered_geju_dual_track_ids() -> list[str]:
    """已登记格局双轨 ID（ZIP09/21/22 等），供回归与 provenance 引用。"""
    return sorted({str(v["id"]) for v in _GEJU_DUAL_BY_PILLARS.values()})


def registered_yongshen_dual_track_ids() -> list[str]:
    """已登记用神双轨 ID（ZIP01/04/05 等）。"""
    return sorted({str(v["id"]) for v in _YONGSHEN_DUAL_BY_PILLARS.values()})
