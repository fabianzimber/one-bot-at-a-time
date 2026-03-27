"""Vacation management endpoints."""

import logging
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlmodel import desc, select
from sqlmodel.ext.asyncio.session import AsyncSession

from hr_service.database import VacationRecord, get_session

logger = logging.getLogger(__name__)

router = APIRouter()
session_dependency = Depends(get_session)


class VacationBalance(BaseModel):
    employee_id: str
    total_days: int
    used_days: int
    remaining_days: int
    year: int


@router.get("/employees/{employee_id}/vacation", response_model=VacationBalance)
async def get_vacation_balance(
    employee_id: str,
    year: int | None = None,
    session: AsyncSession = session_dependency,
) -> VacationBalance:
    """Get vacation balance for an employee."""
    current_year = year or date.today().year
    statement = (
        select(VacationRecord)
        .where(VacationRecord.employee_id == employee_id, VacationRecord.year == current_year)
        .order_by(desc(VacationRecord.year))
    )
    result = await session.exec(statement)
    record = result.first()
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vacation balance not found")

    return VacationBalance(
        employee_id=record.employee_id,
        total_days=record.total_days,
        used_days=record.used_days,
        remaining_days=record.remaining_days,
        year=record.year,
    )
