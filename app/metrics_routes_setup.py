"""app/metrics_routes_setup.py — Prometheus /metrics 端点注册。

Extracted from run.py (Batch B-1 refactor, 2026-05-25).
Test patches for symbols in this module use ``app.metrics_routes_setup.*``.
"""

from __future__ import annotations

from ipaddress import ip_address as _parse_ip
from ipaddress import ip_network as _parse_network
import logging

from fastapi import FastAPI, HTTPException
from starlette.requests import Request

from services.prometheus_monitoring import get_metrics_response  # noqa: F401 — module-level; test patches this

_METRICS_ALLOWED_CIDRS = [
    _parse_network(net) for net in ("127.0.0.1/32", "10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16")
]


def _is_metrics_allowed(client_host: str) -> bool:
    """允许 localhost + 私网段访问 /metrics。(0.09 IP 白名单)"""
    try:
        ip = _parse_ip(client_host)
        return any(ip in net for net in _METRICS_ALLOWED_CIDRS)
    except ValueError:
        return False


def configure_metrics_routes(app: FastAPI, logger: logging.Logger) -> None:
    """向 app 注册 GET /metrics 端点。

    内部函数通过模块全局名称引用 ``_is_metrics_allowed`` 和
    ``get_metrics_response``，因此 ``patch("app.metrics_routes_setup._is_metrics_allowed")``
    和 ``patch("app.metrics_routes_setup.get_metrics_response")`` 可正常拦截。
    """

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
            logger.exception(f"Error exporting metrics: {e!s}", exc_info=True)
            raise HTTPException(status_code=500, detail="Failed to export metrics")
