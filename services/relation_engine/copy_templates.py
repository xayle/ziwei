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

INFERENCE_HEADINGS: dict[str, str] = {
    "couple": "感情相处建议",
    "friend": "友人相处建议",
    "parent_child": "亲子相处建议",
    "colleague": "职场协作建议",
    "business_partner": "合作与风控建议",
    "supervisor_subordinate": "上下级协作建议",
}

# R086 P2 — cross-template phrases that must not leak into another relation_type output.
CROSS_TEMPLATE_FORBIDDEN: dict[str, list[str]] = {
    "couple": ["合伙", "契约", "股权", "分红", "退出机制", "商务伙伴"],
    "friend": ["合伙", "股权", "契约", "婚嫁", "婚后", "夫妻宫缘"],
    "parent_child": ["合伙", "股权", "契约", "感情保鲜"],
    "colleague": ["婚嫁", "感情保鲜", "夫妻宫缘", "桃花"],
    "business_partner": ["感情保鲜", "婚嫁", "桃花", "夫妻宫缘"],
    "supervisor_subordinate": ["合伙", "婚嫁", "感情保鲜", "股权"],
}


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


def merged_forbidden_phrases(relation_type: str, type_cfg: dict[str, Any] | None = None) -> list[str]:
    base = list((type_cfg or {}).get("forbidden_copy") or [])
    extra = list(CROSS_TEMPLATE_FORBIDDEN.get(relation_type) or [])
    seen: set[str] = set()
    out: list[str] = []
    for phrase in base + extra:
        if phrase and phrase not in seen:
            seen.add(phrase)
            out.append(phrase)
    return out


def text_has_forbidden(text: str, forbidden: list[str]) -> bool:
    return bool(check_forbidden(text, forbidden))


def filter_palace_cross(
    crosses: list[dict[str, Any]],
    forbidden: list[str],
) -> list[dict[str, Any]]:
    kept: list[dict[str, Any]] = []
    for cross in crosses:
        blob = " ".join(str(cross.get(k) or "") for k in ("a_palace", "b_palace", "relation_tag", "summary"))
        if text_has_forbidden(blob, forbidden):
            continue
        row = dict(cross)
        row["summary"] = sanitize_text(str(row.get("summary") or ""), forbidden)
        kept.append(row)
    return kept


def build_inference_sections(
    relation_type: str,
    action_items: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    heading = INFERENCE_HEADINGS.get(relation_type, "相处建议")
    return [
        {
            "id": "advice",
            "heading": heading,
            "blocks": [{"text": item["text"]} for item in action_items[:5]],
        }
    ]


def finalize_relation_payload(
    payload: dict[str, Any],
    relation_type: str,
    type_cfg: dict[str, Any],
) -> dict[str, Any]:
    """R086 P2 — apply relation_type templates and forbidden-copy filters across payload."""
    forbidden = merged_forbidden_phrases(relation_type, type_cfg)
    heading = INFERENCE_HEADINGS.get(relation_type, "相处建议")

    payload["summary"] = sanitize_text(str(payload.get("summary") or ""), forbidden)

    for card in payload.get("summary_cards") or []:
        card["text"] = sanitize_text(str(card.get("text") or ""), forbidden)

    for dim in payload.get("dimensions") or []:
        dim["description"] = sanitize_text(str(dim.get("description") or ""), forbidden)
        dim["label"] = sanitize_text(str(dim.get("label") or ""), forbidden)

    payload["palace_cross"] = filter_palace_cross(list(payload.get("palace_cross") or []), forbidden)

    for node in payload.get("timeline") or []:
        node["summary"] = sanitize_text(str(node.get("summary") or ""), forbidden)
        node["label"] = sanitize_text(str(node.get("label") or ""), forbidden)

    filtered_actions: list[dict[str, Any]] = []
    for item in payload.get("action_items") or []:
        text = sanitize_text(str(item.get("text") or ""), forbidden)
        if text and not text_has_forbidden(text, forbidden):
            filtered_actions.append({**item, "text": text})
    if not filtered_actions:
        filtered_actions = build_action_items(relation_type, [])
    payload["action_items"] = filtered_actions

    layers = payload.setdefault("layers", {})
    inference = layers.setdefault("inference", {"collapsed_default": True, "sections": []})
    inference["sections"] = build_inference_sections(relation_type, filtered_actions)

    meta = payload.setdefault("meta", {})
    meta["summary_template_key"] = type_cfg.get("summary_template_key")
    meta["inference_heading"] = heading
    meta["template_id"] = relation_type

    return payload


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
