---
type: index
title: "Machine-Readable Contract"
description: "Lint codes, catalog.json, CI consumption"
created: 2026-09-19
updated: 2026-09-25
---

# Machine-Readable Contract

This page is the contract surface other systems consume: CI, agent harnesses, dashboards. For the human-readable workflows, start at [Core Workflows](./core-workflows).

Everything the fabric validates and catalogs is available in JSON, so CI and
agent harnesses can consume it without parsing prose:

```bash
wf lint --format json            # errors/warnings with code + page + message, ok flag
python3 scripts/cmd/rebuild-index.py # writes registry/catalog.json (catalog with ids, types, scopes, statuses)
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

### `registry/wiki-graph.json` — the wiki's edges (not its prose)

Written by `wf export wiki`. The human wiki is OpenWiki-style paraphrase; its
prose is for people, and `wf query`/`wf context` **skip it** so models never
re-ingest generated narrative (context bloat + drift). The wiki's machine value
is its derived citation graph: topic/project → claim edges with staleness
tiers + claim provenance — emitted as deterministic JSON. A model consumes the
edges and cites a claim for content.

### `registry/catalog.json` — what knowledge exists

Rebuilt by `rebuild-index.py` from actual files (never hand-edited):

```json
{
  "$schema": "wiki-fabric/registry-v1",
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

## Design decisions: one catalog, versioned envelopes

**One catalog, no per-asset sidecars.** The fabric deliberately does *not*
write a JSON manifest next to every asset. `catalog.json` already carries
every retrieval-relevant field a machine consumer needs; per-asset sidecars
would triple Git-diff noise and create a second machine representation of
each page — a second drift target. The invariant that keeps the registry
honest: **it must be deletable and rebuildable from canonical files**
(`rebuild-index.py`). The moment registry data can't be rebuilt, it has
become a hidden source of truth.

**Schema versions are the compatibility boundary.** Machine surfaces carry
their schema in-band: `catalog.json` writes `$schema: wiki-fabric/registry-v1`,
the task manifest writes `wiki-fabric/context-manifest-v1`, and persisted
context receipts write `wiki-fabric/receipt-v1`. Consumers bind to the
version, not to incidental fields. The one-line rule: **Markdown explains,
YAML classifies, JSON executes — and JSON carries its version.**

## Machine surface shapes (v1 contracts)

Harness adapters and CI bind to these field inventories. Each is guarded by a
pytest asserting the shape matches this table, so an accidental removal or
rename fails CI instead of silently breaking a consumer.

### `wf context --format json` → `wiki-fabric/context-manifest-v1`

| Field | Type | Meaning |
|---|---|---|
| `$schema` | string | Always `wiki-fabric/context-manifest-v1` |
| `task` | string | The task text the manifest was compiled for |
| `paths` | string[] | Code-path hints passed via `--paths` |
| `project` | string \| null | Pinned project namespace, if any |
| `compiled` | date | Compile date (YYYY-MM-DD) |
| `integrations` | object | `{graphify: bool, embeddings: bool}` — optional-integration state |
| `selected` | object[] | Delivered artifacts; see item shape below |
| `excluded` | object[] | Withheld artifacts: `stem`, `path`, `reason` |
| `precedence` | string[] | Resolution order: `["project", "domain", "global"]` |

**Selected item shape:** `id`, `stem`, `path`, `type`, `scope`, `reason`,
`priority` (`P1-project` \| `P2-domain` \| `P3-global`), `trust_tier`
(`human-reviewed` \| `machine-confirmed` \| `unverified`) — plus optional
`warning`, `stale_after`, `title`.

### Context receipt → `wiki-fabric/receipt-v1`

The manifest payload **plus**: `receipt_id` (filename must match),
`manifest` (wrapped manifest schema), `fabric_root`, `namespace`
(`projects/<p>` \| `registry`), `revision` (corpus git HEAD sha, `null`
outside a repo). Enforced by lint's `RECEIPT` code.

### `registry/catalog.json` → `wiki-fabric/registry-v1`

`generated` (date-grain for byte-deterministic rebuilds), `total`, `counts`,
`pages[]` (`id`, `stem`, `path`, `type`, `title`, `scope`, optional
`description` + freshness/lifecycle fields). Rebuilt by `rebuild-index.py`;
never hand-edited.

### Compatibility policy

- **Additive within a version:** new fields may appear; existing fields are
  never removed, renamed, or retyped within a `-v1` surface. A pytest guards
  the context-manifest shape against silent removal/rename.
- **Version bump:** any removal, rename, or semantic change bumps the suffix
  (`-v2`) — never mutates `-v1` in place. Consumers parse `$schema` and branch.
- **Ephemeral vs. contractual:** optional fields documented above
  (`warning`, `stale_after`, `title`) are contractual-when-present. Anything
  not in these tables is incidental and may change without notice.

### `--write-receipt`: delivery as an auditable artifact

`wf context --write-receipt` persists the manifest as a **context receipt**
(schema `wiki-fabric/receipt-v1`) — the per-run record of what the fabric
delivered and why. "Provably delivered" stops being a demo claim and becomes
a checkable artifact: eval fixtures, attesters, and CI can assert *after the
fact* that a given task received the required knowledge.

- **Envelope:** the full manifest payload plus `receipt_id`, `manifest`
  (schema of the wrapped manifest), `fabric_root`, `namespace`, and
  `revision` (the corpus's git HEAD sha — receipts record *which* corpus
  revision they compiled against, so an audit can re-run the exact compile;
  `null` when the corpus isn't a git repo).
- **Id is content-derived:** `receipt-<sha256[:12]>` of the manifest payload.
  Same corpus + task + flags ⇒ same id ⇒ re-running overwrites in place —
  receipts never accumulate duplicates, and re-runs are byte-identical.
- **Partitioned by namespace:** pinned project → `projects/<p>/receipts/`;
  otherwise `registry/receipts/`. Receipts travel with their namespace in
  team sync, and no consumer must load "everything" to read one receipt.
- **stdout discipline:** the receipt path goes to **stderr**; stdout remains
  the manifest, byte-identical with or without the flag.
- **Lint (`RECEIPT`):** validates the envelope — `$schema` value, required
  fields (`receipt_id`, `task`, `selected`, `excluded`, `precedence`,
  `namespace`), and filename ↔ `receipt_id` match.
- **Eval:** behavior fixture `be5` re-compiles with `--write-receipt` and
  asserts the persisted receipt proves delivery (schema, id/filename match,
  selected set equals the manifest's, required stems present).

## Keeping the catalog out of context (bloat guardrails)

The catalog is an index over the whole corpus; the task manifest is a
selected subset. Those two surfaces never swap roles:

| Surface | Size | Consumer | Enters a prompt? |
|---|---|---|---|
| `registry/catalog.json` | grows with the corpus (thousands of pages) | CI, dashboards, external tooling | **No — never** |
| `wf context` manifest | bounded by `--max`, `--project`, `--paths` | the agent, before writing code | Yes — the only fabric JSON meant for model-adjacent use |

The fabric's own runtime never reads the catalog: `wf context` compiles from
page frontmatter directly, so catalog size does not affect task-time context.
Guardrails for external consumers:

- **Filter, don't ingest.** Slice the catalog with `jq` (by `type`, `scope`,
  `status`) instead of loading it whole; the `counts` object answers "how much
  knowledge exists" without reading `pages` at all.
- **Descriptions are capped** (140 chars) — the catalog is an index, not prose.
- **The manifest's excluded list is capped** (15 shown, remainder summarized),
  so a large corpus can't bloat task context either.

Same principle, enforced: per-run context receipts are partitioned under the
namespace that produced them (`projects/<p>/receipts/` or
`registry/receipts/`) — machine artifacts stay partitioned so no consumer
must load "everything" to see "anything".

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
