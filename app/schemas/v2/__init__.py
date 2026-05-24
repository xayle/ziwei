"""app/schemas/v2 — API v2 专属 Schema 包."""
from __future__ import annotations

from .verify import (
    ResponseMeta,
    VerifyRequestV2,
    VerifyResponseFull,
    VerifyResponseMinimal,
    VerifyResponseV2,
)

__all__ = [
    "VerifyRequestV2",
    "ResponseMeta",
    "VerifyResponseFull",
    "VerifyResponseMinimal",
    "VerifyResponseV2",
]
