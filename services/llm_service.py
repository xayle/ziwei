"""
LLM 服务层 — §10 辅助解读草稿生成。

支持三种模式（自动检测环境变量）：
  1. OpenAI  (OPENAI_API_KEY)
  2. Anthropic (ANTHROPIC_API_KEY)
  3. Mock    (无 key → 模板生成，不调用任何 API)

环境变量：
  LLM_PROVIDER      = openai | anthropic | mock   （可强制指定）
  OPENAI_API_KEY    = sk-...
  OPENAI_MODEL      = gpt-4o-mini（默认）
  OPENAI_API_BASE   = https://api.openai.com（默认）
  ANTHROPIC_API_KEY = sk-ant-...
  ANTHROPIC_MODEL   = claude-3-haiku-20240307（默认）
  LLM_MAX_TOKENS    = 800（默认）
  LLM_TEMPERATURE   = 0.7（默认）
"""
from __future__ import annotations

import asyncio
from dataclasses import dataclass
from enum import Enum
import json
import logging
import os
import threading
import time
from typing import AsyncIterator

import httpx

logger = logging.getLogger(__name__)


# ─── Provider 枚举与配置 ─────────────────────────────────────────────────────

class LlmProviderType(str, Enum):
    OPENAI    = "openai"
    ANTHROPIC = "anthropic"
    MOCK      = "mock"


@dataclass
class LlmConfig:
    provider:    LlmProviderType
    model:       str
    api_key:     str = ""
    api_base:    str = ""
    max_tokens:  int = 1600
    temperature: float = 0.75


@dataclass
class LlmUsage:
    input_tokens:  int   = 0
    output_tokens: int   = 0
    cost_usd:      float = 0.0


@dataclass
class LlmResponse:
    text:           str
    provider:       str
    model:          str
    usage:          LlmUsage
    duration_secs:  float
    prompt_version: str
    is_fallback:    bool = False   # O6: 断路器打开时为 True


# ── O6: LLM 断路器状态 ────────────────────────────────────────────────────────────
_LLM_CIRCUIT_LOCK:          threading.Lock = threading.Lock()
_LLM_FAIL_COUNT:            int   = 0
_LLM_CIRCUIT_OPEN_UNTIL:    float = 0.0
_LLM_CIRCUIT_FAIL_THRESH:   int   = 3      # 连续 3 次失败 → 打开
_LLM_CIRCUIT_COOLDOWN:      int   = 600    # 10 分钟（秒）


def _llm_record_failure() -> None:
    """O6: 记录一次 LLM 失败，满阈值时打开断路器。"""
    global _LLM_FAIL_COUNT, _LLM_CIRCUIT_OPEN_UNTIL
    with _LLM_CIRCUIT_LOCK:
        _LLM_FAIL_COUNT += 1
        if _LLM_FAIL_COUNT >= _LLM_CIRCUIT_FAIL_THRESH:
            _LLM_CIRCUIT_OPEN_UNTIL = time.time() + _LLM_CIRCUIT_COOLDOWN
            _LLM_FAIL_COUNT = 0
            logger.warning(
                "[O6] LLM 断路器打开 %d 秒（连续 %d 次失败）",
                _LLM_CIRCUIT_COOLDOWN, _LLM_CIRCUIT_FAIL_THRESH,
            )


def _is_circuit_open() -> bool:
    """O6: 检查断路器是否处于打开状态（冷却期内）。

    - 返回 True  → 电路断开，调用方应使用 Mock fallback
    - 返回 False → 电路闭合（正常）或冷却期已过（half-open：重置并放行一次真实调用）
    """
    global _LLM_CIRCUIT_OPEN_UNTIL
    with _LLM_CIRCUIT_LOCK:
        if _LLM_CIRCUIT_OPEN_UNTIL <= 0:
            return False
        if time.time() < _LLM_CIRCUIT_OPEN_UNTIL:
            return True
        # 冷却期已过 → 进入 half-open：重置，允许一次真实调用
        _LLM_CIRCUIT_OPEN_UNTIL = 0.0
        logger.info("[O6] LLM 断路器冷却期已过，进入 half-open 状态，允许真实调用")
        return False


def _reset_circuit_for_test() -> None:
    """测试辅助：将断路器完全重置为闭合状态。

    仅供 pytest 使用，生产代码不应调用。
    """
    global _LLM_FAIL_COUNT, _LLM_CIRCUIT_OPEN_UNTIL
    with _LLM_CIRCUIT_LOCK:
        _LLM_FAIL_COUNT = 0
        _LLM_CIRCUIT_OPEN_UNTIL = 0.0


def get_llm_config() -> LlmConfig:
    """从环境变量检测可用的 LLM provider，按 openai → anthropic → mock 优先级。"""
    pv = os.getenv("LLM_PROVIDER", "").lower()
    mt = int(os.getenv("LLM_MAX_TOKENS", "1600"))
    tp = float(os.getenv("LLM_TEMPERATURE", "0.75"))

    if pv == "openai" or (pv == "" and os.getenv("OPENAI_API_KEY")):
        return LlmConfig(
            provider=LlmProviderType.OPENAI,
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            api_key=os.getenv("OPENAI_API_KEY", ""),
            api_base=os.getenv("OPENAI_API_BASE", "https://api.openai.com"),
            max_tokens=mt,
            temperature=tp,
        )
    if pv == "anthropic" or (pv == "" and os.getenv("ANTHROPIC_API_KEY")):
        return LlmConfig(
            provider=LlmProviderType.ANTHROPIC,
            model=os.getenv("ANTHROPIC_MODEL", "claude-3-haiku-20240307"),
            api_key=os.getenv("ANTHROPIC_API_KEY", ""),
            api_base="https://api.anthropic.com",
            max_tokens=mt,
            temperature=tp,
        )
    return LlmConfig(provider=LlmProviderType.MOCK, model="mock-v1")


# ─── Prompt 模板 ──────────────────────────────────────────────────────────────

PROMPT_VERSION = "ziwei_interpret_v2"

_SYSTEM_PROMPT = (
    "你是一位深研紫微斗数三十年的职业命理师，熟谙十二宫星曜互动、四化飞星与大限流年推算。"
    "你的解读风格直接、有画面感，像面对面为客户讲解，不说废话，不堆砌术语，每句话都指向这一个人的具体命运轨迹。\n\n"
    "接下来你将收到一份紫微命盘数据，请围绕这个人写出深度解读，要求：\n"
    "1. 全程用\u201c你\u201d直接对命主说，有师长与当事人面对面的亲切感；\n"
    "2. 宫位描述必须带意象，例如：\u2018命宫天机坐守，春风化雨之象，一生以智谋谋局，长于迂回而不在正面冲突\u2019；\n"
    "3. 四化飞星（化禄·权·科·忌）各有落点，具体说明对该宫的影响；\n"
    "4. 大限部分说清当下这个章节的底色：是收获期、积累期、还是转折期，举出2-3个具体预判；\n"
    "5. 综合建议落到行动层面：哪个方向值得主动出击、哪件事需要今年内决断；\n"
    "6. 字数 700\u20131000 字，自然段落，无须固定标题格式；\n"
    "7. 禁止出现任何免责声明、禁止出现\u2018仅供参考\u2019或\u2018须复核\u2019等表述。"
)

_USER_TEMPLATE = (
    "命盘摘要如下，请生成解读草稿：\n\n"
    "命宫干支：{life_palace_gz}\n"
    "五行局：{wuxing_ju_name}\n"
    "格局摘要：{pattern_summary}\n"
    "出生信息概要：{birth_info_summary}\n"
)


def build_user_prompt(
    life_palace_gz: str,
    wuxing_ju_name: str,
    pattern_summary: str,
    birth_info_summary: str,
) -> str:
    return _USER_TEMPLATE.format(
        life_palace_gz=life_palace_gz or "（未知）",
        wuxing_ju_name=wuxing_ju_name or "（未知）",
        pattern_summary=pattern_summary or "（暂无格局记录）",
        birth_info_summary=birth_info_summary or "（未提供）",
    )


# ─── Mock 生成器（无 API key 时使用）────────────────────────────────────────────

_ELEM_TALENT: dict[str, str] = {
    "水": "智谋型", "木": "进取型", "火": "活跃型",
    "土": "稳健型", "金": "决断型",
}

_MOCK_TEMPLATE = """\
【命盘综合解读草稿 · AI 辅助生成 · 仅供参考】

▌ 命格气质
命宫{lp_gz}，隶属{wux_ju}，五行以{wux_elem}气为主，命主先天气质偏{talent}，\
处事风格在沉稳中见主见，适合在专业领域积累深厚资历。\
命宫星系在紫微斗数体系中属均衡发展格局，先天禀赋较为全面。

▌ 格局亮点
本盘已识别格局：{patterns}。\
上述格局提示命主在特定人生阶段（尤其大运交替期）将获得外部资源的支持，\
宜在顺运期主动出击，逆运期静守待机，切忌激进冒进。

▌ 大运与流年展望
当前大运运势稳中有升，流年命宫与本命宫形成一定协调关系，\
适合在事业或学业方面稳步拓展。\
感情宫位星情尚稳，需留意沟通细节；健康宫可多关注作息规律与情志调适。

▌ 综合建议
择业方向宜顺{wux_elem}行五行特质发展；居家布局与择时可参考{wux_ju}对应五行方位加持运势。\
化解弱势宫位的关键在于规律作息与内心自省，辅以破局建议中的风水调整措施，可事半功倍。

⚠️ 本文案由 AI 辅助生成，仅供参考，须经命理师复核后方可使用。\
"""


def _mock_generate(
    life_palace_gz: str,
    wuxing_ju_name: str,
    pattern_summary: str,
) -> str:
    wux_elem = next((e for e in _ELEM_TALENT if e in (wuxing_ju_name or "")), "")
    talent   = _ELEM_TALENT.get(wux_elem, "综合型")
    return _MOCK_TEMPLATE.format(
        lp_gz=life_palace_gz or "（未知）",
        wux_ju=wuxing_ju_name or "（未知局）",
        wux_elem=wux_elem or "综合五行",
        talent=talent,
        patterns=pattern_summary or "（无显著格局）",
    )


# ─── 实际 API 调用（httpx）────────────────────────────────────────────────────

async def _call_openai(
    cfg: LlmConfig, system_prompt: str, user_prompt: str
) -> tuple[str, LlmUsage]:
    headers = {
        "Authorization": f"Bearer {cfg.api_key}",
        "Content-Type": "application/json",
    }
    body = {
        "model": cfg.model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_prompt},
        ],
        "max_tokens":  cfg.max_tokens,
        "temperature": cfg.temperature,
    }
    async with httpx.AsyncClient(timeout=60.0) as client:
        r = await client.post(
            f"{cfg.api_base}/v1/chat/completions", headers=headers, json=body
        )
        r.raise_for_status()
        data = r.json()

    text = data["choices"][0]["message"]["content"]
    raw  = data.get("usage", {})
    it, ot = raw.get("prompt_tokens", 0), raw.get("completion_tokens", 0)
    # gpt-4o-mini: ~$0.00015/1K input, ~$0.0006/1K output
    cost = it * 0.00015 / 1000 + ot * 0.0006 / 1000
    return text, LlmUsage(it, ot, round(cost, 6))


async def _call_anthropic(
    cfg: LlmConfig, system_prompt: str, user_prompt: str
) -> tuple[str, LlmUsage]:
    headers = {
        "x-api-key": cfg.api_key,
        "anthropic-version": "2023-06-01",
        "Content-Type": "application/json",
    }
    body = {
        "model":       cfg.model,
        "max_tokens":  cfg.max_tokens,
        "temperature": cfg.temperature,
        "system":      system_prompt,
        "messages":    [{"role": "user", "content": user_prompt}],
    }
    async with httpx.AsyncClient(timeout=60.0) as client:
        r = await client.post(
            f"{cfg.api_base}/v1/messages", headers=headers, json=body
        )
        r.raise_for_status()
        data = r.json()

    text = data["content"][0]["text"]
    raw  = data.get("usage", {})
    it, ot = raw.get("input_tokens", 0), raw.get("output_tokens", 0)
    # claude-3-haiku: ~$0.00025/1K input, ~$0.00125/1K output
    cost = it * 0.00025 / 1000 + ot * 0.00125 / 1000
    return text, LlmUsage(it, ot, round(cost, 6))


# ─── 主入口 ───────────────────────────────────────────────────────────────────

async def generate_interpretation(
    life_palace_gz:     str,
    wuxing_ju_name:     str,
    pattern_summary:    str,
    birth_info_summary: str,
) -> LlmResponse:
    """生成命盘解读草稿，自动选择已配置的 LLM provider。"""
    cfg = get_llm_config()
    t0  = time.monotonic()

    # O6: 断路器打开 → 直接返回 Mock fallback
    if cfg.provider != LlmProviderType.MOCK and _is_circuit_open():
        logger.warning("[O6] 断路器打开，generate_interpretation 使用 Mock fallback")
        text  = _mock_generate(life_palace_gz, wuxing_ju_name, pattern_summary)
        usage = LlmUsage(0, len(text.split()), 0.0)
        return LlmResponse(
            text=text,
            provider=LlmProviderType.MOCK.value,
            model="mock-fallback",
            usage=usage,
            duration_secs=round(time.monotonic() - t0, 3),
            prompt_version=PROMPT_VERSION,
            is_fallback=True,
        )

    if cfg.provider == LlmProviderType.MOCK:
        text  = _mock_generate(life_palace_gz, wuxing_ju_name, pattern_summary)
        usage = LlmUsage(0, len(text.split()), 0.0)
    else:
        user_prompt = build_user_prompt(
            life_palace_gz, wuxing_ju_name, pattern_summary, birth_info_summary
        )
        try:
            if cfg.provider == LlmProviderType.OPENAI:
                text, usage = await _call_openai(cfg, _SYSTEM_PROMPT, user_prompt)
            else:
                text, usage = await _call_anthropic(cfg, _SYSTEM_PROMPT, user_prompt)
        except httpx.HTTPStatusError as e:
            _llm_record_failure()
            raise RuntimeError(
                f"LLM API 返回错误 {e.response.status_code}: {e.response.text[:200]}"
            ) from e
        except Exception as e:
            _llm_record_failure()
            raise RuntimeError(f"LLM API 调用失败: {e}") from e

    return LlmResponse(
        text=text,
        provider=cfg.provider.value,
        model=cfg.model,
        usage=usage,
        duration_secs=round(time.monotonic() - t0, 3),
        prompt_version=PROMPT_VERSION,
    )


# ─── 八字证据链解读（Phase A3）────────────────────────────────────────────────

BAZI_PROMPT_VERSION = "bazi_grounded_v2"

_BAZI_SYSTEM_PROMPT = (
    "你是一位从业三十年的资深子平八字命理师，精研《子平真诠》《三命通会》《神峰通考》《滴天髓》《穷通宝鉴》。"
    "你断命有独到见解，善用命理意象，每句话都落在这一个人身上，绝不泛泛而谈。\n\n"
    "你将收到一份八字命盘的完整数据（格局、用神、专项评分、大运走势）以及相关古籍引文。"
    "请以命理师第一视角，用'你'直接对命主说话，写出一段深度、具体、有打动力的命盘解读：\n\n"
    "要求：\n"
    "1. 开篇以命盘核心意象破题——用一两句有画面感的比喻点出这个命局的本质气质，如'庚金生于亥月，铁沉深水，须炉火煅炼方见锋芒'；\n"
    "2. 格局与用神部分说清楚：这个格局意味着什么人生底色，用神方向应当如何在日常中落地（行业、居所方位、生活习惯）；\n"
    "3. 专项分析（事业/财运/婚恋/健康）各有具体内容：给出行业名称、财富路径、配偶特征、需警惕的年龄段，而非空泛描述；\n"
    "4. 古籍引文自然嵌入叙述，如'正如《子平真诠》所言……'，不做机械尾注；\n"
    "5. 大运走势用'人生章节'作比，说清楚当前这步大运的底色，以及下一个15年的结构性变化节点；\n"
    "6. 字数 750–1000 字，自然段落，无须固定段落标题；\n"
    "7. 严格禁止：①任何免责声明和'仅供参考'；②空话（'努力奋斗''把握机遇''整体平稳'）；③用'该人''命主'，必须用'你'。"
)

# ─── 专项模块 Prompt（各模块聚焦不同维度）────────────────────────────────────

_PROMPT_WEALTH = (
    "你是从业三十年的子平命理师，精研财运论命。\n"
    "根据命盘数据，专项分析此人的财富命格，用'你'直接作答：\n"
    "1. 财格气质：正财还是偏财格局，财星力量如何，一句意象破题（如'偏财坐时柱，如商贾善把行情脉'）；\n"
    "2. 财富路径：最适合的积累方式（主业/副业/投资），给出具体行业名称（最少4个），说明为何与命盘用神吻合；\n"
    "3. 投资风格：适合稳健型还是进取型，对哪类投资标的天生敏感，有哪些消财恶习要主动戒除；\n"
    "4. 大运财运节点：逐步点出哪几个大运是财运高峰，哪步是必须守成的低谷，给出年龄区间；\n"
    "5. 当下行动：此时此刻（结合当前大运流年），最值得主动布局的一件具体财务行动；\n"
    "字数 600–900 字，禁止免责声明，禁止空话。"
)

_PROMPT_CAREER = (
    "你是从业三十年的子平命理师，擅长事业命格分析。\n"
    "根据命盘数据，专项分析此人的事业命格，用'你'直接作答：\n"
    "1. 事业气质：官杀格局还是食伤生财，一句意象破题，说清楚这个人天生适合哪种职场角色；\n"
    "2. 最适合的行业与岗位：给出至少5个明确行业，说明原因——是官星入财库还是食神制杀等；\n"
    "3. 职场风格：领导型还是专家型，适合大企业还是自雇，跟什么类型的人合作最顺畅；\n"
    "4. 上升瓶颈与突破点：目前卡在哪个结构性问题上，何时（哪步大运/哪段流年）是最佳跳槽或创业窗口；\n"
    "5. 五年行动建议：结合当前大运，给出可执行的职业规划方向；\n"
    "字数 600–900 字，禁止免责声明，禁止空话。"
)

_PROMPT_MARRIAGE = (
    "你是从业三十年的子平命理师，精于婚恋论命。\n"
    "根据命盘数据，专项分析此人的婚恋命格，用'你'直接作答：\n"
    "1. 感情气质：官星/夫妻宫状态，一句意象破题（如'夫妻宫坐七杀，遇人则爱，爱则激烈，感情路上波折正是成长课题'）；\n"
    "2. 什么样的人对你好：将配偶五行转译为性格描述（不说'金水命'，说'做事干练、说话直接、内心重情义的人'），给出相处最顺畅的对象画像；\n"
    "3. 感情模式与雷区：天生的相处节律是什么，最容易在哪个感情环节出问题，过去经历里反复出现的模式；\n"
    "4. 最可能稳定的年龄窗口：结合大运说明哪段时期最适合进入认真关系或步入婚姻；\n"
    "5. 婚后相处建议：和什么五行的人长期相处最顺，什么类型的关系动态最能让你舒展；\n"
    "字数 600–900 字，禁止免责声明，禁止空话。"
)

_PROMPT_DAYUN = (
    "你是从业三十年的子平命理师，精于大运推算。\n"
    "根据命盘数据，用'人生章节'的比喻为此人详述大运走势，用'你'直接作答：\n"
    "1. 先给出这张命盘的大运整体韵律：是前好后收还是中年发力，是起伏型还是稳进型；\n"
    "2. 逐步大运展开（最多5步）：每步说清楚这十年的底色是什么——是积累期、收获期、转型期、还是蛰伏期；\n"
    "   在每步大运里点出：①这段时期的事业财运大方向 ②感情与家庭的主要节点 ③最值得把握的一个具体机遇和一个需要警惕的风险；\n"
    "3. 当前大运聚焦：此时此刻命主正处在哪个章节，还剩多少年，最值得在未来1-2年内完成的一件事；\n"
    "字数 700–1000 字，禁止免责声明，禁止空话。"
)

_PROMPT_LIUNIAN = (
    "你是从业三十年的子平命理师，精于流年流月推算。\n"
    "根据命盘数据（尤其是当前大运与今年流年），给出高度可操作的今年行事建议，用'你'直接作答：\n"
    "1. 今年的整体运势底色：流年太岁与命局的关系（生、克、冲、合），用一句话描述今年的主调；\n"
    "2. 四大维度今年预测：事业节点（何时适合出击/蛰伏）、财运关键月份（哪3个月最有机会或最需谨慎）、感情走势（今年的情感主题）、健康注意（具体脏腑或季节）；\n"
    "3. 最值得行动的3件事：具体到可以本周开始做的事，不是方向，是动作；\n"
    "4. 最需回避的1件事：今年最忌的行为模式或决策类型；\n"
    "字数 400–600 字，禁止免责声明，禁止空话，越具体越好。"
)

_PROMPT_FENGSHUI = (
    "你是从业三十年的命理风水师，精于八宅风水与五行调候。\n"
    "根据命盘数据（用神、五行、命宫方位），给出落地可操作的风水与开运建议，用'你'直接作答：\n"
    "1. 个人五行体质：此人命局五行偏重与缺失，主导了整体风水调候方向；\n"
    "2. 居家风水布局：卧室床头方向、书桌/工作台朝向、进门玄关布置，给出具体方位（东/南/西/北/东南等）和理由；\n"
    "3. 开运色彩：日常穿搭、软装配色中最应多用的2-3种颜色，以及应减少的颜色，说明与用神的对应；\n"
    "4. 植物与摆件：适合摆放的植物种类（至少2种）、最合适的位置，以及绝对要避开的植物或物品；\n"
    "5. 年度方位调整：结合当年流年太岁，哪个方位今年需特别加强或清理；\n"
    "字数 400–600 字，落地可操作，禁止免责声明，禁止空话。"
)

_MODULE_PROMPTS: dict[str, str] = {
    "wealth_detail":       _PROMPT_WEALTH,
    "career_detail":       _PROMPT_CAREER,
    "marriage_detail":     _PROMPT_MARRIAGE,
    "dayun_narrative":     _PROMPT_DAYUN,
    "liunian_advice":      _PROMPT_LIUNIAN,
    "fengshui_suggestion": _PROMPT_FENGSHUI,
}

_BAZI_USER_TEMPLATE = (
    "以下是八字命盘的结构化事实，请生成有据可查的解读草稿：\n\n"
    "【命盘事实】\n"
    "{rendered_facts}\n\n"
    "【相关古籍引文】\n"
    "{evidence_block}\n"
)


def _build_bazi_user_prompt(rendered_facts: str, evidence_snippets: list[str]) -> str:
    if evidence_snippets:
        evidence_block = "\n".join(
            f"· {snippet}" for snippet in evidence_snippets
        )
    else:
        evidence_block = "（暂无匹配的古籍引文）"
    return _BAZI_USER_TEMPLATE.format(
        rendered_facts=rendered_facts or "（未提供命盘事实）",
        evidence_block=evidence_block,
    )


def _mock_bazi_generate(rendered_facts: str, evidence_snippets: list[str]) -> str:
    evidence_note = ""
    if evidence_snippets:
        evidence_note = f"\n\n【古籍参考】\n" + "\n".join(f"· {s}" for s in evidence_snippets[:2])
    return (
        "【八字命盘综合解读草稿 · AI 辅助生成 · 仅供参考】\n\n"
        "▌ 格局概述\n"
        f"{rendered_facts[:120] if rendered_facts else '（命盘事实未提供）'}……\n"
        "格局结构较为清晰，命主先天气质独特，具备相应领域的潜力与资质。\n\n"
        "▌ 用神与喜忌\n"
        "根据格局分析，喜用五行方向明确，顺用则吉，逆用则需谨慎调候。\n"
        "流年大运以与用神相生相助的方向为最佳发展窗口。\n\n"
        "▌ 人生建议（事业·财运·感情）\n"
        "事业：顺格局特质择业，避免与命盘五行相冲的行业方向。\n"
        "财运：以正当途径积累，量力而行，不宜激进投机。\n"
        "感情：尊重自身感情节奏，与五行相生的伴侣最为和谐。\n\n"
        "▌ 大运提示\n"
        "关键大运交替期须特别关注，旺运期主动出击，弱运期静守待机。"
        f"{evidence_note}\n\n"
        "⚠️ 本文案由 AI 辅助生成，仅供参考，须经命理师复核后方可使用。"
    )


async def generate_bazi_interpretation(
    rendered_facts: str,
    evidence_snippets: list[str],
    module_type: str | None = None,
) -> LlmResponse:
    """
    八字命盘有据解读入口（Phase A3，独立于紫微 generate_interpretation）。

    参数
    ----
    rendered_facts    : 命盘结构化事实文本（由 Jinja2 模板渲染的格局/用神/建议）
    evidence_snippets : 古籍引文列表（由 evidence_retriever.fetch_evidence() 提供）
    module_type       : 可选模块标识，用于选择专项 prompt（wealth_detail/career_detail 等）

    原 generate_interpretation() 保持不变，两者共存，各自使用独立 prompt 版本。
    """
    # 根据模块类型选择专项 prompt
    system_prompt = _MODULE_PROMPTS.get(module_type or "", _BAZI_SYSTEM_PROMPT) if module_type else _BAZI_SYSTEM_PROMPT

    cfg = get_llm_config()
    t0 = time.monotonic()

    # O6: 断路器打开 → 直接返回 Mock fallback
    if cfg.provider != LlmProviderType.MOCK and _is_circuit_open():
        logger.warning("[O6] 断路器打开，generate_bazi_interpretation 使用 Mock fallback")
        text = _mock_bazi_generate(rendered_facts, evidence_snippets)
        usage = LlmUsage(0, len(text.split()), 0.0)
        return LlmResponse(
            text=text,
            provider=LlmProviderType.MOCK.value,
            model="mock-fallback",
            usage=usage,
            duration_secs=round(time.monotonic() - t0, 3),
            prompt_version=BAZI_PROMPT_VERSION,
            is_fallback=True,
        )

    if cfg.provider == LlmProviderType.MOCK:
        text = _mock_bazi_generate(rendered_facts, evidence_snippets)
        usage = LlmUsage(0, len(text.split()), 0.0)
    else:
        user_prompt = _build_bazi_user_prompt(rendered_facts, evidence_snippets)
        try:
            if cfg.provider == LlmProviderType.OPENAI:
                text, usage = await _call_openai(cfg, system_prompt, user_prompt)
            else:
                text, usage = await _call_anthropic(cfg, system_prompt, user_prompt)
        except httpx.HTTPStatusError as e:
            _llm_record_failure()
            raise RuntimeError(
                f"LLM API 返回错误 {e.response.status_code}: {e.response.text[:200]}"
            ) from e
        except Exception as e:
            _llm_record_failure()
            raise RuntimeError(f"LLM API 调用失败: {e}") from e

    return LlmResponse(
        text=text,
        provider=cfg.provider.value,
        model=cfg.model,
        usage=usage,
        duration_secs=round(time.monotonic() - t0, 3),
        prompt_version=BAZI_PROMPT_VERSION,
    )


async def stream_interpretation(
    life_palace_gz:     str,
    wuxing_ju_name:     str,
    pattern_summary:    str,
    birth_info_summary: str,
) -> AsyncIterator[str]:
    """
    以 SSE 格式流式生成命盘解读草稿。

    yield 每行均为完整 SSE 消息（含 event: / data: / 空行）。
    事件序列：start → chunk(×N) → done | error
    """
    cfg = get_llm_config()
    yield (
        f'event: start\ndata: {json.dumps({"status": "generating", "provider": cfg.provider.value}, ensure_ascii=False)}\n\n'
    )

    if cfg.provider == LlmProviderType.MOCK:
        text  = _mock_generate(life_palace_gz, wuxing_ju_name, pattern_summary)
        # 按句号分块模拟流式输出
        parts = [s + "。" for s in text.split("。") if s.strip()]
        for i, part in enumerate(parts):
            yield f"event: chunk\ndata: {json.dumps({'idx': i, 'text': part}, ensure_ascii=False)}\n\n"
            await asyncio.sleep(0.04)
        usage_dict = {"input_tokens": 0, "output_tokens": len(text.split()), "cost_usd": 0.0}
        full_text  = text
    else:
        user_prompt = build_user_prompt(
            life_palace_gz, wuxing_ju_name, pattern_summary, birth_info_summary
        )
        try:
            if cfg.provider == LlmProviderType.OPENAI:
                full_text, usage_obj = await _call_openai(cfg, _SYSTEM_PROMPT, user_prompt)
            else:
                full_text, usage_obj = await _call_anthropic(cfg, _SYSTEM_PROMPT, user_prompt)
            usage_dict = {
                "input_tokens":  usage_obj.input_tokens,
                "output_tokens": usage_obj.output_tokens,
                "cost_usd":      usage_obj.cost_usd,
            }
        except Exception as e:
            err = json.dumps({"error": str(e)}, ensure_ascii=False)
            yield f"event: error\ndata: {err}\n\n"
            return

        # 按 50 字符分块推送已生成文本
        for i in range(0, len(full_text), 50):
            chunk = full_text[i: i + 50]
            yield f"event: chunk\ndata: {json.dumps({'idx': i // 50, 'text': chunk}, ensure_ascii=False)}\n\n"
            await asyncio.sleep(0.01)

    done_payload = json.dumps(
        {"status": "done", "full_text": full_text, "usage": usage_dict},
        ensure_ascii=False,
    )
    yield f"event: done\ndata: {done_payload}\n\n"


# ─── 年份事件 AI 咨询解读（年份事件预测系统专用）────────────────────────────────

EVENT_CONSULT_PROMPT_VERSION = "event_consult_v1"

_PROMPT_EVENT_CONSULT_SYSTEM = (
    "你是一位从业三十年的资深子平八字命理师，精研《子平真诠》《三命通会》《滴天髓》。\n"
    "你将收到规则引擎对某人某年某事件的结构化预测结论，以及用户的具体问题。\n\n"
    "【严格规则——必须遵守】\n"
    "1. 你只负责深入解释和展开引擎已得出的结论，不得凭空新增事件或重新预测；\n"
    "2. trigger_summary 是结论的边界，你只在这个边界内展开，不得超出；\n"
    "3. 若引擎标注了 avoid_overclaim，你必须在解读末尾如实写明该注意事项；\n"
    "4. 直接回答用户的问题，不要先重述问题；\n"
    "5. 给出具体月份（由 key_months 决定）和具体的现实应对建议；\n"
    "6. 解读要有温度，用'你'作为称呼，不用'该命主'等第三人称；\n"
    "7. 字数 300–500 字，结构清晰，禁止免责声明，禁止空话套话；\n"
    "8. 古籍引文如有可用则自然嵌入，不做机械尾注。"
)


def _build_event_consult_prompt(
    event_result,
    user_question: str,
    materials: dict,
) -> str:
    """构建年份事件 AI 咨询的 user_prompt。"""
    et = event_result
    lines = [
        f"=== 引擎预测结论（{et.event_type} / {et.year}年）===",
        f"风险等级：{et.risk_level}  机遇等级：{et.opportunity_level}  置信度：{et.confidence:.0%}",
        f"核心研判：{et.main_judgment or '（未生成）'}",
        f"触发信号概要：{et.trigger_summary or '（无）'}",
    ]
    if et.event_subtypes:
        lines.append(f"事件子类：{'、'.join(et.event_subtypes)}")
    if et.key_months:
        lines.append(f"关键月份：{'、'.join(str(m)+'月' for m in et.key_months)}")
    if et.possible_manifestations:
        lines.append("可能表现：" + "；".join(et.possible_manifestations[:4]))
    if et.omens:
        lines.append("现实预兆：" + "；".join(et.omens[:3]))
    if et.signals:
        sig_labels = [f"[{s.layer}]{s.label}" for s in et.signals[:5]]
        lines.append("已触发信号：" + "、".join(sig_labels))
    if et.classical_notes:
        for cn in et.classical_notes[:2]:
            lines.append(f"古籍依据：{cn.source}「{cn.basis}」")
    if et.advice:
        lines.append("引擎建议：" + "；".join(et.advice[:3]))
    if et.avoid_overclaim:
        lines.append(f"\n⚠ 注意事项（必须在解读末尾说明）：{et.avoid_overclaim}")
    lines.append("")
    lines.append(f"=== 用户问题 ===")
    lines.append(user_question)
    return "\n".join(lines)


async def generate_event_interpretation(
    event_result,
    user_question: str,
    materials: dict,
) -> LlmResponse:
    """
    年份事件 AI 咨询解读入口。

    参数
    ----
    event_result  : EventResult（来自 event_signal_engine）
    user_question : 用户输入的具体问题
    materials     : get_materials_for_signals() 返回的规则素材字典

    LLM 职责：只解释引擎结论，不重新预测，不凭空新增事件。
    """
    cfg = get_llm_config()
    t0 = time.monotonic()

    # 断路器打开 → 降级
    if cfg.provider != LlmProviderType.MOCK and _is_circuit_open():
        logger.warning("[O6] 断路器打开，generate_event_interpretation 使用 Mock fallback")
        text = f"当前解读服务暂时不可用，请稍后再试。\n已知研判：{event_result.main_judgment or ''}"
        usage = LlmUsage(0, len(text.split()), 0.0)
        return LlmResponse(
            text=text,
            provider=LlmProviderType.MOCK.value,
            model="mock-fallback",
            usage=usage,
            duration_secs=round(time.monotonic() - t0, 3),
            prompt_version=EVENT_CONSULT_PROMPT_VERSION,
            is_fallback=True,
        )

    user_prompt = _build_event_consult_prompt(event_result, user_question, materials)

    if cfg.provider == LlmProviderType.MOCK:
        text = (
            f"【模拟解读】关于你的问题「{user_question}」：\n\n"
            f"根据命盘分析，{event_result.main_judgment or ''}。\n"
            f"触发信号概要：{event_result.trigger_summary or '规则引擎暂无详细记录'}。\n"
        )
        if event_result.advice:
            text += "\n建议：" + "；".join(event_result.advice[:2])
        usage = LlmUsage(0, len(text.split()), 0.0)
    else:
        try:
            if cfg.provider == LlmProviderType.OPENAI:
                text, usage = await _call_openai(cfg, _PROMPT_EVENT_CONSULT_SYSTEM, user_prompt)
            else:
                text, usage = await _call_anthropic(cfg, _PROMPT_EVENT_CONSULT_SYSTEM, user_prompt)
        except Exception as e:
            _llm_record_failure()
            raise RuntimeError(f"LLM 事件咨询调用失败: {e}") from e

    return LlmResponse(
        text=text,
        provider=cfg.provider.value,
        model=cfg.model,
        usage=usage,
        duration_secs=round(time.monotonic() - t0, 3),
        prompt_version=EVENT_CONSULT_PROMPT_VERSION,
    )
