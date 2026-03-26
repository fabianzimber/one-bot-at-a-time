"""Database seeding script — populates the database with mock data."""

import logging

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from hr_service.database.models import Employee, SalaryRecord, TimeEntryRecord, VacationRecord
from hr_service.services.hr_data import generate_seed_data

logger = logging.getLogger(__name__)


async def seed_database(session: AsyncSession, employee_count: int = 50) -> dict:
    """Seed the database with realistic mock data if it is empty."""
    existing = await session.exec(select(Employee.id).limit(1))
    if existing.first() is not None:
        logger.info("Database already seeded")
        return {"employees_created": 0, "message": "Database already seeded"}

    payload = await generate_seed_data(employee_count)

    session.add_all([Employee(**employee) for employee in payload["employees"]])
    session.add_all([SalaryRecord(**salary) for salary in payload["salaries"]])
    session.add_all([VacationRecord(**vacation) for vacation in payload["vacations"]])
    session.add_all([TimeEntryRecord(**entry) for entry in payload["time_entries"]])
    await session.commit()

    summary = {
        "employees_created": len(payload["employees"]),
        "vacation_records_created": len(payload["vacations"]),
        "salary_records_created": len(payload["salaries"]),
        "time_entries_created": len(payload["time_entries"]),
    }
    logger.info("Database seed completed", extra=summary)
    return summary
