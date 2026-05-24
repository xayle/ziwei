"""
routers/export.py — §14 命盘数据导出

端点：
    GET /api/v1/cases/{case_id}/export          — 下载含最新快照的完整 JSON 包
    GET /api/v1/cases/{case_id}/export/meta     — 仅返回 input_snapshot 元数据（JSON）
"""
from __future__ import annotations

from datetime import datetime, timezone
import json
import logging
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
from sqlmodel import Session, desc, select

from app.dependencies.auth import RequiredUser
from app.models.case import Case, Snapshot
from db import get_session

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/cases",
    tags=["命盘导出"],
)

DbSession = Annotated[Session, Depends(get_session)]

# 导出规范版本（当导出格式变更时递增）
_EXPORT_FORMAT_VERSION = "1.0"


# ─────────────────────────────────────────────────────────────
# 辅助：构建导出包
# ─────────────────────────────────────────────────────────────

def _build_export(case: Case, snapshot: Optional[Snapshot]) -> dict:
    """将 Case + Snapshot 合并为标准导出包。"""
    input_snapshot = {
        "id": case.id,
        "name": case.name,
        "gender": case.gender,
        "birth_dt_local": case.birth_dt_local,
        "tz": case.tz,
        "birth_dt": case.birth_dt,
        "city": case.city,
        "lon": case.lon,
        "solar_time_enabled": case.solar_time_enabled,
        "notes": case.notes,
        "tags": case.tags,
        "schema_version": case.schema_version,
        "created_at": case.created_at.isoformat() if case.created_at else None,
        "updated_at": case.updated_at.isoformat() if case.updated_at else None,
    }

    compute_result: Optional[dict] = None
    snapshot_meta: Optional[dict] = None
    if snapshot:
        compute_result = snapshot.output_json
        snapshot_meta = {
            "snapshot_id": snapshot.id,
            "kind": snapshot.kind,
            "api_version": snapshot.api_version,
            "rule_version": snapshot.rule_version,
            "schema_version": snapshot.schema_version,
            "engine_primary": snapshot.summary_engine_primary,
            "created_at": snapshot.created_at.isoformat() if snapshot.created_at else None,
        }

    return {
        "export_format_version": _EXPORT_FORMAT_VERSION,
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "input_snapshot": input_snapshot,
        "snapshot_meta": snapshot_meta,
        "compute_result": compute_result,
    }


def _safe_filename(name: str) -> str:
    """将命盘名称转换为安全的 ASCII 文件名（保留中文，只过滤危险字符）。"""
    safe = "".join(c for c in name if c not in r'\/:*?"<>|').strip()[:40] or "chart"
    return safe


# ─────────────────────────────────────────────────────────────
# GET /api/v1/cases/{case_id}/export — 完整 JSON 下载
# ─────────────────────────────────────────────────────────────

@router.get(
    "/{case_id}/export",
    summary="下载命盘完整 JSON",
    description=(
        "以 JSON 文件格式下载指定命盘的完整数据包，含：\n\n"
        "- `input_snapshot`：出生信息与档案元数据\n"
        "- `snapshot_meta`：计算快照版本信息（如有）\n"
        "- `compute_result`：最新计算结果（含宫位、星曜、大运、格局等）\n\n"
        "浏览器会自动弹出下载对话框。"
    ),
    response_class=Response,
    responses={
        200: {
            "content": {"application/json": {}},
            "headers": {"Content-Disposition": {"schema": {"type": "string"}}},
        }
    },
)
def export_case_json(
    case_id: str,
    current_user: RequiredUser,
    session: DbSession,
) -> Response:
    case = session.get(Case, case_id)
    if case is None or case.deleted_at is not None or case.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"命盘 {case_id} 不存在",
        )

    # 取最新 compute 快照（output_json 非空）
    snapshot = session.exec(
        select(Snapshot)
        .where(
            Snapshot.case_id == case_id,
            Snapshot.output_json.is_not(None),  # type: ignore[union-attr]
            Snapshot.deleted_at.is_(None),       # type: ignore[union-attr]
        )
        .order_by(desc(Snapshot.created_at))
        .limit(1)
    ).first()

    payload = _build_export(case, snapshot)
    filename = _safe_filename(case.name or "chart")
    json_bytes = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")

    logger.info(
        "命盘导出: case_id=%s user=%s snapshot=%s bytes=%d",
        case_id, current_user.id,
        snapshot.id if snapshot else "none",
        len(json_bytes),
    )

    return Response(
        content=json_bytes,
        media_type="application/json; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename*=UTF-8\'\'{filename}.json',
            "Content-Length": str(len(json_bytes)),
        },
    )


# ─────────────────────────────────────────────────────────────
# GET /api/v1/cases/{case_id}/export/meta — 仅 input_snapshot
# ─────────────────────────────────────────────────────────────

@router.get(
    "/{case_id}/export/meta",
    summary="获取命盘元数据（仅 input_snapshot）",
    response_model=dict,
)
def export_case_meta(
    case_id: str,
    current_user: RequiredUser,
    session: DbSession,
) -> dict:
    """轻量接口：只返回出生信息与档案元数据，不含大体积计算结果。"""
    case = session.get(Case, case_id)
    if case is None or case.deleted_at is not None or case.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"命盘 {case_id} 不存在",
        )
    payload = _build_export(case, None)
    return {"input_snapshot": payload["input_snapshot"]}

@router.get(
    "/{case_id}/export/pdf",
    summary="导出命盘为 PDF (需后端 playwright 支持)",
    response_class=Response,
)
async def export_case_pdf(
    case_id: str,
    current_user: RequiredUser,
    session: DbSession,
) -> Response:
    from datetime import datetime
    import os
    
    case = session.get(Case, case_id)
    if case is None or case.deleted_at is not None or case.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"命盘 {case_id} 不存在"
        )
    
    try:
        dt = datetime.fromisoformat(case.birth_dt_local)
    except ValueError:
        raise HTTPException(status_code=400, detail="时间提取异常")
        
    params = {
        "y": dt.year,
        "m": dt.month,
        "d": dt.day,
        "h": dt.hour,
        "min": dt.minute,
        "g": case.gender or "女",
        "lo": case.lon or 116.4,
    }
    
    base_url = os.environ.get("BASE_URL", "http://127.0.0.1:8000")
    
    from services.pdf_exporter import generate_pdf
    try:
        pdf_bytes = await generate_pdf(base_url, params)
        safe_name = _safe_filename(case.name or "命盘")
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=\"{safe_name}.pdf\""}
        )
    except Exception as e:
        logger.error(f"PDF 导出失败: {e}")
        raise HTTPException(status_code=500, detail="PDF服务暂不可用或发生渲染错误")
