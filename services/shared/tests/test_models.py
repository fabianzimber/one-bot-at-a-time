"""Tests for shared models and config."""

import os

from shared.config import BaseServiceSettings
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


# --- Config alias tests ---


class PrefixedSettings(BaseServiceSettings):
    """Simulates a service subclass with env_prefix."""

    model_config = BaseServiceSettings.model_config.copy()
    model_config["env_prefix"] = "TEST_"


def test_shared_fields_read_unprefixed_env(monkeypatch):
    """Unprefixed LOG_LEVEL / OPENAI_API_KEY / CORS_ORIGINS must be picked up
    even when the subclass sets env_prefix='TEST_'."""
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key")
    monkeypatch.setenv("CORS_ORIGINS", '["http://example.com"]')

    s = PrefixedSettings()
    assert s.log_level == "DEBUG"
    assert s.openai_api_key == "sk-test-key"
    assert s.cors_origins == ["http://example.com"]


def test_shared_fields_use_defaults_when_no_env():
    """Without env vars, shared fields must fall back to their defaults."""
    # Clear any env vars that could leak in
    env_keys = ["LOG_LEVEL", "OPENAI_API_KEY", "CORS_ORIGINS", "TEST_LOG_LEVEL", "TEST_OPENAI_API_KEY"]
    old = {k: os.environ.pop(k, None) for k in env_keys}
    try:
        s = PrefixedSettings()
        assert s.log_level == "INFO"
        assert s.openai_api_key == ""
        assert s.cors_origins == ["http://localhost:3000"]
    finally:
        for k, v in old.items():
            if v is not None:
                os.environ[k] = v
