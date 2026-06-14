"""
services/similarity_service.py — 相似命盘特征向量化与余弦相似度检索

特征向量规格 (21 维)：
  dims  0-11 : 命宫地支 one-hot  (子=0 … 亥=11)
  dims 12-16 : 五行局 one-hot    (水二=0, 木三=1, 金四=2, 土五=3, 火六=4)
  dim  17    : 性别              (男=0, 女=1)
  dim  18    : 出生年归一化       (birth_year / 2050)
  dim  19    : 吉格数归一化       (ji_count / 8)
  dim  20    : 凶格数归一化       (xiong_count / 8)

相似度：余弦相似度（纯 Python 实现，不依赖 numpy/scipy）。
"""

from __future__ import annotations

from dataclasses import dataclass
import json
import math
from typing import Any

# ────────────────────────────────────────────────────────────────
# 常量
# ────────────────────────────────────────────────────────────────

_BRANCHES = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
_BRANCH_TO_IDX: dict[str, int] = {b: i for i, b in enumerate(_BRANCHES)}

_WUXING_JU_NAMES = ["水二局", "木三局", "金四局", "土五局", "火六局"]
_WJ_TO_IDX: dict[str, int] = {n: i for i, n in enumerate(_WUXING_JU_NAMES)}

VECTOR_DIM = 21


# ────────────────────────────────────────────────────────────────
# 向量计算
# ────────────────────────────────────────────────────────────────


def build_vector(
    life_palace_gz: str,  # e.g. "甲子"，取最后一字为地支
    wuxing_ju_name: str,  # e.g. "水二局"
    gender: str,  # "男" / "女"
    birth_year: int,
    patterns: list[dict],  # list of {"level": "吉"/"凶"/"大吉"/"大凶", ...}
) -> list[float]:
    """从命盘关键字段构造 21 维特征向量。"""

    vec = [0.0] * VECTOR_DIM

    # ── dims 0-11: 命宫地支 one-hot ──────────────────────────────
    branch = life_palace_gz[-1] if life_palace_gz else ""
    branch_idx = _BRANCH_TO_IDX.get(branch, -1)
    if 0 <= branch_idx < 12:
        vec[branch_idx] = 1.0

    # ── dims 12-16: 五行局 one-hot ───────────────────────────────
    wj_idx = _WJ_TO_IDX.get(wuxing_ju_name, -1)
    if 0 <= wj_idx < 5:
        vec[12 + wj_idx] = 1.0

    # ── dim 17: 性别 ─────────────────────────────────────────────
    vec[17] = 1.0 if gender in ("女", "female", "F", "f") else 0.0

    # ── dim 18: 出生年归一化 ─────────────────────────────────────
    vec[18] = max(0.0, min(1.0, birth_year / 2050.0))

    # ── dims 19-20: 格局吉/凶数归一化 ───────────────────────────
    ji_count = sum(1 for p in patterns if p.get("level") in ("吉", "大吉"))
    xiong_count = sum(1 for p in patterns if p.get("level") in ("凶", "大凶"))
    vec[19] = min(1.0, ji_count / 8.0)
    vec[20] = min(1.0, xiong_count / 8.0)

    return vec


def _dot(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def _norm(v: list[float]) -> float:
    return math.sqrt(sum(x * x for x in v))


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """余弦相似度，值域 [0, 1]，1 = 完全相同。"""
    na, nb = _norm(a), _norm(b)
    if na < 1e-9 or nb < 1e-9:
        return 0.0
    return max(0.0, min(1.0, _dot(a, b) / (na * nb)))


# ────────────────────────────────────────────────────────────────
# 辅助：与路由层解耦的数据提取
# ────────────────────────────────────────────────────────────────


@dataclass
class CaseInput:
    """构建案例所需最精简字段。"""

    chart_hash: str
    birth_year: int
    birth_month: int
    birth_day: int
    birth_hour: int
    gender: str
    wuxing_ju_name: str
    life_palace_gz: str
    pattern_summary: str  # 格局名逗号分隔
    patterns_raw: list[dict]  # [{"name":..., "level":...}, ...]
    source_label: str = "user"


def extract_from_payload(payload: dict[str, Any]) -> CaseInput | None:
    """
    从前端 POST body 提取 CaseInput。
    payload 格式见 SimilarityIndexRequest schema。
    """
    try:
        birth_solar = payload.get("birth_solar", "")
        year = int(birth_solar[:4]) if len(birth_solar) >= 4 else payload.get("birth_year", 0)
        month = payload.get("birth_month", 0)
        day = payload.get("birth_day", 0)
        hour = payload.get("birth_hour", 0)
        patterns_raw: list[dict] = payload.get("patterns", [])
        pattern_summary = ",".join(p.get("name", "") for p in patterns_raw if p.get("name"))
        return CaseInput(
            chart_hash=payload["chart_hash"],
            birth_year=year,
            birth_month=month,
            birth_day=day,
            birth_hour=hour,
            gender=payload.get("gender", ""),
            wuxing_ju_name=payload.get("wuxing_ju_name", ""),
            life_palace_gz=payload.get("life_palace_gz", ""),
            pattern_summary=pattern_summary,
            patterns_raw=patterns_raw,
            source_label=payload.get("source_label", "user"),
        )
    except (KeyError, ValueError, TypeError):
        return None


def vector_from_case_input(ci: CaseInput) -> list[float]:
    return build_vector(
        ci.life_palace_gz,
        ci.wuxing_ju_name,
        ci.gender,
        ci.birth_year,
        ci.patterns_raw,
    )


def vector_to_json(vec: list[float]) -> str:
    return json.dumps([round(v, 6) for v in vec])


def vector_from_json(s: str) -> list[float]:
    try:
        return json.loads(s)
    except (json.JSONDecodeError, TypeError):
        return [0.0] * VECTOR_DIM
