"""Vacation management endpoints."""

import logging
from datetime import date

from fastapi import APIRouter
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter()


class VacationBalance(BaseModel):
    employee_id: str
    total_days: int
    used_days: int
    remaining_days: int
    year: int


@router.get("/employees/{employee_id}/vacation", response_model=VacationBalance)
async def get_vacation_balance(employee_id: str, year: int | None = None) -> VacationBalance:
    year = year or date.today().year
    """Get vacation balance for an employee."""
    # TODO: Query database
    return VacationBalance(
        employee_id=employee_id,
        total_days=30,
        used_days=0,
        remaining_days=30,
        year=year,
    )
