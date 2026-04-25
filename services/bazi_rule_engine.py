"""
services/bazi_rule_engine.py
────────────────────────────
八字规则引擎：加载 data/bazi_rules.json，根据八字计算结果匹配规则，
返回匹配的 RuleMatchModel 列表，用于给 LLM 提供结构化的规则依据。

触发器结构（W2修复 all/any/none）：
    trigger = {
        "all": [...],   # 所有条件都满足
        "any": [...],   # 至少一个条件满足（可省略）
        "none": [...],  # 所有条件都不满足（可省略）
    }
    每个条件形如：
        {"field": "geju.geju_name", "op": "eq", "value": "正官格"}
        {"field": "yongshen.favor", "op": "contains", "value": "火"}
        {"field": "geju.geju_level", "op": "in", "value": ["上格","中格"]}
"""

from __future__ import annotations

import json
import logging
import os
from functools import lru_cache
from typing import Any, Optional

logger = logging.getLogger(__name__)

# ─────────────────────────── 规则加载 ────────────────────────────────────


@lru_cache(maxsize=1)
def _load_rules() -> list[dict]:
    """加载并缓存 data/bazi_rules.json。"""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    rules_path = os.path.join(base_dir, "data", "bazi_rules.json")
    try:
        with open(rules_path, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error("bazi_rules.json not found at %s", rules_path)
        return []
    except json.JSONDecodeError as e:
        logger.error("bazi_rules.json JSON parse error: %s", e)
        return []


# ─────────────────────────── 上下文构建 ──────────────────────────────────


def _build_context(
    geju: Any | None,
    yongshen: Any,
    shensha: list[Any] | None,
) -> dict:
    """把 Pydantic 模型转化为规则引擎可以 getattr 的平坦字典树。"""
    ctx: dict = {}

    # ── geju ──
    if geju is not None:
        ctx["geju"] = {
            "geju_name": getattr(geju, "geju_name", ""),
            "geju_level": getattr(geju, "geju_level", ""),
            "is_broken": getattr(geju, "is_broken", False),
        }
    else:
        ctx["geju"] = {
            "geju_name": "",
            "geju_level": "",
            "is_broken": False,
        }

    # ── yongshen ──
    if yongshen is not None:
        ctx["yongshen"] = {
            "favor": list(getattr(yongshen, "favor", []) or []),
            "avoid": list(getattr(yongshen, "avoid", []) or []),
        }
    else:
        ctx["yongshen"] = {"favor": [], "avoid": []}

    # ── shensha：列表中每个元素展开为 dict，并拼接 name 列表用于 contains 匹配 ──
    if shensha:
        ctx["shensha"] = {
            "name": [
                getattr(s, "name", "") for s in shensha if getattr(s, "name", "")
            ]
        }
    else:
        ctx["shensha"] = {"name": []}

    return ctx


def _resolve_field(ctx: dict, field_path: str) -> Any:
    """
    按点分路径取值，支持列表字段。
    例如：field="yongshen.favor" → ctx["yongshen"]["favor"]
    """
    parts = field_path.split(".")
    node: Any = ctx
    for p in parts:
        if isinstance(node, dict):
            node = node.get(p)
        else:
            return None
    return node


# ─────────────────────────── 条件求值 ────────────────────────────────────


def _eval_condition(cond: dict, ctx: dict) -> bool:
    """
    评估单个条件。
    支持的 op：
        eq       - 等于
        ne       - 不等于
        contains - 列表包含 / 字符串子串
        in       - 字段值在 value（列表）中
    """
    field_val = _resolve_field(ctx, cond.get("field", ""))
    op = cond.get("op", "eq")
    expected = cond.get("value")

    if op == "eq":
        return field_val == expected

    if op == "ne":
        return field_val != expected

    if op == "contains":
        if isinstance(field_val, list):
            return expected in field_val
        if isinstance(field_val, str):
            return str(expected) in field_val
        return False

    if op == "in":
        if not isinstance(expected, list):
            expected = [expected]
        if field_val is None:
            return False
        return field_val in expected

    logger.warning("bazi_rule_engine: unknown op '%s'", op)
    return False


def _eval_trigger(trigger: dict, ctx: dict) -> bool:
    """
    评估触发器（W2 all/any/none 结构）。
    - all 块：所有条件为 True → 才满足
    - any 块：至少一个条件为 True → 才满足（省略则视为 True）
    - none 块：所有条件均为 False → 才满足（省略则视为 True）
    """
    # ── all ──
    for cond in trigger.get("all", []):
        if not _eval_condition(cond, ctx):
            return False

    # ── any ──
    any_conditions = trigger.get("any", [])
    if any_conditions and not any(_eval_condition(c, ctx) for c in any_conditions):
        return False

    # ── none ──
    for cond in trigger.get("none", []):
        if _eval_condition(cond, ctx):
            return False

    return True


# ─────────────────────────── 主入口 ──────────────────────────────────────


def match_rules(
    geju: Any | None,
    yongshen: Any,
    shensha: Optional[list[Any]] = None,
) -> list[dict]:
    """
    根据格局/用神/神煞信息匹配规则，返回匹配命中的规则列表（dict格式）。
    每条记录格式：
        {
            "rule_id": str,
            "name": str,
            "flags": list[str],
            "evidence_text": str,   # evidence_template 填充 yongshen_favor
            "classic_hint": str,
            "disclaimer": str,
        }
    """
    rules = _load_rules()
    if not rules:
        return []

    ctx = _build_context(geju, yongshen, shensha)
    yongshen_favor_str = "、".join(ctx["yongshen"]["favor"]) or "待定"

    matched: list[dict] = []
    for rule in rules:
        trigger = rule.get("trigger", {})
        try:
            if _eval_trigger(trigger, ctx):
                # 填充 evidence_template 中的占位符
                tmpl = rule.get("evidence_template", "")
                evidence_text = tmpl.format(yongshen_favor=yongshen_favor_str)
                matched.append(
                    {
                        "rule_id": rule["id"],
                        "name": rule["name"],
                        "flags": rule.get("flags", []),
                        "evidence_text": evidence_text,
                        "classic_hint": rule.get("classic_hint", ""),
                        "disclaimer": rule.get("disclaimer", "仅供学术研究参考"),
                    }
                )
        except Exception as exc:  # noqa: BLE001
            logger.warning("rule %s eval error: %s", rule.get("id"), exc)

    logger.debug("bazi_rule_engine: %d/%d rules matched", len(matched), len(rules))
    return matched
