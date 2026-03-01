# 🚀 BaZi API v5.3 部署指南

**最后更新**: 2026年2月26日  
**版本**: 5.3.1  
**状态**: ✅ 生产就绪

---

## 📋 目录

1. [快速开始](#快速开始)
2. [部署方式选择](#部署方式选择)
3. [本地开发部署](#本地开发部署)
4. [Docker容器部署](#docker容器部署)
5. [Kubernetes部署](#kubernetes部署)
6. [配置管理](#配置管理)
7. [监控和维护](#监控和维护)
8. [故障排除](#故障排除)
9. [安全建议](#安全建议)

---

## 快速开始

### 最简单方式 (Docker)

```bash
# 1. 进入项目目录
cd /path/to/bazi-api

# 2. 启动应用
docker-compose up -d

# 3. 验证运行
curl http://localhost:8000/health
```

预期响应:
```json
{
  "status": "ok",
  "api_version": "5.3.1",
  "rule_version": "2024-v1",
  "sxtwl_available": true,
  "cnlunar_available": true
}
```

---

## 部署方式选择

### 环境对比表

| 特性 | 本地开发 | Docker | Kubernetes | 云服务 |
|------|--------|--------|-----------|--------|
| **复杂度** | ⭐ 简单 | ⭐⭐ 中等 | ⭐⭐⭐ 复杂 | ⭐⭐⭐⭐ 复杂 |
| **可扩展性** | 低 | 中等 | 高 | 高 |
| **生产就绪** | ❌ 否 | ✅ 是 | ✅ 是 | ✅ 是 |
| **成本** | 低 | 低 | 中等 | 中等-高 |
| **适用场景** | 开发/测试 | 单服务器 | 集群部署 | 企业应用 |

### 推荐选择

- **开发环境**: 本地Python + Uvicorn
- **测试环境**: Docker Compose (本文件)
- **生产环境 (小规模)**: Docker + 反向代理 (Nginx)
- **生产环境 (大规模)**: Kubernetes + Prometheus + ELK

---

## 本地开发部署

### 先决条件

- Python 3.11+ ([下载](https://www.python.org))
- pip 或 poetry

### 安装步骤

```bash
# 1. 创建虚拟环境
python -m venv .venv

# 2. 激活虚拟环境
# Windows:
.\.venv\Scripts\Activate.ps1
# macOS/Linux:
source .venv/bin/activate

# 3. 安装依赖
pip install -r requirements.txt

# 4. 初始化数据库
python -c "from db import init_db; init_db()"

# 5. 运行应用
uvicorn run:app --host 127.0.0.1 --port 8000 --reload
```

### 验证应用

```bash
# 健康检查
curl http://localhost:8000/health

# API文档
访问: http://localhost:8000/docs

# Ready探针
curl http://localhost:8000/ready
```

### 运行测试

```bash
# 完整测试套件
python -m pytest -v

# 快速测试
python -m pytest -q

# 指定测试
python -m pytest tests/test_health_check.py -v
```

---

## Docker容器部署

### 使用Docker Compose (推荐)

#### 开发环境启动

```bash
# 启动应用
docker-compose up

# 后台运行
docker-compose up -d

# 查看日志
docker-compose logs -f app

# 停止应用
docker-compose down
```

#### 生产环境启动

在 `.env.production` 中设置:

```env
# 网络配置
API_PORT=8000

# Uvicorn配置
UVICORN_WORKERS=4          # 根据CPU核心数调整
UVICORN_LOG_LEVEL=info     # 或 warning/error

# 数据库
DB_PATH=/app/data/bazi.db

# CORS配置
ALLOWED_ORIGINS=https://yourdomain.com,https://api.yourdomain.com

# 资源限制
DEPLOY_CPU_LIMIT=4
DEPLOY_CPU_RESERVE=1
DEPLOY_MEMORY_LIMIT=2G
DEPLOY_MEMORY_RESERVE=512M
```

启动生产环境:

```bash
# 加载环境变量
export $(cat .env.production | xargs)

# 启动
docker-compose -f docker-compose.yml up -d

# 查看运行状态
docker-compose ps
docker-compose stats
```

### 直接使用Docker

```bash
# 构建镜像
docker build -t bazi-api:5.3.1 .

# 运行容器
docker run -d \
  --name bazi-api \
  -p 8000:8000 \
  -v $(pwd)/data:/app/data \
  -e UVICORN_WORKERS=2 \
  -e TZ=Asia/Shanghai \
  bazi-api:5.3.1

# 查看日志
docker logs -f bazi-api

# 进行健康检查
docker ps --filter "name=bazi-api"
```

### Docker构建优化

```bash
# 1. 使用构建缓存
docker build --cache-from bazi-api:latest .

# 2. 多阶段构建 (自动使用)
# Dockerfile已优化为多阶段，减少镜像大小

# 3. 查看镜像大小
docker images | grep bazi-api

# 4. 推送到仓库 (可选)
docker tag bazi-api:5.3.1 myregistry.azurecr.io/bazi-api:5.3.1
docker push myregistry.azurecr.io/bazi-api:5.3.1
```

---

## Kubernetes部署

### 先决条件

- Kubernetes 1.20+ 集群
- kubectl 命令行工具
- 容器镜像仓库 (Docker Hub, Azure ACR 等)

### 部署到K8s

#### 1. 创建命名空间

```bash
kubectl create namespace bazi-api
```

#### 2. 创建ConfigMap (配置)

保存为 `k8s-configmap.yaml`:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: bazi-api-config
  namespace: bazi-api
data:
  TZ: "Asia/Shanghai"
  UVICORN_LOG_LEVEL: "info"
  UVICORN_WORKERS: "4"
  ALLOWED_ORIGINS: "https://yourdomain.com,https://api.yourdomain.com"
```

应用:

```bash
kubectl apply -f k8s-configmap.yaml
```

#### 3. 创建部署

保存为 `k8s-deployment.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: bazi-api
  namespace: bazi-api
  labels:
    app: bazi-api
    version: v5.3.1
spec:
  replicas: 3
  selector:
    matchLabels:
      app: bazi-api
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  template:
    metadata:
      labels:
        app: bazi-api
        version: v5.3.1
    spec:
      # 优雅关闭
      terminationGracePeriodSeconds: 30
      
      containers:
      - name: bazi-api
        image: your-registry/bazi-api:5.3.1
        imagePullPolicy: IfNotPresent
        
        # 端口
        ports:
        - name: http
          containerPort: 8000
          protocol: TCP
        
        # 环境变量
        envFrom:
        - configMapRef:
            name: bazi-api-config
        
        # 存活性探针 (Liveness Probe)
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 30
          timeoutSeconds: 5
          failureThreshold: 3
        
        # 就绪性探针 (Readiness Probe)
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3
        
        # 资源限制
        resources:
          requests:
            cpu: "500m"
            memory: "256Mi"
          limits:
            cpu: "2000m"
            memory: "1Gi"
        
        # 安全上下文
        securityContext:
          runAsNonRoot: true
          runAsUser: 1000
          allowPrivilegeEscalation: false
          readOnlyRootFilesystem: false
          capabilities:
            drop:
            - ALL
        
        # 卷挂载
        volumeMounts:
        - name: data
          mountPath: /app/data
        - name: logs
          mountPath: /app/logs
      
      # 卷定义
      volumes:
      - name: data
        emptyDir: {}  # 或使用 PersistentVolumeClaim
      - name: logs
        emptyDir: {}
      
      # Pod调度
      affinity:
        podAntiAffinity:
          preferredDuringSchedulingIgnoredDuringExecution:
          - weight: 100
            podAffinityTerm:
              labelSelector:
                matchExpressions:
                - key: app
                  operator: In
                  values:
                  - bazi-api
              topologyKey: kubernetes.io/hostname
```

应用:

```bash
kubectl apply -f k8s-deployment.yaml
```

#### 4. 创建Service

保存为 `k8s-service.yaml`:

```yaml
apiVersion: v1
kind: Service
metadata:
  name: bazi-api
  namespace: bazi-api
  labels:
    app: bazi-api
spec:
  type: LoadBalancer  # 或 ClusterIP/NodePort
  selector:
    app: bazi-api
  ports:
  - name: http
    port: 80
    targetPort: 8000
    protocol: TCP
```

应用:

```bash
kubectl apply -f k8s-service.yaml
```

#### 5. 验证部署

```bash
# 查看部署状态
kubectl get deployment -n bazi-api
kubectl get pods -n bazi-api

# 查看Service
kubectl get svc -n bazi-api

# 查看日志
kubectl logs -n bazi-api -l app=bazi-api -f

# 进行端口转发 (用于本地测试)
kubectl port-forward -n bazi-api svc/bazi-api 8000:80
```

#### 6. 自动扩展 (HPA)

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: bazi-api
  namespace: bazi-api
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: bazi-api
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

---

## 配置管理

### 环境变量

| 变量 | 说明 | 默认值 | 例值 |
|------|------|--------|------|
| `TZ` | 时区 | `Asia/Shanghai` | `UTC`, `America/New_York` |
| `DB_PATH` | 数据库路径 | `/app/data/bazi.db` | `/var/lib/bazi/bazi.db` |
| `UVICORN_WORKERS` | Worker进程数 | `1` | `4` (CPU核心数) |
| `UVICORN_LOG_LEVEL` | 日志级别 | `info` | `debug`, `warning`, `error` |
| `ALLOWED_ORIGINS` | CORS允许源 | 见代码 | `https://yourdomain.com` |

### Nginx反向代理 (推荐用于生产)

保存为 `nginx.conf`:

```nginx
upstream bazi_api {
    server localhost:8000;
    # 或多个后端
    # server localhost:8000;
    # server localhost:8001;
}

server {
    listen 80;
    server_name api.yourdomain.com;
    
    # 重定向到HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name api.yourdomain.com;
    
    # SSL证书 (使用Let's Encrypt)
    ssl_certificate /etc/letsencrypt/live/api.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.yourdomain.com/privkey.pem;
    
    # 安全头
    add_header Strict-Transport-Security "max-age=31536000" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    
    # 反向代理
    location / {
        proxy_pass http://bazi_api;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # 超时设置
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
```

---

## 监控和维护

### 健康检查端点

```bash
# 存活性检查 (Liveness Probe)
curl http://localhost:8000/health

# 就绪性检查 (Readiness Probe)
curl http://localhost:8000/ready

# 获取详细状态
curl http://localhost:8000/health | jq
```

### 日志分析

```bash
# Docker日志
docker logs -f bazi-api

# Docker Compose日志
docker-compose logs -f app --tail=100

# K8s日志
kubectl logs -n bazi-api -l app=bazi-api -f

# 实时日志流
kubectl logs -n bazi-api --all-containers=true -f
```

### 性能监控

```bash
# Docker资源使用
docker stats bazi-api

# Docker Compose资源使用
docker-compose stats

# K8s资源使用
kubectl top pods -n bazi-api
kubectl top nodes
```

### 备份和恢复

```bash
# 备份数据库
docker exec bazi-api cp /app/data/bazi.db /app/data/bazi.db.backup

# 或通过卷备份
docker run --rm -v bazi-api_data:/data -v $(pwd):/backup \
    alpine tar czf /backup/bazi-backup-$(date +%Y%m%d).tar.gz /data

# 恢复
docker run --rm -v bazi-api_data:/data -v $(pwd):/backup \
    alpine tar xzf /backup/bazi-backup-latest.tar.gz -C /
```

---

## 故障排除

### 常见问题

#### 1. 容器启动失败

**症状**: `docker-compose up` 失败，日志显示错误

**解决**:

```bash
# 查看详细日志
docker-compose logs app -f --tail=50

# 检查依赖是否安装
docker-compose exec app pip list | grep -E "fastapi|sqlmodel"

# 重建镜像
docker-compose build --no-cache
docker-compose up
```

#### 2. 数据库连接错误

**症状**: `sqlite3.OperationalError: database is locked`

**解决**:

```bash
# 数据库文件可能损坏，重新初始化
docker-compose exec app rm -f /app/data/bazi.db
docker-compose exec app python -c "from db import init_db; init_db()"
docker-compose restart
```

#### 3. 端口被占用

**症状**: `Address already in use`

**解决**:

```bash
# 查找占用端口的进程
lsof -i :8000  # macOS/Linux
netstat -ano | findstr :8000  # Windows

# 停止旧容器
docker-compose down
docker ps -a  # 查看所有容器
docker rm <container_id>  # 删除容器
```

#### 4. 性能问题

**症状**: 高延迟或响应缓慢

**解决**:

```bash
# 增加Worker数
export UVICORN_WORKERS=4
docker-compose up -d

# 检查资源
docker stats bazi-api

# 查看慢查询日志
docker-compose exec app tail -f /app/logs/slow_queries.log
```

### 调试技巧

```bash
# 进入容器调试
docker-compose exec app /bin/bash

# 运行测试
docker-compose exec app python -m pytest -v

# 检查配置
docker-compose exec app python -c "from config import settings; print(settings)"

# 数据库检查
docker-compose exec app python -c "from db import get_session; s = next(get_session()); print(s.query(User).count())"
```

---

## 安全建议

### 容器安全

- ✅ 使用非root用户运行 (已在Dockerfile中配置)
- ✅ 启用Read-Only根文件系统
- ✅ 限制特权和能力
- ✅ 定期更新基础镜像

```bash
# 扫描漏洞
docker scan bazi-api:5.3.1
```

### 网络安全

- ✅ 启用HTTPS (使用Nginx反向代理)
- ✅ 使用CORS白名单
- ✅ 启用速率限制 (已集成slowapi)
- ✅ 验证JWT Token (已集成)

### 数据安全

- ✅ 启用逻辑删除保留审计跟踪
- ✅ 定期备份数据库
- ✅ 加密敏感数据

```bash
# 创建备份
docker-compose exec app tar czf /backups/bazi-$(date +%Y%m%d-%H%M%S).tar.gz /app/data
```

### K8s安全

```yaml
# Pod安全策略
apiVersion: policy/v1beta1
kind: PodSecurityPolicy
metadata:
  name: restricted
spec:
  privileged: false
  allowPrivilegeEscalation: false
  requiredDropCapabilities:
  - ALL
  volumes:
  - 'configMap'
  - 'emptyDir'
  - 'projected'
  - 'secret'
  - 'downwardAPI'
  - 'persistentVolumeClaim'
  hostNetwork: false
  hostIPC: false
  hostPID: false
  runAsUser:
    rule: 'MustRunAsNonRoot'
```

---

## 总结

| 部署方式 | 命令 | 适用场景 |
|--------|------|--------|
| **本地** | `uvicorn run:app --reload` | 开发 |
| **Docker** | `docker-compose up -d` | 测试/小规模生产 |
| **K8s** | `kubectl apply -f k8s-*.yaml` | 大规模生产 |

---

## 获取帮助

- 📖 [API文档](./docs/api.md)
- 🐛 [问题报告](https://github.com/yourusername/bazi-api/issues)
- 💬 [讨论](https://github.com/yourusername/bazi-api/discussions)

---

**维护者**: GitHub Copilot  
**最后更新**: 2026年2月26日  
**版本**: v1.0
