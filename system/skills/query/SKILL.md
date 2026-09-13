---
name: query
description: Answer questions from the compiled wiki using the structured query protocol — bottom line, evidence with locators, caveats, confidence, next action.
---

# Query Skill

Answers questions from the compiled evidence fabric using the structured query protocol from AGENTS.md.

## When to Use

User asks a question about the knowledge base: "What does X say about Y?" "Compare X and Y" "Why did we decide Z?"

## Procedure

1. **Classify query type** (per AGENTS.md retrieval policy):
   - Exact repo/API question → lexical: `registry/index.md` → source record → raw
   - "What did we decide?" → `projects/*/decisions/` + recency-weighted synthesis
   - Cross-source synthesis → claims → graph expansion via `relations` → linked sources
   - Claim verification → claim registry + explicit locators only
   - Comparison → experiment index filtered by environment/metrics
   - "What to investigate next?" → `questions/` + unresolved `contradicts` relations

2. **Retrieve**: Read `registry/index.md`, then relevant MoC/concept pages, then claims, then source records. Record which pages were selected and why (explainability).

3. **Answer in structured format**:
```markdown
    ## Bottom line
    ...
 
    ## Evidence
    - [[claim-example-1...]] — supported by [[src-...]], §...
    - [[claim-example-2...]] — contested by [[src-...]], p. ...
 
    ## Caveats and conditions
    ...
 
    ## Confidence
    Medium — three primary sources agree, but no result replicated under target config.
 
    ## Suggested next action
    Run [[experiment-example...]] or ingest ...
    ```

4. **File synthesis if valuable**: If answer contains reusable synthesis, propose filing as `domains/<domain>/syntheses/syn-<slug>.md` (type: synthesis) with claims cited.

## Retrieval Policy

| Query type | Retrieval |
|---|---|
| Exact project/repo/API | Lexical: index → source record → raw |
| "What did we decide?" | Decisions + recency-weighted synthesis |
| Cross-source synthesis | Claims → graph expansion via `relations` → sources |
| Claim verification | Claim registry + explicit locators only |
| Comparison (A vs B) | Experiment index filtered by environment/metrics |
| "What to investigate next?" | `questions/` + unresolved `contradicts` |

## Explainability

Record which pages were selected, why, and what was excluded — file alongside high-value answers.

## Output

- Structured answer per format above
- Optional: new synthesis page proposal
- Updated `registry/log.md` append if synthesis filed