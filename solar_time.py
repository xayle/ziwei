"""Solar time corrections.

⚠️  DEPRECATED — 此文件仅实现了经度修正（4分钟/度），
    缺失 Spencer 时差方程（EoT），最大误差可达 ±16 分钟，
    在时辰边界（15分钟阈值）附近会导致时柱判断错误。

    M1 任务 1.02 将在 services/bazi_engine/solar_time_v2.py 实现
    完整的 Spencer EoT 公式：B = 2π(N-1)/365
    届时主流程将切换到 solar_time_v2.py，本文件废弃。

    当前状态：仍被 verify.py 调用，M1.02 完成前保持可用。
"""

from __future__ import annotations

from constants import DEFAULT_LON


def compute_solar_correction_minutes(lon: float) -> tuple[float, float]:
    """Return (longitude_delta_deg, solar_correction_minutes).

    ⚠️ 仅含经度修正，缺 Spencer EoT，误差最大 ±16 分钟。
    M1 任务 1.02 完成后请切换到 solar_time_v2.py。

    longitude_delta_deg: lon - 120 (east positive)
    solar_correction_minutes: correction to apply to civil time (minutes)
    """
    delta = lon - DEFAULT_LON
    correction_minutes = 4.0 * delta
    return delta, correction_minutes
