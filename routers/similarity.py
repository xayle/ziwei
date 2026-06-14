"""
相似盘检索路由 (§11)

POST   /api/v1/similarity/index        — 索引一张命盘特征向量（登录可选）
GET    /api/v1/similarity/search       — 查找相似命盘（Top-K，按余弦相似度降序）
GET    /api/v1/similarity/cases        — 列出已索引命盘（分页）
DELETE /api/v1/similarity/cases/{id}   — 软删除案例
"""

from __future__ import annotations

from datetime import UTC, datetime
import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlmodel import Session, select

from app.models.chart_case import ChartCase
from db import get_session
from services.similarity_service import (
    CaseInput,
    cosine_similarity,
    extract_from_payload,
    vector_from_case_input,
    vector_from_json,
    vector_to_json,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/similarity", tags=["相似盘检索"])

_DEFAULT_TOP_K = 10
_MAX_TOP_K = 50


# ──────────────────────────────────────────────────────────────
# Schemas
# ──────────────────────────────────────────────────────────────


class SimilarityIndexRequest(BaseModel):
    chart_hash: str
    birth_solar: str = ""  # "YYYY-MM-DD" 或 "YYYY-MM-DDTHH:MM:SS"
    birth_year: int = 0  # 备用（当 birth_solar 缺失时）
    birth_month: int = 0
    birth_day: int = 0
    birth_hour: int = 0
    gender: str = ""
    wuxing_ju_name: str = ""
    life_palace_gz: str = ""
    patterns: list[dict] = []  # [{"name":..., "level":...}]
    source_label: str = "user"


class CaseResponse(BaseModel):
    id: int
    chart_hash: str
    birth_year: int
    birth_month: int
    birth_day: int
    birth_hour: int
    gender: str
    wuxing_ju_name: str
    life_palace_gz: str
    pattern_summary: str
    source_label: str
    created_at: datetime

    model_config = {"from_attributes": True}


class SimilarResult(BaseModel):
    case: CaseResponse
    similarity: float  # 0-1，越大越相似


class SearchResponse(BaseModel):
    query_hash: str
    total_indexed: int
    results: list[SimilarResult]


class CaseListResponse(BaseModel):
    total: int
    items: list[CaseResponse]


# ──────────────────────────────────────────────────────────────
# POST /index — 索引命盘
# ──────────────────────────────────────────────────────────────


@router.post("/index", response_model=CaseResponse, summary="索引命盘特征向量")
def index_case(
    body: SimilarityIndexRequest,
    session: Session = Depends(get_session),
) -> CaseResponse:
    """
    存储命盘特征向量。若相同 chart_hash 已存在，则更新向量与摘要字段。
    """
    payload = body.model_dump()
    ci: CaseInput | None = extract_from_payload(payload)
    if ci is None:
        raise HTTPException(status_code=422, detail="无法解析命盘数据，缺少必要字段。")

    vec = vector_from_case_input(ci)
    vec_json = vector_to_json(vec)

    # 查找是否已有相同 hash 的记录（未删除）
    existing = session.exec(
        select(ChartCase).where(ChartCase.chart_hash == ci.chart_hash).where(ChartCase.deleted_at.is_(None))  # type: ignore[union-attr]
    ).first()

    if existing:
        existing.vector_json = vec_json
        existing.wuxing_ju_name = ci.wuxing_ju_name
        existing.life_palace_gz = ci.life_palace_gz
        existing.pattern_summary = ci.pattern_summary
        existing.gender = ci.gender
        existing.birth_year = ci.birth_year
        existing.birth_month = ci.birth_month
        existing.birth_day = ci.birth_day
        existing.birth_hour = ci.birth_hour
        existing.source_label = ci.source_label
        session.add(existing)
        session.commit()
        session.refresh(existing)
        return CaseResponse.model_validate(existing)

    case = ChartCase(
        chart_hash=ci.chart_hash,
        birth_year=ci.birth_year,
        birth_month=ci.birth_month,
        birth_day=ci.birth_day,
        birth_hour=ci.birth_hour,
        gender=ci.gender,
        wuxing_ju_name=ci.wuxing_ju_name,
        life_palace_gz=ci.life_palace_gz,
        pattern_summary=ci.pattern_summary,
        vector_json=vec_json,
        source_label=ci.source_label,
    )
    session.add(case)
    session.commit()
    session.refresh(case)
    return CaseResponse.model_validate(case)


# ──────────────────────────────────────────────────────────────
# GET /search — 相似度检索
# ──────────────────────────────────────────────────────────────


@router.get("/search", response_model=SearchResponse, summary="查找相似命盘")
def search_similar(
    chart_hash: str = Query(..., description="当前命盘 hash"),
    life_palace_gz: str = Query("", description="命宫干支"),
    wuxing_ju_name: str = Query("", description="五行局"),
    gender: str = Query("", description="性别"),
    birth_year: int = Query(0, description="出生年"),
    patterns: str = Query("", description="格局 JSON 数组（URL 编码）"),
    top_k: int = Query(_DEFAULT_TOP_K, ge=1, le=_MAX_TOP_K),
    session: Session = Depends(get_session),
) -> SearchResponse:
    """
    返回与当前命盘最相似的 Top-K 历史命盘（按余弦相似度降序）。
    当前命盘可不必先调用 /index。
    """
    import json as _json

    patterns_raw: list[dict] = []
    if patterns:
        try:
            patterns_raw = _json.loads(patterns)
        except Exception:
            patterns_raw = []

    from services.similarity_service import build_vector

    query_vec = build_vector(life_palace_gz, wuxing_ju_name, gender, birth_year, patterns_raw)

    # 加载全部未删除的案例
    cases = session.exec(
        select(ChartCase).where(ChartCase.deleted_at.is_(None))  # type: ignore[union-attr]
    ).all()

    scored: list[tuple[float, ChartCase]] = []
    for c in cases:
        if c.chart_hash == chart_hash:
            continue  # 排除自身
        cv = vector_from_json(c.vector_json)
        sim = cosine_similarity(query_vec, cv)
        scored.append((sim, c))

    scored.sort(key=lambda x: x[0], reverse=True)
    top = scored[:top_k]

    return SearchResponse(
        query_hash=chart_hash,
        total_indexed=len(cases),
        results=[
            SimilarResult(
                case=CaseResponse.model_validate(c),
                similarity=round(sim, 4),
            )
            for sim, c in top
        ],
    )


# ──────────────────────────────────────────────────────────────
# GET /cases — 列表
# ──────────────────────────────────────────────────────────────


@router.get("/cases", response_model=CaseListResponse, summary="列出已索引命盘")
def list_cases(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    session: Session = Depends(get_session),
) -> CaseListResponse:
    from sqlmodel import func

    total = session.exec(
        select(func.count()).select_from(ChartCase).where(ChartCase.deleted_at.is_(None))  # type: ignore[union-attr]
    ).one()
    items = session.exec(
        select(ChartCase)
        .where(ChartCase.deleted_at.is_(None))  # type: ignore[union-attr]
        .order_by(ChartCase.created_at.desc())  # type: ignore[union-attr]
        .offset(skip)
        .limit(limit)
    ).all()
    return CaseListResponse(
        total=total,
        items=[CaseResponse.model_validate(c) for c in items],
    )


# ──────────────────────────────────────────────────────────────
# DELETE /cases/{id} — 软删除
# ──────────────────────────────────────────────────────────────


@router.delete("/cases/{case_id}", status_code=204, summary="软删除案例")
def delete_case(
    case_id: int,
    session: Session = Depends(get_session),
) -> None:
    case = session.get(ChartCase, case_id)
    if not case or case.deleted_at is not None:
        raise HTTPException(status_code=404, detail="案例不存在。")
    case.deleted_at = datetime.now(UTC)
    session.add(case)
    session.commit()
