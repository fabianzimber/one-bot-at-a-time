"""Employee management endpoints."""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from hr_service.database import Employee as EmployeeRecord
from hr_service.database import get_session

logger = logging.getLogger(__name__)

router = APIRouter()
session_dependency = Depends(get_session)


class EmployeeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    first_name: str
    last_name: str
    email: str
    department: str
    position: str
    manager_id: str | None = None


@router.get("/employees", response_model=list[EmployeeResponse])
async def list_employees(
    department: str | None = Query(default=None),
    session: AsyncSession = session_dependency,
) -> list[EmployeeResponse]:
    """List all employees, optionally filtered by department."""
    statement = select(EmployeeRecord).order_by(EmployeeRecord.last_name, EmployeeRecord.first_name)
    if department:
        statement = statement.where(EmployeeRecord.department == department)
    result = await session.exec(statement)
    return [EmployeeResponse.model_validate(employee) for employee in result.all()]


@router.get("/employees/{employee_id}", response_model=EmployeeResponse)
async def get_employee(employee_id: str, session: AsyncSession = session_dependency) -> EmployeeResponse:
    """Get a specific employee by ID."""
    employee = await session.get(EmployeeRecord, employee_id)
    if employee is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")
    return EmployeeResponse.model_validate(employee)
