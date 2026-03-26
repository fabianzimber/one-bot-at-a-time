"""Organization chart endpoints."""

import logging

from fastapi import APIRouter
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter()


class OrgNode(BaseModel):
    employee_id: str
    name: str
    position: str
    department: str
    reports: list["OrgNode"] = Field(default_factory=list)


OrgNode.model_rebuild()


@router.get("/org", response_model=list[OrgNode])
async def get_org_chart() -> list[OrgNode]:
    """Get the full organizational chart."""
    # TODO: Build tree from database
    return []


@router.get("/org/{department}", response_model=list[OrgNode])
async def get_department_org(department: str) -> list[OrgNode]:
    """Get the org chart for a specific department."""
    # TODO: Build tree filtered by department
    return []
