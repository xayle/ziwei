"""
routers/name.py — §16 姓名学分析端点

端点：
  POST /api/v1/name/analyze  — 五格数理 + 三才配置分析（无需认证）
  POST /api/v1/name/suggest  — 改名字选建议（无需认证）
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from starlette.requests import Request

from app.schemas.name import (
    GridInfoResponse,
    NameAnalysisResponse,
    NameRequest,
    NameSuggestionItem,
    NameSuggestRequest,
    NameSuggestResponse,
    SancaiInfoResponse,
)
from services.name_engine import analyze_name, suggest_names
from services.rate_limit import limiter

router = APIRouter(prefix="/api/v1/name", tags=["姓名学"])


def _to_response(result) -> NameAnalysisResponse:
    def _grid(g) -> GridInfoResponse:
        return GridInfoResponse(
            number=g.number,
            element=g.element,
            lucky=g.lucky,
            score=g.score,
            desc=g.desc,
        )

    return NameAnalysisResponse(
        surname=result.surname,
        given_name=result.given_name,
        tianke=_grid(result.tianke),
        renke=_grid(result.renke),
        dike=_grid(result.dike),
        waike=_grid(result.waike),
        zonge=_grid(result.zonge),
        sancai=SancaiInfoResponse(
            pattern=result.sancai.pattern,
            lucky=result.sancai.lucky,
            score=result.sancai.score,
            desc=result.sancai.desc,
        ),
        overall_score=result.overall_score,
        summary=result.summary,
    )


@router.post("/analyze", response_model=NameAnalysisResponse, summary="姓名五格三才分析")
@limiter.limit("30/minute")
def analyze_name_endpoint(request: Request, req: NameRequest) -> NameAnalysisResponse:
    """
    输入姓名，返回五格数理分析（天/人/地/外/总格）+ 三才五行配置。

    **五格说明：**
    - 天格：姓的格数（单姓 = 姓笔画+1）
    - 人格：主格，决定主要运势
    - 地格：名的格数（单名 = 名笔画+1）
    - 外格：天格+地格-人格
    - 总格：全名笔画总数

    **评分：** 1=极凶, 5=中性, 8=吉, 10=大吉
    """
    try:
        result = analyze_name(req.surname, req.given_name)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"分析失败：{e}")

    return _to_response(result)


@router.post("/suggest", response_model=NameSuggestResponse, summary="改名字选建议")
@limiter.limit("10/minute")
def suggest_name_endpoint(request: Request, req: NameSuggestRequest) -> NameSuggestResponse:
    """
    根据姓氏和期望五行，在字库中穷举候选名字并按五格数理评分返回最优建议。

    **使用场景：**
    - 宝宝取名、成人改名
    - 结合八字分析，将命盘用神/喜神五行填入 `preferred_elements`，
      自动推荐五行契合度高的名字

    **preferred_elements 示例：**
    - `["水"]`  — 只推荐含水元素字的名字
    - `["水","木"]` — 推荐含水或木元素字的名字
    - 不填 — 不限五行，从全字库搜索

    **评分权重：** 人格 30%、三才 20%、地格 20%、总格 10%、天格/外格各 10%
    """
    # 校验五行参数
    valid_elements = {"木", "火", "土", "金", "水"}
    pref = req.preferred_elements
    if pref is not None:
        invalid = [e for e in pref if e not in valid_elements]
        if invalid:
            raise HTTPException(
                status_code=422,
                detail=f"preferred_elements 包含无效五行值：{invalid}，合法值为 {sorted(valid_elements)}",
            )
        pref = [e for e in pref if e in valid_elements] or None

    try:
        suggestions, total = suggest_names(
            surname=req.surname,
            name_length=req.name_length,
            preferred_elements=pref,
            top_n=req.top_n,
            min_score=req.min_score,
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"建议生成失败：{e}")

    items = [
        NameSuggestionItem(
            given_name=s.given_name,
            overall_score=s.overall_score,
            renke_score=s.renke_score,
            sancai_score=s.sancai_score,
            sancai_pattern=s.sancai_pattern,
            element_composition=s.element_composition,
            summary=s.summary,
        )
        for s in suggestions
    ]
    return NameSuggestResponse(
        surname=req.surname,
        name_length=req.name_length,
        preferred_elements=pref,
        total_candidates_evaluated=total,
        suggestions=items,
    )


# ── T3.2: 中文姓名笔画数字化 ────────────────────────────────────────────────

from pydantic import BaseModel, Field


class StrokesRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=20, description="中文姓名，如'张伟'")


class CharStrokeInfo(BaseModel):
    char: str
    strokes: int
    numerology_digit: int  # 笔画化减到1-9（保留11/22/33）


class StrokesResponse(BaseModel):
    name: str
    chars: list[CharStrokeInfo]
    total_strokes: int
    expression_number: int  # 全名笔画总数化减


@router.post("/strokes", response_model=StrokesResponse, summary="中文姓名笔画数字化")
@limiter.limit("30/minute")
def analyze_strokes_endpoint(request: Request, req: StrokesRequest) -> StrokesResponse:
    """
    对中文姓名逐字查询笔画数，并进行数字命理化减，输出：
    - 每个字对应笔画数及化减后数字（1-9，保留大师数11/22/33）
    - 全名笔画总数及表达数（Expression Number）

    可配合 NumerologyView 的中文模式使用。
    """
    from services.name_engine.engine import get_stroke_count

    def _reduce(n: int) -> int:
        if n in (11, 22, 33):
            return n
        if n < 10:
            return n
        return _reduce(sum(int(d) for d in str(n)))

    chars_info: list[CharStrokeInfo] = []
    total = 0
    for char in req.name:
        s = get_stroke_count(char)
        total += s
        chars_info.append(CharStrokeInfo(char=char, strokes=s, numerology_digit=_reduce(s)))

    return StrokesResponse(
        name=req.name,
        chars=chars_info,
        total_strokes=total,
        expression_number=_reduce(total),
    )
