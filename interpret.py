"""
DEPRECATED — Replaced by services/bazi_engine/ interpretation modules.
[M1 任务1.22] 此文件仅保留以兼容旧导入，M2完成后删除。Do not add new code here.
"""
from __future__ import annotations

from boundary import Validation


def interpret(validation: Validation):
    """Generate human-readable output; must respect interpretation gating."""
    raise NotImplementedError
