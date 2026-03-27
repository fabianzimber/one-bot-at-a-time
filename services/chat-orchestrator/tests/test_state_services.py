"""Tests for stateful chat helpers and SSE streaming."""

from collections import deque

import pytest

from chat_orchestrator.services.conversation import ConversationStore
from chat_orchestrator.services.rate_limit import RateLimiter
from chat_orchestrator.services.streaming import stream_chat_response
from shared.models import Message, MessageRole


class FakeConversationPipeline:
    def __init__(self, store: "FakeConversationRedis") -> None:
        self._store = store
        self._commands: list[tuple[str, tuple[object, ...]]] = []

    def delete(self, key: str) -> None:
        self._commands.append(("delete", (key,)))

    def rpush(self, key: str, *values: str) -> None:
        self._commands.append(("rpush", (key, *values)))

    def expire(self, key: str, ttl: int) -> None:
        self._commands.append(("expire", (key, ttl)))

    async def execute(self) -> list[object]:
        results: list[object] = []
        for cmd, args in self._commands:
            if cmd == "delete":
                self._store.store.pop(str(args[0]), None)
                results.append(0)
            elif cmd == "rpush":
                key = str(args[0])
                self._store.store.setdefault(key, []).extend(str(v) for v in args[1:])
                results.append(len(self._store.store[key]))
            elif cmd == "expire":
                self._store.expirations[str(args[0])] = int(args[1])
                results.append(True)
        return results


class FakeConversationRedis:
    def __init__(self, *, fail_ping: bool = False) -> None:
        self.fail_ping = fail_ping
        self.store: dict[str, list[str]] = {}
        self.expirations: dict[str, int] = {}
        self.closed = False

    async def ping(self) -> None:
        if self.fail_ping:
            raise RuntimeError("redis unavailable")

    async def aclose(self) -> None:
        self.closed = True

    async def lrange(self, key: str, start: int, end: int) -> list[str]:
        del start, end
        return list(self.store.get(key, []))

    async def rpush(self, key: str, *values: str) -> None:
        self.store.setdefault(key, []).extend(values)

    async def expire(self, key: str, ttl: int) -> None:
        self.expirations[key] = ttl

    async def delete(self, key: str) -> None:
        self.store.pop(key, None)

    def pipeline(self) -> FakeConversationPipeline:
        return FakeConversationPipeline(self)


class FakePipeline:
    def __init__(self, count: int) -> None:
        self.count = count
        self.operations: list[tuple[str, object]] = []

    def zremrangebyscore(self, key: str, minimum: float, maximum: float) -> None:
        self.operations.append(("zremrangebyscore", (key, minimum, maximum)))

    def zadd(self, key: str, values: dict[str, float]) -> None:
        self.operations.append(("zadd", (key, values)))

    def zcard(self, key: str) -> None:
        self.operations.append(("zcard", key))

    def expire(self, key: str, ttl: int) -> None:
        self.operations.append(("expire", (key, ttl)))

    async def execute(self) -> list[object]:
        return [0, 1, self.count + 1, True]


class FakeRateRedis:
    def __init__(self, *, count: int = 0, fail_ping: bool = False) -> None:
        self.count = count
        self.fail_ping = fail_ping
        self.pipeline_instance = FakePipeline(count)
        self.zadd_calls: list[tuple[str, dict[str, float]]] = []
        self.zrem_calls: list[tuple[str, str]] = []
        self.closed = False

    async def ping(self) -> None:
        if self.fail_ping:
            raise RuntimeError("redis unavailable")

    def pipeline(self) -> FakePipeline:
        return self.pipeline_instance

    async def zadd(self, key: str, values: dict[str, float]) -> None:
        self.zadd_calls.append((key, values))

    async def zrem(self, key: str, *members: str) -> None:
        self.zrem_calls.append((key, members[0] if members else ""))

    async def aclose(self) -> None:
        self.closed = True


@pytest.mark.asyncio
async def test_conversation_store_memory_roundtrip() -> None:
    store = ConversationStore(redis_url="")
    message = Message(role=MessageRole.USER, content="Hallo")

    await store.append("conv-1", message)
    fetched = await store.get("conv-1")
    await store.replace("conv-1", [message, Message(role=MessageRole.ASSISTANT, content="Hi")])

    assert fetched == [message]
    assert len(await store.get("conv-1")) == 2


@pytest.mark.asyncio
async def test_conversation_store_redis_roundtrip_and_close() -> None:
    store = ConversationStore(redis_url="")
    store._client = FakeConversationRedis()
    await store.connect()

    await store.append("conv-redis", Message(role=MessageRole.USER, content="Hallo"))
    messages = await store.get("conv-redis")
    await store.replace("conv-redis", [Message(role=MessageRole.ASSISTANT, content="Antwort")])
    await store.close()

    assert store._connected is True
    assert messages[0].content == "Hallo"
    assert store._client.closed is True


@pytest.mark.asyncio
async def test_conversation_store_connect_falls_back_when_ping_fails() -> None:
    store = ConversationStore(redis_url="")
    store._client = FakeConversationRedis(fail_ping=True)

    await store.connect()

    assert store._connected is False


@pytest.mark.asyncio
async def test_rate_limiter_memory_allows_then_denies() -> None:
    limiter = RateLimiter(redis_url="", limit=2, window_seconds=60)

    first = await limiter.allow("client-1")
    second = await limiter.allow("client-1")
    third = await limiter.allow("client-1")

    assert first == (True, 0)
    assert second == (True, 0)
    assert third == (False, 60)
    assert isinstance(limiter._memory["client-1"], deque)


@pytest.mark.asyncio
async def test_rate_limiter_redis_branch_allows_then_denies() -> None:
    allowed_limiter = RateLimiter(redis_url="", limit=2, window_seconds=60)
    allowed_limiter._client = FakeRateRedis(count=1)
    await allowed_limiter.connect()
    allowed = await allowed_limiter.allow("client-2")

    denied_limiter = RateLimiter(redis_url="", limit=2, window_seconds=60)
    denied_limiter._client = FakeRateRedis(count=2)
    await denied_limiter.connect()
    denied = await denied_limiter.allow("client-3")
    await allowed_limiter.close()
    await denied_limiter.close()

    assert allowed == (True, 0)
    assert denied == (False, 60)
    assert len(denied_limiter._client.zrem_calls) == 1


@pytest.mark.asyncio
async def test_stream_chat_response_emits_start_content_and_done_events() -> None:
    events = [event async for event in stream_chat_response(conversation_id="conv-stream", message="A" * 70)]

    assert [event["event"] for event in events] == ["start", "content", "content", "done"]
    assert "conv-stream" in events[0]["data"]
