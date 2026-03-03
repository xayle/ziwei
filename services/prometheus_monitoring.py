"""
性能监控服务 - Prometheus 指标收集
用于监控 API 性能、请求延迟、错误率等指标
"""
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from fastapi import Request
from fastapi.responses import Response
import time
from typing import Callable
import functools

# ============================================================================
# 定义 Prometheus 指标
# ============================================================================

# 请求计数器 - 按方法、路径、状态码统计
REQUEST_COUNT = Counter(
    'http_requests_total',
    'HTTP requests total',
    ['method', 'path', 'status']
)

# 请求延迟直方图 - 按方法、路径统计
REQUEST_DURATION = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'path'],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 7.5, 10.0)
)

# 活跃请求数 - 当前正在处理的请求数
REQUESTS_IN_PROGRESS = Gauge(
    'http_requests_in_progress',
    'HTTP requests in progress',
    ['method', 'path']
)

# 数据库操作计数 - 按操作类型统计
DB_OPERATION_COUNT = Counter(
    'db_operations_total',
    'Database operations total',
    ['operation', 'table', 'status']
)

# 数据库操作延迟
DB_OPERATION_DURATION = Histogram(
    'db_operation_duration_seconds',
    'Database operation duration in seconds',
    ['operation', 'table'],
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0)
)

# 认证相关指标
AUTH_ATTEMPTS = Counter(
    'auth_attempts_total',
    'Authentication attempts total',
    ['endpoint', 'status']
)

# 缓存指标 (如果使用)
CACHE_HITS = Counter(
    'cache_hits_total',
    'Cache hits total',
    ['key']
)

CACHE_MISSES = Counter(
    'cache_misses_total',
    'Cache misses total',
    ['key']
)

# 业务逻辑指标
BUSINESS_OPERATION_COUNT = Counter(
    'business_operations_total',
    'Business operations total',
    ['operation', 'status']
)

BUSINESS_OPERATION_DURATION = Histogram(
    'business_operation_duration_seconds',
    'Business operation duration in seconds',
    ['operation'],
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0)
)

# ── N4.05 八字引擎专属指标 ────────────────────────────────────────────────────

# 八字计算耗时（_enrich_v2_analysis 全链路）
BAZI_ENGINE_CALC_SECONDS = Histogram(
    'bazi_engine_calc_seconds',
    'BaZi engine full calculation duration in seconds (_enrich_v2_analysis)',
    buckets=(0.05, 0.1, 0.25, 0.5, 0.75, 1.0, 1.5, 2.0, 3.0, 5.0, 10.0)
)

# 引擎缓存命中/未命中计数（由 run.py 计时区域内手动记录）
BAZI_CACHE_HITS = Counter(
    'bazi_cache_hits_total',
    'BaZi query cache hits total'
)

BAZI_CACHE_MISSES = Counter(
    'bazi_cache_misses_total',
    'BaZi query cache misses total'
)

# ─────────────────────────────────────────────────────────────────────────────
ERROR_COUNT = Counter(
    'errors_total',
    'Total errors',
    ['error_type', 'endpoint']
)

# 自定义业务指标示例
MEMBERS_CREATED = Counter(
    'members_created_total',
    'Total members created'
)

EVENTS_ANALYZED = Counter(
    'events_analyzed_total',
    'Total events analyzed'
)

SCENARIOS_SIMULATED = Counter(
    'scenarios_simulated_total',
    'Total scenarios simulated'
)

# ─────────────────────────────────────────────────────────────────────────────
# M6.08 自定义八字业务指标 [P50]
# ─────────────────────────────────────────────────────────────────────────────

# 命盘排盘请求计数，按 mode / status 标签
BAZI_VERIFY_TOTAL = Counter(
    'bazi_verify_total',
    'Total bazi verify requests',
    ['mode', 'status'],          # mode=dual/single, status=success/error
)

# 命盘排盘耗时直方图（秒），含 mode 标签
BAZI_VERIFY_DURATION = Histogram(
    'bazi_verify_duration_seconds',
    'Bazi verify request duration in seconds',
    ['mode'],
    buckets=(0.05, 0.1, 0.25, 0.5, 0.75, 1.0, 1.5, 2.0, 3.0, 5.0, 10.0),
)

# 命盘边界风险等级计数（L1/L2/L3/H/M/L …），按 boundary_level 标签
BAZI_BOUNDARY_RISK = Counter(
    'bazi_boundary_risk_total',
    'Bazi boundary risk level counts',
    ['boundary_level'],          # 校验级别，如 "H" / "M" / "L" / "L1/H" …
)


def record_verify_metrics(
    mode: str,
    boundary_level: str,
    duration_secs: float,
    success: bool,
) -> None:
    """
    记录单次 /api/v1/verify 请求的三项业务指标。

    :param mode:            "dual" 或 "single"
    :param boundary_level:  校验级别字符串，如 "H"/"M"/"L1/H" 等
    :param duration_secs:   请求耗时（秒）
    :param success:         是否正常完成（500 则 False）
    """
    status = "success" if success else "error"
    BAZI_VERIFY_TOTAL.labels(mode=mode, status=status).inc()
    BAZI_VERIFY_DURATION.labels(mode=mode).observe(duration_secs)
    if boundary_level:
        BAZI_BOUNDARY_RISK.labels(boundary_level=boundary_level).inc()


# ============================================================================
# 中间件和装饰器
# ============================================================================

import re as _re

_PATH_PARAM_RE = _re.compile(r"/[0-9a-fA-F-]{8,}|/\d+")

def _normalize_path(path: str) -> str:
    """0.24: 归一化 Prometheus 路径标签，防止高基数问题。
    /cases/123 → /cases/:id ; /cases/550e8400-... → /cases/:id
    """
    return _PATH_PARAM_RE.sub("/:id", path)


async def prometheus_middleware(request: Request, call_next: Callable):
    """
    Prometheus 监控中间件
    捕捉所有 HTTP 请求的性能数据
    0.24: 路径标签归一化（/cases/{id} → /cases/:id）
    """
    method = request.method
    path = _normalize_path(request.url.path)
    
    # 记录正在处理的请求
    REQUESTS_IN_PROGRESS.labels(method=method, path=path).inc()
    
    # 记录请求开始时间
    start_time = time.time()
    
    try:
        # 调用下一个中间件或处理函数
        response = await call_next(request)
        status = response.status_code
    except Exception as exc:
        # 记录错误
        status = 500
        ERROR_COUNT.labels(error_type=type(exc).__name__, endpoint=path).inc()
        raise
    finally:
        # 计算请求耗时
        duration = time.time() - start_time
        
        # 记录请求计数
        REQUEST_COUNT.labels(method=method, path=path, status=status).inc()
        
        # 记录请求延迟
        REQUEST_DURATION.labels(method=method, path=path).observe(duration)
        
        # 减少正在处理的请求计数
        REQUESTS_IN_PROGRESS.labels(method=method, path=path).dec()
    
    return response


def track_db_operation(operation: str, table: str):
    """
    装饰器：追踪数据库操作性能
    
    使用方法:
        @track_db_operation('select', 'users')
        def get_user(user_id: int):
            # ... 数据库操作 ...
            pass
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                DB_OPERATION_COUNT.labels(
                    operation=operation,
                    table=table,
                    status='success'
                ).inc()
                DB_OPERATION_DURATION.labels(
                    operation=operation,
                    table=table
                ).observe(duration)
                return result
            except Exception as exc:
                duration = time.time() - start_time
                DB_OPERATION_COUNT.labels(
                    operation=operation,
                    table=table,
                    status='error'
                ).inc()
                DB_OPERATION_DURATION.labels(
                    operation=operation,
                    table=table
                ).observe(duration)
                raise
        return wrapper
    return decorator


def track_business_operation(operation: str):
    """
    装饰器：追踪业务逻辑操作性能
    
    使用方法:
        @track_business_operation('bazi_calculation')
        def calculate_bazi(birth_date, location):
            # ... 业务逻辑 ...
            pass
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                BUSINESS_OPERATION_COUNT.labels(
                    operation=operation,
                    status='success'
                ).inc()
                BUSINESS_OPERATION_DURATION.labels(
                    operation=operation
                ).observe(duration)
                return result
            except Exception as exc:
                duration = time.time() - start_time
                BUSINESS_OPERATION_COUNT.labels(
                    operation=operation,
                    status='error'
                ).inc()
                BUSINESS_OPERATION_DURATION.labels(
                    operation=operation
                ).observe(duration)
                raise
        return wrapper
    return decorator


def record_auth_attempt(endpoint: str, success: bool):
    """
    记录认证尝试
    
    Args:
        endpoint: 认证端点名称 (如 'login', 'register')
        success: 是否成功
    """
    status = 'success' if success else 'failure'
    AUTH_ATTEMPTS.labels(endpoint=endpoint, status=status).inc()


def record_cache_hit(key: str):
    """记录缓存命中"""
    CACHE_HITS.labels(key=key).inc()


def record_cache_miss(key: str):
    """记录缓存未命中"""
    CACHE_MISSES.labels(key=key).inc()


# ============================================================================
# Prometheus 指标导出端点
# ============================================================================

def get_metrics_response() -> Response:
    """
    生成 Prometheus 格式的指标响应
    
    使用方法：在 FastAPI app 中添加路由
        @app.get("/metrics")
        def metrics():
            return get_metrics_response()
    """
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )


# ============================================================================
# 使用示例和集成指南
# ============================================================================

"""
FastAPI 集成示例：

from fastapi import FastAPI
from services.prometheus_monitoring import prometheus_middleware, get_metrics_response

app = FastAPI()

# 添加 Prometheus 监控中间件
@app.middleware("http")
async def add_prometheus_middleware(request, call_next):
    return await prometheus_middleware(request, call_next)

# 添加指标导出端点
@app.get("/metrics")
def metrics():
    return get_metrics_response()

# 在路由中使用
from routers.members import router as members_router
from services.prometheus_monitoring import track_db_operation, record_auth_attempt

@members_router.post("/members")
def create_member(body: MemberCreateRequest, session: Session = Depends(get_session)):
    # 创建成员时记录指标
    # MEMBERS_CREATED.inc()
    ...

@auth_router.post("/auth/login")
def login(body: LoginRequest, request: Request, session: Session = Depends(get_session)):
    try:
        # ... 登录逻辑 ...
        record_auth_attempt('login', success=True)
    except Exception:
        record_auth_attempt('login', success=False)
        raise


Docker Compose 配置（prometheus-compose.yml）：

version: '3.8'
services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=sqlite:///./data/mingli.db

  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana_data:/var/lib/grafana
    depends_on:
      - prometheus

volumes:
  prometheus_data:
  grafana_data:


Prometheus 配置文件（prometheus.yml）：

global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'bazi-service'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'
    scrape_interval: 5s


关键监控指标说明：

1. HTTP 请求指标：
   - http_requests_total: 总请求数
   - http_request_duration_seconds: 请求耗时
   - http_requests_in_progress: 当前正在处理的请求数

2. 数据库指标：
   - db_operations_total: 数据库操作数
   - db_operation_duration_seconds: 数据库操作耗时

3. 认证指标：
   - auth_attempts_total: 认证尝试总数

4. 缓存指标：
   - cache_hits_total: 缓存命中数
   - cache_misses_total: 缓存未命中数

5. 业务指标：
   - business_operations_total: 业务操作总数
   - members_created_total: 创建的成员总数
   - events_analyzed_total: 分析的事件总数
   - scenarios_simulated_total: 模拟的场景总数


Grafana Dashboard 配置：

可以使用预定义的 Grafana Dashboard，如：
- Node Exporter Full (ID: 1860)
- FastAPI Prometheus Dashboard (自定义)

或在 Grafana 中创建自定义面板：

1. 请求延迟 P95/P99 图表
2. 请求错误率时间序列
3. 数据库操作耗时分布
4. 活跃请求数量仪表
5. 各个端点的响应时间排行


监控告警规则示例：

groups:
  - name: bazi_service
    interval: 30s
    rules:
      - alert: HighRequestLatency
        expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 1
        for: 5m
        annotations:
          summary: "High request latency detected"

      - alert: HighErrorRate
        expr: rate(errors_total[5m]) > 0.05
        for: 5m
        annotations:
          summary: "Error rate exceeds 5%"

      - alert: HighDatabaseOperationLatency
        expr: histogram_quantile(0.99, rate(db_operation_duration_seconds_bucket[5m])) > 0.5
        for: 5m
        annotations:
          summary: "Database operation latency is high"


部署步骤：

1. 安装依赖：
   pip install prometheus-client

2. 在 run.py 中集成中间件：
   from services.prometheus_monitoring import prometheus_middleware
   @app.middleware("http")
   async def add_prometheus(request, call_next):
       return await prometheus_middleware(request, call_next)

3. 添加指标导出端点：
   @app.get("/metrics")
   def metrics():
       from services.prometheus_monitoring import get_metrics_response
       return get_metrics_response()

4. 启动 Prometheus 和 Grafana：
   docker-compose -f prometheus-compose.yml up -d

5. 访问仪表板：
   - Prometheus: http://localhost:9090
   - Grafana: http://localhost:3000
"""
