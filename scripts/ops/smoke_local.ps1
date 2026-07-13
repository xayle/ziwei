#!/usr/bin/env pwsh
# Local smoke with request_id + warnings checks; runs all cases and summarizes failures.
$ErrorActionPreference = "Continue"

if (-not $env:BASE_URL) { $env:BASE_URL = "http://127.0.0.1:8000" }
$BaseUrl = $env:BASE_URL
$failures = New-Object System.Collections.Generic.List[string]

function Invoke-SmokeCase {
  param(
    [string]$Name,
    [int]$ExpectedStatus,
    [string]$Validator,
    [string[]]$CurlArgs,
    [string]$InputReqId = ""
  )
  $bodyFile = [IO.Path]::GetTempFileName()
  $hdrFile = [IO.Path]::GetTempFileName()
  $status = & curl.exe @CurlArgs -s -o $bodyFile -D $hdrFile -w '%{http_code}'
  if ($LASTEXITCODE -ne 0) {
    $failures.Add(('{0}: curl exit {1}' -f $Name, $LASTEXITCODE))
    return
  }
  if ($status -ne $ExpectedStatus) {
    $failures.Add(('{0}: http {1} (want {2})' -f $Name, $status, $ExpectedStatus))
    return
  }
  if ($Validator -eq "none") { return }

  $py = @'
import json, sys
path, validator, req_in = sys.argv[1:4]
with open(path, encoding="utf-8") as f:
  data = json.load(f)
validation = data.get("validation") or {}
warnings = data.get("warnings") or validation.get("warnings")
reqid = data.get("request_id")

def normalize(ws):
    out = []
    for w in ws or []:
        if isinstance(w, dict):
            msg = w.get("message") or w.get("code") or str(w)
            out.append(str(msg))
        else:
            out.append(str(w))
    return out

norm_warnings = normalize(warnings)

def fail(msg: str) -> None:
    print(msg)
    sys.exit(1)

def has_warn(prefix: str) -> bool:
    return any(w.startswith(prefix) for w in norm_warnings)

if validator == "generated":
    if not isinstance(reqid, str) or not reqid:
        fail("missing request_id")
    if warnings:
        fail(f"unexpected warnings: {warnings}")
elif validator == "echo":
    if reqid != req_in:
        fail(f"request_id not echoed: {reqid} != {req_in}")
    if warnings:
        fail(f"unexpected warnings: {warnings}")
elif validator == "invalid":
  if not warnings:
    fail("expected warnings for invalid request_id")
  if not has_warn("request_id_invalid_chars:"):
    fail(f"missing request_id_invalid_chars warning: {warnings}")
  if reqid == req_in:
    fail("request_id should be replaced")
elif validator == "truncated":
  if not warnings:
    fail("expected warnings for long request_id")
  if not has_warn("request_id_truncated:"):
    fail(f"missing request_id_truncated warning: {warnings}")
  if not isinstance(reqid, str) or len(reqid) != 128:
    fail(f"request_id not truncated to 128 (len={len(reqid) if isinstance(reqid, str) else 'n/a'})")
elif validator == "tz_mismatch":
  if not warnings:
    fail("expected tz_mismatch warning")
  if not has_warn("tz_mismatch:"):
    fail(f"warnings missing tz_mismatch: {warnings}")
'@
  $py | python - "$bodyFile" "$Validator" "$InputReqId"
  if ($LASTEXITCODE -ne 0) {
    $body = Get-Content -Raw $bodyFile
    $failures.Add(('{0}: {1}' -f $Name, $body))
  }
}

Write-Host "BASE_URL=$BaseUrl"

Write-Host "== /health =="
Invoke-SmokeCase -Name "health" -ExpectedStatus 200 -Validator "none" -CurlArgs @("$BaseUrl/health")

Write-Host "== /api/v1/verify (no X-Request-Id; should generate) =="
Invoke-SmokeCase -Name "verify_generate" -ExpectedStatus 200 -Validator "generated" -CurlArgs @(
  "-X","POST","$BaseUrl/api/v1/verify",
  "-H","Content-Type: application/json",
  "-d",'{"dt":"2026-02-24T12:00:00","lon":121.4737,"tz":"Asia/Shanghai"}'
)

Write-Host "== /api/v1/verify (valid X-Request-Id; should echo) =="
Invoke-SmokeCase -Name "verify_echo" -ExpectedStatus 200 -Validator "echo" -InputReqId "test_req-123.ABC" -CurlArgs @(
  "-X","POST","$BaseUrl/api/v1/verify",
  "-H","Content-Type: application/json",
  "-H","X-Request-Id: test_req-123.ABC",
  "-d",'{"dt":"2026-02-24T12:00:00","lon":121.4737,"tz":"Asia/Shanghai"}'
)

Write-Host "== /api/v1/verify (invalid X-Request-Id; replace + warnings) =="
Invoke-SmokeCase -Name "verify_invalid" -ExpectedStatus 200 -Validator "invalid" -InputReqId "bad id !!" -CurlArgs @(
  "-X","POST","$BaseUrl/api/v1/verify",
  "-H","Content-Type: application/json",
  "-H","X-Request-Id: bad id !!",
  "-d",'{"dt":"2026-02-24T12:00:00","lon":121.4737,"tz":"Asia/Shanghai"}'
)

Write-Host "== /api/v1/verify (too long X-Request-Id; truncate + warnings) =="
$LongId = ("a" * 200)
Invoke-SmokeCase -Name "verify_long" -ExpectedStatus 200 -Validator "truncated" -InputReqId $LongId -CurlArgs @(
  "-X","POST","$BaseUrl/api/v1/verify",
  "-H","Content-Type: application/json",
  "-H","X-Request-Id: $LongId",
  "-d",'{"dt":"2026-02-24T12:00:00","lon":121.4737,"tz":"Asia/Shanghai"}'
)

Write-Host "== /api/v1/verify (aware dt + tz mismatch; expect tz_mismatch warning) =="
Invoke-SmokeCase -Name "verify_tz_mismatch" -ExpectedStatus 200 -Validator "tz_mismatch" -CurlArgs @(
  "-X","POST","$BaseUrl/api/v1/verify",
  "-H","Content-Type: application/json",
  "-d",'{"dt":"2026-02-24T12:00:00+09:00","lon":121.4737,"tz":"Asia/Shanghai"}'
)

if ($failures.Count -eq 0) {
  Write-Host "All checks passed."
  exit 0
} else {
  Write-Host "Failures:"
  $failures | ForEach-Object { Write-Host "  - $_" }
  exit 1
}
