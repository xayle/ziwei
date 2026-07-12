"""Relation-type copy templates and forbidden phrase checks."""

from __future__ import annotations

from typing import Any

SUMMARY_TEMPLATES: dict[str, str] = {
    "couple": "有缘相聚，宜沟通与规则并重；分维见日支与财帛/夫妻宫。",
    "friend": "志趣可互补，宜尊重边界；分维见交友宫与迁移。",
    "parent_child": "代际差异需耐心，宜规则清晰；分维见子女宫与父母宫。",
    "colleague": "协作看官禄与喜忌，宜分工明确、减少内耗。",
    "business_partner": "合伙重财帛与契约，宜账目清晰、风险共担。",
    "supervisor_subordinate": "上下级看权责与官杀，宜目标对齐、反馈及时。",
}

GRADE_LABELS = [
    (85, "上上"),
    (70, "上"),
    (50, "中"),
    (30, "下"),
    (0, "下下"),
]


def score_to_grade(score: float) -> str:
    for threshold, label in GRADE_LABELS:
        if score >= threshold:
            return label
    return "下下"


def build_summary(relation_type: str, combined_score: float, conflict_hint: str = "") -> str:
    base = SUMMARY_TEMPLATES.get(relation_type, "合盘仅供参考，请结合实际情况。")
    grade = score_to_grade(combined_score)
    text = f"综合 {combined_score:.1f} 分（{grade}）。{base}"
    if conflict_hint:
        text += f" {conflict_hint}"
    return text[:280]


def check_forbidden(text: str, forbidden: list[str]) -> list[str]:
    return [phrase for phrase in forbidden if phrase in text]


def sanitize_text(text: str, forbidden: list[str]) -> str:
    out = text
    for phrase in forbidden:
        out = out.replace(phrase, "")
    return out.strip()


def build_action_items(relation_type: str, conflicts: list[str]) -> list[dict[str, Any]]:
    common = [
        {"id": "act-communicate", "text": "固定每周一次深度沟通，记录共识与分歧", "priority": "P0"},
        {"id": "act-boundary", "text": "明确各自责任边界，减少隐性期待", "priority": "P1"},
    ]
    type_specific: dict[str, list[dict[str, Any]]] = {
        "couple": [
            {"id": "act-couple-finance", "text": "共同制定财务规则（账户、大额支出协商）", "priority": "P0"},
        ],
        "friend": [
            {"id": "act-friend-space", "text": "尊重私人时间与社交圈，避免过度依赖", "priority": "P0"},
        ],
        "parent_child": [
            {"id": "act-parent-routine", "text": "建立可预期的作息与规则，减少情绪对抗", "priority": "P0"},
        ],
        "colleague": [
            {"id": "act-work-handoff", "text": "文档化交接与决策记录，避免口头约定", "priority": "P0"},
        ],
        "business_partner": [
            {"id": "act-biz-contract", "text": "书面化股权、分红与退出机制", "priority": "P0"},
        ],
        "supervisor_subordinate": [
            {"id": "act-sup-feedback", "text": "设定双周一对一反馈，对齐目标与资源", "priority": "P0"},
        ],
    }
    items = common + type_specific.get(relation_type, [])
    if conflicts:
        items.insert(
            0,
            {
                "id": "act-resolve-conflict",
                "text": f"优先处理：{conflicts[0][:80]}",
                "priority": "P0",
            },
        )
    return items[:8]
