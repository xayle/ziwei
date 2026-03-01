# 🚀 生产部署清单

**版本**: v2.0  
**最后更新**: 2026年2月26日  
**环境**: Windows Server / Linux (CentOS/Ubuntu)

---

## 📋 部署前检查清单

### 1️⃣ 基础设施准备

#### 服务器配置

- [ ] 操作系统: CentOS 8+ / Ubuntu 20.04+ / Windows Server 2019+
- [ ] CPU: >= 4 核
- [ ] 内存: >= 8 GB (推荐 16 GB)
- [ ] 存储: >= 100 GB SSD
- [ ] 网络: >= 100 Mbps

#### 依赖软件

- [ ] Python 3.10+ 已安装
- [ ] Docker >= 20.10 (可选，推荐)
- [ ] Docker Compose >= 1.29 (可选)
- [ ] Git >= 2.30 已安装
- [ ] Nginx >= 1.20 (如使用反向代理)
- [ ] PostgreSQL 13+ (如使用 PostgreSQL，建议用于生产)

---

### 2️⃣ 应用代码准备

#### 代码审计

- [ ] 所有测试通过 (62/62 ✅)
- [ ] 代码覆盖率 >= 80%
- [ ] 没有安全警告 (SAST 扫描)
- [ ] 没有依赖漏洞
- [ ] 代码风格一致 (Black, Pylint)

#### 环境变量配置

创建 `.env.production` 文件:

```env
# ============ 应用配置 ============
ENVIRONMENT=production
APP_NAME=BaZi-Service
API_VERSION=5.3
DEBUG=false

# ============ 服务器配置 ============
HOST=0.0.0.0
PORT=8000
WORKERS=4
LOG_LEVEL=INFO

# ============ 数据库配置 ============
# 推荐用 PostgreSQL
DATABASE_URL=postgresql://user:password@db.example.com:5432/bazi_prod
SQLALCHEMY_ECHO=false
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=40

# ============ 安全配置 ============
SECRET_KEY=<生成 32 个随机字符>
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7

# ============ CORS 配置 ============
CORS_ORIGINS=https://example.com,https://app.example.com

# ============ 监控配置 ============
PROMETHEUS_ENABLED=true
PROMETHEUS_PORT=8001
METRICS_ENABLED=true

# ============ 日志配置 ============
LOG_FORMAT=json
LOG_OUTPUT=stdout,file
LOG_FILE_PATH=/var/log/bazi-service/app.log
LOG_RETENTION_DAYS=30

# ============ 邮件配置 ============
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=alerts@example.com
SMTP_PASSWORD=<app-password>
ALERT_EMAIL=ops@example.com

# ============ 备份配置 ============
BACKUP_ENABLED=true
BACKUP_SCHEDULE=0 2 * * *  # 每天 2 点
BACKUP_RETENTION_DAYS=30
BACKUP_LOCATION=/backups/bazi
```

#### 密钥生成

```bash
# 生成安全的 SECRET_KEY
python -c "import secrets; print(secrets.token_urlsafe(32))"

# 输出示例 (复制到 .env.production):
# vlj8vwNjXpK-4r_Yz-3L_6MQhT_7ZxYvWnQp9aB0dQ4=
```

---

### 3️⃣ 数据库准备

#### 数据库初始化

```bash
# 1. 创建数据库
psql -U postgres -c "CREATE DATABASE bazi_prod;"

# 2. 创建数据库用户
psql -U postgres -c "CREATE USER bazi_user WITH PASSWORD 'secure_password';"

# 3. 授予权限
psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE bazi_prod TO bazi_user;"

# 4. 运行迁移 (如使用 Alembic)
alembic upgrade head

# 或使用 SQLModel 创建表
python -c "from models import Base; from db import engine; Base.metadata.create_all(bind=engine)"

# 5. 导入初始数据 (如有)
python scripts/load_initial_data.py
```

#### 数据库优化

```sql
-- 创建必要的索引 (PostgreSQL)
CREATE INDEX idx_events_user_id ON events(user_id);
CREATE INDEX idx_events_created_at ON events(created_at);
CREATE INDEX idx_scenarios_user_id ON scenarios(user_id);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_deleted_at ON events(deleted_at);

-- 配置连接池大小
-- 在 postgresql.conf 中
max_connections = 200
shared_buffers = 256MB
effective_cache_size = 1GB

-- 分析表更新统计信息
ANALYZE events;
ANALYZE scenarios;
ANALYZE users;
```

---

### 4️⃣ SSL/TLS 配置

#### 证书部署

```bash
# 使用 Let's Encrypt 自动证书
sudo certbot certonly --standalone -d api.example.com

# 证书会保存在:
# /etc/letsencrypt/live/api.example.com/fullchain.pem
# /etc/letsencrypt/live/api.example.com/privkey.pem
```

#### Nginx 配置

```nginx
# /etc/nginx/conf.d/bazi-api.conf

upstream bazi_api {
    server localhost:8000 max_fails=3 fail_timeout=30s;
    server localhost:8001 backup;  # 备用实例
    keepalive 32;
}

server {
    listen 80;
    server_name api.example.com;
    
    # HTTP 重定向到 HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name api.example.com;
    
    # SSL 证书配置
    ssl_certificate /etc/letsencrypt/live/api.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.example.com/privkey.pem;
    
    # SSL 安全配置
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    
    # 安全响应头
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    
    # 压缩
    gzip on;
    gzip_types text/plain text/css application/json application/javascript;
    gzip_min_length 1024;
    gzip_comp_level 6;
    
    # 代理配置
    location / {
        proxy_pass http://bazi_api;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        
        # 超时配置
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # 监控端点 (内部访问)
    location /metrics {
        allow 127.0.0.1;
        allow 10.0.0.0/8;  # 内网
        deny all;
        
        proxy_pass http://bazi_api;
    }
}
```

---

### 5️⃣ 监控和告警配置

#### Prometheus 配置

```yaml
# /etc/prometheus/prometheus.yml

global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'bazi-api'
    static_configs:
      - targets: ['localhost:8001']
    basic_auth:
      username: 'prometheus'
      password: 'secure_password'

  - job_name: 'node-exporter'
    static_configs:
      - targets: ['localhost:9100']

alerting:
  alertmanagers:
    - static_configs:
        - targets: ['localhost:9093']
        
rule_files:
  - '/etc/prometheus/rules/*.yml'
```

#### AlertManager 配置

```yaml
# /etc/alertmanager/alertmanager.yml

global:
  resolve_timeout: 5m
  slack_api_url: '<slack-webhook-removed>'
  smtp_from: 'alerts@example.com'
  smtp_smarthost: 'smtp.gmail.com:587'
  smtp_auth_username: 'alerts@example.com'
  smtp_auth_password: 'app-password'

templates:
  - '/etc/alertmanager/templates/*.tmpl'

route:
  receiver: 'ops-team'
  group_by: ['alertname', 'job']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 12h
  
  routes:
    - match:
        severity: critical
      receiver: 'critical-team'
      repeat_interval: 5m
      
    - match:
        severity: warning
      receiver: 'ops-team'
      repeat_interval: 30m

receivers:
  - name: 'ops-team'
    email_configs:
      - to: 'ops@example.com'
        headers:
          Subject: 'BaZi Alert: {{ .GroupLabels.alertname }}'
    slack_configs:
      - channel: '#alerts'
        title: '{{ .GroupLabels.alertname }}'
        text: '{{ range .Alerts }}{{ .Annotations.description }}{{ end }}'

  - name: 'critical-team'
    email_configs:
      - to: 'critical@example.com'
    slack_configs:
      - channel: '#critical-alerts'
        title: 'CRITICAL: {{ .GroupLabels.alertname }}'
        text: '{{ range .Alerts }}{{ .Annotations.description }}{{ end }}'
```

---

### 6️⃣ 日志配置

#### 日志文件轮转

```bash
# /etc/logrotate.d/bazi-service

/var/log/bazi-service/*.log {
    daily
    rotate 30
    compress
    delaycompress
    notifempty
    create 0640 bazi bazi
    sharedscripts
    postrotate
        systemctl reload bazi-service > /dev/null 2>&1 || true
    endscript
}
```

#### ELK Stack 集成 (可选)

```python
# services/elk_logger.py

from pythonjsonlogger import jsonlogger
import logging
from elasticsearch import Elasticsearch

def setup_elk_logging():
    """配置 ELK Stack 日志"""
    
    # JSON 日志格式
    logHandler = logging.FileHandler('/var/log/bazi-service/app.log')
    formatter = jsonlogger.JsonFormatter()
    logHandler.setFormatter(formatter)
    
    logger = logging.getLogger()
    logger.addHandler(logHandler)
    
    # Elasticsearch 连接
    es = Elasticsearch(['http://localhost:9200'])
    
    # 定期推送日志到 ES
    # (一般由 Logstash 处理)

if __name__ == "__main__":
    setup_elk_logging()
    logging.info("ELK logging configured")
```

---

### 7️⃣ 备份策略

#### 自动备份脚本

```bash
#!/bin/bash
# /scripts/backup.sh

BACKUP_DIR="/backups/bazi-service"
DB_HOST="db.example.com"
DB_NAME="bazi_prod"
DB_USER="bazi_user"
BACKUP_RETENTION_DAYS=30
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# 创建备份目录
mkdir -p "$BACKUP_DIR"

# 数据库备份
BACKUP_FILE="$BACKUP_DIR/bazi_db_$TIMESTAMP.sql.gz"
pg_dump -h "$DB_HOST" -U "$DB_USER" "$DB_NAME" | gzip > "$BACKUP_FILE"

# 应用数据备份 (如有)
tar -czf "$BACKUP_DIR/bazi_app_$TIMESTAMP.tar.gz" /opt/bazi-service/data

# 保留策略
find "$BACKUP_DIR" -name "bazi_db_*.sql.gz" -mtime +$BACKUP_RETENTION_DAYS -delete
find "$BACKUP_DIR" -name "bazi_app_*.tar.gz" -mtime +$BACKUP_RETENTION_DAYS -delete

# 通知
echo "✅ 备份完成: $BACKUP_FILE" | mail -s "BaZi 备份报告" ops@example.com

# 备份验证
gunzip -t "$BACKUP_FILE" && echo "✅ 备份文件有效"
```

#### Cron 定时任务

```bash
# 添加到 crontab -e
0 2 * * * /scripts/backup.sh  # 每天凌晨 2 点
0 3 * * 0 /scripts/verify-backup.sh  # 每周日凌晨 3 点验证
```

---

### 8️⃣ 应用启动配置

#### Systemd 服务文件

```ini
# /etc/systemd/system/bazi-service.service

[Unit]
Description=BaZi Service API
After=network.target postgresql.service

[Service]
Type=notify
User=bazi
Group=bazi
WorkingDirectory=/opt/bazi-service

# 环境变量
EnvironmentFile=/opt/bazi-service/.env.production

# 启动命令
ExecStart=/opt/bazi-service/.venv/bin/python -m uvicorn run:app \
    --host 0.0.0.0 \
    --port 8000 \
    --workers 4 \
    --log-level info

# 重启策略
Restart=always
RestartSec=10

# 资源限制
LimitNOFILE=65535
LimitNPROC=65535

# 日志
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

#### 启动和验证

```bash
# 启用服务
sudo systemctl enable bazi-service

# 启动服务
sudo systemctl start bazi-service

# 查看状态
sudo systemctl status bazi-service

# 查看日志
sudo journalctl -u bazi-service -f

# 重启服务
sudo systemctl restart bazi-service
```

---

### 9️⃣ 性能优化

#### Uvicorn 配置优化

```python
# run.py - 更新启动配置

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "run:app",
        host="0.0.0.0",
        port=8000,
        workers=4,  # CPU 核数
        loop="uvloop",  # 高性能事件循环
        http="httptools",  # C 扩展加速
        log_level="info",
        access_log=True,
    )
```

#### Gunicorn 作为 WSGI 容器

```bash
# 如果需要额外的稳定性，使用 Gunicorn
pip install gunicorn[gevent]

# 启动命令
gunicorn -w 4 \
    -k uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000 \
    --timeout 120 \
    --graceful-timeout 30 \
    --keep-alive 5 \
    --max-requests 10000 \
    --max-requests-jitter 1000 \
    run:app
```

---

### 🔟 安全加固

#### 防火墙配置

```bash
# 使用 UFW (Ubuntu)
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp     # SSH
sudo ufw allow 80/tcp     # HTTP
sudo ufw allow 443/tcp    # HTTPS
sudo ufw allow 8000/tcp   # 内部 API (限制 IP)
sudo ufw allow from 127.0.0.1 to any port 8001  # Prometheus

sudo ufw enable
```

#### 用户权限

```bash
# 创建应用专用用户
sudo useradd -r -s /bin/false -m bazi
sudo chown -R bazi:bazi /opt/bazi-service
sudo chmod 700 /opt/bazi-service/.env.production
```

#### 定期安全更新

```bash
# Ubuntu
sudo apt update
sudo apt upgrade
sudo apt install unattended-upgrades
sudo dpkg-reconfigure unattended-upgrades

# CentOS
sudo yum update
sudo yum install yum-cron
```

---

## ✅ 部署验证清单

部署完成后执行以下验证:

- [ ] **应用健康检查**: `curl https://api.example.com/health` → 200 OK
- [ ] **API 文档**: `https://api.example.com/docs` → Swagger 界面正常
- [ ] **Prometheus metrics**: 内部访问 `/metrics` → Prometheus 格式数据
- [ ] **SSL 证书**: `openssl s_client -connect api.example.com:443` → 有效
- [ ] **数据库连接**: 应用成功连接到数据库
- [ ] **日志输出**: 应用日志正常记录
- [ ] **监控告警**: Prometheus 成功抓取指标，告警规则已加载
- [ ] **备份运行**: 备份脚本已执行，备份文件有效
- [ ] **负载均衡**: 多实例请求均衡分配
- [ ] **性能基线**: P95 延迟 < 200ms，吞吐量 > 400 req/s

---

## 🔍 部署后监控

### 第 1 小时

- 监控应用日志是否有错误
- 检查 Prometheus 指标是否正常采集
- 验证告警规则是否正常工作

### 第 1 天

- 观察 CPU 和内存使用模式
- 检查数据库连接池使用率
- 验证备份是否成功

### 第 1 周

- 分析应用性能指标是否稳定
- 验证告警是否有误报
- 评估是否需要扩容

---

## 📞 故障排除

### 常见问题

**Q: 应用无法连接数据库**
```bash
# 检查数据库连接
psql -h db.example.com -U bazi_user -d bazi_prod -c "SELECT 1;"

# 检查防火墙
telnet db.example.com 5432
```

**Q: 内存持续增长**
```python
# 检查是否有内存泄漏 (Python 内存分析)
pip install memory_profiler
@profile
def memory_intensive_function():
    pass
```

**Q: 性能突然下降**
```bash
# 检查慢查询
select * from pg_stat_statements order by mean_time desc limit 10;

# 重建索引
REINDEX INDEX idx_events_user_id;
```

---

**下一步**: 参考 [PRIORITY2-PERFORMANCE-ANALYSIS.md](PRIORITY2-PERFORMANCE-ANALYSIS.md) 和 [DATABASE-OPTIMIZATION-GUIDE.md](DATABASE-OPTIMIZATION-GUIDE.md) 对应用进行性能优化。
