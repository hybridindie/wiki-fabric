---
type: wiki-article
title: "Graph Critical RLS Contract"
domain: [agent-systems]
review_after: 2027-01-19
---

# Graph Critical RLS Contract

12 current claim(s) support this topic.

- The ingestion_review_queue table has RLS enabled with a single service-role policy named graph_ingestion_review_queue_service_all." [1]
- There are no authenticated-role policies on the review queue, so a direct PostgREST call with an end-user JWT is denied." [2]
- Service-Only Access pattern has no user policies and all access is via service role only." [3]
- The Graph-Critical RLS Contract is enforced by migration and CI contract tests." [4]
- Any drift in policy names, commands, or table RLS state is treated as a failure." [5]
- media_titles has RLS disabled and no contracted policies, with public read/write behavior remaining application-controlled." [6]

---

[1] claim-nomokailist-nomokailist-docs-adr-0005-review-queue-authz-model-md-002 — The ingestion_review_queue table has RLS enabled with a single service-role poli
[2] claim-nomokailist-nomokailist-docs-adr-0005-review-queue-authz-model-md-003 — There are no authenticated-role policies on the review queue, so a direct PostgR
[3] claim-nomokailist-nomokailist-docs-security-rls-md-007 — Service-Only Access pattern has no user policies and all access is via service r
[4] claim-nomokailist-nomokailist-docs-security-rls-md-008 — The Graph-Critical RLS Contract is enforced by migration and CI contract tests."
[5] claim-nomokailist-nomokailist-docs-security-rls-md-009 — Any drift in policy names, commands, or table RLS state is treated as a failure.
[6] claim-nomokailist-nomokailist-docs-security-rls-md-010 — media_titles has RLS disabled and no contracted policies, with public read/write

_Generated from the evidence fabric on 2026-09-21. Citations link to claims in evidence/claims/._
