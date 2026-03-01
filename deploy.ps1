<#
.SYNOPSIS
    BaZi API 部署脚本 (Windows PowerShell)

.DESCRIPTION
    支持本地开发、Docker、Kubernetes等多种部署方式

.PARAMETER Environment
    部署环境: local, docker, k8s, backup, help

.PARAMETER Action
    执行操作: up, down, restart, test, deploy, etc.

.PARAMETER Option
    可选参数: --build, 备份文件路径等

.EXAMPLE
    .\deploy.ps1 -Environment local -Action up
    .\deploy.ps1 -Environment docker -Action up -Option "--build"
    .\deploy.ps1 -Environment k8s -Action deploy

.NOTES
    版本: 5.3.1
    作者: BaZi Team
    日期: 2026-02-26
#>

[CmdletBinding()]
param(
    [Parameter(Position=0)]
    [ValidateSet('local', 'docker', 'k8s', 'backup', 'help', '')]
    [string]$Environment = 'help',

    [Parameter(Position=1)]
    [string]$Action = 'help',

    [Parameter(Position=2)]
    [string]$Option = ''
)

# ============================================================================
# 全局配置
# ============================================================================

$ErrorActionPreference = 'Stop'
$ProjectName = 'bazi-api'
$Version = '5.3.1'
$Timestamp = Get-Date -Format 'yyyyMMdd-HHmmss'

# ============================================================================
# 辅助函数
# ============================================================================

function Write-Info {
    param([string]$Message)
    Write-Host "[INFO] $Message" -ForegroundColor Blue
}

function Write-Success {
    param([string]$Message)
    Write-Host "[SUCCESS] $Message" -ForegroundColor Green
}

function Write-CustomError {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor Red
}

function Write-Warn {
    param([string]$Message)
    Write-Host "[WARN] $Message" -ForegroundColor Yellow
}

# ============================================================================
# 本地开发部署
# ============================================================================

function Deploy-Local {
    param([string]$Action)
    
    switch ($Action) {
        'up' {
            Write-Info '启动本地开发环境...'
            
            # 检查虚拟环境
            if (-not (Test-Path '.venv')) {
                Write-Info '创建虚拟环境...'
                python -m venv .venv
            }
            
            # 激活虚拟环境
            Write-Info '激活虚拟环境...'
            & '.\.venv\Scripts\Activate.ps1'
            
            # 安装依赖
            Write-Info '安装依赖...'
            .\.venv\Scripts\pip.exe install -q -r requirements.txt
            
            # 初始化数据库
            Write-Info '初始化数据库...'
            .\.venv\Scripts\python.exe -c 'from db import init_db; init_db()'
            
            # 启动服务器
            Write-Success '启动开发服务器 (端口 8000)...'
            Write-Info '访问地址: http://127.0.0.1:8000'
            Write-Info 'API文档: http://127.0.0.1:8000/docs'
            Write-Info 'UI界面: http://127.0.0.1:8000/static/verify.html'
            Write-Info ''
            Write-Info '按 Ctrl+C 停止服务器'
            Write-Info ''
            
            .\.venv\Scripts\python.exe -m uvicorn run:app --host 127.0.0.1 --port 8000 --reload
        }
        
        'down' {
            Write-Info '停止本地服务器...'
            Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue | 
                ForEach-Object { Stop-Process -Id $_.OwningProcess -Force }
            Write-Success '服务器已停止'
        }
        
        'test' {
            Write-Info '运行测试...'
            & '.\.venv\Scripts\Activate.ps1'
            .\.venv\Scripts\python.exe -m pytest -v
        }
        
        'smoke' {
            Write-Info '运行冒烟测试...'
            $env:BASE_URL = 'http://127.0.0.1:8000'
            pwsh -NoLogo -NoProfile scripts/smoke_local.ps1
        }
        
        default {
            Write-CustomError "未知操作: $Action"
            Write-Host '可用操作: up, down, test, smoke'
        }
    }
}

# ============================================================================
# Docker部署
# ============================================================================

function Deploy-Docker {
    param(
        [string]$Action,
        [string]$Option
    )
    
    # 检查Docker是否安装
    if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
        Write-CustomError 'Docker未安装或未在PATH中'
        exit 1
    }
    
    switch ($Action) {
        'up' {
            Write-Info '启动Docker容器...'
            
            # 构建镜像 (如果指定)
            if ($Option -eq '--build') {
                Write-Info '构建Docker镜像...'
                docker build -t "${ProjectName}:${Version}" -t "${ProjectName}:latest" .
            }
            
            # 启动容器
            Write-Info '启动容器...'
            docker-compose up -d
            
            # 等待容器就绪
            Start-Sleep -Seconds 3
            
            # 健康检查
            Write-Info '检查应用健康状态...'
            $maxRetries = 30
            for ($i = 1; $i -le $maxRetries; $i++) {
                try {
                    $response = Invoke-WebRequest -Uri 'http://localhost:8000/health' -ErrorAction SilentlyContinue
                    if ($response.StatusCode -eq 200) {
                        Write-Success '应用启动成功!'
                        Write-Info "API访问地址: http://localhost:8000"
                        Write-Info "API文档: http://localhost:8000/docs"
                        Write-Info "UI界面: http://localhost:8000/static/verify.html"
                        return
                    }
                }
                catch {
                    # 继续等待
                }
                
                Write-Host "." -NoNewline
                Start-Sleep -Seconds 1
            }
            
            Write-Host ""
            Write-CustomError '应用启动超时，请检查日志'
            docker-compose logs app
            exit 1
        }
        
        'down' {
            Write-Info '停止Docker容器...'
            docker-compose down
            Write-Success '容器已停止'
        }
        
        'restart' {
            Write-Info '重启Docker容器...'
            docker-compose restart
            Write-Success '容器已重启'
        }
        
        'logs' {
            Write-Info '显示容器日志...'
            docker-compose logs -f app
        }
        
        'shell' {
            Write-Info '进入容器shell...'
            docker-compose exec app /bin/bash
        }
        
        'test' {
            Write-Info '在容器中运行测试...'
            docker-compose exec app python -m pytest -v
        }
        
        'build' {
            Write-Info "构建Docker镜像 ${ProjectName}:${Version}..."
            docker build -t "${ProjectName}:${Version}" -t "${ProjectName}:latest" .
            Write-Success '镜像构建完成'
        }
        
        default {
            Write-CustomError "未知操作: $Action"
            Write-Host '可用操作: up, down, restart, logs, shell, test, build'
        }
    }
}

# ============================================================================
# Kubernetes部署
# ============================================================================

function Deploy-K8s {
    param([string]$Action)
    
    # 检查kubectl是否安装
    if (-not (Get-Command kubectl -ErrorAction SilentlyContinue)) {
        Write-CustomError 'kubectl未安装或未在PATH中'
        exit 1
    }
    
    $namespace = 'bazi-api'
    
    switch ($Action) {
        'deploy' {
            Write-Info '部署到Kubernetes...'
            
            # 创建命名空间
            Write-Info "创建命名空间 $namespace ..."
            kubectl create namespace $namespace --dry-run=client -o yaml | kubectl apply -f -
            
            # 应用配置
            if (-not (Test-Path 'k8s-deployment.yaml')) {
                Write-CustomError 'k8s-deployment.yaml 文件不存在'
                exit 1
            }
            
            Write-Info '应用Kubernetes配置...'
            kubectl apply -f k8s-deployment.yaml
            
            # 等待部署完成
            Write-Info '等待部署完成...'
            kubectl rollout status deployment/bazi-api -n $namespace --timeout=5m
            
            Write-Success 'Kubernetes部署完成!'
            Write-Info '显示Service信息:'
            kubectl get svc -n $namespace bazi-api
        }
        
        'undeploy' {
            Write-Warn '删除Kubernetes部署...'
            if (Test-Path 'k8s-deployment.yaml') {
                kubectl delete -f k8s-deployment.yaml --ignore-not-found=true
            }
            kubectl delete namespace $namespace --ignore-not-found=true
            Write-Success '部署已删除'
        }
        
        'status' {
            Write-Info '显示部署状态...'
            kubectl get deployment -n $namespace
            kubectl get pods -n $namespace
            kubectl get svc -n $namespace
        }
        
        'logs' {
            Write-Info '显示Pod日志...'
            kubectl logs -n $namespace -l app=bazi-api -f --tail=100
        }
        
        'shell' {
            Write-Info '进入Pod...'
            $pod = kubectl get pod -n $namespace -l app=bazi-api -o jsonpath='{.items[0].metadata.name}'
            if ([string]::IsNullOrEmpty($pod)) {
                Write-CustomError '没有找到运行中的Pod'
                exit 1
            }
            kubectl exec -it -n $namespace $pod -- /bin/bash
        }
        
        'port-forward' {
            Write-Info '端口转发 (localhost:8000 -> service:80)...'
            Write-Info '访问地址: http://127.0.0.1:8000'
            kubectl port-forward -n $namespace svc/bazi-api 8000:80
        }
        
        default {
            Write-CustomError "未知操作: $Action"
            Write-Host '可用操作: deploy, undeploy, status, logs, shell, port-forward'
        }
    }
}

# ============================================================================
# 备份和恢复
# ============================================================================

function Backup-BaziData {
    Write-Info '创建备份...'
    
    $backupFile = "backup-${Timestamp}.zip"
    $excludePatterns = @('.venv', '__pycache__', '.pytest_cache', '.ruff_cache', '.git', 'node_modules')
    
    # 使用tar创建备份（更可靠）
    $excludeArgs = $excludePatterns | ForEach-Object { "--exclude=$_" }
    
    Write-Info "备份文件: $backupFile"
    tar -czf $backupFile @excludeArgs .
    
    $fileSize = (Get-Item $backupFile).Length / 1MB
    Write-Success "备份完成: $backupFile ($([math]::Round($fileSize, 2)) MB)"
}

function Restore-BaziData {
    param([string]$BackupFile)
    
    if ([string]::IsNullOrEmpty($BackupFile) -or -not (Test-Path $BackupFile)) {
        Write-CustomError "备份文件不存在: $BackupFile"
        Write-Host '用法: .\deploy.ps1 -Environment backup -Action restore -Option <backup-file.zip>'
        exit 1
    }
    
    Write-Warn "恢复备份: $BackupFile"
    Write-Host '这将覆盖当前文件，是否继续? (Y/N): ' -NoNewline
    $confirm = Read-Host
    
    if ($confirm -ne 'Y' -and $confirm -ne 'y') {
        Write-Info '操作已取消'
        exit 0
    }
    
    tar -xzf $BackupFile
    Write-Success '备份恢复完成'
}

# ============================================================================
# 帮助信息
# ============================================================================

function Show-Help {
    $helpText = @"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  BaZi API v$Version 部署工具
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📋 用法:
  .\deploy.ps1 -Environment <env> -Action <action> [-Option <opt>]

🌍 环境 (Environment):
  local       本地开发环境
  docker      Docker容器
  k8s         Kubernetes集群
  backup      备份/恢复
  help        显示此帮助信息

📦 本地环境操作 (local):
  up          启动开发服务器
  down        停止服务器
  test        运行pytest测试
  smoke       运行冒烟测试

🐳 Docker操作 (docker):
  up          启动容器
  down        停止容器
  restart     重启容器
  logs        查看日志 (实时)
  shell       进入容器shell
  test        在容器中运行测试
  build       构建镜像

☸️  Kubernetes操作 (k8s):
  deploy      部署到K8s集群
  undeploy    删除K8s部署
  status      显示部署状态
  logs        查看Pod日志
  shell       进入Pod
  port-forward 端口转发到本地

💾 备份操作 (backup):
  backup      创建备份压缩包
  restore     恢复备份 (需要 -Option 指定备份文件)

📝 示例:

  # 本地开发
  .\deploy.ps1 -Environment local -Action up

  # Docker部署 (首次构建)
  .\deploy.ps1 -Environment docker -Action up -Option "--build"

  # K8s部署
  .\deploy.ps1 -Environment k8s -Action deploy

  # 创建备份
  .\deploy.ps1 -Environment backup -Action backup

  # 恢复备份
  .\deploy.ps1 -Environment backup -Action restore -Option backup-20260226-120000.zip

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

"@
    Write-Host $helpText
}

# ============================================================================
# 主程序入口
# ============================================================================

# 显示版本信息
Write-Host ''
Write-Host "BaZi API Deployment Tool v$Version" -ForegroundColor Cyan
Write-Host ''

# 处理帮助请求
if ($Environment -eq 'help' -or $Environment -eq '' -or $Action -eq 'help') {
    Show-Help
    exit 0
}

# 执行对应环境的操作
try {
    switch ($Environment) {
        'local' {
            Deploy-Local -Action $Action
        }
        
        'docker' {
            Deploy-Docker -Action $Action -Option $Option
        }
        
        'k8s' {
            Deploy-K8s -Action $Action
        }
        
        'backup' {
            if ($Action -eq 'backup') {
                Backup-BaziData
            }
            elseif ($Action -eq 'restore') {
                Restore-BaziData -BackupFile $Option
            }
            else {
                Write-CustomError "未知备份命令: $Action"
                Write-Host '可用操作: backup, restore'
                exit 1
            }
        }
        
        default {
            Write-CustomError "未知环境: $Environment"
            Show-Help
            exit 1
        }
    }
}
catch {
    Write-CustomError "执行失败: $_"
    Write-Host "错误详情: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# 成功退出
Write-Host ''
exit 0
