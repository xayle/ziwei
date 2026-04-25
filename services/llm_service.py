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
import json
import logging
import os
import threading
import time
from dataclasses import dataclass
from enum import Enum
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
    max_tokens:  int = 800
    temperature: float = 0.7


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
    mt = int(os.getenv("LLM_MAX_TOKENS", "800"))
    tp = float(os.getenv("LLM_TEMPERATURE", "0.7"))

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

PROMPT_VERSION = "ziwei_interpret_v1"

_SYSTEM_PROMPT = (
    "你是一位精通紫微斗数的命理专家，擅长将命盘数据转化为通俗易懂的解读文案。\n"
    "请根据以下命盘结构化数据生成一份简洁、准确的解读草稿。\n"
    "要求：\n"
    "1. 用中文撰写，语气亲切专业；\n"
    "2. 仅基于命盘数据，不凭空臆造；\n"
    "3. 分四段：命格气质 / 格局亮点 / 大运与流年 / 综合建议；\n"
    "4. 总字数 300–500 字；\n"
    "5. 末尾必须附上：「⚠️ 本文案由 AI 辅助生成，仅供参考，须经命理师复核后方可使用。」\n"
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

BAZI_PROMPT_VERSION = "bazi_grounded_v1"

_BAZI_SYSTEM_PROMPT = (
    "你是一位精通子平八字命理的专家，擅长将格局分析与古籍依据融合为通俗易懂的解读。\n"
    "请根据以下八字命盘事实与古籍引文，生成一份有据可查的命理解读草稿。\n"
    "要求：\n"
    "1. 用中文撰写，语气亲切专业；\n"
    "2. 仅依据命盘事实与古籍引文，不凭空杜撰；\n"
    "3. 分四段：格局概述 / 用神与喜忌 / 人生建议（事业·财运·感情）/ 大运提示；\n"
    "4. 如有古籍引文，须在对应段落末尾用括号注明来源，如（《子平真诠》）；\n"
    "5. 总字数 350–550 字；\n"
    "6. 末尾必须附：「⚠️ 本文案由 AI 辅助生成，仅供参考，须经命理师复核后方可使用。」\n"
)

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
) -> LlmResponse:
    """
    八字命盘有据解读入口（Phase A3，独立于紫微 generate_interpretation）。

    参数
    ----
    rendered_facts    : 命盘结构化事实文本（由 Jinja2 模板渲染的格局/用神/建议）
    evidence_snippets : 古籍引文列表（由 evidence_retriever.fetch_evidence() 提供）

    原 generate_interpretation() 保持不变，两者共存，各自使用独立 prompt 版本。
    """
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
                text, usage = await _call_openai(cfg, _BAZI_SYSTEM_PROMPT, user_prompt)
            else:
                text, usage = await _call_anthropic(cfg, _BAZI_SYSTEM_PROMPT, user_prompt)
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
