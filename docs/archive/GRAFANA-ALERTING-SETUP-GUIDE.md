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

## 🔔 Part 2: 告警查看配置（不启用 Slack / Email）

当前仓库已改为**不使用 Slack 通知，也不使用邮箱推送**。

默认策略：

- Grafana 不配置 SMTP
- AlertManager 不配置 `email_configs` / `slack_configs`
- 告警仅在 **Grafana Alerting** 和 **AlertManager UI** 中查看

### 步骤 1: 保持 Grafana 无外部推送配置

`docker-compose-monitoring.yml` / `docker-compose-monitoring-advanced.yml` 中只保留 AlertManager 地址，不启用 SMTP：

```yaml
services:
  grafana:
    environment:
      GF_SMTP_ENABLED: "false"
      GF_ALERTMANAGER_ALERT_MANAGER_URLS: "http://alertmanager:9093"
```

### 步骤 2: 使用基础 `alertmanager.yml`

当前基础配置只负责：

- 告警分组
- 告警去重
- 严重度路由
- 在 AlertManager UI 中统一查看状态

不再配置任何外部发送渠道。

### 步骤 3: 在 Grafana 中查看而不是推送

1. Grafana 左侧菜单 → **Alerting** → **Alert Rules**
2. 查看规则状态：`Normal` / `Pending` / `Firing`
3. 需要排查时，再进入 **Alerting** → **Alert instances**
4. 如需查看路由与分组结果，打开 AlertManager：`http://localhost:9093`

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

1. 保持规则本身开启
2. 不绑定 Email / Slack 渠道
3. 通过 Grafana Alerting 页面直接查看告警状态
4. 可保留标签（如 `severity:high`）用于筛选和分组

#### 步骤 3: 保存和测试

1. **Save** 保存面板
2. **Alerting** → **Alert Rules** 查看所有告警
3. 手动触发告警进行测试 (增加负载)

---

## 🧪 Part 3: 测试告警功能

### 测试 1: 触发告警

```bash
# 在另一个终端中，模拟高请求速率
for i in {1..1000}; do
  curl -X GET http://127.0.0.1:8000/health &
done
wait

# 等待 Prometheus 抓取数据 (15-30 秒)
# 如果触发告警，检查 Grafana / AlertManager UI 状态
```

### 测试 2: Grafana UI 告警

1. Grafana 左侧菜单 → **Alerting** → **Alert Rules**
2. 查看所有活跃告警
3. 点击告警查看详情、分组与状态变化

### 测试 3: AlertManager UI

1. 打开 `http://localhost:9093`
2. 确认告警已进入对应路由
3. 查看分组、抑制和已解决状态

---

## 📋 部署清单

### Grafana 仪表板部署

- [x] Docker 监控栈已启动
- [x] Grafana 访问正常 (admin/admin)
- [x] Prometheus 数据源已添加
- [x] 仪表板已导入 (grafana-dashboard.json)
- [x] 所有面板数据已显示

### 外部推送策略

- [x] SMTP 未启用
- [x] Slack Webhook 未配置
- [x] AlertManager 未配置 Email / Slack 接收器
- [x] 告警仅在 Grafana / AlertManager UI 查看

### 告警规则配置

- [x] 高请求率告警已配置 (> 100 req/s)
- [x] 高延迟告警已配置 (P95 > 1s)
- [x] 高错误率告警已配置 (> 5%)
- [x] 慢查询告警已配置 (> 5s)
- [x] 低认证成功率告警已配置 (< 80%)

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

# 5. 查看告警状态
# Grafana: Alerting → Alert Rules
# AlertManager: http://localhost:9093

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

### 未看到告警

```bash
# 检查 AlertManager 配置
docker-compose -f docker-compose-monitoring.yml exec alertmanager cat /etc/alertmanager/alertmanager.yml

# 检查 Prometheus 规则是否加载
curl http://localhost:9090/api/v1/rules

# 查看 AlertManager 当前告警
curl http://localhost:9093/api/v2/alerts
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

**配置完成！🎉 您现在可以通过 Grafana 仪表板、Grafana Alerting 和 AlertManager UI 监控 BaZi Service。**
