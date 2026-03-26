"""Embedding service — generates vector embeddings via OpenAI."""

import logging

logger = logging.getLogger(__name__)


class Embedder:
    """Generates embeddings using OpenAI's text-embedding API."""

    def __init__(self, model: str = "text-embedding-3-small", api_key: str = "") -> None:
        self.model = model
        self.api_key = api_key
        logger.info("Embedder initialized", extra={"model": model})

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for a batch of texts."""
        # TODO: Implement with openai.AsyncOpenAI client
        # client = AsyncOpenAI(api_key=self.api_key)
        # response = await client.embeddings.create(model=self.model, input=texts)
        # return [item.embedding for item in response.data]
        logger.info("Embedding stub called", extra={"count": len(texts)})
        return [[0.0] * 1536 for _ in texts]

    async def embed_query(self, query: str) -> list[float]:
        """Generate embedding for a single search query."""
        results = await self.embed_texts([query])
        return results[0]
