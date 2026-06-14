"""
test_coverage_boost27.py — services/llm_service.py 断路器状态机 + 全链路测试

覆盖目标（当前 ~52%，目标 80%+）：
  1. 断路器状态机：_llm_record_failure / _is_circuit_open / _reset_circuit_for_test
  2. generate_interpretation() → MOCK / circuit-open fallback / 异常路径
  3. generate_bazi_interpretation() → MOCK / circuit-open fallback / 异常路径
  4. build_user_prompt / _build_bazi_user_prompt
  5. get_llm_config() 各分支
  6. _mock_generate / _mock_bazi_generate
  7. stream_interpretation() MOCK 流式路径

所有测试均使用纯 Mock（不发起真实 HTTP 请求），利用 pytest monkeypatch + unittest.mock。
"""
from __future__ import annotations

import asyncio
import os
import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

import services.llm_service as svc


# ──────────────────────────────────────────────────────────────────────────────
# Fixture：每个测试前重置断路器状态
# ──────────────────────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def reset_circuit():
    """每个测试前后自动重置断路器至闭合状态。"""
    svc._reset_circuit_for_test()
    yield
    svc._reset_circuit_for_test()


# ══════════════════════════════════════════════════════════════════════════════
# A. 断路器核心函数单元测试
# ══════════════════════════════════════════════════════════════════════════════

class TestCircuitBreakerCore:

    def test_initial_state_is_closed(self):
        """初始状态：断路器闭合"""
        assert not svc._is_circuit_open()

    def test_one_failure_not_enough(self):
        """1 次失败不开路"""
        svc._llm_record_failure()
        assert not svc._is_circuit_open()

    def test_two_failures_not_enough(self):
        """2 次失败不开路"""
        svc._llm_record_failure()
        svc._llm_record_failure()
        assert not svc._is_circuit_open()

    def test_three_failures_opens_circuit(self):
        """3 次失败 → 断路器打开"""
        for _ in range(svc._LLM_CIRCUIT_FAIL_THRESH):
            svc._llm_record_failure()
        assert svc._is_circuit_open()

    def test_circuit_open_within_cooldown(self, monkeypatch):
        """冷却期内 → _is_circuit_open 返回 True"""
        # 直接将 open_until 设为未来时间
        monkeypatch.setattr(svc, "_LLM_CIRCUIT_OPEN_UNTIL", time.time() + 600)
        assert svc._is_circuit_open()

    def test_circuit_auto_reset_after_cooldown(self, monkeypatch):
        """冷却期已过 → half-open：_is_circuit_open 返回 False，并重置 open_until"""
        monkeypatch.setattr(svc, "_LLM_CIRCUIT_OPEN_UNTIL", time.time() - 1)
        assert not svc._is_circuit_open()
        assert svc._LLM_CIRCUIT_OPEN_UNTIL == 0.0

    def test_reset_circuit_for_test(self):
        """_reset_circuit_for_test 彻底重置"""
        for _ in range(svc._LLM_CIRCUIT_FAIL_THRESH):
            svc._llm_record_failure()
        assert svc._is_circuit_open()
        svc._reset_circuit_for_test()
        assert not svc._is_circuit_open()

    def test_fail_count_resets_after_open(self):
        """断路器打开后失败计数归零，再次 3 次失败才重新开路"""
        for _ in range(svc._LLM_CIRCUIT_FAIL_THRESH):
            svc._llm_record_failure()
        assert svc._is_circuit_open()
        # 重置（模拟冷却期过）
        svc._reset_circuit_for_test()
        assert not svc._is_circuit_open()
        # 断路器闭合后 2 次失败不开路
        svc._llm_record_failure()
        svc._llm_record_failure()
        assert not svc._is_circuit_open()


# ══════════════════════════════════════════════════════════════════════════════
# B. get_llm_config() 环境变量分支
# ══════════════════════════════════════════════════════════════════════════════

class TestGetLlmConfig:

    def test_no_keys_returns_mock(self, monkeypatch):
        """无 API key → MOCK provider"""
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        monkeypatch.delenv("LLM_PROVIDER", raising=False)
        cfg = svc.get_llm_config()
        assert cfg.provider == svc.LlmProviderType.MOCK

    def test_openai_key_returns_openai(self, monkeypatch):
        """设置 OPENAI_API_KEY → openai provider"""
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
        monkeypatch.delenv("LLM_PROVIDER", raising=False)
        cfg = svc.get_llm_config()
        assert cfg.provider == svc.LlmProviderType.OPENAI
        assert cfg.api_key == "sk-test"

    def test_anthropic_key_returns_anthropic(self, monkeypatch):
        """设置 ANTHROPIC_API_KEY（无 OPENAI_API_KEY）→ anthropic provider"""
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test")
        monkeypatch.delenv("LLM_PROVIDER", raising=False)
        cfg = svc.get_llm_config()
        assert cfg.provider == svc.LlmProviderType.ANTHROPIC

    def test_force_mock_via_provider_env(self, monkeypatch):
        """LLM_PROVIDER=mock 强制 Mock（即使有 API key）"""
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
        monkeypatch.setenv("LLM_PROVIDER", "mock")
        cfg = svc.get_llm_config()
        assert cfg.provider == svc.LlmProviderType.MOCK

    def test_custom_model_and_tokens(self, monkeypatch):
        """自定义 LLM_MAX_TOKENS 和 OPENAI_MODEL"""
        monkeypatch.setenv("OPENAI_API_KEY", "sk-x")
        monkeypatch.setenv("OPENAI_MODEL", "gpt-4o")
        monkeypatch.setenv("LLM_MAX_TOKENS", "1200")
        monkeypatch.delenv("LLM_PROVIDER", raising=False)
        cfg = svc.get_llm_config()
        assert cfg.model == "gpt-4o"
        assert cfg.max_tokens == 1200


# ══════════════════════════════════════════════════════════════════════════════
# C. Prompt 构建函数
# ══════════════════════════════════════════════════════════════════════════════

class TestBuildUserPrompt:

    def test_all_fields(self):
        """所有字段都有值"""
        p = svc.build_user_prompt("甲午", "水二局", "偏财格", "1990年男")
        assert "甲午" in p
        assert "水二局" in p
        assert "偏财格" in p
        assert "1990年男" in p

    def test_empty_fields_use_defaults(self):
        """空字段使用占位符"""
        p = svc.build_user_prompt("", "", "", "")
        assert "（未知）" in p
        assert "（暂无格局记录）" in p

    def test_bazi_prompt_with_evidence(self):
        """_build_bazi_user_prompt 含古籍引文"""
        p = svc._build_bazi_user_prompt("命盘事实内容", ["《子平真诠》：...","《穷通宝鉴》：..."])
        assert "《子平真诠》" in p
        assert "《穷通宝鉴》" in p

    def test_bazi_prompt_no_evidence(self):
        """_build_bazi_user_prompt 无古籍 → 占位文本"""
        p = svc._build_bazi_user_prompt("命盘事实内容", [])
        assert "暂无匹配" in p


# ══════════════════════════════════════════════════════════════════════════════
# D. Mock 生成器函数
# ══════════════════════════════════════════════════════════════════════════════

class TestMockGenerators:

    def test_mock_generate_contains_warning(self):
        """_mock_generate 末尾包含免责声明"""
        t = svc._mock_generate("甲午", "水二局", "偏财格")
        assert "AI 辅助生成" in t

    def test_mock_generate_water_element(self):
        """水局 → 智谋型"""
        t = svc._mock_generate("壬子", "水二局", "")
        assert "智谋型" in t

    def test_mock_generate_fire_element(self):
        """火局 → 活跃型"""
        t = svc._mock_generate("丙午", "火六局", "紫微坐命")
        assert "活跃型" in t

    def test_mock_generate_unknown_element(self):
        """未知五行 → 综合型"""
        t = svc._mock_generate("", "", "")
        assert "综合型" in t

    def test_mock_bazi_generate_with_evidence(self):
        """_mock_bazi_generate 含古籍 → 文本包含"""
        t = svc._mock_bazi_generate("格局事实", ["《子平真诠》：正官格大贵"])
        assert "《子平真诠》" in t
        assert "AI 辅助生成" in t

    def test_mock_bazi_generate_no_evidence(self):
        """_mock_bazi_generate 无古籍 → 不崩溃"""
        t = svc._mock_bazi_generate("格局事实", [])
        assert "AI 辅助生成" in t

    def test_mock_bazi_generate_empty_facts(self):
        """_mock_bazi_generate 空事实 → 占位符"""
        t = svc._mock_bazi_generate("", [])
        assert "命盘事实未提供" in t


# ══════════════════════════════════════════════════════════════════════════════
# E. generate_interpretation() — MOCK + 断路器 + 异常路径
# ══════════════════════════════════════════════════════════════════════════════

class TestGenerateInterpretation:

    def test_mock_provider_normal(self, monkeypatch):
        """MOCK provider → 正常返回，is_fallback=False"""
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        monkeypatch.delenv("LLM_PROVIDER", raising=False)
        resp = asyncio.run(
            svc.generate_interpretation("甲午", "水二局", "偏财格", "1990年男")
        )
        assert resp.provider == "mock"
        assert not resp.is_fallback
        assert "AI 辅助生成" in resp.text
        assert resp.prompt_version == svc.PROMPT_VERSION

    def test_circuit_open_returns_fallback(self, monkeypatch):
        """断路器打开 + openai key → 返回 Mock fallback，is_fallback=True"""
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
        monkeypatch.delenv("LLM_PROVIDER", raising=False)
        # 强制断路器打开
        monkeypatch.setattr(svc, "_LLM_CIRCUIT_OPEN_UNTIL", time.time() + 600)
        resp = asyncio.run(
            svc.generate_interpretation("甲午", "水二局", "偏财格", "1990年男")
        )
        assert resp.is_fallback is True
        assert resp.provider == "mock"
        assert resp.model == "mock-fallback"

    def test_openai_exception_calls_record_failure(self, monkeypatch):
        """OpenAI 调用抛异常 → _llm_record_failure 被调用，并 raise RuntimeError"""
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
        monkeypatch.delenv("LLM_PROVIDER", raising=False)

        async def _fake_openai(*a, **kw):
            raise ConnectionError("network error")

        with patch.object(svc, "_call_openai", _fake_openai):
            with pytest.raises(RuntimeError, match="LLM API 调用失败"):
                asyncio.run(
                    svc.generate_interpretation("甲午", "水二局", "偏财格", "1990年男")
                )
        # 断路器已记录 1 次失败
        assert svc._LLM_FAIL_COUNT == 1

    def test_three_consecutive_failures_open_circuit(self, monkeypatch):
        """连续 3 次失败 → 断路器打开"""
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
        monkeypatch.delenv("LLM_PROVIDER", raising=False)

        async def _fail(*a, **kw):
            raise ConnectionError("timeout")

        with patch.object(svc, "_call_openai", _fail):
            for _ in range(svc._LLM_CIRCUIT_FAIL_THRESH):
                with pytest.raises(RuntimeError):
                    asyncio.run(
                        svc.generate_interpretation("", "", "", "")
                    )
        assert svc._is_circuit_open()

    def test_duration_secs_is_nonnegative(self, monkeypatch):
        """duration_secs >= 0"""
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.delenv("LLM_PROVIDER", raising=False)
        resp = asyncio.run(
            svc.generate_interpretation("壬子", "水二局", "", "")
        )
        assert resp.duration_secs >= 0


# ══════════════════════════════════════════════════════════════════════════════
# F. generate_bazi_interpretation() — MOCK + 断路器 + httpx 异常
# ══════════════════════════════════════════════════════════════════════════════

class TestGenerateBaziInterpretation:

    def test_mock_provider_normal(self, monkeypatch):
        """MOCK provider → 正常返回"""
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.delenv("LLM_PROVIDER", raising=False)
        resp = asyncio.run(
            svc.generate_bazi_interpretation("日主甲木身强", ["《子平真诠》：正官格"])
        )
        assert resp.provider == "mock"
        assert not resp.is_fallback
        assert resp.prompt_version == svc.BAZI_PROMPT_VERSION

    def test_circuit_open_returns_fallback(self, monkeypatch):
        """断路器打开 + openai key → is_fallback=True"""
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
        monkeypatch.delenv("LLM_PROVIDER", raising=False)
        monkeypatch.setattr(svc, "_LLM_CIRCUIT_OPEN_UNTIL", time.time() + 600)
        resp = asyncio.run(
            svc.generate_bazi_interpretation("格局事实", [])
        )
        assert resp.is_fallback is True

    def test_httpx_status_error_calls_record_failure(self, monkeypatch):
        """HTTP 状态错误 → _llm_record_failure，raise RuntimeError"""
        import httpx
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
        monkeypatch.delenv("LLM_PROVIDER", raising=False)

        async def _fake_openai(*a, **kw):
            resp = MagicMock()
            resp.status_code = 429
            resp.text = "rate limit"
            raise httpx.HTTPStatusError("err", request=MagicMock(), response=resp)

        with patch.object(svc, "_call_openai", _fake_openai):
            with pytest.raises(RuntimeError, match="LLM API 返回错误 429"):
                asyncio.run(
                    svc.generate_bazi_interpretation("facts", [])
                )
        assert svc._LLM_FAIL_COUNT == 1

    def test_general_exception_calls_record_failure(self, monkeypatch):
        """通用异常 → _llm_record_failure，raise RuntimeError"""
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
        monkeypatch.delenv("LLM_PROVIDER", raising=False)

        async def _fail(*a, **kw):
            raise TimeoutError("timeout")

        with patch.object(svc, "_call_openai", _fail):
            with pytest.raises(RuntimeError, match="LLM API 调用失败"):
                asyncio.run(
                    svc.generate_bazi_interpretation("facts", [])
                )
        assert svc._LLM_FAIL_COUNT == 1

    def test_anthropic_path_used_when_no_openai_key(self, monkeypatch):
        """无 OPENAI_API_KEY，有 ANTHROPIC_API_KEY → anthropic 路径"""
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test")
        monkeypatch.delenv("LLM_PROVIDER", raising=False)

        captured: list[str] = []

        async def _fake_anthropic(cfg, sys_p, user_p):
            captured.append("anthropic")
            return "generated text", svc.LlmUsage(10, 20, 0.001)

        with patch.object(svc, "_call_anthropic", _fake_anthropic):
            resp = asyncio.run(
                svc.generate_bazi_interpretation("facts", ["evidence"])
            )
        assert captured == ["anthropic"]
        assert resp.text == "generated text"
        assert not resp.is_fallback


# ══════════════════════════════════════════════════════════════════════════════
# G. stream_interpretation() — MOCK 流式输出
# ══════════════════════════════════════════════════════════════════════════════

class TestStreamInterpretation:

    def _collect(self, gen):
        """收集异步生成器所有 SSE 消息。"""
        async def _run():
            chunks = []
            async for msg in gen:
                chunks.append(msg)
            return chunks
        return asyncio.run(_run())

    def test_mock_start_event_first(self, monkeypatch):
        """第一个事件必须是 start"""
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.delenv("LLM_PROVIDER", raising=False)
        msgs = self._collect(
            svc.stream_interpretation("甲午", "水二局", "偏财格", "1990年男")
        )
        assert msgs[0].startswith("event: start")

    def test_mock_done_event_last(self, monkeypatch):
        """最后一个事件必须是 done"""
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.delenv("LLM_PROVIDER", raising=False)
        msgs = self._collect(
            svc.stream_interpretation("甲午", "水二局", "偏财格", "1990年男")
        )
        assert msgs[-1].startswith("event: done")

    def test_mock_has_chunks(self, monkeypatch):
        """中间必须有 chunk 事件"""
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.delenv("LLM_PROVIDER", raising=False)
        msgs = self._collect(
            svc.stream_interpretation("甲午", "水二局", "偏财格", "1990年男")
        )
        chunk_msgs = [m for m in msgs if m.startswith("event: chunk")]
        assert len(chunk_msgs) > 0

    def test_real_provider_error_yields_error_event(self, monkeypatch):
        """真实 provider 调用失败 → yield error 事件"""
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
        monkeypatch.delenv("LLM_PROVIDER", raising=False)

        async def _fail(*a, **kw):
            raise ConnectionError("no network")

        with patch.object(svc, "_call_openai", _fail):
            msgs = self._collect(
                svc.stream_interpretation("甲午", "水二局", "偏财格", "1990年男")
            )
        assert any("event: error" in m for m in msgs)


# ══════════════════════════════════════════════════════════════════════════════
# H. LlmResponse dataclass 验证
# ══════════════════════════════════════════════════════════════════════════════

class TestLlmResponseDataclass:

    def test_is_fallback_default_false(self):
        """is_fallback 默认为 False"""
        r = svc.LlmResponse(
            text="test", provider="mock", model="mock-v1",
            usage=svc.LlmUsage(), duration_secs=0.1, prompt_version="v1"
        )
        assert r.is_fallback is False

    def test_is_fallback_can_be_true(self):
        """is_fallback 可设为 True"""
        r = svc.LlmResponse(
            text="fallback", provider="mock", model="mock-fallback",
            usage=svc.LlmUsage(), duration_secs=0.0, prompt_version="v1",
            is_fallback=True,
        )
        assert r.is_fallback is True

    def test_llm_usage_defaults(self):
        """LlmUsage 默认值为零"""
        u = svc.LlmUsage()
        assert u.input_tokens == 0
        assert u.output_tokens == 0
        assert u.cost_usd == 0.0

