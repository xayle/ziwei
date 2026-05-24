"""
services/followup_service.py — 年份事件追问问题库

为每个事件类别提供 5 条常见追问，AI 咨询后展示在界面底部，
引导用户进行更深入的运势咨询。
"""
from __future__ import annotations

FOLLOWUP_MAP: dict[str, list[str]] = {
    "marriage": [
        "会不会有离婚的风险？",
        "哪几个月感情最不稳定？",
        "有什么具体的化解方式？",
        "感情上的主要矛盾在哪里？",
        "哪一年的婚姻运势最顺？",
    ],
    "wealth": [
        "哪一年财运最旺？",
        "今年适合创业或投资吗？",
        "哪类投资需要避开？",
        "如何防范破财的风险？",
        "什么时候收入提升最明显？",
    ],
    "property": [
        "上半年还是下半年置业更合适？",
        "贷款或资金压力大吗？",
        "会不会因家人意见拖延决策？",
        "哪一年买房时机最好？",
        "会不会多次看房但成交困难？",
    ],
    "career": [
        "什么时候跳槽或升职最有利？",
        "今年适合自主创业吗？",
        "贵人运在哪个方向？",
        "有被裁员或调岗的风险吗？",
        "哪个行业方向对我最有利？",
    ],
    "health": [
        "哪个季节需要重点保养？",
        "哪个脏腑系统最需要关注？",
        "什么时候精神压力最大？",
        "有什么具体的调养建议？",
        "有意外伤病的风险吗？",
    ],
}

# 中文展示名
EVENT_DISPLAY_NAMES: dict[str, str] = {
    "marriage": "婚姻感情",
    "wealth":   "财运财务",
    "property": "置业动产",
    "career":   "事业发展",
    "health":   "健康状态",
}


def get_followup_questions(event_type: str) -> list[str]:
    """返回指定事件类别的追问问题列表，最多 5 条。"""
    return FOLLOWUP_MAP.get(event_type, [])


def get_event_display_name(event_type: str) -> str:
    """返回事件类别的中文展示名。"""
    return EVENT_DISPLAY_NAMES.get(event_type, event_type)
