"""Chat Orchestrator — FastAPI application entry point."""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from chat_orchestrator.config import settings
from chat_orchestrator.routers.chat import router as chat_router
from shared.middleware import setup_cors, setup_logging
from shared.utils import create_health_router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    """Manage application lifecycle — startup and shutdown."""
    setup_logging(settings.log_level)
    logger.info("Chat Orchestrator starting up", extra={"model": settings.llm_model})

    # TODO: Initialize OpenAI client, Redis connection, httpx client
    yield

    logger.info("Chat Orchestrator shutting down")
    # TODO: Close Redis, httpx connections


app = FastAPI(
    title="Trenkwalder AI — Chat Orchestrator",
    description="LLM routing, tool use orchestration, and response streaming.",
    version=settings.service_version,
    lifespan=lifespan,
)

setup_cors(app, settings.cors_origins)
app.include_router(create_health_router(settings.service_name, settings.service_version))
app.include_router(chat_router, prefix="/api/v1", tags=["chat"])
