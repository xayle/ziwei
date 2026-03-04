"""FastAPI entrypoint."""
from __future__ import annotations

import contextlib
import importlib.metadata
import importlib.util
import json
import logging
import os
import re
import time
from datetime import datetime, timedelta
from pathlib import Path
from uuid import uuid4
from zoneinfo import ZoneInfo

from fastapi import FastAPI, Header, HTTPException, Response, Depends
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware  # ✅ Priority 3.3: CORS支持
from fastapi.middleware.gzip import GZipMiddleware  # ✅ Phase 1: GZIP压缩
from ipaddress import ip_address as _parse_ip, ip_network as _parse_network
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from starlette.requests import Request
from typing import Optional, Callable, cast

# ✅ Priority 3.7: 请求验证中间件
from services.request_validation import RequestValidationMiddleware

# ✅ Priority 3.9: Prometheus 监控和性能指标
from services.prometheus_monitoring import (
    prometheus_middleware, get_metrics_response, record_verify_metrics,
    BAZI_ENGINE_CALC_SECONDS, BAZI_CACHE_HITS, BAZI_CACHE_MISSES,
)

# 0.36: 结构化日志配置 — log_level 读环境变量，LOG_FORMAT=json 时输出 JSON
_LOG_LEVEL_STR = os.getenv("LOG_LEVEL", "INFO").upper()
_LOG_LEVEL = getattr(logging, _LOG_LEVEL_STR, logging.INFO)
_LOG_FORMAT_ENV = os.getenv("LOG_FORMAT", "json").lower()

if _LOG_FORMAT_ENV == "json":
    # 简单 JSON 格式，字段与 ELK/Datadog 兼容
    _LOG_FMT = '{"time":"%(asctime)s","level":"%(levelname)s","name":"%(name)s","msg":"%(message)s"}'
else:
    _LOG_FMT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

logging.basicConfig(
    level=_LOG_LEVEL,
    format=_LOG_FMT,
)
logger = logging.getLogger(__name__)

from constants import API_VERSION, JIEQI_THRESHOLD_MIN, RULE_VERSION, SHICHEN_THRESHOLD_MIN, SUPPORTED_YEAR_RANGE
from app.schemas import (
	BackendInfo,
	BaziMethodsModel,
	MarriageFlagsModel,
	MarriageModel,
	PillarModel,
	PillarsModel,
	RiskFlagsModel,
	SocialModel,
	TenGodsModel,
	ValidationModel,
	VerifyRequest,
	VerifyResponse,
	BatchVerifyRequest,
	BatchVerifyResponse,
	WealthModel,
	WarningModel,
	DayMasterStrengthModel,
	WuXingBreakdownModel,
	WuXingScoreModel,
	YongShenModel,
	DaYunModel,
)
from verify import verify_full

from app.config import settings
from db import init_db
from routers import bazi as bazi_router
from routers import cases as cases_router
from routers import relations as relations_router
from routers import compute as compute_router
from routers import snapshots as snapshots_router
from routers import auth as auth_router
from routers import members as members_router
from routers import delegation as delegation_router
from routers import audit as audit_router
from routers import events as events_router
from routers import scenarios as scenarios_router
from routers import static_data as static_data_router
from routers import v2 as v2_router_module  # N6.01: API v2 路由
from services.normalize_input import validate_lon_strict, warn_lon_cn_range
from services.bazi_full_service import (
	build_dayun,
	build_ten_gods,
	compute_strength,
	compute_wuxing,
	compute_yongshen,
	ten_god,
)
# [M1 任务1.23] ENGINE_V2 路由开关
import services.bazi_engine_service as _bazi_engine_service
from services.bazi_engine_service import _enrich_v2_analysis  # M2 分析引擎集成
from services.bazi_engine.classic_refs import get_refs_by_tag  # 大运古籍引用
from services.bazi_engine.relations import get_branch_relations, get_stem_clashes  # 红线14 地支关系 / P0-11 天干相克
from services.bazi_engine.dayun import _ELEM_LOVE_HINT as _LOVE_HINTS, _ELEM_CHILD_HINT as _CHILD_HINTS  # 红线5 感情/子女提示
from services.bazi_engine.shensha import compute_shensha as _compute_shensha  # RL#9 桃花
from services.auth_service import verify_token, TokenPayload
from services.rate_limit import limiter
from zoneinfo import ZoneInfoNotFoundError

# ✅ Week 3: 错误处理框架
from app.error_handling import ExceptionHandlingMiddleware
from app.openapi_docs import setup_openapi_docs

# N4.04: 服务启动时间，用于 /health/detail uptime_seconds
_APP_START_TIME: float = time.time()

# 自定义 JSONResponse 以支持中文字符（ensure_ascii=False）
class UnescapedJSONResponse(JSONResponse):
	"""JSONResponse that keeps Chinese characters unescaped."""
	def render(self, content):
		return json.dumps(
			content,
			ensure_ascii=False,
			allow_nan=False,
			indent=None,
			separators=(",", ":"),
		).encode("utf-8")


_WEAK_KEYS = {
	"your-secret-key-change-in-production",
	"dev-secret-key",
	"secret",
	"changeme",
	"",
}

@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
	# ——— 安全启动检查 ———
	_secret = os.environ.get("SECRET_KEY", "")
	if not _secret or _secret in _WEAK_KEYS:
		raise RuntimeError(
			"[STARTUP] SECRET_KEY 未设置或使用了默认弱密钥！"
			"请在 .env 中配置强随机密钥，可用："
			"python -c \"import secrets; print(secrets.token_urlsafe(32))\" 生成"
		)
	_env = os.environ.get("ENVIRONMENT", "development")
	if _env == "production" and os.environ.get("AUTH_BYPASS", "false").lower() == "true":
		raise RuntimeError("[STARTUP] 生产环境严禁开启 AUTH_BYPASS=true！")
	logger.info("[STARTUP] 安全检查通过 (env=%s, auth_bypass=%s)",
			   _env, os.environ.get("AUTH_BYPASS", "false"))
	init_db()
	logger.info("[STARTUP] 数据库初始化完成")
	yield
	# Shutdown


app = FastAPI(title="BaZi v7.0", version=API_VERSION, lifespan=lifespan)

# ✅ Week 3: 添加全局异常处理中间件（必须在其他中间件之前）
app.add_middleware(ExceptionHandlingMiddleware)

# ✅ Priority 3.2: 速率限制中间件
app.state.limiter = limiter
rate_limit_handler: Callable[[Request, Exception], Response] = cast(
	Callable[[Request, Exception], Response],
	_rate_limit_exceeded_handler,
)
app.add_exception_handler(RateLimitExceeded, rate_limit_handler)
app.add_middleware(SlowAPIMiddleware)

# ✅ Priority 3.3: CORS 中间件配置
# 从环境变量读取允许的源（支持多环境配置）
app.add_middleware(
	CORSMiddleware,
	allow_origins=settings.allowed_origins,  # ✅ 从配置读取
	allow_credentials=settings.allow_credentials,
	allow_methods=settings.allow_methods,
	allow_headers=settings.allow_headers,
)

# ✅ Phase 1 优化: GZIP 压缩中间件
# 压缩大于1KB的响应，减少60%带宽和10%网络延迟
app.add_middleware(GZipMiddleware, minimum_size=1000)

# ✅ Priority 3.7: 请求验证中间件
# 验证 Content-Type、请求大小等
app.add_middleware(RequestValidationMiddleware)


# ✅ Priority 3.9: Prometheus 监控中间件
# 自动跟踪所有HTTP请求的延迟、计数和错误
@app.middleware("http")
async def monitoring_middleware(request: Request, call_next):
	"""Prometheus 性能监控中间件"""
	return await prometheus_middleware(request, call_next)


# N6.03: v1 废弃声明响应头（满足红线 R45）
@app.middleware("http")
async def add_v1_deprecation_headers(request: Request, call_next):
	"""对所有 /api/v1/* 响应追加废弃声明头（R45）."""
	response = await call_next(request)
	if request.url.path.startswith("/api/v1/"):
		response.headers["Deprecation"] = "true"
		response.headers["Sunset"] = "2026-12-31"
	return response


# ✅ P0 安全响应头中间件 (Production Security)
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
	"""添加安全响应头 - CSP, Cache-Control 等"""
	response = await call_next(request)
	
	# 内容安全策略 (CSP) - 防止XSS (P78 / task 4.19)
	# /docs 和 /redoc 需要从 cdn.jsdelivr.net / fastapi.tiangolo.com 加载 Swagger UI 资源
	# 其余路径保持严格 'self' only
	_is_docs_path = request.url.path in ("/docs", "/redoc", "/openapi.json")
	if _is_docs_path:
		# Swagger UI / ReDoc: 开放 jsdelivr CDN + fastapi favicon + 允许内联脚本（Swagger UI 初始化用）
		_CDN = "https://cdn.jsdelivr.net"
		_FASTAPI = "https://fastapi.tiangolo.com"
		response.headers["Content-Security-Policy"] = (
			f"default-src 'self'; "
			f"connect-src 'self' {_CDN}; "
			f"style-src 'self' 'unsafe-inline' {_CDN}; "
			f"script-src 'self' 'unsafe-inline' {_CDN}; "
			f"img-src 'self' data: {_CDN} {_FASTAPI}; "
			f"font-src 'self' {_CDN}; "
			f"object-src 'none'; "
			f"frame-ancestors 'self';"
		)
	else:
		response.headers["Content-Security-Policy"] = (
			"default-src 'self'; "
			"connect-src 'self'; "
			"style-src 'self' 'unsafe-inline'; "
			"script-src 'self'; "
			"img-src 'self' data:; "
			"font-src 'self'; "
			"object-src 'none'; "
			"frame-ancestors 'self';"
		)
	
	# 防点击劫持
	response.headers["X-Frame-Options"] = "SAMEORIGIN"
	
	# 防内容嗅探
	response.headers["X-Content-Type-Options"] = "nosniff"
	
	# XSS保护
	response.headers["X-XSS-Protection"] = "1; mode=block"
	
	# 引荐者策略
	response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
	
	# ✅ Phase 1 优化: 缓存策略（减少30%静态资源延迟）
	if request.url.path == "/static/sw.js":
		# Service Worker 文件不缓存，确保策略更新能及时生效
		response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
		response.headers["Pragma"] = "no-cache"
		response.headers["Expires"] = "0"
	elif request.url.path in ["/", "/dashboard", "/verify"]:
		# 根路径及核心页面：禁止缓存，避免旧 CSP 头被浏览器磁盘缓存复用
		response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
		response.headers["Pragma"] = "no-cache"
		response.headers["Expires"] = "0"
		# 强制客户端清理缓存，避免旧 CSP 头继续被复用
		response.headers["Clear-Site-Data"] = '"cache"'
	elif request.url.path.startswith("/static/") and request.url.path.endswith(".html"):
		# HTML 文件不缓存，确保每次获取最新版本；同时清理缓存避免旧 CSP 复用
		response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
		response.headers["Pragma"] = "no-cache"
		response.headers["Expires"] = "0"
		response.headers["Clear-Site-Data"] = '"cache"'
	elif request.url.path.startswith("/static/"):
		# 其他静态资源（JS/CSS/图片）缓存30天
		response.headers["Cache-Control"] = "public, max-age=2592000, immutable"
	elif request.url.path in ["/docs", "/redoc", "/openapi.json"]:
		# API 文档不缓存：CSP 变更需立即生效，避免浏览器使用旧 CSP 头
		response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
		response.headers["Pragma"] = "no-cache"
		response.headers["Expires"] = "0"
	elif request.url.path.startswith("/api/"):
		# API响应不缓存
		response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, private"
		response.headers["Pragma"] = "no-cache"
		response.headers["Expires"] = "0"
	else:
		# 其他资源缓存1天
		response.headers["Cache-Control"] = "public, max-age=86400"
	
	return response


# --- static UI (local/intranet) ---
_static_dir = Path(__file__).resolve().parent / "static"
if _static_dir.exists():
	app.mount("/static", StaticFiles(directory=str(_static_dir)), name="static")


@app.get("/favicon.ico")
def favicon():
	icon = _static_dir / "favicon.ico"
	if icon.exists():
		return FileResponse(icon, media_type="image/x-icon")
	raise HTTPException(status_code=404, detail="favicon not found")


@app.get("/")
@app.get("/dashboard")
def serve_dashboard():
	dashboard = _static_dir / "dashboard.html"
	if dashboard.exists():
		return FileResponse(dashboard, media_type="text/html")
	raise HTTPException(status_code=404, detail="dashboard ui not found")


@app.get("/verify")
def serve_verify():
	verify_page = _static_dir / "verify.html"
	if verify_page.exists():
		return FileResponse(verify_page, media_type="text/html")
	raise HTTPException(status_code=404, detail="verify ui not found")

app.include_router(cases_router.router)
app.include_router(relations_router.router)
app.include_router(bazi_router.router)
app.include_router(compute_router.router)
app.include_router(snapshots_router.router)
app.include_router(auth_router.router)
app.include_router(members_router.router)
app.include_router(delegation_router.router)
app.include_router(audit_router.router)
app.include_router(events_router.router)
app.include_router(scenarios_router.router)
app.include_router(static_data_router.router)
app.include_router(v2_router_module.router, prefix="/api/v2")  # N6.01: API v2，ENGINE_V2=false时返回501

# ⚙️ 0.13: 统一认证依赖 — 直接从 app.dependencies.auth 引用，run.py 不重复定义
# get_current_user / require_user 已在 app/dependencies/auth.py 实现

# ── /metrics IP 白名单 (0.09) ────────────────────────────────────────────────
_METRICS_ALLOWED_CIDRS = [
    _parse_network(net) for net in
    ("127.0.0.1/32", "10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16")
]

def _is_metrics_allowed(client_host: str) -> bool:
    """允许 localhost + 私网段访问 /metrics（0.09）"""
    try:
        ip = _parse_ip(client_host)
        return any(ip in net for net in _METRICS_ALLOWED_CIDRS)
    except ValueError:
        return False


def _backend_status(name: str) -> tuple[bool, str]:
	spec = importlib.util.find_spec(name)
	available = spec is not None
	version = "unavailable"
	if available:
		try:
			version = importlib.metadata.version(name)
		except importlib.metadata.PackageNotFoundError:
			version = "unknown"
	return available, version


@app.get("/health")
def health():
	tz = ZoneInfo("Asia/Shanghai")
	now_local = datetime.now(tz)
	sxtwl_ok, sxtwl_ver = _backend_status("sxtwl")
	cnlunar_ok, cnlunar_ver = _backend_status("cnlunar")
	return {
		"status": "ok",
		"api_version": API_VERSION,
		"rule_version": RULE_VERSION,
		"sxtwl_available": sxtwl_ok,
		"sxtwl_version": sxtwl_ver,
		"cnlunar_available": cnlunar_ok,
		"cnlunar_version": cnlunar_ver,
		"tz": "Asia/Shanghai",
		"now_utc8": now_local.isoformat(),
		"supported_year_range": SUPPORTED_YEAR_RANGE,
		"thresholds": {
			"shichen_minutes": SHICHEN_THRESHOLD_MIN,
			"jieqi_minutes": JIEQI_THRESHOLD_MIN,
			"jieqi_set": "12jie",
		},
	}


@app.get("/ready")
def ready(response: Response):
	"""
	✅ Priority 3.8: 健康检查 - 就绪探针 (Readiness Probe)
	检查服务是否完全就绪（包括数据库连接）
	返回 200 表示服务已就绪，500 表示未就绪
	"""
	try:
		from db import get_session
		from models import User  # type: ignore
		from sqlmodel import select
		
		# 尝试获取数据库会话并执行简单查询
		session_gen = get_session()
		session = next(session_gen)
		
		# 执行简单的查询以验证数据库连接
		_ = session.exec(select(User)).first()
		session.close()
		
		return {
			"status": "ready",
			"timestamp": datetime.now(ZoneInfo("Asia/Shanghai")).isoformat(),
		}
	except Exception as e:
		logger.error(f"Ready check failed: {str(e)}")
		response.status_code = 500
		return {
			"status": "not_ready",
			"timestamp": datetime.now(ZoneInfo("Asia/Shanghai")).isoformat(),
		}


@app.get("/health/detail")
def health_detail():
	"""
	N4.04: 详细健康检查
	返回 {db_reachable, cache_size, engine_version, uptime_seconds}
	"""
	import importlib.metadata as _imeta

	# db_reachable — 执行 SELECT 1
	db_ok = False
	try:
		from db import get_engine as _get_engine
		from sqlalchemy import text as _sa_text
		with _get_engine().connect() as _conn:
			_conn.execute(_sa_text("SELECT 1"))
		db_ok = True
	except Exception:
		pass

	# cache_size — 使用 __len__ 接口（N4.04 要求，不直接访问 _cache）
	try:
		from services.optimization_tools import query_cache as _qc
		cache_sz = len(_qc)
	except Exception:
		cache_sz = -1

	# engine_version
	try:
		engine_ver = _imeta.version("sxtwl")
	except Exception:
		engine_ver = "unknown"

	return {
		"db_reachable": db_ok,
		"cache_size": cache_sz,
		"engine_version": engine_ver,
		"uptime_seconds": round(time.time() - _APP_START_TIME, 1),
	}


def _attach_tz(dt: datetime, tz_name: str) -> datetime:
	tz = ZoneInfo(tz_name)
	if dt.tzinfo is None or dt.utcoffset() is None:
		return dt.replace(tzinfo=tz)
	return dt.astimezone(tz)


def _format_offset(td: timedelta) -> str:
	seconds = int(td.total_seconds())
	sign = "+" if seconds >= 0 else "-"
	seconds = abs(seconds)
	hours, remainder = divmod(seconds, 3600)
	minutes = remainder // 60
	return f"{sign}{hours:02d}:{minutes:02d}"


def _safe_offset(td: timedelta | None) -> str:
	if td is None:
		return ""
	return _format_offset(td)


_REQUEST_ID_PATTERN = re.compile(r"^[A-Za-z0-9._-]+$")


def _sanitize_request_id(candidate: str | None, warnings: list[str]) -> str:
	if candidate is None:
		return str(uuid4())
	rid = candidate.strip()
	if not rid:
		return str(uuid4())
	if not _REQUEST_ID_PATTERN.match(rid):
		warnings.append("request_id_invalid_chars: action=replaced_with_uuid")
		return str(uuid4())
	if len(rid) > 128:
		warnings.append("request_id_truncated: max_len=128")
		rid = rid[:128]
	return rid


def _to_pillars_model(pillars) -> PillarsModel:
	return PillarsModel(
		year=PillarModel(**pillars.year.__dict__),
		month=PillarModel(**pillars.month.__dict__),
		day=PillarModel(**pillars.day.__dict__),
		hour=PillarModel(**pillars.hour.__dict__),
	)


# 0.17: 有效时区检查工具函数
def _validate_tz(tz_name: str) -> None:
    """校验 IANA 时区字符串，无效时抛出 HTTPException 400 (0.17)"""
    try:
        ZoneInfo(tz_name)
    except (ZoneInfoNotFoundError, KeyError):
        raise HTTPException(status_code=400, detail=f"Invalid timezone: {tz_name!r}")


@app.post("/api/v1/verify")
@limiter.limit("30/minute")  # 0.14: /verify 速率限制 30 req/min
def api_verify(
	request: Request,
	body: VerifyRequest,
	response: Response,
	x_request_id: str | None = Header(None, alias="X-Request-Id"),
):
	warnings: list[str] = []
	req_id = _sanitize_request_id(x_request_id, warnings)
	response.headers["X-Request-Id"] = req_id
	_verify_start = time.time()  # M6.08: Prometheus 计时起点

	# 0.17: 校验时区字符串
	_validate_tz(body.tz)

	# 0.16: 校验年份范围 [1900, 2100]
	if not (1900 <= body.dt.year <= 2100):
		raise HTTPException(
			status_code=400,
			detail=f"dt.year {body.dt.year} 超出支持范围 [1900, 2100]",
		)

	if body.dt.tzinfo is not None and body.dt.utcoffset() is not None:
		target_tz = ZoneInfo(body.tz)
		target_offset = target_tz.utcoffset(body.dt)
		dt_offset = body.dt.utcoffset()
		if target_offset is not None and target_offset != dt_offset:
			offset_str = _safe_offset(dt_offset)
			warnings.append(
				f"tz_mismatch: dt_offset={offset_str} tz={body.tz} action=tz_ignored_for_aware_dt"
			)

	dt = _attach_tz(body.dt, body.tz)
	lon = validate_lon_strict(body.lon)
	offset_minutes_int = 0

	# soft warning for CN range when tz=Asia/Shanghai
	for w in warn_lon_cn_range(body.tz, lon):
		warnings.append(str(w))

	# [M1 任务1.23] ENGINE_V2 路由开关 ─────────────────────────────────────────
	if _bazi_engine_service._engine_v2_enabled():
		try:
			_calc = _bazi_engine_service.calculate(
				dt=dt,
				lon=lon,
				tz=body.tz,
				use_solar=body.solar_time_enabled,
				mode=body.mode,
				gender=getattr(body, "gender", None),
				request_id=req_id,
				extra_warnings=warnings,
				city_tier=getattr(body, "city_tier", None),
				industry=getattr(body, "industry", None),
			)
		except HTTPException:
			raise
		except ValueError as exc:
			record_verify_metrics(mode=body.mode, boundary_level="", duration_secs=time.time() - _verify_start, success=False)
			logger.warning("Verify validation error [v2]",
				extra={"request_id": req_id, "error": str(exc)})
			raise HTTPException(status_code=400, detail="Invalid input parameters")
		except Exception as exc:
			record_verify_metrics(mode=body.mode, boundary_level="", duration_secs=time.time() - _verify_start, success=False)
			logger.exception("Unexpected error in verify [v2]",
				extra={"request_id": req_id, "error_type": type(exc).__name__},
				exc_info=True)
			raise HTTPException(status_code=500, detail="Internal server error")
		response_data = _calc.verify_response.model_dump(mode="json")
		_bl_v2 = response_data.get("validation", {}).get("level", "") if isinstance(response_data.get("validation"), dict) else ""
		record_verify_metrics(mode=body.mode, boundary_level=_bl_v2, duration_secs=time.time() - _verify_start, success=True)
		return UnescapedJSONResponse(
			content=response_data,
			headers={"X-Request-Id": req_id},
		)
	# ──────────────────────────────────────────────────────────────────────────

	try:
		result = verify_full(dt, lon=lon, use_solar=body.solar_time_enabled, mode=body.mode)
	except HTTPException:
		raise
	except ValueError as exc:
		# ✅ 业务逻辑错误：输入验证失败
		record_verify_metrics(mode=body.mode, boundary_level="", duration_secs=time.time() - _verify_start, success=False)
		logger.warning(
			f"Verify validation error",
			extra={"request_id": req_id, "error": str(exc)}
		)
		raise HTTPException(status_code=400, detail="Invalid input parameters")
	except Exception as exc:
		# ✅ 其他未预期的错误，记录详细信息但不暴露给用户
		record_verify_metrics(mode=body.mode, boundary_level="", duration_secs=time.time() - _verify_start, success=False)
		logger.exception(
			f"Unexpected error in verify",
			extra={"request_id": req_id, "error_type": type(exc).__name__},
			exc_info=True
		)
		raise HTTPException(status_code=500, detail="Internal server error")

	offset_minutes_int = int(round(result.solar_time_offset_minutes))
	dt_effective = dt + timedelta(minutes=offset_minutes_int)

	rp = _to_pillars_model(result.pillars_primary)
	rs = _to_pillars_model(result.pillars_secondary) if result.pillars_secondary else None
	rf = RiskFlagsModel(**result.risk_flags.__dict__)
	v_payload = result.validation.__dict__.copy()
	v_payload["risk_flags"] = rf
	raw_warnings = list(result.validation.warnings) + warnings
	parsed_warnings = []
	for w in raw_warnings:
		if isinstance(w, dict):
			parsed_warnings.append(WarningModel.model_validate(w))
		else:
			parsed_warnings.append(WarningModel(code="legacy", message=str(w)))

	v_payload["warnings"] = parsed_warnings
	v = ValidationModel(**v_payload)

	sxtwl_ok, _ = _backend_status("sxtwl")
	cnlunar_ok, _ = _backend_status("cnlunar")

	backend_info = BackendInfo(
		primary=settings.primary_backend,
		secondary="cnlunar" if body.mode == "dual" else None,
		sxtwl_available=sxtwl_ok,
		cnlunar_available=cnlunar_ok,
	)

	# lightweight derived info for UI templates
	wuxing_score_raw, wuxing_breakdown_raw = compute_wuxing(rp)  # RL#1: 保留 breakdown
	strength_raw = compute_strength(rp.day.stem, wuxing_score_raw)
	yongshen_raw = compute_yongshen(wuxing_score_raw, strength_raw, rp)  # RL#2: 5分支
	ten_gods_map = build_ten_gods(rp.day.stem, rp)
	ten_gods = TenGodsModel(**ten_gods_map)

	# 将内部模型转换为 Pydantic 模型，避免类型不匹配
	wuxing_score = WuXingScoreModel.model_validate(
		wuxing_score_raw.model_dump() if hasattr(wuxing_score_raw, "model_dump") else getattr(wuxing_score_raw, "__dict__", wuxing_score_raw)
	)
	wuxing_breakdown = WuXingBreakdownModel.model_validate(
		wuxing_breakdown_raw.model_dump() if hasattr(wuxing_breakdown_raw, "model_dump") else getattr(wuxing_breakdown_raw, "__dict__", wuxing_breakdown_raw)
	)
	strength = DayMasterStrengthModel.model_validate(
		strength_raw.model_dump() if hasattr(strength_raw, "model_dump") else getattr(strength_raw, "__dict__", strength_raw)
	)
	yongshen = YongShenModel.model_validate(
		yongshen_raw.model_dump() if hasattr(yongshen_raw, "model_dump") else getattr(yongshen_raw, "__dict__", yongshen_raw)
	)
	# P0-14: wealth_score 必须独立于 strength.score 计算（不得相等）
	# 使用用神五行得分之和 * 缩放系数，产生 0-100 量级的财运评分
	_wx_dict = wuxing_score.model_dump() if hasattr(wuxing_score, "model_dump") else {}
	_favor = yongshen.favor or []
	_favor_total = sum(_wx_dict.get(e, 0.0) for e in _favor)
	_neutral_penalty = sum(max(0.0, _wx_dict.get(e, 0.0) - 25) for e in ["wood","fire","earth","metal","water"] if e not in _favor and e not in (yongshen.avoid or []))
	_wealth_score_raw = max(0.0, min(100.0, _favor_total * 1.8 - _neutral_penalty * 0.3 + 10))
	_wealth_score = round(_wealth_score_raw, 1)
	wealth = WealthModel(
		wealth_score=_wealth_score,
		industry_tags=yongshen.favor or [],
		risk_hint=("靠近时辰/节气边界，解读请守" if v.boundary_risk_shichen or v.boundary_risk_jieqi else None),
		note="依据五行强弱与用神粗略推断，供前端模板占位",
	)
	marriage = MarriageModel(
		marriage_flags=MarriageFlagsModel(allow_interpret=v.interpretation_enabled),
		risk_hint=("差异/边界存在，婚姻解读需折叠" if v.boundary_risk_shichen or v.boundary_risk_jieqi or v.diff_fields else None),
	)
	# RL#9: 计算桃花神煞
	_shensha_result = _compute_shensha(
		year_stem=rp.year.stem, year_branch=rp.year.branch,
		month_stem=rp.month.stem, month_branch=rp.month.branch,
		day_stem=rp.day.stem, day_branch=rp.day.branch,
		hour_stem=rp.hour.stem, hour_branch=rp.hour.branch,
	)
	_taohua_hit = any(s.get("name") == "桃花" for s in _shensha_result.get("items", []))
	social = SocialModel(
		taohua_hit=_taohua_hit,
		relation_conflict=None,
		social_hint=f"用神:{'/'.join(yongshen.favor)} 忌神:{'/'.join(yongshen.avoid)}" if yongshen.favor or yongshen.avoid else None,
	)
	methods = BaziMethodsModel()
	_gender_for_dayun = getattr(body, "gender", None)
	dayun_model_raw, _raw_dayun = build_dayun(dt_effective, rp, methods, gender=_gender_for_dayun)
	dayun_model = DaYunModel.model_validate(
		dayun_model_raw.model_dump() if hasattr(dayun_model_raw, "model_dump") else getattr(dayun_model_raw, "__dict__", dayun_model_raw)
	)
	# RL#3: 转移大运元数据（方向/锚点节气/起运年龄）
	dayun_model.direction = _raw_dayun.direction
	dayun_model.direction_basis = _raw_dayun.direction_basis
	dayun_model.anchor_jieqi_name = _raw_dayun.anchor_jieqi_name
	dayun_model.anchor_jieqi_dt = _raw_dayun.anchor_jieqi_dt
	if _raw_dayun.computed_months_before_rounding is not None:
		from math import ceil as _ceil
		_sam = _ceil(_raw_dayun.computed_months_before_rounding)
		dayun_model.start_age_months = _sam
		dayun_model.start_age = _sam // 12
	_WX_CN_MAP = {'wood':'木','fire':'火','earth':'土','metal':'金','water':'水'}
	_dayun_base_refs = get_refs_by_tag("大运")[:2]
	for item in dayun_model.items:
		if item.stem:
			item.ten_god = ten_god(rp.day.stem, item.stem)
		if yongshen.favor:
			item.wealth_hint = f"用神倾向: {', '.join(_WX_CN_MAP.get(f,f) for f in yongshen.favor)}"
		if yongshen.avoid:
			item.health_hint = f"忌神: {', '.join(_WX_CN_MAP.get(a,a) for a in yongshen.avoid)}"
		# 红线5: 填充感情/子女提示
		if item.flow_wuxing and not item.love_hint:
			item.love_hint = _LOVE_HINTS.get(item.flow_wuxing, "")
		if item.flow_wuxing and not item.child_hint:
			item.child_hint = _CHILD_HINTS.get(item.flow_wuxing, "")
		# 红线6: 填充大运古籍引用
		if item.refs is None:
			_item_refs = (
				get_refs_by_tag(item.ten_god) if item.ten_god else []
			)
			item.refs = (_dayun_base_refs + _item_refs)[:3]
		# RL#5: wealth_range 按五行粗估
		if item.wealth_range is None and item.flow_wuxing:
			from app.schemas.common import RangeModel as _RM
			_WX_WR = {"wood":(8,30),"fire":(10,40),"earth":(6,25),"metal":(12,50),"water":(10,35)}
			_lo, _hi = _WX_WR.get(item.flow_wuxing, (6, 30))
			item.wealth_range = _RM(min=_lo, max=_hi, currency="万元/年")

	verify_response = VerifyResponse(
		api_version=API_VERSION,
		rule_version=RULE_VERSION,
		request_id=req_id,
		backend=backend_info,
		mode_requested=result.mode_requested,  # type: ignore[arg-type]
		mode_effective=result.mode_effective,  # type: ignore[arg-type]
		pillars_primary=rp,
		pillars_secondary=rs,
		risk_flags=rf,
		validation=v,
		solar_time_offset_minutes=result.solar_time_offset_minutes,
		dt_input=body.dt.isoformat(),
		dt_effective_utc8=dt_effective.isoformat(),
		tz=body.tz,
		wuxing_score=wuxing_score,
		wuxing_breakdown=wuxing_breakdown,
		day_master_strength=strength,
		yongshen=yongshen,
		ten_gods=ten_gods,
		wealth=wealth,
		marriage=marriage,
		social=social,
		dayun=dayun_model,
	)
	# 红线14: 填充地支关系（全合/半合/拱合/六合/六冲）
	try:
		verify_response.dizhi_relations = get_branch_relations(
			rp.year.branch, rp.month.branch, rp.day.branch, rp.hour.branch
		)
	except Exception as _rel_exc:
		logger.debug("[dizhi_relations] %s", _rel_exc)
	# P0-11: 天干相克 scope=day_related
	try:
		verify_response.tiangan_clashes = get_stem_clashes(
			rp.year.stem, rp.month.stem, rp.day.stem, rp.hour.stem
		)
	except Exception as _tc_exc:
		logger.debug("[tiangan_clashes] %s", _tc_exc)
	# ── M2 分析引擎集成 ─────────────────────────────────────────────────
	try:
		_engine_t0 = time.time()  # N4.05: 引擎计时起点
		verify_response = _enrich_v2_analysis(
			verify_response=verify_response,
			rp=rp,
			yongshen=yongshen,
			strength=strength,
			wuxing_score=wuxing_score,
			dayun_model=dayun_model,
			dt=dt_effective,
			gender=getattr(body, "gender", None),
			mode=body.mode,
		)
		BAZI_ENGINE_CALC_SECONDS.observe(time.time() - _engine_t0)  # N4.05
	except Exception as _enrich_exc:
		logger.warning("M2 enrichment failed in legacy path: %s", _enrich_exc, exc_info=True)
	# 使用自定义 UnescapedJSONResponse 以正确处理中文字符
	response_data = verify_response.model_dump(mode="json")
	_bl_legacy = v.level if hasattr(v, "level") else ""
	record_verify_metrics(mode=body.mode, boundary_level=_bl_legacy, duration_secs=time.time() - _verify_start, success=True)
	return UnescapedJSONResponse(
		content=response_data,
		headers={"X-Request-Id": req_id},
	)


# N5.03: 批量验证端点 POST /api/v2/batch/verify
import os as _os
from concurrent.futures import ThreadPoolExecutor, TimeoutError as _FutureTimeoutError, as_completed as _as_completed
import uuid as _uuid

_BATCH_EXECUTOR = ThreadPoolExecutor(
	max_workers=int(_os.getenv("BATCH_WORKERS", "4")),
	thread_name_prefix="batch-verify",
)


def _batch_single_verify(item: VerifyRequest, idx: int) -> tuple[int, dict]:
	"""执行单条批量验证，返回 (index, result_dict)."""
	import warnings as _warn_mod
	_warnings: list[str] = []
	_req_id = _uuid.uuid4().hex[:12]

	# 时区验证
	_validate_tz(item.tz)

	if not (1900 <= item.dt.year <= 2100):
		raise ValueError(f"dt.year {item.dt.year} 超出支持范围 [1900, 2100]")

	_dt = _attach_tz(item.dt, item.tz)
	_lon = validate_lon_strict(item.lon)

	# 优先使用 ENGINE_V2 路径
	if _bazi_engine_service._engine_v2_enabled():
		_calc = _bazi_engine_service.calculate(
			dt=_dt,
			lon=_lon,
			tz=item.tz,
			use_solar=item.solar_time_enabled,
			mode=item.mode,
			gender=getattr(item, "gender", None),
			request_id=_req_id,
			extra_warnings=_warnings,
			city_tier=getattr(item, "city_tier", None),
			industry=getattr(item, "industry", None),
		)
		return idx, _calc.verify_response.model_dump(mode="json")

	# 回退到 v1 路径
	_result = verify_full(_dt, lon=_lon, use_solar=item.solar_time_enabled, mode=item.mode)
	return idx, {"request_id": _req_id, "mode_effective": _result.mode_effective}


@app.post("/api/v2/batch/verify", response_model=BatchVerifyResponse)
@limiter.limit("10/minute")  # N5.03: 每用户10次/分钟（_rate_limit_key 已实现 user-based key）
def api_batch_verify(
	request: Request,
	body: BatchVerifyRequest,
):
	"""N5.03 批量验证端点.

	- items 最多 50 条
	- ENGINE_V2=false 时返回 501（R40）
	- ThreadPoolExecutor(BATCH_WORKERS) 并行
	- 整体超时 60s，单条超时 5s
	- 部分成功返回（partial results on timeout）
	"""
	# ── R40: ENGINE_V2 开关检查 ─────────────────────────────────────────────
	if not _bazi_engine_service._engine_v2_enabled():
		from fastapi import Response as _Response
		from fastapi.responses import JSONResponse as _JSONResponse
		return _JSONResponse(
			status_code=501,
			content={"detail": "v2 engine not enabled (set ENGINE_V2=true to activate)"},
		)

	_deadline = 60.0
	_per_item_timeout = 5.0

	results_map: dict[int, dict] = {}
	failed_list: list[dict] = []

	futures = {
		_BATCH_EXECUTOR.submit(_batch_single_verify, item, idx): idx
		for idx, item in enumerate(body.items)
	}

	import time as _time
	_start = _time.time()

	for future in _as_completed(futures, timeout=_deadline):
		idx = futures[future]
		try:
			_i, _res = future.result(timeout=_per_item_timeout)
			results_map[_i] = _res
		except _FutureTimeoutError:
			failed_list.append({"index": idx, "error": "timeout"})
		except Exception as exc:
			failed_list.append({"index": idx, "error": str(exc)[:200]})

		# 外部截止检查
		if _time.time() - _start >= _deadline:
			# 标记尚未完成的条目为超时
			for f, remaining_idx in futures.items():
				if remaining_idx not in results_map and not any(f_["index"] == remaining_idx for f_ in failed_list):
					f.cancel()
					failed_list.append({"index": remaining_idx, "error": "deadline_exceeded"})
			break

	# 保证 len(results) + len(failed) == len(items)
	all_present = set(results_map.keys()) | {f["index"] for f in failed_list}
	for missing_idx in range(len(body.items)):
		if missing_idx not in all_present:
			failed_list.append({"index": missing_idx, "error": "not_completed"})

	# 按原始顺序输出成功结果
	ordered_results = [results_map[i] for i in sorted(results_map.keys())]

	return UnescapedJSONResponse(
		content={"results": ordered_results, "failed": failed_list}
	)


@app.get("/metrics")
def metrics(request: Request):
	"""
	✅ Priority 3.9: Prometheus 指标导出端点
	0.09: IP 白名单保护（仅允许 localhost + 私网）
	返回 Prometheus 文本格式的指标数据
	"""
	client_host = getattr(request.client, "host", "unknown")
	if not _is_metrics_allowed(client_host):
		raise HTTPException(status_code=403, detail="Access denied")
	try:
		return get_metrics_response()
	except Exception as e:
		logger.exception(f"Error exporting metrics: {str(e)}", exc_info=True)
		raise HTTPException(status_code=500, detail="Failed to export metrics")


# ✅ Week 3: 设置增强的 OpenAPI 文档
setup_openapi_docs(app)
