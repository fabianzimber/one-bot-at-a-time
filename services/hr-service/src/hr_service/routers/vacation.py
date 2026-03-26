"""Vacation management endpoints."""

import logging

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
async def get_vacation_balance(employee_id: str, year: int = 2026) -> VacationBalance:
    """Get vacation balance for an employee."""
    # TODO: Query database
    return VacationBalance(
        employee_id=employee_id,
        total_days=30,
        used_days=0,
        remaining_days=30,
        year=year,
    )
