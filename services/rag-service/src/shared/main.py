"""Shared Service — FastAPI application entry point."""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from shared import __version__
from shared.config import BaseServiceSettings
from shared.middleware import setup_cors, setup_logging
from shared.utils import create_health_router

logger = logging.getLogger(__name__)


class Settings(BaseServiceSettings):
    """Settings for the shared service entry point."""

    service_name: str = "shared"
    service_version: str = __version__


settings = Settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    """Manage application lifecycle."""
    setup_logging(settings.log_level)
    logger.info("Shared Service starting up")
    yield
    logger.info("Shared Service shutting down")


app = FastAPI(
    title="Trenkwalder AI — Shared Service",
    description="Shared configuration, middleware, and health endpoint.",
    version=settings.service_version,
    lifespan=lifespan,
)

setup_cors(app, settings.cors_origins)
app.include_router(create_health_router(settings.service_name, settings.service_version))
