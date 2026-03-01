# Core constants for v7.0
API_VERSION = "v1"
RULE_VERSION = "v7.0"
DEFAULT_LON = 120.0
SUPPORTED_YEAR_RANGE = (1900, 2101)
SHICHEN_THRESHOLD_MIN = 15
JIEQI_THRESHOLD_MIN = 60
# Global lon bounds
MIN_LON, MAX_LON = -180.0, 180.0
# China reference bounds (for warnings only)
CN_MIN_LON, CN_MAX_LON = 73.0, 135.0
MIN_LAT, MAX_LAT = 3.0, 54.0

# 0.23 / P0-12: 差异原因 11 个合法 Key（供 UI 按枚举映射，不展示 raw reason）
VALID_REASON_CODES: frozenset[str] = frozenset({
    "sxtwl_unavailable_single_mode",
    "jieqi_unavailable_single_mode",
    "near_shichen_boundary",
    "near_jieqi_boundary",
    "diff_hour",
    "diff_month",
    "diff_day",
    "diff_year",
    "longitude_fallback_120e",
    "input_out_of_range_year",
    "invalid_lon_format",
})

