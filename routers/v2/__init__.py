"""routers/v2 — API v2 路由包."""
from __future__ import annotations

from fastapi import APIRouter

from .verify import router as verify_router

router = APIRouter()
router.include_router(verify_router)
