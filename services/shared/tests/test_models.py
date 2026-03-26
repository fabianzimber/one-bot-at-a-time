"""Tests for shared models."""

from shared.models import ChatRequest, ChatResponse, Message, MessageRole, ToolCall, ToolResult
from shared.models.tools import ToolStatus


def test_message_creation():
    msg = Message(role=MessageRole.USER, content="Hallo")
    assert msg.role == "user"
    assert msg.content == "Hallo"
    assert msg.timestamp is not None


def test_chat_request_validation():
    req = ChatRequest(message="Was steht im Dokument?")
    assert req.stream is False
    assert req.conversation_id is None


def test_chat_response():
    resp = ChatResponse(
        message="Hier ist die Antwort.",
        conversation_id="conv-123",
        tool_calls_used=["search_documents"],
        model_used="gpt-4o",
    )
    assert resp.conversation_id == "conv-123"
    assert "search_documents" in resp.tool_calls_used


def test_tool_call():
    call = ToolCall(id="call-1", name="search_documents", arguments={"query": "Urlaub"})
    assert call.name == "search_documents"


def test_tool_result():
    result = ToolResult(tool_call_id="call-1", name="search_documents", data={"text": "found"})
    assert result.status == ToolStatus.SUCCESS
    assert result.error is None
