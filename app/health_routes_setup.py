from __future__ import annotations

import importlib.metadata as _imeta
import time
from datetime import datetime
from typing import Callable
from zoneinfo import ZoneInfo

from fastapi import FastAPI, Response

from constants import (
    API_VERSION,
    JIEQI_THRESHOLD_MIN,
    RULE_VERSION,
    SHICHEN_THRESHOLD_MIN,
    SUPPORTED_YEAR_RANGE,
)


def configure_health_routes(
    app: FastAPI,
    backend_status: Callable[[str], tuple[bool, str]],
    app_start_time: float,
    logger,
) -> None:
    @app.get("/health")
    def health():
        tz = ZoneInfo("Asia/Shanghai")
        now_local = datetime.now(tz)
        sxtwl_ok, sxtwl_ver = backend_status("sxtwl")
        cnlunar_ok, cnlunar_ver = backend_status("cnlunar")
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
        try:
            from app.models import User
            from db import get_engine
            from sqlmodel import Session, select

            with Session(get_engine()) as session:
                session.exec(select(User)).first()

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
        db_ok = False
        try:
            from db import get_engine as _get_engine
            from sqlalchemy import text as _sa_text

            with _get_engine().connect() as _conn:
                _conn.execute(_sa_text("SELECT 1"))
            db_ok = True
        except Exception:
            pass

        try:
            from services.optimization_tools import query_cache as _qc

            cache_sz = len(_qc)
        except Exception:
            cache_sz = -1

        try:
            engine_ver = _imeta.version("sxtwl")
        except Exception:
            engine_ver = "unknown"

        return {
            "db_reachable": db_ok,
            "cache_size": cache_sz,
            "engine_version": engine_ver,
            "uptime_seconds": round(time.time() - app_start_time, 1),
        }
