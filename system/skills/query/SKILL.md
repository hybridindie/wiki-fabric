---
name: query
description: Answer questions via `wf query` — deterministic retrieval (0 tokens) + structured answer protocol (bottom line, evidence with locators, caveats, confidence, next action). Never call the LLM to search the fabric.
---

# Query Skill

Answers questions from the compiled evidence fabric. CLI-first: `wf query` (or
`python3 scripts/query.py`) does retrieval deterministically — concept-overlap
scoring, graph expansion, recency weighting — at **0 LLM tokens**. The LLM is
only invoked to synthesize a *new* answer for a consequential question.

## When to Use

- User asks about the knowledge base: "What does X say about Y?", "Compare X and Y", "Why did we decide Z?"
- Mid-session, the agent itself needs project facts (factual lookup, decisions, verification)
- NEVER use the LLM to search: retrieval is `wf query`'s job, synthesis is the LLM's

## CLI Commands

```bash
# Ask anything (0 tokens retrieval, structured answer)
wf query "Why does my code batch writes but pipeline reads?"

# Save a reusable answer as a synthesis page
wf query "What patterns apply to batch-write systems?" --save

# Force a query type (auto-detected by default)
wf query "What did we decide about the bridge?" --type decision

# Show scoring detail (which pages matched, why)
wf query "cache invalidation strategy" --verbose
```

**If graphify is ACTIVE** (`fabric.yaml` → `integrations.graphify.enabled: true`),
graph expansion additionally follows code call/import edges from
`global/graphs/` — query results include code-reachable claims that lexical
matching misses. When graphify is inactive, expansion uses only claim
`relations` (frontmatter), and code-symbol questions should be answered from
the entity index (`build-entity-index.py`) instead.

## Query Types (route by type)

| Type | Boosts | Use when |
|---|---|---|
| `auto` (default) | — | Let the router decide |
| `decision` | decisions + experience events | "What did we decide?" |
| `verify` | claims + locators | Claim verification, factual lookup |
| `compare` | experiments + metrics | A vs B comparisons |
| `gap` | questions + contradictions | "What should we investigate next?" |
| `concept` | concepts + patterns | "How does X work?" |

## Procedure

1. **Run the CLI**: `wf query "<question>" [--type <t>]`. This scores pages
   (concept overlap + type boost + recency), expands via claim `relations` and
   graph edges, and returns the most relevant claims/concepts/sources.
2. **Follow locators**: read the cited sources at the cited locators before
   asserting anything beyond the returned snippets.
3. **Answer in the structured format** (below). Cite every claim with its
   `[[claim-...]]` link and the underlying `[[src-...]]` + locator.
4. **File synthesis if reusable**: if the answer generalizes, save with
   `--save` (writes `syntheses/syn-<slug>.md`, type: synthesis) or file it
   manually in `syntheses/`.

## Answer Format

```markdown
## Bottom line
...

## Evidence
- [[claim-example-1]] — supported by [[src-...]], L42-45
- [[claim-example-2]] — contested by [[src-...]], PR #342

## Caveats and conditions
...

## Confidence
Medium — three primary sources agree, but no replication on target config.

## Suggested next action
Run [[experiment-...]] or ingest ...
```

## Explainability

Record which pages were selected, why, and what was excluded — file alongside
high-value saved syntheses.

## Anti-patterns to Avoid

- Calling the LLM to answer something `wf query` can answer lexically (wasted tokens, unauditable)
- Asserting claims without opening their locators
- Collapsing a contested claim into one side; surface the conflict with both locators
- Answering from memory when the fabric has a `status: contested` claim on the topic

## Output

- Structured answer per format above
- Optional: `--save` writes a synthesis page and updates the index