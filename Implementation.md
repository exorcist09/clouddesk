# Implementation Plan — CloudDesk Smart Customer Support Agent

> Derived from [PRD.txt](file:///home/grey/Documents/gydeon/PRD.txt). Repo inspected: backend/app and backend/tests are empty, Dockerfiles are empty, frontend has a bun-based Next.js 16 skeleton with empty components and pages.

---

## Repo State Summary

| Layer | Status |
|-------|--------|
| `backend/app/` | Empty. requirements.txt has FastAPI, LangGraph, SQLAlchemy, psycopg, langgraph-checkpoint-postgres |
| `backend/tests/` | Empty |
| `backend/Dockerfile` | Empty |
| `frontend/` | Next.js 16 + bun + Tailwind v4 skeleton. Empty page/component files. No API client logic yet |
| `docker-compose.yml` | Empty |
| `.env.example` | Empty |
| `.gitignore` | Empty |

**Missing from requirements.txt** (must add): `pgvector`, `alembic`, `pytest`, `pytest-asyncio`, `httpx` (test client), `sentence-transformers` (or a lighter embedding lib), `asyncpg`.

---

## Phase 1 — Foundation: Config, DB Models, Migrations, Seed Data

**Goal**: Postgres schema up, seed data in, persistence tests green.

### Steps

1. **`.env.example` + `.gitignore`**
   - Define all env vars: `OPENROUTER_API_KEY`, `OPENROUTER_MODEL`, `EMBEDDING_MODEL`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`, `DATABASE_URL`, `NEXT_PUBLIC_API_URL`.
   - `.gitignore`: `.env`, `__pycache__`, `.venv`, `node_modules`, `.next`.

2. **`backend/app/config.py`**
   - Pydantic `Settings` class reading from env. Validate `OPENROUTER_API_KEY` is present at startup.

3. **`backend/app/database.py`**
   - SQLAlchemy 2.x async engine + session factory. Connect to `DATABASE_URL`.

4. **`backend/app/models/`** — SQLAlchemy ORM models:
   - `customer.py` — `customers` table (id, name, email, subscription_plan, tfa_enabled, team_size).
   - `payment.py` — `payments` table (id, customer_id FK, amount, currency, timestamp, status, reference).
   - `ticket.py` — `tickets` table (id, customer_id FK, customer_email, subject, body, domain, confidence, status enum, workflow_stage, draft_reply, final_reply, escalation_reason, error_info, thread_id, created_at, updated_at).
   - `knowledge_article.py` — `knowledge_articles` (id, title, content, category, embedding vector(384), source).
   - `known_bug.py` — `known_bugs` (id, title, description, workaround, service, status).
   - `outage.py` — `outages` (id, service, description, status, started_at, resolved_at).
   - `review_decision.py` — `review_decisions` (id, ticket_id FK unique, decision enum, edited_response, rejection_reason, reviewer, created_at).

5. **Alembic setup**
   - `alembic init backend/alembic`. Configure `env.py` to read `DATABASE_URL`, auto-enable `pgvector` extension.
   - Initial migration: all tables + pgvector extension + indexes.

6. **`backend/app/seed.py`** — Idempotent seed script:
   - 5+ customers with different subscription plans (Free, Pro, Enterprise).
   - 10+ payments. One customer with a duplicate ₹2,999 charge.
   - 8+ knowledge articles across 3 domains. Generate embeddings and store vectors.
   - 3+ known bugs (one with workaround for Gantt chart/Chrome).
   - 2+ outage records.
   - Idempotent: check before insert, or use `ON CONFLICT DO NOTHING`.

7. **LangGraph checkpoint table init**
   - Use `langgraph-checkpoint-postgres` setup method to create checkpoint tables automatically.

### Files to Create
```
backend/app/__init__.py
backend/app/config.py
backend/app/database.py
backend/app/models/__init__.py
backend/app/models/customer.py
backend/app/models/payment.py
backend/app/models/ticket.py
backend/app/models/knowledge_article.py
backend/app/models/known_bug.py
backend/app/models/outage.py
backend/app/models/review_decision.py
backend/alembic/              (alembic init)
backend/app/seed.py
```

### Tests (Write First / Alongside)
```
backend/tests/conftest.py          — test DB fixture, async session
backend/tests/test_database.py     — connection, schema creation
backend/tests/test_seed.py         — idempotent seeding, record counts
backend/tests/test_models.py       — FK constraints, enum validation
```

### Acceptance Criteria
- [ ] `alembic upgrade head` creates all tables + pgvector extension
- [ ] `python -m app.seed` populates data, re-running does not duplicate
- [ ] LangGraph checkpoint tables exist
- [ ] All Phase 1 tests pass

---

## Phase 2 — Specialist Tools + RAG

**Goal**: Tools query real DB data. Vector search retrieves relevant articles.

### Steps

1. **Embedding utility** — `backend/app/embeddings.py`
   - Use `sentence-transformers` with `all-MiniLM-L6-v2` (384-dim, matches pgvector column).
   - `embed_text(text) -> list[float]` function.
   - Document model download requirement.

2. **`backend/app/tools/`** — Specialist tools (real DB queries, not fakes):
   - `billing.py`:
     - `get_customer_billing_history(customer_id)` — query payments table.
     - `get_current_subscription(customer_id)` — query customers table.
   - `technical.py`:
     - `search_knowledge_base(query)` — vector similarity search on knowledge_articles using pgvector.
     - `get_known_bugs(query)` — query known_bugs table.
     - `get_outage_status(service)` — query outages table.
   - `account.py`:
     - `get_account_details(customer_id)` — query customers (email, plan, 2FA, team_size).
     - `search_knowledge_base(query)` — reuse from technical.

3. **Vector search implementation**
   - SQL: `SELECT ... ORDER BY embedding <=> $query_vector LIMIT 3`.
   - Return empty list + flag when no result above similarity threshold.

### Files to Create
```
backend/app/embeddings.py
backend/app/tools/__init__.py
backend/app/tools/billing.py
backend/app/tools/technical.py
backend/app/tools/account.py
```

### Tests
```
backend/tests/test_tools_billing.py    — billing history, subscription, missing customer
backend/tests/test_tools_account.py    — account details, missing customer
backend/tests/test_tools_technical.py  — vector search relevance, no-match behavior
backend/tests/test_embeddings.py       — dimension check, determinism
```

### Acceptance Criteria
- [ ] `get_customer_billing_history("C001")` returns seeded payment records
- [ ] `search_knowledge_base("add team member")` returns relevant article
- [ ] `search_knowledge_base("quantum flux capacitor")` returns empty / low-relevance result
- [ ] `get_known_bugs("gantt chart")` returns the Gantt/Chrome bug with workaround
- [ ] All Phase 2 tests pass

---

## Phase 3 — LangGraph Workflow + Escalation Logic

**Goal**: Full classify → route → specialist → draft → escalate/resolve pipeline. Checkpoint persistence working.

### Steps

1. **`backend/app/workflow/schemas.py`** — Pydantic models:
   - `ClassificationResult(domain, confidence, explanation)`
   - `DraftResponse(reply_text, summary, sources, requires_escalation, escalation_reason)`
   - `ReviewDecisionInput(decision, edited_response?, rejection_reason?)`

2. **`backend/app/workflow/state.py`** — LangGraph state definition:
   - `TicketState` TypedDict: ticket_id, customer_id, subject, body, domain, confidence, specialist_results, draft, escalation_required, escalation_reason, review_decision, final_reply, status, messages.

3. **`backend/app/workflow/nodes.py`** — Graph nodes:
   - `classify_ticket` — LLM call via OpenRouter. Structured output parsed into `ClassificationResult`. Deterministic validation after.
   - `check_confidence` — Conditional edge. Below threshold → escalate. Above → route.
   - `route_to_specialist` — Conditional edge based on domain.
   - `billing_specialist` — Call billing tools, generate draft with LLM.
   - `technical_specialist` — Call tech tools + RAG, generate draft.
   - `account_specialist` — Call account tools + RAG, generate draft.
   - `apply_escalation_rules` — **Deterministic, not LLM**. Check domain-specific mandatory escalation triggers (refund, dispute, >₹5000, data loss, security, deletion, ownership, unauthorized access, no article found).
   - `prepare_for_review` — Set PENDING_REVIEW, interrupt graph.
   - `auto_resolve` — Set RESOLVED, store final reply.
   - `handle_review_decision` — Resume node. Apply approve/edit/reject.

4. **`backend/app/workflow/graph.py`** — Assemble LangGraph `StateGraph`:
   - Wire nodes + conditional edges.
   - Use `interrupt()` at `prepare_for_review`.
   - Configure PostgreSQL checkpointer for persistence.

5. **`backend/app/workflow/llm.py`** — OpenRouter LLM client:
   - HTTP calls to `https://openrouter.ai/api/v1/chat/completions`.
   - Structured output via system prompt + JSON mode.
   - Retry with backoff on 429/5xx. Timeout. Error handling.
   - Never log API key.

6. **`backend/app/workflow/escalation.py`** — Deterministic escalation rules:
   - Billing: refund request, dispute, amount > ₹5000.
   - Technical: no relevant article, data loss, security concern.
   - Account: deletion, ownership transfer, unauthorized access.
   - Low confidence (any domain).
   - Backend enforces these. LLM opinion alone cannot override.

### Files to Create
```
backend/app/workflow/__init__.py
backend/app/workflow/schemas.py
backend/app/workflow/state.py
backend/app/workflow/nodes.py
backend/app/workflow/graph.py
backend/app/workflow/llm.py
backend/app/workflow/escalation.py
```

### Tests
```
backend/tests/test_classification.py   — structured result validation, domain values
backend/tests/test_escalation.py       — every rule individually, combinations, edge cases
backend/tests/test_routing.py          — domain → correct specialist
backend/tests/test_workflow.py         — mock LLM, full graph traversal, auto-resolve path, escalation path
backend/tests/test_checkpoint.py       — persist, restart, resume workflow
```

### Acceptance Criteria
- [ ] Classification returns valid `ClassificationResult` with domain + confidence
- [ ] Low confidence (< threshold) → direct escalation, specialist never called
- [ ] "charged twice" → Billing → dispute → escalated (not auto-resolved)
- [ ] "delete my account" → Account → deletion → escalated
- [ ] "Gantt chart not loading" → Technical → workaround found → auto-resolved
- [ ] Workflow checkpoint survives backend restart
- [ ] All escalation rules tested and enforced deterministically
- [ ] All Phase 3 tests pass with mocked LLM

---

## Phase 4 — FastAPI Endpoints

**Goal**: REST API complete. All endpoints tested.

### Steps

1. **`backend/app/main.py`** — FastAPI app:
   - Lifespan: init DB, run migrations, seed data, init LangGraph checkpointer.
   - Validate `OPENROUTER_API_KEY` on startup. Fail clearly if missing.
   - CORS middleware for frontend.

2. **`backend/app/api/`** — Route modules:
   - `tickets.py`:
     - `POST /api/tickets` — Validate input (Pydantic), persist ticket, start workflow async, return ticket_id immediately.
     - `GET /api/tickets` — List with filters (status, domain) + pagination.
     - `GET /api/tickets/{ticket_id}` — Full ticket details.
     - `GET /api/tickets/{ticket_id}/status` — Stage + status only.
     - `GET /api/tickets/{ticket_id}/reply` — Final reply when available.
   - `reviews.py`:
     - `GET /api/reviews/pending` — Tickets with status PENDING_REVIEW.
     - `POST /api/tickets/{ticket_id}/review` — Submit decision (approve/edit/reject). Resume graph. Prevent duplicate finalization.

3. **`backend/app/api/schemas.py`** — Pydantic request/response models for all endpoints.

4. **Background processing**: Ticket workflow runs in background task after `POST /api/tickets` returns. Status polling via `GET /api/tickets/{id}/status`.

### Files to Create
```
backend/app/main.py
backend/app/api/__init__.py
backend/app/api/tickets.py
backend/app/api/reviews.py
backend/app/api/schemas.py
```

### Tests
```
backend/tests/test_api_tickets.py    — CRUD, validation, 404, pagination
backend/tests/test_api_reviews.py    — approve, edit, reject, duplicate review, 404
backend/tests/test_api_errors.py     — invalid payloads, LLM failure handling
```

### Acceptance Criteria
- [ ] `POST /api/tickets` returns 201 with ticket_id
- [ ] `GET /api/tickets` returns paginated list with filters
- [ ] `GET /api/tickets/{id}` returns 404 for unknown ID
- [ ] `POST /api/tickets/{id}/review` with approve → ticket finalized
- [ ] Duplicate review → 409 Conflict
- [ ] Invalid payload → 422 with clear errors
- [ ] FastAPI auto-generates OpenAPI docs at `/docs`
- [ ] All Phase 4 tests pass

---

## Phase 5 — Next.js Frontend

**Goal**: Functional dashboard, ticket detail view, human review queue. Talks to FastAPI.

### Steps

1. **`frontend/src/lib/api.ts`** — Typed API client:
   - Base URL from `NEXT_PUBLIC_API_URL`.
   - Functions: `createTicket()`, `listTickets()`, `getTicket()`, `getTicketStatus()`, `getPendingReviews()`, `submitReview()`.
   - Type definitions matching backend Pydantic models.

2. **`frontend/src/app/page.tsx`** — Ticket Dashboard:
   - Table: ID, customer, subject, domain, confidence, status, stage, created_at.
   - Status/domain filter dropdowns.
   - "New Ticket" form (customer_name, email, subject, body).
   - Click row → ticket detail page.

3. **`frontend/src/app/ticket/[id]/page.tsx`** — Ticket Detail:
   - Full ticket info: message, classification, confidence, stage, specialist results, draft, escalation reason, final reply.
   - Auto-refresh status while processing.

4. **`frontend/src/app/review/page.tsx`** — Human Review Queue:
   - List PENDING_REVIEW tickets.
   - For each: customer info, original message, AI draft, escalation reason, confidence.
   - Actions: Approve, Edit+Approve (text area), Reject (reason field).
   - Loading/success/error states. Refresh after action.

5. **Components** (fill existing empty files):
   - `ticket-table.tsx` — Reusable ticket list table.
   - `ticket-status.tsx` — Status badge component.
   - `review-panel.tsx` — Review action panel (approve/edit/reject).

6. **`frontend/src/app/error.tsx`** + **`not-found.tsx`** — Error boundaries.

### Files to Modify/Create
```
frontend/src/lib/api.ts              (fill)
frontend/src/app/page.tsx            (fill)
frontend/src/app/layout.tsx          (keep, minor edits)
frontend/src/app/ticket/[id]/page.tsx (create)
frontend/src/app/review/page.tsx     (fill or create)
frontend/src/app/error.tsx           (fill)
frontend/src/app/not-found.tsx       (fill)
frontend/src/components/ticket-table.tsx   (fill)
frontend/src/components/ticket-status.tsx  (fill)
frontend/src/components/review-panel.tsx   (fill)
```

### Acceptance Criteria
- [ ] Dashboard lists tickets, filters work
- [ ] New ticket form submits to API, shows in list
- [ ] Ticket detail page shows all fields
- [ ] Review queue shows escalated tickets
- [ ] Approve/Edit/Reject actions work and update UI
- [ ] `bun run build` succeeds
- [ ] No direct DB access from frontend

---

## Phase 6 — Docker Compose + Full Integration

**Goal**: `docker compose up --build` starts everything. Clean startup, no race conditions.

### Steps

1. **`backend/Dockerfile`**:
   - Python 3.12 base. Install requirements. Copy app code. Run uvicorn.
   - Include sentence-transformers model download step in build.

2. **`frontend/Dockerfile`**:
   - Bun base image. Install deps. Build Next.js. Run with `bun run start`.

3. **`docker-compose.yml`** — Three services:
   - `db`: `pgvector/pgvector:pg16`. Named volume `pgdata`. Health check via `pg_isready`.
   - `api`: Build from `backend/`. Depends on `db` (condition: service_healthy). Env vars from `.env`. Expose port 8000. Run migrations + seed on startup.
   - `frontend`: Build from `frontend/`. Depends on `api`. `NEXT_PUBLIC_API_URL` set for browser access. Expose port 3000.

4. **Startup order**:
   - DB ready → API starts → runs Alembic migrations → seeds data → inits LangGraph checkpointer → serves.
   - Frontend builds with API URL baked in.

5. **`backend/app/main.py` lifespan**:
   - Wait for DB. Run migrations. Seed. Init checkpointer. Log readiness.

### Files to Create/Fill
```
backend/Dockerfile           (fill)
frontend/Dockerfile          (rewrite — current content is wrong)
docker-compose.yml           (fill)
.env.example                 (fill)
```

### Acceptance Criteria
- [ ] `docker compose up --build` starts all 3 services
- [ ] DB initializes with pgvector extension
- [ ] API serves at `localhost:8000`, `/docs` works
- [ ] Frontend serves at `localhost:3000`
- [ ] Data persists across `docker compose down` / `up` (named volume)
- [ ] No crash loops, no race conditions

---

## Phase 7 — Sample Tickets, Full Test Suite, README, Demo

**Goal**: 5 acceptance tickets pass. All tests green. README complete. Demo recorded or checklist provided.

### Steps

1. **5 Sample Ticket Acceptance Tests** — `backend/tests/test_acceptance.py`:

   | # | Input | Expected Path |
   |---|-------|---------------|
   | 1 | "How do I add a team member?" | Account Mgmt → article found → auto-resolve |
   | 2 | "I was charged twice, Rs 2,999 each" | Billing → dispute → escalate |
   | 3 | "Gantt chart not loading on Chrome" | Technical → known bug + workaround → auto-resolve |
   | 4 | "Please delete my account and all data" | Account Mgmt → deletion → escalate |
   | 5 | "Something is wrong but I don't know what" | Low confidence → direct escalation |

2. **Integration test** — `backend/tests/test_integration.py`:
   - Full lifecycle: submit → classify → route → specialist → resolve/escalate → review → finalize.
   - Restart recovery: interrupt backend, restart, verify checkpoint and ticket state.

3. **Run full test suite**: `pytest backend/tests/ -v`. Fix failures.

4. **README.md** — Fill with:
   - Project overview, architecture diagram (mermaid).
   - Folder structure.
   - Tech stack + justifications.
   - DB design summary.
   - LangGraph workflow explanation.
   - Specialist tools + escalation rules.
   - RAG approach + embedding model.
   - Setup: `.env` creation, `docker compose up --build`.
   - Seed data + test commands.
   - API endpoints table.
   - Assumptions + known limitations.

5. **Demo** — Browser recording or manual checklist:
   - Start app → submit tickets → view classifications → auto-resolve → escalation → review → final state.

### Files to Create/Fill
```
backend/tests/test_acceptance.py
backend/tests/test_integration.py
README.md                          (fill)
```

### Acceptance Criteria
- [ ] All 5 sample tickets produce expected outcomes
- [ ] Full `pytest` suite passes (mocked LLM for unit/integration, live-LLM smoke test opt-in)
- [ ] README is complete and accurate
- [ ] `docker compose up --build` works from clean clone + `.env`
- [ ] No secrets committed
- [ ] Demo recording or checklist created

---

## Dependency Graph

```
Phase 1 (DB + Models + Seed)
    ↓
Phase 2 (Tools + RAG)
    ↓
Phase 3 (LangGraph Workflow)
    ↓
Phase 4 (FastAPI Endpoints)
    ↓           ↓
Phase 5      Phase 6
(Frontend)   (Docker)
    ↓           ↓
Phase 7 (Acceptance + README + Demo)
```

## Key Technical Decisions

| Decision | Choice | Reason |
|----------|--------|--------|
| Embedding model | `all-MiniLM-L6-v2` (384-dim) | Small, fast, no API key needed, runs locally in Docker |
| LLM calls | OpenRouter HTTP API (not LangChain wrapper) | Direct control, fewer dependencies, structured JSON output |
| Migrations | Alembic | Explicit, reproducible, required by PRD |
| Checkpointer | `langgraph-checkpoint-postgres` | Already in requirements.txt, PRD mandates PostgreSQL checkpointer |
| Async | SQLAlchemy async + asyncpg | FastAPI is async, avoid blocking DB calls |
| Background tasks | FastAPI `BackgroundTasks` | Ticket processing runs after response, no extra queue needed |
| Frontend API client | Single `api.ts` with typed fetch wrappers | PRD requires centralized typed client |

## Packages to Add

**Backend** (`requirements.txt`):
- `pgvector` — SQLAlchemy pgvector support
- `alembic` — migrations
- `pytest`, `pytest-asyncio` — testing
- `sentence-transformers` — local embeddings
- `asyncpg` — async PostgreSQL driver
- `python-multipart` — FastAPI form support

**Frontend** (`package.json`):
- No additions needed. React 19 + Next.js 16 + TypeScript + Tailwind v4 sufficient.
