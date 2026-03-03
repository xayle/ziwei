"""
tests/e2e/conftest.py — E2E Playwright 测试共享配置

运行前置条件：
    1. pip install playwright pytest-playwright
    2. playwright install chromium
    3. 启动服务：
         AUTH_BYPASS=true SECRET_KEY=dev-key uvicorn run:app --port 8000
         或
         ENGINE_V2=true AUTH_BYPASS=true SECRET_KEY=dev-key uvicorn run:app --port 8000

运行方式（本地，不进 CI）：
    pytest tests/e2e/ -v --headed             # 有浏览器窗口
    pytest tests/e2e/ -v                      # headless
    pytest tests/e2e/ -v --base-url http://localhost:8000

环境变量：
    E2E_BASE_URL  — 测试目标地址（默认 http://localhost:8000）
    E2E_SKIP_AUTH — 为 "true" 时跳过需要登录的测试（默认跳过）
"""
from __future__ import annotations

import os
import pytest

# ─── 默认 base_url ─────────────────────────────────────────────────────────────
BASE_URL = os.getenv("E2E_BASE_URL", "http://localhost:8000")


def pytest_configure(config):
    """注册自定义 marker."""
    config.addinivalue_line("markers", "e2e: mark test as E2E (requires running server + browser)")
    config.addinivalue_line("markers", "slow: mark test as slow")
