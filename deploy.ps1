<#
.SYNOPSIS
    BaZi API deployment helper (Windows PowerShell)

.DESCRIPTION
    Supports local development, Docker, Kubernetes, backup and restore.

.EXAMPLE
    .\deploy.ps1 -Environment local -Action up
    .\deploy.ps1 -Environment docker -Action up -Option "--build"
    .\deploy.ps1 -Environment k8s -Action deploy
#>

[CmdletBinding()]
param(
    [Parameter(Position = 0)]
    [ValidateSet('local', 'docker', 'k8s', 'backup', 'help', '')]
    [string]$Environment = 'help',

    [Parameter(Position = 1)]
    [string]$Action = 'help',

    [Parameter(Position = 2)]
    [string]$Option = ''
)

$ErrorActionPreference = 'Stop'
$ProjectName = 'bazi-api'
$Version = '8.0'
$Timestamp = Get-Date -Format 'yyyyMMdd-HHmmss'

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

function Test-PortInUse {
    param([int]$Port)
    return [bool](Get-NetTCPConnection -LocalAddress 127.0.0.1 -LocalPort $Port -State Listen -ErrorAction SilentlyContinue)
}

function Get-AvailableLocalPort {
    param(
        [int]$StartPort = 8000,
        [int]$MaxProbe = 20
    )

    $port = $StartPort
    $count = 0
    while ((Test-PortInUse -Port $port) -and $count -lt $MaxProbe) {
        $port++
        $count++
    }

    if ($count -ge $MaxProbe -and (Test-PortInUse -Port $port)) {
        throw "No available port in range $StartPort-$($StartPort + $MaxProbe)"
    }

    return $port
}

function Deploy-Local {
    param([string]$Action)

    switch ($Action) {
        'up' {
            Write-Info 'Starting local development environment...'

            if (-not (Test-Path '.venv')) {
                Write-Info 'Creating virtual environment...'
                python -m venv .venv
            }

            Write-Info 'Activating virtual environment...'
            & '.\.venv\Scripts\Activate.ps1'

            Write-Info 'Installing dependencies...'
            .\.venv\Scripts\pip.exe install -q -r requirements.txt

            Write-Info 'Building frontend...'
            if (Test-Path 'frontend\package.json') {
                if (-not (Test-Path 'frontend\node_modules')) {
                    Write-Info '  Installing npm dependencies...'
                    npm install --prefix frontend --legacy-peer-deps
                }
                npm run build --prefix frontend
                Write-Success '  Frontend built → static/app/'
            } else {
                Write-Warn '  frontend/package.json not found, skipping build'
            }

            Write-Info 'Applying database migrations (alembic upgrade head)...'
            $alembicOk = $false
            try {
                .\.venv\Scripts\python.exe -m alembic upgrade head
                $alembicOk = $true
                Write-Success '  Migrations applied'
            } catch {
                Write-Warn "  alembic upgrade head failed: $_"
                Write-Info '  Falling back to init_db (SQLModel.metadata.create_all)...'
                .\.venv\Scripts\python.exe -c 'from db import init_db; init_db()'
            }

            $requestedPort = 8000
            $port = Get-AvailableLocalPort -StartPort $requestedPort -MaxProbe 20
            if ($port -ne $requestedPort) {
                Write-Warn "Port $requestedPort is occupied, switched to $port"
            }

            Write-Success "Starting local server on port $port..."
            Write-Info "Base URL: http://127.0.0.1:$port"
            Write-Info "API docs: http://127.0.0.1:$port/docs"
            Write-Info "Static UI: http://127.0.0.1:$port/static/verify.html"
            Write-Info ''
            Write-Info 'Press Ctrl+C to stop server'
            Write-Info ''

            .\.venv\Scripts\python.exe -m uvicorn run:app --host 127.0.0.1 --port $port --reload
        }

        'down' {
            Write-Info 'Stopping local dev servers on ports 8000-8020...'
            foreach ($p in 8000..8020) {
                Get-NetTCPConnection -LocalAddress 127.0.0.1 -LocalPort $p -ErrorAction SilentlyContinue |
                    ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }
            }
            Write-Success 'Local servers stopped'
        }

        'test' {
            Write-Info 'Running tests...'
            & '.\.venv\Scripts\Activate.ps1'
            .\.venv\Scripts\python.exe -m pytest -v
        }

        'smoke' {
            Write-Info 'Running smoke tests...'
            $env:BASE_URL = if ($env:BASE_URL) { $env:BASE_URL } else { 'http://127.0.0.1:8000' }
            pwsh -NoLogo -NoProfile scripts/smoke_local.ps1
        }

        default {
            Write-CustomError "Unknown action: $Action"
            Write-Host 'Available actions: up, down, test, smoke'
        }
    }
}

function Deploy-Docker {
    param(
        [string]$Action,
        [string]$Option
    )

    if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
        Write-CustomError 'Docker is not installed or not in PATH'
        exit 1
    }

    switch ($Action) {
        'up' {
            Write-Info 'Starting Docker containers...'

            if ($Option -eq '--build') {
                Write-Info 'Building Docker image...'
                docker build -t "${ProjectName}:${Version}" -t "${ProjectName}:latest" .
            }

            docker-compose up -d
            Start-Sleep -Seconds 3

            Write-Info 'Checking health...'
            $maxRetries = 30
            for ($i = 1; $i -le $maxRetries; $i++) {
                try {
                    $response = Invoke-WebRequest -Uri 'http://localhost:8000/health' -ErrorAction SilentlyContinue
                    if ($response.StatusCode -eq 200) {
                        Write-Success 'Application started successfully'
                        Write-Info 'API URL: http://localhost:8000'
                        Write-Info 'API docs: http://localhost:8000/docs'
                        Write-Info 'Static UI: http://localhost:8000/static/verify.html'
                        return
                    }
                }
                catch {
                }
                Write-Host '.' -NoNewline
                Start-Sleep -Seconds 1
            }

            Write-Host ''
            Write-CustomError 'Startup timeout; check logs below'
            docker-compose logs app
            exit 1
        }

        'down' {
            Write-Info 'Stopping Docker containers...'
            docker-compose down
            Write-Success 'Containers stopped'
        }

        'restart' {
            Write-Info 'Restarting Docker containers...'
            docker-compose restart
            Write-Success 'Containers restarted'
        }

        'logs' {
            Write-Info 'Tailing Docker logs...'
            docker-compose logs -f app
        }

        'shell' {
            Write-Info 'Entering container shell...'
            docker-compose exec app /bin/bash
        }

        'test' {
            Write-Info 'Running tests in container...'
            docker-compose exec app python -m pytest -v
        }

        'build' {
            Write-Info "Building image ${ProjectName}:${Version}..."
            docker build -t "${ProjectName}:${Version}" -t "${ProjectName}:latest" .
            Write-Success 'Image build completed'
        }

        default {
            Write-CustomError "Unknown action: $Action"
            Write-Host 'Available actions: up, down, restart, logs, shell, test, build'
        }
    }
}

function Deploy-K8s {
    param([string]$Action)

    if (-not (Get-Command kubectl -ErrorAction SilentlyContinue)) {
        Write-CustomError 'kubectl is not installed or not in PATH'
        exit 1
    }

    $namespace = 'bazi-api'

    switch ($Action) {
        'deploy' {
            Write-Info 'Deploying to Kubernetes...'
            kubectl create namespace $namespace --dry-run=client -o yaml | kubectl apply -f -

            if (-not (Test-Path 'k8s-deployment.yaml')) {
                Write-CustomError 'k8s-deployment.yaml not found'
                exit 1
            }

            kubectl apply -f k8s-deployment.yaml
            kubectl rollout status deployment/bazi-api -n $namespace --timeout=5m

            Write-Success 'Kubernetes deployment completed'
            kubectl get svc -n $namespace bazi-api
        }

        'undeploy' {
            Write-Warn 'Removing Kubernetes deployment...'
            if (Test-Path 'k8s-deployment.yaml') {
                kubectl delete -f k8s-deployment.yaml --ignore-not-found=true
            }
            kubectl delete namespace $namespace --ignore-not-found=true
            Write-Success 'Kubernetes resources removed'
        }

        'status' {
            Write-Info 'Showing Kubernetes status...'
            kubectl get deployment -n $namespace
            kubectl get pods -n $namespace
            kubectl get svc -n $namespace
        }

        'logs' {
            Write-Info 'Tailing pod logs...'
            kubectl logs -n $namespace -l app=bazi-api -f --tail=100
        }

        'shell' {
            Write-Info 'Entering pod shell...'
            $pod = kubectl get pod -n $namespace -l app=bazi-api -o jsonpath='{.items[0].metadata.name}'
            if ([string]::IsNullOrEmpty($pod)) {
                Write-CustomError 'No running pod found'
                exit 1
            }
            kubectl exec -it -n $namespace $pod -- /bin/bash
        }

        'port-forward' {
            Write-Info 'Port forwarding localhost:8000 -> service:80'
            Write-Info 'Visit: http://127.0.0.1:8000'
            kubectl port-forward -n $namespace svc/bazi-api 8000:80
        }

        default {
            Write-CustomError "Unknown action: $Action"
            Write-Host 'Available actions: deploy, undeploy, status, logs, shell, port-forward'
        }
    }
}

function Backup-BaziData {
    Write-Info 'Creating backup...'

    $backupFile = "backup-${Timestamp}.zip"
    $excludePatterns = @('.venv', '__pycache__', '.pytest_cache', '.ruff_cache', '.git', 'node_modules')
    $excludeArgs = $excludePatterns | ForEach-Object { "--exclude=$_" }

    Write-Info "Backup file: $backupFile"
    tar -czf $backupFile @excludeArgs .

    $fileSize = (Get-Item $backupFile).Length / 1MB
    Write-Success "Backup completed: $backupFile ($([math]::Round($fileSize, 2)) MB)"
}

function Restore-BaziData {
    param([string]$BackupFile)

    if ([string]::IsNullOrEmpty($BackupFile) -or -not (Test-Path $BackupFile)) {
        Write-CustomError "Backup file not found: $BackupFile"
        Write-Host 'Usage: .\deploy.ps1 -Environment backup -Action restore -Option <backup-file.zip>'
        exit 1
    }

    Write-Warn "Restoring backup: $BackupFile"
    Write-Host 'This will overwrite current files, continue? (Y/N): ' -NoNewline
    $confirm = Read-Host

    if ($confirm -ne 'Y' -and $confirm -ne 'y') {
        Write-Info 'Operation cancelled'
        exit 0
    }

    tar -xzf $BackupFile
    Write-Success 'Backup restored'
}

function Show-Help {
    $helpText = @"

==============================================================
  BaZi API v$Version Deployment Tool (local start port: 8000)
==============================================================

Usage:
  .\deploy.ps1 -Environment <env> -Action <action> [-Option <opt>]

Environment:
  local       Local development
  docker      Docker
  k8s         Kubernetes
  backup      Backup / restore
  help        Show help

Local actions:
  up          Start local server (auto fallback if 8000 is occupied)
  down        Stop local servers (8000-8020)
  test        Run pytest
  smoke       Run smoke tests

Docker actions:
  up          Start containers
  down        Stop containers
  restart     Restart containers
  logs        Tail logs
  shell       Enter container shell
  test        Run tests in container
  build       Build image

K8s actions:
  deploy      Deploy to cluster
  undeploy    Remove deployment
  status      Show status
  logs        Pod logs
  shell       Enter pod
  port-forward Forward service to local

Backup actions:
  backup      Create archive
  restore     Restore archive (-Option required)

Examples:
  .\deploy.ps1 -Environment local -Action up
  .\deploy.ps1 -Environment docker -Action up -Option "--build"
  .\deploy.ps1 -Environment k8s -Action deploy
  .\deploy.ps1 -Environment backup -Action backup
  .\deploy.ps1 -Environment backup -Action restore -Option backup-20260226-120000.zip

==============================================================

"@
    Write-Host $helpText
}

Write-Host ''
Write-Host "BaZi API Deployment Tool v$Version" -ForegroundColor Cyan
Write-Host ''

if ($Environment -eq 'help' -or $Environment -eq '' -or $Action -eq 'help') {
    Show-Help
    exit 0
}

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
                Write-CustomError "Unknown backup action: $Action"
                Write-Host 'Available actions: backup, restore'
                exit 1
            }
        }
        default {
            Write-CustomError "Unknown environment: $Environment"
            Show-Help
            exit 1
        }
    }
}
catch {
    Write-CustomError "Execution failed: $_"
    Write-Host "Error detail: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

Write-Host ''
exit 0
