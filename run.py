"""FastAPI entrypoint.

Application bootstrap only — all endpoint logic lives in dedicated modules:
  - POST /api/v1/verify  → routers/verify.py
  - GET  /metrics        → app/metrics_routes_setup.py

This file keeps backward-compat re-exports so existing ``from run import ...``
and ``patch("run.*")`` usages continue to work without changes.
"""

from __future__ import annotations

import logging
import os

# 0.36: 结构化日志配置 — log_level 读环境变量，LOG_FORMAT=json 时输出 JSON
_LOG_LEVEL_STR = os.getenv("LOG_LEVEL", "INFO").upper()
_LOG_LEVEL = getattr(logging, _LOG_LEVEL_STR, logging.INFO)
_LOG_FORMAT_ENV = os.getenv("LOG_FORMAT", "json").lower()

if _LOG_FORMAT_ENV == "json":
    _LOG_FMT = '{"time":"%(asctime)s","level":"%(levelname)s","name":"%(name)s","msg":"%(message)s"}'
else:
    _LOG_FMT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

logging.basicConfig(level=_LOG_LEVEL, format=_LOG_FMT)
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

from app.entrypoint_factory import create_application  # noqa: E402
from app.lifecycle import create_lifespan  # noqa: E402

lifespan = create_lifespan(logger)
app = create_application(logger=logger)

# ── backward-compat re-exports ────────────────────────────────────────────────
# Tests import / patch these names via "run.*" — do NOT remove.
# NOTE: patch("run.X") patches the *name binding* here in run.__dict__,
# which is independent of the binding in the module that owns the logic.
# Tests that mock endpoint behaviour must use the canonical module path, e.g.
#   patch("routers.verify.verify_full")            — for /api/v1/verify tests
#   patch("app.metrics_routes_setup._is_metrics_allowed") — for /metrics tests
# The re-exports below keep *direct import* usages (``from run import X``) working.
# fmt: off
from app.metrics_routes_setup import _is_metrics_allowed  # noqa: F401,E402
from app.pkg_utils import backend_status as _backend_status  # noqa: F401,E402
from app.static_routes_setup import _spa_index, _static_dir  # noqa: F401,E402
from routers.verify import (  # noqa: F401,E402
    UnescapedJSONResponse,
    _build_legacy_verify_response,
    _format_offset,
    _safe_offset,
    _sanitize_request_id,
)
from scripts.init_db import init_db  # noqa: F401,E402
from services.bazi_engine.relations import (
    get_branch_relations,  # noqa: F401,E402
    get_stem_clashes,  # noqa: F401,E402
)
import services.bazi_engine_service as _bazi_engine_service  # noqa: F401,E402
from services.bazi_engine_service import _enrich_v2_analysis  # noqa: F401,E402
from services.prometheus_monitoring import get_metrics_response  # noqa: F401,E402
from verify import verify_full as verify_full  # noqa: F401,E402
# fmt: on
