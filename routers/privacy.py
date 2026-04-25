"""
C1: GDPR 匿名化路由

POST /api/v1/users/me/anonymize  — 用户自助匿名化账户数据（204 No Content）

匿名化策略：
- User.email       → f"hashed_{sha256(email)[:12]}@deleted"
- User.username    → f"deleted_{user_id}"
- User.password_hash → ""
- User.is_active   → False
- Case.birth_dt_local → "0000-00-00T00:00:00"（清除出生时间）
- Case.lon          → 0.0（清除经度）
- Case.city         → None
- RefreshToken      → 物理删除 WHERE user_id=?
- AuditLog          → 不删除（保留用于合规审计）
"""
from __future__ import annotations

import hashlib
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session, select

from app.dependencies import RequiredUser
from app.models.base import RefreshToken, User
from app.models.case import Case
from db import get_session
from services.delegation_service import log_action

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/users", tags=["privacy"])


class AnonymizeConfirmRequest(BaseModel):
    confirm: str  # 必须填写 "ANONYMIZE" 以防误操作


@router.post(
    "/me/anonymize",
    status_code=204,
    summary="GDPR 用户数据匿名化（C1）",
    description=(
        "对当前登录用户的个人数据进行不可逆匿名化处理。\n"
        "- `email` → 哈希脱敏\n"
        "- `username` → `deleted_{id}`\n"
        "- `password_hash` → 空字符串（账户失效）\n"
        "- 案例出生时间、经度 → 清零\n"
        "- RefreshToken → 物理删除\n"
        "- AuditLog → 保留（合规要求）\n\n"
        "请求体需携带 `{ \"confirm\": \"ANONYMIZE\" }` 防误操作。"
    ),
)
def anonymize_user(
    body: AnonymizeConfirmRequest,
    current_user: RequiredUser,
    session: Session = Depends(get_session),
) -> None:
    """
    C1 GDPR 匿名化：
    1. 校验确认字符串
    2. 匿名化 User 字段
    3. 清除案例出生信息
    4. 物理删除 RefreshToken
    5. 写入审计日志
    """
    # 1. 确认操作
    if body.confirm != "ANONYMIZE":
        raise HTTPException(
            status_code=400,
            detail="请求体 confirm 字段必须为字符串 'ANONYMIZE' 方可执行匿名化",
        )

    user_id = current_user.id
    if user_id is None:
        raise HTTPException(status_code=400, detail="无法确定用户 ID")

    # 2. 匿名化 User 表
    user = session.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="用户不存在")
    if user.deleted_at is not None:
        raise HTTPException(status_code=410, detail="账户已被注销，无法再次匿名化")

    original_email = user.email
    email_hash = hashlib.sha256(original_email.encode()).hexdigest()[:16]
    user.email = f"hashed_{email_hash}@deleted"
    user.username = f"deleted_{user_id}"
    user.password_hash = ""
    user.is_active = False
    user.deleted_at = datetime.now(timezone.utc)
    session.add(user)

    # 3. 清除该用户所有案例的出生关键信息
    cases = session.exec(
        select(Case).where(Case.owner_id == user_id, Case.deleted_at.is_(None))  # type: ignore[union-attr]
    ).all()
    for case in cases:
        case.birth_dt_local = "0000-00-00T00:00:00"
        case.lon = 0.0
        case.city = None
        session.add(case)

    # 4. 物理删除 RefreshToken
    tokens = session.exec(
        select(RefreshToken).where(RefreshToken.user_id == user_id)
    ).all()
    for token in tokens:
        session.delete(token)

    # 5. 提交所有变更
    session.commit()

    # 6. 写入审计日志（匿名化不记录原始 email，仅记录 user_id）
    try:
        log_action(
            session=session,
            user_id=user_id,
            action="gdpr_anonymize",
            resource_type="user",
            resource_id=str(user_id),
            details={"cases_nulled": len(cases), "tokens_deleted": len(tokens)},
        )
        session.commit()
    except Exception as exc:
        logger.warning("GDPR audit log failed (non-blocking): %s", exc)

    logger.info("[C1 GDPR] user_id=%d anonymized; cases=%d tokens_deleted=%d",
                user_id, len(cases), len(tokens))
    # 204 No Content — FastAPI 自动处理 return None
