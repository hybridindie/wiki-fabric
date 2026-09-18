#!/usr/bin/env bash
# apply-changeset.sh — Apply a change-set to the wiki fabric
#
# Usage: bash scripts/apply-changeset.sh <change-set-slug>
#        bash scripts/apply-changeset.sh --dry-run <change-set-slug>
#
# Reads the change-set manifest and diff, applies changes to canonical pages,
# updates registry/catalog.json and registry/log.md, runs lint, and optionally commits.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VAULT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

DRY_RUN=false
CHANGESET_SLUG=""

# Parse args
while [[ $# -gt 0 ]]; do
    case $1 in
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [--dry-run] <change-set-slug>"
            echo "  Applies a change-set from evidence/traces/change-sets/<slug>/"
            exit 0
            ;;
        *)
            CHANGESET_SLUG="$1"
            shift
            ;;
    esac
done

if [[ -z "${CHANGESET_SLUG}" ]]; then
    echo "Error: change-set slug required" >&2
    echo "Usage: $0 [--dry-run] <change-set-slug>" >&2
    exit 1
fi

CHANGESET_DIR="${VAULT_ROOT}/evidence/traces/change-sets/${CHANGESET_SLUG}"
MANIFEST="${CHANGESET_DIR}/manifest.md"
DIFF_FILE="${CHANGESET_DIR}/diff.md"

if [[ ! -d "${CHANGESET_DIR}" ]]; then
    echo "Error: Change-set not found: ${CHANGESET_DIR}" >&2
    exit 1
fi

if [[ ! -f "${MANIFEST}" ]]; then
    echo "Error: Manifest not found: ${MANIFEST}" >&2
    exit 1
fi

echo "=== Applying change-set: ${CHANGESET_SLUG} ==="
echo "Manifest: ${MANIFEST}"
echo "Dry run: ${DRY_RUN}"
echo ""

# Parse manifest for pages created/updated/deleted
CREATED_FILES=()
UPDATED_FILES=()
DELETED_FILES=()

SECTION=""
while IFS= read -r line; do
    # Detect section headers
    if [[ "${line}" == "## Pages created"* ]]; then
        SECTION="created"
        continue
    elif [[ "${line}" == "## Pages updated"* ]]; then
        SECTION="updated"
        continue
    elif [[ "${line}" == "## Pages deleted"* ]]; then
        SECTION="deleted"
        continue
    elif [[ "${line}" == "## "* ]]; then
        SECTION=""
        continue
    fi
    
    # Parse list items: "- \`path/to/file.md\`" or "- \`path\`" or "- \`path\`: description"
    # Also handles format: "- 1 source record: \`evidence/sources/src-test-source\`"
    if [[ -n "${SECTION}" ]] && [[ "${line}" =~ ^\-\ .*\`([^\`]+)\` ]]; then
        file="${BASH_REMATCH[1]}"
        # Remove trailing wildcards and descriptions
        file=$(echo "${file}" | sed 's/\*.*$//' | sed 's/:.*$//' | xargs)
        case "${SECTION}" in
            created) CREATED_FILES+=("${file}") ;;
            updated) UPDATED_FILES+=("${file}") ;;
            deleted) DELETED_FILES+=("${file}") ;;
        esac
    fi
done < "${MANIFEST}"

echo "Pages to create: ${#CREATED_FILES[@]}"
echo "Pages to update: ${#UPDATED_FILES[@]}"
echo "Pages to delete: ${#DELETED_FILES[@]}"
echo ""

# Apply diff if present
if [[ -f "${DIFF_FILE}" ]]; then
    echo "Applying diff..."
    if [[ "${DRY_RUN}" == true ]]; then
        echo "[DRY RUN] Would apply: git apply ${DIFF_FILE}"
    else
        if git apply "${DIFF_FILE}"; then
            echo "Diff applied successfully"
        else
            echo "Error: Failed to apply diff" >&2
            exit 1
        fi
    fi
else
    echo "No diff file found, will create/update files from manifest"
fi

# Create missing files that should exist (from manifest)
for file in "${CREATED_FILES[@]}"; do
    full_path="${VAULT_ROOT}/${file}"
    if [[ ! -f "${full_path}" ]]; then
        if [[ "${DRY_RUN}" == true ]]; then
            echo "[DRY RUN] Would create: ${file}"
        else
            mkdir -p "$(dirname "${full_path}")"
            stem=$(basename "${file}" .md)
            cat > "${full_path}" <<EOF
---
type: stub
title: ${stem}
created: $(date +%Y-%m-%d)
updated: $(date +%Y-%m-%d)
---

# ${file}

*Created by change-set ${CHANGESET_SLUG} — content pending*
EOF
            echo "Created: ${file}"
        fi
    else
        echo "Exists: ${file}"
    fi
done

# Handle updated files (should exist)
if [[ ${#UPDATED_FILES[@]} -gt 0 ]]; then
    for file in "${UPDATED_FILES[@]}"; do
        full_path="${VAULT_ROOT}/${file}"
        if [[ -f "${full_path}" ]]; then
            echo "Updated: ${file}"
        else
            echo "Warning: Updated file not found (will be created): ${file}"
            if [[ "${DRY_RUN}" == true ]]; then
                echo "[DRY RUN] Would create: ${file}"
            else
                mkdir -p "$(dirname "${full_path}")"
                stem=$(basename "${file}" .md)
                cat > "${full_path}" <<EOF
---
type: stub
title: $(basename "${file}" .md)
created: $(date +%Y-%m-%d)
updated: $(date +%Y-%m-%d)
---

# ${file}

*Updated by change-set ${CHANGESET_SLUG} — content pending*
EOF
                echo "Created (was missing): ${file}"
            fi
        fi
    done
fi

# Handle deleted files
if [[ ${#DELETED_FILES[@]} -gt 0 ]]; then
    for file in "${DELETED_FILES[@]}"; do
        full_path="${VAULT_ROOT}/${file}"
        if [[ "${DRY_RUN}" == true ]]; then
            echo "[DRY RUN] Would delete: ${file}"
        else
            if [[ -f "${full_path}" ]]; then
                git rm "${file}"
                echo "Deleted: ${file}"
            else
                echo "Warning: Delete target not found: ${file}"
            fi
        fi
    done
fi

# Update registry/catalog.json (rebuild from scratch)
if [[ "${DRY_RUN}" == false ]]; then
    echo "Rebuilding registry/catalog.json..."
    python3 - <<'PYEOF'
import os, re
from pathlib import Path

vault = Path(".")
pages = []

for p in Path(".").rglob("*.md"):
    rel = p.relative_to(vault)
    parts = rel.parts
    if any(part in {".git", ".obsidian", ".opencode", "__pycache__", "99-Templates", "evaluations/fixtures"} for part in parts):
        continue
    if "raw" in parts:
        continue
    pages.append((str(rel), p.stem))

# Build index
with open("registry/catalog.json", "w") as f:
    f.write("---\ntype: index\ntitle: Vault Index\nupdated: 2026-09-12\n---\n\n# Index\n\nExhaustive catalog. One line per page. Updated on every ingest and lint.\nFormat: \`- [[stem]] — one-line summary\`\n\n")
    
    # Sources
    f.write("## Sources\n")
    for rel, stem in pages:
        if rel.startswith("evidence/sources/") and rel.endswith(".md"):
            f.write(f"- [[{stem}]] — \n")
    
    f.write("\n## Source Summaries\n")
    for rel, stem in pages:
        if rel.startswith("evidence/source-summaries/") and rel.endswith(".md"):
            f.write(f"- [[{stem}]] — \n")
    
    f.write("\n## Claims\n")
    for rel, stem in pages:
        if rel.startswith("evidence/claims/") and rel.endswith(".md"):
            f.write(f"- [[{stem}]] — \n")
    
    f.write("\n## Concepts\n")
    for rel, stem in pages:
        if rel.startswith("02-Human/Concepts/") and rel.endswith(".md"):
            f.write(f"- [[{stem}]] — \n")
    
    f.write("\n## Projects / Experience Events\n")
    for rel, stem in pages:
        if rel.startswith("02-Human/Projects/") and "experience-events" in rel and rel.endswith(".md"):
            f.write(f"- [[{stem}]] — \n")
    
    f.write("\n## Global (patterns / anti-patterns / skills / rules)\n")
    for rel, stem in pages:
        if rel.startswith("02-Human/Patterns/") and rel.endswith(".md"):
            f.write(f"- [[{stem}]] — \n")
        if rel.startswith("02-Human/Anti-Patterns/") and rel.endswith(".md"):
            f.write(f"- [[{stem}]] — \n")
        if rel.startswith("02-Human/Skills/") and rel.endswith(".md"):
            f.write(f"- [[{stem}]] — \n")
    
    f.write("\n## Registry\n")
    f.write("- [[log]] — Append-only operation timeline\n")
    
    f.write("\n## Source Records (catalog)\n")
    for rel, stem in pages:
        if rel.startswith("evidence/sources/") and rel.endswith(".md"):
            f.write(f"- [[{stem}]]\n")
    
    f.write("\n## Change-sets\n")
    for rel, stem in pages:
        if rel.startswith("evidence/traces/change-sets/") and rel.endswith(".md"):
            f.write(f"- [[{stem}]] — \n")

print("Index rebuilt")

PYEOF
fi

# Append to log
if [[ "${DRY_RUN}" == false ]]; then
    DATE=$(date +%Y-%m-%d)
    LOG_ENTRY="## ${DATE}
* **apply | ${CHANGESET_SLUG}**"
    echo "" >> "${VAULT_ROOT}/registry/log.md"
    echo "${LOG_ENTRY}" >> "${VAULT_ROOT}/registry/log.md"
    echo "- Applied change-set: ${CHANGESET_SLUG}" >> "${VAULT_ROOT}/registry/log.md"
    echo "- Files created: ${#CREATED_FILES[@]}, updated: ${#UPDATED_FILES[@]}, deleted: ${#DELETED_FILES[@]}" >> "${VAULT_ROOT}/registry/log.md"
fi

# Run lint
echo ""
echo "Running lint..."
if python3 "${SCRIPT_DIR}/lint.py" .; then
    echo "Lint: OK"
else
    echo "Error: Lint failed" >&2
    if [[ "${DRY_RUN}" == false ]]; then
        exit 1
    fi
fi

# Commit if not dry run
if [[ "${DRY_RUN}" == false ]]; then
    echo ""
    echo "Committing..."
    git add -A
    git commit -q -m "apply: ${CHANGESET_SLUG} (${#CREATED_FILES[@]} created, ${#UPDATED_FILES[@]} updated, ${#DELETED_FILES[@]} deleted)"
    echo "Committed."
fi

echo ""
echo "=== Change-set ${CHANGESET_SLUG} applied successfully ==="