"""Tests for RAG service endpoints."""

from fastapi.testclient import TestClient

from rag_service.main import app

client = TestClient(app)


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "rag-service"


def test_search_endpoint():
    response = client.post("/api/v1/search", json={"query": "Urlaubsregelung", "top_k": 3})
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert data["query"] == "Urlaubsregelung"


def test_list_documents():
    response = client.get("/api/v1/documents")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_search_validation():
    response = client.post("/api/v1/search", json={"query": ""})
    assert response.status_code == 422
