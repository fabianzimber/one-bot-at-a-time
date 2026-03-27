# Architecture Decisions

This document is the architecture decision log for `one-bot-at-a-time` on branch `main` as of March 27, 2026.

It exists because the repository currently contains three different layers of architectural intent:

- the original project brief in [trenkwalder-project-brief.md](./trenkwalder-project-brief.md)
- older aspirational sections in [README.md](./README.md)
- the implemented Vercel-first branch state in code and environment wiring

When these sources conflict, the implemented branch state wins for deployment, debugging, and operations.

## How To Read This File

- `Historical` means the decision was part of the original brief or an earlier design target.
- `Current` means the decision is implemented in this branch and should be treated as the operational source of truth.
- `Superseded` means the original idea was reasonable at design time but has been replaced by a more practical implementation choice.

## Historical Decisions That Still Stand

### 1. Build a platform, not just a CLI

- Historical decision: over-deliver beyond the minimum CLI requirement and demonstrate design quality, system thinking, and maintainability.
- Current status: retained.
- Why it stayed: the final shape still needs to prove architecture judgment, not just prompt-response behavior. The frontend BFF, separate RAG and HR services, and production-oriented deployment choices all follow from this decision.

### 2. Use a Next.js frontend with a Backend-for-Frontend boundary

- Historical decision: keep the browser talking to a single frontend-owned API layer instead of exposing backend services directly.
- Current status: retained and implemented.
- Why it stayed: it gives one public boundary for bot protection, same-origin behavior, error mapping, and future auth. It also keeps Python service URLs private and replaceable.

### 3. Split backend responsibilities into chat, RAG, and HR domains

- Historical decision: separate the orchestration layer, document retrieval, and HR data access into distinct services.
- Current status: retained and implemented.
- Why it stayed: these domains scale and fail differently. The split also keeps the chat orchestrator focused on tool routing instead of absorbing retrieval and HR-specific data logic.

### 4. Use LLM tool calling instead of brittle intent routing

- Historical decision: let the model decide when to call document search or HR data tools.
- Current status: retained and implemented.
- Why it stayed: this keeps routing logic extensible and avoids hardcoding intent rules that get brittle as the tool surface expands.

### 5. Keep structured business data and retrieval state conceptually separate

- Historical decision: HR data, document metadata, and vector search should not collapse into one undifferentiated store.
- Current status: retained, with a practical preview-first implementation.
- Why it stayed: document lifecycle operations such as list and delete need durable metadata independent of the vector backend, and HR data needs relational semantics that differ from retrieval storage.

### 6. Stream answers to the UI

- Historical decision: responses should be streamed instead of waiting for a fully buffered reply.
- Current status: retained and implemented.
- Why it stayed: the assistant feels materially better when intermediate progress is visible, especially when a request triggers tool use or multiple backend hops.

### 7. Treat security as layered rather than one middleware toggle

- Historical decision: use multiple boundaries such as frontend protection, internal auth, validation, and constrained origins.
- Current status: retained and implemented in a Vercel-specific form.
- Why it stayed: AI endpoints are expensive and attractive abuse targets. The repo now reflects that with a public BFF boundary, BotID on public routes, and `x-internal-api-key` on private service hops.

## Historical Decisions That Changed

### 8. Deployment target changed from mixed options and Fly.io discussions to Vercel-first execution

- Historical decision: the brief and older README discussed AWS Amplify, Vercel, and Fly.io as viable deployment targets.
- Current decision: the active deployment model is four Vercel projects:
  - `one-bot-at-a-time`
  - `one-bot-at-a-time-chat-orchestrator`
  - `one-bot-at-a-time-rag-service`
  - `one-bot-at-a-time-hr-service`
- Why it changed: the project needed one real operating model, not multiple equally plausible targets. Vercel won because preview deployments, branch aliases, environment management, and the frontend hosting model were already aligned there.

### 9. `services/shared` is not deployed as its own runtime unit

- Historical decision: the monorepo included `services/shared` as a normal shared package.
- Current decision: `services/shared` remains the source of truth for shared code, but it is not deployed as a separate service.
- Why it changed: the shared package has no independent runtime responsibility. Deploying it separately would add complexity without creating a real boundary. For Vercel reliability, each Python service vendors a `src/shared` copy into its serverless bundle. A compatibility entrypoint still exists for tests, but it is not part of the active four-project deployment model.

### 10. Preview environments optimize for deployability, not final production persistence

- Historical decision: long-term storage targets included PostgreSQL with `pgvector`, Redis, and object storage.
- Current decision: previews currently run with SQLite-backed metadata and `chroma`, while production intent remains Postgres or Neon with `pgvector`.
- Why it changed: durable infrastructure should not block end-to-end verification of the product. The branch needed a working preview chain first, so the persistence strategy was staged rather than fully provisioned on day one.

### 11. Service initialization cannot rely on startup hooks alone

- Historical decision: older architecture sketches implicitly assumed traditional long-lived service startup semantics.
- Current decision: runtime initialization is guarded by lazy accessors in addition to FastAPI lifespan setup.
- Why it changed: Vercel serverless behavior, tests, and cold starts are less forgiving than a long-lived VM or container. Lazy guards reduce failures caused by partially initialized global state.

### 12. Preview routing uses stable branch aliases instead of per-deployment URLs

- Historical decision: preview connectivity was not fully specified in the brief.
- Current decision: preview environments are chained by branch alias:
  - frontend branch alias -> chat branch alias
  - chat branch alias -> rag branch alias
  - chat branch alias -> hr branch alias
- Why it changed: one-off deployment URLs created drift and broke cross-service previews after redeploys. Branch aliases keep the whole chain aligned across fresh deployments.

## Current Branch Decisions

### 13. The public boundary is the frontend BFF

- Current decision: browsers should call `POST /api/chat`, `POST /api/chat/stream`, and `POST /api/documents` on the frontend, not the Python services directly.
- Why: this keeps public concerns in one place:
  - BotID verification
  - future user auth
  - consistent same-origin requests
  - public rate limiting
  - cleaner error translation

### 14. Internal service hops are authenticated with `x-internal-api-key`

- Current decision: the frontend and Python services share `INTERNAL_API_KEY`, and internal routes require the matching header.
- Why: it is the lightest viable protection for private service-to-service traffic on Vercel and was required to stop otherwise healthy preview deployments from failing with unauthorized cross-service calls.

### 15. Chat must degrade gracefully when Redis is absent

- Current decision: conversation state and rate limiting use Redis when available and fall back to in-memory implementations when it is not.
- Why: previews and local development should still function even before every managed dependency is provisioned. The fallback keeps the app usable without pretending that preview persistence is durable.

### 16. OpenAI tool-calling is paired with deterministic non-LLM fallbacks

- Current decision: the chat orchestrator uses OpenAI when configured, but tests and degraded environments still have deterministic paths.
- Why: the codebase needs reliable CI and preview behavior even when live model access is missing or intentionally disabled.

### 17. RAG ingestion is designed for serverless constraints

- Current decision: uploads are processed from bytes in memory rather than through assumptions about durable local files.
- Why: Vercel functions are not a safe place to assume persistent writable disk. Designing for in-memory ingestion avoids a whole class of deployment-only failures.

### 18. RAG metadata and vector retrieval are separate concerns

- Current decision: SQL-backed document metadata exists alongside a vector store abstraction.
- Why: listing, deleting, and tracing documents should not require vector-store-specific logic. This split also preserves a migration path from `chroma` previews to `pgvector` production.

### 19. HR data is seeded into the database and then served as real records

- Current decision: the HR service seeds realistic `de_DE` Faker data on first boot and serves employee, vacation, salary, time-tracking, and org responses from persisted rows.
- Why: persisted seeded data behaves like a small internal system and is much more useful for orchestration, demos, and tests than hardcoded response stubs.

### 20. HR queries accept human-readable employee references and resolve IDs internally

- Current decision: frontend prompts, LLM tool calls, and chat fallbacks should prefer human-readable employee references such as first names, last names, or forms like `Frau Dowerg`; the chat orchestrator resolves those references to stable employee IDs before calling the HR service.
- Why: opaque IDs like `emp-001` are implementation details and make the assistant feel artificial. Keeping names at the conversational boundary improves demos and usability, while preserving the HR service's stable ID-based API behind the orchestrator.

### 21. SSE must be treated as a wire protocol, not as a platform-specific implementation detail

- Current decision: the frontend normalizes CRLF line endings before splitting SSE frames.
- Why: the preview deployment exposed a real integration issue where the backend stream was correct but the browser client still failed. The fix belongs in the client because standards-compliant SSE can arrive with `\r\n`.

### 22. Vercel `rootDirectory` settings are part of the deployment contract

- Current decision: CLI deploys must be executed from the repository root for linked projects that already define `rootDirectory`.
- Why: deploying from nested directories caused paths like `frontend/frontend` and equivalent backend failures. This is now an operational rule, not a suggestion.

### 23. Large Python bundles are accepted as temporary operational debt

- Current decision: current Vercel Python deployments may trigger runtime dependency installation because the bundle exceeds Vercel's direct packaging limits.
- Why: this was accepted to get the system running end-to-end first. It is explicitly debt, not the final desired steady state.

## Explicitly Rejected Or Deferred Choices

### 24. Do not deploy `services/shared` as a fourth backend

- Rejected choice: turn shared code into its own service.
- Why rejected: shared code has no separate runtime responsibility, would add another failure mode, and would force unnecessary network hops for code that should stay in-process.

### 25. Do not expose Python services directly to the browser

- Rejected choice: let the frontend call chat, rag, or hr services from the client.
- Why rejected: this would duplicate public security concerns, leak internal topology, complicate CORS, and make future auth changes harder.

### 26. Do not rely on ephemeral deployment URLs for preview wiring

- Rejected choice: manually connect previews via one-off deployment URLs.
- Why rejected: redeploys invalidate the assumed chain and create configuration drift. Branch aliases are the stable abstraction.

### 27. Do not treat preview persistence as if it were production-grade durability

- Rejected choice: imply that SQLite in `/tmp` or preview `chroma` storage is already the durable production answer.
- Why rejected: that would blur an important operational boundary. The branch is E2E-functional, but durable production persistence remains a clearly separated next step.

### 28. Do not assume Vercel preview protection alone can substitute for internal service auth

- Rejected choice: rely only on deployment-level protection between services.
- Why rejected: protected previews complicated internal service hops and did not remove the need for explicit service-to-service authentication. `INTERNAL_API_KEY` remains the dependable mechanism inside the service graph.

## Current Source Of Truth

For day-to-day work in this branch, use the following order:

1. Running code and environment wiring in this branch
2. [AGENTS.md](./AGENTS.md)
3. This file
4. The implementation-summary section in [README.md](./README.md)
5. Older aspirational sections in [README.md](./README.md) and the original [trenkwalder-project-brief.md](./trenkwalder-project-brief.md)

## Next Decisions Likely To Change

These are the most likely future architecture updates:

- move RAG production persistence from preview-style `chroma` and SQLite toward Postgres or Neon with `pgvector`
- reduce Python Vercel bundle size so runtime dependency installation is no longer required
- add durable production-grade storage for original uploaded documents if long-term retention becomes a requirement
- tighten production-only auth and rate limiting once the public `onebot.run` traffic shape is known
