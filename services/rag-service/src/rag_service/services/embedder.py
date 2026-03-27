"""Embedding service — generates vector embeddings via OpenAI."""

import hashlib
import logging

from openai import AsyncOpenAI

logger = logging.getLogger(__name__)


class Embedder:
    """Generates embeddings using OpenAI's text-embedding API."""

    def __init__(self, model: str = "text-embedding-3-small", api_key: str = "") -> None:
        self.model = model
        self.api_key = api_key
        self._client = AsyncOpenAI(api_key=api_key) if api_key and not api_key.startswith("test-") else None
        logger.info("Embedder initialized", extra={"model": model})

    def _fallback_embedding(self, text: str, dimensions: int = 1536) -> list[float]:
        """Generate a deterministic pseudo-embedding by hashing successive blocks."""
        values: list[float] = []
        block = 0
        while len(values) < dimensions:
            digest = hashlib.sha256(f"{text}:{block}".encode()).digest()
            for byte in digest:
                if len(values) >= dimensions:
                    break
                values.append(((byte / 255) * 2) - 1)
            block += 1
        return values

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for a batch of texts."""
        if self._client is None:
            logger.info("Using fallback embeddings", extra={"count": len(texts)})
            return [self._fallback_embedding(text) for text in texts]

        response = await self._client.embeddings.create(model=self.model, input=texts)
        return [item.embedding for item in response.data]

    async def embed_query(self, query: str) -> list[float]:
        """Generate embedding for a single search query."""
        results = await self.embed_texts([query])
        return results[0]
