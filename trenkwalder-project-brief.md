# TRENKWALDER AI CHATBOT — Claude Project Brief

> Historical design brief only. This file preserves the original proposal and still contains superseded assumptions such as AWS Amplify/Fly.io deployment options, S3-oriented storage ideas, and earlier version targets. For the implemented branch state, use [README.md](./README.md), [AGENTS.md](./AGENTS.md), and [ARCHITECTURE_DECISIONS.md](./ARCHITECTURE_DECISIONS.md).

## Die Aufgabe (Original)

Einen **Chatbot mit RAG** (Retrieval Augmented Generation) bauen, der:
1. Dokumente verarbeiten und Fragen darüber beantworten kann
2. External API Calls macht um Daten abzurufen
3. "CLI reicht" — aber wir over-delivern mit einer Production-Grade Lösung

**Bewertungskriterien laut Damjan:**
- Design Decisions (Architecture Decision Records)
- Code-Qualität und Struktur
- Passion und Tiefe der Lösung

---

## Unsere Vision: Production-Grade AI Platform

Wir bauen keine Demo. Wir bauen eine skalierbare AI-Chatbot-Plattform die zeigt, dass wir auf Enterprise-Level denken.

---

## ARCHITEKTUR-ÜBERSICHT

```
┌─────────────────────────────────────────────────────────┐
│                      FRONTEND                           │
│          Next.js 14+ (App Router) + Tailwind            │
│          + shadcn/ui — Minimalistisch & Ästhetisch      │
│          Deployed: AWS Amplify / Vercel                 │
└──────────────────────┬──────────────────────────────────┘
                       │ HTTPS (TLS 1.3)
                       ▼
┌─────────────────────────────────────────────────────────┐
│                    API GATEWAY / PROXY                   │
│          Next.js API Routes als BFF (Backend-for-       │
│          Frontend) ODER AWS API Gateway                 │
│          → Auth, Rate Limiting, Request Validation      │
└──────────────────────┬──────────────────────────────────┘
                       │ Internal Network
                       ▼
┌─────────────────────────────────────────────────────────┐
│              PYTHON MICROSERVICE LAYER                   │
│                                                         │
│  ┌─────────────┐  ┌──────────────┐  ┌───────────────┐  │
│  │  Chat       │  │  RAG         │  │  HR Service   │  │
│  │  Orchestrator│  │  Service     │  │  (External    │  │
│  │  (FastAPI)  │  │  (FastAPI)   │  │   API Mock)   │  │
│  │             │  │              │  │  (FastAPI)    │  │
│  │  - LLM      │  │  - Ingest    │  │              │  │
│  │    Router   │  │  - Chunk     │  │  - Urlaub    │  │
│  │  - Tool Use │  │  - Embed     │  │  - Gehalt    │  │
│  │  - Fallback │  │  - Search    │  │  - Mitarb.   │  │
│  │  - History  │  │              │  │              │  │
│  └──────┬──────┘  └──────┬───────┘  └──────┬────────┘  │
│         │                │                  │           │
│         ▼                ▼                  ▼           │
│  ┌─────────────────────────────────────────────────┐    │
│  │           Shared Infrastructure                  │    │
│  │  - Redis (Session/Cache)                        │    │
│  │  - ChromaDB / pgvector (Vector Store)           │    │
│  │  - PostgreSQL (Structured Data)                 │    │
│  │  - S3 (Document Storage)                        │    │
│  └─────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│                   LLM PROVIDER LAYER                    │
│                                                         │
│  Primary: OpenAI GPT-4o                                 │
│  Fallback: GPT-4o-mini (bei hoher Last)                │
│  Emergency: GPT-3.5-turbo (bei Ausfall)                │
│                                                         │
│  Load Detection → Token-basiertes Budget                │
│  Circuit Breaker → Automatischer Provider-Wechsel      │
│  Response Streaming → Server-Sent Events               │
└─────────────────────────────────────────────────────────┘
```

---

## DETAILLIERTE KOMPONENTEN-SPECS

### 1. FRONTEND (Next.js)

**Philosophie:** Intelligent minimalistisch — jedes Pixel hat einen Grund.

```
frontend/
├── app/
│   ├── layout.tsx              # Root Layout mit Providers
│   ├── page.tsx                # Landing/Chat Interface
│   ├── api/                    # BFF Proxy Routes
│   │   ├── chat/route.ts       # POST → Chat Orchestrator
│   │   ├── documents/route.ts  # POST → RAG Service (Upload)
│   │   └── health/route.ts     # GET → Service Health Check
│   └── globals.css
├── components/
│   ├── chat/
│   │   ├── ChatContainer.tsx   # Main Chat Wrapper
│   │   ├── MessageBubble.tsx   # Einzelne Nachricht (User/Bot)
│   │   ├── InputBar.tsx        # Input + Send + File Upload
│   │   ├── ToolIndicator.tsx   # Zeigt an welches Tool der Bot nutzt
│   │   ├── StreamingText.tsx   # Animierter Streaming-Output
│   │   └── SourceCitation.tsx  # Quellenangabe bei RAG-Antworten
│   ├── documents/
│   │   ├── DocumentUpload.tsx  # Drag & Drop Upload
│   │   └── DocumentList.tsx    # Geladene Dokumente anzeigen
│   ├── ui/                     # shadcn/ui Komponenten
│   └── layout/
│       ├── Sidebar.tsx         # Optional: Conversation History
│       └── Header.tsx
├── lib/
│   ├── api-client.ts           # Typed API Client (fetch wrapper)
│   ├── sse-client.ts           # Server-Sent Events Parser
│   └── utils.ts
├── hooks/
│   ├── useChat.ts              # Chat State Management
│   ├── useStreaming.ts         # SSE Hook
│   └── useDocuments.ts
└── types/
    └── index.ts                # Shared TypeScript Types
```

**UI/UX Design-Prinzipien:**
- Dark Mode default, Light Mode toggle
- Mono-Font für Bot-Antworten (JetBrains Mono / Fira Code)
- Sans-Serif für User (Inter / Geist)
- Subtile Animationen (framer-motion): Message appear, typing indicator, tool switching
- Real-time Streaming mit Cursor-Blink-Effekt
- Tool-Use-Visualisierung: Wenn der Bot RAG nutzt → "🔍 Durchsuche Dokumente...", bei API → "📡 Rufe HR-Daten ab..."
- Responsive: Mobile-first, funktioniert auf allen Devices
- Accessibility: ARIA labels, Keyboard navigation, Screen reader support

**Farb-Palette (Vorschlag — anpassbar):**
- Background: `#0a0a0b` (fast schwarz)
- Surface: `#141416`
- Accent: `#6366f1` (Indigo)
- Text Primary: `#fafafa`
- Text Secondary: `#71717a`
- Success: `#22c55e`
- Error: `#ef4444`

---

### 2. PYTHON BACKEND — Chat Orchestrator Service

**Das Herzstück.** Entscheidet via LLM Function Calling welches Tool genutzt wird.

```
services/chat-orchestrator/
├── app/
│   ├── main.py                 # FastAPI App + CORS + Middleware
│   ├── config.py               # Pydantic Settings (env-based)
│   ├── routers/
│   │   ├── chat.py             # POST /chat, GET /chat/stream (SSE)
│   │   └── health.py           # GET /health
│   ├── services/
│   │   ├── llm_router.py       # LLM Provider Management + Fallback
│   │   ├── tool_executor.py    # Executes tool calls from LLM
│   │   ├── conversation.py     # Conversation History Management
│   │   └── streaming.py        # SSE Streaming Logic
│   ├── tools/                  # Tool Definitions (OpenAI Function Calling Format)
│   │   ├── base.py             # Abstract Tool Interface
│   │   ├── rag_tool.py         # "search_documents" tool
│   │   ├── hr_tool.py          # "query_hr_system" tool
│   │   └── registry.py         # Tool Registration & Discovery
│   ├── models/
│   │   ├── chat.py             # Pydantic Models: ChatRequest, ChatResponse
│   │   └── tools.py            # ToolCall, ToolResult Models
│   └── middleware/
│       ├── auth.py             # API Key Validation
│       ├── rate_limit.py       # Token Bucket Rate Limiter
│       └── logging.py          # Structured Logging (JSON)
├── tests/
│   ├── test_chat.py
│   ├── test_llm_router.py
│   └── test_tools.py
├── Dockerfile
├── requirements.txt
└── pyproject.toml
```

**LLM Router / Fallback-Strategie:**
```python
# Pseudocode für die Fallback-Logik
class LLMRouter:
    providers = [
        {"model": "gpt-4o", "priority": 1, "max_rpm": 60, "cost_per_1k": 0.01},
        {"model": "gpt-4o-mini", "priority": 2, "max_rpm": 200, "cost_per_1k": 0.0003},
        {"model": "gpt-3.5-turbo", "priority": 3, "max_rpm": 500, "cost_per_1k": 0.0005},
    ]

    # Circuit Breaker: nach 3 Fehlern in 60s → Provider disabled für 120s
    # Load Detection: wenn RPM > 80% von max_rpm → nächsten Provider nutzen
    # Token Budget: tägliches/monatliches Limit pro Provider
    # Latency Tracking: wenn avg latency > threshold → downgrade
```

**Tool Use Pattern (OpenAI Function Calling):**
```python
tools = [
    {
        "type": "function",
        "function": {
            "name": "search_documents",
            "description": "Durchsucht hochgeladene Dokumente nach relevanten Informationen.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Die Suchanfrage"}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "query_hr_system",
            "description": "Ruft HR-Daten ab: Urlaubstage, Gehaltsinformationen, Mitarbeiterdaten, Organigramm.",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {"type": "string", "enum": ["vacation_balance", "salary_info", "employee_lookup", "org_chart", "time_tracking"]},
                    "employee_id": {"type": "string"},
                    "parameters": {"type": "object"}
                },
                "required": ["action"]
            }
        }
    }
]
```

---

### 3. PYTHON BACKEND — RAG Service

```
services/rag-service/
├── app/
│   ├── main.py
│   ├── config.py
│   ├── routers/
│   │   ├── ingest.py           # POST /ingest (Upload + Process)
│   │   ├── search.py           # POST /search (Query)
│   │   └── documents.py        # GET /documents, DELETE /documents/:id
│   ├── services/
│   │   ├── document_loader.py  # PDF, TXT, MD, DOCX Parser
│   │   ├── chunker.py          # Intelligent Chunking (recursive, semantic)
│   │   ├── embedder.py         # OpenAI text-embedding-3-small
│   │   └── vector_store.py     # ChromaDB / pgvector Interface
│   ├── models/
│   │   └── document.py
│   └── middleware/
│       └── auth.py
├── tests/
├── Dockerfile
└── requirements.txt
```

**Chunking-Strategie:**
- Recursive Character Text Splitter (chunk_size=512, overlap=50)
- Metadata pro Chunk: source_file, page_number, chunk_index
- Semantic Chunking als Option (sentence-transformers basiert)

**Vector Store:**
- ChromaDB für lokale Entwicklung (zero-config)
- pgvector für Production (PostgreSQL Extension)
- Abstraction Layer: Interface das beides unterstützt

---

### 4. PYTHON BACKEND — HR Service (Mock External API)

**Thematisch perfekt für Trenkwalder** (Personaldienstleister!).

```
services/hr-service/
├── app/
│   ├── main.py
│   ├── config.py
│   ├── routers/
│   │   ├── employees.py        # CRUD Employees
│   │   ├── vacation.py         # Urlaubsverwaltung
│   │   ├── salary.py           # Gehaltsinformationen
│   │   ├── timetracking.py     # Zeiterfassung
│   │   └── org.py              # Organigramm
│   ├── services/
│   │   └── hr_data.py          # Mock Data Generator (Faker)
│   ├── models/
│   │   ├── employee.py
│   │   ├── vacation.py
│   │   └── salary.py
│   └── database/
│       ├── init_db.py          # SQLite/PostgreSQL Setup
│       └── seed.py             # Realistic Seed Data
├── tests/
├── Dockerfile
└── requirements.txt
```

**Mock-Daten (realistisch, deutsch):**
- 50+ Mitarbeiter mit deutschen Namen, Abteilungen, Positionen
- Urlaubskonten mit Historie
- Gehaltsbänder nach Position
- Zeiterfassung der letzten 30 Tage
- Organigramm mit 3-4 Hierarchie-Ebenen
- Abteilungen: IT, HR, Finance, Sales, Operations, Marketing

---

### 5. SECURITY LAYER

**Kritisch — zeigt Enterprise-Denken.**

```
Ebene 1: Transport
  - TLS 1.3 everywhere (AWS ALB terminiert)
  - HSTS Headers
  - CORS strict (nur eigene Domain)

Ebene 2: Authentication & Authorization
  - API Keys für Service-to-Service (internal)
  - JWT für User-Sessions (Frontend ↔ BFF)
  - RBAC-ready (Admin, User, Viewer Rollen)

Ebene 3: Input Validation
  - Pydantic Models für alle Inputs (strict mode)
  - File Upload: nur erlaubte MIME Types, Max Size 10MB
  - Prompt Injection Detection (basic heuristics + system prompt hardening)
  - XSS/SQL Injection Prevention

Ebene 4: Rate Limiting & Abuse Prevention
  - Token Bucket per User (Redis-backed)
  - Sliding Window für LLM Calls
  - Cost Tracking per User/Session

Ebene 5: Observability
  - Structured JSON Logging (alle Services)
  - Request Tracing (correlation IDs)
  - Health Checks + Readiness Probes
  - Prometheus Metrics Endpoint (optional)

Ebene 6: Secret Management
  - AWS Secrets Manager / SSM Parameter Store
  - Keine Secrets in Code oder Environment Files
  - .env nur für lokale Entwicklung, .env.example committed
```

---

### 6. AWS INFRASTRUCTURE

```
AWS Architecture:
├── VPC
│   ├── Public Subnet
│   │   ├── ALB (Application Load Balancer)
│   │   └── NAT Gateway
│   ├── Private Subnet
│   │   ├── ECS Fargate Cluster
│   │   │   ├── Chat Orchestrator Service (auto-scaling)
│   │   │   ├── RAG Service (auto-scaling)
│   │   │   └── HR Service (auto-scaling)
│   │   ├── ElastiCache Redis
│   │   └── RDS PostgreSQL (mit pgvector)
│   └── Isolated Subnet
│       └── Secrets Manager
├── S3
│   ├── Document Storage Bucket
│   └── Frontend Static Assets (wenn self-hosted)
├── CloudFront (CDN für Frontend)
├── ECR (Container Registry)
├── CloudWatch (Logging + Monitoring)
└── IAM (Least Privilege Roles)
```

**Auto-Scaling Regeln:**
- Chat Orchestrator: Scale bei CPU > 70% oder Request Count > 100/min
- RAG Service: Scale bei CPU > 80% (embedding-intensive)
- HR Service: Minimal (1 Task), scale bei need

**Infrastructure as Code:**
- Terraform oder AWS CDK (TypeScript) für alle Ressourcen
- Separate Stacks: Network, Database, Services, Monitoring

---

### 7. DOCKER & LOCAL DEVELOPMENT

```yaml
# docker-compose.yml
version: "3.9"
services:
  frontend:
    build: ./frontend
    ports: ["3000:3000"]
    environment:
      - NEXT_PUBLIC_API_URL=http://localhost:3000/api

  chat-orchestrator:
    build: ./services/chat-orchestrator
    ports: ["8001:8000"]
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - RAG_SERVICE_URL=http://rag-service:8000
      - HR_SERVICE_URL=http://hr-service:8000
      - REDIS_URL=redis://redis:6379
    depends_on: [redis, rag-service, hr-service]

  rag-service:
    build: ./services/rag-service
    ports: ["8002:8000"]
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - CHROMA_HOST=chromadb
    depends_on: [chromadb]
    volumes:
      - document-storage:/data/documents

  hr-service:
    build: ./services/hr-service
    ports: ["8003:8000"]
    depends_on: [postgres]

  redis:
    image: redis:7-alpine
    ports: ["6379:6379"]

  chromadb:
    image: chromadb/chroma:latest
    ports: ["8004:8000"]
    volumes:
      - chroma-data:/chroma/chroma

  postgres:
    image: pgvector/pgvector:pg16
    ports: ["5432:5432"]
    environment:
      - POSTGRES_DB=trenkwalder_hr
      - POSTGRES_USER=admin
      - POSTGRES_PASSWORD=${DB_PASSWORD}
    volumes:
      - pg-data:/var/lib/postgresql/data

volumes:
  document-storage:
  chroma-data:
  pg-data:
```

---

### 8. ARCHITECTURE DECISION RECORDS (ADRs)

Jede Entscheidung dokumentiert in `docs/adr/`:

```
docs/adr/
├── 001-microservice-architecture.md
├── 002-python-fastapi-backend.md
├── 003-nextjs-frontend.md
├── 004-openai-function-calling-for-tool-use.md
├── 005-chromadb-vector-store.md
├── 006-llm-fallback-strategy.md
├── 007-sse-streaming.md
├── 008-docker-compose-local-dev.md
├── 009-aws-ecs-fargate-deployment.md
└── 010-security-layers.md
```

**ADR Format:**
```markdown
# ADR-001: Microservice Architecture

## Status: Accepted
## Date: 2026-03-26

## Context
Die Aufgabe verlangt einen Chatbot mit RAG und External API Integration.
Ein Monolith wäre einfacher, aber...

## Decision
Wir nutzen eine Microservice-Architektur mit 3 Services:
Chat Orchestrator, RAG Service, HR Service.

## Consequences
+ Unabhängige Skalierung (RAG ist compute-intensive)
+ Klare Verantwortlichkeiten
+ Einfach erweiterbar um neue Tools/Services
+ Einzelne Services können unabhängig deployed werden
- Höhere Komplexität in Local Dev (→ gelöst durch docker-compose)
- Network Latency zwischen Services (→ mitigiert durch internes Netzwerk)

## Alternatives Considered
- Monolith mit FastAPI: Einfacher, aber schwerer skalierbar
- Serverless (Lambda): Zu viel Cold Start Latency für Chat
```

---

### 9. README.md STRUKTUR

```markdown
# 🤖 Trenkwalder AI Assistant

> An intelligent chatbot platform with RAG capabilities and HR system integration.
> Built with passion. One bot at a time.

## 🏗️ Architecture
[Architektur-Diagramm]

## 🚀 Quick Start
```bash
# Clone
git clone ...
cd trenkwalder-ai-assistant

# Environment
cp .env.example .env
# Add your OPENAI_API_KEY

# Start everything
docker-compose up -d

# Open
open http://localhost:3000
```

## 📖 Features
- **RAG Chat**: Upload documents, ask questions
- **HR Integration**: Query vacation, salary, org data
- **Intelligent Routing**: LLM decides which tool to use
- **Streaming**: Real-time response streaming via SSE
- **Fallback**: Automatic LLM provider switching under load
- **Security**: Multi-layer security architecture

## 🧪 Testing
## 📐 Architecture Decisions
## 🔐 Security
## ☁️ AWS Deployment
## 📊 Monitoring
```

---

### 10. TESTING-STRATEGIE

```
Unit Tests:
  - pytest für alle Python Services
  - Jest + React Testing Library für Frontend
  - Coverage Target: >80%

Integration Tests:
  - Service-to-Service Kommunikation
  - RAG Pipeline End-to-End (Upload → Chunk → Embed → Search → Answer)
  - Tool Use Flow (User Frage → LLM → Tool Call → Response)

E2E Tests (optional, nice-to-have):
  - Playwright für Frontend Flows
  - Full Chat Conversation Test

Load Tests (nice-to-have):
  - Locust für Backend Load Testing
  - Verifiziert Fallback-Strategie unter Last
```

---

## PROJEKT-REPOSITORY STRUKTUR (FINAL)

```
trenkwalder-ai-assistant/
├── README.md
├── docker-compose.yml
├── docker-compose.prod.yml
├── .env.example
├── .gitignore
├── Makefile                    # make dev, make test, make deploy
│
├── frontend/
│   ├── package.json
│   ├── next.config.js
│   ├── tailwind.config.ts
│   ├── tsconfig.json
│   ├── Dockerfile
│   ├── app/
│   ├── components/
│   ├── lib/
│   ├── hooks/
│   └── types/
│
├── services/
│   ├── chat-orchestrator/
│   │   ├── app/
│   │   ├── tests/
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   ├── rag-service/
│   │   ├── app/
│   │   ├── tests/
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   └── hr-service/
│       ├── app/
│       ├── tests/
│       ├── Dockerfile
│       └── requirements.txt
│
├── infrastructure/
│   ├── terraform/              # oder cdk/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   ├── vpc.tf
│   │   ├── ecs.tf
│   │   ├── rds.tf
│   │   └── outputs.tf
│   └── scripts/
│       ├── deploy.sh
│       └── seed-data.sh
│
├── docs/
│   ├── adr/
│   │   ├── 001-microservice-architecture.md
│   │   ├── ...
│   │   └── 010-security-layers.md
│   ├── architecture.md
│   ├── api-spec.md
│   └── security.md
│
├── shared/
│   └── types/                  # Shared Pydantic/TS Types
│
└── .github/
    └── workflows/
        ├── ci.yml              # Lint + Test on PR
        └── deploy.yml          # Deploy to AWS on merge to main
```

---

## CLAUDE PROJECT — CUSTOM INSTRUCTIONS

Nutze folgendes als Custom Instructions im Claude Project:

```
Du bist ein Senior Full-Stack Engineer der eine Production-Grade AI Chatbot Platform baut.

PROJEKT: Trenkwalder AI Assistant
STACK: Next.js 14 (App Router, TypeScript, Tailwind, shadcn/ui) + Python FastAPI Microservices + AWS

ARCHITEKTUR:
- Frontend: Next.js mit BFF-Pattern (API Routes als Proxy)
- Chat Orchestrator: FastAPI — LLM Routing, Tool Use (OpenAI Function Calling), Streaming (SSE)
- RAG Service: FastAPI — Document Upload, Chunking, Embedding (OpenAI), Vector Search (ChromaDB/pgvector)
- HR Service: FastAPI — Mock HR API (Urlaub, Gehalt, Mitarbeiter, Zeiterfassung, Organigramm)
- Infrastructure: Docker Compose (lokal), AWS ECS Fargate (prod), Terraform/CDK

DESIGN-PRINZIPIEN:
1. Klare Separation of Concerns — jeder Service hat eine einzige Verantwortung
2. Security-First — Multi-Layer Security, keine Shortcuts
3. Production-Ready — Logging, Health Checks, Error Handling, Graceful Degradation
4. LLM Fallback — Circuit Breaker Pattern, automatischer Model-Downgrade bei Last
5. Minimalistisches UI — jedes Element hat einen Grund, subtile Animationen, Dark Mode
6. Testbar — pytest, Jest, >80% Coverage Target
7. Dokumentiert — ADRs für jede architektonische Entscheidung

CODE-STIL:
- Python: PEP 8, Type Hints everywhere, Pydantic Models, async/await
- TypeScript: Strict mode, keine any, Zod für Runtime-Validation
- Commits: Conventional Commits (feat:, fix:, docs:, refactor:)
- Error Messages: Immer hilfreich und actionable

KONTEXT:
Dies ist eine Test-Aufgabe für eine Fullstack-Developer-Stelle bei Trenkwalder.
Der Team Lead (Damjan Savić) ist ein AI/Automation-Enthusiast der "One bot at a time" als Motto hat.
Die Aufgabe verlangt einen Chatbot mit RAG + External API Calls.
Wir over-delivern mit einer Enterprise-Grade Lösung.
Qualität > Geschwindigkeit. Jede Zeile Code muss intentional sein.
```

---

## PRIORITÄTEN (Reihenfolge der Implementierung)

1. **Projekt-Skeleton** — Repo, Docker Compose, alle Services als Hello World
2. **Chat Orchestrator** — LLM Integration, Tool Use, Streaming
3. **RAG Service** — Document Upload, Chunking, Embedding, Search
4. **HR Service** — Mock Data, REST API
5. **Frontend** — Chat UI, Document Upload, Streaming
6. **Integration** — Alles zusammen, End-to-End Flow
7. **Security** — Auth, Rate Limiting, Input Validation
8. **LLM Fallback** — Circuit Breaker, Load Detection
9. **AWS Deployment** — Terraform/CDK, ECS, RDS, etc.
10. **Polish** — ADRs, README, Tests, CI/CD

---

## BEISPIEL-KONVERSATIONEN (für Testing)

```
User: "Was steht in dem Dokument über die Urlaubsregelung?"
→ Bot nutzt RAG Tool → Durchsucht hochgeladenes Dokument → Antwortet mit Quellenangabe

User: "Wie viele Urlaubstage hat Maria Schmidt noch?"
→ Bot nutzt HR Tool → query_hr_system(action="vacation_balance", employee_id="...") → Antwortet

User: "Fasse das Dokument zusammen und sag mir gleichzeitig wie viele Mitarbeiter in der IT arbeiten"
→ Bot nutzt BEIDE Tools → RAG + HR → Kombinierte Antwort

User: "Hallo, wer bist du?"
→ Bot antwortet direkt (kein Tool nötig) → Stellt sich als Trenkwalder AI Assistant vor
```
