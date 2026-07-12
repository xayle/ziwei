"""services/fengshui_engine — §15 风水方位计算引擎（八宅派 + 玄空飞星）。"""

from .bagua import DIRECTIONS_ZH, HOUSE_FACING_OPTIONS, calc_bagua
from .xuankong import STAR_AUSPICIOUS, STAR_NAMES, compute_xuankong

__all__ = [
    "DIRECTIONS_ZH",
    "HOUSE_FACING_OPTIONS",
    "STAR_AUSPICIOUS",
    "STAR_NAMES",
    "calc_bagua",
    "compute_xuankong",
]
