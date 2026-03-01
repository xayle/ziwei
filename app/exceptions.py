"""
标准化异常定义和错误处理
"""

from enum import Enum
from typing import Optional, Dict, Any
from fastapi import HTTPException, status


# ============================================================================
# 错误代码枚举
# ============================================================================

class ErrorCode(str, Enum):
    """应用程序错误代码"""
    
    # 认证相关 (AUTH_*)
    AUTH_INVALID_CREDENTIALS = "AUTH_001"
    AUTH_TOKEN_EXPIRED = "AUTH_002"
    AUTH_TOKEN_INVALID = "AUTH_003"
    AUTH_MISSING_TOKEN = "AUTH_004"
    AUTH_USER_INACTIVE = "AUTH_005"
    AUTH_INVALID_REFRESH_TOKEN = "AUTH_006"
    AUTH_PASSWORD_WEAK = "AUTH_007"
    
    # 授权相关 (AUTHZ_*)
    AUTHZ_PERMISSION_DENIED = "AUTHZ_001"
    AUTHZ_ROLE_INSUFFICIENT = "AUTHZ_002"
    AUTHZ_RESOURCE_FORBIDDEN = "AUTHZ_003"
    
    # 数据验证 (VALIDATION_*)
    VALIDATION_INVALID_INPUT = "VALIDATION_001"
    VALIDATION_MISSING_FIELD = "VALIDATION_002"
    VALIDATION_INVALID_FORMAT = "VALIDATION_003"
    VALIDATION_FILE_TOO_LARGE = "VALIDATION_004"
    VALIDATION_INVALID_JSON = "VALIDATION_005"
    
    # 资源错误 (RESOURCE_*)
    RESOURCE_NOT_FOUND = "RESOURCE_001"
    RESOURCE_ALREADY_EXISTS = "RESOURCE_002"
    RESOURCE_CONFLICT = "RESOURCE_003"
    RESOURCE_DELETED = "RESOURCE_004"
    
    # 业务逻辑错误 (BUSINESS_*)
    BUSINESS_INVALID_STATE = "BUSINESS_001"
    BUSINESS_OPERATION_FAILED = "BUSINESS_002"
    BUSINESS_CONSTRAINT_VIOLATION = "BUSINESS_003"
    BUSINESS_DEPENDENCY_ERROR = "BUSINESS_004"
    
    # 外部服务错误 (SERVICE_*)
    SERVICE_UNAVAILABLE = "SERVICE_001"
    SERVICE_TIMEOUT = "SERVICE_002"
    SERVICE_RATE_LIMITED = "SERVICE_003"
    SERVICE_EXTERNAL_ERROR = "SERVICE_004"
    
    # 系统错误 (SYSTEM_*)
    SYSTEM_INTERNAL_ERROR = "SYSTEM_001"
    SYSTEM_DATABASE_ERROR = "SYSTEM_002"
    SYSTEM_CONFIGURATION_ERROR = "SYSTEM_003"
    SYSTEM_UNEXPECTED_ERROR = "SYSTEM_999"


# ============================================================================
# 自定义异常类
# ============================================================================

class AppException(Exception):
    """应用程序基础异常"""
    
    def __init__(
        self,
        code: ErrorCode,
        message: str,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        
        super().__init__(self.message)


class AuthenticationException(AppException):
    """认证异常"""
    
    def __init__(
        self,
        code: ErrorCode,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            code=code,
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            details=details,
        )


class AuthorizationException(AppException):
    """授权异常"""
    
    def __init__(
        self,
        code: ErrorCode,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            code=code,
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
            details=details,
        )


class ValidationException(AppException):
    """数据验证异常"""
    
    def __init__(
        self,
        code: ErrorCode,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            code=code,
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details=details,
        )


class ResourceNotFoundException(AppException):
    """资源不存在异常"""
    
    def __init__(
        self,
        code: ErrorCode = ErrorCode.RESOURCE_NOT_FOUND,
        message: str = "Resource not found",
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        # 支持两种初始化方式：
        # 1. code + message + details（新方式）
        # 2. resource_type + resource_id（旧方式兼容）
        if resource_type and resource_id:
            message = f"{resource_type} with id '{resource_id}' not found"
            details = details or {"resource_type": resource_type, "resource_id": resource_id}
        
        super().__init__(
            code=code,
            message=message,
            status_code=status.HTTP_404_NOT_FOUND,
            details=details or {},
        )


class ResourceConflictException(AppException):
    """资源冲突异常"""

    def __init__(
        self,
        resource_type: str,
        code: ErrorCode = ErrorCode.RESOURCE_ALREADY_EXISTS,
        message: Optional[str] = None,
        resource_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        _message = message or f"{resource_type} already exists or conflicts with existing data"
        super().__init__(
            code=code,
            message=_message,
            status_code=status.HTTP_409_CONFLICT,
            details=details or {"resource_type": resource_type, "resource_id": resource_id},
        )


class BusinessException(AppException):
    """业务逻辑异常"""
    
    def __init__(
        self,
        code: ErrorCode,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            code=code,
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            details=details,
        )


class ServiceException(AppException):
    """外部服务异常"""
    
    def __init__(
        self,
        code: ErrorCode,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            code=code,
            message=message,
            status_code=status.HTTP_502_BAD_GATEWAY,
            details=details,
        )


class DatabaseException(AppException):
    """数据库异常"""
    
    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            code=ErrorCode.SYSTEM_DATABASE_ERROR,
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=details,
        )


# ============================================================================
# 错误响应模型
# ============================================================================

class ErrorDetail:
    """错误详情对象"""
    
    def __init__(self, code: str, message: str, status_code: int, details: Dict[str, Any]):
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "error": {
                "code": self.code,
                "message": self.message,
                "details": self.details,
            }
        }


def exception_to_http_exception(exc: AppException) -> HTTPException:
    """将应用异常转换为 HTTP 异常"""
    error_detail = ErrorDetail(
        code=exc.code.value,
        message=exc.message,
        status_code=exc.status_code,
        details=exc.details,
    )
    
    return HTTPException(
        status_code=exc.status_code,
        detail=error_detail.to_dict(),
    )
