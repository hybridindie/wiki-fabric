---
type: wiki-article
title: "Graph Critical RLS Contract"
domain: [agent-systems]
review_after: 2027-01-19
---

# Graph Critical RLS Contract

12 current claim(s) support this topic.

- The `ingestion_review_queue` table has RLS enabled with a single service-role policy named `graph_ingestion_review_queue_service_all`." [1]
- There are no `authenticated`-role RLS policies on the `ingestion_review_queue` table, so a direct PostgREST call with an end-user JWT is den [2]
- In the graph-critical RLS contract, the media_titles table has RLS disabled, leaving public read/write behavior application-controlled." [3]
- In the graph-critical RLS contract, the media_relations table has RLS enabled with public SELECT access and service-role-only writes." [4]
- In the graph-critical RLS contract, the user_follows table allows public SELECT and authenticated users can only write or delete where auth. [5]
- The graph-critical RLS contract is enforced by a migration, a contract test, and a CI job, with any drift in policy names, commands, or tabl [6]

---

[1] claim-nomokailist-nomokailist-docs-adr-0005-review-queue-authz-model-md-002 — The `ingestion_review_queue` table has RLS enabled with a single service-role po
[2] claim-nomokailist-nomokailist-docs-adr-0005-review-queue-authz-model-md-003 — There are no `authenticated`-role RLS policies on the `ingestion_review_queue` t
[3] claim-nomokailist-nomokailist-docs-security-rls-md-007 — In the graph-critical RLS contract, the media_titles table has RLS disabled, lea
[4] claim-nomokailist-nomokailist-docs-security-rls-md-008 — In the graph-critical RLS contract, the media_relations table has RLS enabled wi
[5] claim-nomokailist-nomokailist-docs-security-rls-md-009 — In the graph-critical RLS contract, the user_follows table allows public SELECT
[6] claim-nomokailist-nomokailist-docs-security-rls-md-010 — The graph-critical RLS contract is enforced by a migration, a contract test, and

_Generated from the evidence fabric on 2026-09-21. Citations link to claims in evidence/claims/._
