"""
services/event_rule_matcher.py — 事件规则匹配器

从 data/event_rules.json 加载规则素材，根据信号 rule_id 列表
查找对应的：古籍依据、现实表现、预兆、建议、avoid_overclaim。
"""
from __future__ import annotations

import json
import logging
import os
from functools import lru_cache
from typing import Any, Optional

from app.schemas.event_prediction import ClassicalNote

logger = logging.getLogger(__name__)

_RULES_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                           "data", "event_rules.json")


@lru_cache(maxsize=1)
def _load_rules() -> list[dict]:
    """加载 event_rules.json（进程内缓存，模块级别）"""
    try:
        with open(_RULES_PATH, encoding="utf-8") as f:
            data = json.load(f)
        logger.info("Loaded %d event rules from %s", len(data), _RULES_PATH)
        return data
    except Exception as exc:
        logger.error("Failed to load event_rules.json: %s", exc)
        return []


@lru_cache(maxsize=1)
def _rules_by_id() -> dict[str, dict]:
    return {r["id"]: r for r in _load_rules()}


def get_subtypes_for_rule_ids(rule_ids: list[str]) -> list[str]:
    """根据 rule_id 列表，聚合对应的所有 subtypes（去重保序）"""
    by_id = _rules_by_id()
    result: list[str] = []
    seen: set[str] = set()
    for rid in rule_ids:
        rule = by_id.get(rid)
        if rule:
            for st in (rule.get("subtypes") or []):
                if st not in seen:
                    seen.add(st)
                    result.append(st)
    return result


def get_materials_for_signals(rule_ids: list[str]) -> dict[str, Any]:
    """
    根据 rule_id 列表，从匹配规则中聚合素材：
      - manifestations:   list[str]  可能的现实表现
      - omens:            list[str]  现实预兆
      - advice:           list[str]  应对建议
      - classical_notes:  list[ClassicalNote]
      - avoid_overclaim:  Optional[str]  （取最严格的一条）
    """
    by_id = _rules_by_id()
    manifestations: list[str] = []
    omens:          list[str] = []
    advice:         list[str] = []
    classical_notes: list[ClassicalNote] = []
    avoid_overclaims: list[str] = []

    seen_m: set[str] = set()
    seen_o: set[str] = set()
    seen_a: set[str] = set()
    seen_c: set[str] = set()

    # 高严重度规则优先
    _SEV_ORDER = {"high": 0, "medium": 1, "low": 2}
    matched = [by_id[rid] for rid in rule_ids if rid in by_id]
    matched.sort(key=lambda r: _SEV_ORDER.get(r.get("severity", "low"), 2))

    for rule in matched:
        for m in (rule.get("possible_manifestations") or []):
            if m not in seen_m:
                seen_m.add(m)
                manifestations.append(m)
        for o in (rule.get("omens") or []):
            if o not in seen_o:
                seen_o.add(o)
                omens.append(o)
        for ad in (rule.get("advice") or []):
            if ad not in seen_a:
                seen_a.add(ad)
                advice.append(ad)
        cb = rule.get("classical_basis", "")
        cs = rule.get("classical_source", "")
        if cb and cb not in seen_c:
            seen_c.add(cb)
            classical_notes.append(ClassicalNote(basis=cb, source=cs))
        avo = rule.get("avoid_overclaim")
        if avo:
            avoid_overclaims.append(avo)

    # 截取合理数量
    return {
        "manifestations":  manifestations[:6],
        "omens":           omens[:5],
        "advice":          advice[:5],
        "classical_notes": classical_notes[:3],
        "avoid_overclaim": avoid_overclaims[0] if avoid_overclaims else None,
    }


def match_rules_by_category(category: str, signal_keys: list[str]) -> list[dict]:
    """
    按 category + 信号关键词模糊匹配规则（备用方案，当没有 rule_id 时使用）。
    matching: signal_key 中任一关键词出现在 trigger_conditions 文本中
    """
    rules = [r for r in _load_rules() if r.get("category") == category]
    matched: list[dict] = []
    for rule in rules:
        conditions_text = " ".join(rule.get("trigger_conditions") or []).lower()
        for sk in signal_keys:
            # 将 signal_key 转换为搜索词
            keywords = sk.replace("_", " ").split()
            if any(kw in conditions_text for kw in keywords if len(kw) > 2):
                matched.append(rule)
                break
    return matched


def get_followup_questions(event_type: str) -> list[str]:
    """返回该事件类别的追问问题列表（从 followup_service 读取）"""
    from services.followup_service import FOLLOWUP_MAP
    return FOLLOWUP_MAP.get(event_type, [])
