"""
场景管理路由 - 支持假设推演和What-If分析
"""

from datetime import UTC, datetime
import json
import logging

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, ConfigDict, ValidationError, field_validator
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from app.dependencies import RequiredUser
from app.error_handling import handle_exceptions
from app.exceptions import (
    AuthorizationException,
    BusinessException,
    ErrorCode,
    ResourceNotFoundException,
    ValidationException,
)
from app.models import Member, Scenario, User
from db import get_session
from services.delegation_service import log_action
from services.json_validators import ScenarioJsonValidator
from services.permission_service import Permission, Role, has_permission

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["scenarios"])


def _validate_json_field(value: str | None, field_name: str, expected_type: type | tuple[type, ...]) -> str | None:
    if value is None:
        return None
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError as exc:
        raise ValueError(f"{field_name} must be valid JSON") from exc
    if not isinstance(parsed, expected_type):
        raise ValueError(f"{field_name} must be JSON {expected_type}")
    return value


class ScenarioCreateRequest(BaseModel):
    """创建场景请求"""

    base_member_id: int
    name: str
    description: str | None = None
    scenario_type: str  # "time_adjustment", "location_adjustment", "custom", etc.
    variations: str | None = None  # JSON object with scenario parameters
    results: str | None = None  # JSON array with calculation results

    @field_validator("variations")
    @classmethod
    def validate_variations(cls, v: str | None) -> str | None:
        return _validate_json_field(v, "variations", dict)

    @field_validator("results")
    @classmethod
    def validate_results(cls, v: str | None) -> str | None:
        return _validate_json_field(v, "results", list)


class ScenarioUpdateRequest(BaseModel):
    """更新场景请求"""

    name: str | None = None
    description: str | None = None
    scenario_type: str | None = None
    variations: str | None = None
    results: str | None = None

    @field_validator("variations")
    @classmethod
    def validate_variations(cls, v: str | None) -> str | None:
        return _validate_json_field(v, "variations", dict)

    @field_validator("results")
    @classmethod
    def validate_results(cls, v: str | None) -> str | None:
        return _validate_json_field(v, "results", list)


class ScenarioResponse(BaseModel):
    """场景响应"""

    model_config = ConfigDict(from_attributes=True)
    id: int
    owner_id: int
    base_member_id: int
    name: str
    description: str | None
    scenario_type: str
    variations: str | None
    results: str | None
    created_at: datetime
    updated_at: datetime


class ScenarioListResponse(BaseModel):
    """场景分页列表响应"""

    items: list[ScenarioResponse]
    total: int
    next_cursor: int | None = None


def check_member_ownership(session: Session, current_user: User, member_id: int) -> Member:
    """检查用户是否拥有该成员"""
    member = session.exec(
        select(Member).where(Member.id == member_id, Member.deleted_at.is_(None))  # type: ignore[union-attr]
    ).first()
    if not member:
        raise ResourceNotFoundException(
            message="Member not found",
            details={"resource_type": "member", "resource_id": member_id},
        )
    if member.owner_id != current_user.id:
        raise AuthorizationException(
            code=ErrorCode.AUTHZ_PERMISSION_DENIED,
            message="Permission denied: member not owned by current user",
        )
    return member


@router.post("/scenarios", response_model=ScenarioResponse, status_code=201)
@handle_exceptions(ErrorCode.SYSTEM_INTERNAL_ERROR)
def create_scenario(
    body: ScenarioCreateRequest,
    current_user: RequiredUser,
    session: Session = Depends(get_session),
):
    """创建新场景"""
    # 检查权限
    try:
        user_role = Role(current_user.role)
    except ValueError:
        user_role = Role.EDITOR
    if not has_permission(user_role, Permission.CREATE_SCENARIO):
        raise AuthorizationException(
            code=ErrorCode.AUTHZ_PERMISSION_DENIED,
            message="Permission denied: create_scenario required",
        )

    # 验证成员所有权
    check_member_ownership(session, current_user, body.base_member_id)

    # ✅ 验证 JSON 字段的结构和内容
    try:
        # 验证 variations（如果提供）
        if body.variations:
            ScenarioJsonValidator.validate_variations(body.variations)

        # 验证 results（如果提供）
        if body.results:
            ScenarioJsonValidator.validate_results(body.results)

        logger.info(f"Scenario JSON validation passed for member_id={body.base_member_id}, type={body.scenario_type}")
    except (ValueError, ValidationError) as e:
        logger.warning(f"Scenario JSON validation failed: {e!s}")
        raise ValidationException(
            code=ErrorCode.VALIDATION_INVALID_JSON,
            message=f"Invalid JSON data format: {e!s}",
        )

    # 创建场景
    new_scenario = Scenario(
        owner_id=current_user.id or 0,
        base_member_id=body.base_member_id,
        name=body.name,
        description=body.description,
        scenario_type=body.scenario_type,
        variations=body.variations,
        results=body.results,
    )

    try:
        session.add(new_scenario)
        session.commit()
        session.refresh(new_scenario)

        # 审计日志
        log_action(
            session,
            user_id=current_user.id or 0,
            action="create_scenario",
            resource_type="scenario",
            resource_id=str(new_scenario.id),
            details={
                "scenario": new_scenario.name,
                "scenario_type": new_scenario.scenario_type,
            },
        )

        return ScenarioResponse.model_validate(new_scenario)
    except IntegrityError as e:
        session.rollback()
        raise BusinessException(
            code=ErrorCode.BUSINESS_OPERATION_FAILED,
            message=f"Failed to create scenario: {e!s}",
        )


@router.get("/scenarios", response_model=ScenarioListResponse)
@handle_exceptions(ErrorCode.SYSTEM_INTERNAL_ERROR)
def list_scenarios(
    current_user: RequiredUser,
    session: Session = Depends(get_session),
    member_id: int | None = None,
    scenario_type: str | None = None,
    limit: int = Query(20, ge=1, le=100, description="每页数量"),
    last_id: int = Query(0, ge=0, description="游标（上一页最后 ID）"),
):
    """列表查询场景"""
    # 检查权限
    try:
        user_role = Role(current_user.role)
    except ValueError:
        user_role = Role.EDITOR
    if not has_permission(user_role, Permission.READ_SCENARIO):
        raise AuthorizationException(
            code=ErrorCode.AUTHZ_PERMISSION_DENIED,
            message="Permission denied: read_scenario required",
        )

    # 基础过滤条件
    base_filters = [
        Scenario.owner_id == current_user.id,
        Scenario.deleted_at.is_(None),  # type: ignore[union-attr]
    ]
    if member_id:
        base_filters.append(Scenario.base_member_id == member_id)  # type: ignore[arg-type]
    if scenario_type:
        base_filters.append(Scenario.scenario_type == scenario_type)  # type: ignore[arg-type]

    # COUNT 查询获取真实总数
    count_stmt = select(func.count()).select_from(Scenario).where(*base_filters)
    total_count: int = session.exec(count_stmt).one()  # type: ignore[assignment]

    # Keyset 分页数据查询
    data_query = select(Scenario).where(*base_filters).order_by(Scenario.id)  # type: ignore[arg-type]
    if last_id > 0:
        data_query = data_query.where(Scenario.id > last_id)  # type: ignore[operator]
    data_query = data_query.limit(limit)
    scenarios = session.exec(data_query).all()

    items = [ScenarioResponse.model_validate(s) for s in scenarios]
    next_cursor = scenarios[-1].id if (scenarios and len(scenarios) == limit) else None
    return {"items": items, "total": total_count, "next_cursor": next_cursor}


@router.get("/scenarios/{scenario_id}", response_model=ScenarioResponse)
@handle_exceptions(ErrorCode.SYSTEM_INTERNAL_ERROR)
def get_scenario(
    scenario_id: int,
    current_user: RequiredUser,
    session: Session = Depends(get_session),
):
    """获取单个场景详情"""
    # 检查权限
    try:
        user_role = Role(current_user.role)
    except ValueError:
        user_role = Role.EDITOR
    if not has_permission(user_role, Permission.READ_SCENARIO):
        raise AuthorizationException(
            code=ErrorCode.AUTHZ_PERMISSION_DENIED,
            message="Permission denied: read_scenario required",
        )

    scenario = session.exec(
        select(Scenario).where(Scenario.id == scenario_id, Scenario.deleted_at.is_(None))  # type: ignore[union-attr]
    ).first()
    if not scenario:
        raise ResourceNotFoundException(
            message="Scenario not found",
            details={"resource_type": "scenario", "resource_id": scenario_id},
        )

    # 验证所有权
    if scenario.owner_id != current_user.id:
        raise AuthorizationException(
            code=ErrorCode.AUTHZ_PERMISSION_DENIED,
            message="Permission denied: scenario not owned by current user",
        )

    return ScenarioResponse.model_validate(scenario)


@router.put("/scenarios/{scenario_id}", response_model=ScenarioResponse)
@handle_exceptions(ErrorCode.SYSTEM_INTERNAL_ERROR)
def update_scenario(
    scenario_id: int,
    body: ScenarioUpdateRequest,
    current_user: RequiredUser,
    session: Session = Depends(get_session),
):
    """更新场景"""
    # 检查权限
    try:
        user_role = Role(current_user.role)
    except ValueError:
        user_role = Role.EDITOR
    if not has_permission(user_role, Permission.UPDATE_SCENARIO):
        raise AuthorizationException(
            code=ErrorCode.AUTHZ_PERMISSION_DENIED,
            message="Permission denied: update_scenario required",
        )

    scenario = session.exec(
        select(Scenario).where(Scenario.id == scenario_id, Scenario.deleted_at.is_(None))  # type: ignore[union-attr]
    ).first()
    if not scenario:
        raise ResourceNotFoundException(
            message="Scenario not found",
            details={"resource_type": "scenario", "resource_id": scenario_id},
        )

    # 验证所有权
    if scenario.owner_id != current_user.id:
        raise AuthorizationException(
            code=ErrorCode.AUTHZ_PERMISSION_DENIED,
            message="Permission denied: scenario not owned by current user",
        )

    # 更新字段
    update_data = body.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(scenario, key, value)

    scenario.updated_at = datetime.now(UTC)

    try:
        session.add(scenario)
        session.commit()
        session.refresh(scenario)

        # 审计日志
        log_action(
            session,
            user_id=current_user.id or 0,
            action="update_scenario",
            resource_type="scenario",
            resource_id=str(scenario.id),
            details={"updated_fields": list(update_data.keys())},
        )

        return ScenarioResponse.model_validate(scenario)
    except IntegrityError as e:
        session.rollback()
        raise BusinessException(
            code=ErrorCode.BUSINESS_OPERATION_FAILED,
            message=f"Failed to update scenario: {e!s}",
        )


@router.delete("/scenarios/{scenario_id}", status_code=204)
@handle_exceptions(ErrorCode.SYSTEM_INTERNAL_ERROR)
def delete_scenario(
    scenario_id: int,
    current_user: RequiredUser,
    session: Session = Depends(get_session),
):
    """删除场景"""
    # 检查权限
    try:
        user_role = Role(current_user.role)
    except ValueError:
        user_role = Role.EDITOR
    if not has_permission(user_role, Permission.DELETE_SCENARIO):
        raise AuthorizationException(
            code=ErrorCode.AUTHZ_PERMISSION_DENIED,
            message="Permission denied: delete_scenario required",
        )

    scenario = session.exec(select(Scenario).where(Scenario.id == scenario_id, Scenario.deleted_at.is_(None))).first()  # type: ignore[union-attr]
    if not scenario:
        raise ResourceNotFoundException(
            message="Scenario not found",
            details={"resource_type": "scenario", "resource_id": scenario_id},
        )

    # 验证所有权
    if scenario.owner_id != current_user.id:
        raise AuthorizationException(
            code=ErrorCode.AUTHZ_PERMISSION_DENIED,
            message="Permission denied: scenario not owned by current user",
        )

    try:
        scenario.deleted_at = datetime.now(UTC)
        scenario.updated_at = datetime.now(UTC)
        session.add(scenario)
        session.commit()

        # 审计日志
        log_action(
            session,
            user_id=current_user.id or 0,
            action="delete_scenario",
            resource_type="scenario",
            resource_id=str(scenario.id),
            details={"scenario": scenario.name},
        )
    except IntegrityError as e:
        session.rollback()
        raise BusinessException(
            code=ErrorCode.BUSINESS_OPERATION_FAILED,
            message=f"Failed to delete scenario: {e!s}",
        )


@router.get("/members/{member_id}/scenarios", response_model=ScenarioListResponse)
@handle_exceptions(ErrorCode.SYSTEM_INTERNAL_ERROR)
def list_member_scenarios(
    member_id: int,
    current_user: RequiredUser,
    session: Session = Depends(get_session),
    limit: int = Query(20, ge=1, le=100, description="每页数量"),
    last_id: int = Query(0, ge=0, description="游标（上一页最后 ID）"),
):
    """获取特定成员的所有场景"""
    # 检查权限
    try:
        user_role = Role(current_user.role)
    except ValueError:
        user_role = Role.EDITOR
    if not has_permission(user_role, Permission.READ_SCENARIO):
        raise AuthorizationException(
            code=ErrorCode.AUTHZ_PERMISSION_DENIED,
            message="Permission denied: read_scenario required",
        )

    # 验证成员所有权
    check_member_ownership(session, current_user, member_id)

    base_filters = [
        Scenario.owner_id == current_user.id,
        Scenario.base_member_id == member_id,
        Scenario.deleted_at.is_(None),  # type: ignore[union-attr]
    ]

    # COUNT 查询
    count_stmt = select(func.count()).select_from(Scenario).where(*base_filters)
    total_count: int = session.exec(count_stmt).one()  # type: ignore[assignment]

    # Keyset 分页
    data_query = select(Scenario).where(*base_filters).order_by(Scenario.id)  # type: ignore[arg-type]
    if last_id > 0:
        data_query = data_query.where(Scenario.id > last_id)  # type: ignore[operator]
    data_query = data_query.limit(limit)
    scenarios = session.exec(data_query).all()

    items = [ScenarioResponse.model_validate(s) for s in scenarios]
    next_cursor = scenarios[-1].id if (scenarios and len(scenarios) == limit) else None
    return {"items": items, "total": total_count, "next_cursor": next_cursor}


# ─────────────────────────────────────────────────────────────────────────────
# W5  场景模拟  POST /api/v1/scenarios/{id}/simulate
# ─────────────────────────────────────────────────────────────────────────────


class SimulateRequest(BaseModel):
    """W5 场景模拟请求：可选覆盖 birth_dt / longitude，触发重新计算并回写 results。"""

    birth_dt_override: str | None = None
    longitude_override: float | None = None
    gender_override: str | None = None
    note: str | None = None


class SimulateResponse(BaseModel):
    scenario_id: int
    geju_name: str = ""
    yongshen_favor: list[str] = []
    yongshen_avoid: list[str] = []
    wuxing_scores: dict[str, float] = {}
    note: str = ""
    simulated_at: str


@router.post(
    "/scenarios/{scenario_id}/simulate",
    response_model=SimulateResponse,
    summary="W5 场景模拟（What-If 推演）",
    description=(
        "对已有场景执行 What-If 推演：可临时覆盖出生时间/经度/性别，"
        "重新计算八字关键指标并将结果回写到 scenario.results，不修改原始成员数据。"
    ),
)
@handle_exceptions(ErrorCode.SYSTEM_INTERNAL_ERROR)
def simulate_scenario(
    scenario_id: int,
    payload: SimulateRequest,
    current_user: RequiredUser,
    session: Session = Depends(get_session),
):
    """W5: What-If 场景模拟，回写 results，返回轻量对比快照。"""
    scenario = session.get(Scenario, scenario_id)
    if not scenario or scenario.deleted_at is not None:
        raise ResourceNotFoundException(
            message="场景不存在",
            details={"resource_id": str(scenario_id)},
        )
    if scenario.owner_id != current_user.id:
        raise AuthorizationException(
            code=ErrorCode.AUTHZ_PERMISSION_DENIED,
            message="Permission denied: scenario not owned by current user",
        )

    member = session.get(Member, scenario.base_member_id)
    if not member:
        raise ResourceNotFoundException(
            message="基础成员不存在",
            details={"resource_id": str(scenario.base_member_id)},
        )

    from datetime import datetime as _dt
    import json as _json
    import zoneinfo as _zi

    from services.bazi_engine_service import calculate

    if payload.birth_dt_override:
        # 前端传来的覆盖时间（可能已带时区）
        birth_dt = _dt.fromisoformat(payload.birth_dt_override)
        if birth_dt.tzinfo is None:
            tz_name_tmp = getattr(member, "timezone", None) or "Asia/Shanghai"
            birth_dt = birth_dt.replace(tzinfo=_zi.ZoneInfo(tz_name_tmp))
    else:
        # 从成员 birth_date + birth_time_hour/minute 组合
        bd = getattr(member, "birth_date", None)
        if not bd:
            raise ValidationException(
                code=ErrorCode.VALIDATION_MISSING_FIELD,
                message="成员缺少出生日期，无法模拟",
            )
        tz_name_tmp = getattr(member, "timezone", None) or "Asia/Shanghai"
        tz_obj = _zi.ZoneInfo(tz_name_tmp)
        hh = getattr(member, "birth_time_hour", None) or 0
        mm = getattr(member, "birth_time_minute", None) or 0
        # bd 可能是 date 对象或 str
        if isinstance(bd, str):
            from datetime import date as _date

            bd = _date.fromisoformat(bd)
        birth_dt = _dt(bd.year, bd.month, bd.day, hh, mm, 0, tzinfo=tz_obj)

    lon = float(
        payload.longitude_override
        if payload.longitude_override is not None
        else (getattr(member, "birth_longitude", None) or 116.4)
    )
    # 统一 gender 值：数据库里可能存 'male'/'female' 或 'M'/'F'，计算引擎允许中英文
    _raw_gender = payload.gender_override or getattr(member, "gender", None) or "M"
    gender = _raw_gender  # bazi_engine_service.calculate 接受任意格式，内部会 normalize
    tz_name = getattr(member, "timezone", None) or "Asia/Shanghai"

    result = calculate(birth_dt, lon, tz_name, gender=gender)
    vr = result.verify_response
    favor = list(getattr(vr.yongshen, "favor", []))
    avoid = list(getattr(vr.yongshen, "avoid", []))
    geju = getattr(vr.geju, "geju_name", "") if vr.geju else ""
    wx_raw = getattr(vr, "wuxing", None)
    wx_scores: dict[str, float] = {}
    if wx_raw:
        for el in ("wood", "fire", "earth", "metal", "water"):
            v = getattr(wx_raw, el, None)
            if v is not None:
                wx_scores[el] = float(v)

    simulated_at = _dt.utcnow().replace(microsecond=0).isoformat() + "Z"
    scenario.results = _json.dumps(
        {
            "geju_name": geju,
            "yongshen_favor": favor,
            "yongshen_avoid": avoid,
            "wuxing_scores": wx_scores,
            "simulated_at": simulated_at,
            "overrides": {
                "birth_dt": payload.birth_dt_override,
                "longitude": payload.longitude_override,
                "gender": payload.gender_override,
            },
        },
        ensure_ascii=False,
    )
    if payload.note:
        scenario.description = payload.note
    scenario.updated_at = _dt.now(UTC)
    session.add(scenario)
    session.commit()

    log_action(
        session,
        user_id=current_user.id or 0,
        action="simulate_scenario",
        resource_type="scenario",
        resource_id=str(scenario_id),
        details={"geju": geju, "favor": favor},
    )

    return SimulateResponse(
        scenario_id=scenario_id,
        geju_name=geju,
        yongshen_favor=favor,
        yongshen_avoid=avoid,
        wuxing_scores=wx_scores,
        note=payload.note or "",
        simulated_at=simulated_at,
    )
