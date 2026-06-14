# Core constants for v8.0
API_VERSION = "v1"
RULE_VERSION = "v8.0"

# 天干地支标准序（O8 / test_property_bazi.py 用于合法性断言）
STEMS: list[str] = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
BRANCHES: list[str] = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
DEFAULT_LON = 120.0
SUPPORTED_YEAR_RANGE = (1900, 2101)
SHICHEN_THRESHOLD_MIN = 15
JIEQI_THRESHOLD_MIN = 60
# Global lon bounds
MIN_LON, MAX_LON = -180.0, 180.0
# China reference bounds (for warnings only)
CN_MIN_LON, CN_MAX_LON = 73.0, 135.0
MIN_LAT, MAX_LAT = 3.0, 54.0

# W4: 算法模块版本追踪常量
# 每个模块升级时同步更新对应版本号，便于排盘结果追溯
ENGINE_VERSION = "8.0.0"  # 整体引擎版本
BAZI_ENGINE_VERSION = "8.0.0"  # 八字引擎版本
ZIWEI_ENGINE_VERSION = "8.0.0"  # 紫微引擎版本
YONGSHEN_MODULE_VERSION = "3.1.0"  # 用神算法版本
GEJU_MODULE_VERSION = "2.1.0"  # 格局算法版本
DAYUN_MODULE_VERSION = "2.0.0"  # 大运算法版本
WUXING_MODULE_VERSION = "1.5.0"  # 五行算法版本
FLYING_MODULE_VERSION = "1.2.0"  # 飞星算法版本

# W8: SLO 基线阈值（毫秒）
SLO_WARN_MS = 500  # p95 超过此值记录 WARNING
SLO_CRIT_MS = 1500  # p95 超过此值记录 CRITICAL

# 0.23 / P0-12: 差异原因 11 个合法 Key（供 UI 按枚举映射，不展示 raw reason）
VALID_REASON_CODES: frozenset[str] = frozenset(
    {
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
    }
)
