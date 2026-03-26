"""Tool registration and discovery."""

import logging

from chat_orchestrator.tools.base import BaseTool

logger = logging.getLogger(__name__)


class ToolRegistry:
    """Central registry for all available tools."""

    def __init__(self) -> None:
        self._tools: dict[str, BaseTool] = {}

    def register(self, tool: BaseTool) -> None:
        """Register a tool by its name."""
        name = tool.definition.name
        self._tools[name] = tool
        logger.info("Tool registered", extra={"tool": name})

    def get(self, name: str) -> BaseTool | None:
        """Retrieve a tool by name."""
        return self._tools.get(name)

    def get_all_definitions(self) -> list[dict]:
        """Return all tool definitions in OpenAI function-calling format."""
        return [
            {
                "type": "function",
                "function": {
                    "name": tool.definition.name,
                    "description": tool.definition.description,
                    "parameters": tool.definition.parameters,
                },
            }
            for tool in self._tools.values()
        ]

    @property
    def tool_names(self) -> list[str]:
        return list(self._tools.keys())
