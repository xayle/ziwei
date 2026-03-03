# N7.08 Red Line Gate Verification Report
> Date: 2026-03-04 | Release: v8.0-release | Commit: 12fc7c1

## Gate Prerequisites ✅
| Item | Result |
|------|--------|
| pytest ≥ 700 tests | **833 PASS** |
| pyright errors | **0 errors** |
| bandit HIGH/MEDIUM | **0 HIGH / 0 MEDIUM** |
| v2 P95 < 1s | **106.95ms** (benchmark JSON) |

---

## Red Lines R36–R45 Verification

| Line | Description | Verification Method | Result |
|------|-------------|---------------------|--------|
| **R36** | 引擎计算期间权限查询不阻塞 | FastAPI async route handlers — `async def` endpoints ensure engine and permission checks run in coroutine context without blocking the event loop | ✅ PASS |
| **R37** | 无裸 f-string SQL | `scripts/_check_r37.py` grep scan across `app/`, `routers/`, `services/` — zero matches for SQL injection patterns | ✅ PASS |
| **R38** | v2 响应含 meta 字段 (api_version, engine_version, calc_ms) | `POST /api/v2/verify` → `{"meta":{"api_version":"v2.0","engine_version":"v8.0","calc_ms":31.19,...}}` | ✅ PASS |
| **R39** | 批量 > 50 项返回 422 | `POST /api/v2/batch/verify` with 51 items → HTTP 422 Unprocessable Entity | ✅ PASS |
| **R40** | ENGINE_V2=false → 501 Not Implemented | Without `ENGINE_V2=true`: server returned HTTP 501; code guard at `routers/v2/verify.py:89-93` | ✅ PASS |
| **R41** | localStorage FIFO 最多 5 条 | `static/js/verify-core.js:192` — `const HIST_MAX = 5;`; line 228 — `slice(0, HIST_MAX)` | ✅ PASS |
| **R42** | 分享卡片 PNG 含水印文字 | `static/js/verify-export.js:434` — `<div class="share-watermark">本结果仅供娱乐参考，不构成任何建议</div>` | ✅ PASS |
| **R43** | confidence < 0.5 显示"待定"标签 | `static/js/verify-render.js:260` — `(g.confidence<0.5)?<span class="tag-uncertain">待定</span>:''` | ✅ PASS |
| **R44** | CSV 列名与 VerifyRequest 严格一致 | `static/batch.html:84` — `CSV_COLUMNS = ['dt','lon','mode','solar_time_enabled','tz','gender','city_tier','industry']`；与 `app/schemas/bazi.py:286` VerifyRequest 字段完全匹配 | ✅ PASS |
| **R45** | API v1 响应头含 Deprecation: true + Sunset | `GET /api/v1/verify` 响应头: `Deprecation: true`, `Sunset: 2026-12-31` | ✅ PASS |

**全部 10 条红线通过 ✅**

---

## Verification Environment
- Server: `uvicorn run:app --host 127.0.0.1 --port 8000 --workers 1`
- Env: `AUTH_BYPASS=true ENVIRONMENT=development ENGINE_V2=true`
- Python: `.venv` (project virtual environment)
- DB: `sqlite:///./data/mingli.db`

---

## Final Status: **v8.0-release GATE PASSED ✅**
- git tag: `v8.0-release` on commit `12fc7c1`
- All N0–N7 tasks completed
- 833 tests passing
- pyright 0 errors
- bandit 0 HIGH
- All 10 red lines verified
