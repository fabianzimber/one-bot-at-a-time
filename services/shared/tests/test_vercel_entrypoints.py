"""Tests for the Vercel-compatible service entry points."""

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

from fastapi.testclient import TestClient

SERVICES_ROOT = Path(__file__).resolve().parents[2]
ENTRYPOINTS = (
    ("chat-orchestrator", "chat-orchestrator"),
    ("rag-service", "rag-service"),
    ("hr-service", "hr-service"),
)


def load_app(service_dir: str):
    module_path = SERVICES_ROOT / service_dir / "main.py"
    spec = spec_from_file_location(f"{service_dir.replace('-', '_')}_vercel_main", module_path)
    assert spec is not None
    assert spec.loader is not None
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.app


def test_vercel_entrypoints_expose_service_apps():
    for service_dir, service_name in ENTRYPOINTS:
        client = TestClient(load_app(service_dir))
        response = client.get("/health")

        assert response.status_code == 200
        assert response.json()["service"] == service_name
