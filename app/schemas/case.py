"""Case and Snapshot schemas."""

from __future__ import annotations

from datetime import datetime
import re
from zoneinfo import ZoneInfo

from pydantic import BaseModel, Field, field_validator, model_validator

from app.schemas.utm import clean_optional
from constants import MAX_LON, MIN_LON

_TAG_PATTERN = re.compile(r"^[\w\s,\-:/.\u4e00-\u9fff]+$")
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
_VALID_YEAR_DIVIDE: frozenset[str] = frozenset({"lichun", "normal"})
_VALID_DAY_DIVIDE: frozenset[str] = frozenset({"solar_next", "forward", "current"})
_VALID_ZI_DAY_RULE: frozenset[str] = frozenset({"sxtwl", "early_zi_prev_day", "early_zi_same_day"})
_VALID_ZIWEI_BRIGHTNESS: frozenset[str] = frozenset({"standard", "zhongzhou", "mod1", "mod2"})
_VALID_ZIWEI_YOUBI: frozenset[str] = frozenset({"month", "hour"})
_VALID_ZIWEI_SIHUA: frozenset[str] = frozenset({"quanshu", "zhongzhou"})
_VALID_ZIWEI_LIUNIAN_SIHUA: frozenset[str] = frozenset({"year_stem", "life_palace_stem"})
_VALID_ZIWEI_KUIYUE: frozenset[str] = frozenset({"standard", "gengxin_mahu", "gengxin_huima", "liuxin_mahu"})
_VALID_ZIWEI_TIANMA: frozenset[str] = frozenset({"year", "month"})
_VALID_ZIWEI_TEMPLATE: frozenset[str] = frozenset({"standard", "pro", "simple"})


class CaseBase(BaseModel):
    """Case基础字段验证"""

    model_config = {
        "from_attributes": True,
    }
    name: str
    gender: str | None = None

    @field_validator("gender")
    @classmethod
    def validate_gender(cls, v: str | None) -> str | None:
        if v is None:
            return v
        if v not in _VALID_GENDERS:
            raise ValueError(f"gender must be 'male', 'female' or null, got: {v!r}")
        return v

    birth_dt_local: str
    tz: str
    birth_dt: str | None = None
    city: str | None = None
    lon: float
    current_city: str | None = None
    current_province: str | None = None
    current_lon: float | None = None
    current_tz: str | None = None
    calendar_mode: str = "gregorian"
    is_leap_month: bool = False
    birth_time_precision: str = "exact"
    unknown_time_fallback: str = "midday"
    solar_time_enabled: bool = False
    year_divide: str = Field(default="lichun", description="紫微年界：lichun | normal")
    day_divide: str = Field(default="solar_next", description="晚子换日：solar_next | forward | current")
    zi_day_rule: str = Field(default="sxtwl", description="八字子时换日：sxtwl | early_zi_prev_day | early_zi_same_day")
    ziwei_brightness_method: str = Field(default="standard", description="紫微亮度：standard | zhongzhou | mod1 | mod2")
    ziwei_youbi_method: str = Field(default="month", description="紫微右弼：month | hour")
    ziwei_sihua_method: str = Field(default="quanshu", description="生年四化：quanshu | zhongzhou")
    ziwei_liunian_sihua_method: str = Field(default="year_stem", description="流年四化：year_stem | life_palace_stem")
    ziwei_kuiyue_method: str = Field(default="standard", description="魁钺安法")
    ziwei_tianma_method: str = Field(default="year", description="天马安法：year | month")
    ziwei_template_version: str = Field(default="standard", description="紫微模板：standard | pro | simple")
    notes: str | None = None
    tags: str | None = None
    utm_source: str | None = Field(default=None, description="渠道，如 douyin")
    utm_campaign: str | None = Field(default=None, description="活动/话题")
    content_id: str | None = Field(default=None, description="抖音视频 ID 等素材 ID")

    @field_validator("utm_source", "utm_campaign", mode="before")
    @classmethod
    def validate_utm_text(cls, v: object) -> str | None:
        if v is None or isinstance(v, str):
            return clean_optional(v if isinstance(v, str) else None, max_len=128)
        raise ValueError("must be a string or null")

    @field_validator("content_id", mode="before")
    @classmethod
    def validate_content_id(cls, v: object) -> str | None:
        if v is None or isinstance(v, str):
            return clean_optional(v if isinstance(v, str) else None, max_len=64)
        raise ValueError("must be a string or null")

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

    @field_validator("calendar_mode", mode="before")
    @classmethod
    def default_calendar_mode(cls, v: str | None) -> str:
        return v or "gregorian"

    @field_validator("is_leap_month", mode="before")
    @classmethod
    def default_is_leap_month(cls, v: bool | None) -> bool:
        return False if v is None else v

    @field_validator("birth_time_precision", mode="before")
    @classmethod
    def default_birth_time_precision(cls, v: str | None) -> str:
        return v or "exact"

    @field_validator("unknown_time_fallback", mode="before")
    @classmethod
    def default_unknown_time_fallback(cls, v: str | None) -> str:
        return v or "midday"

    @field_validator("solar_time_enabled", mode="before")
    @classmethod
    def default_solar_time_enabled(cls, v: bool | None) -> bool:
        return False if v is None else v

    @field_validator("year_divide", mode="before")
    @classmethod
    def default_year_divide(cls, v: str | None) -> str:
        value = (v or "lichun").strip()
        if value not in _VALID_YEAR_DIVIDE:
            raise ValueError("year_divide must be lichun or normal")
        return value

    @field_validator("day_divide", mode="before")
    @classmethod
    def default_day_divide(cls, v: str | None) -> str:
        value = (v or "solar_next").strip()
        if value not in _VALID_DAY_DIVIDE:
            raise ValueError("day_divide must be solar_next, forward, or current")
        return value

    @field_validator("zi_day_rule", mode="before")
    @classmethod
    def default_zi_day_rule(cls, v: str | None) -> str:
        value = (v or "sxtwl").strip()
        if value not in _VALID_ZI_DAY_RULE:
            raise ValueError("invalid zi_day_rule")
        return value

    @field_validator("ziwei_brightness_method", mode="before")
    @classmethod
    def default_ziwei_brightness_method(cls, v: str | None) -> str:
        value = (v or "standard").strip()
        if value not in _VALID_ZIWEI_BRIGHTNESS:
            raise ValueError("invalid ziwei_brightness_method")
        return value

    @field_validator("ziwei_youbi_method", mode="before")
    @classmethod
    def default_ziwei_youbi_method(cls, v: str | None) -> str:
        value = (v or "month").strip()
        if value not in _VALID_ZIWEI_YOUBI:
            raise ValueError("invalid ziwei_youbi_method")
        return value

    @field_validator("ziwei_sihua_method", mode="before")
    @classmethod
    def default_ziwei_sihua_method(cls, v: str | None) -> str:
        value = (v or "quanshu").strip()
        if value not in _VALID_ZIWEI_SIHUA:
            raise ValueError("invalid ziwei_sihua_method")
        return value

    @field_validator("ziwei_liunian_sihua_method", mode="before")
    @classmethod
    def default_ziwei_liunian_sihua_method(cls, v: str | None) -> str:
        value = (v or "year_stem").strip()
        if value not in _VALID_ZIWEI_LIUNIAN_SIHUA:
            raise ValueError("invalid ziwei_liunian_sihua_method")
        return value

    @field_validator("ziwei_kuiyue_method", mode="before")
    @classmethod
    def default_ziwei_kuiyue_method(cls, v: str | None) -> str:
        value = (v or "standard").strip()
        if value not in _VALID_ZIWEI_KUIYUE:
            raise ValueError("invalid ziwei_kuiyue_method")
        return value

    @field_validator("ziwei_tianma_method", mode="before")
    @classmethod
    def default_ziwei_tianma_method(cls, v: str | None) -> str:
        value = (v or "year").strip()
        if value not in _VALID_ZIWEI_TIANMA:
            raise ValueError("invalid ziwei_tianma_method")
        return value

    @field_validator("ziwei_template_version", mode="before")
    @classmethod
    def default_ziwei_template_version(cls, v: str | None) -> str:
        value = (v or "standard").strip()
        if value not in _VALID_ZIWEI_TEMPLATE:
            raise ValueError("invalid ziwei_template_version")
        return value

    @field_validator("tags", mode="before")
    @classmethod
    def validate_tags(cls, v) -> str | None:
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
            raise ValueError(
                "tags may contain letters, digits, spaces, comma, hyphen, underscore, colon, slash, dot, CJK"
            )
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

    name: str | None = None
    gender: str | None = None

    @field_validator("gender")
    @classmethod
    def validate_gender(cls, v: str | None) -> str | None:
        if v is None:
            return v
        if v not in _VALID_GENDERS:
            raise ValueError(f"gender must be 'male', 'female' or null, got: {v!r}")
        return v

    birth_dt_local: str | None = None
    tz: str | None = None
    birth_dt: str | None = None
    city: str | None = None
    lon: float | None = None
    current_city: str | None = None
    current_province: str | None = None
    current_lon: float | None = None
    current_tz: str | None = None
    calendar_mode: str | None = None
    is_leap_month: bool | None = None
    birth_time_precision: str | None = None
    unknown_time_fallback: str | None = None
    solar_time_enabled: bool | None = None
    year_divide: str | None = None
    day_divide: str | None = None
    zi_day_rule: str | None = None
    ziwei_brightness_method: str | None = None
    ziwei_youbi_method: str | None = None
    ziwei_sihua_method: str | None = None
    ziwei_liunian_sihua_method: str | None = None
    ziwei_kuiyue_method: str | None = None
    ziwei_tianma_method: str | None = None
    ziwei_template_version: str | None = None
    notes: str | None = None
    tags: str | None = None

    @field_validator("birth_dt_local")
    @classmethod
    def validate_birth_dt_local(cls, v: str | None) -> str | None:
        if v is None:
            return v
        return _normalize_birth_dt_local(v)

    @field_validator("tz")
    @classmethod
    def validate_tz(cls, v: str | None) -> str | None:
        if v is None:
            return v
        try:
            ZoneInfo(v)
        except Exception as exc:
            raise ValueError(f"tz must be IANA name: {exc}")
        return v

    @field_validator("year_divide")
    @classmethod
    def validate_year_divide(cls, v: str | None) -> str | None:
        if v is None:
            return v
        value = v.strip()
        if value not in _VALID_YEAR_DIVIDE:
            raise ValueError("year_divide must be lichun or normal")
        return value

    @field_validator("day_divide")
    @classmethod
    def validate_day_divide(cls, v: str | None) -> str | None:
        if v is None:
            return v
        value = v.strip()
        if value not in _VALID_DAY_DIVIDE:
            raise ValueError("day_divide must be solar_next, forward, or current")
        return value

    @field_validator("zi_day_rule")
    @classmethod
    def validate_zi_day_rule(cls, v: str | None) -> str | None:
        if v is None:
            return v
        value = v.strip()
        if value not in _VALID_ZI_DAY_RULE:
            raise ValueError("invalid zi_day_rule")
        return value

    @field_validator("ziwei_brightness_method")
    @classmethod
    def validate_ziwei_brightness_method(cls, v: str | None) -> str | None:
        if v is None:
            return v
        value = v.strip()
        if value not in _VALID_ZIWEI_BRIGHTNESS:
            raise ValueError("invalid ziwei_brightness_method")
        return value

    @field_validator("ziwei_youbi_method")
    @classmethod
    def validate_ziwei_youbi_method(cls, v: str | None) -> str | None:
        if v is None:
            return v
        value = v.strip()
        if value not in _VALID_ZIWEI_YOUBI:
            raise ValueError("invalid ziwei_youbi_method")
        return value

    @field_validator("ziwei_sihua_method")
    @classmethod
    def validate_ziwei_sihua_method(cls, v: str | None) -> str | None:
        if v is None:
            return v
        value = v.strip()
        if value not in _VALID_ZIWEI_SIHUA:
            raise ValueError("invalid ziwei_sihua_method")
        return value

    @field_validator("ziwei_liunian_sihua_method")
    @classmethod
    def validate_ziwei_liunian_sihua_method(cls, v: str | None) -> str | None:
        if v is None:
            return v
        value = v.strip()
        if value not in _VALID_ZIWEI_LIUNIAN_SIHUA:
            raise ValueError("invalid ziwei_liunian_sihua_method")
        return value

    @field_validator("ziwei_kuiyue_method")
    @classmethod
    def validate_ziwei_kuiyue_method(cls, v: str | None) -> str | None:
        if v is None:
            return v
        value = v.strip()
        if value not in _VALID_ZIWEI_KUIYUE:
            raise ValueError("invalid ziwei_kuiyue_method")
        return value

    @field_validator("ziwei_tianma_method")
    @classmethod
    def validate_ziwei_tianma_method(cls, v: str | None) -> str | None:
        if v is None:
            return v
        value = v.strip()
        if value not in _VALID_ZIWEI_TIANMA:
            raise ValueError("invalid ziwei_tianma_method")
        return value

    @field_validator("ziwei_template_version")
    @classmethod
    def validate_ziwei_template_version(cls, v: str | None) -> str | None:
        if v is None:
            return v
        value = v.strip()
        if value not in _VALID_ZIWEI_TEMPLATE:
            raise ValueError("invalid ziwei_template_version")
        return value

    @field_validator("tags", mode="before")
    @classmethod
    def validate_tags(cls, v) -> str | None:
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
            raise ValueError(
                "tags may contain letters, digits, spaces, comma, hyphen, underscore, colon, slash, dot, CJK"
            )
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
    last_snapshot_at: datetime | None = None
    api_version_last: str | None = None
    rule_version_last: str | None = None
    schema_version: str | None = None
    latest_verify_summary: dict | None = None
    is_leap_month_inferred: bool | None = None
    # 覆盖父类 str 类型 → 输出为列表，前端标签组件可直接绑定
    tags: list[str] | None = None  # type: ignore[assignment]

    @field_validator("tags", mode="before")
    @classmethod
    def validate_tags(cls, v) -> list[str] | None:
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

    model_config = {"from_attributes": True}

    id: str
    case_id: str
    kind: str
    compute_flags: dict | None = None
    input_json: dict | None = None
    output_json: dict | None = None
    backend_json: dict | None = None
    api_version: str | None = None
    rule_version: str | None = None
    schema_version: str | None = None
    summary_level: str | None = None
    summary_warning_count: int | None = None
    summary_diff_count: int | None = None
    summary_engine_primary: str | None = None
    note: str | None = None
    created_at: datetime


class CaseListResponse(BaseModel):
    """Case 分页列表响应"""

    items: list[CaseOut]
    total: int
    next_cursor: str | None = None
