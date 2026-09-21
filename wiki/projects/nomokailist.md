---
type: index
title: "nomokailist: What We Learned"
review_after: 2027-03-20
---

# nomokailist: What We Learned

## Current state

235 verified claim(s) from 235 analyzed sources.

## Key findings

- The NomikaiList backend is built with FastAPI and LangGraph 1.0 for recommendation agents." [1]
- The NomikaiList frontend uses Next.js with shadcn UI components." [2]
- The database is Supabase (PostgreSQL + RLS) and no direct DB access is permitted from the frontend; all queries must go through the API laye [3]
- The Python package manager for NomikaiList is `uv`, not pip or poetry." [4]
- Type hints are required on all Python function signatures and enforced by mypy." [5]
- TDD is required: a failing test must be written before implementing a new feature." [6]
- Backend test coverage must be at least 68%, enforced in CI via --cov-fail-under=68." [7]
- The unified ingestion pipeline runs as one command (`nomikai ingest run --mode batch|stream|refresh`) orchestrating Phases A–D (populate → e [8]
- Phase D (validate) runs automatically after Phase C, computing a field-status matrix and three measurements (required_completeness, enrichme [9]
- Ingestion exit codes for k3s Job.backoffLimit are: 0=success, 2=populate, 3=extract, 4=commit, 5=validate, 6=graph_validate (agent construct [10]
- Tier-based cache TTL in by_request_hash_tiered is: finished=90d, airing=3d, upcoming=14d, NULL=7d, with status sourced from media_raw_payloa [11]
- LangGraph agent state in NomikaiList uses TypedDict (not dataclass), and tools return dicts for LangGraph to merge rather than mutating stat [12]
- The team decided to use Supabase as the sole backend infrastructure provider for database, authentication, file storage, and real-time subsc [13]
- SQLAlchemy ORM is explicitly excluded in favor of using the Supabase Python client directly." [14]
- Redis is explicitly excluded, with Supabase used for caching patterns where needed." [15]

