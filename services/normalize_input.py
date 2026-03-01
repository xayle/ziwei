from __future__ import annotations

from typing import Any, Dict, List

from fastapi import HTTPException, status

from constants import CN_MAX_LON, CN_MIN_LON, MAX_LON, MIN_LON


def validate_lon_strict(lon: float) -> float:
    if lon is None or not isinstance(lon, (int, float)):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"code": "lon_invalid"})
    if not (MIN_LON <= lon <= MAX_LON):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "lon_out_of_range", "message": f"lon must be between {MIN_LON} and {MAX_LON}"},
        )
    return lon


def warn_lon_cn_range(tz: str, lon: float) -> List[Dict[str, Any]]:
    warnings: List[Dict[str, Any]] = []
    if tz == "Asia/Shanghai" and (lon < CN_MIN_LON or lon > CN_MAX_LON):
        warnings.append(
            {
                "code": "lon_out_of_cn_range",
                "message": "tz=Asia/Shanghai but lon is outside China range [73,135]; calculation continues.",
                "meta": {"tz": tz, "lon": lon, "expected_range": [CN_MIN_LON, CN_MAX_LON]},
            }
        )
    return warnings
