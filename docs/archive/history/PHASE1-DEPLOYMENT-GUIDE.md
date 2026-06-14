# 🚀 生产部署启动指南 (Phase 1-3)

**启动日期**: 2026-02-27  
**部署阶段**: Phase 1 (基础设施准备) → Phase 2 (环境配置) → Phase 3 (监控部署)  
**预计耗时**: 4-7 小时  
**风险等级**: 中等 (可回滚)  

---

## 📋 前置检查清单

在开始生产部署前，请验证以下条件：

### ✅ 代码准备

- [x] Phase 1 优化已实施
  - db.py: 连接池扩容 (pool_size=20)
  - 6个数据库索引已创建
  - GZIP中间件已启用
  - HTTP缓存策略已配置

- [x] 性能基准测试完成
  - 300请求成功 (100% success rate)
  - 平均吞吐量: 510.6 req/s
  - 平均延迟: 71.4 ms
  - 对比报告: PHASE1-OPTIMIZATION-ANALYSIS.md

- [x] 应用启动验证
  - /health: ✅ 200 OK
  - /metrics: ✅ 200 OK
  - /docs: ✅ 200 OK
  - 无Syntax错误

### ⚠️ 部署环境验证

- [x] 服务器/VPS 已准备
- [x] 操作系统: Linux (推荐 Ubuntu 20.04 LTS 或更新)
- [x] 网络连接: 稳定，防火墙规则预留 80/443/22
- [x] 域名与SSL: 已注册，DNS已指向服务器IP

### 📦 依赖确认

- [x] PostgreSQL 13+ 已安装（或计划安装）
- [x] Python 3.9+ 已安装
- [x] Nginx 已安装
- [x] Docker & Docker Compose (可选，用于容器部署)

---

## 🔧 Phase 1: 基础设施准备 (2-4 小时)

### 步骤1.1: 服务器初始化

**SSH登录到服务器**:
```bash
ssh -i your_key.pem ubuntu@your_server_ip
```

**更新系统包**:
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y curl wget git htop vim
```

**创建应用用户** (非root运行):
```bash
sudo useradd -m -s /bin/bash baziapp
sudo usermod -aG sudo baziapp
su - baziapp
```

---

### 步骤1.2: 安装 Python & 虚拟环境

```bash
# 安装 Python 3.11+
sudo apt install -y python3.11 python3.11-venv python3.11-dev python3-pip

# 创建应用目录
mkdir -p /home/baziapp/bazi-service
cd /home/baziapp/bazi-service

# 创建虚拟环境
python3.11 -m venv venv
source venv/bin/activate

# 更新pip
pip install --upgrade pip setuptools wheel
```

---

### 步骤1.3: 安装核心依赖

**克隆/上传代码**:
```bash
# 选项A: 从git克隆
# git clone your_repo .

# 选项B: 上传本地项目文件
# scp -r -i your_key.pem ./c1/* baziapp@your_server_ip:/home/baziapp/bazi-service/
```

**安装Python依赖**:
```bash
source venv/bin/activate
pip install -r requirements.txt
```

**验证关键包**:
```bash
pip list | grep -E "fastapi|sqlmodel|requests|prometheus"
```

---

### 步骤1.4: 安装 PostgreSQL

```bash
# 添加PostgreSQL官方仓库
sudo sh -c 'echo "deb http://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list'
wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | sudo apt-key add -
sudo apt update

# 安装PostgreSQL 14
sudo apt install -y postgresql-14 postgresql-contrib-14

# 启动PostgreSQL服务
sudo systemctl enable postgresql
sudo systemctl start postgresql
```

**创建数据库和用户**:
```bash
sudo -u postgres psql <<EOF
CREATE USER bazi_user WITH PASSWORD 'your_secure_password_here';
CREATE DATABASE bazi_prod OWNER bazi_user;

-- 设置连接限制
ALTER DATABASE bazi_prod CONNECTION LIMIT 100;

-- 启用必要扩展
\c bazi_prod
CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS uuid-ossp;

-- 验证
\du
\l
EOF
```

**允许本地TCP连接** (编辑 `/etc/postgresql/14/main/postgresql.conf`):
```bash
sudo sed -i "s/#listen_addresses = 'localhost'/listen_addresses = '*'/g" /etc/postgresql/14/main/postgresql.conf
```

编辑 `/etc/postgresql/14/main/pg_hba.conf`:
```
# 在文件末尾添加
host    bazi_prod    bazi_user    127.0.0.1/32    md5
host    bazi_prod    bazi_user    ::1/128         md5
```

重启PostgreSQL:
```bash
sudo systemctl restart postgresql
```

---

### 步骤1.5: Nginx 安装

```bash
# 安装Nginx
sudo apt install -y nginx

# 启动服务
sudo systemctl enable nginx
sudo systemctl start nginx

# 验证
nginx -v
```

---

### ✅ Phase 1 验证

执行以下命令确认基础设施就绪:

```bash
# 检查Python环境
python --version

# 检查PostgreSQL
psql -U bazi_user -d bazi_prod -c "\l"  # 应列出bazi_prod数据库

# 检查Nginx
sudo systemctl status nginx  # 应显示 active (running)

# 检查防火墙状态
sudo ufw status

echo "✅ Phase 1 完成"
```

---

## ⚙️ Phase 2: 环境配置 (1-2 小时)

### 步骤2.1: 创建 .env 配置文件

在 `/home/baziapp/bazi-service/.env.production` 创建:

```bash
# ===== 应用配置 =====
ENVIRONMENT=production
DEBUG=false
SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')
API_VERSION=5.3

# ===== 数据库配置 =====
DATABASE_URL=postgresql://bazi_user:your_secure_password_here@localhost:5432/bazi_prod

# SQLAlchemy 连接池设置
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=30
DB_POOL_PRE_PING=true

# ===== 服务器配置 =====
HOST=127.0.0.1
PORT=8000
WORKERS=4  # 根据CPU核心数调整 (建议 2*CPU_CORES + 1)
WORKER_TIMEOUT=120

# ===== CORS 配置 =====
ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# ===== JWT 令牌配置 =====
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7

# ===== 日志配置 =====
LOG_LEVEL=INFO
LOG_FILE=/var/log/bazi/app.log

# ===== 告警查看配置 (可选) =====
# 当前默认仅通过 Grafana / AlertManager UI 查看告警
# 不配置 SMTP / Email / Slack 推送

# ===== Sentry 错误追踪 (可选) =====
SENTRY_DSN=your_sentry_dsn_if_configured
```

**生成安全的 SECRET_KEY**:
```bash
python3 -c 'import secrets; print(secrets.token_urlsafe(32))'
```

---

### 步骤2.2: 应用初始化

```bash
cd /home/baziapp/bazi-service
source venv/bin/activate

# 设置环境变量
export $(cat .env.production | xargs)

# 初始化数据库 (创建表结构)
python -c "from db import init_db; init_db()"

# 创建数据库索引
python scripts/apply_indexes.py

# 验证
python -c "from db import get_engine; e = get_engine(); print('✅ Database connected')"
```

---

### 步骤2.3: 创建日志目录

```bash
# 创建日志目录
sudo mkdir -p /var/log/bazi
sudo chown baziapp:baziapp /var/log/bazi
sudo chmod 755 /var/log/bazi

# 测试日志写入
touch /var/log/bazi/app.log
```

---

### 步骤2.4: Nginx 配置

创建 `/etc/nginx/sites-available/bazi-service`:

```nginx
# BaZi Service Nginx Configuration
upstream bazi_backend {
    server 127.0.0.1:8000;
    server 127.0.0.1:8001;  # 第二个worker (如果运行多个)
    keepalive 32;
}

server {
    listen 80;
    listen [::]:80;
    server_name yourdomain.com www.yourdomain.com;
    
    # 重定向到HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;

    # SSL证书 (Let's Encrypt)
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

    # SSL 安全配置
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # 性能优化
    client_max_body_size 10M;
    gzip on;
    gzip_types text/plain text/css text/javascript application/json;
    gzip_min_length 1000;

    # 日志
    access_log /var/log/nginx/bazi_access.log combined;
    error_log /var/log/nginx/bazi_error.log warn;

    # 安全头
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # API代理
    location / {
        proxy_pass http://bazi_backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;

        # 超时设置
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # 健康检查
    location /health {
        proxy_pass http://bazi_backend;
        access_log off;
    }

    # Prometheus 指标 (仅内网访问)
    location /metrics {
        proxy_pass http://bazi_backend;
        allow 127.0.0.1;
        allow 10.0.0.0/8;
        deny all;
    }
}
```

**启用Nginx配置**:
```bash
sudo ln -s /etc/nginx/sites-available/bazi-service /etc/nginx/sites-enabled/
sudo nginx -t  # 测试配置
sudo systemctl reload nginx
```

---

### ✅ Phase 2 验证

```bash
# 检查环境变量
grep -E "DATABASE_URL|SECRET_KEY" /home/baziapp/bazi-service/.env.production | head -2

# 检查数据库连接
python -c "from db import get_engine; print(get_engine())"

# 检查Nginx配置
sudo nginx -t

# 检查日志权限
ls -la /var/log/bazi/

echo "✅ Phase 2 完成"
```

---

## 🔍 Phase 3: 监控栈部署 (1 小时)

### 步骤3.1: Docker Compose 启动监控栈

```bash
# 进入应用目录
cd /home/baziapp/bazi-service

# 启动Prometheus + Grafana + AlertManager
docker-compose -f docker-compose-monitoring.yml up -d

# 验证容器运行
docker-compose ps

# 查看日志
docker-compose logs -f
```

### 步骤3.2: 配置Prometheus

生成 `/home/baziapp/bazi-service/prometheus.yml`:

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'bazi-service'
    static_configs:
      - targets: ['127.0.0.1:8000']
    metrics_path: '/metrics'
```

### 步骤3.3: Grafana 初始化

访问 `http://your_server_ip:3000`
- 默认用户: admin
- 默认密码: admin

**导入仪表板**: grafana-dashboard.json

### ✅ Phase 3 验证

```bash
# 检查容器
docker-compose -f docker-compose-monitoring.yml ps

# 验证Prometheus采集数据
curl -s http://127.0.0.1:9090/api/v1/query?query=up | jq '.'

# 验证Grafana
curl -I http://127.0.0.1:3000

echo "✅ Phase 3 完成"
```

---

## 📌 完成清单

### Phase 1: 基础设施 ✅
- [x] 服务器初始化
- [x] Python & 虚拟环境
- [x] PostgreSQL 部署
- [x] Nginx 安装

### Phase 2: 环境配置 ✅
- [x] .env.production 创建
- [x] 数据库初始化与索引
- [x] Nginx 配置
- [x] 日志目录准备

### Phase 3: 监控部署 ✅
- [x] Docker Compose 启动
- [x] Prometheus 配置
- [x] Grafana 初始化

---

## 🎯 关键命令速查

```bash
# 应用启动 (Systemd方式，见下一文档)
sudo systemctl start bazi-api
sudo systemctl status bazi-api

# 手动启动应用
cd /home/baziapp/bazi-service
source venv/bin/activate
gunicorn -w 4 -k uvicorn.workers.UvicornWorker run:app

# 查看日志
tail -f /var/log/bazi/app.log
sudo tail -f /var/log/nginx/bazi_access.log

# 监控栈管理
docker-compose -f docker-compose-monitoring.yml logs -f
docker-compose -f docker-compose-monitoring.yml stop

# 数据库备份
pg_dump -U bazi_user bazi_prod > backup.sql
```

---

## ⚠️ 故障排查

### 问题1: PostgreSQL 连接失败

```bash
# 检查PostgreSQL状态
sudo systemctl status postgresql

# 查看pg_hba.conf配置
sudo cat /etc/postgresql/14/main/pg_hba.conf | grep bazi_prod

# 重启PostgreSQL
sudo systemctl restart postgresql
```

### 问题2: 应用无法启动

```bash
# 检查Python依赖
pip list | grep fastapi

# 检查配置文件
cat .env.production | grep DATABASE_URL

# 手动运行以查看错误
python run.py
```

### 问题3: Nginx 502 Bad Gateway

```bash
# 检查后端服务
curl -v http://127.0.0.1:8000/health

# 检查Nginx配置
sudo nginx -t
sudo systemctl reload nginx

# 查看Nginx错误日志
sudo tail -f /var/log/nginx/bazi_error.log
```

---

## 📖 下一步: Phase 4-6

准备好后，按顺序执行：
1. **Phase 4**: 应用部署 (Systemd服务配置)
2. **Phase 5**: 安全加固 (防火墙、SSL证书)
3. **Phase 6**: 数据备份与恢复

详见 `PRODUCTION-DEPLOYMENT-CHECKLIST.md`

---

**准备就绪**: ✅ 所有步骤已文档化，可按顺序执行  
**下一步**: 根据您的部署方式选择继续
