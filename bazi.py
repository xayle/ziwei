"""
DEPRECATED — Replaced by services/bazi_engine/ engine modules.
[M1 任务1.22] 此文件仅保留以兼容旧导入，M2完成后删除。Do not add new code here.
"""
from __future__ import annotations

from boundary import Pillars


def build_bazi(dt_utc8, lon: float, use_solar: bool) -> Pillars:
    """Construct pillars using primary backend."""
    raise NotImplementedError
