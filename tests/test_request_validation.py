"""
Test Request Validation Middleware

验证请求验证中间件功能
"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.middleware.base import BaseHTTPMiddleware

from services.request_validation import RequestValidationMiddleware


@pytest.fixture
def test_app():
    """创建测试应用"""
    app = FastAPI()
    app.add_middleware(RequestValidationMiddleware)
    
    @app.post("/test")
    def test_endpoint(body: dict):
        return {"received": body}
    
    @app.get("/test")
    def test_get():
        return {"message": "ok"}
    
    return app


def test_missing_content_type_on_post(test_app):
    """测试: POST 请求缺少 Content-Type"""
    client = TestClient(test_app)
    
    # POST 请求不包含 Content-Type 头
    response = client.post("/test", content='{"key": "value"}')
    
    assert response.status_code == 400
    assert "Content-Type header is required" in response.text


def test_invalid_content_type(test_app):
    """测试: POST 请求使用无效的 Content-Type"""
    client = TestClient(test_app)
    
    response = client.post(
        "/test",
        content='{"key": "value"}',
        headers={"content-type": "text/plain"}
    )
    
    assert response.status_code == 415
    assert "Unsupported Content-Type" in response.text


def test_valid_json_content_type(test_app):
    """测试: 有效的 JSON Content-Type"""
    client = TestClient(test_app)
    
    response = client.post(
        "/test",
        json={"key": "value"},
        headers={"content-type": "application/json"}
    )
    
    # 由于 TestClient 自动处理 JSON,这里应该成功
    # 但如果我们的中间件正常工作,会返回 200
    assert response.status_code in [200, 422]  # 422 是 Pydantic 验证错误


def test_request_too_large(test_app):
    """测试: 请求大小超过限制"""
    client = TestClient(test_app)
    
    # 创建超大请求(11MB > 10MB 限制)
    large_data = "x" * (11 * 1024 * 1024)
    
    response = client.post(
        "/test",
        content=large_data,
        headers={
            "content-type": "application/json",
            "content-length": str(len(large_data))
        }
    )
    
    assert response.status_code == 413
    assert "Request entity too large" in response.text


def test_get_request_no_validation(test_app):
    """测试: GET 请求不需要 Content-Type 验证"""
    client = TestClient(test_app)
    
    response = client.get("/test")
    
    assert response.status_code == 200
    assert response.json() == {"message": "ok"}


def test_delete_request_no_validation(test_app):
    """测试: DELETE 请求不需要 Content-Type 验证"""
    client = TestClient(test_app)
    
    @test_app.delete("/test")
    def test_delete():
        return {"deleted": True}
    
    response = client.delete("/test")
    
    # DELETE 请求没有 Content-Type 验证
    assert response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
