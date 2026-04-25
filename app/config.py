"""
增强的配置系统 - 支持环境变量和多环境配置。

环境变量优先级：
1. .env 文件（开发环境）
2. 环境变量（系统环境变量）
3. 代码默认值
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import ClassVar, Optional
from dotenv import load_dotenv

from constants import DEFAULT_LON, RULE_VERSION, API_VERSION

# 加载 .env 文件（优先级最低）
_root_dir = Path(__file__).resolve().parent.parent
_env_file = _root_dir / ".env"
if _env_file.exists():
    load_dotenv(_env_file)


@dataclass
class Settings:
    """应用配置"""
    
    # ===== 应用基本配置 =====
    app_name: str = os.getenv("APP_NAME", "BaZi Service v8.0")
    app_env: str = os.getenv("APP_ENV", "development")  # development, staging, production
    debug: bool = os.getenv("DEBUG", "false").lower() == "true"
    
    # ===== API 配置 =====
    api_version: str = API_VERSION
    rule_version: str = RULE_VERSION
    primary_backend: str = os.getenv("PRIMARY_BACKEND", "sxtwl")
    default_lon: float = float(os.getenv("DEFAULT_LON", DEFAULT_LON))
    solar_time_enabled: bool = os.getenv("SOLAR_TIME_ENABLED", "false").lower() == "true"
    
    # ===== 数据库配置 =====
    # 优先使用 DATABASE_URL 环境变量（生产环境），否则使用 SQLite
    database_url: Optional[str] = os.getenv("DATABASE_URL")
    db_path: Path = Path(os.getenv(
        "DB_PATH",
        str(Path(__file__).resolve().parent.parent / "data" / "mingli.db")
    ))
    
    # PostgreSQL 连接池配置（仅在 database_url 为 PostgreSQL 时有效）
    db_pool_size: int = int(os.getenv("DB_POOL_SIZE", "20"))
    db_max_overflow: int = int(os.getenv("DB_MAX_OVERFLOW", "30"))
    db_pool_recycle: int = int(os.getenv("DB_POOL_RECYCLE", "3600"))
    
    # ===== 认证配置 =====
    # 密钥统一使用 SECRET_KEY（与 auth_service.py 保持一致）
    jwt_secret_key: str = os.getenv(
        "SECRET_KEY",
        "your-secret-key-change-in-production"  # ⚠️ run.py lifespan 会检查此值
    )
    jwt_algorithm: str = os.getenv("JWT_ALGORITHM", "HS256")
    # Access Token = 15分钟（安全优先）；Refresh Token = 7天
    jwt_access_minutes: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "15"))
    jwt_refresh_days: int = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))
    
    # ===== CORS 配置 =====
    allowed_origins: list[str] = field(default_factory=list)
    allow_credentials: bool = True
    allow_methods: list[str] = field(default_factory=lambda: ["GET", "POST", "PUT", "PATCH", "DELETE"])
    allow_headers: list[str] = field(default_factory=lambda: [
        "Authorization", "Content-Type", "X-Request-Id", "Accept", "Accept-Language",
    ])
    
    # ===== 缓存配置 =====
    cache_enabled: bool = os.getenv("CACHE_ENABLED", "true").lower() == "true"
    cache_ttl_members: int = int(os.getenv("CACHE_TTL_MEMBERS", "600"))  # 10分钟
    cache_ttl_events: int = int(os.getenv("CACHE_TTL_EVENTS", "300"))    # 5分钟
    cache_ttl_cases: int = int(os.getenv("CACHE_TTL_CASES", "1200"))     # 20分钟
    
    # Redis 可选配置（用于分布式缓存）
    redis_url: Optional[str] = os.getenv("REDIS_URL")
    redis_enabled: bool = redis_url is not None and os.getenv("REDIS_ENABLED", "false").lower() == "true"
    
    # ===== 日志配置 =====
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    log_format: str = os.getenv("LOG_FORMAT", "json")  # json 或 text
    structured_logging: bool = log_format == "json"
    
    # ===== 性能监控配置 =====
    prometheus_enabled: bool = os.getenv("PROMETHEUS_ENABLED", "true").lower() == "true"
    metrics_port: int = int(os.getenv("METRICS_PORT", "8001"))
    
    # ===== 引擎功能开关（O9）=====
    # ENGINE_V2=true 时走新四柱计算路径（当前与 v1 行为相同，保留用于未来切换）
    engine_v2: bool = os.getenv("ENGINE_V2", "false").lower() == "true"
    # SANDBOX_ENABLED=true 时请求头 X-Sandbox: true 返回固定样本（C2）
    sandbox_enabled: bool = os.getenv("SANDBOX_ENABLED", "false").lower() == "true"

    # ===== 速率限制 =====
    rate_limit_enabled: bool = os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true"
    rate_limit_requests: int = int(os.getenv("RATE_LIMIT_REQUESTS", "100"))
    rate_limit_window_seconds: int = int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60"))
    
    # 弱密钥常量集合（用于生产环境检查）— ClassVar 使其不作为 dataclass 字段
    _WEAK_SECRET_KEYS: ClassVar[frozenset] = frozenset({
        "your-secret-key-change-in-production",
        "dev-secret-key-change-in-production",
        "secret",
        "changeme",
        "password",
    })

    def __post_init__(self):
        """初始化后处理 - 解析 ALLOWED_ORIGINS + 生产环境安全检查"""
        # 生产环境弱密钥检测（提前阻断，避免上线后被暴击）
        if self.app_env == "production" and self.jwt_secret_key in self._WEAK_SECRET_KEYS:
            raise ValueError(
                "FATAL: SECRET_KEY is set to a known-weak default value. "
                "Set a strong random key via the SECRET_KEY environment variable "
                "before running in production."
            )

        origins_str = os.getenv("ALLOWED_ORIGINS")
        if origins_str:
            # 支持逗号分隔的列表
            self.allowed_origins = [o.strip() for o in origins_str.split(",")]
        else:
            # 默认值：仅本地开发
            if self.app_env == "development":
                self.allowed_origins = [
                    "http://localhost:3000",
                    "http://localhost:5173",
                    "http://127.0.0.1:3000",
                    "http://127.0.0.1:5173",
                    "http://localhost:8765",
                    "http://127.0.0.1:8765",
                ]
            elif self.app_env == "staging":
                self.allowed_origins = os.getenv("ALLOWED_ORIGINS", "").split(",") if os.getenv("ALLOWED_ORIGINS") else []
            else:
                # 生产环境必须明确配置
                self.allowed_origins = os.getenv("ALLOWED_ORIGINS", "").split(",") if os.getenv("ALLOWED_ORIGINS") else []
    
    @property
    def is_production(self) -> bool:
        """是否是生产环境"""
        return self.app_env == "production"
    
    @property
    def is_development(self) -> bool:
        """是否是开发环境"""
        return self.app_env == "development"
    
    @property
    def use_postgres(self) -> bool:
        """是否使用 PostgreSQL"""
        return self.database_url is not None and self.database_url.startswith("postgresql")


# 单例实例
settings = Settings()
