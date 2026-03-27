# One Bot at a Time

Trenkwalder AI assistant monorepo with a Next.js 16 frontend/BFF and three FastAPI services for chat orchestration, RAG, and seeded HR data.

Architecture board: [One-Bot-At-A-Time Architecture](https://www.figma.com/board/RsHSH7Eo0zcGJXcz3zNqS4/One-Bot-At-A-Time-Architecture?t=sPJ4CkVoSVkvKVkz-1)

If your Markdown renderer strips `iframe` embeds, use the board link above.

## Current Source Of Truth

- Runtime behavior and route contracts in this branch
- [AGENTS.md](./AGENTS.md)
- [ARCHITECTURE_DECISIONS.md](./ARCHITECTURE_DECISIONS.md)
- This README
- [trenkwalder-project-brief.md](./trenkwalder-project-brief.md) as historical design context only

## Architecture Snapshot

| Layer | Current implementation |
| --- | --- |
| Public entrypoint | `frontend/` on Next.js 16 App Router, deployed as the public BFF |
| Browser-facing routes | `POST /api/chat`, `POST /api/chat/stream`, `POST /api/documents`, plus UI routes `/` and `/mock-data` |
| Public edge protections | `botid` verification and frontend in-memory rate limiting |
| Chat backend | `services/chat-orchestrator/` FastAPI service with OpenAI tool-calling and deterministic fallbacks |
| Retrieval backend | `services/rag-service/` FastAPI service for upload, chunking, embeddings, search, and document lifecycle |
| HR backend | `services/hr-service/` FastAPI service with seeded relational HR data |
| Shared code | `services/shared/` is the source of truth; each Python service vendors `src/shared` for Vercel runtime reliability |
| Deployment target | Four Vercel projects: frontend, chat orchestrator, rag service, hr service |

## Request Flow

1. The browser talks only to the Next.js BFF.
2. The BFF applies BotID checks and frontend rate limiting.
3. The BFF forwards internal requests with `x-internal-api-key` and, in preview, optional `_vercel_share` tokens.
4. The chat orchestrator decides whether to answer directly, search documents, or query HR data.
5. The chat orchestrator calls the RAG and HR services over internal HTTP.
6. Streamed responses come back as SSE; the frontend normalizes CRLF line endings before parsing events.

## Services

### Frontend (`frontend/`)

- Next.js `16.2.1`, React `19.2.4`, Tailwind CSS v4, shadcn/ui primitives
- Public BFF for chat and document upload
- Main UI at `/`
- Seeded HR verification view at `/mock-data`
- Server-rendered internal fetch on `/mock-data` calls the chat orchestrator route `/api/v1/mock-data/hr-overview`

### Chat Orchestrator (`services/chat-orchestrator/`)

- FastAPI app mounted at `/api/v1`
- Main routes:
  - `POST /api/v1/chat`
  - `GET /api/v1/chat/stream`
  - `GET /api/v1/mock-data/hr-overview`
- Uses OpenAI chat completions with tool definitions for RAG and HR access
- Falls back to deterministic heuristic routing when no usable OpenAI key is present
- Uses Redis for conversation state and rate limiting when available, otherwise in-memory fallbacks
- Resolves human-readable employee names to stable employee IDs before HR service calls

### RAG Service (`services/rag-service/`)

- FastAPI app mounted at `/api/v1`
- Main routes:
  - `POST /api/v1/ingest`
  - `POST /api/v1/search`
  - `GET /api/v1/documents`
  - `DELETE /api/v1/documents/{document_id}`
- Upload parsing is in-memory and Vercel-safe
- Document metadata is stored separately from vector retrieval state
- Current preview/local backend is `chroma`; production intent remains Postgres or Neon with `pgvector`

### HR Service (`services/hr-service/`)

- FastAPI app mounted at `/api/v1`
- Domain routes for employees, vacation, salary, timetracking, and org charts
- Seeds realistic `de_DE` Faker data on first boot
- Serves persisted records after seeding rather than hardcoded mock responses

### Shared Package (`services/shared/`)

- Source of truth for shared config, middleware, and models
- Not deployed as its own runtime service in the active architecture
- A Vercel-style entrypoint still exists for compatibility tests, but it is not part of the active four-project deployment model

## Repository Layout

```text
one-bot-at-a-time/
├── frontend/
├── services/
│   ├── chat-orchestrator/
│   ├── rag-service/
│   ├── hr-service/
│   ├── shared/
│   └── docker-compose.yml
├── AGENTS.md
├── ARCHITECTURE_DECISIONS.md
└── trenkwalder-project-brief.md
```

## Environment Contracts

### Frontend

- `CHAT_ORCHESTRATOR_URL`
- `CHAT_ORCHESTRATOR_SHARE_TOKEN`
- `RAG_SERVICE_URL`
- `RAG_SERVICE_SHARE_TOKEN`
- `INTERNAL_API_KEY`

### Chat Orchestrator

- `OPENAI_API_KEY`
- `REDIS_URL`
- `CHAT_RAG_SERVICE_URL`
- `CHAT_HR_SERVICE_URL`
- `CHAT_RAG_SERVICE_SHARE_TOKEN`
- `CHAT_HR_SERVICE_SHARE_TOKEN`
- `INTERNAL_API_KEY`
- `CORS_ORIGINS`
- `LOG_LEVEL`

### RAG Service

- `OPENAI_API_KEY`
- `INTERNAL_API_KEY`
- `RAG_VECTOR_BACKEND`
- `RAG_DATABASE_URL`
- `RAG_CHROMA_HOST`
- `RAG_CHROMA_PORT`
- `RAG_CHROMA_COLLECTION`
- `CORS_ORIGINS`
- `LOG_LEVEL`

### HR Service

- `INTERNAL_API_KEY`
- `HR_DATABASE_URL`
- `CORS_ORIGINS`
- `LOG_LEVEL`

## Local Development

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
npm install
npm run check
npm run dev
```

## Deployment Notes

- Active deployment target is Vercel, not Fly.io or Amplify.
- There are four active Vercel projects:
  - `one-bot-at-a-time`
  - `one-bot-at-a-time-chat-orchestrator`
  - `one-bot-at-a-time-rag-service`
  - `one-bot-at-a-time-hr-service`
- These projects rely on Vercel `rootDirectory` settings.
- Deploy linked projects from the repository root, not from `frontend/` or `services/*`, otherwise `rootDirectory` can be double-applied.
- Preview environments should be chained by branch alias:
  - frontend branch alias -> chat branch alias
  - chat branch alias -> rag branch alias
  - chat branch alias -> hr branch alias
- If the preview `INTERNAL_API_KEY` changes, update it consistently across all four projects.
- Legacy `fly.toml` files still exist in service folders, but they are not the active deployment contract.

## Known Operational Debt

- Current Vercel Python bundles may trigger runtime dependency installation because the bundles are still too large.
- Preview persistence uses SQLite-backed metadata and `chroma`; this is acceptable for previews but not the final durable production setup.
- Production-grade RAG persistence still needs a real Postgres or Neon rollout with `pgvector`.

## Related Documents

- [ARCHITECTURE_DECISIONS.md](./ARCHITECTURE_DECISIONS.md) records why the current branch differs from earlier design targets.
- [frontend/README.md](./frontend/README.md) documents the current UI/BFF behavior.
- [trenkwalder-project-brief.md](./trenkwalder-project-brief.md) preserves the original brief and intentionally contains superseded assumptions.
