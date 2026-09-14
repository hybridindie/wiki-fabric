#!/usr/bin/env bash
# smoke-test.sh — End-to-end checks of the wf CLI in a throwaway fabric.
#
# Usage:
#   bash scripts/smoke-test.sh            # run in a temp copy (safe, no mutation of this repo)
#   SMOKE_IN_PLACE=1 bash scripts/smoke-test.sh   # run against this repo (mutates evidence/, cleans up)
#
# Exits non-zero on first failure. Requires: python3, bash, git.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FABRIC_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
MODE="${SMOKE_MODE:-isolated}"

# Colors
RED='\033[0;31m'; GREEN='\033[0;32m'; NC='\033[0m'
pass() { echo -e "${GREEN}✓${NC} $*"; }
fail() { echo -e "${RED}✗${NC} $*"; exit 1; }

# In isolated mode, copy the harness to a temp dir so tests can't dirty this repo
if [[ "${MODE}" == "isolated" ]]; then
    TMPROOT="$(mktemp -d "${TMPDIR:-/tmp}/wf-smoke.XXXXXX")"
    trap 'rm -rf "${TMPROOT}"' EXIT
    cp -R "${FABRIC_ROOT}/." "${TMPROOT}/fabric/"
    rm -rf "${TMPROOT}/fabric/.git" "${TMPROOT}/fabric/evidence/raw"/* "${TMPROOT}/fabric/.venv"
    FABRIC="${TMPROOT}/fabric"
    echo "Smoke test (isolated): ${FABRIC}"
else
    FABRIC="${FABRIC_ROOT}"
    echo "Smoke test (in-place): ${FABRIC}"
fi
echo ""

cd "${FABRIC}"

# 0. Python runner: prefer fabric venv (created by wf install), fall back to python3
if [[ -x "${FABRIC}/.venv/bin/python" ]]; then
    PY="${FABRIC}/.venv/bin/python"
    pass "fabric venv present: ${PY}"
elif command -v uv &>/dev/null; then
    (cd "${FABRIC}" && uv venv --quiet && uv pip install -q -r requirements.txt --python .venv/bin/python) || true
    [[ -x "${FABRIC}/.venv/bin/python" ]] && PY="${FABRIC}/.venv/bin/python" || PY="python3"
else
    PY="python3"
fi
pass "python runner: ${PY}"

# 1. wf CLI loads and help renders
bash "${FABRIC}/scripts/wiki-fabric.sh" help >/dev/null 2>&1 || fail "wf help"
pass "wf help"

# 2. All Python scripts compile
for py in "${FABRIC}"/scripts/*.py; do
    python3 -m py_compile "${py}" || fail "py_compile $(basename "${py}")"
done
pass "all $(ls "${FABRIC}"/scripts/*.py | wc -l | tr -d ' ') python scripts compile"

# 3. All shell scripts parse
for sh in "${FABRIC}"/scripts/*.sh; do
    bash -n "${sh}" || fail "bash -n $(basename "${sh}")"
done
pass "all $(ls "${FABRIC}"/scripts/*.sh | wc -l | tr -d ' ') shell scripts parse"

# 4. Lint is clean on the harness itself
"${PY}" "${FABRIC}/scripts/lint.py" . >/dev/null 2>&1 || fail "lint (expected 0 errors)"
pass "lint clean"

# 5. Capture fixture source (dry run reports, no writes)
mkdir -p "${FABRIC}/evidence/raw/smoke-project"
cat > "${FABRIC}/evidence/raw/smoke-project/sample.md" <<'MD'
# Sample fixture

The system uses a single writer. Writes serialize; reads pipeline (L4).
MD
pass "fixture created"

# 6. ingest --changed (dry run) reports the fixture
out="$("${PY}" "${FABRIC}/scripts/ingest.py" --changed smoke-project --dry-run 2>&1)"
echo "${out}" | grep -q "sample.md" || fail "ingest --changed (dry run) did not see fixture"
pass "ingest --changed detects fixture"

# 7. ingest --changed ingests, and is idempotent on second run
"${PY}" "${FABRIC}/scripts/ingest.py" --changed smoke-project >/dev/null 2>&1 || fail "ingest --changed run"
[[ -f "evidence/sources/src-smoke-project-sample-md.md" ]] || fail "source record not created"
[[ -f "evidence/source-summaries/sum-smoke-project-sample-md.md" ]] || fail "source summary not created"
pass "ingest creates source record + summary"

out="$("${PY}" "${FABRIC}/scripts/ingest.py" --changed smoke-project 2>&1)"
echo "${out}" | grep -q "nothing to ingest" || fail "ingest --changed not idempotent: ${out}"
pass "ingest --changed idempotent (anti-loop)"

# 8. rebuild-index runs and index is stable (idempotent)
"${PY}" "${FABRIC}/scripts/rebuild-index.py" >/dev/null 2>&1 || fail "rebuild-index"
cp registry/index.md /tmp/wf-idx-1.md 2>/dev/null || cp "${FABRIC}/registry/index.md" /tmp/wf-idx-1.md
"${PY}" "${FABRIC}/scripts/rebuild-index.py" >/dev/null 2>&1
diff <(grep -v 'updated:' /tmp/wf-idx-1.md) <(grep -v 'updated:' registry/index.md) >/dev/null || fail "rebuild-index not idempotent"
pass "rebuild-index idempotent"

# 9. Lint still clean after ingest artifacts
"${PY}" "${FABRIC}/scripts/lint.py" . >/dev/null 2>&1 || fail "lint after ingest"
pass "lint clean after ingest"

# 9b. Lint JSON report is valid + registry/index.json is machine-readable
"${PY}" "${FABRIC}/scripts/lint.py" . --format json | "${PY}" -m json.tool >/dev/null 2>&1 || fail "lint --format json invalid"
pass "lint --format json valid"
"${PY}" -c "import json; d=json.load(open('registry/index.json')); assert 'pages' in d and 'counts' in d" 2>/dev/null || fail "registry/index.json invalid"
pass "registry/index.json valid"

# 10. log.md was appended
grep -q "ingest | smoke-project" registry/log.md || fail "registry/log.md not appended"
pass "registry/log.md appended"

# 11. capture-git local repo path (uses this repo's own git history as source)
out="$("${PY}" "${FABRIC}/scripts/capture-git.py" smoke-project --repo "${FABRIC}" --since 1y --limit 5 --dry-run 2>&1)"
echo "${out}" | grep -qE "captured|Capture summary" || fail "capture-git local dry-run: ${out}"
pass "capture-git local repo path"

# 12. query runs without crashing (0-token retrieval path)
"${PY}" "${FABRIC}/scripts/query.py" "smoke test question" >/dev/null 2>&1 || fail "query run"
pass "query executes"

# 13. mine-promotions dry-run (0 tokens)
"${PY}" "${FABRIC}/scripts/mine-promotions.py" --dry-run >/dev/null 2>&1 || fail "mine-promotions --dry-run"
pass "mine-promotions dry-run"

# 14. context manifest compiles (markdown) and valid JSON output
"${PY}" "${FABRIC}/scripts/context.py" --task "smoke test task" | grep -q "## Precedence" || fail "context markdown manifest"
"${PY}" "${FABRIC}/scripts/context.py" --task "smoke test task" --format json | "${PY}" -m json.tool >/dev/null 2>&1 || fail "context --format json"
pass "context manifest compiles (md + json)"

# 15. behavior evaluation passes (0 tokens, manifest compliance)
"${PY}" "${FABRIC}/scripts/eval-behavior.py" >/dev/null 2>&1 || fail "behavior eval"
pass "behavior eval (4 fixtures)"

# 16. stability eval (deterministic gates only)
"${PY}" "${FABRIC}/scripts/eval-stability.py" --skip-llm >/dev/null 2>&1 || fail "stability eval"
pass "stability gates (G1/G2 determinism)"

echo ""
echo "All smoke tests passed (18 checks)"

if [[ "${MODE}" == "isolated" ]]; then
    echo "(isolated temp fabric removed on exit)"
fi