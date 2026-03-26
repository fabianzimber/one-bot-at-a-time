"""Time tracking endpoints."""

import logging
from datetime import date

from fastapi import APIRouter
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter()


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
) -> TimeTrackingSummary:
    """Get time tracking entries for an employee."""
    period_start = start or date(2026, 3, 1)
    period_end = end or date.today()

    # TODO: Query database
    return TimeTrackingSummary(
        employee_id=employee_id,
        period_start=period_start,
        period_end=period_end,
        total_hours=0.0,
        entries=[],
    )
