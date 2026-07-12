"""
routers/fusheng_report.py — 浮生档案报告导出

POST /api/v1/fusheng/report/pdf — 档案驱动服务端 PDF（Playwright 渲染）
"""

from __future__ import annotations

import logging
from urllib.parse import quote

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from starlette.requests import Request

from app.schemas.fusheng_report import FushengReportPdfRequest
from services.fusheng_report_service import build_fusheng_report_payload, render_fusheng_report_html
from services.pdf_exporter import render_html_to_pdf
from services.rate_limit import limiter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/fusheng", tags=["浮生报告"])


def _safe_filename(label: str) -> str:
    safe = "".join(c for c in label if c not in r'\/:*?"<>|').strip()[:40] or "fusheng-report"
    return safe


@router.post(
    "/report/pdf",
    summary="导出浮生命理档案 PDF",
    response_class=Response,
)
@limiter.limit("10/minute")
async def export_fusheng_report_pdf(request: Request, body: FushengReportPdfRequest) -> Response:
    """
    根据档案字段聚合八字、紫微、姓名分析，服务端渲染 HTML 并导出 PDF。
    需本机安装 Playwright Chromium：`playwright install chromium`
    """
    try:
        payload = await build_fusheng_report_payload(body)
        html = render_fusheng_report_html(payload)
        pdf_bytes = await render_html_to_pdf(html)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("浮生报告 PDF 导出失败")
        raise HTTPException(status_code=500, detail="PDF 服务暂不可用，请稍后重试或使用客户端导出。") from exc

    filename = _safe_filename(body.label)
    encoded = quote(f"{filename}.pdf")
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{encoded}"},
    )
