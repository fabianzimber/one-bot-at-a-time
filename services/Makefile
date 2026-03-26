.PHONY: install dev test lint format clean docker-up docker-down

# ── Development ──────────────────────────────────────────────

install:  ## Install all dependencies
	uv sync

dev-chat:  ## Start Chat Orchestrator (port 8001)
	uv run uvicorn chat_orchestrator.main:app --reload --port 8001

dev-rag:  ## Start RAG Service (port 8002)
	uv run uvicorn rag_service.main:app --reload --port 8002

dev-hr:  ## Start HR Service (port 8003)
	uv run uvicorn hr_service.main:app --reload --port 8003

# ── Quality ──────────────────────────────────────────────────

test:  ## Run all tests
	uv run pytest -v

test-cov:  ## Run tests with coverage
	uv run pytest --cov --cov-report=html

lint:  ## Run linter
	uv run ruff check .

format:  ## Format code
	uv run ruff format .

check:  ## Lint + format check (CI-friendly)
	uv run ruff check .
	uv run ruff format --check .

# ── Docker ───────────────────────────────────────────────────

docker-up:  ## Start all services with Docker Compose
	docker compose up -d

docker-down:  ## Stop all services
	docker compose down

docker-build:  ## Build all Docker images
	docker compose build

docker-logs:  ## Show logs from all services
	docker compose logs -f

# ── Cleanup ──────────────────────────────────────────────────

clean:  ## Remove generated files
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .ruff_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	rm -rf htmlcov .coverage

help:  ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'
