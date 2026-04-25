# 🚀 改进快速启动指南

**快速开始**: 3分钟内体验改进的功能

---

## 📦 步骤 1: 安装依赖 (1分钟)

```bash
# 进入项目目录
cd d:\Users\Administrator\Desktop\c1

# 激活虚拟环境
.\.venv\Scripts\Activate.ps1

# 安装 prometheus-client
pip install prometheus-client
```

## ✅ 步骤 2: 验证 Token 时间改进 (10秒)

```bash
# 检查 Access Token 过期时间已改为 15 分钟
python -c "from services.auth_service import ACCESS_TOKEN_EXPIRE_MINUTES; print(f'Token 过期时间: {ACCESS_TOKEN_EXPIRE_MINUTES} 分钟')"

# 预期输出：
# Token 过期时间: 15 分钟
```

## ✅ 步骤 3: 测试 JSON 验证 (1分钟)

```bash
# 运行 Python 脚本测试 JSON 验证
python << 'EOF'
from services.json_validators import EventJsonValidator

# 测试有效的 bazi_json
valid_bazi = {
    "pillars_primary": {
        "year_pillar": {"heavenly_stem": "甲", "earthly_branch": "子"},
        "month_pillar": {"heavenly_stem": "乙", "earthly_branch": "丑"},
        "day_pillar": {"heavenly_stem": "丙", "earthly_branch": "寅"},
        "time_pillar": {"heavenly_stem": "丁", "earthly_branch": "卯"}
    },
    "ten_gods": {}
}

try:
    result = EventJsonValidator.validate_bazi_json(valid_bazi)
    print("✅ JSON 验证成功!")
except Exception as e:
    print(f"❌ 验证失败: {e}")
EOF
```

**预期输出:**
```
✅ JSON 验证成功!
```

## 🎯 步骤 4: 启动 Prometheus 监控栈 (1分钟)

### 选项 A: 使用 Docker Compose (推荐)

```bash
# 前提：需要安装 Docker 和 Docker Compose

# 启动完整的监控栈 (API + Prometheus + Grafana + AlertManager)
docker-compose -f docker-compose-monitoring.yml up -d

# 查看服务状态
docker-compose -f docker-compose-monitoring.yml ps

# 查看日志
docker-compose -f docker-compose-monitoring.yml logs -f app
```

### 选项 B: 本地启动（不使用 Docker）

```bash
# 1. 启动 API 服务
python -m uvicorn run:app --host 0.0.0.0 --port 8000 &

# 2. 安装 Prometheus (Windows)
# - 从 https://prometheus.io/download/ 下载 Windows 版本
# - 解压到 C:\prometheus
# - 将 prometheus.yml 复制到解压目录
# - 运行: C:\prometheus\prometheus.exe

# 3. 启动 Grafana
# - 安装：choco install grafana （或手动下载）
# - 或使用 Docker：docker run -p 3000:3000 grafana/grafana
```

## 📊 访问监控仪表板

完成启动后，访问以下地址：

| 服务 | 地址 | 用户 | 密码 |
|------|------|------|------|
| **API** | http://localhost:8000 | - | - |
| **API 文档** | http://localhost:8000/docs | - | - |
| **指标导出** | http://localhost:8000/metrics | - | - |
| **Prometheus** | http://localhost:9090 | - | - |
| **Grafana** | http://localhost:3000 | admin | admin |
| **AlertManager** | http://localhost:9093 | - | - |

## 🔍 查询示例

### 在 Prometheus 中查询指标

访问 http://localhost:9090，在查询框中输入：

```promql
# 查询 HTTP 请求总数
http_requests_total

# 查询平均响应时间
rate(http_request_duration_seconds_sum[5m]) / rate(http_request_duration_seconds_count[5m])

# 查询 95 分位数响应时间
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))

# 查询错误率
rate(errors_total[5m])

# 查询数据库操作延迟
rate(db_operation_duration_seconds_sum[5m]) / rate(db_operation_duration_seconds_count[5m])
```

### 创建 Grafana 仪表板

1. 访问 http://localhost:3000
2. 点击 "Create" → "Dashboard" → "Add Panel"
3. 选择 "Prometheus" 数据源
4. 在 "Metrics" 框中执行上面的 PromQL 查询
5. 设置标题和刷新间隔
6. 保存仪表板

## 🧪 运行测试

```bash
# 运行所有单元测试
python -m pytest tests/ -v

# 运行特定测试
python -m pytest tests/test_json_validators.py -v

# 生成覆盖率报告
python -m pytest tests/ --cov=services --cov=routers
```

## 📈 性能测试

```bash
# 使用 Apache Bench 进行压力测试
# 前提：安装 Apache Bench (ab.exe)

# 测试 API 端点
ab -n 1000 -c 10 http://localhost:8000/health

# 查看 Grafana 中的性能指标
# - 访问 http://localhost:3000/d/bazi-api
# - 观察请求延迟、错误率等指标
```

## 📝 常见操作

### 查看 API 健康状态

```bash
curl http://localhost:8000/health
```

### 查看指标导出

```bash
curl http://localhost:8000/metrics | head -50
```

### 停止监控栈

```bash
docker-compose -f docker-compose-monitoring.yml down
```

### 清除所有数据并重新启动

```bash
docker-compose -f docker-compose-monitoring.yml down -v
docker-compose -f docker-compose-monitoring.yml up -d
```

### 查看 Docker 容器日志

```bash
# 查看 API 服务日志
docker-compose -f docker-compose-monitoring.yml logs app

# 查看 Prometheus 日志
docker-compose -f docker-compose-monitoring.yml logs prometheus

# 查看 Grafana 日志
docker-compose -f docker-compose-monitoring.yml logs grafana

# 实时跟踪日志
docker-compose -f docker-compose-monitoring.yml logs -f
```

## 🔧 故障排查

### 问题：Prometheus 无法连接到 API

**解决方案:**
```bash
# 检查 API 是否在运行
curl http://localhost:8000/health

# 检查 prometheus.yml 中的目标配置
# 确保 targets 指向正确的地址：['localhost:8000'] 或 ['host.docker.internal:8000']
```

### 问题：Grafana 无法看到数据

**解决方案:**
```bash
# 1. 检查 Prometheus 数据源是否配置
#    Settings → Data Sources → Prometheus

# 2. 确保数据源 URL 正确：http://prometheus:9090

# 3. 刷新 Grafana 界面或检查时间范围
```

### 问题：告警不发送通知

**解决方案:**
```bash
# 1. 检查 AlertManager 是否运行
curl http://localhost:9093/-/healthy

# 2. 在 AlertManager 中检查集成配置
#    编辑 alertmanager.yml 中的接收器配置

# 3. 查看 Prometheus 中的告警状态
#    访问 http://localhost:9090/alerts
```

## 📚 文档参考

- [JSON 验证服务详细文档](services/json_validators.py)
- [Prometheus 监控详细文档](services/prometheus_monitoring.py)
- [改进实现指南](IMPROVEMENTS-IMPLEMENTATION-GUIDE.md)
- [项目自检报告](SELF-INSPECTION-REPORT-2026-02-26.md)

## ✨ 下一步

1. **集成到 API 路由** (可选)
   - 在 `routers/events.py` 中导入 `EventJsonValidator`
   - 在创建事件时验证 JSON 数据
   - 参考文档：[IMPROVEMENTS-IMPLEMENTATION-GUIDE.md](IMPROVEMENTS-IMPLEMENTATION-GUIDE.md#step-1-在-routersevents-py-中使用验证器)

2. **配置告警规则** (可选)
    - 编辑 `alertmanager.yml` 调整路由、分组和抑制规则
    - 在 Grafana / AlertManager UI 中验证告警流转

3. **创建自定义仪表板** (可选)
   - 在 Grafana 中为业务指标创建自定义面板
   - 设置 SLA 告警规则

## 📞 获取帮助

- 查看 Prometheus 文档: https://prometheus.io/docs/
- 查看 Grafana 文档: https://grafana.com/docs/
- 查看 AlertManager 文档: https://prometheus.io/docs/alerting/latest/alertmanager/

---

**版本**: v5.1.0-improvements  
**更新时间**: 2026-02-26  
**现状**: ✅ 所有改进已就绪，可以立即使用

