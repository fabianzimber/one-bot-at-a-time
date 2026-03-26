"""HR Service — FastAPI application entry point."""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from hr_service.config import settings
from hr_service.routers.employees import router as employees_router
from hr_service.routers.org import router as org_router
from hr_service.routers.salary import router as salary_router
from hr_service.routers.timetracking import router as timetracking_router
from hr_service.routers.vacation import router as vacation_router
from shared.middleware import setup_cors, setup_logging
from shared.utils import create_health_router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    """Manage application lifecycle."""
    setup_logging(settings.log_level)
    logger.info("HR Service starting up", extra={"database": settings.database_url})

    # TODO: Initialize database, run migrations, seed if empty
    yield

    logger.info("HR Service shutting down")


app = FastAPI(
    title="Trenkwalder AI — HR Service",
    description="Mock HR API: employees, vacation, salary, time tracking, org chart.",
    version=settings.service_version,
    lifespan=lifespan,
)

setup_cors(app, settings.cors_origins)
app.include_router(create_health_router(settings.service_name, settings.service_version))
app.include_router(employees_router, prefix="/api/v1", tags=["employees"])
app.include_router(vacation_router, prefix="/api/v1", tags=["vacation"])
app.include_router(salary_router, prefix="/api/v1", tags=["salary"])
app.include_router(timetracking_router, prefix="/api/v1", tags=["timetracking"])
app.include_router(org_router, prefix="/api/v1", tags=["org"])
