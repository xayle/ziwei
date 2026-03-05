"""
身份验证路由 - 登录、登出、权限检查
"""
import logging
import re
from datetime import datetime, timezone
from pydantic import BaseModel, field_validator
from fastapi import APIRouter, Depends, Request
from sqlmodel import Session, select

from db import get_session
from app.models import User, RefreshToken
from app.dependencies.auth import _auth_bypass_enabled
from app.exceptions import (
    AuthenticationException,
    ValidationException,
    AuthorizationException,
    ResourceNotFoundException,
    ResourceConflictException,
    BusinessException,
    ErrorCode,
)
from app.error_handling import handle_exceptions
from services.auth_service import (
    create_access_token,
    hash_password,
    verify_password,
    TokenResponse,
    TokenPayload,
    create_refresh_token_record,
    revoke_refresh_token,
    revoke_all_user_tokens,
    verify_token,
)
from services.rate_limit import limiter

router = APIRouter(prefix="/api/v1", tags=["auth"])
logger = logging.getLogger(__name__)


def get_current_user_from_token(
    request: Request,
    session: Session = Depends(get_session)
) -> TokenPayload:
    """
    ✅ 从 Authorization header 提取并验证 JWT Token
    返回 TokenPayload 对象，如果验证失败返回 401
    """
    # 本地联调直接绕过鉴权，保持接口可用
    if _auth_bypass_enabled():
        return TokenPayload(user_id=0, username="local", role="owner")

    auth_header = request.headers.get("Authorization")
    if not auth_header:
        raise AuthenticationException(
            code=ErrorCode.AUTH_MISSING_TOKEN,
            message="Authorization header required",
        )
    
    parts = auth_header.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise AuthenticationException(
            code=ErrorCode.AUTH_TOKEN_INVALID,
            message="Invalid authorization header format",
            details={"header": auth_header[:20] + "..." if len(auth_header) > 20 else auth_header},
        )
    
    token = parts[1]
    payload = verify_token(token)
    
    if not payload:
        raise AuthenticationException(
            code=ErrorCode.AUTH_TOKEN_INVALID,
            message="Invalid or expired token",
        )
    
    return payload


# ✅ 别名，用于依赖注入
async def require_user(
    user: TokenPayload = Depends(get_current_user_from_token)
) -> TokenPayload:
    """强制认证的依赖函数"""
    if _auth_bypass_enabled():
        return TokenPayload(user_id=0, username="local", role="owner")
    if user is None:
        raise AuthenticationException(
            code=ErrorCode.AUTH_TOKEN_INVALID,
            message="Authentication required",
        )
    return user


class LoginRequest(BaseModel):
    """登录请求"""
    username: str
    password: str
    
    @field_validator('username')
    @classmethod
    def validate_username(cls, v: str) -> str:
        """验证用户名格式"""
        if not v or len(v) < 3:
            raise ValueError('用户名至少3个字符')
        if len(v) > 50:
            raise ValueError('用户名不超过50个字符')
        if not re.match(r'^[a-zA-Z0-9_]+$', v):
            raise ValueError('用户名只能包含字母、数字和下划线')
        return v
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        """验证密码基本要求"""
        if not v or len(v) < 8:
            raise ValueError('密码至少8个字符')
        return v


class RegisterRequest(BaseModel):
    """注册请求"""
    username: str
    email: str  # 使用自定义验证器验证邮箱格式
    password: str
    
    @field_validator('username')
    @classmethod
    def validate_username(cls, v: str) -> str:
        """验证用户名格式"""
        if not v or len(v) < 3:
            raise ValueError('用户名至少3个字符')
        if len(v) > 50:
            raise ValueError('用户名不超过50个字符')
        if not re.match(r'^[a-zA-Z0-9_]+$', v):
            raise ValueError('用户名只能包含字母、数字和下划线')
        return v
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v: str) -> str:
        """验证邮箱格式"""
        if not v:
            raise ValueError('邮箱不能为空')
        # 简单的邮箱格式验证
        email_pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
        if not re.match(email_pattern, v):
            raise ValueError('邮箱格式不正确')
        if len(v) > 255:
            raise ValueError('邮箱不超过255个字符')
        return v.lower()  # 统一转换为小写
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        """验证密码强度"""
        if not v or len(v) < 8:
            raise ValueError('密码至少8个字符')
        if len(v) > 128:
            raise ValueError('密码不超过128个字符')
        
        # 检查密码强度：至少包含字母和数字
        has_letter = bool(re.search(r'[a-zA-Z]', v))
        has_digit = bool(re.search(r'[0-9]', v))
        
        if not (has_letter and has_digit):
            raise ValueError('密码须同时包含字母和数字')
        
        return v


class ChangePasswordRequest(BaseModel):
    """修改密码请求"""
    old_password: str
    new_password: str
    
    @field_validator('new_password')
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        """验证新密码强度"""
        if not v or len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if len(v) > 128:
            raise ValueError('Password must not exceed 128 characters')
        
        # 检查密码强度：至少包含字母和数字
        has_letter = bool(re.search(r'[a-zA-Z]', v))
        has_digit = bool(re.search(r'[0-9]', v))
        
        if not (has_letter and has_digit):
            raise ValueError('Password must contain both letters and numbers')
        
        return v


class RefreshTokenRequest(BaseModel):
    """刷新令牌请求"""
    refresh_token: str


class RefreshTokenResponse(BaseModel):
    """刷新令牌响应"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


@router.post("/auth/login", response_model=TokenResponse)
@handle_exceptions(ErrorCode.SYSTEM_INTERNAL_ERROR)
@limiter.limit("5/minute")
def login(body: LoginRequest, request: Request, session: Session = Depends(get_session)):
    """
    用户登录 - 返回JWT Token並包含用户角色
    """
    # 查找用户
    statement = select(User).where(
        User.username == body.username,
        User.deleted_at.is_(None),  # type: ignore
    )
    user = session.exec(statement).first()
    
    if not user:
        raise AuthenticationException(
            code=ErrorCode.AUTH_INVALID_CREDENTIALS,
            message="Invalid username or password",
        )
    
    # 验证密码
    if not verify_password(body.password, user.password_hash):
        raise AuthenticationException(
            code=ErrorCode.AUTH_INVALID_CREDENTIALS,
            message="Invalid username or password",
        )
    
    if not user.is_active:
        raise AuthenticationException(
            code=ErrorCode.AUTH_USER_INACTIVE,
            message="User account is disabled",
        )
    
    # 生成Token（包含role）
    token_data = create_access_token(user.id or 0, user.username, role=user.role)
    
    # 创建刷新令牌（原子操作）
    try:
        ip_address = request.client.host if request.client else None
        user_agent = request.headers.get("User-Agent") or ""
        refresh_token = create_refresh_token_record(session, user.id or 0, ip_address, user_agent)
        session.commit()  # 提交 refresh_token
        token_data["refresh_token"] = refresh_token
    except Exception:
        session.rollback()  # 回滚 refresh_token 创建
        # 刷新令牌是可选的，不影响登录
        pass
    
    return TokenResponse(**token_data)


@router.post("/auth/register", response_model=TokenResponse)
@handle_exceptions(ErrorCode.SYSTEM_INTERNAL_ERROR)
@limiter.limit("3/minute")
def register(body: RegisterRequest, request: Request, session: Session = Depends(get_session)):
    """
    用户注册 - 返回JWT Token並设置无体与initial role
    """
    # 检查username是否已存在
    existing_user = session.exec(
        select(User).where(User.username == body.username)
    ).first()
    
    if existing_user:
        raise ResourceConflictException(
            code=ErrorCode.RESOURCE_ALREADY_EXISTS,
            message="Username already exists",
            resource_type="User",
            resource_id=body.username,
        )
    
    # 检查email是否已存在
    existing_email = session.exec(
        select(User).where(User.email == body.email)
    ).first()
    
    if existing_email:
        raise ResourceConflictException(
            code=ErrorCode.RESOURCE_ALREADY_EXISTS,
            message="Email already exists",
            resource_type="User",
            resource_id=body.email,
        )
    
    # 创建新用户（体质上是你的上帚-虉主）
    new_user = User(
        username=body.username,
        email=body.email,
        password_hash=hash_password(body.password),
        is_active=True,
        role="owner",  # 上帚虉下的数据可应有完整控制权
        is_admin=False,
    )
    
    # 原子操作：用户创建 + refresh_token 创建
    try:
        session.add(new_user)
        session.flush()  # 获取 user.id 但不提交
        
        # 创建刷新令牌
        ip_address = request.client.host if request.client else None
        user_agent = request.headers.get("User-Agent") or ""
        refresh_token = create_refresh_token_record(session, new_user.id or 0, ip_address, user_agent)
        
        session.commit()  # 一次性提交所有更改
        session.refresh(new_user)
        
        # 生成Token
        token_data = create_access_token(new_user.id or 0, new_user.username, role=new_user.role)
        token_data["refresh_token"] = refresh_token
        
        return TokenResponse(**token_data)
    except Exception as exc:
        session.rollback()  # 回滚所有更改
        logger.error(f"User registration failed for username={body.username}: {exc}", exc_info=True)
        raise BusinessException(
            code=ErrorCode.BUSINESS_OPERATION_FAILED,
            message="Registration failed",
            details={"username": body.username},
        )


@router.get("/auth/me")
@handle_exceptions(ErrorCode.SYSTEM_INTERNAL_ERROR)
def get_current_user_info(
    session: Session = Depends(get_session),
    user: TokenPayload = Depends(require_user)
):
    """
    获取当前用户信息 - 返回登录用户的详细信息
    需要有效的Authorization Bearer token
    """
    # 从数据库获取最新用户信息
    db_user = session.exec(
        select(User).where(User.id == user.user_id, User.deleted_at.is_(None))  # type: ignore
    ).first()
    
    if not db_user:
        raise ResourceNotFoundException(
            code=ErrorCode.RESOURCE_NOT_FOUND,
            message="User not found",
            resource_type="User",
            resource_id=str(user.user_id),
        )
    
    return {
        "user_id": db_user.id,
        "username": db_user.username,
        "email": db_user.email,
        "role": db_user.role,
        "is_active": db_user.is_active,
        "is_admin": db_user.is_admin,
        "created_at": db_user.created_at.isoformat(),
        "updated_at": db_user.updated_at.isoformat(),
        "token_type": "bearer",
        "token_iat": user.iat.isoformat() if user.iat else None,
        "token_exp": user.exp.isoformat() if user.exp else None,
    }


@router.post("/auth/refresh", response_model=RefreshTokenResponse)
@handle_exceptions(ErrorCode.SYSTEM_INTERNAL_ERROR)
def refresh_token(
    body: RefreshTokenRequest,
    request: Request,
    session: Session = Depends(get_session),
):
    """
    使用刷新令牌获取新的访问令牌
    
    Args:
        body: 包含刷新令牌
        request: HTTP请求对象
        session: 数据库会话
        
    Returns:
        新的访问令牌和刷新令牌
    """
    # 查询刷新令牌
    refresh_token_obj = session.exec(
        select(RefreshToken).where(
            RefreshToken.token == body.refresh_token,
            RefreshToken.deleted_at.is_(None)  # type: ignore
        )
    ).first()
    
    if not refresh_token_obj or refresh_token_obj.is_revoked:
        raise AuthenticationException(
            code=ErrorCode.AUTH_INVALID_REFRESH_TOKEN,
            message="Invalid or revoked refresh token",
        )
    
    # 检查刷新令牌是否过期
    if datetime.now(timezone.utc) > refresh_token_obj.expires_at:
        raise AuthenticationException(
            code=ErrorCode.AUTH_TOKEN_EXPIRED,
            message="Refresh token expired",
        )
    
    # 获取用户信息
    user = session.exec(
        select(User).where(User.id == refresh_token_obj.user_id, User.deleted_at.is_(None))  # type: ignore
    ).first()
    if not user or not user.is_active:
        raise AuthenticationException(
            code=ErrorCode.AUTH_USER_INACTIVE,
            message="User not found or inactive",
        )
    
    # 生成新的访问令牌
    new_token_data = create_access_token(user.id or 0, user.username, role=user.role)
    
    # 生成新的刷新令牌
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("User-Agent") or ""
    new_refresh_token = create_refresh_token_record(session, user.id or 0, ip_address, user_agent)
    
    # 撤销旧的刷新令牌（Refresh Token 旋转）0.10）
    revoke_refresh_token(session, body.refresh_token)

    return RefreshTokenResponse(
        access_token=new_token_data["access_token"],
        refresh_token=new_refresh_token,
        token_type=new_token_data["token_type"],
        expires_in=new_token_data["expires_in"],
    )


@router.post("/auth/logout", status_code=204)
@handle_exceptions(ErrorCode.SYSTEM_INTERNAL_ERROR)
def logout(
    body: RefreshTokenRequest,
    session: Session = Depends(get_session),
):
    """
    用户登出 - 撤销刷新令牌
    
    Args:
        body: 包含刷新令牌
        session: 数据库会话
    """
    try:
        revoke_refresh_token(session, body.refresh_token)
    except Exception:
        # 即使撤销失败也返回成功
        pass


@router.post("/auth/change-password", status_code=200)
@handle_exceptions(ErrorCode.SYSTEM_INTERNAL_ERROR)
def change_password(
    body: ChangePasswordRequest,
    session: Session = Depends(get_session),
    user: TokenPayload = Depends(require_user)
):
    """
    修改密码 - ✅ 修改后自动撤销所有旧 RefreshToken
    
    Args:
        body: 包含旧密码和新密码
        session: 数据库会话
        user: 当前用户信息
        
    Returns:
        成功消息
    """
    # 从数据库获取用户
    db_user = session.exec(
        select(User).where(User.id == user.user_id, User.deleted_at.is_(None))  # type: ignore
    ).first()
    
    if not db_user:
        raise ResourceNotFoundException(
            code=ErrorCode.RESOURCE_NOT_FOUND,
            message="User not found",
            resource_type="User",
            resource_id=str(user.user_id),
        )
    
    # 验证旧密码是否正确
    if not verify_password(body.old_password, db_user.password_hash):
        raise AuthenticationException(
            code=ErrorCode.AUTH_INVALID_CREDENTIALS,
            message="Old password is incorrect",
        )
    
    # 新旧密码不能相同
    if body.old_password == body.new_password:
        raise ValidationException(
            code=ErrorCode.VALIDATION_INVALID_INPUT,
            message="New password must be different from old password",
        )
    
    try:
        # ✅ 更新密码
        db_user.password_hash = hash_password(body.new_password)
        db_user.updated_at = datetime.now(timezone.utc)
        session.add(db_user)
        session.flush()
        
        # ✅ 撤销所有旧 RefreshToken（强制用户重新登录）
        revoke_all_user_tokens(session, user.user_id)
        
        session.commit()
        
        return {"message": "Password changed successfully. Please login again."}
    except Exception as exc:
        session.rollback()
        logger.error(f"Password change failed for user_id={user.user_id}: {exc}", exc_info=True)
        raise BusinessException(
            code=ErrorCode.BUSINESS_OPERATION_FAILED,
            message="Failed to change password",
            details={"user_id": user.user_id},
        )
