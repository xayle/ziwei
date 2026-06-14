"""
塔罗牌 API 路由（§7.2）

POST /api/v1/tarot/draw       — 单张抽牌（服务端随机）
POST /api/v1/tarot/spread     — N 张牌阵
GET  /api/v1/tarot/cards      — 返回所有大阿尔卡那牌义
GET  /api/v1/tarot/card/{num} — 查询单张牌义（0-21）
"""

from __future__ import annotations

import random

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/v1/tarot", tags=["塔罗"])

# ─────────────────────────────────────────────────────────────────────────────
# 大阿尔卡那数据（22 张）
# ─────────────────────────────────────────────────────────────────────────────

MAJOR_ARCANA: list[dict] = [
    {
        "num": 0,
        "name": "The Fool",
        "cn": "愚者",
        "emoji": "🃏",
        "keyword": "新的开始·纯真·冒险",
        "upright": "踏上全新旅程，以开放之心拥抱未知，充满纯真勇气。",
        "reversed": "鲁莽草率，逃避现实，缺乏方向与计划。",
        "advice": "勇敢踏出第一步，相信旅途自有引导。",
        "color": "#f59e0b",
    },
    {
        "num": 1,
        "name": "The Magician",
        "cn": "魔术师",
        "emoji": "🪄",
        "keyword": "意志力·行动·创造",
        "upright": "拥有实现目标所需一切资源，意志坚定，行动力强。",
        "reversed": "操控他人，才华空转，缺乏专注。",
        "advice": "集中意志，将内在潜能化为具体行动。",
        "color": "#ef4444",
    },
    {
        "num": 2,
        "name": "The High Priestess",
        "cn": "女祭司",
        "emoji": "🌙",
        "keyword": "直觉·内在智慧·神秘",
        "upright": "聆听内心直觉，深藏的智慧正在提示你答案。",
        "reversed": "封闭内心，忽视直觉，秘密与隐藏。",
        "advice": "静下心来，内在的声音才是你真正的向导。",
        "color": "#6366f1",
    },
    {
        "num": 3,
        "name": "The Empress",
        "cn": "女皇",
        "emoji": "🌸",
        "keyword": "丰盛·创造力·滋养",
        "upright": "生命力旺盛，丰盛到来，创造与自然之美。",
        "reversed": "依赖、过度保护，或缺乏自我价值。",
        "advice": "拥抱自然节律，滋养自己与周围的人。",
        "color": "#22c55e",
    },
    {
        "num": 4,
        "name": "The Emperor",
        "cn": "皇帝",
        "emoji": "👑",
        "keyword": "权威·稳定·秩序",
        "upright": "建立秩序与结构，以权威和耐心掌控局面。",
        "reversed": "专制、刚愎自用，或缺乏掌控力。",
        "advice": "建立清晰边界和规则，成为自己生活的主导者。",
        "color": "#f97316",
    },
    {
        "num": 5,
        "name": "The Hierophant",
        "cn": "教皇",
        "emoji": "⛪",
        "keyword": "传统·信仰·指导",
        "upright": "遵循传统与制度，寻求精神指引和道德秩序。",
        "reversed": "固执于旧规，反叛权威，盲目追从。",
        "advice": "在传统智慧中寻找指引，同时保持独立判断。",
        "color": "#8b5cf6",
    },
    {
        "num": 6,
        "name": "The Lovers",
        "cn": "恋人",
        "emoji": "💑",
        "keyword": "爱情·选择·价值观",
        "upright": "深刻的情感连接，重要的价值观选择到来。",
        "reversed": "关系失衡，与内心价值脱节，错误选择。",
        "advice": "跟随内心真实的渴望做出选择。",
        "color": "#ec4899",
    },
    {
        "num": 7,
        "name": "The Chariot",
        "cn": "战车",
        "emoji": "⚔️",
        "keyword": "意志力·掌控·胜利",
        "upright": "以坚定意志和自律驾驭局面，走向胜利。",
        "reversed": "失控、方向混乱，强行为之。",
        "advice": "保持专注与自律，以意志力克服前进的阻碍。",
        "color": "#3b82f6",
    },
    {
        "num": 8,
        "name": "Strength",
        "cn": "力量",
        "emoji": "🦁",
        "keyword": "内在力量·耐心·勇气",
        "upright": "以柔克刚，温柔而坚韧，内在力量战胜困境。",
        "reversed": "怀疑自我，压抑本能，软弱与怯懦。",
        "advice": "相信内在的勇气，用温柔而坚定的方式面对挑战。",
        "color": "#f97316",
    },
    {
        "num": 9,
        "name": "The Hermit",
        "cn": "隐者",
        "emoji": "🏔️",
        "keyword": "内省·独处·智慧",
        "upright": "向内探索，智慧从沉思与孤独中涌现。",
        "reversed": "孤立无援，拒绝建议，与世隔绝。",
        "advice": "给自己独处的时间，答案就在内心深处。",
        "color": "#475569",
    },
    {
        "num": 10,
        "name": "Wheel of Fortune",
        "cn": "命运之轮",
        "emoji": "☸️",
        "keyword": "命运·循环·转机",
        "upright": "命运转轮开始运转，好运与机遇随之而来。",
        "reversed": "逆境来临，感到命运摆布，抵制变化。",
        "advice": "顺应宇宙节律，把握变化中的机遇。",
        "color": "#f59e0b",
    },
    {
        "num": 11,
        "name": "Justice",
        "cn": "正义",
        "emoji": "⚖️",
        "keyword": "公正·真相·因果",
        "upright": "公平的裁断到来，因果法则起作用。",
        "reversed": "不公平、不诚实，逃避责任。",
        "advice": "诚实面对自己的行动，因果终将显现。",
        "color": "#6366f1",
    },
    {
        "num": 12,
        "name": "The Hanged Man",
        "cn": "倒吊人",
        "emoji": "🙃",
        "keyword": "暂停·牺牲·新视角",
        "upright": "暂时放弃掌控，以全新视角看待局面。",
        "reversed": "无谓的牺牲，拖延，缺乏放手的勇气。",
        "advice": "放慢节奏，换个视角，静候时机。",
        "color": "#0ea5e9",
    },
    {
        "num": 13,
        "name": "Death",
        "cn": "死神",
        "emoji": "💀",
        "keyword": "转变·终结·重生",
        "upright": "旧事即将画上句号，新阶段的开始。",
        "reversed": "抗拒改变，拖延转化，恐惧结束。",
        "advice": "放下执念，迎接蜕变，新生从旧的终结中诞生。",
        "color": "#1e293b",
    },
    {
        "num": 14,
        "name": "Temperance",
        "cn": "节制",
        "emoji": "🕊️",
        "keyword": "平衡·调和·耐心",
        "upright": "耐心调和，寻找中道，身心逐渐趋于平衡。",
        "reversed": "不节制，极端，内外失衡。",
        "advice": "以温和适度调整步伐，一切都在流动均衡中。",
        "color": "#10b981",
    },
    {
        "num": 15,
        "name": "The Devil",
        "cn": "恶魔",
        "emoji": "😈",
        "keyword": "束缚·执念·物质",
        "upright": "受物质或恐惧所束缚，执念于世俗欲望。",
        "reversed": "挣脱束缚，重获自由，认清幻象。",
        "advice": "认识到束缚你的是什么，觉察是自由的开始。",
        "color": "#dc2626",
    },
    {
        "num": 16,
        "name": "The Tower",
        "cn": "高塔",
        "emoji": "⚡",
        "keyword": "颠覆·突变·启示",
        "upright": "突如其来的颠覆，旧有秩序崩塌，真相显现。",
        "reversed": "抗拒必要的改变，内在危机悄然积聚。",
        "advice": "接受必要的崩塌，它是更好重建的前奏。",
        "color": "#b45309",
    },
    {
        "num": 17,
        "name": "The Star",
        "cn": "星星",
        "emoji": "⭐",
        "keyword": "希望·信念·疗愈",
        "upright": "充满希望，内心平静，宇宙在守护你。",
        "reversed": "失去信念，绝望感，与内在光断联。",
        "advice": "保持希望，宇宙的恩惠正在流向你。",
        "color": "#0ea5e9",
    },
    {
        "num": 18,
        "name": "The Moon",
        "cn": "月亮",
        "emoji": "🌕",
        "keyword": "幻象·潜意识·直觉",
        "upright": "进入潜意识领域，幻象与恐惧需要辨别。",
        "reversed": "幻象消散，困惑逐渐明朗。",
        "advice": "倾听梦境与直觉，但不完全迷失其中。",
        "color": "#6366f1",
    },
    {
        "num": 19,
        "name": "The Sun",
        "cn": "太阳",
        "emoji": "☀️",
        "keyword": "喜悦·活力·成功",
        "upright": "充满活力、喜悦与光明，成功与幸福到来。",
        "reversed": "遮蔽与延迟，过于关注小事。",
        "advice": "张开双臂拥抱生命的光，快乐就在此刻。",
        "color": "#f59e0b",
    },
    {
        "num": 20,
        "name": "Judgement",
        "cn": "审判",
        "emoji": "📯",
        "keyword": "觉醒·审判·召唤",
        "upright": "更高的召唤响起，灵魂的觉醒与自我更新。",
        "reversed": "自我怀疑，拒绝召唤，停滞不前。",
        "advice": "倾听内心深处的召唤，勇敢踏上更高使命之路。",
        "color": "#8b5cf6",
    },
    {
        "num": 21,
        "name": "The World",
        "cn": "世界",
        "emoji": "🌍",
        "keyword": "完成·成就·整合",
        "upright": "一个重要循环圆满完成，充满成就感与整合。",
        "reversed": "缺少收尾，半途而废，对完成感不满足。",
        "advice": "庆祝你的旅程成就，带着完整感迎接下一段。",
        "color": "#10b981",
    },
]

CARD_BY_NUM: dict[int, dict] = {c["num"]: c for c in MAJOR_ARCANA}

# ─────────────────────────────────────────────────────────────────────────────
# 响应模型
# ─────────────────────────────────────────────────────────────────────────────


class TarotCard(BaseModel):
    num: int
    name: str
    cn: str
    emoji: str
    keyword: str
    upright: str
    reversed: str
    advice: str
    color: str


class DrawnCard(BaseModel):
    card: TarotCard
    is_reversed: bool
    interpretation: str


class DrawResponse(BaseModel):
    card: DrawnCard
    context: str | None = None


class SpreadRequest(BaseModel):
    count: int = Field(3, ge=1, le=10, description="抽取张数（1-10）")
    context: str | None = Field(None, description="可选上下文说明，如「感情」「事业」等")
    allow_reversed: bool = Field(True, description="是否允许逆位")


class SpreadPosition(BaseModel):
    position: str
    card: DrawnCard


class SpreadResponse(BaseModel):
    count: int
    positions: list[SpreadPosition]
    context: str | None = None


# ─────────────────────────────────────────────────────────────────────────────
# 工具函数
# ─────────────────────────────────────────────────────────────────────────────

THREE_CARD_POSITIONS = ["过去", "现在", "未来"]


def _draw_card(allow_reversed: bool = True) -> DrawnCard:
    card_data = random.choice(MAJOR_ARCANA)
    is_rev = allow_reversed and random.random() < 0.3
    card = TarotCard(**card_data)
    interpretation = card.reversed if is_rev else card.upright
    return DrawnCard(card=card, is_reversed=is_rev, interpretation=interpretation)


# ─────────────────────────────────────────────────────────────────────────────
# 端点
# ─────────────────────────────────────────────────────────────────────────────


@router.post("/draw", response_model=DrawResponse, summary="单张抽牌")
def draw_single(context: str | None = None) -> DrawResponse:
    """随机从大阿尔卡那中抽取一张牌，约 30% 概率逆位。"""
    return DrawResponse(card=_draw_card(), context=context)


@router.post("/spread", response_model=SpreadResponse, summary="N 张牌阵")
def draw_spread(req: SpreadRequest) -> SpreadResponse:
    """
    随机抽取 N 张牌并按位置分配。

    - 1 张：单牌指引
    - 3 张：过去 / 现在 / 未来
    - 其他：自动按序编号
    """
    cards = [_draw_card(req.allow_reversed) for _ in range(req.count)]
    if req.count == 3:
        positions = THREE_CARD_POSITIONS
    else:
        positions = [f"第{i + 1}张" for i in range(req.count)]

    return SpreadResponse(
        count=req.count,
        positions=[SpreadPosition(position=pos, card=card) for pos, card in zip(positions, cards)],
        context=req.context,
    )


@router.get("/cards", response_model=list[TarotCard], summary="获取所有大阿尔卡那牌义")
def list_cards() -> list[TarotCard]:
    """返回全部 22 张大阿尔卡那牌义列表（按编号升序）。"""
    return [TarotCard(**c) for c in MAJOR_ARCANA]


@router.get("/card/{num}", response_model=TarotCard, summary="查询单张牌义")
def get_card(num: int) -> TarotCard:
    """查询指定编号（0-21）大阿尔卡那牌的完整牌义。"""
    if num not in CARD_BY_NUM:
        raise HTTPException(404, f"牌号 {num} 不存在（大阿尔卡那编号 0~21）")
    return TarotCard(**CARD_BY_NUM[num])
