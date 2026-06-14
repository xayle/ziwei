import json
import pathlib
from typing import Any

from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/api/v1/rules", tags=["rules"])

# Fallback path if not dynamically resolveable
RULES_PATH = pathlib.Path(__file__).parent.parent / "data" / "life_suggestions_rules.json"

# W9: 化劫规则文件路径
REMEDIES_RULES_PATH = pathlib.Path(__file__).parent.parent / "data" / "remedies_rules.json"


@router.get("")
async def get_rules():
    """获取所有生活化建议推理规则"""
    if not RULES_PATH.exists():
        return []
    with open(RULES_PATH, encoding="utf-8") as f:
        return json.load(f)


@router.put("")
async def update_rules(rules: list[dict[str, Any]]):
    """更新规则，并热重载后端引擎缓存"""
    try:
        with open(RULES_PATH, "w", encoding="utf-8") as f:
            json.dump(rules, f, ensure_ascii=False, indent=2)

        # 尝试热重载引擎里的全局变量
        import services.ziwei_engine.life_suggestions as mod

        mod._RULES = None  # Invalidate memory cache
        mod._load_rules()  # Reload into memory

        # B2: 失效八字计算缓存，防止旧规则结果残留
        try:
            from services.bazi_engine_service import invalidate_rule_cache

            invalidate_rule_cache()
        except Exception:
            pass

        return {"status": "success", "message": "规则已更新并热重载完成。"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────────────────────────────────────
# W9: 化劫规则管理  GET/PUT /api/v1/remedies-rules
# ─────────────────────────────────────────────────────────────────────────────


@router.get(
    "/remedies-rules",
    summary="W9 获取化劫规则列表",
    description="返回 data/remedies_rules.json 中的所有化劫规则，供客户端展示和编辑。",
)
async def get_remedies_rules() -> list[dict[str, Any]]:
    """获取化劫规则列表（data/remedies_rules.json）。"""
    if not REMEDIES_RULES_PATH.exists():
        return []
    with open(REMEDIES_RULES_PATH, encoding="utf-8") as f:
        return json.load(f)


@router.put(
    "/remedies-rules",
    summary="W9 更新化劫规则",
    description="覆盖写入 data/remedies_rules.json，并热重载内存缓存。",
)
async def update_remedies_rules(rules: list[dict[str, Any]]) -> dict[str, str]:
    """更新化劫规则，写入文件并热重载引擎缓存。"""
    # 简单校验：每条规则必须有 id 字段
    for i, rule in enumerate(rules):
        if "id" not in rule:
            raise HTTPException(
                status_code=422,
                detail=f"第 {i + 1} 条规则缺少 'id' 字段",
            )
    try:
        with open(REMEDIES_RULES_PATH, "w", encoding="utf-8") as f:
            json.dump(rules, f, ensure_ascii=False, indent=2)

        # 热重载：尝试清除引擎内的 remedies 规则缓存
        try:
            import services.ziwei_engine.remedies as _rem_mod

            if hasattr(_rem_mod, "_RULES"):
                _rem_mod._RULES = None  # type: ignore[attr-defined]
            if hasattr(_rem_mod, "_load_rules"):
                _rem_mod._load_rules()  # type: ignore[attr-defined]
        except Exception:
            pass  # 模块不存在时静默忽略

        # B2-兼容：同时令八字缓存失效
        try:
            from services.bazi_engine_service import invalidate_rule_cache

            invalidate_rule_cache()
        except Exception:
            pass

        return {"status": "success", "message": f"化劫规则已更新（共 {len(rules)} 条）并热重载完成。"}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
