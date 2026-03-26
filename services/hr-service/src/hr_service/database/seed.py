"""Database seeding script — populates the database with mock data."""

import logging

from hr_service.services.hr_data import generate_seed_data

logger = logging.getLogger(__name__)


async def seed_database(employee_count: int = 50) -> None:
    """Seed the database with realistic mock data if empty."""
    # TODO: Check if database is empty, then generate and insert
    result = await generate_seed_data(employee_count)
    logger.info("Database seed completed", extra=result)
