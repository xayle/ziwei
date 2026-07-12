"""
快捷起盘端点 — 一步完成：建档 + 计算 + 返回命盘
用户无需分三步（POST /cases → POST /cases/{id}/compute → GET snapshots），
一个请求即可拿到完整结果。
"""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field, field_validator, model_validator
from sqlmodel import Session

from app.dependencies import RequiredUser
from app.error_handling import handle_exceptions
from app.exceptions import ErrorCode, ValidationException
from app.models import Case
from app.schemas import CaseOut, ComputeRequest, ComputeResponse
from constants import MAX_LON, MIN_LON
from db import get_session
from routers.compute import _do_compute_for_case
from services.case_leap_month import infer_case_leap_month
from services.normalize_input import normalize_birth_datetime

router = APIRouter(prefix="/api/v1", tags=["quickstart"])


class QuickstartRequest(BaseModel):
    """一步建档+计算请求体"""

    # ── 人物档案字段（与 CaseCreate 一致）──
    name: str = Field(..., description="档案名称，例如：张三 2000年")
    birth_dt_local: str = Field(
        ...,
        description="出生时间（本地时间，ISO8601 无偏移），例如 '2000-01-15T08:30:00'",
    )
    tz: str = Field(..., description="IANA 时区，例如 'Asia/Shanghai'")
    lon: float = Field(..., description="出生地经度，范围 -180~180")
    gender: str | None = Field(default=None, description="'male' 或 'female'")
    city: str | None = Field(default=None, description="出生城市名称")
    solar_time_enabled: bool = Field(default=False, description="是否启用真太阳时修正")
    notes: str | None = Field(default=None, description="备注")
    tags: list[str] | None = Field(default=None, description="标签列表")

    @field_validator("tags", mode="before")
    @classmethod
    def parse_tags(cls, v) -> list[str] | None:
        """接受逗号分隔字符串或列表，统一转为 List[str]"""
        if v is None:
            return v
        if isinstance(v, str):
            parts = [t.strip() for t in v.split(",") if t.strip()]
            return parts if parts else None
        return v

    @model_validator(mode="after")
    def validate_lon_range(self):
        if not (MIN_LON <= self.lon <= MAX_LON):
            raise ValueError(f"lon must be between {MIN_LON} and {MAX_LON}")
        return self

    # ── 计算选项（与 ComputeRequest 一致）──
    mode: str = Field(default="dual", description="计算模式：'dual'（双引擎）或 'single'")
    liunian_years: list[int] | None = Field(
        default=None,
        description="流年范围（相对当前年，例如 [-2, 2] 表示前后2年）",
    )


class QuickstartResponse(BaseModel):
    """一步建档+计算响应体"""

    case: CaseOut
    compute: ComputeResponse


def _now_utc() -> datetime:
    return datetime.now(UTC)


@router.post(
    "/quickstart",
    response_model=QuickstartResponse,
    status_code=status.HTTP_201_CREATED,
    summary="快捷建档+计算（一步完成）",
    description=(
        "**新用户入口**：只需提供出生信息，系统自动建档并执行完整的八字+验证计算，"
        "返回案例档案和命盘快照。无需分步调用 POST /cases → POST /cases/{id}/compute。"
    ),
)
@handle_exceptions(ErrorCode.SYSTEM_INTERNAL_ERROR)
def quickstart(
    body: QuickstartRequest,
    current_user: RequiredUser,
    session: Session = Depends(get_session),
) -> QuickstartResponse:
    # ── 1. 参数校验 ──────────────────────────────────────────────────
    from zoneinfo import ZoneInfo

    try:
        ZoneInfo(body.tz)
    except Exception:
        raise ValidationException(
            code=ErrorCode.VALIDATION_INVALID_FORMAT,
            message=f"tz 不是合法的 IANA 时区：{body.tz!r}",
        )

    # tags list → comma-separated string for storage
    tags_str: str | None = None
    if body.tags:
        tags_str = ",".join(t.strip() for t in body.tags if t.strip()) or None

    # ── 2. 建档（Case）────────────────────────────────────────────────
    now = _now_utc()
    case = Case(
        name=body.name,
        birth_dt_local=body.birth_dt_local,
        tz=body.tz,
        lon=body.lon,
        gender=body.gender,
        city=body.city,
        solar_time_enabled=body.solar_time_enabled,
        notes=body.notes,
        tags=tags_str,
        owner_id=current_user.id,
        created_at=now,
        updated_at=now,
    )
    try:
        normalized_birth = normalize_birth_datetime(
            datetime.fromisoformat(body.birth_dt_local),
            body.tz,
            auto_dst=body.solar_time_enabled,
        )
        case.birth_dt = normalized_birth.normalized_birth_dt_utc
    except Exception:
        case.birth_dt = None
    inferred_leap_month = infer_case_leap_month(case.birth_dt_local, "gregorian")
    if inferred_leap_month is not None:
        case.is_leap_month = inferred_leap_month
    session.add(case)
    session.commit()
    session.refresh(case)

    # ── 3. 计算（bazi + verify）───────────────────────────────────────
    compute_payload = ComputeRequest(
        mode=body.mode,  # type: ignore[arg-type]
        solar_time_enabled=body.solar_time_enabled,
        liunian_years=body.liunian_years,
    )
    compute_result = _do_compute_for_case(session, case, compute_payload)

    # ── 4. 刷新 case（last_snapshot_at 已由 compute 写入）────────────
    session.refresh(case)

    return QuickstartResponse(
        case=CaseOut.model_validate(case),
        compute=compute_result,
    )
