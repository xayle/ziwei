# 部署指南 & 生产检查清单

> **当前版本**: v8.0.3 (2026-03-04)  
> **Git 标签**: `git tag v8.0.3`  
> **测试状态**: **854 passed** (全绿，含 N5/N6/N7 新增用例) · `bazi:v8.0`

## 🎯 部署前检查清单

### 代码质量检查
- [x] 所有测试通过 (854/854 — 含 N5/N6/N7 新增用例)
- [x] 无语法错误
- [x] Pylance类型检查通过
- [x] 核心引擎覆盖率 **99%** (bazi_engine 包整体，目标≥80%)，core modules均100%
- [x] 无未处理的异常
- [x] 所有导入解决

### 安全检查
- [x] Argon2密码启用 (参数验核)
- [x] 权限级联防护实施
- [x] JWT验证启用
- [x] CSRF保护启用
- [x] SQL注入防护
- [x] XSS保护启用
- [x] CORS配置完成
- [x] 敏感信息不在日志
- [x] API密钥管理
- [x] 环境变量配置

### 性能检查
- [x] 数据库索引优化
- [x] 查询优化完成
- [x] 缓存策略制定
- [x] 连接池配置
- [x] 超时设置合理
- [x] 内存使用正常

### 数据库检查
- [x] 数据库备份计划
- [x] 外键约束完整
- [x] 索引创建完成
- [x] 初始数据加载
- [x] 迁移脚本就绪
- [x] 回滚计划制定

### 监控与日志
- [x] 审计日志启用
- [x] 错误日志配置
- [x] 日志级别设置
- [x] 日志轮换配置
- [x] 日志存储位置
- [x] 告警规则制定
- [x] **Prometheus 业务指标**: `bazi_verify_total` / `bazi_verify_duration_seconds` / `bazi_boundary_risk_total`

### 文档完成度
- [x] API文档完整
- [x] 部署指南完成 (v8.0 更新)
- [x] 故障排查指南
- [x] 权限管理指南
- [x] 开发者指南
- [x] 更新日志记录

### N7 验收门 (v8.0 发布门)
- [x] `pytest tests/` 全通过 (833 passed，核心引擎覆盖率 99% ≥ 80%)
- [x] `/verify` P95 延迟 < 3s (实测 106.95ms，N4.01 skip 已确认)
- [x] Docker healthcheck 使用 `urllib.request` [F4]，URL 已修正为 `/health`
- [x] `.dockerignore` 排除 `.env` / `.env.*` / `data/*.db` [M6.10]
- [x] SheetJS xlsx.mini.min.js (280KB) 本地化，Excel 6 Sheet 导出 [M5.03/P0-22]
- [x] CSV 字段名与 API 响应字段名零不匹配 [M5.02/红线#12]
- [x] Dockerfile `LABEL version="8.0"` (N7.07)
- [x] docker-compose.yml `image: bazi:v8.0` (N7.07)
- [x] bandit 0 MEDIUM, 0 HIGH (N7.05)
- [x] `git tag v8.0-release` 已打标

### .dockerignore 验证 (M6.10)
确认以下路径均在 `.dockerignore` 中排除，构建镜像不含敏感文件：
```
.env
.env.*
!.env.example
*.db
data/*.db
```

---

## 🚀 部署步骤

### 阶段 1: 预部署准备 (1小时)

#### 1.1 环境准备
```bash
# 检查系统要求
# - 操作系统: Windows/Linux/macOS
# - Python: 3.10+
# - 磁盘空间: 最小 500MB
# - 内存: 最小 2GB

# 创建部署目录
mkdir -p /opt/bazi-api
cd /opt/bazi-api

# 克隆代码
git clone <repository-url> .

# 验证代码完整性
git status  # 应显示干净状态
ls -la | grep -E "^d" | wc -l  # 应有主要目录
```

#### 1.2 配置文件设置
```bash
# 创建环境配置
cat > .env << EOF
# 数据库配置
DATABASE_URL=sqlite:///./bazi.db

# 安全配置
SECRET_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(32))")
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
REFRESH_TOKEN_EXPIRE_DAYS=7

# API配置
API_TITLE=BaZi API
API_VERSION=5.0.0
API_DESCRIPTION=八字分析系统

# 环境
ENVIRONMENT=production
DEBUG=false

# 日志
LOG_LEVEL=INFO
LOG_FILE=/var/log/bazi-api/app.log
EOF

# 校验配置文件
stat .env  # 文件应存在且可读
```

#### 1.3 python虚拟环境
```bash
# 创建虚拟环境
python3 -m venv .venv

# 激活虚拟环境
source .venv/bin/activate  # Linux/macOS
# 或 .\.venv\Scripts\Activate.ps1  # Windows

# 验证
which python  # 应指向.venv中的python

# 升级pip
pip install --upgrade pip setuptools wheel

# 验证版本
pip --version  # 应为最新版本
```

### 阶段 2: 依赖安装 (30分钟)

#### 2.1 安装python依赖
```bash
# 安装生产依赖
pip install -r requirements.txt

# 验证关键包
python -c "import fastapi; print(f'FastAPI: {fastapi.__version__}')"
python -c "import sqlmodel; print(f'SQLModel: {sqlmodel.__version__}')"
python -c "import argon2; print(f'Argon2: OK')"

# 检查依赖完整性
pip check  # 不应有冲突
```

#### 2.2 验证导入
```bash
# 测试关键模块导入
python -c "from run import app; print('✓ App import OK')"
python -c "from db import init_db; print('✓ DB init OK')"
python -c "from services.auth_service import hash_password; print('✓ Auth service OK')"
python -c "from services.permission_cascade_service import get_user_effective_permissions; print('✓ Cascade service OK')"
```

### 阶段 3: 数据库初始化 (15分钟)

#### 3.1 创建数据库
```bash
# 删除旧数据库(如果存在)
rm -f bazi.db

# 初始化新数据库
python -c "from db import init_db; init_db(); print('✓ Database initialized')"

# 验证数据库结构
sqlite3 bazi.db ".tables"  # 应显示9个表

# 检查表记录数
sqlite3 bazi.db "SELECT COUNT(*) FROM users;"  # 应为0
sqlite3 bazi.db ".schema users"  # 显示表结构
```

#### 3.2 加载初始数据(可选)
```bash
# 如果有初始数据脚本
python scripts/seed-data.py  # (如果存在)

# 验证数据
sqlite3 bazi.db "SELECT COUNT(*) FROM users;"
```

### 阶段 4: 测试验证 (30分钟)

#### 4.1 单元测试
```bash
# 运行全部测试
pytest tests/ -v --tb=short

# 检查结果
# 预期: 32 passed, 4 warnings

# 运行特定测试集
pytest tests/test_cascade_validation.py -v  # 权限系统 (12个)
pytest tests/test_models.py -v  # 数据模型 (7个)
```

#### 4.2 代码质量检查
```bash
# 语法检查
python -m py_compile run.py services/*.py routers/*.py

# Pylance检查 (如果配置)
pylance analyze .

# 类型检查
mypy run.py --ignore-missing-imports
```

#### 4.3 集成测试(可选)
```bash
# 设定端口与 API 地址（默认 8000；若脚本自动回退请改成实际端口）
PORT=8000
BASE_URL=http://127.0.0.1:${PORT}

# 启动API服务器
uvicorn run:app --host 127.0.0.1 --port ${PORT} &

# 等待启动
sleep 2

# 测试认证端点
curl -X POST ${BASE_URL}/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","email":"test@test.com","password":"Test123!"}'

# 停止服务器
kill %1
```

```powershell
# Windows / PowerShell 推荐：自动检查端口占用并回退
.\start-local.ps1 -Port 8000

# 或使用统一部署脚本
.\deploy.ps1 -Environment local -Action up
```

> 说明：若 `8000` 已被占用，脚本会自动切换到后续可用端口（最多探测 20 个端口），并在启动日志打印实际端口。

### 阶段 5: 部署 (20分钟)

#### 5.1 选择部署方式

**选项A: 直接运行 (开发/测试)**
```bash
# 默认端口与地址（本地脚本自动回退端口时请改为实际端口）
PORT=8000
BASE_URL=http://localhost:${PORT}

# 前台运行 (不推荐生产)
uvicorn run:app --host 0.0.0.0 --port ${PORT}

# 后台运行 (Linux)
nohup uvicorn run:app --host 0.0.0.0 --port ${PORT} > app.log 2>&1 &

# 检查运行
jobs
curl ${BASE_URL}/docs
```

```powershell
# Windows 推荐（本地开发）
.\deploy.ps1 -Environment local -Action up
# 若 8000 被占用，将自动回退到可用端口
```

**选项B: systemd服务 (推荐 - Linux)**
```bash
# 创建服务文件
sudo cat > /etc/systemd/system/bazi-api.service << EOF
[Unit]
Description=BaZi API Service
After=network.target

[Service]
Type=notify
User=www-data
WorkingDirectory=/opt/bazi-api
Environment="PATH=/opt/bazi-api/.venv/bin"
ExecStart=/opt/bazi-api/.venv/bin/uvicorn run:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# 启用服务
sudo systemctl daemon-reload
sudo systemctl enable bazi-api
sudo systemctl start bazi-api

# 检查状态
sudo systemctl status bazi-api
```

**选项C: Docker容器 (推荐 - 任意平台)**
```bash
# 构建镜像 (使用根目录的Dockerfile)
docker build -t bazi-api:latest .

# 运行容器
docker run -d \
  --name bazi-api \
  -p 8000:8000 \
  -v $(pwd)/bazi.db:/app/bazi.db \
  -e DATABASE_URL=sqlite:///./bazi.db \
  bazi-api:latest

# 检查容器
docker ps
docker logs bazi-api
```

**选项D: 云平台 (AWS/Azure/GCP)**
- 见各平台特定部署指南
- 使用Docker容器或平台特定运行时

#### 5.2 启通验证
```bash
# 与上文保持一致；如端口回退请更新 BASE_URL
PORT=8000
BASE_URL=http://localhost:${PORT}

# 检查服务状态
curl -s ${BASE_URL}/docs

# 检查各端点
curl -s ${BASE_URL}/auth/me \
  -H "Authorization: Bearer invalid" \
  -w "\nHTTP Status: %{http_code}\n"

# 查看详细日志
tail -f app.log  # 或 /var/log/bazi-api/app.log
```

### 阶段 6: 后续步骤 (持续)

#### 6.1 监控设置
```bash
# 启用日志收集
# 配置日志路径: /var/log/bazi-api/

# 设置告警规则
# - 错误率 > 1%
# - 响应时间 > 1秒
# - 内存使用 > 80%
# - 磁盘使用 > 90%

# 定期备份
crontab -e
# 添加: 0 2 * * * /opt/bazi-api/backup.sh
```

#### 6.2 定期维护
```bash
# 日志轮换
sudo logrotate -f /etc/logrotate.d/bazi-api

# 数据库备份
sqlite3 bazi.db ".backup backup-$(date +%Y%m%d).db"

# 依赖更新检查
pip list --outdated

# 安全更新
pip install -U -r requirements.txt
```

---

## 🔧 故障排查

### 常见问题

**问题 1: 端口已被占用**
```bash
# 查找占用进程
lsof -i :8000

# 杀死进程
kill -9 <PID>

# 或使用不同端口
uvicorn run:app --port 8001
```

**问题 2: 数据库锁定**
```bash
# 检查打开的连接
sqlite3 bazi.db "SELECT * FROM sqlite_master WHERE type='table';"

# 删除数据库并重新初始化
rm bazi.db
python -c "from db import init_db; init_db()"
```

**问题 3: Argon2不可用**
```bash
# 重新安装Argon2
pip uninstall argon2-cffi -y
pip install argon2-cffi --force-reinstall

# 验证
python -c "import argon2; print('OK')"
```

**问题 4: 权限错误**
```bash
# 检查文件权限
ls -la bazi.db

# 修复权限
chmod 644 bazi.db
chown www-data:www-data bazi.db  # 如果使用www-data用户
```

**问题 5: 导入错误**
```bash
# 检查PYTHONPATH
export PYTHONPATH=/opt/bazi-api:$PYTHONPATH

# 或在虚拟环境中添加
echo "export PYTHONPATH=/opt/bazi-api:$PYTHONPATH" >> .venv/bin/activate
source .venv/bin/activate
```

---

## 📊 性能优化指南

### 数据库优化
```python
# 1. 启用预写式日志 (WAL)
import sqlite3
conn = sqlite3.connect('bazi.db')
conn.execute('PRAGMA journal_mode=WAL')

# 2. 调整缓存大小
conn.execute('PRAGMA cache_size=10000')

# 3. 启用外键约束
conn.execute('PRAGMA foreign_keys=ON')
```

### API性能
```python
# 1. 启用缓存
from fastapi_cache2 import FastAPICache2

# 2. 配置连接池
# 在models.py中设置池大小
pool_size = 10
max_overflow = 20

# 3. 添加请求超时
REQUEST_TIMEOUT = 30
```

### 压缩与格式
```python
# 启用gzip压缩
from fastapi.middleware.gzip import GZIPMiddleware
app.add_middleware(GZIPMiddleware, minimum_size=1000)
```

---

## 🔒 安全加固

### 在生产中必须启用

```python
# 1. HTTPS强制
# 在nginx/反向代理中配置

# 2. HSTS头
app.add_middleware(...)

# 3. 速率限制
from slowapi import Limiter
limiter = Limiter(key_func=get_remote_address)

# 4. 请求验证
# 已由Pydantic自动完成

# 5. SQL注入防护
# 已由SQLModel参数化查询完成

# 6. XSS防护
# 已由FastAPI自动完成

# 7. CSRF防护
# 考虑添加FastAPI CSRF中间件

# 8. 安全头
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],  # 仅允许真实域名
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)
```

---

## 📈 监控指标

### 关键指标
```
- API响应时间: <500ms (95%) 
- 数据库查询: <100ms (95%)
- 权限检查: <50ms (95%)
- 错误率: <0.1%
- CPU使用: <70%
- 内存使用: <80%
- 磁盘使用: <90%
```

### 告警阈值
```
- 错误率 > 1% → CRITICAL
- 响应时间 > 2秒 → WARNING
- 内存 > 90% → WARNING
- 磁盘 > 95% → CRITICAL
```

---

## ✅ 验收标准

### 功能验收
- [x] 所有30个端点可访问
- [x] RBAC权限正常工作
- [x] 权限级联防护启用
- [x] 审计日志记录完整
- [x] 错误处理正确

### 性能验收
- [x] 响应时间 <1秒
- [x] 吞吐量 >100 req/s
- [x] 并发连接 >50

### 安全验收
- [x] 无SQL注入风险
- [x] 无认证绕过方式
- [x] Argon2密码哈希
- [x] JWT验证启用
- [x] HTTPS就绪

### 文档验收
- [x] API文档完整
- [x] 部署指南清晰
- [x] 故障排查指南详细
- [x] 代码注释充分

---

## � PostgreSQL 生产部署配置（N7.06）

生产环境建议将默认 SQLite 切换为 PostgreSQL，以获得更好的并发性能和数据可靠性。

### 1. 安装 PostgreSQL 驱动

```bash
pip install asyncpg psycopg2-binary
```

或追加到 `requirements.txt`：

```
asyncpg>=0.29
psycopg2-binary>=2.9
```

### 2. .env 配置示例

```dotenv
# SQLite（默认开发配置）
# DATABASE_URL=sqlite:///./data/mingli.db

# PostgreSQL（生产环境）
DATABASE_URL=postgresql+asyncpg://bazi_user:StrongPass@localhost:5432/mingli

# 连接池调优（PostgreSQL 推荐值）
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=30
DB_POOL_RECYCLE=3600
```

> ⚠️ `asyncpg` 异步驱动与 `SQLAlchemy` 异步引擎配合使用；如使用同步 ORM 查询，改用
> `psycopg2` 并将 URL scheme 改为 `postgresql+psycopg2://`。

### 3. 初始化数据库

```bash
# 创建数据库和用户
psql -U postgres -c "CREATE USER bazi_user WITH PASSWORD 'StrongPass';"
psql -U postgres -c "CREATE DATABASE mingli OWNER bazi_user;"

# 执行 Alembic 迁移
alembic upgrade head

# 初始化种子数据（可选）
python init_db.py
```

### 4. Docker Compose 集成

```yaml
services:
  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: bazi_user
      POSTGRES_PASSWORD: StrongPass
      POSTGRES_DB: mingli
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U bazi_user -d mingli"]
      interval: 10s
      timeout: 5s
      retries: 5

  api:
    image: bazi:v8.0
    depends_on:
      db:
        condition: service_healthy
    environment:
      DATABASE_URL: postgresql+asyncpg://bazi_user:StrongPass@db:5432/mingli
      DB_POOL_SIZE: "20"
      DB_MAX_OVERFLOW: "30"

volumes:
  pgdata:
```

### 5. 性能对比参考

| 指标 | SQLite (单机) | PostgreSQL (生产) |
|------|--------------|------------------|
| 并发写入 | 受 WAL 锁限制 | 多进程无锁 |
| P95 响应（concurrency=50） | 120.9 ms | 预期 80-100 ms |
| 连接池 | 不适用 | pool_size=20 |
| 适用场景 | 开发 / 单节点演示 | 生产 / 多节点 |

---

## �📞 支持与维护

### 获取帮助
- GitHub Issues: <repository-issues-url>
- Email: support@example.com
- 文档: {repository-docs-url}

### 反馈与改进
- 提交Issue
- 提交PR
- 发送建议邮件

---

**部署指南版本**: v8.0.3
**最后更新**: 2026年3月4日
**维护者**: DevOps Team
