"""Rate limiting helpers for chat endpoints."""

import time
from collections import defaultdict, deque

import redis.asyncio as redis


class RateLimiter:
    """Sliding-window rate limiter backed by Redis with an in-memory fallback."""

    def __init__(self, redis_url: str, limit: int = 20, window_seconds: int = 60) -> None:
        self.limit = limit
        self.window_seconds = window_seconds
        self._client = redis.from_url(redis_url, decode_responses=True) if redis_url else None
        self._memory: dict[str, deque[float]] = defaultdict(deque)
        self._connected = False

    async def connect(self) -> None:
        if self._client is None:
            return
        try:
            await self._client.ping()
            self._connected = True
        except Exception:  # pragma: no cover - network failure fallback
            self._connected = False

    async def close(self) -> None:
        if self._client is not None:
            await self._client.aclose()

    async def allow(self, key: str) -> tuple[bool, int]:
        now = time.time()
        window_start = now - self.window_seconds

        if self._connected and self._client is not None:
            redis_key = f"rate-limit:{key}"
            pipeline = self._client.pipeline()
            pipeline.zremrangebyscore(redis_key, 0, window_start)
            pipeline.zcard(redis_key)
            pipeline.expire(redis_key, self.window_seconds)
            _, count, _ = await pipeline.execute()
            if int(count) >= self.limit:
                return False, self.window_seconds
            # Only add the request after confirming we're under the limit
            await self._client.zadd(redis_key, {str(now): now})
            return True, 0

        # Prune stale entries and clean up keys with no active requests
        if key in self._memory:
            bucket = self._memory[key]
            while bucket and bucket[0] <= window_start:
                bucket.popleft()
            if not bucket:
                del self._memory[key]

        bucket = self._memory[key]
        if len(bucket) >= self.limit:
            return False, self.window_seconds
        bucket.append(now)
        return True, 0
