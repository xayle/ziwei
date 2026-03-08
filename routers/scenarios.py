"""
场景管理路由 - 支持假设推演和What-If分析
"""
import json
import logging
from datetime import datetime, timezone
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, field_validator, ValidationError
from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import func
from sqlmodel import Session, select
from sqlalchemy.exc import IntegrityError

from db import get_session
from app.models import User, Member, Scenario
from app.dependencies import require_user, RequiredUser
from services.permission_service import Permission, has_permission, Role
from services.delegation_service import log_action
from services.json_validators import ScenarioJsonValidator
from app.exceptions import (
    AuthorizationException,
    BusinessException,
    ErrorCode,
    ResourceNotFoundException,
    ValidationException,
)
from app.error_handling import handle_exceptions

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["scenarios"])


def _validate_json_field(value: Optional[str], field_name: str, expected_type: type | tuple[type, ...]) -> Optional[str]:
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
    description: Optional[str] = None
    scenario_type: str  # "time_adjustment", "location_adjustment", "custom", etc.
    variations: Optional[str] = None  # JSON object with scenario parameters
    results: Optional[str] = None  # JSON array with calculation results

    @field_validator("variations")
    @classmethod
    def validate_variations(cls, v: Optional[str]) -> Optional[str]:
        return _validate_json_field(v, "variations", dict)

    @field_validator("results")
    @classmethod
    def validate_results(cls, v: Optional[str]) -> Optional[str]:
        return _validate_json_field(v, "results", list)


class ScenarioUpdateRequest(BaseModel):
    """更新场景请求"""
    name: Optional[str] = None
    description: Optional[str] = None
    scenario_type: Optional[str] = None
    variations: Optional[str] = None
    results: Optional[str] = None

    @field_validator("variations")
    @classmethod
    def validate_variations(cls, v: Optional[str]) -> Optional[str]:
        return _validate_json_field(v, "variations", dict)

    @field_validator("results")
    @classmethod
    def validate_results(cls, v: Optional[str]) -> Optional[str]:
        return _validate_json_field(v, "results", list)


class ScenarioResponse(BaseModel):
    """场景响应"""
    model_config = ConfigDict(from_attributes=True)
    id: int
    owner_id: int
    base_member_id: int
    name: str
    description: Optional[str]
    scenario_type: str
    variations: Optional[str]
    results: Optional[str]
    created_at: datetime
    updated_at: datetime


class ScenarioListResponse(BaseModel):
    """场景分页列表响应"""
    items: List[ScenarioResponse]
    total: int
    next_cursor: Optional[int] = None


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
    user_role = Role(current_user.role)
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
            variations_data = ScenarioJsonValidator.validate_variations(body.variations)
        
        # 验证 results（如果提供）
        if body.results:
            results_data = ScenarioJsonValidator.validate_results(body.results)
        
        logger.info(f"Scenario JSON validation passed for member_id={body.base_member_id}, type={body.scenario_type}")
    except (ValueError, ValidationError) as e:
        logger.warning(f"Scenario JSON validation failed: {str(e)}")
        raise ValidationException(
            code=ErrorCode.VALIDATION_INVALID_JSON,
            message=f"Invalid JSON data format: {str(e)}",
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
            message=f"Failed to create scenario: {str(e)}",
        )


@router.get("/scenarios", response_model=ScenarioListResponse)
@handle_exceptions(ErrorCode.SYSTEM_INTERNAL_ERROR)
def list_scenarios(
    current_user: RequiredUser,
    session: Session = Depends(get_session),
    member_id: Optional[int] = None,
    scenario_type: Optional[str] = None,
    limit: int = Query(20, ge=1, le=100, description="每页数量"),
    last_id: int = Query(0, ge=0, description="游标（上一页最后 ID）"),
):
    """列表查询场景"""
    # 检查权限
    user_role = Role(current_user.role)
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
    user_role = Role(current_user.role)
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
    user_role = Role(current_user.role)
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
    
    scenario.updated_at = datetime.now(timezone.utc)
    
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
            message=f"Failed to update scenario: {str(e)}",
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
    user_role = Role(current_user.role)
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
        scenario.deleted_at = datetime.now(timezone.utc)
        scenario.updated_at = datetime.now(timezone.utc)
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
            message=f"Failed to delete scenario: {str(e)}",
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
    user_role = Role(current_user.role)
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
