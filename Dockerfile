# ============================================================================
# BaZi API v8.0 — 多阶段构建
# 阶段 1: frontend-builder  — Node.js 构建前端 SPA
# 阶段 2: builder           — Python 安装依赖
# 阶段 3: production        — 最终镜像
# ============================================================================

# ──── 阶段 1: 前端 SPA 构建 ────────────────────────────────────────────────
FROM node:20-slim AS frontend-builder

WORKDIR /frontend

# 仅先复制 package 文件以利用 Docker 层缓存
COPY frontend/package*.json ./
RUN npm ci --legacy-peer-deps

# 复制前端源码并构建
COPY frontend/ ./
RUN npm run build
# 构建产物输出到 /frontend/dist/

# ──── 阶段 2: Python 依赖安装 ─────────────────────────────────────────────
FROM python:3.11-slim AS builder

# 设置Python环境变量
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# 复制和安装依赖（使用锁定版本保证可重现构建）
COPY requirements-lock.txt ./
RUN python -m pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements-lock.txt

# ──── 阶段 3: 生产镜像 ────────────────────────────────────────────────────
FROM python:3.11-slim

LABEL version="8.0" \
      maintainer="bazi-api" \
      description="八字排盘 API v8.0"

# 配置时区和Python行为
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    TZ=Asia/Shanghai \
    UVICORN_WORKERS=4 \
    UVICORN_LOG_LEVEL=info

# 创建非root用户运行应用（增强安全性）
RUN groupadd -r appuser && useradd -r -g appuser appuser

WORKDIR /app

# 从builder阶段复制Python依赖
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# 复制应用代码
COPY --chown=appuser:appuser . .

# 覆盖静态 SPA 产物：用构建阶段的最新产物替换可能滞后的快照
COPY --from=frontend-builder --chown=appuser:appuser /frontend/dist/ ./static/app/

# 创建数据目录
RUN mkdir -p /app/data && chown -R appuser:appuser /app/data

# 安装 Playwright Chromium 浏览器（§14 PDF 导出依赖）
# PLAYWRIGHT_BROWSERS_PATH 指向系统级目录，appuser 可读
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright
RUN playwright install chromium --with-deps && \
    chmod -R 755 /ms-playwright

# 切换到非root用户
USER appuser

EXPOSE 8000

# M6.11: Docker healthcheck (urllib, 无需安装 requests) [F4]
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
  CMD python -c "import urllib.request, sys; urllib.request.urlopen('http://localhost:8000/health', timeout=8); sys.exit(0)" || exit 1

# 启动应用
CMD ["sh", "-c", "uvicorn run:app --host 0.0.0.0 --port 8000 --workers ${UVICORN_WORKERS} --log-level ${UVICORN_LOG_LEVEL}"]
