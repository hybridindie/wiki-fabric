---
type: index
title: "nomokailist: What We Learned"
review_after: 2027-03-20
---

# nomokailist — Project Retrospective

nomokailist is a recommendation system built around a catalog of titles that move through finished, airing, and upcoming lifecycle states. Its job is to turn a raw catalog into ranked recommendations, and it does so with a backend of FastAPI and LangGraph 1.0 recommendation agents [3] behind a Next.js frontend built from shadcn UI components [4]. It matters because the interesting engineering is not the ranking itself but the discipline wrapped around it: a single ingestion pipeline, a constitution that is checked by machine, and a deliberately narrow infrastructure surface.

## What was built

The backend is FastAPI plus LangGraph 1.0 for the recommendation agents [3]. The frontend is Next.js with shadcn components [4], and it never touches the database directly — every query goes through the API layer [5].

Ingestion is one command: `nomikai ingest run --mode batch|stream|refresh`, orchestrating Phases A–D (populate → extract → commit → validate) [10]. Each phase has a distinct exit code — 0 success, 2 populate, 3 extract, 4 commit, 5 validate, 6 graph_validate for agent construction failure, 64 usage error [11] — so a caller can tell exactly where a run stopped.

Caching is tier-based in `by_request_hash_tiered`: finished titles 90 days, airing 3 days, upcoming 14 days, NULL 7 days [12].

Supabase is the sole backend infrastructure provider — database, authentication, file storage, and real-time subscriptions [13]. Auth tokens are validated with `supabase.auth.get_user(token)`; there is no static secret decoding [23]. Row Level Security enforces data isolation at the database layer [17], and Supabase Auth supplies PKCE and JWT handling without manual implementation [18].

Tooling is fixed: `uv` for Python packages [6], `ruff check` and `mypy` for backend lint and typecheck [1], `npm run lint && npm run type-check` for the frontend [2].

## Constraints discovered

The sharpest constraint was that SQLAlchemy bypasses Supabase RLS policies unless explicitly configured [19]. That single fact drove the ORM decision. Redis was excluded in favor of Supabase caching patterns [15], and Celery was excluded in favor of async Python tasks or LangGraph workflows [16].

Vendor lock-in is real: migrating away from Supabase requires rewriting repositories [20]. Local development requires Docker to run `supabase start` [24].

Process constraints are equally hard. Type hints are required on all function signatures and enforced by mypy [7]. TDD is required — a failing test first, then implementation [8]. Backend minimum coverage is 68%, enforced in CI [9]. `check-constitution.py` Article II checks for forbidden dependencies in `pyproject.toml` [22].

## Patterns that emerged

The repository pattern isolates Supabase client calls, which converts a future migration from a service/API rewrite into a repository rewrite [21]. That is the mitigation for the lock-in constraint, and it is the reason the constraint is survivable rather than fatal.

The second pattern is a constitution that is both human-readable and machine-checkable. Canonical rules live in `.claude/rules/` as structured Markdown articles I–IX and are the single source of truth [26]. `AGENTS.md` is a derived entry point that summarizes and links the rules but does not replace them [27]. `opencode.json` loads the rules via an instructions glob so sessions have them in context [28]. A checker at `backend/scripts/check-constitution.py` validates the articles against the running codebase on demand and in CI [29]. The update order is defined: `.claude/rules/` → `AGENTS.md` [30].

The third pattern is encoding failure location into exit codes rather than log parsing [11], and the fourth is tiering cache TTL by lifecycle state instead of a single global TTL [12].

This project's evidence contributed to the promoted patterns [[pattern-cluster_1c9cac89]], [[pattern-cluster_6cb87c7c]], [[pattern-cluster_a0bba1b7]], and [[pattern-cluster_cf12208f]].

## Decisions made

Supabase as sole infrastructure provider [13] was chosen with eyes open about lock-in [20], and the repository pattern [21] was adopted as the containment strategy. SQLAlchemy was explicitly excluded [14] because it bypasses RLS [19]. Redis was excluded [15]; Celery was excluded [16]. `uv` was chosen as the Python package manager over pip or poetry [6]. The frontend was forbidden from direct database access [5]. Ingestion was consolidated into one command with three modes rather than separate tools [10]. Rules were centralized in `.claude/rules/` with `AGENTS.md` as a derived summary [26][27].

## Current state

The evidence available for this retrospective does not record a claims count or a graph status snapshot, so neither is asserted here. What is verifiable: the constitution checker runs on demand and in CI [29], the 68% coverage floor is enforced in CI [9], and the pipeline's exit-code taxonomy is defined [11]. The open item is the migration path away from Supabase — the repository pattern makes it a repository rewrite [21], but that rewrite has not been described in the evidence. No related topic articles were recorded for this project, so none are linked.

---

_Generated from the evidence fabric on 2026-09-21. 238 current claim(s) from 238 analyzed sources._
