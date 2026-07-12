"""
静态数据 API 端点（M0 任务 §4.13 + Sprint 5 D2/D3/D6/C3）

- GET /api/v1/glossary              — 命理术语词汇表 (≥50条)，支持全文搜索 ?q=
- PUT /api/v1/glossary/{term}       — 管理员更新词汇定义 (D6)
- GET /api/v1/cities                — 城市经纬度列表，支持智能搜索 ?q= (D3)
- GET /api/v1/classics              — 古籍原文 TF-IDF 检索 (D2)
- GET /api/v1/docs/concepts         — 八字/紫微术语概念说明 (C3)

数据源: data/glossary.json / data/cities.json / data/classics.json / data/concepts.json
服务启动时一次性加载至内存，每次请求不访问 DB。
"""

from __future__ import annotations

from functools import lru_cache
import json
import logging
from pathlib import Path
from typing import Literal

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.dependencies import RequiredUser
from services.classics_search import (
    ClassicPassageModel,
    load_classics,
)
from services.classics_search import (
    tfidf_score as _tfidf_score,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["static-data"])

# ── 数据文件路径 ────────────────────────────────────────────────────────────────
_DATA_DIR = Path(__file__).resolve().parent.parent / "data"


# ── Schema 模型 ─────────────────────────────────────────────────────────────────
class GlossaryItemModel(BaseModel):
    term: str  # 术语，如"七杀"
    pinyin: str  # 拼音，如"qī shā"
    definition: str  # 简明定义（≤80字）
    category: Literal["格局", "神煞", "五行", "十神", "大运", "紫微", "其他"]
    classic_source: str | None = None  # 来源典籍（如有）


class GlossaryUpdateRequest(BaseModel):
    definition: str
    pinyin: str | None = None
    classic_source: str | None = None


class CityModel(BaseModel):
    name: str  # 城市名，如"北京"
    province: str  # 省份，如"北京市"
    lng: float  # 经度，精确到小数点后2位，范围[73.0, 135.5]
    lat: float  # 纬度
    city_type: Literal["直辖市", "省会", "计划单列市", "地级市"]


class ConceptModel(BaseModel):
    id: str
    term: str
    category: Literal["bazi", "ziwei"]
    definition: str
    aliases: list[str] = []
    related: list[str] = []


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
        items.sort(key=lambda x: (x.category, x.term))
        logger.info("Loaded %d glossary terms from %s", len(items), path)
        return items
    except Exception as exc:
        logger.error("Failed to load glossary.json: %s", exc)
        return []


@lru_cache(maxsize=1)
def _load_cities() -> list[CityModel]:
    """服务启动时一次性加载城市列表至内存（§4.13）"""
    path = _DATA_DIR / "cities.json"
    if not path.exists():
        logger.warning("cities.json not found at %s", path)
        return []
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        cities = [CityModel(**c) for c in raw]
        order = {"直辖市": 0, "省会": 1, "计划单列市": 2, "地级市": 3}
        cities.sort(key=lambda c: (order.get(c.city_type, 9), c.name))
        logger.info("Loaded %d cities from %s", len(cities), path)
        return cities
    except Exception as exc:
        logger.error("Failed to load cities.json: %s", exc)
        return []


# _load_classics 已迁移至 services.classics_search.load_classics
# 本地别名保持向后兼容
_load_classics = load_classics


@lru_cache(maxsize=1)
def _load_concepts() -> list[ConceptModel]:
    """服务启动时一次性加载概念术语表（C3）"""
    path = _DATA_DIR / "concepts.json"
    if not path.exists():
        logger.warning("concepts.json not found at %s", path)
        return []
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        items = [ConceptModel(**item) for item in raw]
        logger.info("Loaded %d concepts from %s", len(items), path)
        return items
    except Exception as exc:
        logger.error("Failed to load concepts.json: %s", exc)
        return []


# _tokenize / _tfidf_score 已迁移至 services.classics_search
# （别名已在顶部 import 时声明）


# ── 端点 ─────────────────────────────────────────────────────────────────────────


@router.get(
    "/glossary",
    response_model=list[GlossaryItemModel],
    summary="命理术语词汇表（支持全文搜索）",
    description=(
        "返回命理术语词汇表。"
        "可选 ?q= 进行全文搜索（匹配 term/definition/pinyin）；"
        "可选 ?category= 分类过滤。"
        "无需认证，数据来自 data/glossary.json，启动时加载至内存。"
    ),
)
def get_glossary(
    q: str | None = Query(None, description="全文搜索关键词"),
    category: str | None = Query(None, description="分类过滤：格局/神煞/五行/十神/大运/紫微/其他"),
    limit: int = Query(100, ge=1, le=500),
) -> list[GlossaryItemModel]:
    """GET /api/v1/glossary — 返回命理术语，支持 ?q= 全文搜索"""
    items = _load_glossary()
    if not items:
        raise HTTPException(status_code=503, detail="Glossary data not available")
    if category:
        items = [i for i in items if i.category == category]
    if q and q.strip():
        docs = [(f"{i.term} {i.pinyin} {i.definition}", i) for i in items]
        scored = _tfidf_score(q.strip(), docs)
        items = [obj for score, obj in scored if score > 0]
        if not items:
            # 降级：简单包含匹配
            ql = q.strip().lower()
            items = [
                i
                for i in _load_glossary()
                if ql in i.term.lower() or ql in i.definition.lower() or ql in (i.pinyin or "").lower()
            ]
    return items[:limit]


@router.put(
    "/glossary/{term}",
    response_model=GlossaryItemModel,
    summary="管理员更新词汇定义（D6）",
    description="需要管理员权限。更新 data/glossary.json 中指定词汇的定义（内存缓存同步更新）。",
)
def update_glossary_term(
    term: str,
    body: GlossaryUpdateRequest,
    _user: RequiredUser,
) -> GlossaryItemModel:
    """PUT /api/v1/glossary/{term} — 更新词汇定义（管理员）"""
    # 鉴权：仅管理员可更新词汇
    if not getattr(_user, "is_admin", False):
        raise HTTPException(status_code=403, detail="需要管理员权限")
    items = _load_glossary()
    for item in items:
        if item.term == term:
            item.definition = body.definition
            if body.pinyin is not None:
                item.pinyin = body.pinyin
            if body.classic_source is not None:
                item.classic_source = body.classic_source
            # 持久化写回 JSON
            path = _DATA_DIR / "glossary.json"
            try:
                raw = [i.model_dump() for i in items]
                path.write_text(json.dumps(raw, ensure_ascii=False, indent=2), encoding="utf-8")
            except Exception as exc:
                logger.error("Failed to persist glossary.json: %s", exc)
                raise HTTPException(status_code=500, detail="词汇更新失败，无法写入文件") from exc
            return item
    raise HTTPException(status_code=404, detail=f"词汇 '{term}' 不存在")


@router.get(
    "/cities",
    response_model=list[CityModel],
    summary="城市经纬度列表（支持智能搜索）",
    description=(
        "返回城市经纬度，可选 ?q= 进行城市名/省份模糊搜索（D3）。"
        "可选 ?city_type= 分类过滤。"
        "无需认证，数据来自 data/cities.json，启动时加载至内存，不访问 DB。"
    ),
)
def get_cities(
    q: str | None = Query(None, description="城市名或省份模糊搜索"),
    city_type: str | None = Query(None, description="直辖市/省会/计划单列市/地级市"),
) -> list[CityModel]:
    """GET /api/v1/cities — 支持 ?q= 模糊搜索城市名/省份"""
    cities = _load_cities()
    if not cities:
        raise HTTPException(status_code=503, detail="Cities data not available")
    if city_type:
        cities = [c for c in cities if c.city_type == city_type]
    if q and q.strip():
        ql = q.strip().lower()
        cities = [c for c in cities if ql in c.name.lower() or ql in c.province.lower()]
    return cities


@router.get(
    "/classics",
    response_model=list[ClassicPassageModel],
    summary="古籍原文 TF-IDF 全文检索（D2）",
    description=(
        "对 data/classics.json 古籍语料进行 TF-IDF 全文检索，按相关度排序。"
        "可选 ?query= 搜索关键词；?tag= 按标签过滤；?limit= 返回数量。"
        "无需认证。"
    ),
)
def search_classics(
    query: str | None = Query(None, description="检索关键词（TF-IDF 排序）"),
    tag: str | None = Query(None, description='按标签过滤，如"格局"、"用神"'),
    limit: int = Query(10, ge=1, le=50),
) -> list[ClassicPassageModel]:
    """GET /api/v1/classics — 古籍 TF-IDF 全文检索"""
    items = list(_load_classics())
    if not items:
        raise HTTPException(status_code=503, detail="Classics data not available")
    if tag:
        items = [i for i in items if tag in i.tags]
    if query and query.strip():
        docs = [(f"{i.title} {i.passage} {i.notes or ''} {' '.join(i.tags)}", i) for i in items]
        scored = _tfidf_score(query.strip(), docs)
        result = []
        for score, obj in scored[:limit]:
            if score > 0:
                obj_copy = obj.model_copy(update={"score": round(score, 4)})
                result.append(obj_copy)
        if not result:
            # 降级：简单包含匹配
            ql = query.strip().lower()
            result = [
                i for i in items if ql in i.passage.lower() or ql in i.title.lower() or ql in (i.notes or "").lower()
            ][:limit]
        return result
    return items[:limit]


@router.get(
    "/docs/concepts",
    response_model=list[ConceptModel],
    summary="八字/紫微术语概念说明（C3）",
    description=(
        "返回命理术语概念列表，支持 ?category=bazi|ziwei 分类过滤与 ?q= 关键词搜索。"
        "数据来自 data/concepts.json，无需认证。"
    ),
)
def get_concepts(
    category: str | None = Query(None, description="分类过滤：bazi 或 ziwei"),
    q: str | None = Query(None, description="关键词搜索（匹配 term/definition/aliases）"),
    limit: int = Query(100, ge=1, le=500),
) -> list[ConceptModel]:
    """GET /api/v1/docs/concepts — 命理概念术语说明"""
    items = _load_concepts()
    if not items:
        raise HTTPException(status_code=503, detail="Concepts data not available")
    if category:
        if category not in ("bazi", "ziwei"):
            raise HTTPException(status_code=400, detail="category 只支持 bazi 或 ziwei")
        items = [i for i in items if i.category == category]
    if q and q.strip():
        ql = q.strip().lower()
        items = [
            i
            for i in items
            if ql in i.term.lower() or ql in i.definition.lower() or any(ql in alias.lower() for alias in i.aliases)
        ]
    return items[:limit]
