---
type: index
title: "nomokailist: What We Learned"
review_after: 2027-03-20
---

# nomokailist: What We Learned

## Current state

238 verified claim(s) from 238 analyzed sources.

## Key findings

- Backend lint and typecheck are run with `cd backend && uv run ruff check src/ && uv run mypy src/`." [1]
- Frontend verification runs `cd frontend && npm run lint && npm run type-check`." [2]
- The backend uses FastAPI + LangGraph 1.0 for recommendation agents." [3]
- The frontend uses Next.js with shadcn UI components." [4]
- There is no direct DB access from the frontend; all queries go through the API layer." [5]
- The package manager for Python is `uv` (not pip/poetry)." [6]
- Type hints are required on all function signatures and enforced by mypy." [7]
- TDD is required: write a failing test first, then implement." [8]
- Backend minimum coverage is 68%, enforced in CI." [9]
- The unified ingestion pipeline runs as one command `nomikai ingest run --mode batch|stream|refresh` orchestrating Phases A–D (populate → ext [10]
- Exit codes are 0=success, 2=populate, 3=extract, 4=commit, 5=validate, 6=graph_validate (agent construction failure), 64=usage error." [11]
- Tier-based cache TTL in `by_request_hash_tiered` is finished=90d / airing=3d / upcoming=14d / NULL=7d." [12]
- Supabase is used as the sole backend infrastructure provider for database, authentication, file storage, and real-time subscriptions." [13]
- SQLAlchemy ORM is explicitly excluded; the Supabase Python client is used directly instead." [14]
- Redis is explicitly excluded; Supabase is used for caching patterns where needed." [15]

