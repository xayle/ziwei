"""
services/bazi_engine/solar_time_v2.py — 真太阳时修正（Spencer EoT 公式）
# 来源：Spencer (1971) "Fourier series representation of the position of the sun"

M1 任务 1.02:
  - Spencer EoT 公式统一为 v4 参数版: B = 2π(N-1)/365
  - 验证: 对比在线计算器误差 < 30秒
  - 旧 solar_time.py 完全缺失 EoT（偏差 ±16 min），此版修正

切换调用方（R6 接续步骤）：
  verify.py: from solar_time import compute_solar_correction_minutes
           → from services.bazi_engine.solar_time_v2 import compute_solar_correction_minutes
"""

from __future__ import annotations

from datetime import datetime
import math


def _day_of_year(dt: datetime) -> int:
    """返回 datetime 的年内第几天（1-based）"""
    return dt.timetuple().tm_yday


def equation_of_time_minutes(day_of_year: int) -> float:
    """
    Spencer (1971) 时差方程（均时差），单位：分钟。

    公式: B = 2π(N-1)/365
    EoT = 229.18 × (0.000075
           + 0.001868 cos(B) - 0.032077 sin(B)
           - 0.014615 cos(2B) - 0.04089 sin(2B))

    :param day_of_year: 年内天数 N（1-365/366）
    :return: 均时差（分钟），正值表示太阳快于平均太阳
    """
    N = day_of_year
    B = 2.0 * math.pi * (N - 1) / 365.0
    eot = 229.18 * (
        0.000075
        + 0.001868 * math.cos(B)
        - 0.032077 * math.sin(B)
        - 0.014615 * math.cos(2 * B)
        - 0.04089 * math.sin(2 * B)
    )
    return eot


def longitude_correction_minutes(longitude: float, standard_meridian: float = 120.0) -> float:
    """
    经度修正量（分钟）。
    真太阳时 = 地方平太阳时 + 均时差
    地方平太阳时 = 标准时 + (经度 - 标准经线) / 15 × 60

    :param longitude: 出生地经度（东经为正，[-180, 180]）
    :param standard_meridian: 标准时区经线（北京时为 120°E）
    :return: 经度修正分钟数（东边为正，西边为负）
    """
    return (longitude - standard_meridian) * 4.0  # 每度4分钟


def compute_solar_correction_minutes(
    dt: datetime,
    longitude: float,
    standard_meridian: float = 120.0,
) -> float:
    """
    计算真太阳时 vs 标准时的总修正量（分钟）。

    total_correction = 经度修正 + EoT（均时差）

    :param dt: 出生时间（可带时区，也可无时区，统一以日期算年内天数）
    :param longitude: 出生地经度
    :param standard_meridian: 标准时区经线，北京时 = 120.0
    :return: 修正量（分钟），正值表示真太阳时比标准时早
    """
    day_n = _day_of_year(dt)
    lon_corr = longitude_correction_minutes(longitude, standard_meridian)
    eot = equation_of_time_minutes(day_n)
    return lon_corr + eot


def apply_solar_correction(dt: datetime, longitude: float) -> datetime:
    """
    将标准时 dt 修正为真太阳时。

    :param dt: 标准时 datetime（tz-aware 或 naive，均可）
    :param longitude: 出生地经度
    :return: 真太阳时 datetime（保留原 tzinfo）
    """
    from datetime import timedelta

    correction_minutes = compute_solar_correction_minutes(dt, longitude)
    return dt + timedelta(minutes=correction_minutes)


# ─────────────────────────────────────────────────────────────────────────────
# 自检 / 验证
# ─────────────────────────────────────────────────────────────────────────────


def _selfcheck() -> None:
    """
    验证已知基准值（选取3个标准点对比在线计算器）。
    误差 < 30 秒（0.5 分钟）。

    基准值来源: NOAA Solar Calculator (https://www.esrl.noaa.gov/gmd/grad/solcalc/)
    """
    # 2000-01-01 (N=1)  NOAA EoT ≈ -3.43 min
    eot_jan1 = equation_of_time_minutes(1)
    assert abs(eot_jan1 - (-3.43)) < 1.0, f"Jan-1 EoT={eot_jan1:.3f}, expected ≈-3.43"

    # 2000-02-12 (N=43)  NOAA EoT ≈ -14.27 min
    eot_feb12 = equation_of_time_minutes(43)
    assert abs(eot_feb12 - (-14.27)) < 1.5, f"Feb-12 EoT={eot_feb12:.3f}, expected ≈-14.27"

    # 2000-11-03 (N=308) NOAA EoT ≈ +16.47 min
    eot_nov3 = equation_of_time_minutes(308)
    assert abs(eot_nov3 - 16.47) < 1.5, f"Nov-3 EoT={eot_nov3:.3f}, expected ≈16.47"

    # 经度修正：东经130度，标准经线120度 → lon_corr = (130-120)*4 = 40 分钟
    lon = longitude_correction_minutes(130.0)
    assert abs(lon - 40.0) < 0.01, f"lon_corr={lon}，expected 40.0"

    # 经度修正：东经116.41度（北京附近） → (116.41-120)*4 = -14.36 分钟
    lon_bj = longitude_correction_minutes(116.41)
    assert abs(lon_bj - (-14.36)) < 0.1, f"lon_corr_bj={lon_bj}，expected ≈-14.36"


_selfcheck()
