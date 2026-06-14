"""
西方占星出生盘计算服务 — 纯 Python 天文算法实现
基于 Jean Meeus《Astronomical Algorithms》2nd ed.

精度估计：
  太阳: ±0.01°   月亮: ±1°
  内行星（水/金/火）: ±1-2°
  外行星（木/土/天/海）: ±0.5°
  上升/中天: ±0.1°
  （精度均足以判断行星所在星座，各星座宽 30°）
"""

from __future__ import annotations

from datetime import UTC, datetime
import math
from typing import Any


# ── 辅助 ─────────────────────────────────────────────────────
def _r(d: float) -> float:
    return d * math.pi / 180.0


def _d(r: float) -> float:
    return r * 180.0 / math.pi


def _n(d: float) -> float:
    return d % 360.0  # 归一化到 [0, 360)


# ── 黄道十二宫 ────────────────────────────────────────────────
# (中文名, 英文名, Unicode符号, 元素, 模式)
SIGNS: list[tuple[str, str, str, str, str]] = [
    ("白羊", "Aries", "♈", "fire", "cardinal"),
    ("金牛", "Taurus", "♉", "earth", "fixed"),
    ("双子", "Gemini", "♊", "air", "mutable"),
    ("巨蟹", "Cancer", "♋", "water", "cardinal"),
    ("狮子", "Leo", "♌", "fire", "fixed"),
    ("处女", "Virgo", "♍", "earth", "mutable"),
    ("天秤", "Libra", "♎", "air", "cardinal"),
    ("天蝎", "Scorpio", "♏", "water", "fixed"),
    ("射手", "Sagittarius", "♐", "fire", "mutable"),
    ("摩羯", "Capricorn", "♑", "earth", "cardinal"),
    ("水瓶", "Aquarius", "♒", "air", "fixed"),
    ("双鱼", "Pisces", "♓", "water", "mutable"),
]

_ELEM_CN = {"fire": "火象", "earth": "土象", "air": "风象", "water": "水象"}
_MODE_CN = {"cardinal": "本位", "fixed": "固定", "mutable": "变动"}


def _sign_info(lon: float) -> dict[str, Any]:
    """给定黄经（度）返回星座信息字典"""
    idx = int(_n(lon) / 30) % 12
    deg = _n(lon) % 30.0
    cn, en, sym, elem, mode = SIGNS[idx]
    mins = int((deg % 1) * 60)
    return {
        "sign_index": idx,
        "sign_cn": cn,
        "sign_en": en,
        "sign_symbol": sym,
        "element": elem,
        "element_cn": _ELEM_CN[elem],
        "mode": mode,
        "mode_cn": _MODE_CN[mode],
        "degree": round(deg, 2),
        "degree_str": f"{int(deg)}°{mins:02d}′",
    }


# ── 儒略日 ───────────────────────────────────────────────────
def julian_day(dt: datetime) -> float:
    """UTC datetime → 儒略日（JD）"""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    y, m, d = dt.year, dt.month, dt.day
    h = dt.hour + dt.minute / 60.0 + dt.second / 3600.0
    if m <= 2:
        y -= 1
        m += 12
    A = int(y / 100)
    B = 2 - A + int(A / 4)
    return int(365.25 * (y + 4716)) + int(30.6001 * (m + 1)) + d + h / 24.0 + B - 1524.5


# ── 太阳黄经（视黄经 ±0.01°） ────────────────────────────────
def sun_longitude(T: float) -> float:
    """视太阳黄经（度），T = 自 J2000.0 的儒略世纪数。Meeus Ch.25"""
    L0 = _n(280.46646 + 36000.76983 * T + 0.0003032 * T * T)
    M = _n(357.52911 + 35999.05029 * T - 0.0001537 * T * T)
    Mr = _r(M)
    C = (
        (1.9146 - 0.004817 * T - 0.000014 * T * T) * math.sin(Mr)
        + (0.019993 - 0.000101 * T) * math.sin(2.0 * Mr)
        + 0.000290 * math.sin(3.0 * Mr)
    )
    Ω = _n(125.04 - 1934.136 * T)
    return _n(L0 + C - 0.00569 - 0.00478 * math.sin(_r(Ω)))


# ── 月亮黄经（简化 Brown 理论 ±1°） ─────────────────────────
def moon_longitude(T: float) -> float:
    """月亮黄经（度），精度 ±1°。Meeus Ch.47 简化版"""
    L = _n(218.3165 + 481267.8813 * T)  # 平黄经
    M = _n(357.5291 + 35999.0503 * T)  # 太阳平近点角
    Mp = _n(134.9634 + 477198.8676 * T)  # 月亮平近点角
    D = _n(297.8502 + 445267.1115 * T)  # 月亮平距角
    F = _n(93.2720 + 483202.0175 * T)  # 纬度参数

    def s(a: float) -> float:
        return math.sin(_r(a))

    return _n(
        L
        + 6.2886 * s(Mp)
        + 1.2740 * s(2.0 * D - Mp)
        + 0.6583 * s(2.0 * D)
        + 0.2136 * s(2.0 * Mp)
        - 0.1851 * s(M)
        - 0.1143 * s(2.0 * F)
        + 0.0588 * s(2.0 * D - 2.0 * Mp)
        + 0.0572 * s(2.0 * D - M - Mp)
        + 0.0533 * s(2.0 * D + Mp)
        + 0.0458 * s(2.0 * D - M)
        - 0.0409 * s(M + Mp)
    )


# ── 行星开普勒轨道（Meeus Table 33.a） ──────────────────────
# 轨道根数: (L0, L1, a, e, ω, Ω, i)
#   L0  = 平黄经（J2000, 度）
#   L1  = 平黄经变化率（度/世纪）
#   a   = 半长轴（AU）
#   e   = 离心率
#   ω   = 近日点黄经（度）
#   Ω   = 升交点黄经（度）
#   i   = 轨道倾角（度）

_PL: dict[str, tuple[float, ...]] = {
    "Mercury": (252.250906, 149472.6746358, 0.38709927, 0.20563593, 77.45779628, 48.33076593, 7.00497902),
    "Venus": (181.979801, 58517.8156760, 0.72333566, 0.00677672, 131.60246718, 76.67984255, 3.39467605),
    "Mars": (355.433275, 19140.2993313, 1.52371034, 0.09339410, -23.94362959, 49.55953891, 1.84969142),
    "Jupiter": (34.351519, 3034.7056233, 5.20288700, 0.04838624, 14.72847983, 100.47390909, 1.30439695),
    "Saturn": (50.077444, 1222.1137943, 9.53667594, 0.05386179, 92.59887831, 113.66242448, 2.48599187),
    "Uranus": (314.055005, 428.4669983, 19.18916464, 0.04725744, 170.95427630, 74.01692503, 0.77263783),
    "Neptune": (304.348665, 218.4862002, 30.06992276, 0.00859048, 44.96476227, 131.78422574, 1.77004347),
}
# 地球轨道根数
_EARTH: tuple[float, ...] = (100.464457, 36000.7698278, 1.00000011, 0.016702, 102.947719, 0.0, 0.0)


def _helio_lon_r(
    L0: float, L1: float, a: float, e: float, w: float, O: float, i: float, T: float
) -> tuple[float, float]:
    """
    行星日心黄经（度）和日心距（AU）。
    简化开普勒轨道——忽略行星纬度项，足以判断黄经星座。
    """
    L = _n(L0 + L1 * T)  # 平黄经
    M = _r(_n(L - _n(w)))  # 平近点角（弧度）
    # Newton 法解开普勒方程 E - e*sin(E) = M
    E = M + e * math.sin(M)
    for _ in range(8):
        E = M + e * math.sin(E)
    # 真近点角
    nu = 2.0 * math.atan2(
        math.sqrt(1.0 + e) * math.sin(E / 2.0),
        math.sqrt(1.0 - e) * math.cos(E / 2.0),
    )
    # 日心黄经
    helio_lon = _n(_d(nu) + _n(w))
    # 日心距
    r = a * (1.0 - e * math.cos(E))
    return helio_lon, r


def planet_longitude(name: str, T: float) -> float:
    """
    行星地心黄经（度），忽略黄纬（精度 ±2-5°，用于判星座已足够）。
    """
    p_lon, p_r = _helio_lon_r(*_PL[name], T)  # type: ignore[arg-type]
    e_lon, e_r = _helio_lon_r(*_EARTH, T)  # type: ignore[arg-type]
    # 转换到地心直角坐标系（在黄道面内）
    px = p_r * math.cos(_r(p_lon)) - e_r * math.cos(_r(e_lon))
    py = p_r * math.sin(_r(p_lon)) - e_r * math.sin(_r(e_lon))
    return _n(_d(math.atan2(py, px)))


# ── 上升点 / 中天（±0.1°） ──────────────────────────────────
def ascendant_mc(jd: float, lat: float, lon: float) -> tuple[float, float]:
    """
    计算上升黄经（ASC）和中天黄经（MC）。
    lat: 地理纬度（北纬为正）
    lon: 地理经度（东经为正）
    """
    T = (jd - 2451545.0) / 36525.0
    # 格林尼治平恒星时（度）
    GMST = _n(280.46061837 + 360.98564736629 * (jd - 2451545.0) + 0.000387933 * T * T)
    LST = _n(GMST + lon)  # 本地恒星时（度）
    eps = 23.4393 - 0.013004 * T  # 黄赤交角（度）
    eps_r = _r(eps)
    LST_r = _r(LST)
    lat_r = _r(lat)

    # 中天黄经 (MC)
    mc = _n(_d(math.atan2(math.sin(LST_r), math.cos(LST_r) * math.cos(eps_r))))

    # 上升黄经 (ASC) — 东方地平线
    # 公式来自 Meeus，适用于非极地纬度
    tan_lat = math.tan(lat_r)
    denom = -(math.sin(LST_r) * math.cos(eps_r) + tan_lat * math.sin(eps_r))
    asc = _n(_d(math.atan2(math.cos(LST_r), denom)))

    return asc, mc


# ── 逆行检测 ─────────────────────────────────────────────────
def is_retrograde(name: str, T: float) -> bool:
    """通过比较 T 和 T+1天 的黄经差判断行星是否逆行"""
    dt = 1.0 / 36525.0  # 1天对应的儒略世纪步长
    fn = planet_longitude
    d = fn(name, T + dt) - fn(name, T)
    return ((d + 180.0) % 360.0 - 180.0) < 0.0


# ── 相位计算 ─────────────────────────────────────────────────
_ASPECT_DEFS: list[tuple[str, str, int, float]] = [
    ("合相", "Conjunction", 0, 8.0),
    ("六分相", "Sextile", 60, 5.0),
    ("四分相", "Square", 90, 7.0),
    ("三分相", "Trine", 120, 7.0),
    ("补十二分相", "Quincunx", 150, 3.0),
    ("对冲相", "Opposition", 180, 8.0),
]

_ASPECT_COLORS: dict[str, str] = {
    "Conjunction": "#f59e0b",
    "Sextile": "#22c55e",
    "Square": "#ef4444",
    "Trine": "#3b82f6",
    "Opposition": "#a855f7",
    "Quincunx": "#94a3b8",
}


def compute_aspects(positions: dict[str, float]) -> list[dict[str, Any]]:
    """计算行星间相位列表"""
    names = list(positions)
    result: list[dict[str, Any]] = []
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            n1, n2 = names[i], names[j]
            diff = abs((positions[n2] - positions[n1] + 180.0) % 360.0 - 180.0)
            for cn, en, ang, orb in _ASPECT_DEFS:
                if abs(diff - ang) <= orb:
                    result.append(
                        {
                            "planet1": n1,
                            "planet2": n2,
                            "aspect_cn": cn,
                            "aspect_en": en,
                            "angle": ang,
                            "orb": round(abs(diff - ang), 2),
                            "color": _ASPECT_COLORS.get(en, "#94a3b8"),
                        }
                    )
                    break
    return result


# ── 儒略日 → UTC datetime ──────────────────────────────────────
def jd_to_datetime(jd: float) -> datetime:
    """儒略日（JD）→ UTC datetime"""
    from datetime import timedelta

    delta_days = jd - 2451545.0  # 相对 J2000.0
    return datetime(2000, 1, 1, 12, 0, 0, tzinfo=UTC) + timedelta(days=delta_days)


# ── 太阳回归年盘 ─────────────────────────────────────────────
def solar_return_chart(
    natal_sun_lon: float,
    sr_year: int,
    lat: float,
    lon: float,
) -> dict[str, Any]:
    """
    太阳回归年盘（Solar Return Chart）。
    找出 sr_year 年中太阳黄经等于出生太阳黄经的精确时刻，
    并在该时刻/地点计算完整出生盘。

    参数
    ----
    natal_sun_lon : 出生太阳黄经（度）
    sr_year       : 欲求年份（公历年）
    lat, lon      : 回归年所在地坐标（用于计算上升/中天）

    返回
    ----
    compute_chart() 全部字段 + 'sr_dt_utc', 'sr_year', 'natal_sun_lon'
    """
    DEG_PER_DAY = 360.0 / 365.25  # 太阳每天约行 0.9856°

    # 从该年的 1 月 1 日开始估算
    dt_start = datetime(sr_year, 1, 1, 0, 0, 0, tzinfo=UTC)
    jd_start = julian_day(dt_start)

    T0 = (jd_start - 2451545.0) / 36525.0
    lon0 = sun_longitude(T0)

    # 向前推进的黄经差 [0, 360)
    diff = (natal_sun_lon - lon0 + 360.0) % 360.0
    jd_approx = jd_start + diff / DEG_PER_DAY

    # Newton 迭代，通常 10 步即可收敛到 < 1e-8°
    for _ in range(40):
        T = (jd_approx - 2451545.0) / 36525.0
        lon_now = sun_longitude(T)
        err = (natal_sun_lon - lon_now + 180.0) % 360.0 - 180.0
        if abs(err) < 1e-8:
            break
        jd_approx += err / DEG_PER_DAY

    sr_dt = jd_to_datetime(jd_approx)
    chart = compute_chart(sr_dt, lat, lon)
    chart["sr_dt_utc"] = sr_dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    chart["sr_year"] = sr_year
    chart["natal_sun_lon"] = round(natal_sun_lon, 4)
    return chart


# ── 主入口 ───────────────────────────────────────────────────
_PLANET_LIST = [
    "Sun",
    "Moon",
    "Mercury",
    "Venus",
    "Mars",
    "Jupiter",
    "Saturn",
    "Uranus",
    "Neptune",
]
_CN: dict[str, str] = {
    "Sun": "太阳",
    "Moon": "月亮",
    "Mercury": "水星",
    "Venus": "金星",
    "Mars": "火星",
    "Jupiter": "木星",
    "Saturn": "土星",
    "Uranus": "天王星",
    "Neptune": "海王星",
}
_SYM: dict[str, str] = {
    "Sun": "☉",
    "Moon": "☽",
    "Mercury": "☿",
    "Venus": "♀",
    "Mars": "♂",
    "Jupiter": "♃",
    "Saturn": "♄",
    "Uranus": "⛢",
    "Neptune": "♆",
}


def compute_chart(dt_utc: datetime, lat: float, lon: float) -> dict[str, Any]:
    """
    西方出生盘计算主入口。

    参数
    ----
    dt_utc : UTC 时间
    lat    : 地理纬度（北纬正）
    lon    : 地理经度（东经正）

    返回
    ----
    完整出生盘数据字典，含行星位置、上升/中天、相位、元素/模式统计。
    """
    jd = julian_day(dt_utc)
    T = (jd - 2451545.0) / 36525.0

    # 计算各天体地心黄经
    positions: dict[str, float] = {
        "Sun": sun_longitude(T),
        "Moon": moon_longitude(T),
    }
    for pname in ["Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Uranus", "Neptune"]:
        positions[pname] = planet_longitude(pname, T)

    # 计算行星日心黄经（用于天文辅助展示）
    earth_helio_lon, _ = _helio_lon_r(*_EARTH, T)  # type: ignore[arg-type]
    heliocentric_positions: dict[str, float] = {
        "Earth": earth_helio_lon,
    }
    for pname in ["Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Uranus", "Neptune"]:
        p_helio_lon, _ = _helio_lon_r(*_PL[pname], T)  # type: ignore[arg-type]
        heliocentric_positions[pname] = p_helio_lon

    # 上升 / 中天
    asc, mc = ascendant_mc(jd, lat, lon)

    # 行星详情列表
    planets: list[dict[str, Any]] = []
    for pname in _PLANET_LIST:
        si = _sign_info(positions[pname])
        retro = is_retrograde(pname, T) if pname not in ("Sun", "Moon") else False
        planets.append(
            {
                "name_en": pname,
                "name_cn": _CN[pname],
                "symbol": _SYM[pname],
                "longitude": round(positions[pname], 2),
                "retrograde": retro,
                **si,
            }
        )

    # 元素 & 模式统计
    elem_counts = {"fire": 0, "earth": 0, "air": 0, "water": 0}
    mode_counts = {"cardinal": 0, "fixed": 0, "mutable": 0}
    for p in planets:
        elem_counts[p["element"]] += 1
        mode_counts[p["mode"]] += 1

    return {
        "julian_day": round(jd, 4),
        "planets": planets,
        "ascendant": {"longitude": round(asc, 2), **_sign_info(asc)},
        "midheaven": {"longitude": round(mc, 2), **_sign_info(mc)},
        "aspects": compute_aspects(positions),
        "element_counts": elem_counts,
        "mode_counts": mode_counts,
        "geocentric_longitudes": {k: round(v, 2) for k, v in positions.items()},
        "heliocentric_longitudes": {k: round(v, 2) for k, v in heliocentric_positions.items()},
    }
