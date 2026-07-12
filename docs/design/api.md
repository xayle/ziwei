# API Contract (v5.1.0)

## Overview
- Base URL (local dev, default): `http://127.0.0.1:8000`
- Example variable: `BASE_URL=http://127.0.0.1:8000`
- If you start API via `start-local.ps1` or `deploy.ps1 -Environment local -Action up`, port may auto-fallback when `8000` is occupied. Use the actual startup log port.
- Health: `GET /health` (versions, backend availability, clock, thresholds)
- Main: `POST /api/v1/verify`
- Full payload: `POST /api/v1/bazi/full`
- Primary UI (SPA): `${BASE_URL}/static/app/cases`（例如 `http://127.0.0.1:8000/static/app/cases`）
- Compatibility entry: `${BASE_URL}/static/index.html`（例如 `http://127.0.0.1:8000/static/index.html`）— 会优先跳转到 `${BASE_URL}/static/app/cases`，若新版资源不存在则回退到 legacy `ziwei.html`
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
Full BaZi analysis: pillars, ten gods, dayun, liunian, wuxing/strength/yongshen (unified `services/bazi_engine/`), pillar details, optional liuri/liushi.

Schema version: **`bazi_full@5.1`**

### Request (JSON)
Content-Type: `application/json`

**Fields (BaziFullRequest)**
- `dt` (datetime, required): ISO-8601; naive interpreted with `tz`.
- `tz` (string, optional, default `"Asia/Shanghai"`).
- `lon` (number, required): **[-180, 180]**; CN outside [70, 140] emits warning.
- `mode` (`"dual"` | `"single"`, default `"dual"`).
- `solar_time_enabled` (boolean, default `false`): Use `services/bazi_engine/solar_time_v2.py` when true.
- `gender` (`"male"` | `"female"` | null, optional): Dayun direction (阳年男顺女逆).
- `city_tier` (`"一线"` | `"新一线"` | `"其余"` | null, optional): Wealth estimate multiplier (M3.03).
- `industry` (string | null, optional): Wealth estimate industry keyword.
- `liunian_years` (int[] | null, optional): Year offsets for liunian list, default `[-2, 2]`.
- `target_date` (datetime | null, optional): When set, response includes `liuri_liushi`.
- `target_hour` (int 0–23 | null, optional): Hour for liushi; used with `target_date`.

**Example**
```json
{
  "dt": "1990-07-17T12:20:00",
  "tz": "Asia/Shanghai",
  "lon": 121.47,
  "mode": "dual",
  "solar_time_enabled": false,
  "gender": "female",
  "target_date": "1900-01-01T12:00:00",
  "target_hour": 14
}
```

### Response (JSON) — stable highlights
- Meta: `api_version`, `rule_version`, `schema_version`, `request_id`, `warnings`, `methods`.
- Core: `pillars_primary`, `pillars_secondary`, `ten_gods`, `wuxing_score`, `wuxing_breakdown`, `day_master_strength`, `yongshen`.
- Flow: `dayun` (includes `start_age_days`, `transition_hint`, items with `self_seat`, `wealth_range`), `liunian`.
- Details: `pillar_details` (per-pillar `xingyun`, `self_seat`, `kongwang`, `shensha`).
- Relations: `dizhi_relations`, `tiangan_clashes`, `kongwang`, `bazi_structural_summary.adjustment_summary` (调候).
- Optional: `liuri_liushi` when `target_date` provided — `{ date, day_ganzhi, hour_ganzhi, day_ten_god, hour_ten_god, missing_fields[] }`.
- M2 modules (when enrich path runs): `geju`, `wealth_analysis`, `career`, `health`, etc.
- Debug: `raw` (append-only, not a stability guarantee).

See [samples/bazi_full.json](samples/bazi_full.json), [bazi ENGINE-METHOD-REGISTRY](bazi/ENGINE-METHOD-REGISTRY.md).

### ENGINE_V2 flag
Environment variable `ENGINE_V2=true` routes to `_calculate_v2`, which uses **`services/bazi_engine/pillars.py`** as the canonical four-pillars layer (sxtwl/cnlunar + `solar_time_v2`). Analysis modules are the same as v1. Pillar output should match v1; the flag selects the v2 code path and sets `engine_version="v2"`.

Regenerate OpenAPI snapshot: `python scripts/export_openapi.py`

---

## POST /api/v1/ziwei/full

### Purpose
Compute full Ziwei chart: palaces, main/aux stars, sihua, dayun, liunian, liuyue, flying, forecast, patterns.

### Request (JSON)
**Fields (ZiweiRequest)** — selected
- Birth: `year`, `month`, `day`, `hour`, `minute`, `gender` (`男`/`女`).
- Optional: `liunian_year`, `longitude` (true solar time), `template_version` (`simple`|`standard`|`pro`).
- Method params (partial list exposed on API): `late_zishi`, `sihua_stem_indices`, `leap_month_method`, `kuiyue_method`, `tianma_method`, `tiankong_method`, `brightness_method`, `jiukong_method`, `tianshang_method`, `mingzhu_method`, `liunian_sihua_method`, `changsheng_method`.

> Engine-only params (defaults apply; not yet on HTTP request): `wenchang_method`, `youbi_method`, `liunian_life_method`, `liuyue_method`, `xiaoxian_start_method`, `flow_lunar_day`, `flow_liuyue_month`, `flow_hour_branch`. See [ziwei ENGINE-METHOD-REGISTRY](ziwei/ENGINE-METHOD-REGISTRY.md).

### Response (JSON) — stable highlights
- `lunar`, `life_palace_gz`, `body_palace_gz`, `wuxing_ju`, `palaces[]`, `dayun`, `liunian`, `liuyue[]`.
- `missing_fields`, `engine_warnings` (engine-level gaps, e.g. failed solar correction).
- `liuri_liushi` (optional; populated when engine computed with `flow_*` params).
- `patterns`, `forecast`, `flying` (omitted or reduced when `template_version=simple`).

---

## POST /api/v1/bazi/full (legacy section below retained for raw trace)

### Raw trace (append-only)
`raw` contains `day_boundary_crossed`, jieqi anchor, dayun direction basis. Clients should not depend on raw field stability beyond additive growth.

**Examples**
- [samples/bazi_full.json](samples/bazi_full.json): typical response.
- [samples/bazi_full_dayun_anchor.json](samples/bazi_full_dayun_anchor.json): dayun anchor demo.
- [samples/verify.json](samples/verify.json): verify response.

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
