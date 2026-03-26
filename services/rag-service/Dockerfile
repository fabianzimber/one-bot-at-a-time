# Multi-stage build with uv for fast, reproducible builds
FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim AS builder

WORKDIR /app

COPY pyproject.toml ./
COPY shared/ shared/
COPY rag-service/ rag-service/

RUN uv sync --frozen --package rag-service --no-dev

# --- Runtime stage ---
FROM python:3.13-slim-bookworm

WORKDIR /app

COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/shared/src /app/shared/src
COPY --from=builder /app/rag-service/src /app/rag-service/src

ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

CMD ["uvicorn", "rag_service.main:app", "--host", "0.0.0.0", "--port", "8000"]
