"""
全局请求验证中间件 - 验证 Content-Type、请求大小等

Priority 3.7: 请求验证中间件
"""

import logging
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger(__name__)

# 配置常量
MAX_REQUEST_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_CONTENT_TYPES = {
    "application/json",
    "multipart/form-data",
    "application/x-www-form-urlencoded",
}

# 不需要验证 Content-Type 的 HTTP 方法
METHODS_WITHOUT_BODY = {"GET", "DELETE", "HEAD", "OPTIONS"}


class RequestValidationMiddleware(BaseHTTPMiddleware):
    """
    全局请求验证中间件
    
    功能:
    1. 验证 POST/PATCH/PUT 请求的 Content-Type
    2. 验证请求大小限制(防止超大上传)
    3. 记录无效请求日志
    """

    async def dispatch(self, request: Request, call_next):
        """处理请求验证"""
        
        # 1. 验证请求大小
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                size = int(content_length)
                if size > MAX_REQUEST_SIZE:
                    _client_host = request.client.host if request.client else "unknown"
                    logger.warning(
                        f"Request too large: {size} bytes from {_client_host} "
                        f"to {request.url.path}"
                    )
                    return Response(
                        "Request entity too large",
                        status_code=413,
                        media_type="application/json",
                    )
            except ValueError:
                logger.warning(f"Invalid content-length header: {content_length}")
                return Response("Invalid content-length", status_code=400)
        
        # 2. 验证请求方法对应的 Content-Type
        if request.method not in METHODS_WITHOUT_BODY:
            content_type = request.headers.get("content-type", "").lower()
            
            # 检查是否有有效的 Content-Type
            if not content_type:
                _client_host = request.client.host if request.client else "unknown"
                logger.warning(
                    f"Missing Content-Type header for {request.method} "
                    f"from {_client_host} to {request.url.path}"
                )
                return Response(
                    "Content-Type header is required",
                    status_code=400,
                    media_type="application/json",
                )
            
            # 检查 Content-Type 是否被允许
            is_valid = any(
                allowed in content_type for allowed in ALLOWED_CONTENT_TYPES
            )
            if not is_valid:
                _client_host = request.client.host if request.client else "unknown"
                logger.warning(
                    f"Invalid Content-Type '{content_type}' for {request.method} "
                    f"from {_client_host} to {request.url.path}"
                )
                return Response(
                    f"Unsupported Content-Type. Allowed: {', '.join(ALLOWED_CONTENT_TYPES)}",
                    status_code=415,
                    media_type="application/json",
                )
        
        # 3. 继续处理请求
        response = await call_next(request)
        return response
