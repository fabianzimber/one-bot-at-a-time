# One Bot at a Time — Trenkwalder AI Assistant

A production-grade AI chatbot platform with Retrieval-Augmented Generation (RAG) capabilities, built to demonstrate enterprise-level architecture. The original requirement was a CLI-based chatbot with RAG; this project deliberately over-delivers to showcase scalable design decisions, code quality, and engineering depth.

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Architecture Overview](#2-architecture-overview)
3. [Frontend Architecture](#3-frontend-architecture)
4. [Backend Microservices](#4-backend-microservices)
5. [Database & Storage Layer](#5-database--storage-layer)
6. [LLM Strategy & Fallback Design](#6-llm-strategy--fallback-design)
7. [Infrastructure & Deployment](#7-infrastructure--deployment)
8. [Security Design](#8-security-design)
9. [Development Workflow](#9-development-workflow)
10. [Testing Philosophy](#10-testing-philosophy)
11. [CI/CD Pipeline](#11-cicd-pipeline)
12. [Roadmap](#12-roadmap)

---

## 1. Project Overview

**One Bot at a Time** is an internal AI assistant for Trenkwalder, capable of:

- Answering questions from uploaded company documents (RAG)
- Querying internal HR data (employees, vacation balances, org chart, salary, time tracking)
- Routing each request to the right tool via LLM function calling
- Streaming responses in real time via Server-Sent Events

### Why a Full Platform Instead of a CLI?

> The evaluation criteria specified: design decisions, code quality, and passion/depth.

A CLI answers the literal requirement; a full platform demonstrates engineering judgment. The architectural choices below are intentional and defensible — each decision was made to maximise long-term maintainability, scalability, and developer experience.

---

## 2. Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                        BROWSER                          │
│           Next.js 16 (App Router) + Tailwind v4         │
│           + shadcn/ui — Minimal, Accessible             │
│           Deployed: Vercel / Fly.io static              │
└──────────────────────┬──────────────────────────────────┘
                       │ HTTPS / TLS 1.3
                       ▼
┌─────────────────────────────────────────────────────────┐
│              BFF — Next.js API Routes                   │
│   Auth checkpoint · Bot detection · Request proxy       │
└──────────────────────┬──────────────────────────────────┘
                       │ Internal HTTP
                       ▼
┌─────────────────────────────────────────────────────────┐
│              PYTHON MICROSERVICE LAYER                   │
│                                                         │
│  ┌───────────────┐  ┌──────────────┐  ┌─────────────┐  │
│  │  Chat          │  │  RAG         │  │  HR Service │  │
│  │  Orchestrator  │  │  Service     │  │  (Mock API) │  │
│  │  :8001         │  │  :8002       │  │  :8003      │  │
│  │                │  │              │  │             │  │
│  │  LLM Router    │  │  Ingest      │  │  Employees  │  │
│  │  Tool Use      │  │  Chunk       │  │  Vacation   │  │
│  │  Fallbacks     │  │  Embed       │  │  Salary     │  │
│  │  History       │  │  Search      │  │  Org Chart  │  │
│  └───────┬────────┘  └──────┬───────┘  └──────┬──────┘  │
│          │                  │                  │         │
│          └──────────────────┴──────────────────┘         │
│                             │                            │
│          ┌──────────────────▼────────────────────┐       │
│          │        Shared Infrastructure           │       │
│          │  Redis · ChromaDB · PostgreSQL · S3   │       │
│          └───────────────────────────────────────┘       │
└─────────────────────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│                  LLM PROVIDER LAYER                     │
│  Primary: GPT-4o                                        │
│  Fallback: GPT-4o-mini  (high load)                    │
│  Emergency: GPT-3.5-turbo  (provider outage)           │
│                                                         │
│  Circuit breaker · Token budget · Latency tracking      │
└─────────────────────────────────────────────────────────┘
```

### Monorepo Layout

```
one-bot-at-a-time/
├── frontend/                    # Next.js 16 (TypeScript)
├── services/                    # Python uv workspace
│   ├── shared/                 # Shared models, config, middleware
│   ├── chat-orchestrator/      # LLM routing & tool orchestration
│   ├── rag-service/            # Document ingestion & semantic search
│   ├── hr-service/             # Mock HR API (SQLModel + async DB)
│   └── docker-compose.yml      # Local development stack
├── .github/workflows/ci.yml    # GitHub Actions CI/CD
└── trenkwalder-project-brief.md # Original architecture brief
```

**Decision: Monorepo over multi-repo**
All services share a single version-control timeline. This enables atomic cross-service refactors, a single lockfile (`uv.lock`) for reproducibility, and one CI pipeline covering the entire system. The cost is a slightly larger clone; the benefit is zero "works on my machine" drift across service boundaries.

---

## 3. Frontend Architecture

### Stack Decision Matrix

| Layer | Choice | Alternatives Considered | Reason for Choice |
|---|---|---|---|
| Framework | Next.js 16 (App Router) | Remix, SvelteKit, plain React | React Server Components reduce client JS; built-in BFF via API routes eliminates a separate gateway for simple cases; strong ecosystem |
| Styling | Tailwind CSS v4 | CSS Modules, styled-components, Emotion | JIT compilation keeps bundle size proportional to usage; utility-first approach removes naming overhead; v4 adds lightning-fast Rust-based builds |
| Component system | shadcn/ui + Base UI | MUI, Ant Design, Radix full | shadcn/ui is copy-paste — no dependency update breaking changes; Base UI (`@base-ui/react`) provides WCAG-compliant primitives without styling opinions |
| Language | TypeScript 5 strict mode | JavaScript | Type safety surfaces integration errors at compile time, not at user's keyboard |
| Bot protection | `botid` (Vercel BotID) | reCAPTCHA, hCaptcha | Invisible to users; server-side verification in API routes; no third-party cookie dependencies |

### Backend-for-Frontend (BFF) Pattern

```
Browser → POST /api/chat (Next.js route) → Bot check → POST http://chat-orchestrator:8001/api/v1/chat
```

**Why a BFF?** The browser never needs the internal service URLs. The Next.js API route:

1. Validates the bot-detection token before any compute is spent on the backend.
2. Acts as the single CORS boundary — all frontend requests stay on the same origin.
3. Is the natural place for future auth headers, request signing, or response transformation without touching backend services.

### Fonts

- **Space Grotesk** (headings, UI labels) — humanist geometric, readable at all sizes.
- **IBM Plex Mono** (bot responses, code) — monospace reinforces the "AI terminal" aesthetic while remaining highly legible.

Both fonts are loaded via `next/font` with `display: swap` and subsets limited to Latin, minimising cumulative layout shift and network payload.

### Design Tokens

All brand colours live as CSS custom properties in `app/globals.css` and are consumed by Tailwind config and shadcn/ui semantic tokens. This single source of truth means changing the brand primary colour is a one-line edit:

```css
--brand-electric-indigo: #6366f1;  /* primary interactive */
--brand-midnight: #0d1117;         /* page background */
--brand-teal: #14b8a6;             /* accent / success */
```

Dark mode is the default (matching the brand book) with no JavaScript toggle overhead — the `<html>` element carries the `.dark` class at render time.

---

## 4. Backend Microservices

### Why Microservices?

The three backend domains have very different scaling profiles:

- **Chat Orchestrator**: CPU-bound, LLM round-trips, needs horizontal scaling independently.
- **RAG Service**: I/O-bound (embedding API + vector DB), scales independently of chat.
- **HR Service**: Low traffic, read-heavy, could run on a tiny VM indefinitely.

Monolithic deployment would mean over-provisioning two services to meet the demands of one. Independent deployment also means a ChromaDB upgrade cannot take down the HR API.

### Why FastAPI?

| Criterion | FastAPI | Django REST | Flask |
|---|---|---|---|
| Async native | ✅ Built-in `asyncio` | ❌ Requires ASGI adapter | ❌ Sync-first |
| Auto OpenAPI | ✅ Pydantic → schema | ✅ (drf-spectacular) | ❌ Manual |
| Performance | ✅ Starlette/Uvicorn | Slower sync workers | Moderate |
| Pydantic integration | ✅ First-class | ❌ Two validation systems | ❌ |
| Boilerplate | Minimal | Heavy | Minimal but no typing |

FastAPI's first-class Pydantic integration means request validation, response serialisation, and OpenAPI documentation are all derived from the same Python type hints — no duplication.

### Why Python 3.13 + uv?

Python 3.13 introduces free-threaded mode (no-GIL preview) and significant CPython performance improvements. `uv` replaces pip + virtualenv + pip-tools with a single Rust-based tool that resolves and installs dependencies an order of magnitude faster than pip. The `uv.lock` lockfile provides byte-for-byte reproducibility across developer machines and CI.

### Shared Package (`services/shared`)

Rather than copying models and utilities into each service, a local `shared` package is declared as a workspace dependency:

```toml
# services/chat-orchestrator/pyproject.toml
dependencies = ["shared"]
```

This means:

- **`shared/models/chat.py`** — `Message`, `ChatRequest`, `ChatResponse` are defined once, used by both the orchestrator and the frontend BFF type contracts.
- **`shared/middleware/logging.py`** — Structured JSON logging with ISO 8601 timestamps, injected identically into every service.
- **`shared/config.py`** — `BaseServiceSettings` with `AliasChoices` so `LOG_LEVEL` (unprefixed) overrides `CHAT_LOG_LEVEL` (prefixed), allowing shared environment defaults without service-specific variable duplication.

### Structured JSON Logging

```json
{
  "time": "2025-06-01T14:22:03.410Z",
  "level": "INFO",
  "logger": "chat_orchestrator.routers.chat",
  "message": "Chat request received",
  "session_id": "abc123",
  "model": "gpt-4o"
}
```

**Decision rationale**: Plain text logs are unqueryable at scale. JSON logs feed directly into log aggregation tools (Loki, Datadog, CloudWatch Logs Insights) with zero ETL. The `extra={}` pattern allows per-request context fields without log format changes.

### Lifespan Context Managers

Every FastAPI service uses `@asynccontextmanager` for startup/shutdown:

```python
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    setup_logging()
    redis_client = await connect_redis()
    yield
    await redis_client.aclose()
```

This replaces deprecated `@app.on_event` handlers and ensures clean resource teardown (DB connections, HTTP clients) even when services are killed by the container orchestrator.

### Service Summaries

#### Chat Orchestrator (`services/chat-orchestrator`)

The decision-making hub. Receives a user message, calls the LLM with a set of tool definitions, interprets function-call responses, routes to RAG or HR service, re-injects the tool result, and returns the final answer.

Key config (`chat_orchestrator/config.py`):

| Setting | Default | Purpose |
|---|---|---|
| `llm_model` | `gpt-4o` | Primary LLM |
| `llm_fallback_model` | `gpt-4o-mini` | High-load fallback |
| `llm_emergency_model` | `gpt-3.5-turbo` | Provider outage emergency |
| `rag_service_url` | `http://localhost:8002` | RAG service internal URL |
| `hr_service_url` | `http://localhost:8003` | HR service internal URL |
| `redis_url` | `redis://localhost:6379/0` | Conversation session store |

#### RAG Service (`services/rag-service`)

Handles document ingestion, chunking, embedding, and semantic search.

| Config | Default | Rationale |
|---|---|---|
| `embedding_model` | `text-embedding-3-small` | 62× cheaper than `ada-002`, marginally lower quality — acceptable for internal docs |
| `chunk_size` | 512 tokens | Balances retrieval precision (small chunks) with context sufficiency (large chunks); 512 is the empirically observed sweet spot for paragraph-level coherence |
| `chunk_overlap` | 50 tokens | Prevents context loss at chunk boundaries |
| `max_file_size_mb` | 10 MB | Prevents memory spikes during in-process PDF parsing |
| `allowed_extensions` | `.pdf .txt .md .docx` | Common internal document formats; binary formats excluded |

#### HR Service (`services/hr-service`)

A mock internal HR API backed by SQLModel (async SQLAlchemy + Pydantic). Uses SQLite locally and PostgreSQL in production — the async driver swap (`aiosqlite` ↔ `asyncpg`) requires only a one-line URL change because SQLModel abstracts the driver.

The service uses **Faker** to seed realistic employee data, making development and demos indistinguishable from production queries.

---

## 5. Database & Storage Layer

### Decision: Three Separate Stores, Each Fit-for-Purpose

| Store | Technology | Why |
|---|---|---|
| Conversation cache | Redis 7 | Sub-millisecond read/write; natural TTL support for session expiry; no schema needed |
| Vector embeddings | ChromaDB | Purpose-built for cosine/dot-product search; handles metadata filtering; local-first for development with Fly.io deployment path |
| Structured HR data | PostgreSQL 16 (pgvector) | ACID guarantees; relational queries across employees/org/salary; pgvector extension available for future hybrid search |
| Document files | Volume mount (→ S3) | Decoupled from compute; presigned URLs for direct browser upload (planned) |

### Why Not a Single Database?

Using PostgreSQL for everything would technically work, but:

- Full-text vector search in PostgreSQL requires `pgvector` and careful index tuning. ChromaDB's primary use case is vector similarity — it has first-class support for collection management, embedding upserts, and filtered retrieval with less operational effort.
- Redis TTL-based session expiry is trivial to configure; implementing equivalent behaviour in PostgreSQL requires a background job or trigger.
- Separating stores means a ChromaDB failure cannot cause HR data corruption.

### ORM Choice: SQLModel

SQLModel merges SQLAlchemy Core (schema definition, migration support) with Pydantic v2 (validation, serialisation). A single class serves as both the database table definition and the API response model:

```python
class Employee(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str
    department: str
    email: str
```

This eliminates the typical two-layer translation (ORM model → Pydantic schema) that causes inconsistencies when one is updated without the other.

---

## 6. LLM Strategy & Fallback Design

### Multi-Model Fallback Chain

```
Request
  └─▶ GPT-4o  (primary — best quality)
        │ fail / high RPM
        └─▶ GPT-4o-mini  (fallback — 10× cheaper, adequate for most queries)
              │ fail / outage
              └─▶ GPT-3.5-turbo  (emergency — always available, lower capability)
```

### Circuit Breaker Logic

Inspired by the Hystrix/Resilience4j pattern:

```
3 failures in 60 s → provider disabled for 120 s → re-probe → re-enable if healthy
```

| Trigger | Action |
|---|---|
| RPM > 80% of quota | Shift traffic to next provider |
| Average latency > threshold | Downgrade to faster/smaller model |
| 3 consecutive errors | Open circuit, route to fallback |
| Daily token budget exceeded | Switch provider until midnight reset |

**Why not just retry?** Blind retries amplify load during provider incidents. A circuit breaker fails fast and routes around the problem immediately, protecting both the user (no 30-second wait) and the provider (no thundering herd).

### Tool Use via LLM Function Calling

The LLM is given structured tool definitions at every request. It responds with either a text answer or a tool call:

```
User: "How many vacation days does Anna Maier have left?"

LLM → function_call: query_hr_system({"employee_name": "Anna Maier", "data": "vacation_balance"})
Tool executor → GET http://hr-service/api/v1/employees/42/vacation
Result injected → LLM → "Anna Maier has 12 days remaining."
```

This approach keeps business logic in the LLM rather than in fragile intent-classification code. Adding a new tool requires only a new tool definition and executor — the LLM decides when to invoke it.

---

## 7. Infrastructure & Deployment

### Local Development

```bash
cd services
docker compose up
```

The `docker-compose.yml` starts all six components (three FastAPI services + Redis + PostgreSQL + ChromaDB) with a single command. Developers never need to install or configure any data stores locally.

```
Service          Host Port   Container Port
chat-orchestrator  8001      →  8000
rag-service        8002      →  8000
hr-service         8003      →  8000
redis              6379      →  6379
postgres           5432      →  5432
chromadb           8004      →  8000
```

All services share a Docker network and communicate by container name (e.g., `http://chat-orchestrator:8000`).

### Production: Fly.io

Each service is deployed independently to Fly.io in the `fra` (Frankfurt) region. Fly.io was selected over AWS/GCP for the following reasons:

| Criterion | Fly.io | AWS ECS | GCP Cloud Run |
|---|---|---|---|
| Setup time | Minutes (single TOML) | Hours (IAM, VPC, ALB, task def) | Moderate |
| Cost at low scale | Scale-to-zero (free tier) | Always-on minimum | Pay-per-request |
| Internal networking | `.internal` DNS automatic | Requires VPC config | Requires VPC connector |
| HTTPS | Automatic | Requires ACM + ALB | Automatic |
| Secrets management | `fly secrets set` | SSM Parameter Store | Secret Manager |

Scale-to-zero means zero cost when the application is idle, which is appropriate for a demo/internal tool that does not receive constant traffic.

### Multi-Stage Docker Builds

```dockerfile
# Stage 1: Builder (includes build tools, uv, full workspace)
FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim AS builder
COPY . .
RUN uv sync --frozen

# Stage 2: Runtime (no build tools, minimal attack surface)
FROM python:3.13-slim-bookworm
COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/src /app/src
CMD ["uvicorn", "chat_orchestrator.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Benefits**:
- Final image contains only the runtime virtual environment and source — no compiler, no uv binary, no workspace config.
- The `uv sync --frozen` in the builder uses the committed `uv.lock` — identical packages in CI, development, and production.
- Smaller images reduce pull time, cold-start latency, and vulnerability surface area.

---

## 8. Security Design

### Layered Defence

```
Internet
   │
   ▼
[Bot Detection]   ← botid (Vercel BotID) — invisible, no CAPTCHA friction
   │
   ▼
[HTTPS / TLS]     ← force_https = true in fly.toml
   │
   ▼
[BFF Proxy]       ← internal service URLs never exposed to browser
   │
   ▼
[CORS]            ← allowlist-only, configured via CORS_ORIGINS env var
   │
   ▼
[Pydantic Input Validation]  ← all request bodies validated before handler
   │
   ▼
[Structured Secrets]  ← API keys in Fly.io secrets, never in source code
```

### Bot Detection

The `botid` library runs a cryptographic challenge in the browser. The resulting token is sent with every `/api/chat` request. The Next.js API route calls `checkBotId(token)` server-side before forwarding to the backend. Bots that do not execute JavaScript (or that fail the challenge) receive a `403 Forbidden` with no backend compute cost.

**Why botid over reCAPTCHA?** reCAPTCHA v3 requires a third-party cookie and a visible widget in some configurations. botid is invisible, first-party, and does not require Google dependency injection into the app.

### CORS Configuration

CORS origins are passed as an environment variable, not hardcoded. Default is `http://localhost:3000` for development. In production, only the deployed frontend domain is added. This prevents any other origin from making credentialed requests to the API.

### API Key Management

- The OpenAI API key is read from `OPENAI_API_KEY` at runtime via Pydantic Settings.
- In production, secrets are injected by `fly secrets set` and never appear in Docker images, container logs, or version control.
- `AliasChoices` in `BaseServiceSettings` allows the same key to be used without service-specific prefixes (useful for shared infrastructure secrets).

---

## 9. Development Workflow

### Prerequisites

- **Frontend**: Node.js 20+, npm
- **Backend**: Python 3.13+, [uv](https://docs.astral.sh/uv/getting-started/installation/), Docker

### Quick Start

```bash
# Backend services (all in one)
cd services
docker compose up

# Frontend
cd frontend
npm install
npm run dev          # http://localhost:3000
```

### Backend Development (without Docker)

```bash
cd services
uv sync --all-packages       # install all workspace packages + dev deps
uv run uvicorn chat_orchestrator.main:app --reload --port 8001
uv run uvicorn rag_service.main:app --reload --port 8002
uv run uvicorn hr_service.main:app --reload --port 8003
```

### Code Quality

```bash
# Backend
cd services
uv run ruff check .           # lint
uv run ruff format .          # format
uv run pytest -q              # tests

# Frontend
cd frontend
npm run check                 # tsc --noEmit + eslint (zero warnings)
```

### Environment Variables

Copy `.env.example` files and fill in required values:

```bash
cp services/chat-orchestrator/.env.example services/chat-orchestrator/.env
```

Required variables:

| Variable | Service | Description |
|---|---|---|
| `OPENAI_API_KEY` | chat-orchestrator, rag-service | OpenAI API key |
| `CHAT_REDIS_URL` | chat-orchestrator | Redis connection string |
| `RAG_CHROMA_HOST` | rag-service | ChromaDB host |
| `HR_DATABASE_URL` | hr-service | PostgreSQL / SQLite URL |
| `CORS_ORIGINS` | all services | Allowed frontend origins |

---

## 10. Testing Philosophy

### Coverage Requirement: 80%

CI fails if test coverage drops below 80%. This threshold is a deliberate balance: 100% coverage often leads to testing implementation details rather than behaviour; 80% ensures critical paths are covered while leaving room for pragmatic trade-offs.

### Test Categories

| Category | Location | What it tests |
|---|---|---|
| Model validation | `shared/tests/test_models.py` | Pydantic model creation, field validation, alias resolution |
| API endpoints | `*/tests/test_*.py` | HTTP status codes, request/response contracts, error handling |
| Config aliases | `shared/tests/test_models.py` | Unprefixed env vars override prefixed defaults |
| LLM routing | `chat-orchestrator/tests/test_llm_router.py` | Fallback chain, circuit breaker (planned) |

### Async-First Tests

All tests use `asyncio_mode = "auto"` from pytest-asyncio — async test functions are automatically awaited without needing `@pytest.mark.asyncio` decorators. This keeps test code readable:

```python
async def test_health_check(client: AsyncClient) -> None:
    response = await client.get("/health")
    assert response.status_code == 200
```

### Test Infrastructure

```toml
# services/pyproject.toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["shared/tests", "chat-orchestrator/tests", "rag-service/tests", "hr-service/tests"]
pythonpath = ["shared/src", "chat-orchestrator/src", "rag-service/src", "hr-service/src"]
```

All service source directories are added to `pythonpath`, so tests import from the installed package, not from relative paths.

---

## 11. CI/CD Pipeline

The pipeline runs on every push to `main` and on every pull request targeting `main`, but only when files under `services/**` or `.github/workflows/ci.yml` change. Frontend changes skip the Python pipeline entirely, reducing unnecessary CI minutes.

```
┌─────────────────────────────────────────┐
│  Trigger: push/PR to main               │
│  Path filter: services/** or ci.yml     │
└────────────────┬────────────────────────┘
                 │
        ┌────────┴────────┐
        ▼                 ▼
  ┌───────────┐     ┌───────────┐
  │   Lint    │     │   Test    │
  │           │     │           │
  │ uv sync   │     │ uv sync   │
  │ ruff check│     │ pytest -v │
  │ ruff fmt  │     │ --cov     │
  │  --check  │     │ ≥80% cov  │
  └───────────┘     └───────────┘
```

**Why Ruff instead of flake8 + isort + black?** Ruff is a single Rust-based tool that replaces all three. It runs 10–100× faster than the Python equivalents, eliminating a common bottleneck in larger monorepos. The configuration lives in `pyproject.toml` alongside everything else, removing the `setup.cfg` / `.flake8` / `.isort.cfg` sprawl.

---

## 12. Roadmap

### In Progress

| Feature | Service | Status |
|---|---|---|
| LLM router with circuit breaker | chat-orchestrator | Scaffolded |
| Tool executor (RAG + HR) | chat-orchestrator | Scaffolded |
| SSE streaming endpoint | chat-orchestrator | Route defined, logic pending |
| Document chunking + embedding | rag-service | Scaffolded |
| ChromaDB client integration | rag-service | Scaffolded |
| HR database models + seeding | hr-service | Scaffolded |
| Chat UI (messages, streaming) | frontend | Scaffolded |
| Document upload UI | frontend | Scaffolded |

### Planned

| Feature | Priority | Notes |
|---|---|---|
| Service-to-service authentication | High | HMAC request signing or internal API keys |
| Rate limiting middleware | High | Token bucket per IP / session |
| Metrics + health dashboards | Medium | Prometheus + Grafana, or Fly.io Metrics |
| Error tracking | Medium | Sentry integration for both frontend and backend |
| S3 document storage | Medium | Replace volume mount for production scalability |
| Conversation history persistence | Medium | PostgreSQL-backed, currently Redis-only |
| Light mode toggle | Low | Brand tokens already support dual modes |

---

## License

MIT — see [LICENSE](LICENSE).
