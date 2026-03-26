"""Tool use domain models — shared across all services."""

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class ToolStatus(StrEnum):
    SUCCESS = "success"
    ERROR = "error"
    TIMEOUT = "timeout"


class ToolDefinition(BaseModel):
    """Schema for registering a tool with the LLM."""

    name: str
    description: str
    parameters: dict[str, Any]


class ToolCall(BaseModel):
    """Represents an LLM-initiated tool call."""

    id: str
    name: str
    arguments: dict[str, Any] = Field(default_factory=dict)


class ToolResult(BaseModel):
    """Result returned after executing a tool."""

    tool_call_id: str
    name: str
    status: ToolStatus = ToolStatus.SUCCESS
    data: Any = None
    error: str | None = None
