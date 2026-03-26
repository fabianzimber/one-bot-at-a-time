"""Reusable health check router for all services."""

from datetime import UTC, datetime

from fastapi import APIRouter
from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str = "healthy"
    service: str
    version: str
    timestamp: str


def create_health_router(service_name: str, version: str) -> APIRouter:
    """Create a health check router for a service."""
    router = APIRouter(tags=["health"])

    @router.get("/health", response_model=HealthResponse)
    async def health_check() -> HealthResponse:
        return HealthResponse(
            service=service_name,
            version=version,
            timestamp=datetime.now(UTC).isoformat(),
        )

    return router
