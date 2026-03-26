"""Executes tool calls returned by the LLM."""

import logging

from shared.models import ToolCall, ToolResult
from shared.models.tools import ToolStatus

logger = logging.getLogger(__name__)


class ToolExecutor:
    """Dispatches tool calls to the appropriate service."""

    def __init__(self, rag_service_url: str, hr_service_url: str) -> None:
        self.rag_service_url = rag_service_url
        self.hr_service_url = hr_service_url

    async def execute(self, tool_call: ToolCall) -> ToolResult:
        """Execute a single tool call and return the result."""
        logger.info("Executing tool", extra={"tool": tool_call.name, "id": tool_call.id})

        # TODO: Dispatch to RAG or HR service via httpx
        return ToolResult(
            tool_call_id=tool_call.id,
            name=tool_call.name,
            status=ToolStatus.SUCCESS,
            data=f"Stub result for {tool_call.name}",
        )
