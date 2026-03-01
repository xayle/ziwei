"""
静态数据 API 端点（M0 任务 §4.13）
- GET /api/v1/glossary  — 命理术语词汇表 (≥50条, GAP-06)
- GET /api/v1/cities    — 城市经纬度列表 (36城, GAP-06)

数据源: data/glossary.json / data/cities.json（随代码库提交）
服务启动时一次性加载至内存，每次请求不访问 DB。
"""
from __future__ import annotations

import json
import logging
from functools import lru_cache
from pathlib import Path
from typing import Literal, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["static-data"])

# ── 数据文件路径 ────────────────────────────────────────────────────────────────
_DATA_DIR = Path(__file__).resolve().parent.parent / "data"


# ── Schema 模型 ─────────────────────────────────────────────────────────────────
class GlossaryItemModel(BaseModel):
    term: str                   # 术语，如"七杀"
    pinyin: str                 # 拼音，如"qī shā"
    definition: str             # 简明定义（≤80字）
    category: Literal["格局", "神煞", "五行", "十神", "大运", "其他"]
    classic_source: Optional[str] = None  # 来源典籍（如有）


class CityModel(BaseModel):
    name: str       # 城市名，如"北京"
    province: str   # 省份，如"北京市"
    lng: float      # 经度，精确到小数点后2位，范围[73.0, 135.5]
    lat: float      # 纬度
    city_type: Literal["直辖市", "省会", "计划单列市"]


# ── 内存缓存加载 ─────────────────────────────────────────────────────────────────
@lru_cache(maxsize=1)
def _load_glossary() -> list[GlossaryItemModel]:
    """服务启动时一次性加载术语表至内存（§4.13）"""
    path = _DATA_DIR / "glossary.json"
    if not path.exists():
        logger.warning("glossary.json not found at %s", path)
        return []
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        items = [GlossaryItemModel(**item) for item in raw]
        # 按 category 分组，组内按 term 拼音升序（此处按 term 字节序排序，前端可按 pinyin 排序）
        items.sort(key=lambda x: (x.category, x.term))
        logger.info("Loaded %d glossary terms from %s", len(items), path)
        return items
    except Exception as exc:
        logger.error("Failed to load glossary.json: %s", exc)
        return []


@lru_cache(maxsize=1)
def _load_cities() -> list[CityModel]:
    """服务启动时一次性加载36城市列表至内存（§4.13）"""
    path = _DATA_DIR / "cities.json"
    if not path.exists():
        logger.warning("cities.json not found at %s", path)
        return []
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        cities = [CityModel(**c) for c in raw]
        # 按 city_type 分组，组内按 name 排序
        order = {"直辖市": 0, "省会": 1, "计划单列市": 2}
        cities.sort(key=lambda c: (order.get(c.city_type, 9), c.name))
        logger.info("Loaded %d cities from %s", len(cities), path)
        return cities
    except Exception as exc:
        logger.error("Failed to load cities.json: %s", exc)
        return []


# ── 端点 ─────────────────────────────────────────────────────────────────────────
@router.get(
    "/glossary",
    response_model=list[GlossaryItemModel],
    summary="命理术语词汇表",
    description=(
        "返回命理术语词汇表，供前端 tooltip 使用。"
        "无需认证，数据来自 data/glossary.json，启动时加载至内存。"
        "按 category 分组，组内按 term 排序。"
        "可选参数 ?category= 客户端过滤。"
    ),
)
def get_glossary(category: Optional[str] = None) -> list[GlossaryItemModel]:
    """GET /api/v1/glossary — 返回 ≥50 条命理术语"""
    items = _load_glossary()
    if not items:
        raise HTTPException(status_code=503, detail="Glossary data not available")
    if category:
        items = [i for i in items if i.category == category]
    return items


@router.get(
    "/cities",
    response_model=list[CityModel],
    summary="城市经纬度列表",
    description=(
        "返回 36 个城市经纬度（4直辖+27省会+5计划单列市），供城市选择器使用。"
        "无需认证，数据来自 data/cities.json，启动时加载至内存，不访问 DB。"
        "按 city_type 分组（直辖市/省会/计划单列市），组内按城市名排序。"
    ),
)
def get_cities() -> list[CityModel]:
    """GET /api/v1/cities — 返回恰好 36 城"""
    cities = _load_cities()
    if not cities:
        raise HTTPException(status_code=503, detail="Cities data not available")
    return cities
