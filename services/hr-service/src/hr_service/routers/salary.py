"""Salary information endpoints."""

import logging

from fastapi import APIRouter
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter()


class SalaryInfo(BaseModel):
    employee_id: str
    gross_annual: float
    net_monthly: float
    currency: str = "EUR"
    pay_grade: str


@router.get("/employees/{employee_id}/salary", response_model=SalaryInfo)
async def get_salary_info(employee_id: str) -> SalaryInfo:
    """Get salary information for an employee."""
    # TODO: Query database
    return SalaryInfo(
        employee_id=employee_id,
        gross_annual=0.0,
        net_monthly=0.0,
        pay_grade="stub",
    )
