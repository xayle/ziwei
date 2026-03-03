# BaZi API — 本地启动脚本
# 用法: .\start-local.ps1 [-Port 8000] [-Workers 1] [-Reload]
param(
    [int]$Port = 8000,
    [int]$Workers = 1,
    [switch]$Reload
)

Set-Location $PSScriptRoot

# 检查虚拟环境
if (-not (Test-Path ".\.venv\Scripts\python.exe")) {
    Write-Error "未找到虚拟环境，请先运行: python -m venv .venv && .\.venv\Scripts\pip install -r requirements-lock.txt"
    exit 1
}

# 检查 .env
if (-not (Test-Path ".\.env")) {
    Write-Error "未找到 .env 文件，请先复制 .env.example 并填写配置"
    exit 1
}

# 检查数据库
if (-not (Test-Path ".\data\mingli.db")) {
    Write-Host "数据库不存在，正在初始化..." -ForegroundColor Yellow
    .\.venv\Scripts\python.exe scripts/seed_data.py
}

$uvicornArgs = @(
    "-m", "uvicorn", "run:app",
    "--host", "127.0.0.1",
    "--port", "$Port",
    "--workers", "$Workers"
)
if ($Reload) { $uvicornArgs += "--reload" }

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  BaZi API v8.0  本地启动" -ForegroundColor Cyan
Write-Host "  http://127.0.0.1:$Port" -ForegroundColor Green
Write-Host "  文档: http://127.0.0.1:$Port/docs" -ForegroundColor Green
Write-Host "  管理员: admin / BaZi@2025!" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

.\.venv\Scripts\python.exe @uvicornArgs
