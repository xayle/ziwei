# ============================================================================
# BaZi API v7.0 — 多阶段构建
# ============================================================================

FROM python:3.11-slim as builder

# 设置Python环境变量
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# 复制和安装依赖
COPY requirements.txt ./
RUN python -m pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ============================================================================
# 生产镜像
# ============================================================================

FROM python:3.11-slim

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

# 创建数据目录
RUN mkdir -p /app/data && chown -R appuser:appuser /app/data

# 切换到非root用户
USER appuser

EXPOSE 8000

# 启动应用
CMD ["sh", "-c", "uvicorn run:app --host 0.0.0.0 --port 8000 --workers ${UVICORN_WORKERS} --log-level ${UVICORN_LOG_LEVEL}"]
