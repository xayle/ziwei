# deploy.ps1 部署脚本使用指南

## 概述

`deploy.ps1` 是 BaZi API 项目的统一部署脚本，支持多种部署环境和操作。

---

## 快速开始

### 查看帮助

```powershell
.\deploy.ps1 -Environment help
```

或直接运行（默认显示帮助）：

```powershell
.\deploy.ps1
```

---

## 本地开发环境

### 启动开发服务器

```powershell
.\deploy.ps1 -Environment local -Action up
```

服务器默认启动在 `http://127.0.0.1:8000`（若被占用会自动回退到后续可用端口，最多探测 20 个）

访问地址：
- API文档: http://127.0.0.1:{实际端口}/docs
- UI界面: http://127.0.0.1:{实际端口}/static/verify.html
- 健康检查: http://127.0.0.1:{实际端口}/health

### 停止开发服务器

```powershell
.\deploy.ps1 -Environment local -Action down
```

### 运行测试

```powershell
# 运行pytest测试
.\deploy.ps1 -Environment local -Action test

# 运行冒烟测试
.\deploy.ps1 -Environment local -Action smoke
```

---

## Docker部署

### 前提条件

- Docker Desktop 已安装并运行
- docker-compose 可用

### 构建并启动

```powershell
# 首次部署（构建镜像）
.\deploy.ps1 -Environment docker -Action up -Option "--build"

# 后续启动（使用已有镜像）
.\deploy.ps1 -Environment docker -Action up
```

### 停止容器

```powershell
.\deploy.ps1 -Environment docker -Action down
```

### 重启容器

```powershell
.\deploy.ps1 -Environment docker -Action restart
```

### 查看日志

```powershell
# 实时查看日志
.\deploy.ps1 -Environment docker -Action logs
```

### 进入容器

```powershell
.\deploy.ps1 -Environment docker -Action shell
```

### 在容器中运行测试

```powershell
.\deploy.ps1 -Environment docker -Action test
```

### 仅构建镜像

```powershell
.\deploy.ps1 -Environment docker -Action build
```

---

## Kubernetes部署

### 前提条件

- kubectl 已安装并配置
- 有权限访问K8s集群
- `k8s-deployment.yaml` 配置文件存在

### 部署到集群

```powershell
.\deploy.ps1 -Environment k8s -Action deploy
```

### 删除部署

```powershell
.\deploy.ps1 -Environment k8s -Action undeploy
```

### 查看部署状态

```powershell
.\deploy.ps1 -Environment k8s -Action status
```

### 查看Pod日志

```powershell
.\deploy.ps1 -Environment k8s -Action logs
```

### 进入Pod

```powershell
.\deploy.ps1 -Environment k8s -Action shell
```

### 端口转发

```powershell
# 将K8s服务转发到本地 8000 端口
.\deploy.ps1 -Environment k8s -Action port-forward
```

---

## 备份与恢复

### 创建备份

```powershell
.\deploy.ps1 -Environment backup -Action backup
```

会生成类似 `backup-20260226-143000.zip` 的备份文件。

备份内容：
- ✅ 所有源代码
- ✅ 配置文件
- ✅ 数据库文件
- ❌ 虚拟环境 (.venv)
- ❌ 缓存文件 (__pycache__)
- ❌ Git仓库 (.git)

### 恢复备份

```powershell
.\deploy.ps1 -Environment backup -Action restore -Option backup-20260226-143000.zip
```

⚠️ **警告**：恢复操作会覆盖当前文件，请谨慎操作！

---

## 参数说明

### -Environment (必需)

指定部署环境：

| 值 | 说明 |
|---|---|
| `local` | 本地开发环境 |
| `docker` | Docker容器 |
| `k8s` | Kubernetes集群 |
| `backup` | 备份/恢复操作 |
| `help` | 显示帮助信息 |

### -Action (必需)

指定要执行的操作，不同环境支持的操作不同（见上文）。

### -Option (可选)

提供额外参数：

- Docker构建: `--build`
- 备份恢复: 备份文件路径

---

## 常见问题

### Q: 脚本无法执行怎么办？

**A**: PowerShell执行策略限制。运行：

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

或使用绕过策略：

```powershell
powershell -ExecutionPolicy Bypass -File .\deploy.ps1 -Environment help
```

### Q: 端口 8000 被占用？

**A**: 现在 `up` 会自动切换到下一个可用端口（最多探测 20 个），无需手动改命令。你也可以先执行 `down` 清理旧进程：

```powershell
.\deploy.ps1 -Environment local -Action down
```

或手动释放端口：

```powershell
Get-NetTCPConnection -LocalPort 8000 | ForEach-Object { 
    Stop-Process -Id $_.OwningProcess -Force 
}
```

### Q: Docker 部署失败？

**A**: 检查：
1. Docker Desktop 是否运行
2. docker-compose.yml 是否存在
3. 查看日志: `.\deploy.ps1 -Environment docker -Action logs`

### Q: 如何快速重启服务？

**A**: 
```powershell
# 本地
.\deploy.ps1 -Environment local -Action down
.\deploy.ps1 -Environment local -Action up

# Docker
.\deploy.ps1 -Environment docker -Action restart
```

---

## 开发技巧

### 开发时的典型工作流

1. **启动服务器**
   ```powershell
   .\deploy.ps1 -Environment local -Action up
   ```

2. **修改代码**（服务器自动重载）

3. **运行测试**
   ```powershell
   # 新开一个终端
   .\deploy.ps1 -Environment local -Action test
   ```

4. **创建备份**（重大修改前）
   ```powershell
   .\deploy.ps1 -Environment backup -Action backup
   ```

### 调试Docker部署

```powershell
# 1. 构建镜像
.\deploy.ps1 -Environment docker -Action build

# 2. 启动容器
.\deploy.ps1 -Environment docker -Action up

# 3. 查看日志
.\deploy.ps1 -Environment docker -Action logs

# 4. 进入容器调试
.\deploy.ps1 -Environment docker -Action shell
```

---

## 脚本特性

✅ **参数验证** - 自动验证环境参数有效性  
✅ **错误处理** - 完善的错误捕获和提示  
✅ **健康检查** - 自动验证服务启动状态  
✅ **彩色输出** - 清晰的颜色编码信息  
✅ **交互确认** - 危险操作需要确认  
✅ **详细帮助** - 完整的使用说明  

---

## 更新日志

### v5.3.1 (2026-02-26)
- ✨ 重写为纯PowerShell脚本
- ✨ 添加参数验证和CmdletBinding
- ✨ 改进错误处理和用户体验
- ✨ 添加冒烟测试支持
- 🐛 修复批处理语法残留问题
- 🐛 解决VSCode语法错误提示

---

## 贡献

如需添加新功能或改进脚本，请：

1. Fork项目
2. 创建特性分支
3. 提交Pull Request

---

## 许可证

与 BaZi API 项目相同

---

**© 2026 BaZi Team**
