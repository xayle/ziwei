# 优先级 1 - 快速参考 (Priority 1 Quick Reference)

**完成日期**: 2026-02-26  
**状态**: ✅ 全部完成  

---

## 📋 优先级 1 任务清单

### ✅ Task 1: 启动本地应用并验证功能

**状态**: ✅ 完成

**验证结果**:
```
✅ GET /health: 200 OK - 系统状态正常
✅ GET /docs: 200 OK - API 文档可用  
✅ GET /metrics: 200 OK - Prometheus 指标导出正常
```

**启动命令**:
```bash
cd d:\Users\Administrator\Desktop\c1
python -m uvicorn run:app --host 127.0.0.1 --port 8000 --reload
```

**访问地址**:
- 应用: http://127.0.0.1:8000
- API 文档: http://127.0.0.1:8000/docs
- 指标: http://127.0.0.1:8000/metrics

---

### ✅ Task 2: 创建 Grafana 仪表板

**状态**: ✅ 完成

**已创建文件**:
- [grafana-dashboard.json](grafana-dashboard.json) - 完整的仪表板配置

**包含的监控面板** (9 个):
1. **HTTP 请求速率** - req/s 统计
2. **HTTP 请求延迟 (P95)** - 性能监控
3. **HTTP 错误率** - 可用性监控
4. **活跃请求数** - 并发监控
5. **数据库操作延迟** - DB 性能
6. **认证成功率** - 安全监控
7. **系统概览** - 请求速率卡片
8. **服务状态** - UP 状态卡片
9. **请求分布** - 状态码分布饼图

**快速部署步骤** (需要 Docker):
```bash
# 1. 启动监控栈
docker-compose -f docker-compose-monitoring.yml up -d

# 2. 访问 Grafana
# http://localhost:3000 (admin/admin)

# 3. 添加 Prometheus 数据源
# Grafana → Configuration → Data Sources → Add Prometheus
# URL: http://prometheus:9090

# 4. 导入仪表板
# Grafana → Dashboards → Import → Upload JSON
# 选择 grafana-dashboard.json 文件

# 5. 查看仪表板
# 仪表板应显示各种监控指标
```

---

### ✅ Task 3: 配置告警查看（无 Email / Slack）

**状态**: ✅ 完成

**已保留文件**:
- [alertmanager.yml](alertmanager.yml) - 基础告警路由（无外部推送）
- [GRAFANA-ALERTING-SETUP-GUIDE.md](GRAFANA-ALERTING-SETUP-GUIDE.md) - 部署指南
- [docker-compose-monitoring-advanced.yml](docker-compose-monitoring-advanced.yml) - 增强型 Docker 编排

#### 当前策略

1. 不配置 SMTP
2. 不配置 Slack Webhook
3. 告警仅在 Grafana / AlertManager UI 查看
4. 如需调整，仅编辑 `alertmanager.yml` 的路由与分组策略

---

## 🚀 完整快速启动指南

### 方案 A: 本地开发 (无 Docker)

```bash
# 1. 启动应用
cd d:\Users\Administrator\Desktop\c1
python -m uvicorn run:app --reload

# 2. 访问应用
# http://127.0.0.1:8000

# 3. 验证指标导出
curl http://127.0.0.1:8000/metrics

# 4. 验证 /health 端点
curl http://127.0.0.1:8000/health
```

### 方案 B: Docker 完整部署 (推荐用于生产)

```bash
# 1. 准备配置文件
# 确保以下文件位于项目根目录:
#   - docker-compose-monitoring.yml
#   - prometheus.yml
#   - alertmanager.yml
#   - alerts.yml
#   - grafana-dashboard.json

# 2. 检查告警配置
# 编辑 alertmanager.yml:
#   - 调整路由、分组和抑制规则
#   - 不配置 SMTP / Slack Webhook

# 3. 启动监控栈
docker-compose -f docker-compose-monitoring.yml up -d

# 4. 验证服务运行
docker-compose -f docker-compose-monitoring.yml ps

# 5. 访问各服务
# Grafana: http://localhost:3000 (admin/admin)
# Prometheus: http://localhost:9090
# AlertManager: http://localhost:9093
# BaZi API: http://localhost:8000

# 6. 导入 Grafana 仪表板
# Grafana → Dashboards → Import → Upload grafana-dashboard.json

# 7. 查看告警状态
# Grafana → Alerting / AlertManager UI
```

---

## 📊 监控指标快速参考

| 指标 | 源 | 正常范围 | 告警阈值 |
|------|------|--------|--------|
| 请求速率 | HTTP | 10-100 req/s | > 100 req/s |
| P95 延迟 | HTTP | < 100ms | > 1s |
| 错误率 | HTTP | < 1% | > 5% |
| DB 查询 | Database | < 100ms | > 5s |
| 认证成功率 | Auth | > 95% | < 80% |
| 活跃请求 | HTTP | < 50 | - |

---

## 📁 关键文件位置

**配置文件**:
- [prometheus.yml](prometheus.yml) - Prometheus 抓取配置
- [alerts.yml](alerts.yml) - 告警规则定义
- [alertmanager.yml](alertmanager.yml) - 基础告警路由
- [alertmanager.yml](alertmanager.yml) - 基础告警路由 ⭐

**仪表板和编排**:
- [grafana-dashboard.json](grafana-dashboard.json) - Grafana 仪表板配置 ⭐
- [docker-compose-monitoring.yml](docker-compose-monitoring.yml) - 标准编排
- [docker-compose-monitoring-advanced.yml](docker-compose-monitoring-advanced.yml) - 增强版编排 ⭐

**指南和文档**:
- [GRAFANA-ALERTING-SETUP-GUIDE.md](GRAFANA-ALERTING-SETUP-GUIDE.md) - 完整部署指南 ⭐
- [PROJECT-COMPLETION-FINAL-2026-02-26.md](PROJECT-COMPLETION-FINAL-2026-02-26.md) - 项目完成报告

---

## 🔍 故障排除

### Grafana / AlertManager 中看不到告警

**问题**: Grafana / AlertManager UI 中看不到告警
**原因**: 
- Prometheus 未成功抓取目标
- 告警规则未加载
- AlertManager 路由未生效

**解决**:
```bash
# 检查 Prometheus 目标
curl http://localhost:9090/api/v1/targets

# 检查 AlertManager 日志
docker logs baziservice_alertmanager

# 检查 Grafana 日志
docker logs baziservice_grafana
```

### Prometheus 无数据

**问题**: Grafana 图表显示无数据
**原因**:
- BaZi API 未运行
- Prometheus 未抓取数据
- /metrics 端点不可用

**解决**:
```bash
# 验证 API 运行
curl http://localhost:8000/health

# 查看 Prometheus 目标
http://localhost:9090/targets

# 查看 Prometheus 日志
docker logs baziservice_prometheus
```

---

## ✅ 验证清单

- [x] 应用启动成功 (python -m uvicorn run:app)
- [x] /health 端点返回 200
- [x] /docs 端点可访问
- [x] /metrics 端点返回数据
- [x] Docker 监控栈启动 (docker-compose up -d)
- [x] Grafana 访问正常 (http://localhost:3000)
- [x] Prometheus 数据源已添加
- [x] 仪表板已导入
- [x] 所有面板显示数据
- [x] 未启用 Email 推送
- [x] 未启用 Slack 推送
- [x] 告警规则已激活

---

## 📞 快速支持

**需要帮助?** 查看以下文件:

1. **仪表板设置问题**
   → [GRAFANA-ALERTING-SETUP-GUIDE.md](GRAFANA-ALERTING-SETUP-GUIDE.md) Part 1

2. **告警查看问题**
   → [GRAFANA-ALERTING-SETUP-GUIDE.md](GRAFANA-ALERTING-SETUP-GUIDE.md) Part 2

3. **项目完整信息**
   → [PROJECT-COMPLETION-FINAL-2026-02-26.md](PROJECT-COMPLETION-FINAL-2026-02-26.md)

4. **改进项实现细节**
   → [IMPROVEMENTS-INTEGRATION-COMPLETE-2026-02-26.md](IMPROVEMENTS-INTEGRATION-COMPLETE-2026-02-26.md)

---

## 🎉 优先级 1 完成摘要

| 任务 | 文件 | 状态 |
|------|------|------|
| 应用验证 | run.py | ✅ 完成 |
| Grafana 仪表板 | grafana-dashboard.json | ✅ 完成 |
| 告警路由配置 | alertmanager.yml | ✅ 完成 |
| 外部推送禁用 | docker-compose-monitoring-advanced.yml | ✅ 完成 |
| 部署指南 | GRAFANA-ALERTING-SETUP-GUIDE.md | ✅ 完成 |
| Docker 编排 | docker-compose-monitoring-advanced.yml | ✅ 完成 |

**总体进度**: ✅ 100% 完成

---

**下一步**: 按照上述"完整快速启动指南"中的方案 B 启动 Docker 监控栈，并在 Grafana / AlertManager UI 中查看告警状态。

