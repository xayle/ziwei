"""
测试错误处理系统的完整测试套件
"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from datetime import datetime

from app.exceptions import (
    ValidationException,
    AuthenticationException,
    AuthorizationException,
    ResourceNotFoundException,
    ErrorCode,
)
from app.error_handling import (
    ExceptionHandlingMiddleware,
    handle_exceptions,
    safe_execute,
)


# ============================================================================
# 测试异常处理中间件
# ============================================================================

class TestExceptionHandlingMiddleware:
    """测试全局异常处理中间件"""
    
    def test_app_exception_handling(self):
        """测试 AppException 处理"""
        app = FastAPI()
        app.add_middleware(ExceptionHandlingMiddleware)
        
        @app.get("/test")
        def test_endpoint():
            raise ValidationException(
                code=ErrorCode.VALIDATION_INVALID_INPUT,
                message="Test error",
            )
        
        client = TestClient(app)
        response = client.get("/test")
        
        assert response.status_code == 422
        data = response.json()
        assert data["error"]["code"] == ErrorCode.VALIDATION_INVALID_INPUT.value
        assert data["error"]["message"] == "Test error"
    
    def test_unexpected_exception_handling(self):
        """测试非预期异常处理"""
        app = FastAPI()
        app.add_middleware(ExceptionHandlingMiddleware)
        
        @app.get("/test")
        def test_endpoint():
            raise ValueError("Unexpected error")
        
        client = TestClient(app)
        response = client.get("/test")
        
        assert response.status_code == 500
        data = response.json()
        assert "error" in data
        assert data["error"]["message"] == "Internal server error"
    
    def test_authentication_exception(self):
        """测试认证异常"""
        app = FastAPI()
        app.add_middleware(ExceptionHandlingMiddleware)
        
        @app.get("/test")
        def test_endpoint():
            raise AuthenticationException(
                code=ErrorCode.AUTH_INVALID_CREDENTIALS,
                message="Invalid credentials",
            )
        
        client = TestClient(app)
        response = client.get("/test")
        
        assert response.status_code == 401
        data = response.json()
        assert data["error"]["code"] == ErrorCode.AUTH_INVALID_CREDENTIALS.value
    
    def test_authorization_exception(self):
        """测试授权异常"""
        app = FastAPI()
        app.add_middleware(ExceptionHandlingMiddleware)
        
        @app.get("/test")
        def test_endpoint():
            raise AuthorizationException(
                code=ErrorCode.AUTHZ_PERMISSION_DENIED,
                message="Permission denied",
            )
        
        client = TestClient(app)
        response = client.get("/test")
        
        assert response.status_code == 403
        data = response.json()
        assert data["error"]["code"] == ErrorCode.AUTHZ_PERMISSION_DENIED.value
    
    def test_resource_not_found_exception(self):
        """测试资源未找到异常"""
        app = FastAPI()
        app.add_middleware(ExceptionHandlingMiddleware)
        
        @app.get("/test")
        def test_endpoint():
            raise ResourceNotFoundException(
                code=ErrorCode.RESOURCE_NOT_FOUND,
                message="User not found",
                details={"resource_type": "User", "resource_id": 123},
            )
        
        client = TestClient(app)
        response = client.get("/test")
        
        assert response.status_code == 404
        data = response.json()
        assert data["error"]["code"] == ErrorCode.RESOURCE_NOT_FOUND.value
        assert data["error"]["details"]["resource_id"] == 123


# ============================================================================
# 测试异常处理装饰器
# ============================================================================

class TestHandleExceptionsDecorator:
    """测试 @handle_exceptions 装饰器"""
    
    def test_sync_function_exception_handling(self):
        """测试同步函数异常处理"""
        @handle_exceptions(ErrorCode.SYSTEM_INTERNAL_ERROR)
        def test_func():
            raise ValueError("Test error")
        
        with pytest.raises(Exception):
            test_func()
    
    def test_async_function_exception_handling(self):
        """测试异步函数异常处理"""
        import asyncio
        
        @handle_exceptions(ErrorCode.SYSTEM_INTERNAL_ERROR)
        async def test_func():
            raise ValueError("Test error")
        
        with pytest.raises(Exception):
            asyncio.run(test_func())
    
    def test_decorator_with_custom_status_code(self):
        """测试装饰器自定义状态码"""
        @handle_exceptions(
            ErrorCode.VALIDATION_INVALID_INPUT,
            status_code=422
        )
        def test_func():
            raise ValueError("Validation error")
        
        with pytest.raises(Exception):
            test_func()
    
    def test_successful_function_execution(self):
        """测试成功的函数执行"""
        @handle_exceptions(ErrorCode.SYSTEM_INTERNAL_ERROR)
        def test_func():
            return "success"
        
        result = test_func()
        assert result == "success"
    
    def test_decorator_preserves_function_metadata(self):
        """测试装饰器保留函数元数据"""
        @handle_exceptions(ErrorCode.SYSTEM_INTERNAL_ERROR)
        def test_func():
            """测试函数"""
            return "success"
        
        assert test_func.__name__ == "test_func"
        assert "测试函数" in (test_func.__doc__ or "")


# ============================================================================
# 测试 safe_execute 函数
# ============================================================================

class TestSafeExecute:
    """测试 safe_execute 保护执行函数"""
    
    def test_successful_execution(self):
        """测试成功执行"""
        result = safe_execute(
            lambda: "success",
            error_code=ErrorCode.SYSTEM_INTERNAL_ERROR,
            error_message="Test error",
        )
        assert result == "success"
    
    def test_exception_wrapping(self):
        """测试异常包装"""
        from app.exceptions import AppException
        
        with pytest.raises(AppException):
            safe_execute(
                lambda: 1 / 0,
                error_code=ErrorCode.SYSTEM_INTERNAL_ERROR,
                error_message="Division error",
            )
    
    def test_custom_error_code(self):
        """测试自定义错误码"""
        from app.exceptions import AppException
        
        with pytest.raises(AppException) as exc_info:
            safe_execute(
                lambda: 1 / 0,
                error_code=ErrorCode.VALIDATION_INVALID_INPUT,
                error_message="Invalid input",
            )
        
        assert exc_info.value.code == ErrorCode.VALIDATION_INVALID_INPUT


# ============================================================================
# 测试验证函数
# ============================================================================

class TestValidationFunctions:
    """测试验证辅助函数"""
    
    def test_assert_not_none_success(self):
        """测试 assert_not_none 成功"""
        from app.error_handling import assert_not_none
        
        result = assert_not_none(
            "value",
            "Cannot be none",
            ErrorCode.VALIDATION_INVALID_INPUT
        )
        assert result == "value"
    
    def test_assert_not_none_failure(self):
        """测试 assert_not_none 失败"""
        from app.error_handling import assert_not_none
        from app.exceptions import ValidationException
        
        with pytest.raises(ValidationException):
            assert_not_none(
                None,
                "Cannot be none",
                ErrorCode.VALIDATION_INVALID_INPUT
            )
    
    def test_assert_valid_format_success(self):
        """测试 assert_valid_format 成功"""
        from app.error_handling import assert_valid_format
        import re
        
        result = assert_valid_format(
            "test@example.com",
            r"^[\w\.-]+@[\w\.-]+\.\w+$",
            "Invalid email",
            ErrorCode.VALIDATION_INVALID_INPUT
        )
        assert result == "test@example.com"
    
    def test_assert_valid_format_failure(self):
        """测试 assert_valid_format 失败"""
        from app.error_handling import assert_valid_format
        from app.exceptions import ValidationException
        import re
        
        with pytest.raises(ValidationException):
            assert_valid_format(
                "invalid-email",
                r"^[\w\.-]+@[\w\.-]+\.\w+$",
                "Invalid email",
                ErrorCode.VALIDATION_INVALID_INPUT
            )
    
    def test_assert_in_range_success(self):
        """测试 assert_in_range 成功"""
        from app.error_handling import assert_in_range
        
        result = assert_in_range(
            5,
            min_value=0,
            max_value=10,
            message="Out of range",
            code=ErrorCode.VALIDATION_INVALID_INPUT
        )
        assert result == 5
    
    def test_assert_in_range_failure(self):
        """测试 assert_in_range 失败"""
        from app.error_handling import assert_in_range
        from app.exceptions import ValidationException
        
        with pytest.raises(ValidationException):
            assert_in_range(
                15,
                min_value=0,
                max_value=10,
                message="Out of range",
                code=ErrorCode.VALIDATION_INVALID_INPUT
            )


# ============================================================================
# 集成测试
# ============================================================================

class TestErrorHandlingIntegration:
    """集成测试：测试完整的错误处理流程"""
    
    def test_validation_error_flow(self):
        """测试验证错误的完整流程"""
        from fastapi import Body
        
        app = FastAPI()
        app.add_middleware(ExceptionHandlingMiddleware)
        
        @app.post("/test")
        @handle_exceptions(ErrorCode.SYSTEM_INTERNAL_ERROR)
        def test_endpoint(value: int = Body(..., embed=True)):
            from app.error_handling import assert_in_range
            
            assert_in_range(
                value,
                min_value=0,
                max_value=100,
                message="Value out of range",
                code=ErrorCode.VALIDATION_INVALID_INPUT
            )
            return {"result": value}
        
        client = TestClient(app)
        
        # 成功的请求
        response = client.post("/test", json={"value": 50})
        assert response.status_code == 200
        
        # 失败的请求
        response = client.post("/test", json={"value": 150})
        assert response.status_code == 422
        data = response.json()
        assert data["error"]["code"] == ErrorCode.VALIDATION_INVALID_INPUT.value
    
    def test_authorization_error_flow(self):
        """测试授权错误的完整流程"""
        app = FastAPI()
        app.add_middleware(ExceptionHandlingMiddleware)
        
        @app.get("/admin")
        @handle_exceptions(ErrorCode.SYSTEM_INTERNAL_ERROR)
        def admin_endpoint(is_admin: bool = False):
            if not is_admin:
                raise AuthorizationException(
                    code=ErrorCode.AUTHZ_PERMISSION_DENIED,
                    message="Admin access required",
                )
            return {"message": "Admin area"}
        
        client = TestClient(app)
        
        # 成功的请求
        response = client.get("/admin?is_admin=true")
        assert response.status_code == 200
        
        # 失败的请求
        response = client.get("/admin?is_admin=false")
        assert response.status_code == 403
        data = response.json()
        assert data["error"]["code"] == ErrorCode.AUTHZ_PERMISSION_DENIED.value
    
    def test_resource_not_found_flow(self):
        """测试资源未找到的完整流程"""
        app = FastAPI()
        app.add_middleware(ExceptionHandlingMiddleware)
        
        @app.get("/users/{user_id}")
        @handle_exceptions(ErrorCode.SYSTEM_INTERNAL_ERROR)
        def get_user(user_id: int):
            if user_id <= 0:
                raise ResourceNotFoundException(
                    code=ErrorCode.RESOURCE_NOT_FOUND,
                    message=f"User {user_id} not found",
                    details={"resource_type": "User", "resource_id": user_id},
                )
            return {"id": user_id, "name": "Test User"}
        
        client = TestClient(app)
        
        # 成功的请求
        response = client.get("/users/1")
        assert response.status_code == 200
        
        # 失败的请求
        response = client.get("/users/-1")
        assert response.status_code == 404
        data = response.json()
        assert data["error"]["code"] == ErrorCode.RESOURCE_NOT_FOUND.value


# ============================================================================
# 错误响应格式测试
# ============================================================================

class TestErrorResponseFormat:
    """测试标准错误响应格式"""
    
    def test_error_response_structure(self):
        """测试错误响应的结构"""
        app = FastAPI()
        app.add_middleware(ExceptionHandlingMiddleware)
        
        @app.get("/test")
        def test_endpoint():
            raise ValidationException(
                code=ErrorCode.VALIDATION_INVALID_INPUT,
                message="Test error",
                details={"field": "email", "reason": "Invalid format"},
            )
        
        client = TestClient(app)
        response = client.get("/test")
        
        # 验证响应结构
        assert response.status_code == 422
        data = response.json()
        
        # 验证顶层结构
        assert "error" in data
        error = data["error"]
        
        # 验证错误对象结构
        assert "code" in error
        assert "message" in error
        assert "details" in error
        
        # 验证字段值
        assert error["code"] == ErrorCode.VALIDATION_INVALID_INPUT.value
        assert error["message"] == "Test error"
        assert error["details"]["field"] == "email"
    
    def test_error_response_without_details(self):
        """测试不包含详情的错误响应"""
        app = FastAPI()
        app.add_middleware(ExceptionHandlingMiddleware)
        
        @app.get("/test")
        def test_endpoint():
            raise AuthenticationException(
                code=ErrorCode.AUTH_INVALID_CREDENTIALS,
                message="Invalid credentials",
            )
        
        client = TestClient(app)
        response = client.get("/test")
        
        data = response.json()
        error = data["error"]
        
        # 验证必要字段
        assert error["code"] == ErrorCode.AUTH_INVALID_CREDENTIALS.value
        assert error["message"] == "Invalid credentials"
        # details 可能为空对象或不存在
        if "details" in error:
            assert error["details"] is not None


# ============================================================================
# 性能测试
# ============================================================================

class TestErrorHandlingPerformance:
    """错误处理性能测试"""
    
    def test_middleware_overhead(self):
        """测试中间件开销"""
        import time
        
        app = FastAPI()
        app.add_middleware(ExceptionHandlingMiddleware)
        
        @app.get("/test")
        def test_endpoint():
            return {"result": "success"}
        
        client = TestClient(app)
        
        start_time = time.time()
        for _ in range(100):
            response = client.get("/test")
            assert response.status_code == 200
        
        elapsed_time = time.time() - start_time
        avg_time = elapsed_time / 100
        
        # 平均响应时间应该小于 10ms
        assert avg_time < 0.01
    
    def test_exception_raising_overhead(self):
        """测试异常抛出的开销"""
        import time
        
        app = FastAPI()
        app.add_middleware(ExceptionHandlingMiddleware)
        
        @app.get("/test")
        def test_endpoint(should_error: bool = False):
            if should_error:
                raise ValidationException(
                    code=ErrorCode.VALIDATION_INVALID_INPUT,
                    message="Test error",
                )
            return {"result": "success"}
        
        client = TestClient(app)
        
        # 成功请求的响应时间
        start_time = time.time()
        for _ in range(100):
            response = client.get("/test?should_error=false")
            assert response.status_code == 200
        success_time = time.time() - start_time
        
        # 失败请求的响应时间
        start_time = time.time()
        for _ in range(100):
            response = client.get("/test?should_error=true")
            assert response.status_code == 422
        failure_time = time.time() - start_time
        
        # 失败请求的响应时间应该不超过成功请求的 5 倍
        assert failure_time / success_time < 5
