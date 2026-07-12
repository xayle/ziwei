"""
scripts/locustfile.py — API v2 压力测试（N6.06）

使用方法：
    pip install locust
    locust -f scripts/locustfile.py --host http://localhost:8000

目标（N6.06 验收标准）：
    单并发  /api/v2/verify  P95 < 1000 ms
    10 并发 /api/v2/verify  P95 < 3000 ms

运行示例（无 UI 模式，自动终止）：
    locust -f scripts/locustfile.py --host http://localhost:8000 \\
           --users 1 --spawn-rate 1 --run-time 60s --headless \\
           --csv scripts/locust_p95_single

    locust -f scripts/locustfile.py --host http://localhost:8000 \\
           --users 10 --spawn-rate 2 --run-time 60s --headless \\
           --csv scripts/locust_p95_10

设置 API_TOKEN 环境变量可在压测中携带 JWT：
    API_TOKEN=<your_jwt> locust ...
"""
from __future__ import annotations

import json
import os
import time
import random

from locust import HttpUser, between, task, events  # type: ignore[import-untyped]

# ─── 配置 ─────────────────────────────────────────────────────────────────────
TOKEN = os.getenv("API_TOKEN", "")
# 测试请求体样本（多样化输入，避免缓存命中导致数据失真）
_SAMPLE_DTS = [
    "1990-03-15T08:30:00",
    "1985-07-20T10:00:00",
    "2000-12-31T23:30:00",
    "1978-05-05T06:00:00",
    "1993-11-11T11:11:00",
]
_SAMPLE_LONS = [116.41, 121.47, 104.06, 113.26, 87.62]


def _random_payload(output_format: str = "full") -> dict:
    return {
        "dt": random.choice(_SAMPLE_DTS),
        "lon": random.choice(_SAMPLE_LONS),
        "mode": "dual",
        "solar_time_enabled": False,
        "tz": "Asia/Shanghai",
        "gender": random.choice(["male", "female", None]),
        "output_format": output_format,
    }


# ─── 用户类 ───────────────────────────────────────────────────────────────────

class BaziV2User(HttpUser):
    """模拟访问 API v2 的用户.

    wait_time = between(1, 3)：每次任务执行后等待 1-3 秒，模拟真实用户思考时间。
    """
    wait_time = between(1, 3)

    def on_start(self) -> None:
        """设置通用请求头."""
        self.headers = {"Content-Type": "application/json"}
        if TOKEN:
            self.headers["Authorization"] = f"Bearer {TOKEN}"

    @task(8)
    def v2_verify_full(self) -> None:
        """v2 完整排盘（主要负载，权重=8）."""
        payload = _random_payload("full")
        with self.client.post(
            "/api/v2/verify",
            data=json.dumps(payload, ensure_ascii=False),
            headers=self.headers,
            catch_response=True,
            name="/api/v2/verify [full]",
        ) as resp:
            if resp.status_code == 501:
                resp.failure("ENGINE_V2=false，v2 未启用")
            elif resp.status_code == 429:
                resp.failure(f"限流 429，Retry-After={resp.headers.get('Retry-After')}")
            elif resp.status_code >= 400:
                resp.failure(f"HTTP {resp.status_code}")
            else:
                resp.success()

    @task(2)
    def v2_verify_minimal(self) -> None:
        """v2 精简排盘（权重=2，验证 minimal 路径）."""
        payload = _random_payload("minimal")
        with self.client.post(
            "/api/v2/verify",
            data=json.dumps(payload, ensure_ascii=False),
            headers=self.headers,
            catch_response=True,
            name="/api/v2/verify [minimal]",
        ) as resp:
            if resp.status_code == 501:
                resp.failure("ENGINE_V2=false")
            elif resp.status_code >= 400:
                resp.failure(f"HTTP {resp.status_code}")
            else:
                resp.success()

    @task(1)
    def v1_verify(self) -> None:
        """v1 排盘对比基准（权重=1）."""
        payload = _random_payload()
        del payload["output_format"]   # v1 无此字段
        with self.client.post(
            "/api/v1/verify",
            data=json.dumps(payload, ensure_ascii=False),
            headers=self.headers,
            catch_response=True,
            name="/api/v1/verify",
        ) as resp:
            if resp.status_code >= 400:
                resp.failure(f"HTTP {resp.status_code}")
            else:
                # 校验废弃响应头（R45）
                if "Deprecation" not in resp.headers:
                    resp.failure("缺少 Deprecation 响应头（R45 未满足）")
                else:
                    resp.success()

    @task(1)
    def health_check(self) -> None:
        """健康检查（权重=1，确认服务存活）."""
        self.client.get("/health", name="/health")

    @task(1)
    def batch_verify_small(self) -> None:
        """2条批量验证（权重=1，轻量测试批量接口）."""
        payload = {
            "items": [
                {"dt": "1990-01-01T08:00:00", "lon": 116.41, "tz": "Asia/Shanghai"},
                {"dt": "1995-05-15T12:30:00", "lon": 121.47, "tz": "Asia/Shanghai"},
            ]
        }
        with self.client.post(
            "/api/v2/batch/verify",
            data=json.dumps(payload, ensure_ascii=False),
            headers=self.headers,
            catch_response=True,
            name="/api/v2/batch/verify [2items]",
        ) as resp:
            if resp.status_code >= 400:
                resp.failure(f"HTTP {resp.status_code}")
            else:
                resp.success()


# ─── 测试结束后打印 P95 摘要 ──────────────────────────────────────────────────

@events.quitting.add_listener
def on_quitting(environment, **kw):
    stats = environment.stats
    print("\n====== P95 延迟摘要（N6.06 验收参考） ======")
    for name, entry in stats.entries.items():
        p95 = entry.get_response_time_percentile(0.95) or 0
        print(f"  {name[1]:40s}  P95={p95:6.0f} ms  RPS={entry.current_rps:.1f}")
    total = stats.total
    p95_all = total.get_response_time_percentile(0.95) or 0
    print(f"\n  总体 P95 = {p95_all:.0f} ms")
    print("  验收标准: 单并发 <1000ms，10并发 <3000ms")
    print("============================================\n")
