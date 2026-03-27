"""Runtime initialization helpers for the RAG service."""

import asyncio
from datetime import UTC, datetime

from fastapi import FastAPI

from rag_service.config import settings
from rag_service.database import ensure_database_ready
from rag_service.services.embedder import Embedder
from rag_service.services.vector_store import VectorStore
from shared.middleware import setup_logging

_init_lock = asyncio.Lock()


async def ensure_runtime_ready(app: FastAPI) -> None:
    await ensure_database_ready()
    if hasattr(app.state, "embedder") and hasattr(app.state, "vector_store") and hasattr(app.state, "settings"):
        return

    async with _init_lock:
        await ensure_database_ready()
        if hasattr(app.state, "embedder") and hasattr(app.state, "vector_store") and hasattr(app.state, "settings"):
            return

        setup_logging(settings.log_level)
        await ensure_database_ready()
        app.state.settings = settings
        app.state.now_factory = lambda: datetime.now(UTC)
        app.state.embedder = Embedder(model=settings.embedding_model, api_key=settings.openai_api_key)
        app.state.vector_store = VectorStore(
            host=settings.chroma_host,
            port=settings.chroma_port,
            collection_name=settings.chroma_collection,
            backend=settings.vector_backend,
        )
        await app.state.vector_store.initialize()
