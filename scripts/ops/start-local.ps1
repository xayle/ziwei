# BaZi API local startup script
# Usage: .\start-local.ps1 [-Port 8000] [-Workers 1] [-Reload]
param(
    [int]$Port = 8000,
    [int]$Workers = 1,
    [switch]$Reload
)

$RepoRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
Set-Location $RepoRoot

if (-not (Test-Path ".\.venv\Scripts\python.exe")) {
    Write-Error "Virtual environment not found. Run: python -m venv .venv; .\.venv\Scripts\pip install -r requirements-lock.txt"
    exit 1
}

if (-not (Test-Path ".\.env")) {
    Write-Error ".env file not found. Copy .env.example to .env and fill required values."
    exit 1
}

if (-not (Test-Path ".\data\mingli.db")) {
    Write-Host "Database not found, initializing..." -ForegroundColor Yellow
    .\.venv\Scripts\python.exe scripts/seed_data.py
}

function Test-PortInUse {
    param([int]$TargetPort)
    return [bool](Get-NetTCPConnection -LocalAddress 127.0.0.1 -LocalPort $TargetPort -State Listen -ErrorAction SilentlyContinue)
}

$requestedPort = $Port
$maxProbe = 20
$probeCount = 0
while (Test-PortInUse -TargetPort $Port -and $probeCount -lt $maxProbe) {
    if ($probeCount -eq 0) {
        Write-Host "Port $requestedPort is already in use. Searching for next available port..." -ForegroundColor Yellow
    }
    $Port++
    $probeCount++
}

if ($probeCount -ge $maxProbe -and (Test-PortInUse -TargetPort $Port)) {
    Write-Error "No available port found in range $requestedPort-$($requestedPort + $maxProbe)."
    exit 1
}

if ($Port -ne $requestedPort) {
    Write-Host "Using fallback port: $Port" -ForegroundColor Yellow
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
Write-Host "  BaZi API v8.0 Local Startup" -ForegroundColor Cyan
Write-Host "  http://127.0.0.1:$Port" -ForegroundColor Green
Write-Host "  Docs: http://127.0.0.1:$Port/docs" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

.\.venv\Scripts\python.exe @uvicornArgs
