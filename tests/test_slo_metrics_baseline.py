"""SLO middleware + metrics baseline (R019)."""

from __future__ import annotations

import collections

from services import slo_middleware
from services.slo_middleware import SLOMiddleware, get_all_slo_stats, get_endpoint_p95


def test_slo_p95_computation():
    slo_middleware._latency_buckets.clear()
    path = "/api/v1/bazi/full"
    bucket = collections.deque(maxlen=100)
    for ms in range(1, 101):
        bucket.append(float(ms))
    slo_middleware._latency_buckets[path] = bucket
    p95 = get_endpoint_p95(path)
    assert p95 is not None
    assert p95 >= 95


def test_slo_stats_export():
    slo_middleware._latency_buckets.clear()
    slo_middleware._latency_buckets["/api/v1/ziwei/full"] = collections.deque(
        [float(i) for i in range(1, 25)],
        maxlen=100,
    )
    stats = get_all_slo_stats()
    assert "/api/v1/ziwei/full" in stats


def test_slo_middleware_class_available():
    assert SLOMiddleware is not None


def test_metrics_response_importable():
    from services.prometheus_monitoring import get_metrics_response

    resp = get_metrics_response()
    assert resp.status_code == 200
