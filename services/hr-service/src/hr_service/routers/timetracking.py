"""Time tracking endpoints."""

import logging
from datetime import date

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from hr_service.database import TimeEntryRecord, get_session

logger = logging.getLogger(__name__)

router = APIRouter()
session_dependency = Depends(get_session)


class TimeEntry(BaseModel):
    employee_id: str
    date: date
    hours_worked: float
    project: str | None = None


class TimeTrackingSummary(BaseModel):
    employee_id: str
    period_start: date
    period_end: date
    total_hours: float
    entries: list[TimeEntry]


@router.get("/employees/{employee_id}/timetracking", response_model=TimeTrackingSummary)
async def get_time_tracking(
    employee_id: str,
    start: date | None = None,
    end: date | None = None,
    session: AsyncSession = session_dependency,
) -> TimeTrackingSummary:
    """Get time tracking entries for an employee."""
    period_start = start or date(2026, 3, 1)
    period_end = end or date.today()
    statement = (
        select(TimeEntryRecord)
        .where(
            TimeEntryRecord.employee_id == employee_id,
            TimeEntryRecord.entry_date >= period_start,
            TimeEntryRecord.entry_date <= period_end,
        )
        .order_by(TimeEntryRecord.entry_date)
    )
    result = await session.exec(statement)
    records = result.all()
    entries = [
        TimeEntry(
            employee_id=record.employee_id,
            date=record.entry_date,
            hours_worked=record.hours_worked,
            project=record.project,
        )
        for record in records
    ]
    return TimeTrackingSummary(
        employee_id=employee_id,
        period_start=period_start,
        period_end=period_end,
        total_hours=round(sum(record.hours_worked for record in records), 2),
        entries=entries,
    )
