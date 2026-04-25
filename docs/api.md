# API Contract (v5.1.0)

## Overview
- Base URL (local dev, default): `http://127.0.0.1:8000`
- Example variable: `BASE_URL=http://127.0.0.1:8000`
- If you start API via `start-local.ps1` or `deploy.ps1 -Environment local -Action up`, port may auto-fallback when `8000` is occupied. Use the actual startup log port.
- Health: `GET /health` (versions, backend availability, clock, thresholds)
- Main: `POST /api/v1/verify`
- Full payload: `POST /api/v1/bazi/full`
- Primary UI (SPA): `${BASE_URL}/static/app/workbench`（例如 `http://127.0.0.1:8000/static/app/workbench`）
- Compatibility entry: `${BASE_URL}/static/index.html`（例如 `http://127.0.0.1:8000/static/index.html`）— 会优先跳转到 `${BASE_URL}/static/app/workbench`，若新版资源不存在则回退到 legacy `ziwei.html`
- Compatibility alias (bazi): `${BASE_URL}/bazi` — 会优先跳转到 `${BASE_URL}/static/app/bazi`，若新版资源不存在则回退到 legacy `bazi.html`
- Compatibility alias (admin): `${BASE_URL}/admin` — 会优先跳转到 `${BASE_URL}/static/app/admin`，若新版资源不存在则回退到 legacy `admin.html`
- Compatibility pages: `/static/bazi.html`、`/static/admin.html`（默认优先跳往 SPA，可通过 `?legacy=1` 停留旧版）
- Retained legacy pages: `/static/ziwei.html`、`/static/batch.html`

---

## POST /api/v1/verify

### Purpose
Compute BaZi pillars, risk flags, and validation, honoring requested `mode` (`dual`/`single`) with explicit fallback reported via `mode_effective`.

### Request (JSON)
Content-Type: `application/json`

**Fields (VerifyRequest)**
- `dt` (datetime, required): ISO-8601; may include offset (e.g. `2026-02-24T12:34:56+08:00`) or be naive (`2026-02-24T12:34:56`, interpreted with `tz`).
- `tz` (string, optional, default `"Asia/Shanghai"`): Used only when `dt` is naive.
- `lon` (number, required): Longitude in degrees, must be within **[-180, 180]**; CN inputs outside [70, 140] emit a warning.
- `mode` (string, optional, default `"dual"`): One of `"dual" | "single"`.
- `solar_time_enabled` (boolean, optional, default `false`): Apply solar-time adjustment when true.

**Example**
```json
{
  "dt": "2026-02-24T12:34:56",
  "tz": "Asia/Shanghai",
  "lon": 121.4737,
  "mode": "dual",
  "solar_time_enabled": false
}
```

### Response (JSON)
Stable schema (VerifyResponse):
- `api_version` (string)
- `rule_version` (string)
- `request_id` (string): Correlation id; echoes `X-Request-Id` header or generated UUID.
- `backend` (object)
  - `primary` (string)
  - `secondary` (string | null)
  - `sxtwl_available` (boolean)
  - `cnlunar_available` (boolean)
  - Versions are exposed via `/health` (this payload omits them for brevity).
- `mode_requested` ("dual" | "single")
- `mode_effective` ("dual" | "single")
- `dt_input` (string): Parsed `dt` re-serialized via `.isoformat()` (not the raw input string).
- `dt_effective_utc8` (string): Datetime normalized to Asia/Shanghai (UTC+8), after applying the assumed timezone for naive input.
- `tz` (string): Echo of requested `tz` (default Asia/Shanghai); only used to interpret naive `dt`.
- `solar_time_offset_minutes` (number): Always a number; `0.0` when `solar_time_enabled=false` (no adjustment applied), otherwise the applied solar correction.
- `pillars_primary` (object):
  - `year|month|day|hour`: `{ stem, branch, ganzhi? }`
- `pillars_secondary` (object | null): Same shape; null when `mode_effective="single"`.
- `risk_flags` (object):
  - `near_shichen_boundary` (boolean)
  - `near_jieqi_boundary` (boolean)
  - `jieqi_boundary_status` ("ok" | "unavailable"): `ok` means jieqi context available and near/offset computed; `unavailable` means jieqi context missing (minutes may be null, near_jieqi_boundary should be false).
  - `minutes_to_shichen_boundary` (number | null)
  - `minutes_to_jieqi_boundary` (number | null)
- `validation` (object):
  - `level` ("L0" | "L1" | "L2" | "L3")
  - `mode` ("dual" | "single")
  - `recommended` (string): `"beijing_time" | "solar_time" | "none"` (none when boundary risk blocks interpretation).
  - `interpretation_enabled` (boolean)
  - `reasons` (array of string)
  - `diff_fields` (array of "year" | "month" | "day" | "hour")
  - `boundary_risk_shichen` / `boundary_risk_jieqi` (boolean): true when close to boundary per thresholds.
  - `risk_flags` (same shape as above)
  - `warnings` (array of string): non-blocking notices using `code: key=value...` format (e.g., `tz_mismatch: dt_offset=+09:00 tz=Asia/Shanghai action=tz_ignored_for_aware_dt`, `request_id_invalid_chars: action=replaced_with_uuid`, `request_id_truncated: max_len=128`).
- Optional structured add-ons for front-end templates (omitted if unavailable):
  - `wealth`: `{ wealth_range?, wealth_score?, industry_tags?, risk_hint?, note? }`
  - `marriage`: `{ marriage_flags?, love_window?, child_hint?, risk_hint?, note? }`
  - `social`: `{ taohua_hit?, relation_conflict?, taohua_year_hit?, social_hint? }`
  - `dayun`: `{ method, boundary, items[] }`, where items may include `ten_god`, `wealth_hint`, `health_hint`, `love_hint`, `child_hint`, `refs`.

**Shape example**
```json
{
  "api_version": "v1",
  "rule_version": "v5.3",
  "backend": {
    "primary": "sxtwl",
    "secondary": "cnlunar",
    "sxtwl_available": true,
    "cnlunar_available": true
  },
  "mode_requested": "dual",
  "mode_effective": "dual",
  "dt_input": "2026-02-24T12:34:56+08:00",
  "dt_effective_utc8": "2026-02-24T12:34:56+08:00",
  "tz": "Asia/Shanghai",
  "solar_time_offset_minutes": 0.0,
  "pillars_primary": {
    "year": { "stem": "甲", "branch": "子", "ganzhi": "甲子" },
    "month": { "stem": "乙", "branch": "丑", "ganzhi": "乙丑" },
    "day": { "stem": "丙", "branch": "寅", "ganzhi": "丙寅" },
    "hour": { "stem": "丁", "branch": "卯", "ganzhi": "丁卯" }
  },
  "pillars_secondary": null,
  "risk_flags": {
    "near_shichen_boundary": false,
    "near_jieqi_boundary": false,
    "jieqi_boundary_status": "ok",
    "minutes_to_shichen_boundary": 26.0,
    "minutes_to_jieqi_boundary": 13524.7
  },
  "validation": {
    "level": "L1",
    "mode": "dual",
    "recommended": "beijing_time",
    "interpretation_enabled": false,
    "reasons": ["sxtwl_unavailable_single_mode"],
    "diff_fields": [],
    "risk_flags": {
      "near_shichen_boundary": false,
      "near_jieqi_boundary": false,
      "jieqi_boundary_status": "ok",
      "minutes_to_shichen_boundary": 26.0,
      "minutes_to_jieqi_boundary": 13524.7
    }
  }
}
```

### Errors
- **422 Unprocessable Entity**: Pydantic validation failures (e.g., `lon` out of range, invalid `dt`). Detail includes field path.
- **500**: Unexpected server errors (propagated message in `detail`).

### Conventions
- Prefer timezone-aware `dt` with offset. If `dt` is naive, server applies `tz` (default Asia/Shanghai).
- Clients should honor `mode_effective` (may downgrade from requested `dual`).

---

## POST /api/v1/bazi/full

### Purpose
Compute full BaZi output: pillars, ten_gods, liunian, dayun (12-jie anchor, days/3 ceil), wuxing, strength tiers, yongshen. Includes raw trace for debugging (append-only, not a stable contract).

### Request (JSON)
Content-Type: `application/json`

**Fields (BaZiFullRequest)**
- `dt` (datetime, required), `tz` (string, optional, default "Asia/Shanghai"), `lon` (number, required within **[-180, 180]**; CN inputs outside [70, 140] emit a warning).
- `solar_time_enabled` (boolean, optional, default `false`).
- Methods (all defaulted and stable for v5.0.0):
  - `day_boundary_rule` (`"zi_initial"` default)
  - `solar_time_rule` (`"longitude_only"` default)
  - `dayun_method` (`"sxtwl_next_jieqi_div3"` default, uses next jieqi as anchor, ceil(days/3)).

**Example**: see [samples/bazi_full.json](samples/bazi_full.json) for a full payload/response pair.

### Response (JSON)
Stable fields (BaZiFullResponse):
- `api_version`, `rule_version`, `request_id`, `methods` (echoes effective methods), `mode_effective`.
- `pillars` (year/month/day/hour with ganzhi), `ten_gods`, `liunian` (yearly), `dayun` (decadal, with `sequence_start` and raw anchor info), `wuxing`, `strength`, `yongshen`.
- `warnings` (array of string, top-level for bazi_full). `validation.warnings` is not used here.
- `raw` (append-only debug trace): contains `day_boundary_crossed` (means dt is in the zi_initial window 23:00-00:59, not that day pillar changed), `birth_to_jieqi_days`, `anchor_jieqi`, `anchor_jieqi_dt`, `sequence_start`, and other traces. Fields like `computed_months_before_rounding` or `rounding_applied` are not emitted in v5.0.0 (planned/optional later). Clients should not depend on raw stability beyond additive growth.

**Examples**
- [samples/bazi_full.json](samples/bazi_full.json): typical response.
- [samples/bazi_full_dayun_anchor.json](samples/bazi_full_dayun_anchor.json): demonstrates raw dayun anchor and boundary flag.
- [samples/verify.json](samples/verify.json): verify response with warnings and lon bounds.

---

## GET /health

Returns lightweight service status and build context.

**Fields**
- `status` ("ok")
- `api_version`, `rule_version`
- `sxtwl_available`, `sxtwl_version`
- `cnlunar_available`, `cnlunar_version`
- `tz` ("Asia/Shanghai")
- `now_utc8` (ISO string)
- `supported_year_range` (tuple)
- `thresholds`: `{ shichen_minutes, jieqi_minutes, jieqi_set }`

Example:
```json
{
  "status": "ok",
  "api_version": "v1",
  "rule_version": "v5.3",
  "sxtwl_available": true,
  "sxtwl_version": "2.0.7",
  "cnlunar_available": true,
  "cnlunar_version": "0.2.4",
  "tz": "Asia/Shanghai",
  "now_utc8": "2026-02-25T10:00:00+08:00",
  "supported_year_range": [1900, 2101],
  "thresholds": {
    "shichen_minutes": 15,
    "jieqi_minutes": 60,
    "jieqi_set": "12jie"
  }
}
```
