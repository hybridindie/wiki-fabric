---
type: attested-computation
id: ac-fabric-profile-lint
title: "Attested Computation: fabric profile lint (0 errors gate)"
description: "Sanctioned lint: 14-check profile. CI gate; failing lint blocks commit per git policy."
runtime: python
parameters:
  - { name: vault, type: string, required: true }
executor:
  resource: "references/skills/run-profile-lint.md"
  receipt: [errors, warnings, ok]
attester:
  resource: "references/attesters/check-zero-errors.py"
generated: { by: "process:story-okf-04", at: "2026-09-18T00:00:00Z" }
tags: [lint, gate]
created: 2026-09-18
updated: 2026-09-18
---

# Computation

    python3 scripts/cmd/lint.py <vault>

Exit 1 on any error. The `--okf` sibling is the interop floor; this is the ceiling.
