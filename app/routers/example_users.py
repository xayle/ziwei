"""
示例路由：展示如何使用新的错误处理和文档系统
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional, List

from app.dependencies.auth import (
    get_current_user,
    require_user,
    User,
)
from app.exceptions import (
    ValidationException,
    AuthenticationException,
    AuthorizationException,
    ResourceNotFoundException,
    ErrorCode,
)
from app.models.base import User as UserModel
from app.error_handling import handle_exceptions
from pydantic import BaseModel, EmailStr, Field


# ============================================================================
# 数据模型定义
# ============================================================================

class UserCreateRequest(BaseModel):
    """用户创建请求"""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8)
    
    class Config:
        json_schema_extra = {
            "example": {
                "username": "john_doe",
                "email": "john@example.com",
                "password": "SecurePass123",
            }
        }


class UserUpdateRequest(BaseModel):
    """用户更新请求"""
    email: Optional[EmailStr] = None
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "newemail@example.com",
                "username": "new_username",
            }
        }


class UserResponse(BaseModel):
    """用户响应模型"""
    id: int
    username: str
    email: str
    is_active: bool
    created_at: datetime
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": 1,
                "username": "john_doe",
                "email": "john@example.com",
                "is_active": True,
                "created_at": "2026-01-01T00:00:00",
            }
        }


# ============================================================================
# 路由定义
# ============================================================================

router = APIRouter(
    prefix="/api/v1/users",
    tags=["users"],
    responses={
        401: {
            "description": "Unauthorized",
            "content": {
                "application/json": {
                    "example": {
                        "error": {
                            "code": "AUTH_001",
                            "message": "Missing authorization token",
                        }
                    }
                }
            },
        },
        403: {
            "description": "Permission denied",
            "content": {
                "application/json": {
                    "example": {
                        "error": {
                            "code": "AUTHZ_001",
                            "message": "Permission denied",
                        }
                    }
                }
            },
        },
        422: {
            "description": "Validation error",
            "content": {
                "application/json": {
                    "example": {
                        "error": {
                            "code": "VALIDATION_001",
                            "message": "Validation failed",
                            "details": {"field": "email", "reason": "Invalid format"},
                        }
                    }
                }
            },
        },
    },
)


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    summary="获取用户信息",
    description="根据用户 ID 获取用户详细信息",
)
@handle_exceptions(default_error_code=ErrorCode.SYSTEM_INTERNAL_ERROR)
async def get_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    """
    获取用户信息
    
    - **user_id**: 用户 ID
    - **Returns**: 用户详细信息
    
    错误码:
    - `RESOURCE_001`: 资源不存在
    """
    if user_id <= 0:
        raise ValidationException(
            code=ErrorCode.VALIDATION_INVALID_INPUT,
            message="Invalid user_id",
            details={"field": "user_id", "issue": "must be positive"},
        )
    
    # 模拟数据库查询
    if user_id == 999:
        raise ResourceNotFoundException(
            code=ErrorCode.RESOURCE_NOT_FOUND,
            message=f"User {user_id} not found",
            details={"resource_type": "User", "resource_id": user_id},
        )
    
    return UserResponse(
        id=user_id,
        username="john_doe",
        email="john@example.com",
        is_active=True,
        created_at=datetime.now(),
    )


@router.post(
    "",
    response_model=UserResponse,
    status_code=201,
    summary="创建新用户",
    description="创建一个新的用户账户",
)
@handle_exceptions(default_error_code=ErrorCode.SYSTEM_INTERNAL_ERROR)
async def create_user(
    request: UserCreateRequest,
    current_user: User = Depends(require_user),
) -> UserResponse:
    """
    创建新用户
    
    - **username**: 用户名 (3-50 字符)
    - **email**: 邮箱地址
    - **password**: 密码 (至少 8 字符)
    - **Returns**: 创建的用户信息
    
    错误码:
    - `VALIDATION_001`: 输入验证失败
    - `VALIDATION_002`: 重复的邮箱
    """
    # 验证用户名
    if len(request.username) < 3:
        raise ValidationException(
            code=ErrorCode.VALIDATION_INVALID_INPUT,
            message="Username too short",
            details={"field": "username", "min_length": 3, "provided": len(request.username)},
        )
    
    # 验证邮箱
    if not request.email:
        raise ValidationException(
            code=ErrorCode.VALIDATION_INVALID_INPUT,
            message="Email is required",
            details={"field": "email"},
        )
    
    # 模拟邮箱重复检查
    if request.email == "duplicate@example.com":
        raise ValidationException(
            code=ErrorCode.RESOURCE_ALREADY_EXISTS,
            message="Email already exists",
            details={"field": "email", "value": request.email},
        )
    
    return UserResponse(
        id=1,
        username=request.username,
        email=request.email,
        is_active=True,
        created_at=datetime.now(),
    )


@router.put(
    "/{user_id}",
    response_model=UserResponse,
    summary="更新用户信息",
    description="更新指定用户的信息",
)
@handle_exceptions(default_error_code=ErrorCode.SYSTEM_INTERNAL_ERROR)
async def update_user(
    user_id: int,
    request: UserUpdateRequest,
    current_user: User = Depends(require_user),
) -> UserResponse:
    """
    更新用户信息
    
    - **user_id**: 用户 ID
    - **email**: 新邮箱 (可选)
    - **username**: 新用户名 (可选)
    - **Returns**: 更新后的用户信息
    
    错误码:
    - `AUTHZ_001`: 权限不足
    - `RESOURCE_001`: 资源不存在
    - `VALIDATION_001`: 验证失败
    """
    # 权限检查
    if current_user.id != user_id and not hasattr(current_user, 'is_admin'):
        raise AuthorizationException(
            code=ErrorCode.AUTHZ_PERMISSION_DENIED,
            message="Cannot update another user",
            details={"user_id": user_id, "current_user": current_user.id},
        )
    
    # 检查用户是否存在
    if user_id == 999:
        raise ResourceNotFoundException(
            code=ErrorCode.RESOURCE_NOT_FOUND,
            message=f"User {user_id} not found",
            details={"resource_type": "User", "resource_id": user_id},
        )
    
    return UserResponse(
        id=user_id,
        username=request.username or "john_doe",
        email=request.email or "john@example.com",
        is_active=True,
        created_at=datetime.now(),
    )


@router.delete(
    "/{user_id}",
    status_code=204,
    summary="删除用户",
    description="删除指定的用户账户",
)
@handle_exceptions(default_error_code=ErrorCode.SYSTEM_INTERNAL_ERROR)
async def delete_user(
    user_id: int,
    current_user: User = Depends(require_user),
) -> None:
    """
    删除用户
    
    - **user_id**: 用户 ID
    
    错误码:
    - `AUTHZ_001`: 权限不足
    - `RESOURCE_001`: 资源不存在
    """
    # 权限检查
    if current_user.id != user_id and not hasattr(current_user, 'is_admin'):
        raise AuthorizationException(
            code=ErrorCode.AUTHZ_PERMISSION_DENIED,
            message="Cannot delete another user",
            details={"user_id": user_id, "current_user": current_user.id},
        )
    
    # 检查用户是否存在
    if user_id == 999:
        raise ResourceNotFoundException(
            code=ErrorCode.RESOURCE_NOT_FOUND,
            message=f"User {user_id} not found",
            details={"resource_type": "User", "resource_id": user_id},
        )


@router.get(
    "",
    response_model=List[UserResponse],
    summary="列出所有用户",
    description="获取用户列表 (需要管理员权限)",
)
@handle_exceptions(default_error_code=ErrorCode.SYSTEM_INTERNAL_ERROR)
async def list_users(
    skip: int = 0,
    limit: int = 10,
    current_user: User = Depends(require_user),
) -> List[UserResponse]:
    """
    列出所有用户
    
    - **skip**: 跳过的记录数
    - **limit**: 返回的最大记录数
    - **Returns**: 用户列表
    
    错误码:
    - `AUTHZ_001`: 需要管理员权限
    - `VALIDATION_001`: 参数验证失败
    """
    # 权限检查
    if not hasattr(current_user, 'is_admin') or not current_user.is_admin:
        raise AuthorizationException(
            code=ErrorCode.AUTHZ_PERMISSION_DENIED,
            message="Admin privileges required",
            details={"required": "admin", "current": "user"},
        )
    
    # 参数验证
    if skip < 0 or limit < 1:
        raise ValidationException(
            code=ErrorCode.VALIDATION_INVALID_INPUT,
            message="Invalid pagination parameters",
            details={"skip": skip, "limit": limit},
        )
    
    return [
        UserResponse(
            id=1,
            username="john_doe",
            email="john@example.com",
            is_active=True,
            created_at=datetime.now(),
        )
    ]
