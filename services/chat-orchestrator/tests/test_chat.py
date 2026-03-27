"""Tests for chat orchestrator endpoints."""

from fastapi.testclient import TestClient

from chat_orchestrator.main import app
from chat_orchestrator.services.chat_service import ChatService
from shared.models import ToolResult
from shared.models.tools import ToolStatus

client = TestClient(app)


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "chat-orchestrator"


def test_chat_endpoint():
    response = client.post("/api/v1/chat", json={"message": "Hallo, wer bist du?"})
    assert response.status_code == 200
    data = response.json()
    assert "conversation_id" in data
    assert "message" in data


def test_chat_validation_empty_message():
    response = client.post("/api/v1/chat", json={"message": ""})
    assert response.status_code == 422


def test_direct_tool_message_for_unknown_employee():
    service = ChatService(
        llm_router=None,  # type: ignore[arg-type]
        tool_registry=None,  # type: ignore[arg-type]
        tool_executor=None,  # type: ignore[arg-type]
        conversation_store=None,  # type: ignore[arg-type]
    )

    message = service._build_direct_tool_message(
        [
            ToolResult(
                tool_call_id="tool-1",
                name="query_hr_system",
                status=ToolStatus.ERROR,
                data={
                    "kind": "hr_not_found",
                    "action": "vacation_balance",
                    "employee_id": "emp-999",
                    "detail": "Vacation balance not found",
                },
                error="Vacation balance not found",
            )
        ]
    )

    assert message is not None
    assert "emp-999" in message
    assert "HR-Datensatz" in message
