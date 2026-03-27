"""Conversation state management with Redis fallback."""

import logging
from collections import defaultdict

import redis.asyncio as redis

from shared.models import Message

logger = logging.getLogger(__name__)


class ConversationStore:
    """Stores conversation history in Redis with an in-memory fallback."""

    def __init__(self, redis_url: str) -> None:
        self.redis_url = redis_url
        self._client = redis.from_url(redis_url, decode_responses=True) if redis_url else None
        self._memory: dict[str, list[Message]] = defaultdict(list)
        self._connected = False

    async def connect(self) -> None:
        if self._client is None:
            return

        try:
            await self._client.ping()
            self._connected = True
        except Exception:  # pragma: no cover - network failure fallback
            logger.warning("Redis unavailable, using in-memory conversation store")
            self._connected = False

    async def close(self) -> None:
        if self._client is not None:
            await self._client.aclose()

    async def get(self, conversation_id: str) -> list[Message]:
        if self._connected and self._client is not None:
            raw_messages = await self._client.lrange(f"conversation:{conversation_id}", 0, -1)
            return [Message.model_validate_json(item) for item in raw_messages]
        return list(self._memory[conversation_id])

    async def append(self, conversation_id: str, message: Message) -> None:
        if self._connected and self._client is not None:
            key = f"conversation:{conversation_id}"
            await self._client.rpush(key, message.model_dump_json())
            await self._client.expire(key, 86400)
            return
        self._memory[conversation_id].append(message)

    async def replace(self, conversation_id: str, messages: list[Message]) -> None:
        if self._connected and self._client is not None:
            key = f"conversation:{conversation_id}"
            payload = [message.model_dump_json() for message in messages]
            pipeline = self._client.pipeline()
            pipeline.delete(key)
            if payload:
                pipeline.rpush(key, *payload)
                pipeline.expire(key, 86400)
            await pipeline.execute()
            return
        self._memory[conversation_id] = list(messages)
