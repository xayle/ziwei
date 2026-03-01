#!/usr/bin/env bash
# Local smoke for /health and /api/v1/verify with request_id + warnings checks.
# Runs all cases, summarizes failures, exits non-zero on any failure.
set -u -o pipefail

BASE_URL="${BASE_URL:-http://127.0.0.1:8000}"
failures=()

run_case() {
  local name="$1" exp_status="$2" validator="$3"
  shift 3
  local body tmp_hdr
  body="$(mktemp)"
  tmp_hdr="$(mktemp)"
  local status
  status="$(curl -s -o "$body" -D "$tmp_hdr" -w "%{http_code}" "$@")" || status=$?
  if [[ "$status" != "$exp_status" ]]; then
    failures+=("$name: http $status (want $exp_status)")
    return
  fi
  if [[ "$validator" == "none" ]]; then
    return
  fi

  python - "$body" "$validator" "${REQID_INPUT:-}" <<'PY'
import json, sys
path, validator, req_in = sys.argv[1:4]
with open(path, encoding="utf-8") as f:
  data = json.load(f)
validation = data.get("validation") or {}
warnings = data.get("warnings") or validation.get("warnings")
reqid = data.get("request_id")

def fail(msg: str) -> None:
    print(msg)
    sys.exit(1)

def has_warn(ws, prefix: str) -> bool:
  return any(str(w).startswith(prefix) for w in ws or [])

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
  if not has_warn(warnings, "request_id_invalid_chars:"):
    fail(f"missing request_id_invalid_chars warning: {warnings}")
  if reqid == req_in:
    fail("request_id should be replaced")
elif validator == "truncated":
  if not warnings:
    fail("expected warnings for long request_id")
  if not has_warn(warnings, "request_id_truncated:"):
    fail(f"missing request_id_truncated warning: {warnings}")
  if not isinstance(reqid, str) or len(reqid) != 128:
    fail(f"request_id not truncated to 128 (len={len(reqid) if isinstance(reqid, str) else 'n/a'})")
elif validator == "tz_mismatch":
  if not warnings:
    fail("expected tz_mismatch warning")
  if not has_warn(warnings, "tz_mismatch:"):
    fail(f"warnings missing tz_mismatch: {warnings}")
PY
  local rc=$?
  if [[ $rc -ne 0 ]]; then
    failures+=("$name: $(cat "$body")")
  fi
}

echo "BASE_URL=$BASE_URL"

echo "== /health =="
run_case "health" "200" "none" "$BASE_URL/health"

echo "== /api/v1/verify (no X-Request-Id; should generate) =="
run_case "verify_generate" "200" "generated" \
  -X POST "$BASE_URL/api/v1/verify" \
  -H "Content-Type: application/json" \
  -d '{"dt":"2026-02-24T12:00:00","lon":121.4737,"tz":"Asia/Shanghai"}'

echo "== /api/v1/verify (valid X-Request-Id; should echo) =="
REQID_INPUT="test_req-123.ABC" run_case "verify_echo" "200" "echo" \
  -X POST "$BASE_URL/api/v1/verify" \
  -H "Content-Type: application/json" \
  -H "X-Request-Id: test_req-123.ABC" \
  -d '{"dt":"2026-02-24T12:00:00","lon":121.4737,"tz":"Asia/Shanghai"}'

echo "== /api/v1/verify (invalid X-Request-Id; replace + warnings) =="
REQID_INPUT="bad id !!" run_case "verify_invalid" "200" "invalid" \
  -X POST "$BASE_URL/api/v1/verify" \
  -H "Content-Type: application/json" \
  -H "X-Request-Id: bad id !!" \
  -d '{"dt":"2026-02-24T12:00:00","lon":121.4737,"tz":"Asia/Shanghai"}'

echo "== /api/v1/verify (too long X-Request-Id; truncate + warnings) =="
LONG_ID="$(python - <<'PY'
print("a"*200)
PY
)"
REQID_INPUT="$LONG_ID" run_case "verify_long" "200" "truncated" \
  -X POST "$BASE_URL/api/v1/verify" \
  -H "Content-Type: application/json" \
  -H "X-Request-Id: $LONG_ID" \
  -d '{"dt":"2026-02-24T12:00:00","lon":121.4737,"tz":"Asia/Shanghai"}'

echo "== /api/v1/verify (aware dt + tz mismatch; expect tz_mismatch warning) =="
run_case "verify_tz_mismatch" "200" "tz_mismatch" \
  -X POST "$BASE_URL/api/v1/verify" \
  -H "Content-Type: application/json" \
  -d '{"dt":"2026-02-24T12:00:00+09:00","lon":121.4737,"tz":"Asia/Shanghai"}'

echo
if [[ ${#failures[@]} -eq 0 ]]; then
  echo "All checks passed."
  exit 0
else
  echo "Failures:"
  printf '  - %s\n' "${failures[@]}"
  exit 1
fi
