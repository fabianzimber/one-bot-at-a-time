# AGENTS.md

This file captures the current repo-specific working rules for `one-bot-at-a-time`. It is intentionally branch-local and reflects the implementation state in this branch rather than older workspace-wide defaults.

## Project Snapshot

`one-bot-at-a-time` is a Trenkwalder AI assistant monorepo with:

- `frontend/`: Next.js 16 App Router frontend and public BFF
- `services/chat-orchestrator/`: FastAPI chat orchestration service
- `services/rag-service/`: FastAPI document ingestion and semantic search service
- `services/hr-service/`: FastAPI seeded HR data service
- `services/shared/`: shared Python package for config, middleware, and models

## Current Architecture Decisions

- Vercel is the active deployment target for the frontend, chat, rag, and hr projects.
- `services/shared` is not deployed separately.
- Public browser traffic should enter via the frontend BFF, not by calling Python services directly.
- Internal service hops use `x-internal-api-key` backed by `INTERNAL_API_KEY`.
- Chat runtime uses Redis when available and in-memory fallbacks otherwise.
- RAG previews currently use `chroma` plus SQLite metadata storage; production intent remains `pgvector`.
- HR data is seeded into the DB on first boot and then served from persisted records.
- Service initialization must remain safe for tests and Vercel cold starts; do not move back to startup-only assumptions.

## Deployment Layout

There are four Vercel projects:

- `one-bot-at-a-time`
- `one-bot-at-a-time-chat-orchestrator`
- `one-bot-at-a-time-rag-service`
- `one-bot-at-a-time-hr-service`

Important:

- These backend Vercel projects rely on `rootDirectory` in project settings.
- To deploy them from CLI, link the repo root to the target Vercel project first, then run `vercel deploy -y` from the repo root.
- Deploying from inside `services/chat-orchestrator`, `services/rag-service`, or `services/hr-service` can double-apply the `rootDirectory` and fail.

## Environment Contracts

### Frontend

- `CHAT_ORCHESTRATOR_URL`
- `INTERNAL_API_KEY`

### Chat Orchestrator

- `OPENAI_API_KEY`
- `REDIS_URL`
- `CHAT_RAG_SERVICE_URL`
- `CHAT_HR_SERVICE_URL`
- `INTERNAL_API_KEY`
- `CORS_ORIGINS`
- `LOG_LEVEL`

### RAG Service

- `OPENAI_API_KEY`
- `INTERNAL_API_KEY`
- `RAG_VECTOR_BACKEND`
- `RAG_DATABASE_URL`
- `CORS_ORIGINS`
- `LOG_LEVEL`

### HR Service

- `INTERNAL_API_KEY`
- `HR_DATABASE_URL`
- `CORS_ORIGINS`
- `LOG_LEVEL`

## Branch Preview Wiring

For this branch, previews are expected to be chained:

- frontend preview -> chat preview
- chat preview -> rag preview
- chat preview -> hr preview

If you redeploy one service and its preview URL changes, update the upstream preview env vars before treating the chain as current.

## Development Commands

### Backend

```bash
cd services
uv lock
uv run ruff check .
uv run pytest -q
```

### Frontend

```bash
cd frontend
npm run check
```

## Editing Rules

- Use `apply_patch` for manual text edits.
- Keep Python service contracts aligned with `services/shared`.
- Preserve the lazy runtime initialization helpers in:
  - `services/chat-orchestrator/src/chat_orchestrator/runtime.py`
  - `services/rag-service/src/rag_service/runtime.py`
  - `services/hr-service/src/hr_service/database/connection.py`
- Do not reintroduce a separate deployed `shared` service unless there is a real runtime responsibility for it.
- Do not silently replace branch-specific preview URLs with production URLs when debugging preview behavior.

## Known Operational Debt

- Python Vercel bundles currently trigger runtime dependency installation due to bundle size.
- Preview persistence currently uses SQLite in `/tmp`, which is acceptable for preview but not a durable production strategy.
- Production-grade RAG persistence still needs a real Postgres/Neon plus `pgvector` rollout.
