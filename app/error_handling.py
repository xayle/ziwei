"""
错误处理中间件和工具函数
"""

import logging
import json
from typing import Callable, Any, Optional
from functools import wraps
from datetime import datetime, timezone

from fastapi import Request, Response
from fastapi.exceptions import HTTPException as FastAPIHTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import status

from app.exceptions import (
    AppException,
    ErrorDetail,
    ErrorCode,
    DatabaseException,
)

logger = logging.getLogger(__name__)


# ============================================================================
# 全局异常处理中间件
# ============================================================================

class ExceptionHandlingMiddleware(BaseHTTPMiddleware):
    """处理所有未捕获的异常"""
    
    async def dispatch(self, request: Request, call_next) -> Response:
        try:
            return await call_next(request)
        
        except AppException as exc:
            # 应用程序异常 - 记录并返回友好错误
            logger.warning(
                f"Application error {exc.code.value}: {exc.message}",
                extra={
                    "request_path": request.url.path,
                    "request_method": request.method,
                    "status_code": exc.status_code,
                    "error_code": exc.code.value,
                }
            )
            
            error_detail = ErrorDetail(
                code=exc.code.value,
                message=exc.message,
                status_code=exc.status_code,
                details=exc.details,
            )
            
            return JSONResponse(
                status_code=exc.status_code,
                content=error_detail.to_dict(),
            )
        
        except Exception as exc:
            # §4.5.1: SQLite "database is locked" → 503
            if "database is locked" in str(exc).lower():
                logger.warning("SQLite database is locked: %s", request.url.path)
                return JSONResponse(
                    status_code=503,
                    content={"error": "数据库暂时不可用，请重试", "detail": "database is locked"},
                )
            # 未预期的异常 - 记录错误信息，返回通用错误
            logger.error(
                f"Unexpected error: {str(exc)}",
                exc_info=True,
                extra={
                    "request_path": request.url.path,
                    "request_method": request.method,
                    "exception_type": type(exc).__name__,
                }
            )
            
            from datetime import timezone as _tz
            error_detail = ErrorDetail(
                code=ErrorCode.SYSTEM_UNEXPECTED_ERROR.value,
                message="Internal server error",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                details={
                    "timestamp": datetime.now(_tz.utc).isoformat(),
                },
            )
            
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content=error_detail.to_dict(),
            )


# ============================================================================
# 错误处理装饰器
# ============================================================================

def handle_exceptions(
    default_error_code: ErrorCode = ErrorCode.SYSTEM_INTERNAL_ERROR,
    status_code: Optional[int] = None,
    default_status_code: Optional[int] = None,
):
    """
    装饰器：捕获函数中的异常并转换为标准格式
    
    使用示例：
    @handle_exceptions(
        default_error_code=ErrorCode.BUSINESS_OPERATION_FAILED,
        default_status_code=status.HTTP_400_BAD_REQUEST,
    )
    def my_service_function():
        ...
    """
    # 支持 status_code 和 default_status_code 两个参数名
    final_status_code = status_code if status_code is not None else (default_status_code or status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            try:
                return await func(*args, **kwargs)
            except AppException:
                # 已处理的应用异常，直接抛出
                raise
            except FastAPIHTTPException:
                # FastAPI HTTPException 直接透传，不包装为 500
                raise
            except Exception as exc:
                logger.error(
                    f"Error in {func.__name__}: {str(exc)}",
                    exc_info=True,
                )
                raise AppException(
                    code=default_error_code,
                    message="服务器内部错误，请稍后重试",
                    status_code=final_status_code,
                )
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            try:
                return func(*args, **kwargs)
            except AppException:
                # 已处理的应用异常，直接抛出
                raise
            except FastAPIHTTPException:
                # FastAPI HTTPException 直接透传，不包装为 500
                raise
            except Exception as exc:
                logger.error(
                    f"Error in {func.__name__}: {str(exc)}",
                    exc_info=True,
                )
                raise AppException(
                    code=default_error_code,
                    message="服务器内部错误，请稍后重试",
                    status_code=final_status_code,
                )
        
        # 根据函数是否异步选择包装器
        if hasattr(func, '__call__'):
            import inspect
            if inspect.iscoroutinefunction(func):
                return async_wrapper
            else:
                return sync_wrapper
        
        return sync_wrapper
    
    return decorator


def safe_execute(
    func: Callable,
    *args,
    error_code: ErrorCode = ErrorCode.SYSTEM_INTERNAL_ERROR,
    error_message: str = "Operation failed",
    **kwargs
) -> Any:
    """
    安全执行函数，捕获异常
    
    使用示例：
    result = safe_execute(
        my_function,
        arg1, arg2,
        error_code=ErrorCode.DATABASE_ERROR,
        error_message="Database operation failed",
    )
    """
    try:
        return func(*args, **kwargs)
    except AppException:
        raise
    except Exception as exc:
        logger.error(
            f"Error executing {func.__name__}: {str(exc)}",
            exc_info=True,
        )
        raise AppException(
            code=error_code,
            message=error_message,
        )


# ============================================================================
# 日志和监控相关
# ============================================================================

def log_exception(
    exc: Exception,
    context: str = "",
    level: str = "error",
) -> None:
    """
    标准化异常日志记录
    
    Args:
        exc: 异常对象
        context: 上下文描述
        level: 日志级别 (debug, info, warning, error, critical)
    """
    log_func = getattr(logger, level, logger.error)
    
    exc_type = type(exc).__name__
    exc_message = str(exc)
    
    log_data = {
        "exception_type": exc_type,
        "message": exc_message,
    }
    
    if isinstance(exc, AppException):
        log_data.update({  # type: ignore[arg-type]
            "error_code": exc.code.value,
            "status_code": exc.status_code,
            "details": exc.details,
        })
    
    if context:
        log_data["context"] = context
    
    log_func(
        f"{context}: {exc_type} - {exc_message}" if context else f"{exc_type} - {exc_message}",
        extra=log_data,
        exc_info=True,
    )


# ============================================================================
# 错误响应生成器
# ============================================================================

def create_error_response(
    code: ErrorCode,
    message: str,
    status_code: int = status.HTTP_400_BAD_REQUEST,
    details: Optional[dict] = None,
) -> tuple:
    """
    创建标准化错误响应
    
    返回: (status_code, response_dict)
    """
    error_detail = ErrorDetail(
        code=code.value,
        message=message,
        status_code=status_code,
        details=details or {},
    )
    
    return status_code, error_detail.to_dict()


# ============================================================================
# 验证和断言函数
# ============================================================================

def assert_not_none(value: Any, message: str, code: ErrorCode = ErrorCode.VALIDATION_MISSING_FIELD) -> Any:
    """断言值不为 None"""
    if value is None:
        from app.exceptions import ValidationException
        raise ValidationException(code=code, message=message)
    return value


def assert_valid_format(
    value: str,
    pattern: str,
    message: str,
    code: ErrorCode = ErrorCode.VALIDATION_INVALID_FORMAT,
) -> str:
    """断言值匹配指定的模式"""
    import re
    if not re.match(pattern, value):
        from app.exceptions import ValidationException
        raise ValidationException(code=code, message=message)
    return value


def assert_in_range(
    value: Any,
    min_value: Any = None,
    max_value: Any = None,
    message: str = "Value out of range",
    code: ErrorCode = ErrorCode.VALIDATION_INVALID_INPUT,
    min_val: Any = None,
    max_val: Any = None,
) -> Any:
    """断言值在指定范围内（支持多种参数命名）"""
    # 支持两种参数命名方式
    min_v = min_value if min_value is not None else min_val
    max_v = max_value if max_value is not None else max_val
    
    if not (min_v <= value <= max_v):
        from app.exceptions import ValidationException
        raise ValidationException(code=code, message=message)
    return value
