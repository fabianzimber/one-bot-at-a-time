"""HR tool — query_hr_system via the HR service."""

from typing import Any

from chat_orchestrator.tools.base import BaseTool
from shared.models import ToolDefinition


class HRTool(BaseTool):
    """Queries the HR system for employee data."""

    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="query_hr_system",
            description="Ruft HR-Daten ab: Urlaubstage, Gehaltsinformationen, Mitarbeiterdaten, Organigramm.",
            parameters={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": [
                            "vacation_balance",
                            "salary_info",
                            "employee_lookup",
                            "org_chart",
                            "time_tracking",
                        ],
                        "description": "Die gewuenschte HR-Aktion",
                    },
                    "employee_id": {
                        "type": "string",
                        "description": "Die Mitarbeiter-ID (optional)",
                    },
                    "parameters": {
                        "type": "object",
                        "description": "Zusaetzliche Parameter fuer die Aktion",
                    },
                },
                "required": ["action"],
            },
        )

    async def execute(self, **kwargs: Any) -> Any:
        """Forward HR query to the HR service."""
        # TODO: httpx call to HR service
        action = kwargs.get("action", "")
        return {"action": action, "data": {}, "message": "HR query stub"}
