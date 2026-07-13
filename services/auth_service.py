"""
认证服务 - JWT生成、验证、权限检查
"""

from datetime import UTC, datetime, timedelta
import hashlib
import os
import uuid

from argon2 import PasswordHasher
from argon2.exceptions import VerificationError, VerifyMismatchError
from jose import JWTError, jwt
from pydantic import BaseModel

from app.config import settings

# ✅ Week 4: 集成新的错误处理系统
from app.exceptions import (
    AuthenticationException,
    ErrorCode,
)

# 配置 - 统一从 settings 读取，env var 优先
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
ALGORITHM = "HS256"
# ✅ Priority 3.1: 读取配置而非硬编码（env var → settings → 默认15分钟）
ACCESS_TOKEN_EXPIRE_MINUTES: int = settings.jwt_access_minutes
REFRESH_TOKEN_EXPIRE_DAYS: int = settings.jwt_refresh_days
# T095 / BE-GTM-07：H5 落地页试读短 token（默认可短于正式 access）
H5_PREVIEW_EXPIRE_MINUTES: int = int(os.getenv("H5_PREVIEW_TOKEN_MINUTES", "30"))
H5_PREVIEW_SCOPE = "life_vol1_preview"
H5_PREVIEW_TOKEN_USE = "h5_preview"

# Argon2密码哈希器
_argon2_hasher = PasswordHasher()

# ============ Access Token JTI 黑名单（内存 + DB 双重持久化）============
# 内存集合用于高速查询；DB 确保进程重启后撤销不丢失
_revoked_jtis: set[str] = set()


def revoke_access_token_jti(
    jti: str,
    expires_at: datetime | None = None,
    session=None,
) -> None:
    """将 Access Token 的 JTI 加入黑名单。

    - 始终写入内存集合（同步生效）。
    - 若提供 session，同时持久化到 DB（重启后仍有效）。
    - expires_at 用于 DB 中的过期清理；若为 None 则按 ACCESS_TOKEN_EXPIRE_MINUTES 推算。
    """
    _revoked_jtis.add(jti)
    if session is not None:
        from sqlmodel import select as _select

        from app.models import RevokedJti

        # 避免重复插入（幂等）
        existing = session.exec(_select(RevokedJti).where(RevokedJti.jti == jti)).first()
        if not existing:
            exp = expires_at or datetime.now(UTC) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
            session.add(RevokedJti(jti=jti, expires_at=exp))
            try:
                session.commit()
            except Exception:
                session.rollback()


def load_revoked_jtis_from_db(session) -> int:
    """启动时将 DB 中未过期的 JTI 黑名单加载到内存集合。

    Returns:
        加载的 JTI 数量
    """
    from sqlmodel import select as _select

    from app.models import RevokedJti

    now = datetime.now(UTC)
    rows = session.exec(_select(RevokedJti).where(RevokedJti.expires_at > now)).all()
    for row in rows:
        _revoked_jtis.add(row.jti)
    return len(rows)


class TokenPayload(BaseModel):
    """JWT Token中的载荷信息"""

    user_id: int
    username: str
    role: str = "editor"  # RBAC角色
    exp: datetime | None = None
    iat: datetime | None = None


class TokenResponse(BaseModel):
    """Token响应模型"""

    access_token: str
    token_type: str = "bearer"
    expires_in: int
    role: str = "editor"  # RBAC角色信息
    refresh_token: str | None = None  # Week 3: RefreshToken支持


def hash_password(password: str) -> str:
    """
    使用Argon2哈希密码 - 企业级密码安全

    Args:
        password: 原始密码

    Returns:
        str: Argon2哈希值
    """
    return _argon2_hasher.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    验证密码是否匹配

    支持两种哈希格式:
    1. Argon2 (推荐) - 新密码
    2. SHA256 (兼容) - 旧密码，自动升级到Argon2

    Args:
        plain_password: 明文密码
        hashed_password: 存储的哈希值

    Returns:
        bool: 密码是否匹配
    """
    # 检测是否是Argon2格式 (以$argon2开头)
    if hashed_password.startswith("$argon2"):
        try:
            _argon2_hasher.verify(hashed_password, plain_password)
            return True
        except (VerifyMismatchError, VerificationError):
            return False

    # 向后兼容: 检测是否是SHA256格式 (64个十六进制字符)
    if len(hashed_password) == 64 and all(c in "0123456789abcdef" for c in hashed_password):
        sha256_result = hashlib.sha256(plain_password.encode()).hexdigest()
        return sha256_result == hashed_password

    # 未知格式，返回False
    return False


def create_access_token(
    user_id: int, username: str, role: str = "editor", expires_delta: timedelta | None = None
) -> dict:
    """创建JWT Access Token，包含RBAC角色信息"""
    if expires_delta is None:
        expires_delta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    now = datetime.now(UTC)
    expire = now + expires_delta

    payload = {
        "user_id": user_id,
        "username": username,
        "role": role,
        "exp": int(expire.timestamp()),
        "iat": int(now.timestamp()),
        "jti": str(uuid.uuid4()),  # JWT ID — 用于 Access Token 吊销
    }

    encoded_jwt = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

    return {
        "access_token": encoded_jwt,
        "token_type": "bearer",
        "expires_in": int(expires_delta.total_seconds()),
        "role": role,
    }


class H5PreviewPayload(BaseModel):
    """H5 试读短 token 声明（不可当作正式登录 access）。"""

    user_id: int
    case_id: str
    scope: str = H5_PREVIEW_SCOPE
    exp: datetime | None = None
    iat: datetime | None = None
    jti: str | None = None


def create_h5_preview_token(
    *,
    user_id: int,
    case_id: str,
    expires_delta: timedelta | None = None,
) -> dict:
    """签发绑 case 的短时 JWT，仅允许读卷一摘要（T095 / BE-GTM-07）。

    故意不含 username/role，无法通过 verify_token / 正式鉴权依赖。
    """
    if expires_delta is None:
        expires_delta = timedelta(minutes=H5_PREVIEW_EXPIRE_MINUTES)

    now = datetime.now(UTC)
    expire = now + expires_delta
    jti = str(uuid.uuid4())
    payload = {
        "token_use": H5_PREVIEW_TOKEN_USE,
        "scope": H5_PREVIEW_SCOPE,
        "user_id": user_id,
        "case_id": case_id,
        "exp": int(expire.timestamp()),
        "iat": int(now.timestamp()),
        "jti": jti,
    }
    encoded_jwt = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return {
        "access_token": encoded_jwt,
        "token_type": "bearer",
        "expires_in": int(expires_delta.total_seconds()),
        "case_id": case_id,
        "scope": H5_PREVIEW_SCOPE,
    }


def verify_h5_preview_token(token: str) -> H5PreviewPayload:
    """校验 H5 试读短 token；失败抛 AuthenticationException。"""
    if not token:
        raise AuthenticationException(
            code=ErrorCode.AUTH_MISSING_TOKEN,
            message="H5 preview token is missing",
        )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("token_use") != H5_PREVIEW_TOKEN_USE:
            raise AuthenticationException(
                code=ErrorCode.AUTH_TOKEN_INVALID,
                message="Not an H5 preview token",
            )
        if payload.get("scope") != H5_PREVIEW_SCOPE:
            raise AuthenticationException(
                code=ErrorCode.AUTH_TOKEN_INVALID,
                message="Invalid H5 preview scope",
            )
        jti = payload.get("jti")
        if jti and jti in _revoked_jtis:
            raise AuthenticationException(
                code=ErrorCode.AUTH_TOKEN_INVALID,
                message="Token has been revoked",
            )
        user_id_value = payload.get("user_id")
        case_id_value = payload.get("case_id")
        if not isinstance(user_id_value, int) or not isinstance(case_id_value, str) or not case_id_value:
            raise AuthenticationException(
                code=ErrorCode.AUTH_TOKEN_INVALID,
                message="Invalid H5 preview token structure",
            )
        exp_timestamp = payload.get("exp")
        iat_timestamp = payload.get("iat")
        return H5PreviewPayload(
            user_id=user_id_value,
            case_id=case_id_value,
            scope=str(payload.get("scope") or H5_PREVIEW_SCOPE),
            exp=datetime.fromtimestamp(exp_timestamp, tz=UTC) if exp_timestamp else None,
            iat=datetime.fromtimestamp(iat_timestamp, tz=UTC) if iat_timestamp else None,
            jti=jti if isinstance(jti, str) else None,
        )
    except AuthenticationException:
        raise
    except JWTError as e:
        if "expired" in str(e).lower():
            raise AuthenticationException(
                code=ErrorCode.AUTH_TOKEN_EXPIRED,
                message="H5 preview token has expired",
                details={"error": str(e)},
            )
        raise AuthenticationException(
            code=ErrorCode.AUTH_TOKEN_INVALID,
            message="Invalid or malformed H5 preview token",
            details={"error": str(e)},
        ) from e


def verify_token(token: str) -> TokenPayload | None:
    """
    验证JWT Token，返回payload或None如果无效

    引发:
        AuthenticationException: 令牌无效或过期
    """
    if not token:
        raise AuthenticationException(
            code=ErrorCode.AUTH_MISSING_TOKEN,
            message="Authorization token is missing",
        )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id_value = payload.get("user_id")
        username_value = payload.get("username")
        role_value = payload.get("role", "editor")

        if not isinstance(user_id_value, int) or not isinstance(username_value, str):
            raise AuthenticationException(
                code=ErrorCode.AUTH_TOKEN_INVALID,
                message="Invalid token structure",
            )

        # JTI 黑名单检查（Access Token 吊销）
        jti = payload.get("jti")
        if jti and jti in _revoked_jtis:
            raise AuthenticationException(
                code=ErrorCode.AUTH_TOKEN_INVALID,
                message="Token has been revoked",
            )

        user_id = user_id_value
        username = username_value
        role = role_value if isinstance(role_value, str) else "editor"

        exp_timestamp = payload.get("exp")
        iat_timestamp = payload.get("iat")

        exp = datetime.fromtimestamp(exp_timestamp, tz=UTC) if exp_timestamp else None
        iat = datetime.fromtimestamp(iat_timestamp, tz=UTC) if iat_timestamp else None

        return TokenPayload(
            user_id=user_id,
            username=username,
            role=role,
            exp=exp,
            iat=iat,
        )
    except JWTError as e:
        # 检查是否是过期错误
        if "expired" in str(e).lower():
            raise AuthenticationException(
                code=ErrorCode.AUTH_TOKEN_EXPIRED,
                message="Token has expired",
                details={"error": str(e)},
            )
        else:
            raise AuthenticationException(
                code=ErrorCode.AUTH_TOKEN_INVALID,
                message="Invalid or malformed token",
                details={"error": str(e)},
            )


def validate_token_exists_and_valid(token: str) -> bool:
    """快速验证token是否有效"""
    return verify_token(token) is not None


# ============ 刷新令牌管理函数 ============


def generate_refresh_token() -> str:
    """生成唯一的刷新令牌"""
    import secrets

    return secrets.token_urlsafe(32)


def create_refresh_token_record(
    session, user_id: int, ip_address: str | None = None, user_agent: str | None = None
) -> str:
    """
    创建刷新令牌记录

    Args:
        session: 数据库会话
        user_id: 用户ID
        ip_address: 请求的IP地址
        user_agent: 请求的User-Agent

    Returns:
        str: 生成的刷新令牌
    """
    from app.models import RefreshToken

    token = generate_refresh_token()
    # ✅ 使用配置常量（而非硬编码7天）
    expires_at = datetime.now(UTC) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

    refresh_token = RefreshToken(
        user_id=user_id,
        token=token,
        expires_at=expires_at,
        ip_address=ip_address,
        user_agent=user_agent,
    )

    session.add(refresh_token)
    session.commit()

    return token


def verify_refresh_token(session, user_id: int, token: str) -> bool:
    """
    验证刷新令牌是否有效

    Args:
        session: 数据库会话
        user_id: 用户ID
        token: 刷新令牌

    Returns:
        bool: 令牌是否有效

    引发:
        AuthenticationException: 令牌无效或已到期
    """
    from sqlmodel import select

    from app.models import RefreshToken

    if not token:
        raise AuthenticationException(
            code=ErrorCode.AUTH_INVALID_REFRESH_TOKEN,
            message="Refresh token is required",
        )

    try:
        refresh_token = session.exec(
            select(RefreshToken).where(
                (RefreshToken.user_id == user_id)
                & (RefreshToken.token == token)
                & (RefreshToken.is_revoked == False)
                & (RefreshToken.deleted_at.is_(None))  # type: ignore
            )
        ).first()

        if not refresh_token:
            raise AuthenticationException(
                code=ErrorCode.AUTH_INVALID_REFRESH_TOKEN,
                message="Refresh token not found or revoked",
            )

        # 检查是否过期（兼容 SQLite 返回 naive datetime 和 aware datetime）
        expires = refresh_token.expires_at
        now_utc = datetime.now(UTC)
        if expires.tzinfo is None:
            # SQLite 剥离了 tzinfo，视为 UTC 进行比较
            expires = expires.replace(tzinfo=UTC)
        if now_utc > expires:
            raise AuthenticationException(
                code=ErrorCode.AUTH_TOKEN_EXPIRED,
                message="Refresh token has expired",
                details={"expires_at": refresh_token.expires_at.isoformat()},
            )

        return True
    except AuthenticationException:
        raise
    except Exception as exc:
        raise AuthenticationException(
            code=ErrorCode.AUTH_INVALID_REFRESH_TOKEN,
            message="Failed to verify refresh token",
            details={"error": str(exc)},
        )


def revoke_refresh_token(session, token: str):
    """撤销刷新令牌"""
    from sqlmodel import select

    from app.models import RefreshToken

    refresh_token = session.exec(
        select(RefreshToken).where(RefreshToken.token == token, RefreshToken.deleted_at.is_(None))  # type: ignore
    ).first()

    if refresh_token:
        refresh_token.is_revoked = True
        session.add(refresh_token)
        session.commit()


def revoke_all_user_tokens(session, user_id: int):
    """撤销用户的所有刷新令牌 (如修改密码时调用)"""
    from sqlmodel import select

    from app.models import RefreshToken

    tokens = session.exec(
        select(RefreshToken).where(
            (RefreshToken.user_id == user_id) & (RefreshToken.is_revoked == False) & (RefreshToken.deleted_at.is_(None))  # type: ignore
        )
    ).all()

    for token in tokens:
        token.is_revoked = True
        session.add(token)

    session.commit()
