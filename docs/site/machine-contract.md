---
type: index
title: "Machine-Readable Contract"
description: "Lint codes, catalog.json, CI consumption"
created: 2026-09-19
updated: 2026-09-19
---

# Machine-Readable Contract

This page is the contract surface other systems consume: CI, agent harnesses, dashboards. For the human-readable workflows, start at [Core Workflows](./core-workflows).

Everything the fabric validates and catalogs is available in JSON, so CI and
agent harnesses can consume it without parsing prose:

```bash
wf lint --format json            # errors/warnings with code + page + message, ok flag
python3 scripts/rebuild-index.py # writes registry/catalog.json (catalog with ids, types, scopes, statuses)
```

The lint report codes are stable: `FRONTMATTER`, `BROKEN-LINK`, `SCOPE`,
`REVIEW-AFTER`, `CLAIM`, `CONCEPT`, `PATTERN`, `DUP-ID`, `SOURCE`,
`SOURCE-DRIFT`, `SYNC-CONFLICT`, `ORPHAN`, `LLM-CONFIG`, `GENERATED`,
`STALE-AFTER`, `TRUST-TIER`, `IGNORE-CONFIG`, `VERIFIED`, plus the OKF-floor
`OKF-*` codes (`--okf` mode). The rest are structural — `FRONTMATTER`
(malformed metadata), `BROKEN-LINK`, `DUP-ID`, `SOURCE` — and each message
names the offending page and field. `registry/catalog.json` carries every
cataloged page with its `id`, `type`, `scope`, `status`, `maturity`,
`review_after`, and `last_verified` — a deterministic, auditable answer to
"what knowledge exists and how fresh is it."

**Checks the contract enforces:**

| Check | Meaning |
|-------|---------|
| `SCOPE` | frontmatter `scope:` must match the path-implied scope (`global/` `domains/` `projects/`) — precedence comes from scope, so scope lies are errors |
| `REVIEW-AFTER` | pages with a past `review_after` date are flagged stale (warning; message shows days overdue) — staleness is detected, not forgotten |
| `SYNC-CONFLICT` | unresolved team-sync conflicts block commit/push |
| `SOURCE-DRIFT` | a captured source's sha256 changed without re-ingest |

---

## The registry

Two files, two jobs — both machine-written, human-readable:

### `registry/catalog.json` — what knowledge exists

Rebuilt by `rebuild-index.py` from actual files (never hand-edited):

```json
{
  "okf_version": "0.2",
  "generated": "2026-09-19",
  "total": 4506,
  "counts": { "claim": 3800, "pattern": 14, "...": 0 },
  "pages": [
    {
      "id": "claim-alpaca-agents-retry-backoff-001",
      "stem": "claim-alpaca-agents-retry-backoff-001",
      "path": "evidence/claims/claim-alpaca-agents-retry-backoff-001.md",
      "type": "claim",
      "title": "...",
      "scope": "project",
      "description": "one-line summary",
      "status": "supported",
      "confidence": "high",
      "last_verified": "2026-09-12"
    }
  ]
}
```

Every entry answers "what knowledge exists and how fresh is it" — the field
CI and dashboards consume. `--json` prints it to stdout for piping.

### `registry/log.md` — the append-only timeline

OKF §9 shape (the OKF bundle standard's log format — see [OKF](./okf)): one `## YYYY-MM-DD` heading per day, `* **<op> | <subject>**`
bullets beneath. Eval scripts, imports, hooks, and promotions **append**; no
tooling rewrites past entries (CONTRIBUTING.md: "never rewrite history — the
log is the history"). It's also the data source for the compiler-eval gate (why model swaps require re-evaluation — see [Model Policy & Evals](./evals)):
`promote`/`mine-promotions` scan it for a PASS eval naming the current
compiler model.

```markdown
## 2026-09-19
* **eval-stability | gemma4:e4b-fixed** — Claim recall: 0.89 (threshold 0.8) — PASS
* **okf-import | team-a** — bundle ext-bundle: 12 concepts (quarantine 1), tiers {...}
```

---

Next: [When the contract fails: troubleshooting](./troubleshooting)
