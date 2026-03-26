"""Tests for HR service endpoints."""

from fastapi.testclient import TestClient

from hr_service.main import app

client = TestClient(app)


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "hr-service"


def test_list_employees():
    response = client.get("/api/v1/employees")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_employee():
    response = client.get("/api/v1/employees/emp-001")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "emp-001"


def test_vacation_balance():
    response = client.get("/api/v1/employees/emp-001/vacation")
    assert response.status_code == 200
    data = response.json()
    assert "remaining_days" in data


def test_org_chart():
    response = client.get("/api/v1/org")
    assert response.status_code == 200
