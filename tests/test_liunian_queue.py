"""T075 unit tests — liunian Redis queue with in-memory fake client."""

from __future__ import annotations

import json
from typing import Any

import pytest

from services import liunian_queue as q


class _FakeRedis:
    def __init__(self) -> None:
        self.lists: dict[str, list[str]] = {}
        self.hashes: dict[str, dict[str, int]] = {}

    def ping(self) -> bool:
        return True

    def rpush(self, key: str, value: str) -> int:
        self.lists.setdefault(key, []).append(value)
        return len(self.lists[key])

    def llen(self, key: str) -> int:
        return len(self.lists.get(key, []))

    def hincrby(self, key: str, field: str, amount: int) -> int:
        bucket = self.hashes.setdefault(key, {})
        bucket[field] = int(bucket.get(field, 0)) + int(amount)
        return bucket[field]

    def hgetall(self, key: str) -> dict[str, Any]:
        return {k: str(v) for k, v in self.hashes.get(key, {}).items()}

    def blpop(self, key: str, timeout: int = 5):  # noqa: ARG002
        items = self.lists.get(key) or []
        if not items:
            return None
        return key, items.pop(0)


@pytest.fixture()
def fake_redis(monkeypatch: pytest.MonkeyPatch) -> _FakeRedis:
    fake = _FakeRedis()
    monkeypatch.setenv("REDIS_URL", "redis://fake:6379/0")
    monkeypatch.setattr(q, "_redis_client", lambda: fake)
    return fake


def test_enqueue_and_dequeue(fake_redis: _FakeRedis) -> None:
    assert q.enqueue_liunian_job(
        task_id="t1",
        case_id="c1",
        year=2026,
        include_months=True,
    )
    assert q.queue_depth() == 1
    job = q.dequeue_liunian_job(timeout_sec=1)
    assert job is not None
    assert job["task_id"] == "t1"
    assert job["case_id"] == "c1"
    assert job["year"] == 2026
    assert job["include_months"] is True
    assert q.queue_depth() == 0
    metrics = q.read_metrics()
    assert metrics.get("enqueued") == 1


def test_poison_message_counted(fake_redis: _FakeRedis) -> None:
    fake_redis.rpush(q.LIUNIAN_QUEUE_KEY, "not-json")
    assert q.dequeue_liunian_job(timeout_sec=1) is None
    assert q.read_metrics().get("poison") == 1


def test_dispatch_uses_redis_when_available(fake_redis: _FakeRedis) -> None:
    called = {"n": 0}

    async def runner(*_a, **_k):
        called["n"] += 1

    backend = q.dispatch_liunian_job(
        task_id="t2",
        case_id="c2",
        year=2025,
        include_months=False,
        runner=runner,
    )
    assert backend == "redis"
    assert called["n"] == 0
    assert fake_redis.llen(q.LIUNIAN_QUEUE_KEY) == 1
    raw = fake_redis.lists[q.LIUNIAN_QUEUE_KEY][0]
    assert json.loads(raw)["task_id"] == "t2"


def test_dispatch_falls_back_to_asyncio(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("REDIS_URL", raising=False)
    monkeypatch.delenv("LIUNIAN_REDIS_URL", raising=False)
    monkeypatch.setattr(q, "_redis_client", lambda: None)

    created: list[object] = []

    def fake_create_task(coro):
        created.append(coro)
        coro.close()
        return None

    monkeypatch.setattr(q.asyncio, "create_task", fake_create_task)

    async def runner(*_a, **_k):
        return None

    backend = q.dispatch_liunian_job(
        task_id="t3",
        case_id="c3",
        year=2024,
        include_months=False,
        runner=runner,
    )
    assert backend == "asyncio"
    assert len(created) == 1
