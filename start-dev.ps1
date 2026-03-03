#!/usr/bin/env pwsh
# start-dev.ps1 — 一键启动开发服务器（自动处理端口冲突）
# 用法: .\start-dev.ps1 [-Port 8765] [-Detach]
param(
    [int]$Port = 8765,
    [switch]$Detach     # 后台运行，不阻塞终端
)

$ErrorActionPreference = "Stop"

# 1. 设置环境变量
$env:SECRET_KEY   = "testkey-for-dev-only-not-prod"
$env:ENVIRONMENT  = "development"
$env:AUTH_BYPASS  = "true"
$env:ENGINE_V2    = "true"
$env:PYTHONIOENCODING = "utf-8"

# 2. 清理已占用端口（只检查 LISTEN 状态，忽略 TIME_WAIT 等连接）
$occupied = (Get-NetTCPConnection -LocalPort $Port -State Listen -EA SilentlyContinue).OwningProcess | Select-Object -Unique
if ($occupied) {
    foreach ($pid_ in $occupied) {
        Write-Host "[start-dev] 杀掉占用 $Port 的进程 PID=$pid_" -ForegroundColor Yellow
        Stop-Process -Id $pid_ -Force -EA SilentlyContinue
    }
    Start-Sleep -Seconds 1
}

# 3. 确认端口已释放（只检查 LISTEN 状态）
$check = Get-NetTCPConnection -LocalPort $Port -State Listen -EA SilentlyContinue
if ($check) {
    Write-Error "[start-dev] 端口 $Port 仍被占用，请手动处理"
    exit 1
}

$python = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) {
    Write-Error "[start-dev] 找不到 $python，请先创建 .venv"
    exit 1
}

$uvArgs = @("run:app", "--host", "127.0.0.1", "--port", "$Port", "--log-level", "info")

if ($Detach) {
    # 后台静默运行，输出重定向到文件
    $logOut = Join-Path $env:TEMP "bazi_dev_${Port}_out.log"
    $logErr = Join-Path $env:TEMP "bazi_dev_${Port}_err.log"
    Write-Host "[start-dev] 后台启动 PID=?" -ForegroundColor Cyan
    $proc = Start-Process -FilePath $python -ArgumentList (@("-m","uvicorn") + $uvArgs) `
        -RedirectStandardOutput $logOut -RedirectStandardError $logErr `
        -NoNewWindow -PassThru
    Start-Sleep -Seconds 3
    if ($proc.HasExited) {
        Write-Host "[start-dev] 启动失败！日志: $logErr" -ForegroundColor Red
        Get-Content $logErr -EA SilentlyContinue | Select-Object -Last 20
        exit 1
    }
    Write-Host "[start-dev] 服务器已在后台运行 PID=$($proc.Id) port=$Port" -ForegroundColor Green
    Write-Host "[start-dev] 日志: out=$logOut  err=$logErr"
    Write-Host "[start-dev] 停止: Stop-Process -Id $($proc.Id) -Force"
} else {
    # 前台运行（阻塞，Ctrl+C 停止）
    Write-Host "[start-dev] 前台启动 http://127.0.0.1:$Port/ (Ctrl+C 停止)" -ForegroundColor Green
    & $python -m uvicorn @uvArgs
}
