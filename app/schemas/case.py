"""Case and Snapshot schemas."""
from __future__ import annotations

import re
from datetime import datetime
from typing import Any, Dict, List, Literal, Optional
from zoneinfo import ZoneInfo

from pydantic import BaseModel, Field, field_validator, model_validator

from constants import MAX_LON, MIN_LON


_TAG_PATTERN = re.compile(r"^[\w\s,\-\u4e00-\u9fff]+$")
_ISO_NAIVE_PATTERN = re.compile(
    r"^(?P<y>\d{4})-(?P<m>\d{1,2})-(?P<d>\d{1,2})"
    r"T(?P<h>\d{1,2}):(?P<mi>\d{1,2})(?::(?P<s>\d{1,2})(?:\.(?P<us>\d{1,6}))?)?$"
)


def _normalize_birth_dt_local(value: str) -> str:
    """Normalize to zero-offset ISO8601 (allows single-digit month/day/time)."""
    if not isinstance(value, str):
        raise ValueError("birth_dt_local must be ISO8601 without offset")
    value = value.strip()
    match = _ISO_NAIVE_PATTERN.match(value)
    if not match:
        raise ValueError("birth_dt_local must be ISO8601 without offset")
    parts = match.groupdict()
    micro = parts.get("us") or ""
    microsecond = int(micro.ljust(6, "0")) if micro else 0
    try:
        dt = datetime(
            int(parts["y"]),
            int(parts["m"]),
            int(parts["d"]),
            int(parts["h"]),
            int(parts["mi"]),
            int(parts.get("s") or 0),
            microsecond,
        )
    except ValueError:
        raise ValueError("birth_dt_local must be ISO8601 without offset")
    return dt.isoformat(timespec="microseconds" if microsecond else "seconds")


_VALID_GENDERS: frozenset[str] = frozenset({"male", "female"})


class CaseBase(BaseModel):
    """Case基础字段验证"""
    model_config = {
        "from_attributes": True,
    }
    name: str
    gender: Optional[str] = None

    @field_validator("gender")
    @classmethod
    def validate_gender(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        if v not in _VALID_GENDERS:
            raise ValueError(
                f"gender must be 'male', 'female' or null, got: {v!r}"
            )
        return v
    birth_dt_local: str
    tz: str
    birth_dt: Optional[str] = None
    city: Optional[str] = None
    lon: float
    solar_time_enabled: bool = False
    notes: Optional[str] = None
    tags: Optional[str] = None

    @field_validator("birth_dt_local")
    @classmethod
    def validate_birth_dt_local(cls, v: str) -> str:
        return _normalize_birth_dt_local(v)

    @field_validator("tz")
    @classmethod
    def validate_tz(cls, v: str) -> str:
        try:
            ZoneInfo(v)
        except Exception as exc:
            raise ValueError(f"tz must be IANA name: {exc}")
        return v

    @field_validator("tags", mode="before")
    @classmethod
    def validate_tags(cls, v) -> Optional[str]:
        if v is None:
            return v
        # 支持前端传入 List[str]，自动转为逗号分隔字符串存储
        if isinstance(v, list):
            parts = [str(t).strip() for t in v if str(t).strip()]
            v = ",".join(parts) if parts else None
            if v is None:
                return None
        if not isinstance(v, str):
            raise ValueError("tags must be str or list of str")
        v = v.strip()
        if not v:
            return None
        if len(v) > 200:
            raise ValueError("tags too long (max 200)")
        if not _TAG_PATTERN.match(v):
            raise ValueError("tags may contain letters, digits, spaces, comma, hyphen, underscore, CJK")
        return v

    @model_validator(mode="after")
    def validate_lon(self):  # type: ignore[override]
        if not (MIN_LON <= self.lon <= MAX_LON):
            raise ValueError(f"lon must be between {MIN_LON} and {MAX_LON}")
        return self


class CaseCreate(CaseBase):
    """创建 Case 的请求"""
    pass


class CasePatch(BaseModel):
    """修补 Case 的请求"""
    name: Optional[str] = None
    gender: Optional[str] = None

    @field_validator("gender")
    @classmethod
    def validate_gender(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        if v not in _VALID_GENDERS:
            raise ValueError(
                f"gender must be 'male', 'female' or null, got: {v!r}"
            )
        return v
    birth_dt_local: Optional[str] = None
    tz: Optional[str] = None
    birth_dt: Optional[str] = None
    city: Optional[str] = None
    lon: Optional[float] = None
    solar_time_enabled: Optional[bool] = None
    notes: Optional[str] = None
    tags: Optional[str] = None

    @field_validator("birth_dt_local")
    @classmethod
    def validate_birth_dt_local(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        return _normalize_birth_dt_local(v)

    @field_validator("tz")
    @classmethod
    def validate_tz(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        try:
            ZoneInfo(v)
        except Exception as exc:
            raise ValueError(f"tz must be IANA name: {exc}")
        return v

    @field_validator("tags", mode="before")
    @classmethod
    def validate_tags(cls, v) -> Optional[str]:
        if v is None:
            return v
        if isinstance(v, list):
            parts = [str(t).strip() for t in v if str(t).strip()]
            v = ",".join(parts) if parts else None
            if v is None:
                return None
        if not isinstance(v, str):
            raise ValueError("tags must be str or list of str")
        v = v.strip()
        if not v:
            return None
        if len(v) > 200:
            raise ValueError("tags too long (max 200)")
        if not _TAG_PATTERN.match(v):
            raise ValueError("tags may contain letters, digits, spaces, comma, hyphen, underscore, CJK")
        return v

    @model_validator(mode="after")
    def validate_lon(self):  # type: ignore[override]
        lon = getattr(self, "lon", None)
        if lon is None:
            return self
        if not (MIN_LON <= lon <= MAX_LON):
            raise ValueError(f"lon must be between {MIN_LON} and {MAX_LON}")
        return self


class CaseOut(CaseBase):
    """Case 响应模型"""
    id: str
    created_at: datetime
    updated_at: datetime
    last_snapshot_at: Optional[datetime] = None
    api_version_last: Optional[str] = None
    rule_version_last: Optional[str] = None
    schema_version: Optional[str] = None
    latest_verify_summary: Optional[dict] = None
    # 覆盖父类 str 类型 → 输出为列表，前端标签组件可直接绑定
    tags: Optional[List[str]] = None  # type: ignore[assignment]

    @field_validator("tags", mode="before")
    @classmethod
    def validate_tags(cls, v) -> Optional[List[str]]:
        """覆盖 CaseBase.validate_tags：DB 字符串拆分为列表输出。"""
        if v is None:
            return None
        if isinstance(v, str):
            parts = [t.strip() for t in v.split(",") if t.strip()]
            return parts or None
        if isinstance(v, list):
            parts = [str(t).strip() for t in v if str(t).strip()]
            return parts or None
        return None


class SnapshotOut(BaseModel):
    """Snapshot 响应模型"""
    id: str
    case_id: str
    kind: str
    compute_flags: Optional[dict] = None
    input_json: Optional[dict] = None
    output_json: Optional[dict] = None
    backend_json: Optional[dict] = None
    api_version: Optional[str] = None
    rule_version: Optional[str] = None
    schema_version: Optional[str] = None
    summary_level: Optional[str] = None
    summary_warning_count: Optional[int] = None
    summary_diff_count: Optional[int] = None
    summary_engine_primary: Optional[str] = None
    note: Optional[str] = None
    created_at: datetime
