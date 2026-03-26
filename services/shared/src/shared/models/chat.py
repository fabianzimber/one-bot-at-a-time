"""Chat domain models — shared across all services."""

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class MessageRole(StrEnum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"


class Message(BaseModel):
    role: MessageRole
    content: str
    name: str | None = None
    tool_call_id: str | None = None
    timestamp: datetime = Field(default_factory=datetime.now)


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=10_000)
    conversation_id: str | None = None
    stream: bool = False


class ChatResponse(BaseModel):
    message: str
    conversation_id: str
    tool_calls_used: list[str] = Field(default_factory=list)
    sources: list[dict] = Field(default_factory=list)
    model_used: str | None = None
    timestamp: datetime = Field(default_factory=datetime.now)
