"""FastAPI entrypoint."""
from __future__ import annotations

import json
import logging
import os
import re
import time
from datetime import datetime, timedelta
from uuid import uuid4
from zoneinfo import ZoneInfo

from fastapi import Header, HTTPException, Response
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from starlette.requests import Request

# ✅ Priority 3.9: Prometheus 监控和性能指标
from services.prometheus_monitoring import (
	get_metrics_response, record_verify_metrics,
	BAZI_ENGINE_CALC_SECONDS,
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

# O7: structlog JSON 结构化日志配置
try:
    import structlog as _structlog
    _structlog.configure(
        processors=[
            _structlog.contextvars.merge_contextvars,
            _structlog.stdlib.add_log_level,
            _structlog.stdlib.add_logger_name,
            _structlog.processors.TimeStamper(fmt="iso", utc=True),
            _structlog.processors.StackInfoRenderer(),
            _structlog.processors.format_exc_info,
            _structlog.processors.JSONRenderer(ensure_ascii=False),
        ],
        context_class=dict,
        logger_factory=_structlog.stdlib.LoggerFactory(),
        wrapper_class=_structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
except ImportError:
    pass  # structlog 未安装，降级为标准 logging

from constants import API_VERSION, RULE_VERSION
from app.bootstrap import create_app, is_metrics_allowed, backend_status
from app.lifecycle import APP_START_TIME, create_lifespan
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
from app.docs_routes_setup import configure_docs_routes
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
from services.rate_limit import limiter
from zoneinfo import ZoneInfoNotFoundError
from init_db import init_db  # re-export for test patching

# Backward-compat aliases (functions moved to app.bootstrap in refactor)
_backend_status = backend_status
_is_metrics_allowed = is_metrics_allowed

# Static path re-exports for test patching
from app.static_routes_setup import _static_dir, _spa_index  # noqa: E402

# ✅ Week 3: 错误处理框架


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
lifespan = create_lifespan(logger)
app = create_app(logger=logger, lifespan=lifespan, app_start_time=APP_START_TIME)

# ⚙️ 0.13: 统一认证依赖 — 直接从 app.dependencies.auth 引用，run.py 不重复定义
# get_current_user / require_user 已在 app/dependencies/auth.py 实现

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


def _build_legacy_verify_response(body, dt, lon, req_id, warnings):
	"""Legacy path (ENGINE_V2 disabled): 完整计算返回 (VerifyResponse, boundary_level)。
	遇到输入/内部错误时直接抛出 HTTPException，由调用方负责指标记录。
	"""
	try:
		result = verify_full(dt, lon=lon, use_solar=body.solar_time_enabled, mode=body.mode)
	except HTTPException:
		raise
	except ValueError as exc:
		logger.warning("Verify validation error", extra={"request_id": req_id, "error": str(exc)})
		raise HTTPException(status_code=400, detail="Invalid input parameters")
	except Exception as exc:
		logger.exception("Unexpected error in verify",
			extra={"request_id": req_id, "error_type": type(exc).__name__}, exc_info=True)
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
	wuxing_score_raw, wuxing_breakdown_raw = compute_wuxing(rp)  # RL#1
	strength_raw = compute_strength(rp.day.stem, wuxing_score_raw)
	yongshen_raw = compute_yongshen(wuxing_score_raw, strength_raw, rp)  # RL#2
	ten_gods_map = build_ten_gods(rp.day.stem, rp)
	ten_gods = TenGodsModel(**ten_gods_map)

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
	# P0-14: wealth_score 独立于 strength.score 计算
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
	# RL#3: 大运元数据
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
		if item.flow_wuxing and not item.love_hint:  # 红线5
			item.love_hint = _LOVE_HINTS.get(item.flow_wuxing, "")
		if item.flow_wuxing and not item.child_hint:  # 红线5
			item.child_hint = _CHILD_HINTS.get(item.flow_wuxing, "")
		if item.refs is None:  # 红线6
			_item_refs = (get_refs_by_tag(item.ten_god) if item.ten_god else [])
			item.refs = (_dayun_base_refs + _item_refs)[:3]
		if item.wealth_range is None and item.flow_wuxing:  # RL#5
			from app.schemas.common import RangeModel as _RM
			_WX_WR = {"wood":(8,30),"fire":(10,40),"earth":(6,25),"metal":(12,50),"water":(10,35)}
			_lo, _hi = _WX_WR.get(item.flow_wuxing, (6, 30))
			item.wealth_range = _RM(min=_lo, max=_hi, currency="万元/年")

	verify_response = VerifyResponse(
		api_version=API_VERSION, rule_version=RULE_VERSION, request_id=req_id,
		backend=backend_info,
		mode_requested=result.mode_requested,  # type: ignore[arg-type]
		mode_effective=result.mode_effective,  # type: ignore[arg-type]
		pillars_primary=rp, pillars_secondary=rs, risk_flags=rf, validation=v,
		solar_time_offset_minutes=result.solar_time_offset_minutes,
		dt_input=body.dt.isoformat(), dt_effective_utc8=dt_effective.isoformat(), tz=body.tz,
		wuxing_score=wuxing_score, wuxing_breakdown=wuxing_breakdown,
		day_master_strength=strength, yongshen=yongshen, ten_gods=ten_gods,
		wealth=wealth, marriage=marriage, social=social, dayun=dayun_model,
	)
	try:  # 红线14
		verify_response.dizhi_relations = get_branch_relations(
			rp.year.branch, rp.month.branch, rp.day.branch, rp.hour.branch
		)
	except Exception as _rel_exc:
		logger.debug("[dizhi_relations] %s", _rel_exc)
	try:  # P0-11
		verify_response.tiangan_clashes = get_stem_clashes(
			rp.year.stem, rp.month.stem, rp.day.stem, rp.hour.stem
		)
	except Exception as _tc_exc:
		logger.debug("[tiangan_clashes] %s", _tc_exc)
	try:  # M2 分析引擎集成
		_engine_t0 = time.time()
		verify_response = _enrich_v2_analysis(
			verify_response=verify_response, rp=rp, yongshen=yongshen, strength=strength,
			wuxing_score=wuxing_score, dayun_model=dayun_model, dt=dt_effective,
			gender=getattr(body, "gender", None), mode=body.mode,
		)
		BAZI_ENGINE_CALC_SECONDS.observe(time.time() - _engine_t0)  # N4.05
	except Exception as _enrich_exc:
		logger.warning("M2 enrichment failed in legacy path: %s", _enrich_exc, exc_info=True)

	return verify_response, v.level if hasattr(v, "level") else ""


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
		# 缓存命中时 request_id 可能来自旧请求，用当前 req_id 覆盖以保证 header 与 body 一致
		response_data["request_id"] = req_id
		# 缓存命中时 extra_warnings（request_id_invalid_chars 等）未写入缓存结果，补充合并
		if warnings:
			_val = response_data.get("validation") or {}
			_existing_warns = _val.get("warnings") or []
			_extra_warns = [{"code": "legacy", "message": str(w)} for w in warnings]
			_val["warnings"] = _existing_warns + _extra_warns
			response_data["validation"] = _val
		_bl_v2 = response_data.get("validation", {}).get("level", "") if isinstance(response_data.get("validation"), dict) else ""
		record_verify_metrics(mode=body.mode, boundary_level=_bl_v2, duration_secs=time.time() - _verify_start, success=True)
		return UnescapedJSONResponse(
			content=response_data,
			headers={"X-Request-Id": req_id},
		)
	# ──────────────────────────────────────────────────────────────────────────

	# Legacy path: 委托给 _build_legacy_verify_response() 完成全部计算
	try:
		verify_response, _bl_legacy = _build_legacy_verify_response(body, dt, lon, req_id, warnings)
	except HTTPException:
		record_verify_metrics(mode=body.mode, boundary_level="", duration_secs=time.time() - _verify_start, success=False)
		raise
	record_verify_metrics(mode=body.mode, boundary_level=_bl_legacy, duration_secs=time.time() - _verify_start, success=True)
	return UnescapedJSONResponse(
		content=verify_response.model_dump(mode="json"),
		headers={"X-Request-Id": req_id},
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


configure_docs_routes(app)
