"""
OpenAPI 文档增强和自动生成
"""

from typing import Dict, List, Any, Optional
from fastapi.openapi.utils import get_openapi
from fastapi import FastAPI
from pydantic import BaseModel
from app.exceptions import ErrorCode


# ============================================================================
# API 文档增强
# ============================================================================

def get_openapi_with_error_schemas(app: FastAPI) -> Dict[str, Any]:
    """
    获取增强的 OpenAPI schema，包含标准错误定义
    
    Args:
        app: FastAPI 应用实例
    
    Returns:
        增强的 OpenAPI schema
    """
    if app.openapi_schema:
        return app.openapi_schema
    
    # 获取默认的 OpenAPI schema
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    
    # 添加标准错误响应定义
    if "components" not in openapi_schema:
        openapi_schema["components"] = {}
    
    if "schemas" not in openapi_schema["components"]:
        openapi_schema["components"]["schemas"] = {}
    
    # 添加错误响应模型
    openapi_schema["components"]["schemas"]["ErrorResponse"] = {
        "type": "object",
        "properties": {
            "error": {
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "标准错误代码",
                        "example": "AUTH_001",
                    },
                    "message": {
                        "type": "string",
                        "description": "错误消息",
                        "example": "Invalid credentials",
                    },
                    "details": {
                        "type": "object",
                        "description": "额外错误详情",
                        "example": {},
                    },
                },
                "required": ["code", "message"],
            },
        },
        "required": ["error"],
    }
    
    # 添加常见错误响应
    openapi_schema["components"]["responses"] = {
        "UnauthorizedError": {
            "description": "Unauthorized",
            "content": {
                "application/json": {
                    "schema": {"$ref": "#/components/schemas/ErrorResponse"},
                    "example": {
                        "error": {
                            "code": str(ErrorCode.AUTH_MISSING_TOKEN.value),
                            "message": "Missing authorization token",
                        }
                    },
                }
            },
        },
        "ForbiddenError": {
            "description": "Forbidden",
            "content": {
                "application/json": {
                    "schema": {"$ref": "#/components/schemas/ErrorResponse"},
                    "example": {
                        "error": {
                            "code": str(ErrorCode.AUTHZ_PERMISSION_DENIED.value),
                            "message": "Permission denied",
                        }
                    },
                }
            },
        },
        "NotFoundError": {
            "description": "Resource not found",
            "content": {
                "application/json": {
                    "schema": {"$ref": "#/components/schemas/ErrorResponse"},
                    "example": {
                        "error": {
                            "code": str(ErrorCode.RESOURCE_NOT_FOUND.value),
                            "message": "Resource not found",
                        }
                    },
                }
            },
        },
        "ValidationError": {
            "description": "Validation error",
            "content": {
                "application/json": {
                    "schema": {"$ref": "#/components/schemas/ErrorResponse"},
                    "example": {
                        "error": {
                            "code": str(ErrorCode.VALIDATION_INVALID_INPUT.value),
                            "message": "Validation failed",
                            "details": {"field": "email", "reason": "Invalid format"},
                        }
                    },
                }
            },
        },
        "InternalServerError": {
            "description": "Internal server error",
            "content": {
                "application/json": {
                    "schema": {"$ref": "#/components/schemas/ErrorResponse"},
                    "example": {
                        "error": {
                            "code": str(ErrorCode.SYSTEM_INTERNAL_ERROR.value),
                            "message": "Internal server error",
                        }
                    },
                }
            },
        },
    }
    
    # 为每个路由添加标准错误响应
    for path, methods in openapi_schema.get("paths", {}).items():
        for method, operation in methods.items():
            if method not in ["get", "post", "put", "delete", "patch"]:
                continue
            
            if "responses" not in operation:
                operation["responses"] = {}
            
            # 添加常见错误响应
            common_responses = {
                "400": {"$ref": "#/components/responses/ValidationError"},
                "401": {"$ref": "#/components/responses/UnauthorizedError"},
                "403": {"$ref": "#/components/responses/ForbiddenError"},
                "404": {"$ref": "#/components/responses/NotFoundError"},
                "500": {"$ref": "#/components/responses/InternalServerError"},
            }
            
            # 仅添加未定义的响应
            for status_code, response in common_responses.items():
                if status_code not in operation["responses"]:
                    operation["responses"][status_code] = response
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema


# ============================================================================
# 文档字符串增强
# ============================================================================

class APIEndpointDoc:
    """API 端点文档增强工具"""
    
    @staticmethod
    def success_response(
        status_code: int = 200,
        description: str = "Success",
        schema: Optional[BaseModel] = None,
    ) -> Dict[str, Any]:
        """生成成功响应文档"""
        return {
            str(status_code): {
                "description": description,
                **({"content": {"application/json": {"schema": schema}}} if schema else {}),
            }
        }
    
    @staticmethod
    def error_response(
        status_code: int,
        description: str,
        error_code: ErrorCode,
    ) -> Dict[str, Any]:
        """生成错误响应文档"""
        return {
            str(status_code): {
                "description": description,
                "content": {
                    "application/json": {
                        "schema": {"$ref": "#/components/schemas/ErrorResponse"},
                        "example": {
                            "error": {
                                "code": error_code.value,
                                "message": description,
                            }
                        },
                    }
                },
            }
        }


# ============================================================================
# 服务文档生成
# ============================================================================

class ServiceDocGenerator:
    """服务类文档自动生成"""
    
    @staticmethod
    def generate_service_doc(
        service_class,
        title: str,
        description: str,
    ) -> str:
        """为服务类生成 Markdown 文档"""
        doc = f"# {title}\n\n{description}\n\n"
        
        # 获取公共方法
        methods = [m for m in dir(service_class) if not m.startswith("_") and callable(getattr(service_class, m))]
        
        if methods:
            doc += "## Methods\n\n"
            for method_name in methods:
                method = getattr(service_class, method_name)
                if method.__doc__:
                    doc += f"### {method_name}\n\n{method.__doc__}\n\n"
        
        return doc


# ============================================================================
# API 版本管理
# ============================================================================

class APIVersionManager:
    """API 版本管理器"""
    
    def __init__(self):
        self.api_versions = {}
    
    def register_version(self, version: str, description: str, deprecated: bool = False):
        """注册 API 版本"""
        self.api_versions[version] = {
            "description": description,
            "deprecated": deprecated,
        }
    
    def get_versions(self) -> Dict[str, Dict[str, Any]]:
        """获取所有 API 版本"""
        return self.api_versions
    
    def add_version_info_to_openapi(self, openapi_schema: Dict[str, Any]) -> Dict[str, Any]:
        """在 OpenAPI schema 中添加版本信息"""
        if "info" not in openapi_schema:
            openapi_schema["info"] = {}
        
        openapi_schema["info"]["x-api-versions"] = self.api_versions
        return openapi_schema


# ============================================================================
# Swagger UI 自定义配置
# ============================================================================

def get_swagger_ui_html_custom() -> str:
    """自定义 Swagger UI HTML"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>API Documentation</title>
        <meta charset="utf-8"/>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <link rel="stylesheet" href="https://unpkg.com/swagger-ui-dist@3/swagger-ui.css">
    </head>
    <body>
        <div id="swagger-ui"></div>
        <script src="https://unpkg.com/swagger-ui-dist@3/swagger-ui.js"></script>
        <script>
        window.onload = function() {
            window.ui = SwaggerUIBundle({
                url: "/openapi.json",
                dom_id: '#swagger-ui',
                presets: [
                    SwaggerUIBundle.presets.apis,
                    SwaggerUIBundle.SwaggerUIStandalonePreset
                ],
                layout: "BaseLayout"
            })
        }
        </script>
    </body>
    </html>
    """


# ============================================================================
# API 文档生成函数
# ============================================================================

def setup_openapi_docs(app: FastAPI) -> None:
    """为 FastAPI 应用设置增强的 OpenAPI 文档"""
    
    @app.get("/openapi.json", include_in_schema=False)
    def get_openapi():
        return get_openapi_with_error_schemas(app)
    
    # 版本管理器
    version_manager = APIVersionManager()
    version_manager.register_version("v1", "Initial version")
    
    openapi_schema = get_openapi_with_error_schemas(app)
    openapi_schema = version_manager.add_version_info_to_openapi(openapi_schema)
    
    app.openapi_schema = openapi_schema
