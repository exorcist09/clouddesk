# Graph Report - gydeon  (2026-10-22)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 315 nodes · 582 edges · 22 communities (13 shown, 9 thin omitted)
- Extraction: 98% EXTRACTED · 2% INFERRED · 0% AMBIGUOUS · INFERRED: 14 edges (avg confidence: 0.94)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- readme_audit.py
- conftest.py
- seed.py
- package.json
- seed_all
- test_tools_technical.py
- compilerOptions
- test_database.py
- test_tools_billing.py
- sqlalchemy_ext_asyncio
- env.py
- layout.tsx
- get_session_factory

## God Nodes (most connected - your core abstractions)
1. `seed_all()` - 25 edges
2. `audit_readme()` - 21 edges
3. `Base` - 20 edges
4. `compilerOptions` - 16 edges
5. `Customer` - 13 edges
6. `embed_batch()` - 10 edges
7. `search_knowledge_base()` - 10 edges
8. `KnowledgeArticle` - 8 edges
9. `KnownBug` - 8 edges
10. `Outage` - 8 edges

## Surprising Connections (you probably didn't know these)
- `test_engine()` --uses--> `Base`  [INFERRED]
  backend/tests/conftest.py → backend/app/database.py
- `get_account_details()` --uses--> `Customer`  [INFERRED]
  backend/app/tools/account.py → backend/app/models/customer.py
- `get_current_subscription()` --uses--> `Customer`  [INFERRED]
  backend/app/tools/billing.py → backend/app/models/customer.py
- `test_customer_email_unique_constraint()` --uses--> `Customer`  [INFERRED]
  backend/tests/test_database.py → backend/app/models/customer.py
- `test_review_decision_unique_per_ticket()` --uses--> `Customer`  [INFERRED]
  backend/tests/test_database.py → backend/app/models/customer.py

## Import Cycles
- None detected.

## Communities (22 total, 9 thin omitted)

### Community 0 - "readme_audit.py"
Cohesion: 0.06
Nodes (47): audit_readme(), count_badges(), detect_project_type(), detect_track(), general_score_badges(), general_score_hero_visual(), general_score_problem_value(), general_score_quick_start() (+39 more)

### Community 1 - "conftest.py"
Cohesion: 0.06
Nodes (37): get_settings(), Return a cached Settings instance., Settings, embed_batch(), embed_text(), _pseudo_vector(), Embedding utility using OpenRouter Embeddings API. Calls OpenRouter's…, Deterministic normalized float vector for offline / test mock. (+29 more)

### Community 2 - "seed.py"
Cohesion: 0.15
Nodes (21): Base, Shared declarative base for all ORM models., Customer, KnowledgeArticle, KnownBug, Outage, Payment, ReviewDecision (+13 more)

### Community 3 - "package.json"
Cohesion: 0.07
Nodes (29): dependencies, next, react, react-dom, devDependencies, tailwindcss, @tailwindcss/turbopack, @types/node (+21 more)

### Community 4 - "seed_all"
Cohesion: 0.16
Nodes (23): AsyncSession, Populate the database with deterministic mock data. Safe to call multiple times…, seed_all(), _upsert_customers(), _upsert_knowledge_articles(), _upsert_known_bugs(), _upsert_outages(), _upsert_payments() (+15 more)

### Community 5 - "test_tools_technical.py"
Cohesion: 0.16
Nodes (19): Specialist tools package for CloudDesk., get_known_bugs(), get_outage_status(), AsyncSession, Check current service outages or incidents. Args: service: Service name to…, Semantic search across knowledge articles using pgvector cosine distance. Args:…, Search known issues and workarounds by keyword or service name. Args: query:…, search_knowledge_base() (+11 more)

### Community 6 - "compilerOptions"
Cohesion: 0.11
Nodes (18): compilerOptions, allowJs, esModuleInterop, incremental, isolatedModules, jsx, lib, module (+10 more)

### Community 7 - "test_database.py"
Cohesion: 0.15
Nodes (17): str, ReviewDecisionType, str, TicketStatus, asyncio, Tests for database connection and schema initialization., DB is reachable and returns a result., pgvector extension must be installed. (+9 more)

### Community 8 - "test_tools_billing.py"
Cohesion: 0.20
Nodes (16): get_current_subscription(), get_customer_billing_history(), AsyncSession, Fetch billing and payment history for a customer. Args: customer_id: The…, Get current subscription plan and status for a customer. Args: customer_id: The…, asyncio, AsyncSession, Tests for billing specialist tools. (+8 more)

### Community 9 - "sqlalchemy_ext_asyncio"
Cohesion: 0.21
Nodes (12): get_account_details(), AsyncSession, Account management specialist tools., Fetch comprehensive account details for a customer. Args: customer_id: The…, asyncio, AsyncSession, Tests for account management specialist tools., Fetch full profile for seeded customer. (+4 more)

### Community 10 - "env.py"
Cohesion: 0.24
Nodes (10): asyncio, do_run_migrations(), _get_url(), Alembic migration environment., Read DATABASE_URL from environment, converting to async driver., Run migrations in 'offline' mode., Run migrations in 'online' mode using async engine., run_migrations_offline() (+2 more)

### Community 11 - "layout.tsx"
Cohesion: 0.18
Nodes (6): nextConfig, frontend_src_app_globals, geistMono, geistSans, metadata, next

### Community 12 - "get_session_factory"
Cohesion: 0.29
Nodes (8): async_sessionmaker, get_db_session(), get_engine(), get_session_factory(), _make_engine(), AsyncSession, FastAPI dependency — yields a scoped DB session., _main()

## Knowledge Gaps
- **47 isolated node(s):** `nextConfig`, `geistMono`, `geistSans`, `metadata`, `next` (+42 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 162 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **9 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `seed_all()` connect `seed_all` to `seed.py`, `test_tools_technical.py`, `test_tools_billing.py`, `sqlalchemy_ext_asyncio`, `get_session_factory`?**
  _High betweenness centrality (0.058) - this node is a cross-community bridge._
- **Why does `Base` connect `seed.py` to `conftest.py`, `env.py`?**
  _High betweenness centrality (0.043) - this node is a cross-community bridge._
- **Why does `Customer` connect `seed.py` to `test_tools_billing.py`, `sqlalchemy_ext_asyncio`, `seed_all`, `test_database.py`?**
  _High betweenness centrality (0.037) - this node is a cross-community bridge._
- **What connects `nextConfig`, `geistMono`, `geistSans` to the rest of the system?**
  _47 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `readme_audit.py` be split into smaller, more focused modules?**
  _Cohesion score 0.06382978723404255 - nodes in this community are weakly interconnected._
- **Should `conftest.py` be split into smaller, more focused modules?**
  _Cohesion score 0.0595959595959596 - nodes in this community are weakly interconnected._
- **Should `package.json` be split into smaller, more focused modules?**
  _Cohesion score 0.06666666666666667 - nodes in this community are weakly interconnected._