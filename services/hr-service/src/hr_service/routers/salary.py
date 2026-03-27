"""Salary information endpoints."""

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlmodel.ext.asyncio.session import AsyncSession

from hr_service.database import SalaryRecord, get_session

logger = logging.getLogger(__name__)

router = APIRouter()
session_dependency = Depends(get_session)


class SalaryInfo(BaseModel):
    employee_id: str
    gross_annual: float
    net_monthly: float
    currency: str = "EUR"
    pay_grade: str


@router.get("/employees/{employee_id}/salary", response_model=SalaryInfo)
async def get_salary_info(employee_id: str, session: AsyncSession = session_dependency) -> SalaryInfo:
    """Get salary information for an employee."""
    record = await session.get(SalaryRecord, employee_id)
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Salary record not found")

    return SalaryInfo(
        employee_id=record.employee_id,
        gross_annual=record.gross_annual,
        net_monthly=record.net_monthly,
        currency=record.currency,
        pay_grade=record.pay_grade,
    )
