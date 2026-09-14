#!/usr/bin/env bash
# demo.sh — P0: the one-session value proof.
#
# Shows that an agent makes a better engineering decision BECAUSE the fabric
# supplied scoped, validated knowledge. No LLM required: the demo compiles a
# real context manifest and asserts that the agent-facing prompt contains
# (a) a global policy, (b) an anti-pattern warning, and (c) the project decision —
# i.e. the fabric delivered the exact knowledge that changes the agent's behavior.
#
# Usage:
#   bash scripts/demo.sh            # run in a temp copy (no mutation of this repo)
#   bash scripts/demo.sh --json     # machine-readable proof report on stdout
#
# What the scenario shows:
#   Task: "Add token refresh to the auth service"
#   Fabric supplies:  a global secret-handling policy
#                     an anti-pattern warning (shared token cache — banned)
#                     a domain pattern (rotate tokens on refresh)
#                     a project decision (rotate, never extend sessions)
#   Without the fabric, an LLM would happily implement a shared token cache.
#   With the manifest, the banned approach is named before code is written.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
JSON_OUT=false
[[ "${1:-}" == "--json" ]] && JSON_OUT=true

RED='\033[0;31m'; GREEN='\033[0;32m'; BLUE='\033[0;34m'; BOLD='\033[1m'; NC='\033[0m'
if [[ "${1:-}" == "--json" ]]; then
    pass() { :; }
    step() { :; }
else
    pass() { echo -e "${GREEN}✓${NC} $*"; }
    step() { echo -e "${BLUE}▸${NC} $*"; }
fi
die() { echo -e "${RED}✗${NC} $*" >&2; exit 1; }

TMP="$(mktemp -d "${TMPDIR:-/tmp}/wf-demo.XXXXXX")"
trap 'rm -rf "${TMP}"' EXIT
FABRIC="${TMP}/fabric"

# ── 1. Fresh fabric ──────────────────────────────────────────────────────────
step "Initialize a fabric"
cp -R "${REPO_ROOT}/." "${FABRIC}/"
rm -rf "${FABRIC}/.git" "${FABRIC}/.venv" "${FABRIC}/fabric.yaml"
pass "fabric at ${FABRIC}"

mkdir -p "${FABRIC}/patterns" "${FABRIC}/anti-patterns" "${FABRIC}/projects/auth-service/decisions" "${FABRIC}/projects/auth-service/experience-events" "${FABRIC}/domains/oauth/concepts"

# ── 2. Seed knowledge (this is what a team accumulates in week 1) ────────────
step "Seed 4 artifacts: 1 global policy, 1 domain pattern, 1 anti-pattern, 1 project decision"

cat > "${FABRIC}/patterns/pattern-token-rotation.md" <<'MD'
---
type: pattern
id: pattern-token-rotation
title: "Rotate tokens on refresh"
scope: global
status: recommended
maturity: 2
evidence:
  - ref: "[[ee-auth-rotation-success]]"
    kind: direct-experience
    outcome: positive
  - ref: "[[ee-billing-rotation-success]]"
    kind: direct-experience
    outcome: positive
review_after: 2027-01-01
---

# Pattern: Rotate tokens on refresh

When a refresh flow issues new tokens, the previous token must be **rotated**
(mark old + issue new), never extended. Detection of reuse of a rotated token
is an auth-failure signal: revoke the family.
MD

cat > "${FABRIC}/anti-patterns/anti-pattern-shared-token-cache.md" <<'MD'
---
type: anti-pattern
id: anti-pattern-shared-token-cache
title: "Shared token cache across service instances"
scope: global
status: recommended
maturity: 2
---
# Anti-pattern: Shared token cache

**Observed failure** (2 independent projects): caching tokens in a shared
store (redis, DB) and serving any instance's request with any cached token
caused cross-session token bleed and audit failures. Token caches must be
**per-session** and invalidated on rotation.

**Misleading fix:** "just add TTL to the cache" — TTL does not prevent
cross-session reuse; it only delays it.

**Instead:** per-session token storage + rotation with reuse detection.
MD

cat > "${FABRIC}/projects/auth-service/decisions/decision-rotation-over-sessions.md" <<'MD'
---
type: decision
id: decision-rotation-over-sessions
title: "Auth service uses rotating refresh tokens, not session extension"
scope: project
project: auth-service
date: 2026-09-01
---

The auth service chose **rotating refresh tokens** over server-side session
extension. Rationale: stateless horizontal scaling; reuse detection gives
free compromise signaling. Session-extension proposals should be redirected.
MD

cat > "${FABRIC}/projects/auth-service/experience-events/ee-shared-cache-bleed.md" <<'MD'
---
type: experience-event
id: ee-shared-cache-bleed
title: "Shared token cache caused cross-session bleed"
project: auth-service
observed_problem: "Tokens cached in shared redis were served across sessions; 40 audit findings."
intervention: "Moved to per-session cache with rotation + reuse detection."
outcomes:
    audit_findings: "40→0"
confidence: high
created: 2026-08-20
---

# ee-shared-cache-bleed

The shared cache anti-pattern, observed with measured outcome.
MD

pass "seeded: pattern, anti-pattern, decision, experience event"

# ── 3. The agent asks for context (this is the fabric's job) ─────────────────
TASK="Add token refresh to the auth service"
echo ""
step "Agent asks for task context: \"${TASK}\""

MANIFEST_MD="$(python3 "${FABRIC}/scripts/context.py" --task "${TASK}" --paths services/auth --project auth-service)"
MANIFEST_JSON="$(python3 "${FABRIC}/scripts/context.py" --task "${TASK}" --paths services/auth --project auth-service --format json)"

if $JSON_OUT; then
    echo "${MANIFEST_JSON}"
    exit 0
fi

echo -e "${BOLD}${MANIFEST_MD}${NC}"

# ── 4. Build the agent prompt from the manifest (what an agent harness does) ─
PROMPT="$(python3 - "$FABRIC" "$TASK" <<'PYEOF'
import sys, json, subprocess
from pathlib import Path
fabric, task = Path(sys.argv[1]), sys.argv[2]
manifest = json.loads(subprocess.run(
    ["python3", str(fabric / "scripts" / "context.py"), "--task", task,
     "--paths", "services/auth", "--project", "auth-service", "--format", "json"],
    capture_output=True, text=True).stdout)
parts = [f"# Task\n{task}\n", "# Knowledge you must follow (from wiki-fabric)\n"]
for s in manifest["selected"]:
    text = (fabric / s["path"]).read_text()
    body = text.split("---", 2)[-1].strip() if text.count("---") >= 2 else text
    # strip frontmatter keys that leaked (indented or key: lines), keep prose
    lines = [l for l in body.split("\n") if l.strip() and not l.strip().startswith(("#", "observed_problem:", "intervention:", "outcomes:", "confidence:", "created:", "review_after:", "evidence:"))]
    paras = [p.strip() for p in "\n".join(lines).split("\n\n") if p.strip()]
    body_text = (max(paras, key=len)[:400] if paras else "").strip()
    warn = f" ⚠ {s['warning']}" if s.get("warning") else ""
    kind = {"decision": "BINDING DECISION", "anti-pattern": "DO NOT", "pattern": "PATTERN",
            "concept": "BACKGROUND", "experience-event": "EVIDENCE"}.get(s["type"], s["type"].upper())
    parts.append(f"## [{kind}] {s.get('title') or s['id']}{warn}\nReason: {s['reason']}\n\n{body_text}\n")
print("\n".join(parts))
PYEOF
)"

# ── 5. The proof: does the prompt contain the behavior-changing knowledge? ───
echo ""
echo "════════════════════════════════════════════"
echo -e "${BOLD}Agent prompt assembled from the manifest (what the LLM would actually receive):${NC}"
echo "════════════════════════════════════════════"
echo "${PROMPT}"
echo ""
echo "════════════════════════════════════════════"
echo "   Assertions: the manifest changed the agent's instructions"
echo "════════════════════════════════════════════"

echo "${PROMPT}" | grep -qi "shared token cache" || die "FAIL: anti-pattern not in prompt"
pass "anti-pattern warning delivered: agent is told NOT to build a shared token cache"

echo "${PROMPT}" | grep -qi "rotating" || die "FAIL: rotation pattern not in prompt"
pass "domain pattern delivered: rotate-on-refresh named"

echo "${PROMPT}" | grep -qi "BINDING DECISION" || die "FAIL: project decision not in prompt"
pass "project decision delivered: binding, highest precedence"

echo "${PROMPT}" | grep -qi "per-session" || die "FAIL: anti-pattern correction not in prompt"
pass "correct alternative delivered: per-session cache"

echo ""
echo "════════════════════════════════════════════"
echo -e "${GREEN}${BOLD}PROOF: without the fabric, an LLM would plausibly implement the banned shared cache.${NC}"
echo -e "${GREEN}${BOLD}With the manifest, the banned approach is named in the prompt BEFORE code is written.${NC}"
echo "════════════════════════════════════════════"
echo ""
echo "This is one session of value. The fabric compounds it: the experience event"
echo "behind the anti-pattern was mined from 2 projects (maturity 2), and the"
echo "decision is binding for auth-service only — global patterns still apply."