#!/usr/bin/env bash
# wheel-smoke.sh — Build the wheel, install in a throwaway venv, exercise the
# packaged wf against a fresh fabric. Catches _harness-staging breakage
# (missing packaged assets, broken packaged-mode resolution) BEFORE a tag
# publishes a broken release.
#
# Usage:
#   bash scripts/pkg/wheel-smoke.sh           # build + install + verify
#   WHEEL_SMOKE_SKIP_BUILD=1 bash ...         # reuse dist/ wheels (CI: build job)
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
RED='\033[0;31m'; GREEN='\033[0;32m'; NC='\033[0m'
pass() { echo -e "${GREEN}✓${NC} $*"; }
fail() { echo -e "${RED}✗${NC} $*"; exit 1; }

cd "$REPO"

WORK="$(mktemp -d "${TMPDIR:-/tmp}/wf-wheel-smoke.XXXXXX")"
# WHEEL_SMOKE_KEEP=1 leaves the workdir for post-mortem inspection.
if [[ "${WHEEL_SMOKE_KEEP:-0}" == "1" ]]; then
    trap 'echo "kept: ${WORK}"' EXIT
else
    trap 'rm -rf "${WORK}"' EXIT
fi

if [[ "${WHEEL_SMOKE_SKIP_BUILD:-0}" != "1" ]]; then
    echo "── prep + build"
    # self-sufficiency: CI legs don't preinstall `build` (publish.yml does)
    # Pick an interpreter that has `build` (CI legs run the smoke inside the
    # uv-managed .venv; publish.yml preinstalls into system python) — else
    # install minimally via uv into a scratch target.
    # Provision `build` into a KNOWN interpreter (uv-first). Old distros
    # carry a `build` without __main__ — verify by running its CLI, not by
    # importing the package (the check above that fooled CI twice).
    PY=".venv/bin/python"
    [[ -x "${PY}" ]] || PY="${VIRTUAL_ENV:-}/bin/python"
    [[ -x "${PY}" ]] || PY="python3"
    "${PY}" -m build --version >/dev/null 2>&1 || {
        command -v uv >/dev/null 2>&1 && { uv pip install -q -U build pyyaml openai anthropic --python "${PY}"; }
        "${PY}" -m build --version >/dev/null 2>&1 || fail "cannot provision `build` (tried uv)"
    }
    echo "using interpreter: ${PY}"
    "${PY}" scripts/pkg/prep-package.py
    "${PY}" -m build --outdir "${WORK}/dist" || fail "python -m build failed"
else
    echo "── reuse dist/ wheels (skip build)"
    mkdir -p "${WORK}/dist_w"
    cp dist/*.whl "${WORK}/dist_w/" || fail "no wheels in dist/"
fi
WHEEL="$(ls -t "${WORK}"/dist/*.whl "${WORK}"/dist_w/*.whl 2>/dev/null | head -1 || true)"
[[ -z "${WHEEL}" ]] && WHEEL="$(ls -t "${WORK}"/dist/*.whl | head -1 || true)"
[[ -n "${WHEEL}" ]] || fail "no wheel found"
pass "wheel built: $(basename "${WHEEL}")"

echo "── install into clean venv"
python3 -m venv "${WORK}/venv" || fail "venv create failed"
"${WORK}/venv/bin/pip" install --quiet --no-input "${WHEEL}" || fail "wheel install failed"
pass "installed"

WF="${WORK}/venv/bin/wf"
[[ -x "${WF}" ]] || fail "wf entrypoint missing from wheel"
echo "── venv python: $("${WORK}/venv/bin/python" -c 'import sys; print(sys.version.split()[0])')"

echo "── packaged-mode sanity"
"${WORK}/venv/bin/python" -c "
from pathlib import Path
import wiki_fabric
h = wiki_fabric.package_root()
assert (h / 'scripts' / 'wiki-fabric.sh').is_file(), f'no harness scripts at {h}'
assert (h / 'scripts' / 'cmd').is_dir(), 'no scripts/cmd'
for top in ('system', 'templates', 'schemas', 'references', 'evaluations'):
    assert (h / top).is_dir(), f'missing shipped tree: {top} at {h}'
import os
os.environ.get('WF_PACKAGED')  # touch for existence; __init__ sets it at import
assert os.environ.get('WF_PACKAGED') == '1', 'WF_PACKAGED not set in wheel install'
print('harness root:', h)
" || fail "packaged _harness tree incomplete"
pass "_harness trees present (scripts/system/templates/schemas/references/evaluations)"

"${WF}" version || fail "wf version failed"
"${WF}" --help >/dev/null || fail "wf --help failed"

echo "── fresh-fabric lifecycle (install → status → lint)"
# `wf install` short-circuits when find_fabric() already resolves, so resolve
# must be clean: run from an empty cwd with no WIKI_FABRIC_DIR, using --dir.
RUNDIR="${WORK}/rundir"
mkdir -p "${RUNDIR}"
(
    cd "${RUNDIR}"
    unset WIKI_FABRIC_DIR
    "${WF}" install --dir "${RUNDIR}/fabric" >/dev/null || exit 99
)
[[ -f "${RUNDIR}/fabric/fabric.yaml" ]] || fail "fabric.yaml not created by install"
export WIKI_FABRIC_DIR="${RUNDIR}/fabric"

"${WF}" status >/dev/null || fail "wf status failed on fresh fabric"
"${WF}" lint >/dev/null 2>&1 || true   # fresh fabric: warn-level OK, must not crash
pass "init + status + lint on fresh fabric"

# config template shape: packaged skeleton must render the canonical config
grep -q "llm:" "${WIKI_FABRIC_DIR}/fabric.yaml" || fail "fabric.yaml missing llm config"
grep -q "owner:" "${WIKI_FABRIC_DIR}/fabric.yaml" || fail "fabric.yaml missing owner"

echo "── no fabric-content leakage"
if [[ -e "${REPO}/src/wiki_fabric/_harness/global/entities" ]] && [[ -n "$(ls "${REPO}/src/wiki_fabric/_harness/global/entities" 2>/dev/null)" ]]; then
    fail "personal fabric entities leaked into wheel staging"
fi
if [[ -n "${WHEEL}" ]]; then
    python3 - "${WHEEL}" <<'PY' || fail "leak check failed"
import sys, zipfile
leaks = []
with zipfile.ZipFile(sys.argv[1]) as z:
    for n in z.namelist():
        parts = n.split("/")
        # packaged global/ must only be computations (+attesters refs); entities/graphs = content
        if "_harness/global/" in n and ("entities/" in n or "graphs/" in n):
            leaks.append(n)
        if n.endswith("_harness/evidence") or "/_harness/evidence/" in n:
            leaks.append(n)
assert not leaks, f"fabric content leaked into wheel: {leaks[:5]}"
print("no fabric-content leaks in wheel")
PY
fi

echo "── registry import shape (anti-drift contract)"
"${WORK}/venv/bin/python" "${REPO}/scripts/pkg/_smoke_import_shape.py" "${REPO}" \
    || fail "packaged shared-lib imports broken"

pass "wheel smoke complete"