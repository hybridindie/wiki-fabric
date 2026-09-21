---
type: index
title: "nomokailist: What We Learned"
review_after: 2027-03-20
---

# NomikaiList — Project Retrospective

NomikaiList is a full-stack application whose backend pairs FastAPI with LangGraph 1.0 to run recommendation agents [3], and whose frontend is a Next.js app built from shadcn UI components [4]. Data enters through a unified ingestion pipeline, and the entire supporting infrastructure — database, authentication, file storage, real-time subscriptions — is Supabase [13]. The project is worth reading as a case study in self-imposed constraint: a written constitution, checked by a script against the live codebase, decides which dependencies are permitted and how work is verified.

## What was built

The backend is FastAPI plus LangGraph 1.0 for recommendation agents [3]. The frontend is Next.js with shadcn components [4], and it never touches the database directly — every query goes through the API layer [5].

Ingestion is a single command, `nomikai ingest run --mode batch|stream|refresh`, orchestrating four phases: populate → extract → commit → validate [10]. Each phase has its own exit code — 0 success, 2 populate, 3 extract, 4 commit, 5 validate, 6 graph_validate for agent construction failure, 64 usage error [11]. That means a failed run tells you which phase broke without parsing logs.

Caching is tiered by request hash in `by_request_hash_tiered`, with TTLs of 90 days for finished content, 3 days for airing, 14 days for upcoming, and 7 days for NULL [12].

Tooling is deliberately narrow. Python uses `uv`, not pip or poetry [6]. Backend lint and typecheck run as `cd backend && uv run ruff check src/ && uv run mypy src/` [1]; frontend verification runs `cd frontend && npm run lint && npm run type-check` [2].

The AI-assistant configuration lives in `AGENTS.md`, `.opencode/`, and `.claude/rules/`, loaded through `opencode.json` instructions [25]. Canonical rules are structured Markdown articles I–IX in `.claude/rules/` and are the single source of truth [26]. `AGENTS.md` is a derived entry point that summarizes and links them but does not replace them [27], and `opencode.json` loads the rules via an instructions glob so sessions have them in context [28]. A machine-readable checker at `backend/scripts/check-constitution.py` validates the articles against the running codebase on demand and in CI [29]; its Article II checks for forbidden dependencies in `pyproject.toml` [22].

## Constraints discovered

Several constraints came from how Supabase actually behaves rather than from preference. SQLAlchemy bypasses Supabase RLS policies unless explicitly configured [19], which is why SQLAlchemy is excluded outright [14]. Redis is excluded, with Supabase used for caching patterns where needed [15]. Celery is excluded, with async Python tasks or LangGraph handling workflows [16].

Auth tokens are validated via `supabase.auth.get_user(token)` with no static secret decoding [23]. Local development requires Docker to run `supabase start` [24].

Verification constraints are equally hard: type hints are required on all function signatures and enforced by mypy [7]; TDD is required, meaning a failing test is written first and then implemented [8]; and backend minimum coverage is 68%, enforced in CI [9].

## Patterns that emerged

The repository pattern isolates Supabase client calls, so migrating to another backend is a repository rewrite rather than a service or API rewrite [21]. That is the main structural answer to vendor lock-in. Row Level Security enforces data isolation at the database layer [17], and Supabase Auth supplies PKCE and JWT token management without manual implementation [18] — both are capabilities the project gets by staying on the platform rather than by building around it.

The constitution pattern is the other durable result: canonical rules in structured Markdown, a derived entry point that links rather than duplicates them, and a checker that runs both on demand and in CI [26][27][29]. The rule update order is defined as `.claude/rules/` → `AGENTS.md` [30], which keeps the derived file from drifting.

The load-bearing rules promoted from this project's evidence are [[pattern-cluster_1c9cac89]], [[pattern-cluster_6cb87c7c]], [[pattern-cluster_a0bba1b7]], and [[pattern-cluster_cf12208f]].

## Decisions made

Supabase was chosen as the sole backend infrastructure provider for database, authentication, file storage, and real-time subscriptions [13]. The rationale follows from the constraints: RLS gives data isolation at the database layer [17], and Auth provides PKCE and JWT management without hand-rolling it [18].

SQLAlchemy was excluded because it bypasses RLS unless explicitly configured [19]. Redis was excluded in favor of Supabase caching patterns [15]. Celery was excluded in favor of async Python tasks or LangGraph [16]. The repository pattern was adopted specifically to contain the lock-in cost, since migrating away otherwise requires rewriting repositories [20].

`uv` was chosen as the Python package manager over pip and poetry [6]. TDD, mandatory type hints, and the 68% coverage floor were adopted as enforced rules rather than conventions [7][8][9]. Rules were placed in `.claude/rules/` as the single source of truth, with `AGENTS.md` derived from them [26][27].

## Current state

The pipeline phases and their exit codes are defined [10][11], the tiered cache TTLs are set [12], and the constitution checker runs on demand and in CI [29]. The coverage floor of 68% is enforced in CI [9].

What remains open is structural. Vendor lock-in to Supabase still means migrating away requires rewriting repositories [20]; the repository pattern reduces the blast radius but does not remove the dependency [21]. Local development still requires Docker for `supabase start` [24].

The evidence available for this retrospective does not include claim counts or graph status figures, so those are not reported here. No related topic articles were linked for this project.

---

_Generated from the evidence fabric on 2026-09-21. 238 current claim(s) from 238 analyzed sources._
