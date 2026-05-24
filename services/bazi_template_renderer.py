"""
services/bazi_template_renderer.py
────────────────────────────────────
Jinja2 模板渲染层（Phase C2）。

功能：
1. 加载并缓存 data/bazi_templates_samples.json（样本库）
2. 根据 BaziFullResponse 找到最相似的样本（geju_name 精确 → yongshen 重合度最高）
3. 渲染 services/templates/bazi_summary.j2，生成 rendered_facts 字符串
   供后续 generate_bazi_interpretation(rendered_facts, evidence_snippets) 使用

公开接口：
    render_summary(bazi_result: BaziFullResponse, evidence_snippets: list[dict]) -> str
"""

from __future__ import annotations

from functools import lru_cache
import json
import logging
import os
from typing import Any, Optional

logger = logging.getLogger(__name__)

# ─────────────────────────── 样本加载 ────────────────────────────────────


@lru_cache(maxsize=1)
def _load_samples() -> list[dict]:
    """加载并缓存 data/bazi_templates_samples.json。"""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    path = os.path.join(base_dir, "data", "bazi_templates_samples.json")
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        logger.warning("bazi_templates_samples.json not found at %s", path)
        return []
    except json.JSONDecodeError as e:
        logger.error("bazi_templates_samples.json JSON error: %s", e)
        return []


def _find_best_sample(
    geju_name: str,
    yongshen_favor: list[str],
    strength_tier: str,
) -> Optional[dict]:
    """
    按优先级找最相似样本：
    1. geju_name 精确匹配（再按 yongshen_favor 重合度排序，取最高）
    2. 若无 geju_name 匹配，尝试 strength tier 同类中 yongshen 重合最高
    3. 都没有则返回 None
    """
    samples = _load_samples()
    if not samples:
        return None

    def _overlap(sample: dict) -> int:
        """计算 yongshen_favor 与样本 favor 字段的重合数。"""
        s_favor = sample.get("yongshen_favor") or sample.get("favor") or []
        if isinstance(s_favor, str):
            s_favor = [x.strip() for x in s_favor.replace("、", ",").split(",") if x.strip()]
        return len(set(yongshen_favor) & set(s_favor))

    # 策略 1：geju_name 精确匹配
    geju_matches = [s for s in samples if s.get("geju_name") == geju_name]
    if geju_matches:
        return max(geju_matches, key=_overlap)

    # 策略 2：strength_tier 同类匹配
    strength_map = {
        "strong": ["strong", "very_strong", "身强", "旺"],
        "weak": ["weak", "very_weak", "身弱", "弱"],
        "neutral": ["neutral", "中和", "平"],
    }
    peer_tiers = strength_map.get(strength_tier, [strength_tier])
    tier_matches = [
        s for s in samples
        if s.get("strength") in peer_tiers or s.get("strength_tier") in peer_tiers
    ]
    if tier_matches:
        return max(tier_matches, key=_overlap)

    return None


# ─────────────────────────── Jinja2 环境 ─────────────────────────────────


@lru_cache(maxsize=1)
def _get_jinja_env():
    """构建并缓存 Jinja2 Environment，指向 services/templates/。"""
    try:
        from jinja2 import Environment, FileSystemLoader, select_autoescape

        templates_dir = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "templates"
        )
        env = Environment(
            loader=FileSystemLoader(templates_dir),
            autoescape=select_autoescape(enabled_extensions=()),  # 纯文本，不做 HTML escape
            trim_blocks=True,
            lstrip_blocks=True,
        )
        return env
    except ImportError:
        logger.error("Jinja2 not installed; install with: pip install jinja2")
        return None


def _render_template(template_name: str, ctx: dict) -> str:
    """安全渲染指定 Jinja2 模板，出错时返回空字符串并记录日志。"""
    env = _get_jinja_env()
    if env is None:
        return ""
    try:
        tmpl = env.get_template(template_name)
        return tmpl.render(**ctx)
    except Exception as exc:  # noqa: BLE001
        logger.error("Jinja2 render error for %s: %s", template_name, exc)
        return ""


# ─────────────────────────── 主入口 ──────────────────────────────────────


def render_summary(bazi_result: Any, evidence_snippets: list[dict]) -> str:
    """
    将 BaziFullResponse 渲染为 rendered_facts 字符串供 LLM 使用。

    参数：
        bazi_result      : BaziFullResponse  instance
        evidence_snippets: list[dict]，来自 evidence_retriever.fetch_evidence()
    返回：
        str  — Jinja2 渲染后的事实摘要，一般 300–600 字
    """
    # ── 提取字段 ──
    geju = getattr(bazi_result, "geju", None)
    yongshen = getattr(bazi_result, "yongshen", None)
    strength = getattr(bazi_result, "day_master_strength", None)
    pillars = getattr(bazi_result, "pillars_primary", None)
    rule_matches = list(getattr(bazi_result, "rule_matches", []) or [])
    shensha = getattr(bazi_result, "shensha", None)

    geju_name: str = getattr(geju, "geju_name", "") if geju else ""
    geju_level: str = getattr(geju, "geju_level", "") if geju else ""
    geju_broken: bool = bool(getattr(geju, "is_broken", False)) if geju else False

    favor_list: list[str] = list(getattr(yongshen, "favor", []) or []) if yongshen else []
    avoid_list: list[str] = list(getattr(yongshen, "avoid", []) or []) if yongshen else []
    rationale: str = getattr(yongshen, "rationale", "") or "" if yongshen else ""

    strength_tier: str = getattr(strength, "tier", "neutral") if strength else "neutral"
    strength_score: float = float(getattr(strength, "score", 0.0)) if strength else 0.0

    day_stem: str = ""
    if pillars:
        day_pillar = getattr(pillars, "day", None)
        day_stem = getattr(day_pillar, "stem", "") if day_pillar else ""

    # ── 序列化 pillars 为 dict ──
    def _pillar_to_dict(p: Any) -> dict:
        return {
            "stem": getattr(p, "stem", ""),
            "branch": getattr(p, "branch", ""),
        }

    pillars_dict: Optional[dict] = None
    if pillars:
        pillars_dict = {
            "year": _pillar_to_dict(getattr(pillars, "year", None)),
            "month": _pillar_to_dict(getattr(pillars, "month", None)),
            "day": _pillar_to_dict(getattr(pillars, "day", None)),
            "hour": _pillar_to_dict(getattr(pillars, "hour", None)),
        }

    # ── rule_matches 序列化（可能是 dict 或 Pydantic model）──
    def _rm_to_dict(rm: Any) -> dict:
        if isinstance(rm, dict):
            return rm
        return {
            "rule_id": getattr(rm, "rule_id", ""),
            "name": getattr(rm, "name", ""),
            "flags": list(getattr(rm, "flags", []) or []),
            "evidence_text": getattr(rm, "evidence_text", ""),
            "classic_hint": getattr(rm, "classic_hint", ""),
        }

    rule_matches_dicts = [_rm_to_dict(rm) for rm in rule_matches]

    # ── 查找最佳样本 ──
    sample = _find_best_sample(geju_name, favor_list, strength_tier)

    # ── 构建模板上下文 ──
    ctx = {
        "day_stem": day_stem,
        "geju_name": geju_name or "无格",
        "geju_level": geju_level or "无格",
        "geju_broken": geju_broken,
        "yongshen_favor": "、".join(favor_list) if favor_list else "待推断",
        "yongshen_avoid": "、".join(avoid_list) if avoid_list else "",
        "yongshen_rationale": rationale,
        "strength_tier": strength_tier,
        "strength_score": strength_score,
        "rule_matches": rule_matches_dicts,
        "evidence_snippets": evidence_snippets or [],
        "sample": sample,
        "pillars": pillars_dict,
    }

    rendered = _render_template("bazi_summary.j2", ctx)

    # ── Fallback：若渲染失败则返回纯文本摘要 ──
    if not rendered.strip():
        lines = [
            f"日主：{day_stem}（{strength_tier}）",
            f"格局：{geju_name or '无格'}（{geju_level}）{'【破格】' if geju_broken else ''}",
            f"喜用神：{ctx['yongshen_favor']}",
            f"忌神：{ctx['yongshen_avoid'] or '无'}",
        ]
        if rule_matches_dicts:
            lines.append("命中规则：" + " | ".join(r["name"] for r in rule_matches_dicts[:5]))
        rendered = "\n".join(lines)

    return rendered
