# 🚀 生产部署快速参考 - Phase 4-6

**部署阶段**: Phase 4 (应用部署) → Phase 5 (安全加固) → Phase 6 (备份恢复)  
**预计耗时**: 2-3 小时  

---

## ⚡ Phase 4: 应用部署 (30 分钟)

### Systemd 服务配置

创建 `/etc/systemd/system/bazi-api.service`:

```ini
[Unit]
Description=BaZi Service API
After=network.target postgresql.service

[Service]
Type=notify
User=baziapp
Group=www-data
WorkingDirectory=/home/baziapp/bazi-service

# 环境变量
EnvironmentFile=/home/baziapp/bazi-service/.env.production

# 启动命令
ExecStart=/home/baziapp/bazi-service/venv/bin/gunicorn \
    -w 4 \
    -k uvicorn.workers.UvicornWorker \
    -b 127.0.0.1:8000 \
    --timeout 120 \
    --access-logfile /var/log/bazi/access.log \
    --error-logfile /var/log/bazi/error.log \
    run:app

Restart=always
RestartSec=10

# 性能优化
LimitNOFILE=65536
LimitNPROC=65536

[Install]
WantedBy=multi-user.target
```

**启用服务**:
```bash
# 安装 gunicorn 依赖
pip install gunicorn

# 重新加载systemd
sudo systemctl daemon-reload

# 启用开机自动启动
sudo systemctl enable bazi-api

# 启动服务
sudo systemctl start bazi-api

# 查看状态
sudo systemctl status bazi-api

# 查看日志
sudo journalctl -u bazi-api -f
```

### 验证应用部署

```bash
# 检查应用是否运行
curl http://127.0.0.1:8000/health

# 检查Nginx反向代理
curl -I https://yourdomain.com/health

# 监控日志
tail -f /var/log/bazi/app.log
```

---

## 🔒 Phase 5: 安全加固 (1 小时)

### 步骤5.1: SSL/TLS 证书 (Let's Encrypt)

```bash
# 安装certbot
sudo apt install -y certbot python3-certbot-nginx

# 获取SSL证书
sudo certbot certonly --nginx -d yourdomain.com -d www.yourdomain.com

# 验证证书
sudo certbot certificates

# 自动续期
sudo systemctl enable certbot.timer
sudo systemctl start certbot.timer
```

### 步骤5.2: 防火墙配置 (UFW)

```bash
# 启用UFW
sudo ufw enable

# 允许SSH (防止被锁定!)
sudo ufw allow 22/tcp

# 允许HTTP/HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# 允许数据库接口 (仅本机)
sudo ufw allow from 127.0.0.1 to any port 5432

# 拒绝其他所有入站
sudo ufw default deny incoming
sudo ufw default allow outgoing

# 查看规则
sudo ufw status verbose
```

### 步骤5.3: 防暴力破解 (Fail2ban)

```bash
# 安装fail2ban
sudo apt install -y fail2ban

# 启动服务
sudo systemctl enable fail2ban
sudo systemctl start fail2ban

# 创建配置 /etc/fail2ban/jail.local
sudo tee /etc/fail2ban/jail.local > /dev/null << 'EOF'
[DEFAULT]
bantime = 3600
maxretry = 5
destemail = admin@example.com
sendername = Fail2Ban
mta = sendmail

[sshd]
enabled = true
port = ssh
logpath = /var/log/auth.log

[nginx-http-auth]
enabled = true
port = http,https
logpath = /var/log/nginx/bazi_error.log

[nginx-noscript]
enabled = true
port = http,https
logpath = /var/log/nginx/bazi_error.log
EOF

sudo systemctl restart fail2ban
```

### 步骤5.4: 自动安全更新

```bash
# 安装unattended-upgrades
sudo apt install -y unattended-upgrades apt-listchanges

# 启用自动更新
sudo dpkg-reconfigure -plow unattended-upgrades

# 查看配置
sudo cat /etc/apt/apt.conf.d/50unattended-upgrades
```

### 步骤5.5: 系统安全加固

```bash
# 禁用root登录
sudo sed -i 's/^#PermitRootLogin yes/PermitRootLogin no/' /etc/ssh/sshd_config

# 禁用密码登录 (仅SSH密钥)
sudo sed -i 's/^#PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config

# 设置文件权限
chmod 700 /home/baziapp
chmod 600 /home/baziapp/bazi-service/.env.production

# 重启SSH服务
sudo systemctl restart sshd
```

### 验证安全配置

```bash
# 检查防火墙
sudo ufw status verbose

# 检查SSL证书
sudo certbot certificates

# 检查Fail2ban
sudo fail2ban-client status

# 检查SSH配置
sudo sshd -t
```

---

## 💾 Phase 6: 备份与恢复 (30 分钟)

### 步骤6.1: 数据库自动备份

创建 `/home/baziapp/scripts/backup_db.sh`:

```bash
#!/bin/bash

BACKUP_DIR="/home/baziapp/backups"
DB_NAME="bazi_prod"
DB_USER="bazi_user"
RETENTION_DAYS=30

# 创建备份目录
mkdir -p $BACKUP_DIR

# 生成备份文件名
BACKUP_FILE="$BACKUP_DIR/bazi_prod_$(date +\%Y\%m\%d_\%H\%M\%S).sql"

# 执行备份
pg_dump -U $DB_USER $DB_NAME | gzip > $BACKUP_FILE.gz

# 检查备份是否成功
if [ -f "$BACKUP_FILE.gz" ]; then
    echo "✅ 备份成功: $BACKUP_FILE.gz"
    
    # 删除过期备份
    find $BACKUP_DIR -name "bazi_prod_*.sql.gz" -mtime +$RETENTION_DAYS -delete
    echo "✅ 清理超过 ${RETENTION_DAYS} 天的备份"
else
    echo "❌ 备份失败"
    exit 1
fi
```

**设置定时备份** (crontab):

```bash
# 每天凌晨3点执行备份
crontab -e

# 添加以下行:
0 3 * * * /home/baziapp/scripts/backup_db.sh >> /var/log/bazi/backup.log 2>&1

# 验证
crontab -l
```

### 步骤6.2: 应用配置备份

```bash
# 备份关键文件
tar -czf /home/baziapp/backups/config_$(date +\%Y\%m\%d).tar.gz \
    /home/baziapp/bazi-service/.env.production \
    /etc/nginx/sites-available/bazi-service \
    /etc/systemd/system/bazi-api.service
```

### 步骤6.3: 恢复流程

**恢复数据库**:

```bash
# 从备份恢复
gunzip -c /home/baziapp/backups/bazi_prod_20260227_030000.sql.gz | \
    psql -U bazi_user bazi_prod

# 验证恢复
psql -U bazi_user -d bazi_prod -c "\dt"
```

**恢复应用配置**:

```bash
# 解压备份
tar -xzf /home/baziapp/backups/config_20260227.tar.gz -C /

# 重启相关服务
sudo systemctl restart nginx
sudo systemctl restart bazi-api
```

### 步骤6.4: 备份验证

```bash
# 列出所有备份
ls -lh /home/baziapp/backups/

# 验证备份完整性
tar -tzf /home/baziapp/backups/config_*.tar.gz | head

# 检查备份日志
tail -f /var/log/bazi/backup.log
```

---

## ✅ 完整部署清单

### Phase 4 检查
- [x] Gunicorn 安装
- [x] Systemd 服务文件创建
- [x] 服务启动和启用
- [x] 应用日志验证
- [x] 反向代理验证

### Phase 5 检查
- [x] SSL证书获取 (Let's Encrypt)
- [x] UFW 防火墙配置
- [x] Fail2ban 安装
- [x] 自动安全更新配置
- [x] SSH 加固

### Phase 6 检查
- [x] 数据库备份脚本
- [x] 配置文件备份
- [x] Cron 定时备份
- [x] 恢复流程文档
- [x] 备份验证

---

## 🎯 部署验证命令

```bash
# 应用健康检查
curl -I https://yourdomain.com/health

# 监控页面访问 (需要VPN/内网)
curl -I https://yourdomain.com/metrics

# API文档
curl -I https://yourdomain.com/docs

# 系统日志检查
sudo tail -f /var/log/syslog

# 应用日志检查
sudo tail -f /var/log/bazi/app.log

# Nginx日志检查
sudo tail -f /var/log/nginx/bazi_access.log

# 性能监控
htop
iostat -x 1 5

# 磁盘空间
df -h

# 数据库连接池检查
psql -U bazi_user -d bazi_prod -c "SELECT datname, count(*) as connections FROM pg_stat_activity GROUP BY datname;"
```

---

## 📊 监控仪表板

### Grafana 访问

```
URL: https://yourdomain.com:3000  (如配置了反向代理)
或: http://your_server_ip:3000     (直接访问)

用户: admin
密码: (在 docker-compose-monitoring.yml 中配置)
```

### 关键告警规则

| 告警 | 阈值 | 说明 |
|------|------|------|
| 高吞吐量 | > 100 req/s | 可能需要扩容 |
| 高延迟 | P95 > 150ms | 性能下降 |
| 高错误率 | > 5% | 应用问题 |
| CPU使用率 | > 80% | 系统过载 |
| 内存使用率 | > 85% | OOM风险 |

---

## 🚨 故障排查速查表

| 问题 | 症状 | 解决方案 |
|------|------|--------|
| **应用无法启动** | 502 Bad Gateway | `systemctl status bazi-api`, 检查日志 |
| **连接超时** | 504 Gateway Timeout | 增加 Gunicorn workers, 检查DB连接 |
| **磁盘满** | 无法写入日志 | `df -h`, 清理旧日志或备份 |
| **数据库连接池耗尽** | 连接拒绝 | 检查活跃连接数, 增加 pool_size |
| **SSL证书过期** | HTTPS警告 | `sudo certbot renew --dry-run` |
| **高内存占用** | OOM killed | 检查内存泄漏, 增加SWAP或关闭不用服务 |

---

## 📈 性能优化建议

部署后，根据实际情况调整：

1. **Gunicorn workers** (当前: 4)
   ```bash
   建议: 2 * CPU_CORES + 1
   示例 (8核服务器): workers = 17
   ```

2. **PostgreSQL 连接池** (当前: 20)
   ```bash
   建议: 公式 = DB_CONNECTIONS / (WORKERS + 2)
   ```

3. **Nginx worker_connections** (当前: 768)
   ```bash
   建议根据并发数调整
   ```

4. **GZIP 压缩** (当前: minimum_size=1000)
   ```bash
   对于大API响应: 改为 500
   对于小API响应: 改为 2000
   ```

---

## 🎉 部署完成标志

部署完全成功的标志：

✅ **应用在线**: `curl https://yourdomain.com/health` 返回 200 OK  
✅ **监控就绪**: Grafana 仪表板显示数据  
✅ **日志录制**: `/var/log/bazi/app.log` 有新日志  
✅ **备份运行**: `/home/baziapp/backups/` 有最新备份  
✅ **告警配置**: AlertManager 能接收Prometheus告警  
✅ **SSL有效**: `openssl s_client -connect yourdomain.com:443` 显示有效证书  

---

## 📞 部署后支持

| 内容 | 文件位置 |
|-----|--------|
| **性能分析** | PHASE1-OPTIMIZATION-ANALYSIS.md |
| **优化指南** | DATABASE-OPTIMIZATION-GUIDE.md |
| **完整清单** | PRODUCTION-DEPLOYMENT-CHECKLIST.md |
| **部署指南** | PHASE1-DEPLOYMENT-GUIDE.md (本文档) |

---

**准备就绪**: ✅ Phase 4-6 流程已完整文档化  
**状态**: 可以立即执行生产部署  
**风险等级**: 低 (遵循文档即可安全部署)
