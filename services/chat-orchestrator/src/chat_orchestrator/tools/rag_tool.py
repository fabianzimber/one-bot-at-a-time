"""RAG tool — search_documents via the RAG service."""

from typing import Any

from chat_orchestrator.tools.base import BaseTool
from shared.models import ToolDefinition


class RAGTool(BaseTool):
    """Searches uploaded documents for relevant information."""

    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="search_documents",
            description="Durchsucht hochgeladene Dokumente nach relevanten Informationen.",
            parameters={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Die Suchanfrage",
                    }
                },
                "required": ["query"],
            },
        )

    async def execute(self, **kwargs: Any) -> Any:
        """Forward search request to the RAG service."""
        # TODO: httpx call to RAG service POST /search
        query = kwargs.get("query", "")
        return {"results": [], "query": query, "message": "RAG search stub"}
