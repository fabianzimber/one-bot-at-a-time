"""Organization chart endpoints."""

import logging

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from hr_service.database import Employee, get_session

logger = logging.getLogger(__name__)

router = APIRouter()
session_dependency = Depends(get_session)


class OrgNode(BaseModel):
    employee_id: str
    name: str
    position: str
    department: str
    reports: list["OrgNode"] = Field(default_factory=list)


OrgNode.model_rebuild()


def _build_org_nodes(employees: list[Employee], department: str | None = None) -> list[OrgNode]:
    filtered = [employee for employee in employees if department is None or employee.department == department]
    by_manager: dict[str | None, list[Employee]] = {}
    for employee in filtered:
        by_manager.setdefault(employee.manager_id, []).append(employee)

    for reports in by_manager.values():
        reports.sort(key=lambda item: (item.department, item.last_name, item.first_name))

    def to_node(employee: Employee) -> OrgNode:
        return OrgNode(
            employee_id=employee.id,
            name=f"{employee.first_name} {employee.last_name}",
            position=employee.position,
            department=employee.department,
            reports=[to_node(report) for report in by_manager.get(employee.id, [])],
        )

    roots = [employee for employee in filtered if employee.manager_id not in {item.id for item in filtered}]
    roots.sort(key=lambda item: (item.department, item.last_name, item.first_name))
    return [to_node(employee) for employee in roots]


@router.get("/org", response_model=list[OrgNode])
async def get_org_chart(session: AsyncSession = session_dependency) -> list[OrgNode]:
    """Get the full organizational chart."""
    result = await session.exec(select(Employee))
    return _build_org_nodes(result.all())


@router.get("/org/{department}", response_model=list[OrgNode])
async def get_department_org(department: str, session: AsyncSession = session_dependency) -> list[OrgNode]:
    """Get the org chart for a specific department."""
    result = await session.exec(select(Employee).where(Employee.department == department))
    return _build_org_nodes(result.all(), department=department)
