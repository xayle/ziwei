#!/usr/bin/env python3
"""
docs/samples/python_v2_example.py
——————————————————————————————————
API v2 Python 调用示例（完整可运行）

依赖：pip install httpx

使用方法：
    # 设置 BASE_URL 为服务器地址（本地开发）
    export BASE_URL=http://localhost:8000
    python docs/samples/python_v2_example.py
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime

import httpx

# ─── 配置 ─────────────────────────────────────────────────────────────────────
BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")

# 如有 JWT Token，填入此处（或通过环境变量 API_TOKEN 指定）
TOKEN = os.getenv("API_TOKEN", "")

HEADERS: dict[str, str] = {"Content-Type": "application/json"}
if TOKEN:
    HEADERS["Authorization"] = f"Bearer {TOKEN}"


# ─── 示例 1：v2 完整排盘（output_format=full）─────────────────────────────────
def example_full_verify() -> None:
    print("\n[示例 1] POST /api/v2/verify  (output_format=full)")

    payload = {
        "dt": "1990-03-15T08:30:00",
        "lon": 116.41,
        "mode": "dual",
        "solar_time_enabled": False,
        "tz": "Asia/Shanghai",
        "gender": "male",
        "city_tier": "一线",
        "industry": "金融IT",
        "output_format": "full",
    }

    with httpx.Client(base_url=BASE_URL, timeout=30.0) as client:
        resp = client.post("/api/v2/verify", json=payload, headers=HEADERS)

    if resp.status_code == 501:
        print("  ⚠️  v2 引擎未启用（ENGINE_V2=false），请设置 ENGINE_V2=true 后重试")
        return
    if resp.status_code == 429:
        print("  ⚠️  请求频率超限（429 Too Many Requests），请稍后重试")
        return

    resp.raise_for_status()
    data = resp.json()

    meta = data["meta"]
    print(f"  api_version   : {meta['api_version']}")
    print(f"  engine_version: {meta['engine_version']}")
    print(f"  calc_ms       : {meta['calc_ms']} ms")

    resp_data = data["data"]
    print(f"  response_type : {resp_data.get('response_type')}")
    if geju := resp_data.get("geju"):
        print(f"  格局名称      : {geju.get('geju_name')}")
        print(f"  格局 confidence: {geju.get('confidence')}")
    if ys := resp_data.get("yongshen"):
        print(f"  用神          : {ys.get('favor')}")
    if pillars := resp_data.get("pillars_primary"):
        day = pillars.get("day", {})
        print(f"  日柱          : {day.get('stem')}{day.get('branch')}")


# ─── 示例 2：v2 精简排盘（output_format=minimal）─────────────────────────────
def example_minimal_verify() -> None:
    print("\n[示例 2] POST /api/v2/verify  (output_format=minimal)")

    payload = {
        "dt": "1985-07-20T10:00:00",
        "lon": 121.47,
        "mode": "dual",
        "solar_time_enabled": False,
        "tz": "Asia/Shanghai",
        "gender": "female",
        "output_format": "minimal",
    }

    with httpx.Client(base_url=BASE_URL, timeout=30.0) as client:
        resp = client.post("/api/v2/verify", json=payload, headers=HEADERS)

    if resp.status_code == 501:
        print("  ⚠️  v2 引擎未启用")
        return

    resp.raise_for_status()
    data = resp.json()

    meta = data["meta"]
    print(f"  calc_ms       : {meta['calc_ms']} ms")

    resp_data = data["data"]
    print(f"  response_type : {resp_data.get('response_type')}")
    print(f"  精简字段      : {list(resp_data.keys())}")
    if ys := resp_data.get("yongshen"):
        print(f"  用神          : {ys.get('favor')}")
    if dc := resp_data.get("dayun_current"):
        print(f"  当前大运      : {dc.get('stem', '')}{dc.get('branch', '')}")


# ─── 示例 3：v2 批量排盘（POST /api/v2/batch/verify）─────────────────────────
def example_batch_verify() -> None:
    print("\n[示例 3] POST /api/v2/batch/verify")

    payload = {
        "items": [
            {
                "dt": "1990-01-01T08:00:00",
                "lon": 116.41,
                "tz": "Asia/Shanghai",
                "gender": "male",
            },
            {
                "dt": "1995-05-15T12:30:00",
                "lon": 121.47,
                "tz": "Asia/Shanghai",
                "gender": "female",
            },
        ]
    }

    with httpx.Client(base_url=BASE_URL, timeout=60.0) as client:
        resp = client.post("/api/v2/batch/verify", json=payload, headers=HEADERS)

    if resp.status_code == 429:
        retry_after = resp.headers.get("Retry-After", "60")
        print(f"  ⚠️  频率超限，请 {retry_after} 秒后重试")
        return
    if resp.status_code == 422:
        print(f"  ⚠️  请求参数错误（CSV 行数超限或字段有误）: {resp.text[:200]}")
        return

    resp.raise_for_status()
    data = resp.json()

    results = data.get("results", [])
    failed = data.get("failed", [])
    print(f"  成功 {len(results)} 条，失败 {len(failed)} 条")

    for i, r in enumerate(results):
        pillars = r.get("pillars_primary", {})
        day = pillars.get("day", {})
        geju = r.get("geju", {})
        print(f"  [{i}] 日柱={day.get('stem','?')}{day.get('branch','?')}  格局={geju.get('geju_name','?')}")

    for f in failed:
        print(f"  [FAIL] index={f['index']}  error={f['error']}")


# ─── 示例 4：检查 v1 废弃响应头（R45）─────────────────────────────────────────
def example_check_deprecation_header() -> None:
    print("\n[示例 4] 验证 /api/v1/* 废弃响应头（R45）")

    with httpx.Client(base_url=BASE_URL, timeout=10.0) as client:
        resp = client.post(
            "/api/v1/verify",
            json={
                "dt": "1990-01-01T08:00:00",
                "lon": 116.41,
                "tz": "Asia/Shanghai",
            },
            headers=HEADERS,
        )

    deprecation = resp.headers.get("Deprecation")
    sunset = resp.headers.get("Sunset")
    print(f"  Deprecation: {deprecation!r}")
    print(f"  Sunset     : {sunset!r}")
    assert deprecation == "true", "❌ 缺少 Deprecation: true 响应头"
    assert sunset == "2026-12-31", "❌ 缺少 Sunset: 2026-12-31 响应头"
    print("  ✅ 废弃声明响应头验证通过")


# ─── 主入口 ───────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print(f"=== API v2 Python 示例（BASE_URL={BASE_URL}）===")
    example_full_verify()
    example_minimal_verify()
    example_batch_verify()
    example_check_deprecation_header()
    print("\n=== 全部示例执行完毕 ===")
