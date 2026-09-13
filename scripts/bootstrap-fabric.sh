#!/usr/bin/env bash
# bootstrap-fabric.sh — One-time global Wiki Fabric installation
#
# Usage: bash bootstrap-fabric.sh [--install-dir DIR]
#
# Installs the global Wiki Fabric to ~/wiki-fabric (or custom dir).
# Run ONCE per machine/user. Projects then connect via .wiki-overlay.md.

set -euo pipefail

INSTALL_DIR="${HOME}/wiki-fabric"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Parse args
while [[ $# -gt 0 ]]; do
    case $1 in
        --install-dir)
            INSTALL_DIR="$2"
            shift 2
            ;;
        -h|--help)
            echo "Usage: $0 [--install-dir DIR]"
            echo "  Installs global Wiki Fabric to DIR (default: ~/wiki-fabric)"
            exit 0
            ;;
        *)
            echo "Unknown option: $1" >&2
            exit 1
            ;;
    esac
done

echo "=== Wiki Fabric Global Install ==="
echo "Install directory: ${INSTALL_DIR}"
echo "Source: ${SCRIPT_DIR}"
echo ""

# Check if already installed
if [[ -d "${INSTALL_DIR}/.git" ]]; then
    echo "⚠️  Wiki Fabric already installed at ${INSTALL_DIR}"
    read -p "Reinstall? This will overwrite. [y/N] " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Aborted."
        exit 0
    fi
    rm -rf "${INSTALL_DIR}"
fi

# Create install directory
mkdir -p "${INSTALL_DIR}"

# Copy fabric (exclude .git, raw evidence, node_modules, etc.)
echo "Copying fabric to ${INSTALL_DIR}..."
rsync -av \
    --exclude='.git' \
    --exclude='evidence/raw/' \
    --exclude='node_modules/' \
    --exclude='.obsidian/' \
    --exclude='.DS_Store' \
    --exclude='*.pyc' \
    --exclude='__pycache__/' \
    "${SCRIPT_DIR}/" "${INSTALL_DIR}/"

# Create evidence/raw directory structure (empty, for captures)
mkdir -p "${INSTALL_DIR}/evidence/raw"

# Initialize git repo if not already
cd "${INSTALL_DIR}"
if [[ ! -d .git ]]; then
    git init -q
    git add -A
    git commit -q -m "chore: initial global fabric install"
    echo "Initialized git repository"
fi

# Create empty evidence directories
mkdir -p evidence/sources evidence/source-summaries evidence/claims
mkdir -p evidence/experiments evidence/traces/change-sets evidence/_inbox
mkdir -p evidence/raw

# Create empty project directories structure
mkdir -p projects global/patterns global/anti-patterns global/skills
mkdir -p global/playbooks global/decision-rules global/entities global/ontologies
mkdir -p global/templates domains/agent-systems/concepts domains/agent-systems/questions
mkdir -p domains/agent-systems/syntheses

mkdir -p registry/promotions

# Create empty registry files if they don't exist
[[ -f registry/index.md ]] || cat > registry/index.md <<'EOF'
---
type: index
title: Vault Index
updated: $(date +%Y-%m-%d)
---

# Index

Exhaustive catalog. One line per page. Updated on every ingest and lint.
Format: `- [[stem]] — one-line summary`

## Sources
_(none yet)_

## Source Summaries
_(none yet)_

## Claims
_(none yet)_

## Concepts
_(none yet)_

## Projects / Experience Events
_(none yet)_

## Global (patterns / anti-patterns / skills / rules)
_(none yet)_

## Registry
- [[log]] — Append-only operation timeline

## Source Records (catalog)
_(none yet)_

## Change-sets
_(none yet)_
EOF

[[ -f registry/log.md ]] || cat > registry/log.md <<'EOF'
---
type: log
title: Log
created: $(date +%Y-%m-%d)
updated: $(date +%Y-%m-%d)
---

# Log

Append-only timeline. One `## [YYYY-MM-DD] <op> | <subject>` entry per operation.

## [$(date +%Y-%m-%d)] init | Global fabric installed

- Wiki Fabric installed at $(pwd)
- Ready for project connections via .wiki-overlay.md
EOF

[[ -f registry/pattern-index.md ]] || cat > registry/pattern-index.md <<'EOF'
---
type: registry
title: Pattern Index
updated: $(date +%Y-%m-%d)
---

# Pattern Index

| Pattern | Maturity | Domains | Applicability |
|---|---|---|---|
| _(none yet)_ | _ | _ | _ |

Anti-patterns → _(none yet)_
EOF

[[ -f registry/rule-index.md ]] || cat > registry/rule-index.md <<'EOF'
---
type: registry
title: Rule Index
updated: $(date +%Y-%m-%d)
---

# Rule Index

Rules (narrow, enforceable invariants). None promoted yet; candidates in [[promotion-queue]].
EOF

[[ -f registry/skill-index.md ]] || cat > registry/skill-index.md <<'EOF'
---
type: registry
title: Skill Index
updated: $(date +%Y-%m-%d)
---

# Skill Index

Reusable agent procedures. None promoted yet; `global/skills/` is empty.
When a pattern reaches maturity 3, package it as a `skill` + `template` here.
EOF

[[ -f registry/promotion-queue.md ]] || cat > registry/promotion-queue.md <<'EOF'
---
type: registry
title: Promotion Queue
updated: $(date +%Y-%m-%d)
---

# Promotion Queue

Candidates awaiting human promotion. **No auto-promotion** — only the user sets
`status: recommended`/`standard` on pattern pages.

| Pattern | Maturity | Evidence lineage | Dossier |
|---|---|---|---|
| _(none yet)_ | _ | _ | _ |

## Review checklist (per dossier)

1. Independence: do the supporting experience-events share a lineage? (No → OK.)
2. Evidence: are claims in `source_refs` actually entailed by cited locators?
3. Applicability: are `includes`/`excludes` conditions correct and non-vacuous?
4. Counterexamples: listed and acknowledged?
5. Tradeoff: cost/benefit stated?
6. Asset changes: which `global/` entries does promotion create/update?
7. Owner: user — user. Promote only when all pass.
EOF

# Create empty evidence directories
mkdir -p evidence/sources evidence/source-summaries evidence/claims
mkdir -p evidence/experiments evidence/traces/change-sets evidence/_inbox

# Create empty project directories
mkdir -p projects

# Create empty global directories
mkdir -p global/patterns global/anti-patterns global/skills
mkdir -p global/playbooks global/decision-rules global/entities global/ontologies
mkdir -p global/templates

# Create empty domain directories
mkdir -p domains/agent-systems/concepts domains/agent-systems/questions domains/agent-systems/syntheses

# Create empty registry subdirs
mkdir -p registry/promotions

# Create empty evidence directories
mkdir -p evidence/sources evidence/source-summaries evidence/claims
mkdir -p evidence/experiments evidence/traces/change-sets evidence/_inbox

# Create empty project directories
mkdir -p projects

# Create .gitkeep files for empty directories
find . -type d -empty -exec touch {}/.gitkeep \;

echo ""
echo "✅ Global Wiki Fabric installed at ${INSTALL_DIR}"
echo ""
echo "Next steps:"
echo "  1. In each project, copy the overlay template:"
echo "     cp ${INSTALL_DIR}/.wiki-overlay.md.template .wiki-overlay.md"
echo "  2. Edit .wiki-overlay.md with your project config"
echo "  3. Add to project's opencode.json:"
echo '     { "references": { "wiki-fabric": { "path": "'${INSTALL_DIR}'", "description": "Global knowledge fabric" } }, "instructions": ["'${INSTALL_DIR}'/AGENTS.md", ".wiki-overlay.md"] }'
echo ""
echo "Then in the project, run opencode and the agent will load global fabric + overlay."
echo ""
echo "To capture sources from upstream repos:"
echo "  python3 ${INSTALL_DIR}/scripts/lint.py --hash evidence/raw/<repo>/<file>.md  # get hash"
echo "  # Then run ingest skill: 'ingest evidence/raw/<repo>/<file>.md'"
echo ""
echo "To run lint: python3 ${INSTALL_DIR}/scripts/lint.py ."
echo ""
echo "✅ Global Wiki Fabric installed at ${INSTALL_DIR}"