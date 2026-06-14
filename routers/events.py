"""
事件管理路由 - 存储和查询八字计算结果
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
from app.models import Event, Member, User
from db import get_session
from services.delegation_service import log_action
from services.json_validators import EventJsonValidator
from services.optimization_tools import QueryCache
from services.permission_service import Permission, Role, has_permission

# [A1 Phase2] 模块级单例 — 跨请求共享缓存（避免每次请求重新实例化导致缓存失效）
_events_cache = QueryCache(cache_seconds=300)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["events"])


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


class EventCreateRequest(BaseModel):
    """创建事件请求"""

    member_id: int
    name: str
    event_type: str  # "verification", "consultation", "prediction", etc.
    bazi_json: str  # 完整的BaZi计算结果
    pillars_primary: str | None = None
    ten_gods: str | None = None
    five_elements: str | None = None
    L_level: int = 0
    confidence_score: float = 0.0
    recommendation: str | None = None
    recommendation_engine: str | None = None

    @field_validator("bazi_json")
    @classmethod
    def validate_bazi_json(cls, v: str) -> str:
        return _validate_json_field(v, "bazi_json", dict) or v

    @field_validator("pillars_primary")
    @classmethod
    def validate_pillars_primary(cls, v: str | None) -> str | None:
        return _validate_json_field(v, "pillars_primary", dict)

    @field_validator("ten_gods")
    @classmethod
    def validate_ten_gods(cls, v: str | None) -> str | None:
        return _validate_json_field(v, "ten_gods", list)

    @field_validator("five_elements")
    @classmethod
    def validate_five_elements(cls, v: str | None) -> str | None:
        return _validate_json_field(v, "five_elements", dict)

    @field_validator("recommendation")
    @classmethod
    def validate_recommendation(cls, v: str | None) -> str | None:
        return _validate_json_field(v, "recommendation", dict)


class EventUpdateRequest(BaseModel):
    """部分更新事件请求（PATCH）— 所有字段可选，不允许修改计算结果 bazi_json"""

    name: str | None = None
    event_type: str | None = None
    L_level: int | None = None
    confidence_score: float | None = None
    recommendation: str | None = None
    recommendation_engine: str | None = None
    pillars_primary: str | None = None
    ten_gods: str | None = None
    five_elements: str | None = None

    @field_validator("recommendation")
    @classmethod
    def validate_recommendation(cls, v: str | None) -> str | None:
        return _validate_json_field(v, "recommendation", dict)

    @field_validator("pillars_primary")
    @classmethod
    def validate_pillars_primary(cls, v: str | None) -> str | None:
        return _validate_json_field(v, "pillars_primary", dict)

    @field_validator("ten_gods")
    @classmethod
    def validate_ten_gods(cls, v: str | None) -> str | None:
        return _validate_json_field(v, "ten_gods", list)

    @field_validator("five_elements")
    @classmethod
    def validate_five_elements(cls, v: str | None) -> str | None:
        return _validate_json_field(v, "five_elements", dict)


class EventResponse(BaseModel):
    """事件响应"""

    model_config = ConfigDict(from_attributes=True)
    id: int
    owner_id: int
    member_id: int
    name: str
    event_type: str
    bazi_json: str
    pillars_primary: str | None
    ten_gods: str | None
    five_elements: str | None
    L_level: int
    confidence_score: float
    recommendation: str | None
    recommendation_engine: str | None
    created_at: datetime
    updated_at: datetime


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
            message="You don't have permission to access this member",
        )

    return member


@router.post("/events", response_model=EventResponse, status_code=201)
@handle_exceptions(ErrorCode.SYSTEM_INTERNAL_ERROR)
def create_event(
    body: EventCreateRequest,
    current_user: RequiredUser,
    session: Session = Depends(get_session),
):
    """
    创建事件 - 存储八字计算结果
    需要权限：CREATE_EVENT
    """
    # 检查权限
    user_role = Role(current_user.role)
    if not has_permission(user_role, Permission.CREATE_EVENT):
        raise AuthorizationException(
            code=ErrorCode.AUTHZ_PERMISSION_DENIED,
            message="Permission denied: create_event required",
        )

    # 验证成员存在且属于当前用户
    check_member_ownership(session, current_user, body.member_id)

    # ✅ 验证 JSON 字段的结构和内容
    try:
        # 验证 bazi_json
        EventJsonValidator.validate_bazi_json(body.bazi_json)

        # 验证 recommendation（如果提供）
        if body.recommendation:
            EventJsonValidator.validate_recommendation(body.recommendation)

        # 验证 five_elements（如果提供）
        if body.five_elements:
            EventJsonValidator.validate_five_elements(body.five_elements)

        logger.info(f"Event JSON validation passed for member_id={body.member_id}")
    except (ValueError, ValidationError) as e:
        logger.warning(f"Event JSON validation failed: {e!s}")
        raise ValidationException(
            code=ErrorCode.VALIDATION_INVALID_JSON,
            message=f"Invalid JSON data format: {e!s}",
        )

    # 创建事件
    new_event = Event(
        owner_id=current_user.id or 0,
        member_id=body.member_id,
        name=body.name,
        event_type=body.event_type,
        bazi_json=body.bazi_json,
        pillars_primary=body.pillars_primary,
        ten_gods=body.ten_gods,
        five_elements=body.five_elements,
        L_level=body.L_level,
        confidence_score=body.confidence_score,
        recommendation=body.recommendation,
        recommendation_engine=body.recommendation_engine,
    )

    try:
        session.add(new_event)
        session.commit()
        session.refresh(new_event)
    except IntegrityError:
        session.rollback()
        raise BusinessException(
            code=ErrorCode.BUSINESS_OPERATION_FAILED,
            message="Event creation failed",
        )

    # 记录审计日志
    log_action(
        session,
        user_id=current_user.id or 0,
        action="create_event",
        resource_type="event",
        resource_id=str(new_event.id),
        details={
            "member_id": body.member_id,
            "name": body.name,
            "event_type": body.event_type,
            "L_level": body.L_level,
        },
    )

    # 写操作后立即使缓存失效
    _events_cache.clear(pattern=f"events:{current_user.id}")
    return EventResponse.model_validate(new_event)


@router.get("/events")
@handle_exceptions(ErrorCode.SYSTEM_INTERNAL_ERROR)
def list_events(
    current_user: RequiredUser,
    session: Session = Depends(get_session),
    member_id: int | None = None,
    event_type: str | None = None,
    limit: int = Query(20, ge=1, le=100, description="每页数量"),
    last_id: int = Query(0, ge=0, description="最后一条记录的ID（游标分页）"),
):
    """
    列出用户的事件 - 支持分页、过滤和缓存

    性能优化:
    - 使用 Keyset 分页代替 OFFSET/LIMIT（快 25 倍）
    - 缓存结果 5 分钟
    - 支持按 member_id 和 event_type 过滤

    参数:
    - member_id: 按成员ID过滤（可选）
    - event_type: 按事件类型过滤（可选）
    - limit: 每页事件数（默认20，最多100）
    - last_id: 游标（上一页最后的ID）
    """
    # 检查权限
    user_role = Role(current_user.role)
    if not has_permission(user_role, Permission.READ_EVENT):
        raise AuthorizationException(
            code=ErrorCode.AUTHZ_PERMISSION_DENIED,
            message="Permission denied: read_event required",
        )

    # ✅ 第一步：尝试从缓存获取
    cache = _events_cache
    cache_key = f"events:{current_user.id}:{member_id}:{event_type}:{last_id}:{limit}"

    cached_result = cache.get(cache_key)
    if cached_result:
        return cached_result

    # ✅ 第二步：验证成员所有权（如果指定了 member_id）
    if member_id:
        check_member_ownership(session, current_user, member_id)

    # ✅ 第三步：构建基础过滤条件（不含游标/limit）
    base_filters = [Event.owner_id == current_user.id, Event.deleted_at.is_(None)]  # type: ignore[union-attr]
    if member_id:
        base_filters.append(Event.member_id == member_id)  # type: ignore[arg-type]
    if event_type:
        base_filters.append(Event.event_type == event_type)  # type: ignore[arg-type]

    # ✅ 第四步：COUNT 查询获取真实总数（游标无关）
    count_stmt = select(func.count()).select_from(Event).where(*base_filters)
    total_count: int = session.exec(count_stmt).one()  # type: ignore[assignment]

    # ✅ 第五步：应用游标分页，获取分页数据
    data_query = select(Event).where(*base_filters)
    if last_id > 0:
        data_query = data_query.where(Event.id > last_id)  # type: ignore[operator]
    data_query = data_query.order_by(Event.id).limit(limit)  # type: ignore[arg-type]
    events = session.exec(data_query).all()

    # ✅ 第六步：准备响应
    event_responses = [EventResponse.model_validate(e) for e in events]
    next_cursor = events[-1].id if (events and len(events) == limit) else None

    result = {
        "items": event_responses,
        "next_cursor": next_cursor,
        "total": total_count,
    }

    # ✅ 第六步：缓存结果 5 分钟
    cache.set(cache_key, result)

    return result


@router.get("/events/stats", summary="事件类型分布统计")
@handle_exceptions(ErrorCode.SYSTEM_INTERNAL_ERROR)
def get_events_stats(
    current_user: RequiredUser,
    session: Session = Depends(get_session),
    date_from: str | None = Query(None, description="起始日期 YYYY-MM-DD（含）"),
    date_to: str | None = Query(None, description="截止日期 YYYY-MM-DD（含）"),
):
    """
    D5: 统计当前用户的事件按 event_type 分组数量。
    可选通过 date_from / date_to 过滤 created_at 范围（闭区间）。
    返回 { total, by_type: [{event_type, count}] }
    """
    from datetime import datetime as _dt

    from sqlalchemy import func as sa_func

    stmt = (
        select(Event.event_type, sa_func.count(Event.id).label("count"))
        .where(Event.owner_id == current_user.id)
        .where(Event.deleted_at.is_(None))  # type: ignore[union-attr]
    )
    if date_from:
        try:
            df = _dt.strptime(date_from, "%Y-%m-%d").replace(tzinfo=UTC)
            stmt = stmt.where(Event.created_at >= df)  # type: ignore[operator]
        except ValueError:
            raise BusinessException(code=ErrorCode.VALIDATION_FAILED, message="date_from 格式错误，请使用 YYYY-MM-DD")
    if date_to:
        try:
            from datetime import timedelta as _td

            dt_ = _dt.strptime(date_to, "%Y-%m-%d").replace(tzinfo=UTC) + _td(days=1)
            stmt = stmt.where(Event.created_at < dt_)  # type: ignore[operator]
        except ValueError:
            raise BusinessException(code=ErrorCode.VALIDATION_FAILED, message="date_to 格式错误，请使用 YYYY-MM-DD")
    stmt = stmt.group_by(Event.event_type).order_by(sa_func.count(Event.id).desc())  # type: ignore[arg-type]
    rows = session.exec(stmt).all()
    by_type = [{"event_type": r[0], "count": r[1]} for r in rows]
    return {"total": sum(r["count"] for r in by_type), "by_type": by_type}


@router.get("/events/{event_id}")
@handle_exceptions(ErrorCode.SYSTEM_INTERNAL_ERROR)
def get_event(
    event_id: int,
    current_user: RequiredUser,
    session: Session = Depends(get_session),
):
    """
    获取单个事件详情
    需要权限：READ_EVENT
    """
    # 检查权限
    user_role = Role(current_user.role)
    if not has_permission(user_role, Permission.READ_EVENT):
        raise AuthorizationException(
            code=ErrorCode.AUTHZ_PERMISSION_DENIED,
            message="Permission denied: read_event required",
        )

    event = session.exec(
        select(Event).where(Event.id == event_id, Event.deleted_at.is_(None))  # type: ignore[union-attr]
    ).first()

    if not event:
        raise ResourceNotFoundException(
            message="Event not found",
            details={"resource_type": "event", "resource_id": event_id},
        )

    # 检查所有权
    if event.owner_id != current_user.id:
        raise AuthorizationException(
            code=ErrorCode.AUTHZ_PERMISSION_DENIED,
            message="You don't have permission to access this event",
        )

    return EventResponse.model_validate(event)


@router.patch("/events/{event_id}")
@handle_exceptions(ErrorCode.SYSTEM_INTERNAL_ERROR)
def patch_event(
    event_id: int,
    body: EventUpdateRequest,
    current_user: RequiredUser,
    session: Session = Depends(get_session),
):
    """
    部分更新事件（仅修改提供的字段）
    不允许修改 bazi_json：计算结果应通过重新计算生成
    需要权限：UPDATE_EVENT
    """
    user_role = Role(current_user.role)
    if not has_permission(user_role, Permission.UPDATE_EVENT):
        raise AuthorizationException(
            code=ErrorCode.AUTHZ_PERMISSION_DENIED,
            message="Permission denied: update_event required",
        )

    event = session.exec(
        select(Event).where(Event.id == event_id, Event.deleted_at.is_(None))  # type: ignore[union-attr]
    ).first()

    if not event:
        raise ResourceNotFoundException(
            message="Event not found",
            details={"resource_type": "event", "resource_id": event_id},
        )

    if event.owner_id != current_user.id:
        raise AuthorizationException(
            code=ErrorCode.AUTHZ_PERMISSION_DENIED,
            message="You don't have permission to update this event",
        )

    # 只更新请求中显式提供的字段
    updates = body.model_dump(exclude_unset=True)
    for key, value in updates.items():
        setattr(event, key, value)
    event.updated_at = datetime.now(UTC)

    try:
        session.add(event)
        session.commit()
        session.refresh(event)
    except IntegrityError:
        session.rollback()
        raise BusinessException(
            code=ErrorCode.BUSINESS_OPERATION_FAILED,
            message="Patch failed",
        )

    log_action(
        session,
        user_id=current_user.id or 0,
        action="patch_event",
        resource_type="event",
        resource_id=str(event_id),
        details=updates,
    )

    _events_cache.clear(pattern=f"events:{current_user.id}")
    return EventResponse.model_validate(event)


@router.put("/events/{event_id}")
@handle_exceptions(ErrorCode.SYSTEM_INTERNAL_ERROR)
def update_event(
    event_id: int,
    body: EventCreateRequest,
    current_user: RequiredUser,
    session: Session = Depends(get_session),
):
    """
    更新事件
    需要权限：UPDATE_EVENT
    """
    # 检查权限
    user_role = Role(current_user.role)
    if not has_permission(user_role, Permission.UPDATE_EVENT):
        raise AuthorizationException(
            code=ErrorCode.AUTHZ_PERMISSION_DENIED,
            message="Permission denied: update_event required",
        )

    event = session.exec(
        select(Event).where(Event.id == event_id, Event.deleted_at.is_(None))  # type: ignore[union-attr]
    ).first()

    if not event:
        raise ResourceNotFoundException(
            message="Event not found",
            details={"resource_type": "event", "resource_id": event_id},
        )

    if event.owner_id != current_user.id:
        raise AuthorizationException(
            code=ErrorCode.AUTHZ_PERMISSION_DENIED,
            message="You don't have permission to update this event",
        )

    # 验证新的成员所有权
    if body.member_id != event.member_id:
        check_member_ownership(session, current_user, body.member_id)

    # 更新字段
    event.name = body.name
    event.event_type = body.event_type
    event.bazi_json = body.bazi_json
    event.pillars_primary = body.pillars_primary
    event.ten_gods = body.ten_gods
    event.five_elements = body.five_elements
    event.L_level = body.L_level
    event.confidence_score = body.confidence_score
    event.recommendation = body.recommendation
    event.recommendation_engine = body.recommendation_engine

    try:
        session.add(event)
        session.commit()
        session.refresh(event)
    except IntegrityError:
        session.rollback()
        raise BusinessException(
            code=ErrorCode.BUSINESS_OPERATION_FAILED,
            message="Update failed",
        )

    # 记录审计日志
    log_action(
        session,
        user_id=current_user.id or 0,
        action="update_event",
        resource_type="event",
        resource_id=str(event_id),
        details={"name": body.name},
    )

    _events_cache.clear(pattern=f"events:{current_user.id}")
    return EventResponse.model_validate(event)


@router.delete("/events/{event_id}", status_code=204)
@handle_exceptions(ErrorCode.SYSTEM_INTERNAL_ERROR)
def delete_event(
    event_id: int,
    current_user: RequiredUser,
    session: Session = Depends(get_session),
):
    """
    删除事件
    需要权限：DELETE_EVENT
    """
    # 检查权限
    user_role = Role(current_user.role)
    if not has_permission(user_role, Permission.DELETE_EVENT):
        raise AuthorizationException(
            code=ErrorCode.AUTHZ_PERMISSION_DENIED,
            message="Permission denied: delete_event required",
        )

    event = session.exec(
        select(Event).where(Event.id == event_id, Event.deleted_at.is_(None))  # type: ignore[union-attr]
    ).first()

    if not event:
        raise ResourceNotFoundException(
            message="Event not found",
            details={"resource_type": "event", "resource_id": event_id},
        )

    if event.owner_id != current_user.id:
        raise AuthorizationException(
            code=ErrorCode.AUTHZ_PERMISSION_DENIED,
            message="You don't have permission to delete this event",
        )

    event.deleted_at = datetime.now(UTC)
    event.updated_at = datetime.now(UTC)
    session.add(event)
    session.commit()

    # 记录审计日志
    log_action(
        session,
        user_id=current_user.id or 0,
        action="delete_event",
        resource_type="event",
        resource_id=str(event_id),
        details={"name": event.name},
    )
    _events_cache.clear(pattern=f"events:{current_user.id}")


@router.get("/members/{member_id}/events")
@handle_exceptions(ErrorCode.SYSTEM_INTERNAL_ERROR)
def list_member_events(
    member_id: int,
    current_user: RequiredUser,
    session: Session = Depends(get_session),
    last_id: int = Query(default=0, ge=0, description="游标分页起始 ID"),
    limit: int = Query(default=50, ge=1, le=200, description="每页最多返回条数"),
):
    """
    获取特定成员的所有事件（游标分页）
    需要权限：READ_EVENT
    """
    # 检查权限
    user_role = Role(current_user.role)
    if not has_permission(user_role, Permission.READ_EVENT):
        raise AuthorizationException(
            code=ErrorCode.AUTHZ_PERMISSION_DENIED,
            message="Permission denied: read_event required",
        )

    # 验证成员存在且属于当前用户
    check_member_ownership(session, current_user, member_id)

    query = select(Event).where(
        Event.member_id == member_id,
        Event.deleted_at.is_(None),  # type: ignore[union-attr]
    )
    if last_id > 0:
        query = query.where(Event.id > last_id)  # type: ignore[operator]
    query = query.order_by(Event.id).limit(limit)  # type: ignore[arg-type]
    events = session.exec(query).all()

    next_cursor = events[-1].id if (events and len(events) == limit) else None
    return {
        "events": [EventResponse.model_validate(e) for e in events],
        "next_cursor": next_cursor,
        "has_more": next_cursor is not None,
        "total_returned": len(events),
    }
