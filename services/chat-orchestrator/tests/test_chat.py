"""Tests for chat orchestrator endpoints."""

from fastapi.testclient import TestClient

from chat_orchestrator.main import app

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
