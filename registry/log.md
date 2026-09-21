---
type: log
title: Log
created: 2026-09-18
updated: 2026-09-18
---

# Log

Append-only timeline. One `## YYYY-MM-DD` heading per day with `* **<op> | <subject>**` entries (OKF §9).

## 2026-09-18
* **okf-import | t1** — bundle ext-bundle: 1 concepts (quarantine 0), tiers {'unverified': 0, 'machine-confirmed': 0, 'human-reviewed': 1}

## 2026-09-18
* **ingest | perf-test-perf-test-a-md**
- Ingested perf-test-a.md (sha256 3087d1a00277...)
- Extracted 4 claims
- Change-set: /Users/johnd/Development/wiki-fabric/evidence/traces/change-sets/2026-09-18-perf-test-perf-test-a-md

## 2026-09-18
* **ingest | perf-test-perf-test-c-md**
- Ingested perf-test-c.md (sha256 01136a52798a...)
- Extracted 4 claims
- Change-set: /Users/johnd/Development/wiki-fabric/evidence/traces/change-sets/2026-09-18-perf-test-perf-test-c-md

## 2026-09-18
* **ingest | perf-test-perf-test-b-md**
- Ingested perf-test-b.md (sha256 b06dc819dbae...)
- Extracted 5 claims
- Change-set: /Users/johnd/Development/wiki-fabric/evidence/traces/change-sets/2026-09-18-perf-test-perf-test-b-md

## 2026-09-18
* **eval | formal golden corpus**
- Total extracted: 24, golden: 9, covered: 8
- Recall: 0.89, Locator rate: 1.00, Quote rate: 0.67
- Overall: FAIL

## 2026-09-18
* **eval | formal golden corpus**
- Total extracted: 23, golden: 9, covered: 8
- Recall: 0.89, Locator rate: 1.00, Quote rate: 0.65
- Overall: FAIL

## 2026-09-18
* **eval | formal golden corpus**
- Total extracted: 37, golden: 9, covered: 7
- Recall: 0.78, Locator rate: 1.00, Quote rate: 0.84
- Overall: FAIL

## 2026-09-18
* **eval | formal golden corpus**
- Total extracted: 43, golden: 9, covered: 8
- Recall: 0.89, Locator rate: 1.00, Quote rate: 0.88
- Overall: FAIL

## 2026-09-18
* **bench | SLM extraction candidates (gemma4:E4B-QAT 6.1GB, spark-x2.5-4b 2.6GB)**

- gemma4:e4b-it-qat: recall 8/9 (0.89) PASS, locator 1.0 PASS, quote rate 0.65 FAIL (<0.9);
  G4 vs deepseek: fuzzy 0.65 (below 0.75 target, above 0.6 floor); G4 vs qwen2.5-7b: fuzzy 0.83 PASS;
  latency 7.6s/fixture (vs 7b: 6.2s — no speed win); G3 self-stability FAIL (0.53 — over-splits between runs)
- spark-x2.5-4b: reasoning model, burns entire token budget on reasoning channel
  (376s for 2 claims) — unusable for extraction at this size
- Verdict: gemma4 E4B is CLOSE but fails two gates (quote rate, G3 stability).
  qwen2.5-coder:7b remains the local fallback (recall PASS, quote 0.88, G4 0.83 vs gemma4).
  The quote-rate failure mode: model paraphrases instead of quoting verbatim —
  prompt-side fix possible (explicit "quote MUST be verbatim substring" reinforcement).

## 2026-09-18
* **eval | formal golden corpus**
- Total extracted: 22, golden: 9, covered: 8
- Recall: 0.89, Locator rate: 1.00, Quote rate: 0.95
- Overall: PASS

## 2026-09-18
* **eval | formal golden corpus**
- Total extracted: 24, golden: 9, covered: 8
- Recall: 0.89, Locator rate: 1.00, Quote rate: 0.96
- Overall: PASS

## 2026-09-18
* **bench | gemma4 E4B with prompt+code fixes — PASSES golden corpus**

- Two fixes landed:
  1. quote-repair in verify_and_fix_locators — deterministic markdown-normalization
     fuzzy-match that rewrites model quotes back to true verbatim source text
     (quote rate 0.65 -> 0.96)
  2. gemma4:e4b-fixed — Modelfile temperature 0.1 + top_k 10 (the stock QAT build
     ships temperature 1, overriding API calls; fixed variant bakes low temp)
- gemma4:e4b-fixed results:
  - golden recall: 8/9 (0.89) PASS
  - locator presence: 1.0 PASS
  - quote rate: 0.96 PASS (was 0.65)
  - G3 self-stability: PASS (with temp 0.1 baked)
  - G4 vs deepseek: fuzzy 0.78 (above 0.75 quality bar, below 0.8 target)
  - G4 vs qwen2.5-7b: fuzzy 0.68 PASS
  - latency: 6.1s/fixture (vs 7.6s for the stock build, vs 6.2s for 7b)
- Verdict: gemma4:e4b-fixed PASSES the golden corpus and G4-vs-qwen2.5 — a viable
  6.1GB local extraction model. The quote-repair fix benefits ALL models.
- The G4-vs-deepseek 0.78-vs-0.8 shortfall is small-model capability variance;
  acceptable for the local tier given the cloud tier handles the precision-critical path.

## 2026-09-19
* **okf-import | t1** — bundle ext-bundle: 1 concepts (quarantine 0), tiers {'unverified': 0, 'machine-confirmed': 0, 'human-reviewed': 1}


## 2026-09-20
* **okf-import | t1** — bundle ext-bundle: 1 concepts (quarantine 0), tiers {'unverified': 0, 'machine-confirmed': 0, 'human-reviewed': 1}

## 2026-09-20
* **okf-import | t1** — bundle ext-bundle: 1 concepts (quarantine 0), tiers {'unverified': 0, 'machine-confirmed': 0, 'human-reviewed': 1}

## 2026-09-20
* **okf-import | t1** — bundle ext-bundle: 1 concepts (quarantine 0), tiers {'unverified': 0, 'machine-confirmed': 0, 'human-reviewed': 1}

## 2026-09-20
* **okf-import | t1** — bundle ext-bundle: 1 concepts (quarantine 0), tiers {'unverified': 0, 'machine-confirmed': 0, 'human-reviewed': 1}

## 2026-09-20
* **okf-import | t1** — bundle ext-bundle: 1 concepts (quarantine 0), tiers {'unverified': 0, 'machine-confirmed': 0, 'human-reviewed': 1}

## 2026-09-20
* **okf-import | t1** — bundle ext-bundle: 1 concepts (quarantine 0), tiers {'unverified': 0, 'machine-confirmed': 0, 'human-reviewed': 1}

## 2026-09-20
* **okf-import | t1** — bundle ext-bundle: 1 concepts (quarantine 0), tiers {'unverified': 0, 'machine-confirmed': 0, 'human-reviewed': 1}

## 2026-09-20
* **okf-import | t1** — bundle ext-bundle: 1 concepts (quarantine 0), tiers {'unverified': 0, 'machine-confirmed': 0, 'human-reviewed': 1}

## 2026-09-20
* **okf-import | t1** — bundle ext-bundle: 1 concepts (quarantine 0), tiers {'unverified': 0, 'machine-confirmed': 0, 'human-reviewed': 1}

## 2026-09-20
* **okf-import | t1** — bundle ext-bundle: 1 concepts (quarantine 0), tiers {'unverified': 0, 'machine-confirmed': 0, 'human-reviewed': 1}

## 2026-09-20
* **okf-import | t1** — bundle ext-bundle: 1 concepts (quarantine 0), tiers {'unverified': 0, 'machine-confirmed': 0, 'human-reviewed': 1}

## 2026-09-20
* **ingest | godot-mcp-git-issue-477-md**
- Ingested issue-477.md (sha256 e89fcce1f3f0...)
- Extracted 12 claims
- Change-set: /Users/johnd/Development/wiki-fabric/evidence/traces/change-sets/2026-09-20-godot-mcp-git-issue-477-md

## 2026-09-20
* **ingest | godot-mcp-git-issue-488-md**
- Ingested issue-488.md (sha256 b646c0a7c7b4...)
- Extracted 9 claims
- Change-set: /Users/johnd/Development/wiki-fabric/evidence/traces/change-sets/2026-09-20-godot-mcp-git-issue-488-md

## 2026-09-20
* **ingest | godot-mcp-git-issue-487-md**
- Ingested issue-487.md (sha256 145810385c55...)
- Extracted 11 claims
- Change-set: /Users/johnd/Development/wiki-fabric/evidence/traces/change-sets/2026-09-20-godot-mcp-git-issue-487-md

## 2026-09-20
* **ingest | godot-mcp-git-issue-485-md**
- Ingested issue-485.md (sha256 64e8123ebacc...)
- Extracted 12 claims
- Change-set: /Users/johnd/Development/wiki-fabric/evidence/traces/change-sets/2026-09-20-godot-mcp-git-issue-485-md

## 2026-09-20
* **ingest | godot-mcp-git-issue-486-md**
- Ingested issue-486.md (sha256 6c57675d4421...)
- Extracted 8 claims
- Change-set: /Users/johnd/Development/wiki-fabric/evidence/traces/change-sets/2026-09-20-godot-mcp-git-issue-486-md

## 2026-09-20
* **ingest | godot-mcp-git-issue-481-md**
- Ingested issue-481.md (sha256 1f8ede7a148c...)
- Extracted 12 claims
- Change-set: /Users/johnd/Development/wiki-fabric/evidence/traces/change-sets/2026-09-20-godot-mcp-git-issue-481-md

## 2026-09-20
* **ingest | godot-mcp-git-issue-490-md**
- Ingested issue-490.md (sha256 5979b631bf2a...)
- Extracted 10 claims
- Change-set: /Users/johnd/Development/wiki-fabric/evidence/traces/change-sets/2026-09-20-godot-mcp-git-issue-490-md

## 2026-09-20
* **ingest | godot-mcp-git-issue-484-md**
- Ingested issue-484.md (sha256 4b1fa9846ed0...)
- Extracted 12 claims
- Change-set: /Users/johnd/Development/wiki-fabric/evidence/traces/change-sets/2026-09-20-godot-mcp-git-issue-484-md

## 2026-09-20
* **ingest | godot-mcp-git-issue-489-md**
- Ingested issue-489.md (sha256 07d6a0f9e08a...)
- Extracted 10 claims
- Change-set: /Users/johnd/Development/wiki-fabric/evidence/traces/change-sets/2026-09-20-godot-mcp-git-issue-489-md

## 2026-09-20
* **ingest | godot-mcp-git-issue-522-md**
- Ingested issue-522.md (sha256 c9349504c710...)
- Extracted 12 claims
- Change-set: /Users/johnd/Development/wiki-fabric/evidence/traces/change-sets/2026-09-20-godot-mcp-git-issue-522-md

## 2026-09-20
* **ingest | godot-mcp-git-issue-521-md**
- Ingested issue-521.md (sha256 0ce6ef162313...)
- Extracted 11 claims
- Change-set: /Users/johnd/Development/wiki-fabric/evidence/traces/change-sets/2026-09-20-godot-mcp-git-issue-521-md

## 2026-09-20
* **ingest | godot-mcp-git-issue-520-md**
- Ingested issue-520.md (sha256 ee2212a87545...)
- Extracted 11 claims
- Change-set: /Users/johnd/Development/wiki-fabric/evidence/traces/change-sets/2026-09-20-godot-mcp-git-issue-520-md

## 2026-09-20
* **ingest | godot-mcp-git-issue-525-md**
- Ingested issue-525.md (sha256 2375cbef7b1f...)
- Extracted 11 claims
- Change-set: /Users/johnd/Development/wiki-fabric/evidence/traces/change-sets/2026-09-20-godot-mcp-git-issue-525-md

## 2026-09-20
* **ingest | godot-mcp-git-issue-523-md**
- Ingested issue-523.md (sha256 56b1c297fe65...)
- Extracted 11 claims
- Change-set: /Users/johnd/Development/wiki-fabric/evidence/traces/change-sets/2026-09-20-godot-mcp-git-issue-523-md

## 2026-09-20
* **ingest | godot-mcp-git-issue-524-md**
- Ingested issue-524.md (sha256 f716c68a40ea...)
- Extracted 12 claims
- Change-set: /Users/johnd/Development/wiki-fabric/evidence/traces/change-sets/2026-09-20-godot-mcp-git-issue-524-md

## 2026-09-20
* **ingest | godot-mcp-git-issue-528-md**
- Ingested issue-528.md (sha256 301c2f73578a...)
- Extracted 12 claims
- Change-set: /Users/johnd/Development/wiki-fabric/evidence/traces/change-sets/2026-09-20-godot-mcp-git-issue-528-md

## 2026-09-20
* **ingest | godot-mcp-git-issue-527-md**
- Ingested issue-527.md (sha256 97650416e800...)
- Extracted 14 claims
- Change-set: /Users/johnd/Development/wiki-fabric/evidence/traces/change-sets/2026-09-20-godot-mcp-git-issue-527-md

## 2026-09-20
* **ingest | godot-mcp-git-issue-526-md**
- Ingested issue-526.md (sha256 1b97f6424018...)
- Extracted 11 claims
- Change-set: /Users/johnd/Development/wiki-fabric/evidence/traces/change-sets/2026-09-20-godot-mcp-git-issue-526-md

## 2026-09-20
* **ingest | godot-mcp-git-issue-529-md**
- Ingested issue-529.md (sha256 08426892aeab...)
- Extracted 12 claims
- Change-set: /Users/johnd/Development/wiki-fabric/evidence/traces/change-sets/2026-09-20-godot-mcp-git-issue-529-md

## 2026-09-20
* **ingest | godot-mcp-git-issue-531-md**
- Ingested issue-531.md (sha256 b21c863245bb...)
- Extracted 12 claims
- Change-set: /Users/johnd/Development/wiki-fabric/evidence/traces/change-sets/2026-09-20-godot-mcp-git-issue-531-md

## 2026-09-20
* **ingest | godot-mcp-git-issue-534-md**
- Ingested issue-534.md (sha256 3407617ef116...)
- Extracted 12 claims
- Change-set: /Users/johnd/Development/wiki-fabric/evidence/traces/change-sets/2026-09-20-godot-mcp-git-issue-534-md

## 2026-09-20
* **ingest | godot-mcp-git-issue-535-md**
- Ingested issue-535.md (sha256 4da5379053d4...)
- Extracted 12 claims
- Change-set: /Users/johnd/Development/wiki-fabric/evidence/traces/change-sets/2026-09-20-godot-mcp-git-issue-535-md

## 2026-09-20
* **ingest | godot-mcp-git-issue-532-md**
- Ingested issue-532.md (sha256 639ff83b3ea1...)
- Extracted 11 claims
- Change-set: /Users/johnd/Development/wiki-fabric/evidence/traces/change-sets/2026-09-20-godot-mcp-git-issue-532-md

## 2026-09-20
* **ingest | godot-mcp-git-issue-533-md**
- Ingested issue-533.md (sha256 e572adf4a245...)
- Extracted 12 claims
- Change-set: /Users/johnd/Development/wiki-fabric/evidence/traces/change-sets/2026-09-20-godot-mcp-git-issue-533-md

## 2026-09-20
* **ingest | godot-mcp-git-issue-530-md**
- Ingested issue-530.md (sha256 d0a9b9391e11...)
- Extracted 11 claims
- Change-set: /Users/johnd/Development/wiki-fabric/evidence/traces/change-sets/2026-09-20-godot-mcp-git-issue-530-md

## 2026-09-20
* **ingest | godot-mcp-git-issue-537-md**
- Ingested issue-537.md (sha256 e69546bc1a01...)
- Extracted 12 claims
- Change-set: /Users/johnd/Development/wiki-fabric/evidence/traces/change-sets/2026-09-20-godot-mcp-git-issue-537-md

## 2026-09-20
* **ingest | godot-mcp-git-issue-538-md**
- Ingested issue-538.md (sha256 92a20f3bc099...)
- Extracted 12 claims
- Change-set: /Users/johnd/Development/wiki-fabric/evidence/traces/change-sets/2026-09-20-godot-mcp-git-issue-538-md

## 2026-09-20
* **ingest | godot-mcp-git-issue-539-md**
- Ingested issue-539.md (sha256 4815aacbc4fa...)
- Extracted 11 claims
- Change-set: /Users/johnd/Development/wiki-fabric/evidence/traces/change-sets/2026-09-20-godot-mcp-git-issue-539-md

## 2026-09-20
* **ingest | godot-mcp-git-issue-540-md**
- Ingested issue-540.md (sha256 38c329c4a45a...)
- Extracted 11 claims
- Change-set: /Users/johnd/Development/wiki-fabric/evidence/traces/change-sets/2026-09-20-godot-mcp-git-issue-540-md

## 2026-09-20
* **ingest | godot-mcp-git-issue-536-md**
- Ingested issue-536.md (sha256 e47d0f3702ab...)
- Extracted 12 claims
- Change-set: /Users/johnd/Development/wiki-fabric/evidence/traces/change-sets/2026-09-20-godot-mcp-git-issue-536-md

## 2026-09-20
* **ingest | godot-mcp-git-pr-499-md**
- Ingested pr-499.md (sha256 c00117b2b504...)
- Extracted 11 claims
- Change-set: /Users/johnd/Development/wiki-fabric/evidence/traces/change-sets/2026-09-20-godot-mcp-git-pr-499-md

## 2026-09-20
* **ingest | godot-mcp-git-pr-497-md**
- Ingested pr-497.md (sha256 de3f1c9c53a2...)
- Extracted 11 claims
- Change-set: /Users/johnd/Development/wiki-fabric/evidence/traces/change-sets/2026-09-20-godot-mcp-git-pr-497-md

## 2026-09-20
* **ingest | godot-mcp-git-pr-501-md**
- Ingested pr-501.md (sha256 4ad20dc40bb5...)
- Extracted 12 claims
- Change-set: /Users/johnd/Development/wiki-fabric/evidence/traces/change-sets/2026-09-20-godot-mcp-git-pr-501-md

## 2026-09-20
* **ingest | godot-mcp-git-pr-500-md**
- Ingested pr-500.md (sha256 db594b39bc19...)
- Extracted 10 claims
- Change-set: /Users/johnd/Development/wiki-fabric/evidence/traces/change-sets/2026-09-20-godot-mcp-git-pr-500-md

## 2026-09-20
* **ingest | godot-mcp-git-pr-502-md**
- Ingested pr-502.md (sha256 7aa80c795472...)
- Extracted 12 claims
- Change-set: /Users/johnd/Development/wiki-fabric/evidence/traces/change-sets/2026-09-20-godot-mcp-git-pr-502-md

## 2026-09-20
* **ingest | godot-mcp-git-pr-504-md**
- Ingested pr-504.md (sha256 68f515025f97...)
- Extracted 12 claims
- Change-set: /Users/johnd/Development/wiki-fabric/evidence/traces/change-sets/2026-09-20-godot-mcp-git-pr-504-md

## 2026-09-20
* **ingest | godot-mcp-git-pr-506-md**
- Ingested pr-506.md (sha256 46ce52e04535...)
- Extracted 9 claims
- Change-set: /Users/johnd/Development/wiki-fabric/evidence/traces/change-sets/2026-09-20-godot-mcp-git-pr-506-md

## 2026-09-20
* **ingest | godot-mcp-git-pr-508-md**
- Ingested pr-508.md (sha256 f0d29e74efa9...)
- Extracted 12 claims
- Change-set: /Users/johnd/Development/wiki-fabric/evidence/traces/change-sets/2026-09-20-godot-mcp-git-pr-508-md

## 2026-09-20
* **ingest | godot-mcp-git-pr-507-md**
- Ingested pr-507.md (sha256 6e0b701e929b...)
- Extracted 12 claims
- Change-set: /Users/johnd/Development/wiki-fabric/evidence/traces/change-sets/2026-09-20-godot-mcp-git-pr-507-md

## 2026-09-20
* **ingest | godot-mcp-git-pr-498-md**
- Ingested pr-498.md (sha256 76e178df14da...)
- Extracted 12 claims
- Change-set: /Users/johnd/Development/wiki-fabric/evidence/traces/change-sets/2026-09-20-godot-mcp-git-pr-498-md

## 2026-09-20
* **ingest | godot-mcp-git-pr-503-md**
- Ingested pr-503.md (sha256 3c9612eae06f...)
- Extracted 12 claims
- Change-set: /Users/johnd/Development/wiki-fabric/evidence/traces/change-sets/2026-09-20-godot-mcp-git-pr-503-md

## 2026-09-20
* **ingest | godot-mcp-git-pr-509-md**
- Ingested pr-509.md (sha256 53606aed48a6...)
- Extracted 12 claims
- Change-set: /Users/johnd/Development/wiki-fabric/evidence/traces/change-sets/2026-09-20-godot-mcp-git-pr-509-md

## 2026-09-20
* **ingest | godot-mcp-git-pr-510-md**
- Ingested pr-510.md (sha256 73688b93a55a...)
- Extracted 12 claims
- Change-set: /Users/johnd/Development/wiki-fabric/evidence/traces/change-sets/2026-09-20-godot-mcp-git-pr-510-md

## 2026-09-20
* **ingest | godot-mcp-git-pr-512-md**
- Ingested pr-512.md (sha256 e5f835ea6cc0...)
- Extracted 11 claims
- Change-set: /Users/johnd/Development/wiki-fabric/evidence/traces/change-sets/2026-09-20-godot-mcp-git-pr-512-md

## 2026-09-20
* **ingest | godot-mcp-git-pr-514-md**
- Ingested pr-514.md (sha256 3a7a0d57fa0f...)
- Extracted 11 claims
- Change-set: /Users/johnd/Development/wiki-fabric/evidence/traces/change-sets/2026-09-20-godot-mcp-git-pr-514-md

## 2026-09-20
* **ingest | godot-mcp-git-pr-513-md**
- Ingested pr-513.md (sha256 1e0ba7eb8284...)
- Extracted 11 claims
- Change-set: /Users/johnd/Development/wiki-fabric/evidence/traces/change-sets/2026-09-20-godot-mcp-git-pr-513-md

## 2026-09-20
* **ingest | godot-mcp-git-pr-505-md**
- Ingested pr-505.md (sha256 f12f7f5369c2...)
- Extracted 12 claims
- Change-set: /Users/johnd/Development/wiki-fabric/evidence/traces/change-sets/2026-09-20-godot-mcp-git-pr-505-md

## 2026-09-20
* **ingest | godot-mcp-git-pr-511-md**
- Ingested pr-511.md (sha256 ab078cda3127...)
- Extracted 12 claims
- Change-set: /Users/johnd/Development/wiki-fabric/evidence/traces/change-sets/2026-09-20-godot-mcp-git-pr-511-md

## 2026-09-20
* **ingest | godot-mcp-git-pr-516-md**
- Ingested pr-516.md (sha256 a98a258a4b2e...)
- Extracted 12 claims
- Change-set: /Users/johnd/Development/wiki-fabric/evidence/traces/change-sets/2026-09-20-godot-mcp-git-pr-516-md

## 2026-09-20
* **ingest | godot-mcp-git-pr-518-md**
- Ingested pr-518.md (sha256 92e55657a6bc...)
- Extracted 10 claims
- Change-set: /Users/johnd/Development/wiki-fabric/evidence/traces/change-sets/2026-09-20-godot-mcp-git-pr-518-md

## 2026-09-20
* **ingest | godot-mcp-git-pr-517-md**
- Ingested pr-517.md (sha256 f30302320deb...)
- Extracted 10 claims
- Change-set: /Users/johnd/Development/wiki-fabric/evidence/traces/change-sets/2026-09-20-godot-mcp-git-pr-517-md

## 2026-09-20
* **ingest | godot-mcp-git-pr-519-md**
- Ingested pr-519.md (sha256 3280f781b308...)
- Extracted 10 claims
- Change-set: /Users/johnd/Development/wiki-fabric/evidence/traces/change-sets/2026-09-20-godot-mcp-git-pr-519-md

## 2026-09-20
* **ingest | godot-mcp-git-pr-515-md**
- Ingested pr-515.md (sha256 c067546ea344...)
- Extracted 12 claims
- Change-set: /Users/johnd/Development/wiki-fabric/evidence/traces/change-sets/2026-09-20-godot-mcp-git-pr-515-md

## 2026-09-20
* **ingest | godot-mcp-git-pr-541-md**
- Ingested pr-541.md (sha256 d53f4acfb173...)
- Extracted 12 claims
- Change-set: /Users/johnd/Development/wiki-fabric/evidence/traces/change-sets/2026-09-20-godot-mcp-git-pr-541-md

## 2026-09-20
* **ingest | godot-mcp-git-pr-543-md**
- Ingested pr-543.md (sha256 44de873ac5c6...)
- Extracted 12 claims
- Change-set: /Users/johnd/Development/wiki-fabric/evidence/traces/change-sets/2026-09-20-godot-mcp-git-pr-543-md

## 2026-09-20
* **ingest | godot-mcp-git-pr-542-md**
- Ingested pr-542.md (sha256 6c35a9676953...)
- Extracted 13 claims
- Change-set: /Users/johnd/Development/wiki-fabric/evidence/traces/change-sets/2026-09-20-godot-mcp-git-pr-542-md

## 2026-09-20
* **ingest | godot-mcp-git-pr-544-md**
- Ingested pr-544.md (sha256 955e5a00264f...)
- Extracted 12 claims
- Change-set: /Users/johnd/Development/wiki-fabric/evidence/traces/change-sets/2026-09-20-godot-mcp-git-pr-544-md

## 2026-09-20
* **ingest | godot-mcp-git-pr-545-md**
- Ingested pr-545.md (sha256 b80502697f39...)
- Extracted 12 claims
- Change-set: /Users/johnd/Development/wiki-fabric/evidence/traces/change-sets/2026-09-20-godot-mcp-git-pr-545-md

## 2026-09-20
* **ingest | godot-mcp-git-pr-546-md**
- Ingested pr-546.md (sha256 c6ccc9c23349...)
- Extracted 12 claims
- Change-set: /Users/johnd/Development/wiki-fabric/evidence/traces/change-sets/2026-09-20-godot-mcp-git-pr-546-md

## 2026-09-20
* **ingest | godot-mcp-git-pr-547-md**
- Ingested pr-547.md (sha256 91a9e00a09f6...)
- Extracted 12 claims
- Change-set: /Users/johnd/Development/wiki-fabric/evidence/traces/change-sets/2026-09-20-godot-mcp-git-pr-547-md

## 2026-09-20
* **okf-import | t1** — bundle ext-bundle: 1 concepts (quarantine 0), tiers {'unverified': 0, 'machine-confirmed': 0, 'human-reviewed': 1}

## 2026-09-20
* **okf-import | t1** — bundle ext-bundle: 1 concepts (quarantine 0), tiers {'unverified': 0, 'machine-confirmed': 0, 'human-reviewed': 1}

## 2026-09-20
* **okf-import | t1** — bundle ext-bundle: 1 concepts (quarantine 0), tiers {'unverified': 0, 'machine-confirmed': 0, 'human-reviewed': 1}

## 2026-09-20
* **okf-import | t1** — bundle ext-bundle: 1 concepts (quarantine 0), tiers {'unverified': 0, 'machine-confirmed': 0, 'human-reviewed': 1}

## 2026-09-20
* **ingest | godot-mcp-chats-2026-09-16-chat-graphify-has-hooks-for-harnesses-like-claude-let**
- Ingested 2026-09-16-chat-graphify-has-hooks-for-harnesses-like-claude-let-s-recreate-.md (sha256 fb2f1d90f4b9...)
- Extracted 12 claims
- Change-set: /Users/johnd/Development/wiki-fabric/evidence/traces/change-sets/2026-09-20-godot-mcp-chats-2026-09-16-chat-graphify-has-hooks-for-harnesses-like-claude-let

## 2026-09-20
* **ingest | godot-mcp-chats-2026-09-08-chat-let-s-address-the-open-prs-on-this-repo-there-is**
- Ingested 2026-09-08-chat-let-s-address-the-open-prs-on-this-repo-there-is-ci-failures.md (sha256 5559bcbf3e89...)
- Extracted 12 claims
- Change-set: /Users/johnd/Development/wiki-fabric/evidence/traces/change-sets/2026-09-20-godot-mcp-chats-2026-09-08-chat-let-s-address-the-open-prs-on-this-repo-there-is

## 2026-09-20
* **ingest | godot-mcp-chats-2026-09-08-chat-read-the-file-users-johnd-local-share-opencode-t**
- Ingested 2026-09-08-chat-read-the-file-users-johnd-local-share-opencode-tool-output-t.md (sha256 c393dc2502f8...)
- Extracted 12 claims
- Change-set: /Users/johnd/Development/wiki-fabric/evidence/traces/change-sets/2026-09-20-godot-mcp-chats-2026-09-08-chat-read-the-file-users-johnd-local-share-opencode-t

## 2026-09-20
* **okf-import | t1** — bundle ext-bundle: 1 concepts (quarantine 0), tiers {'unverified': 0, 'machine-confirmed': 0, 'human-reviewed': 1}

## 2026-09-20
* **okf-import | t1** — bundle ext-bundle: 1 concepts (quarantine 0), tiers {'unverified': 0, 'machine-confirmed': 0, 'human-reviewed': 1}

## 2026-09-20
* **okf-import | t1** — bundle ext-bundle: 1 concepts (quarantine 0), tiers {'unverified': 0, 'machine-confirmed': 0, 'human-reviewed': 1}
