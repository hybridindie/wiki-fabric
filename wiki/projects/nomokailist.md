---
type: index
title: "nomokailist: What We Learned"
review_after: 2027-03-20
---

# nomokailist: Project Retrospective

nomokailist is a recommendation system for seasonal anime, built around a unified ingestion pipeline and LangGraph-based recommendation agents. In the knowledge fabric, it serves as a concrete case study for a Supabase-only backend, constitution-as-code, and strict TDD. Its main contribution is not just the product but the set of constraints and patterns that emerged when building an AI-assisted, type-safe, test-driven application on a single infrastructure provider.

## Constraints Discovered

The biggest constraint was the decision to use Supabase as the sole backend infrastructure provider for database, authentication, file storage, and real-time subscriptions. This choice eliminated several common tools: SQLAlchemy ORM, Redis, and Celery were explicitly excluded. The Supabase Python client is used directly, and async Python or LangGraph handles workflows. This simplifies operations but creates vendor lock-in: migrating away requires rewriting repositories. The repository pattern isolates Supabase client calls, so migration is a repository rewrite rather than a service/API rewrite. See [[supabase-as-sole-backend]] and [[repository-pattern]].

Security and auth constraints followed. Built-in Row Level Security enforces data isolation at the database layer. Supabase Auth provides PKCE and JWT token management without manual implementation. Auth tokens are validated via `supabase.auth.get_user(token)` with no static secret decoding. SQLAlchemy bypasses Supabase RLS policies unless explicitly configured, which reinforced the exclusion. Local development requires Docker for `supabase start`. See [[supabase-auth-and-rls]].

Development constraints were equally strict. Type hints are required on all function signatures and enforced by mypy. TDD is required: write a failing test first, then implement. Backend minimum coverage is 68%, enforced in CI. Backend lint and typecheck run with `cd backend && uv run ruff check src/ && uv run mypy src/`. Frontend verification runs `cd frontend && npm run lint && npm run type-check`. The Python package manager is `uv`, not pip or poetry. See [[tdd-and-coverage-gates]] and [[uv-toolchain]].

## Patterns That Emerged

The unified ingestion pipeline became the central operational pattern. It runs as one command: `nomikai ingest run --mode batch|stream|refresh`, orchestrating Phases A–D (populate → extract → commit → validate). Exit codes are explicit: 0=success, 2=populate, 3=extract, 4=commit, 5=validate, 6=graph_validate (agent construction failure), 64=usage error. This makes failures diagnosable without parsing logs. See [[unified-ingestion-pipeline]] and [[exit-code-contract]].

Caching followed a tier-based TTL pattern in `by_request_hash_tiered`: finished=90d, airing=3d, upcoming=14d, NULL=7d. This matches the data's volatility and avoids over-caching stale seasonal information. See [[tiered-cache-ttl]].

The frontend uses Next.js with shadcn UI components. There is no direct DB access from the frontend; all queries go through the API layer. The backend uses FastAPI + LangGraph 1.0 for recommendation agents. This separation keeps the frontend simple and the backend authoritative. See [[frontend-api-boundary]] and [[langgraph-agents]].

Constitution-as-code emerged as a governance pattern. Canonical rules live in `.claude/rules/` as structured Markdown articles (I–IX) and are the single source of truth. `AGENTS.md` is the derived entry point that summarizes and links the rules but does not replace them. `opencode.json` loads the rules via the instructions glob so opencode sessions have them in context. A machine-readable checker at `backend/scripts/check-constitution.py` validates articles against the running codebase on demand and in CI. Article II checks for forbidden dependencies in `pyproject.toml`. The rule update order is defined as `.claude/rules/` → `AGENTS.md`. See [[constitution-as-code]] and [[agent-configuration]].

## Decisions Made

We chose Supabase over a multi-service stack to reduce operational surface area. We accepted vendor lock-in as a trade-off, mitigated by the repository pattern. We excluded SQLAlchemy, Redis, and Celery to avoid bypassing RLS, adding cache infrastructure, or introducing a separate task queue. We chose `uv` for Python dependency management. We chose FastAPI + LangGraph for the backend and Next.js + shadcn for the frontend. We defined explicit exit codes and tiered cache TTLs. We made TDD and type hints non-negotiable, enforced by CI. We made the constitution the source of truth, with a checker to prevent drift.

## Current State

At the time of writing, nomokailist contributes 30 claims to the knowledge fabric. The graph is validated and connected, with claims covering the ingestion pipeline, backend constraints, agent configuration, and frontend boundary. The project remains a reference for Supabase-only architecture, constitution-as-code, and strict TDD in an AI-assisted codebase.

---

_Generated from the evidence fabric on 2026-09-21. 238 current claim(s) from 238 analyzed sources._
