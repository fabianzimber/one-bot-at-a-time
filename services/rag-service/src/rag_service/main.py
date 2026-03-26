"""RAG Service — FastAPI application entry point."""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from rag_service.config import settings
from rag_service.routers.documents import router as documents_router
from rag_service.routers.ingest import router as ingest_router
from rag_service.routers.search import router as search_router
from shared.middleware import setup_cors, setup_logging
from shared.utils import create_health_router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    """Manage application lifecycle."""
    setup_logging(settings.log_level)
    logger.info(
        "RAG Service starting up",
        extra={"chroma_host": settings.chroma_host, "embedding_model": settings.embedding_model},
    )

    # TODO: Initialize ChromaDB client and OpenAI embeddings client
    yield

    logger.info("RAG Service shutting down")


app = FastAPI(
    title="Trenkwalder AI — RAG Service",
    description="Document ingestion, chunking, embedding, and semantic search.",
    version=settings.service_version,
    lifespan=lifespan,
)

setup_cors(app, settings.cors_origins)
app.include_router(create_health_router(settings.service_name, settings.service_version))
app.include_router(ingest_router, prefix="/api/v1", tags=["ingest"])
app.include_router(search_router, prefix="/api/v1", tags=["search"])
app.include_router(documents_router, prefix="/api/v1", tags=["documents"])
