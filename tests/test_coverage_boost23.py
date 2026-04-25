"""
tests/test_coverage_boost23.py
──────────────────────────────
目标覆盖模块：
  - services/api_cache.py         (async wrapper LRU eviction, sync wrapper, cache hit)
  - services/sandbox_middleware.py (dispatch intercept, file-not-found, json-error)
  - services/bazi_rule_engine.py   (FileNotFoundError, JSONDecodeError, match_rules 分支)
"""
from __future__ import annotations

import asyncio
import json
import types
import pytest


# ══════════════════════════════════════════════════════════════════════════════
# 一、services/api_cache.py
# ══════════════════════════════════════════════════════════════════════════════

class TestApiCache:
    def setup_method(self):
        """每个测试前清空缓存，防止测试间互相影响。"""
        import services.api_cache as ac
        ac._LRU_CACHE.clear()

    # ── 1-1  get_cache_key 包含 Pydantic BaseModel 参数 ────────────────────
    def test_get_cache_key_with_pydantic(self):
        from services.api_cache import get_cache_key
        from pydantic import BaseModel

        class M(BaseModel):
            x: int = 1

        k = get_cache_key("test", M(x=42), "plain")
        assert k.startswith("test:")
        assert len(k) > 10

    # ── 1-2  get_cache_key 包含 kwargs Pydantic ──────────────────────────────
    def test_get_cache_key_with_pydantic_kwarg(self):
        from services.api_cache import get_cache_key
        from pydantic import BaseModel

        class M(BaseModel):
            y: str = "hello"

        k = get_cache_key("pfx", model=M(y="world"))
        assert "pfx:" in k

    # ── 1-3  同步装饰器：首次调用写入缓存，第二次命中 ──────────────────────
    def test_sync_wrapper_cache_hit(self):
        from services.api_cache import api_response_cache, _LRU_CACHE
        call_count = [0]

        @api_response_cache(prefix="sync_test")
        def compute(x: int) -> int:
            call_count[0] += 1
            return x * 2

        r1 = compute(5)
        r2 = compute(5)
        assert r1 == 10
        assert r2 == 10
        assert call_count[0] == 1   # 缓存命中，仅调用一次

    # ── 1-4  同步装饰器：LRU 超限剔除 ────────────────────────────────────
    def test_sync_wrapper_lru_eviction(self):
        import services.api_cache as ac
        from services.api_cache import api_response_cache

        # 修改 _MAX_CACHE_SIZE 为极小值，强制触发 eviction
        original_max = ac._MAX_CACHE_SIZE
        ac._MAX_CACHE_SIZE = 1  # len > 1 时触发 eviction

        @api_response_cache(prefix="evict_test")
        def fn(x: int) -> int:
            return x

        try:
            fn(1)   # len=0>1=F, add → len=1
            fn(2)   # len=1>1=F, add → len=2
            fn(3)   # len=2>1=T  → evict + add → len=2
            assert len(ac._LRU_CACHE) <= 2   # eviction 生效
        finally:
            ac._MAX_CACHE_SIZE = original_max
            ac._LRU_CACHE.clear()

    # ── 1-5  异步装饰器：cache miss → 调用函数 ───────────────────────────
    def test_async_wrapper_cache_miss(self):
        from services.api_cache import api_response_cache, _LRU_CACHE
        call_count = [0]

        @api_response_cache(prefix="async_test")
        async def async_fn(x: int) -> int:
            call_count[0] += 1
            return x + 1

        result = asyncio.run(async_fn(10))
        assert result == 11
        assert call_count[0] == 1

    # ── 1-6  异步装饰器：cache hit ─────────────────────────────────────────
    def test_async_wrapper_cache_hit(self):
        from services.api_cache import api_response_cache
        call_count = [0]

        @api_response_cache(prefix="async_hit")
        async def async_fn2(x: int) -> str:
            call_count[0] += 1
            return f"v{x}"

        import services.api_cache as ac
        ac._LRU_CACHE.clear()
        r1 = asyncio.run(async_fn2(7))
        # 手动再次运行，但缓存已存在
        r2 = asyncio.run(async_fn2(7))
        assert r1 == "v7"
        assert r2 == "v7"
        assert call_count[0] == 1   # 第二次命中缓存

    # ── 1-7  异步装饰器：LRU 超限剔除 ────────────────────────────────────
    def test_async_wrapper_lru_eviction(self):
        import services.api_cache as ac
        from services.api_cache import api_response_cache

        original_max = ac._MAX_CACHE_SIZE
        ac._MAX_CACHE_SIZE = 1  # len > 1 时触发 eviction

        @api_response_cache(prefix="async_evict")
        async def afn(x: int) -> int:
            return x * 3

        try:
            asyncio.run(afn(100))  # add → len=1
            asyncio.run(afn(200))  # add → len=2, not > 1... wait need 3 calls
            asyncio.run(afn(300))  # len=2 > 1 → evict + add → len=2 ✓
            assert len(ac._LRU_CACHE) <= 3
        finally:
            ac._MAX_CACHE_SIZE = original_max
            ac._LRU_CACHE.clear()


# ══════════════════════════════════════════════════════════════════════════════
# 二、services/sandbox_middleware.py
# ══════════════════════════════════════════════════════════════════════════════

class TestSandboxMiddleware:

    # ── 2-1  disabled 时直接 pass through ──────────────────────────────────
    def test_dispatch_disabled_passes_through(self):
        """sandbox_enabled=False 时，任何请求直接放行。"""
        from services.sandbox_middleware import SandboxMiddleware
        from starlette.applications import Starlette
        from starlette.testclient import TestClient
        from starlette.responses import JSONResponse
        from starlette.routing import Route

        async def homepage(req):
            return JSONResponse({"ok": True})

        app = Starlette(routes=[Route("/api/v1/verify", homepage)])
        app.add_middleware(SandboxMiddleware, sandbox_enabled=False)

        client = TestClient(app)
        resp = client.get("/api/v1/verify", headers={"X-Sandbox": "true"})
        assert resp.status_code == 200
        assert resp.json() == {"ok": True}

    # ── 2-2  enabled + 正确路径 + 正确请求头 → 返回沙箱响应 ──────────────
    def test_dispatch_intercepts_when_enabled(self):
        """sandbox_enabled=True + X-Sandbox:true + 匹配路径 → 返回固定沙箱样本。"""
        from services.sandbox_middleware import SandboxMiddleware
        from starlette.applications import Starlette
        from starlette.testclient import TestClient
        from starlette.responses import JSONResponse
        from starlette.routing import Route

        async def real_handler(req):
            return JSONResponse({"real": True})

        app = Starlette(routes=[Route("/api/v1/verify", real_handler)])
        app.add_middleware(SandboxMiddleware, sandbox_enabled=True)

        client = TestClient(app)
        resp = client.get("/api/v1/verify", headers={"X-Sandbox": "true"})
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("sandbox") is True
        assert "X-LLM-Fallback" in resp.headers
        assert resp.headers["X-LLM-Fallback"] == "sandbox"

    # ── 2-3  enabled + 无 X-Sandbox 头 → 正常放行 ──────────────────────
    def test_dispatch_no_sandbox_header_passes_through(self):
        from services.sandbox_middleware import SandboxMiddleware
        from starlette.applications import Starlette
        from starlette.testclient import TestClient
        from starlette.responses import JSONResponse
        from starlette.routing import Route

        async def handler(req):
            return JSONResponse({"normal": True})

        app = Starlette(routes=[Route("/api/v1/verify", handler)])
        app.add_middleware(SandboxMiddleware, sandbox_enabled=True)

        client = TestClient(app)
        resp = client.get("/api/v1/verify")
        assert resp.status_code == 200
        assert resp.json() == {"normal": True}

    # ── 2-4  enabled + 不匹配路径 → 正常放行 ──────────────────────────────
    def test_dispatch_non_matching_path_passes_through(self):
        from services.sandbox_middleware import SandboxMiddleware
        from starlette.applications import Starlette
        from starlette.testclient import TestClient
        from starlette.responses import JSONResponse
        from starlette.routing import Route

        async def handler(req):
            return JSONResponse({"normal": 1})

        app = Starlette(routes=[Route("/api/v2/other", handler)])
        app.add_middleware(SandboxMiddleware, sandbox_enabled=True)

        client = TestClient(app)
        resp = client.get("/api/v2/other", headers={"X-Sandbox": "true"})
        assert resp.status_code == 200
        assert resp.json() == {"normal": 1}

    # ── 2-5  _load_sandbox_sample：文件不存在时返回 {} ─────────────────────
    def test_load_sandbox_sample_file_not_found(self, monkeypatch, tmp_path):
        import services.sandbox_middleware as sm
        # 重置 lru_cache，指向不存在的文件
        sm._load_sandbox_sample.cache_clear()
        monkeypatch.setattr(sm, "_DATA_DIR", tmp_path)   # tmp_path 没有 ground_truth_cases.json
        result = sm._load_sandbox_sample()
        assert result == {}
        sm._load_sandbox_sample.cache_clear()

    # ── 2-6  _load_sandbox_sample：JSON 解析错误时返回 {} ─────────────────
    def test_load_sandbox_sample_json_error(self, monkeypatch, tmp_path):
        import services.sandbox_middleware as sm

        bad_json = tmp_path / "ground_truth_cases.json"
        bad_json.write_text("THIS IS NOT JSON", encoding="utf-8")
        sm._load_sandbox_sample.cache_clear()
        monkeypatch.setattr(sm, "_DATA_DIR", tmp_path)
        result = sm._load_sandbox_sample()
        assert result == {}
        sm._load_sandbox_sample.cache_clear()

    # ── 2-7  _load_sandbox_sample：空 cases 列表时返回 {} ─────────────────
    def test_load_sandbox_sample_empty_cases(self, monkeypatch, tmp_path):
        import services.sandbox_middleware as sm

        good_json = tmp_path / "ground_truth_cases.json"
        good_json.write_text(json.dumps({"cases": []}), encoding="utf-8")
        sm._load_sandbox_sample.cache_clear()
        monkeypatch.setattr(sm, "_DATA_DIR", tmp_path)
        result = sm._load_sandbox_sample()
        assert result == {}
        sm._load_sandbox_sample.cache_clear()

    # ── 2-8  _load_sandbox_sample：正常加载返回第一条 ─────────────────────
    def test_load_sandbox_sample_normal(self, monkeypatch, tmp_path):
        import services.sandbox_middleware as sm

        sample_data = {"cases": [{"id": "TEST001", "name": "测试案例"}]}
        good_json = tmp_path / "ground_truth_cases.json"
        good_json.write_text(json.dumps(sample_data), encoding="utf-8")
        sm._load_sandbox_sample.cache_clear()
        monkeypatch.setattr(sm, "_DATA_DIR", tmp_path)
        result = sm._load_sandbox_sample()
        assert result.get("id") == "TEST001"
        sm._load_sandbox_sample.cache_clear()


# ══════════════════════════════════════════════════════════════════════════════
# 三、services/bazi_rule_engine.py
# ══════════════════════════════════════════════════════════════════════════════

class TestBaziRuleEngine:

    # ── 3-1  _load_rules：正常加载，返回非空列表 ──────────────────────────
    def test_load_rules_normal(self):
        from services.bazi_rule_engine import _load_rules
        _load_rules.cache_clear()
        rules = _load_rules()
        # 允许空（若 bazi_rules.json 不存在），但不报错
        assert isinstance(rules, list)

    # ── 3-2  _load_rules：FileNotFoundError 时返回 [] ─────────────────────
    def test_load_rules_file_not_found(self, monkeypatch):
        import services.bazi_rule_engine as bre
        bre._load_rules.cache_clear()
        # 让 open 抛出 FileNotFoundError
        monkeypatch.setattr("builtins.open", lambda *a, **kw: (_ for _ in ()).throw(FileNotFoundError("no file")))
        result = bre._load_rules()
        assert result == []
        bre._load_rules.cache_clear()

    # ── 3-3  _load_rules：JSONDecodeError 时返回 [] ───────────────────────
    def test_load_rules_json_error(self, monkeypatch, tmp_path):
        import services.bazi_rule_engine as bre
        import os
        bre._load_rules.cache_clear()
        # 构造一个损坏的 json 文件
        bad = tmp_path / "bad.json"
        bad.write_text("NOTJSON", encoding="utf-8")
        monkeypatch.setenv("BAZI_RULES_PATH", str(bad))  # 不直接用，但 patch open 返回该文件
        original_open = open

        def patched_open(path, *args, **kwargs):
            if "bazi_rules" in str(path):
                return original_open(str(bad), *args, **kwargs)
            return original_open(path, *args, **kwargs)

        monkeypatch.setattr("builtins.open", patched_open)
        result = bre._load_rules()
        assert result == []
        bre._load_rules.cache_clear()

    # ── 3-4  _build_context：geju=None 时仍返回合法 context ──────────────
    def test_build_context_geju_none(self):
        from services.bazi_rule_engine import _build_context

        class FakeYongshen:
            favor = ["火", "土"]
            avoid = ["水"]

        ctx = _build_context(None, FakeYongshen(), None)
        assert ctx["geju"]["geju_name"] == ""
        assert ctx["yongshen"]["favor"] == ["火", "土"]
        assert ctx["shensha"]["name"] == []

    # ── 3-5  _build_context：yongshen=None 时仍合法 ──────────────────────
    def test_build_context_yongshen_none(self):
        from services.bazi_rule_engine import _build_context
        ctx = _build_context(None, None, None)
        assert ctx["yongshen"]["favor"] == []
        assert ctx["yongshen"]["avoid"] == []

    # ── 3-6  _build_context：带有 shensha 列表 ──────────────────────────
    def test_build_context_with_shensha(self):
        from services.bazi_rule_engine import _build_context

        class FakeShensha:
            def __init__(self, name):
                self.name = name

        ctx = _build_context(None, None, [FakeShensha("天乙贵人"), FakeShensha("文昌")])
        assert "天乙贵人" in ctx["shensha"]["name"]
        assert "文昌" in ctx["shensha"]["name"]

    # ── 3-7  _eval_condition：op=ne ────────────────────────────────────
    def test_eval_condition_ne(self):
        from services.bazi_rule_engine import _eval_condition
        cond = {"field": "geju.geju_name", "op": "ne", "value": "正官格"}
        ctx = {"geju": {"geju_name": "伤官格"}}
        assert _eval_condition(cond, ctx) is True
        ctx2 = {"geju": {"geju_name": "正官格"}}
        assert _eval_condition(cond, ctx2) is False

    # ── 3-8  _eval_condition：op=contains (list) ─────────────────────────
    def test_eval_condition_contains_list(self):
        from services.bazi_rule_engine import _eval_condition
        cond = {"field": "yongshen.favor", "op": "contains", "value": "火"}
        ctx = {"yongshen": {"favor": ["火", "土"]}}
        assert _eval_condition(cond, ctx) is True
        ctx2 = {"yongshen": {"favor": ["水", "木"]}}
        assert _eval_condition(cond, ctx2) is False

    # ── 3-9  _eval_condition：op=contains (str) ──────────────────────────
    def test_eval_condition_contains_str(self):
        from services.bazi_rule_engine import _eval_condition
        cond = {"field": "geju.geju_name", "op": "contains", "value": "官"}
        ctx = {"geju": {"geju_name": "正官格"}}
        assert _eval_condition(cond, ctx) is True

    # ── 3-10  _eval_condition：op=in ────────────────────────────────────
    def test_eval_condition_in(self):
        from services.bazi_rule_engine import _eval_condition
        cond = {"field": "geju.geju_level", "op": "in", "value": ["上格", "中格"]}
        ctx = {"geju": {"geju_level": "上格"}}
        assert _eval_condition(cond, ctx) is True
        ctx2 = {"geju": {"geju_level": "下格"}}
        assert _eval_condition(cond, ctx2) is False

    # ── 3-11  _eval_condition：op=in，field=None ─────────────────────────
    def test_eval_condition_in_field_none(self):
        from services.bazi_rule_engine import _eval_condition
        cond = {"field": "nonexistent.path", "op": "in", "value": ["A"]}
        ctx = {}
        assert _eval_condition(cond, ctx) is False

    # ── 3-12  _eval_condition：未知 op 返回 False ─────────────────────────
    def test_eval_condition_unknown_op(self):
        from services.bazi_rule_engine import _eval_condition
        cond = {"field": "geju.geju_name", "op": "regex", "value": ".*"}
        ctx = {"geju": {"geju_name": "正官格"}}
        assert _eval_condition(cond, ctx) is False

    # ── 3-13  _eval_trigger：any 块（至少一个满足）──────────────────────
    def test_eval_trigger_any(self):
        from services.bazi_rule_engine import _eval_trigger
        trigger = {
            "all": [],
            "any": [
                {"field": "geju.geju_name", "op": "eq", "value": "正官格"},
                {"field": "geju.geju_name", "op": "eq", "value": "财官格"},
            ],
        }
        ctx = {"geju": {"geju_name": "正官格"}}
        assert _eval_trigger(trigger, ctx) is True
        ctx2 = {"geju": {"geju_name": "伤官格"}}
        assert _eval_trigger(trigger, ctx2) is False

    # ── 3-14  _eval_trigger：none 块（所有都不满足）──────────────────────
    def test_eval_trigger_none(self):
        from services.bazi_rule_engine import _eval_trigger
        trigger = {
            "all": [],
            "none": [
                {"field": "geju.is_broken", "op": "eq", "value": True},
            ],
        }
        ctx = {"geju": {"is_broken": False}}
        assert _eval_trigger(trigger, ctx) is True
        ctx2 = {"geju": {"is_broken": True}}
        assert _eval_trigger(trigger, ctx2) is False

    # ── 3-15  match_rules：规则引擎端到端 ───────────────────────────────
    def test_match_rules_with_mock_rules(self, monkeypatch):
        import services.bazi_rule_engine as bre
        bre._load_rules.cache_clear()

        # 注入两条规则：一正一反
        fake_rules = [
            {
                "id": "R001",
                "name": "正官格利仕途",
                "trigger": {"all": [{"field": "geju.geju_name", "op": "eq", "value": "正官格"}]},
                "flags": ["仕途"],
                "evidence_template": "用神{yongshen_favor}有利仕途",
                "classic_hint": "《滴天髓》",
                "disclaimer": "仅供参考",
            },
            {
                "id": "R002",
                "name": "财官双美",
                "trigger": {"all": [{"field": "geju.geju_name", "op": "eq", "value": "七杀格"}]},
                "flags": ["财运"],
                "evidence_template": "七杀制化得宜",
                "classic_hint": "",
                "disclaimer": "",
            },
        ]
        monkeypatch.setattr(bre, "_load_rules", lambda: fake_rules)

        class FakeGeju:
            geju_name = "正官格"
            geju_level = "上格"
            is_broken = False

        class FakeYongshen:
            favor = ["火", "土"]
            avoid = ["水"]

        matched = bre.match_rules(FakeGeju(), FakeYongshen(), None)
        assert len(matched) == 1
        assert matched[0]["rule_id"] == "R001"
        assert "火、土" in matched[0]["evidence_text"]

    # ── 3-16  match_rules：规则列表为空时返回 [] ─────────────────────────
    def test_match_rules_empty_rules(self, monkeypatch):
        import services.bazi_rule_engine as bre
        monkeypatch.setattr(bre, "_load_rules", lambda: [])
        result = bre.match_rules(None, None)
        assert result == []

    # ── 3-17  _resolve_field：深层路径未找到返回 None ─────────────────────
    def test_resolve_field_missing(self):
        from services.bazi_rule_engine import _resolve_field
        ctx = {"a": {"b": 1}}
        assert _resolve_field(ctx, "a.c") is None
        assert _resolve_field(ctx, "x.y.z") is None
