# Multi-stage build with uv for fast, reproducible builds
FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim AS builder

WORKDIR /app

COPY pyproject.toml uv.lock ./
COPY shared/ shared/
COPY hr-service/ hr-service/

# Install dependencies (--frozen requires uv.lock)
RUN uv sync --frozen --package hr-service --no-dev

# --- Runtime stage ---
FROM python:3.13-slim-bookworm

WORKDIR /app

COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/shared/src /app/shared/src
COPY --from=builder /app/hr-service/src /app/hr-service/src

ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

CMD ["uvicorn", "hr_service.main:app", "--host", "0.0.0.0", "--port", "8000"]
