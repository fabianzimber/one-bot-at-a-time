# Multi-stage build with uv for fast, reproducible builds
FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim AS builder

WORKDIR /app

# Copy workspace root, lockfile, and shared library first (better layer caching)
COPY pyproject.toml uv.lock ./
COPY shared/ shared/
COPY chat-orchestrator/ chat-orchestrator/

# Install dependencies (--frozen requires uv.lock)
RUN uv sync --frozen --package chat-orchestrator --no-dev

# --- Runtime stage ---
FROM python:3.13-slim-bookworm

WORKDIR /app

# Copy installed packages and source code from builder
COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/shared/src /app/shared/src
COPY --from=builder /app/chat-orchestrator/src /app/chat-orchestrator/src

ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

CMD ["uvicorn", "chat_orchestrator.main:app", "--host", "0.0.0.0", "--port", "8000"]
