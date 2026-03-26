"""Abstract base class for all tools."""

from abc import ABC, abstractmethod
from typing import Any

from shared.models import ToolDefinition


class BaseTool(ABC):
    """Interface that every tool must implement."""

    @property
    @abstractmethod
    def definition(self) -> ToolDefinition:
        """Return the tool's OpenAI function-calling schema."""

    @abstractmethod
    async def execute(self, **kwargs: Any) -> Any:
        """Execute the tool with the given arguments."""
