# Single-process Playwright browser install (avoids __dirlock races on Windows)
$browserRoot = Join-Path $env:LOCALAPPDATA "ms-playwright"
$lock = Join-Path $browserRoot "__dirlock"

if (Test-Path $lock) {
  $age = (Get-Date) - (Get-Item $lock).LastWriteTime
  if ($age.TotalMinutes -lt 10) {
    Write-Host "Playwright install lock is fresh (<10m). Another install may be running — wait and retry."
    exit 1
  }
  Write-Host "Removing stale Playwright lock ($([int]$age.TotalMinutes)m old)..."
  Remove-Item -Recurse -Force $lock -ErrorAction SilentlyContinue
  Start-Sleep -Seconds 2
}

Set-Location $PSScriptRoot\..
npx playwright install chromium
if ($LASTEXITCODE -ne 0) {
  # Download may have succeeded but lock finalization failed — verify binary
  $chrome = Join-Path $browserRoot "chromium-1161\chrome-win\chrome.exe"
  if (Test-Path $chrome) {
    Write-Host "Install reported error but Chromium binary exists — treating as ready."
    exit 0
  }
  Write-Host "Fallback: python -m playwright install chromium (for scripts/capture_design_targets.py)"
  exit $LASTEXITCODE
}
Write-Host "Playwright chromium ready."
