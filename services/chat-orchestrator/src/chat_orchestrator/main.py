"""Chat Orchestrator — FastAPI application entry point."""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI

from chat_orchestrator.config import settings
from chat_orchestrator.routers.chat import router as chat_router
from chat_orchestrator.runtime import close_runtime, ensure_runtime_ready
from shared.middleware import build_internal_api_key_dependency, setup_cors, setup_logging
from shared.utils import create_health_router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    """Manage application lifecycle — startup and shutdown."""
    setup_logging(settings.log_level)
    logger.info("Chat Orchestrator starting up", extra={"model": settings.llm_model})

    await ensure_runtime_ready(app)
    yield

    await close_runtime(app)
    logger.info("Chat Orchestrator shutting down")


app = FastAPI(
    title="Trenkwalder AI — Chat Orchestrator",
    description="LLM routing, tool use orchestration, and response streaming.",
    version=settings.service_version,
    lifespan=lifespan,
)

setup_cors(app, settings.cors_origins)
app.include_router(create_health_router(settings.service_name, settings.service_version))
protected_dependencies = [Depends(build_internal_api_key_dependency(settings.internal_api_key))]
app.include_router(chat_router, prefix="/api/v1", tags=["chat"], dependencies=protected_dependencies)
