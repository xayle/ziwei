# Grafana 仪表板和告警配置完整指南

## 📊 Part 1: Grafana 仪表板部署

### 前置条件

1. **Prometheus 已运行** (通过 docker-compose-monitoring.yml)
2. **Grafana 已运行** (通过 docker-compose-monitoring.yml)
3. **BaZi API 运行在 http://127.0.0.1:8000**

### 步骤 1: 启动 Docker 监控栈

```bash
cd d:\Users\Administrator\Desktop\c1

# 启动 Prometheus + Grafana + AlertManager
docker-compose -f docker-compose-monitoring.yml up -d

# 验证服务运行
docker-compose -f docker-compose-monitoring.yml ps

# 查看日志
docker-compose -f docker-compose-monitoring.yml logs -f grafana
```

**预期输出**:
```
NAME           STATUS      PORTS
app            running     0.0.0.0:8000->8000/tcp
prometheus     running     0.0.0.0:9090->9090/tcp
grafana        running     0.0.0.0:3000->3000/tcp
alertmanager   running     0.0.0.0:9093->9093/tcp
```

### 步骤 2: 访问 Grafana

```
URL: http://localhost:3000
用户名: admin
密码: admin
```

### 步骤 3: 添加 Prometheus 数据源

1. 登录 Grafana (http://localhost:3000)
2. **左侧菜单** → **Configuration** → **Data Sources**
3. **Add data source** 按钮
4. 选择 **Prometheus**
5. 输入配置:
   ```
   名称: Prometheus
   URL: http://prometheus:9090
   HTTP 方法: GET
   其他设置: 保持默认
   ```
6. 点击 **Save & Test**
   - 预期显示: "Data source is working"

### 步骤 4: 导入仪表板

#### 方法 A: 通过 JSON 文件导入 (推荐)

1. **左侧菜单** → **Dashboards** → **Import**
2. **Upload JSON file** 选项
3. 选择文件: `grafana-dashboard.json`
4. 选择数据源: **Prometheus**
5. 点击 **Import**

#### 方法 B: 手动创建仪表板

如果导入失败，可以手动创建：

1. **左侧菜单** → **Dashboards** → **Create** → **New Dashboard**
2. **Add a new panel**
3. 在 **Metric** 中输入 Prometheus 查询:
   ```promql
   rate(http_requests_total[1m])
   ```
4. 设置标题和其他选项
5. **Save**

### 仪表板面板说明

#### 面板 1: HTTP 请求速率
- **查询**: `rate(http_requests_total[1m])`
- **单位**: 请求/秒
- **告警阈值**: > 100 req/s

#### 面板 2: HTTP 请求延迟 (P95)
- **查询**: `histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))`
- **单位**: 秒
- **告警阈值**: > 1 秒

#### 面板 3: HTTP 错误率
- **查询**: `sum(rate(http_requests_total{status=~"5.."}[5m])) / sum(rate(http_requests_total[5m])) * 100`
- **单位**: 百分比
- **告警阈值**: > 5%

#### 面板 4: 活跃请求数
- **查询**: `http_requests_in_progress`
- **单位**: 个
- **说明**: 实时监控并发请求数

#### 面板 5: 数据库操作延迟
- **查询**: `rate(db_operation_duration_seconds_sum[5m]) / rate(db_operation_duration_seconds_count[5m])`
- **单位**: 毫秒
- **告警阈值**: > 5 秒

#### 面板 6: 认证成功率
- **查询**: `sum(rate(auth_attempts_total{status="success"}[5m])) / sum(rate(auth_attempts_total[5m])) * 100`
- **单位**: 百分比
- **说明**: 绿色 (>95%) | 黄色 (80-95%) | 红色 (<80%)

---

## 🔔 Part 2: 告警通知配置

### Email 通知设置

#### 步骤 1: 配置 Grafana 邮件设置

编辑 `docker-compose-monitoring.yml` 中的 Grafana 环境变量：

```yaml
services:
  grafana:
    environment:
      # SMTP 设置
      GF_SMTP_ENABLED: "true"
      GF_SMTP_HOST: smtp.gmail.com:587
      GF_SMTP_USER: your-email@gmail.com
      GF_SMTP_PASSWORD: your-app-password  # 使用 Google App Password
      GF_SMTP_FROM_ADDRESS: alerts@baziservice.com
      GF_SMTP_SKIP_VERIFY: "false"
      
      # 告警管理器地址
      GF_ALERTMANAGER_ALERTS_URL: http://alertmanager:9093
```

#### Gmail App Password 获取步骤

1. 访问 https://myaccount.google.com
2. **Security** 选项卡
3. **App & Device Passwords** (需要启用 2FA)
4. 生成 16 位密码
5. 复制密码到 `GF_SMTP_PASSWORD`

#### 步骤 2: 创建 Email 通知渠道

1. Grafana 左侧菜单 → **Alerting** → **Notification channels**
2. **New channel** 按钮
3. 填写信息:
   ```
   名称: Email Support Team
   类型: Email
   收件人: alerts@your-company.com
   是否默认: 勾选
   ```
4. **Test** 发送测试邮件
5. **Save**

---

### Slack 通知设置

#### 步骤 1: 创建 Slack Webhook

1. 访问 https://api.slack.com/apps
2. **Create New App** → **From scratch**
3. 输入应用名称 (如: BaZi-Alerts)
4. **Left Sidebar** → **Incoming Webhooks**
5. **Add New Webhook to Workspace**
6. 选择通知频道 (如: #alerts)
7. **Authorize** 后复制 Webhook URL

**Webhook URL 格式**:
```
<slack-webhook-removed>
```

#### 步骤 2: 配置 AlertManager Slack 通知

编辑 `alertmanager.yml`:

```yaml
global:
  resolve_timeout: 5m

route:
  receiver: 'slack-notifications'
  group_by: ['alertname']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 12h

receivers:
  - name: 'slack-notifications'
    slack_configs:
      - api_url: '<slack-webhook-removed>'
        channel: '#alerts'
        title: 'BaZi Service Alert'
        text: '{{ .GroupLabels.alertname }}: {{ .CommonAnnotations.summary }}'
        send_resolved: true
        color: '{{ if eq .Status "firing" }}danger{{ else }}good{{ end }}'
```

#### 步骤 3: 在 Grafana 中创建 Slack 通知渠道

1. Grafana 左侧菜单 → **Alerting** → **Notification channels**
2. **New channel** 按钮
3. 填写信息:
   ```
   名称: Slack Engineering Team
   类型: Slack
   Webhook URL: <粘贴你的 Webhook URL>
   频道: #alerts
   用户名: BaZi-Alerts
   ```
4. **Test** 发送测试消息到 Slack
5. **Save**

---

### Grafana 告警规则配置

#### 步骤 1: 编辑仪表板面板

1. 点击面板标题 → **Edit**
2. **Alert** 选项卡
3. 配置告警规则:

**示例: 高请求延迟告警**

```
Rule name: High P95 Latency
Condition: B cuando A > 1

Metric Query A:
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))

For: 5m (持续 5 分钟才触发告警)

Alert message: 
P95 HTTP request latency exceeded 1 second
Current value: {{ .Values.B }}
```

#### 步骤 2: 通知策略

1. **Send to** 选择通知渠道
2. **Notification settings**:
   - 通知频道: Email Support Team + Slack Engineering Team
   - 标签 (可选): severity:high

#### 步骤 3: 保存和测试

1. **Save** 保存面板
2. **Alerting** → **Alert Rules** 查看所有告警
3. 手动触发告警进行测试 (增加负载)

---

## 🧪 Part 3: 测试告警功能

### 测试 1: Email 告警

```bash
# 在另一个终端中，模拟高请求速率
for i in {1..1000}; do
  curl -X GET http://127.0.0.1:8000/health &
done
wait

# 等待 Prometheus 抓取数据 (15-30 秒)
# 如果触发告警，检查邮箱是否收到邮件
```

### 测试 2: Slack 告警

```bash
# AlertManager 将自动发送 Slack 消息
# 查看 #alerts 频道中的通知
```

### 测试 3: Grafana UI 告警

1. Grafana 左侧菜单 → **Alerting** → **Alert Rules**
2. 查看所有活跃告警
3. 点击告警查看详情和通知状态

---

## 📋 部署清单

### Grafana 仪表板部署

- [ ] Docker 监控栈已启动
- [ ] Grafana 访问正常 (admin/admin)
- [ ] Prometheus 数据源已添加
- [ ] 仪表板已导入 (grafana-dashboard.json)
- [ ] 所有面板数据已显示

### Email 通知配置

- [ ] SMTP 配置已设置
- [ ] Email 通知渠道已创建
- [ ] 测试邮件已发送
- [ ] 告警规则已绑定 Email 渠道

### Slack 通知配置

- [ ] Slack Webhook 已获取
- [ ] AlertManager 配置已更新
- [ ] Slack 通知渠道已创建
- [ ] 测试消息已发送到 Slack

### 告警规则配置

- [ ] 高请求率告警已配置 (> 100 req/s)
- [ ] 高延迟告警已配置 (P95 > 1s)
- [ ] 高错误率告警已配置 (> 5%)
- [ ] 慢查询告警已配置 (> 5s)
- [ ] 低认证成功率告警已配置 (< 80%)

---

## 🚀 快速启动命令

```bash
# 1. 启动监控栈
docker-compose -f docker-compose-monitoring.yml up -d

# 2. 启动 BaZi 应用
python -m uvicorn run:app --host 0.0.0.0 --port 8000

# 3. 访问 Grafana
# http://localhost:3000 (admin/admin)

# 4. 导入仪表板
# 使用 grafana-dashboard.json 文件

# 5. 配置告警通知
# Email: Configuration → Notification Channels → Email Support Team
# Slack: Configuration → Notification Channels → Slack Engineering Team

# 6. 停止监控栈
docker-compose -f docker-compose-monitoring.yml down
```

---

## 📞 故障排除

### Grafana 无法连接 Prometheus

```bash
# 检查 Prometheus 是否运行
docker-compose -f docker-compose-monitoring.yml ps

# 检查 Prometheus 日志
docker-compose -f docker-compose-monitoring.yml logs prometheus

# 验证 Prometheus 健康检查
curl http://localhost:9090/-/healthy
```

### 邮件不发送

```bash
# 检查 SMTP 设置
# 1. Gmail 需要 App Password (不是普通密码)
# 2. 需要启用"不安全应用访问"或使用 App Password
# 3. 检查防火墙是否阻止 SMTP 端口 (587)

# 在 docker-compose.yml 中查看 Grafana 日志
docker logs <grafana_container_id> | grep -i smtp
```

### Slack 消息不发送

```bash
# 检查 Webhook URL 是否正确
curl -X POST -H 'Content-type: application/json' \
  --data '{"text":"Test message"}' \
  YOUR_WEBHOOK_URL

# 检查 AlertManager 配置
docker-compose -f docker-compose-monitoring.yml exec alertmanager cat /etc/alertmanager/alertmanager.yml
```

---

## 📊 监控指标汇总

### 关键指标

| 指标 | 正常范围 | 告警阈值 |
|------|--------|--------|
| 请求速率 | 10-100 req/s | > 100 req/s |
| P95 延迟 | < 100ms | > 1s |
| 错误率 | < 1% | > 5% |
| 数据库查询 | < 100ms | > 5s |
| 认证成功率 | > 95% | < 80% |
| 活跃请求 | < 50 | - |

---

**配置完成！🎉 您现在可以通过 Grafana 仪表板和告警通知监控 BaZi Service。**
