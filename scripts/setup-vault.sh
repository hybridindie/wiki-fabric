#!/usr/bin/env bash
# setup-vault.sh — Create an Obsidian vault that symlinks to wiki-fabric content
#
# Usage: bash scripts/setup-vault.sh [vault_path]
#
# Creates symlinks from the vault to the fabric's human-readable directories.
# Obsidian follows symlinks, so you browse real files without duplication.

set -euo pipefail

FABRIC_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# Default: vault sits beside the fabric (dirname of the fabric root) —
# wherever the fabric lives, the vault is created next to it
VAULT_PATH="${1:-$(dirname "${FABRIC_ROOT}")/vault}"

echo "=== Setting up Obsidian vault ==="
echo "Fabric: ${FABRIC_ROOT}"
echo "Vault:  ${VAULT_PATH}"
echo ""

mkdir -p "${VAULT_PATH}"
cd "${VAULT_PATH}"

# Preserve .obsidian if it exists (Obsidian workspace config)
# Create symlinks for human-readable content
LINKS=(
    "AGENTS.md"
    "README.md"
    "concepts"
    "patterns"
    "anti-patterns"
    "skills"
    "projects"
    "syntheses"
    "registry"
    "evidence/claims"
    "evidence/source-summaries"
    "domains"
)

for link in "${LINKS[@]}"; do
    target="${FABRIC_ROOT}/${link}"
    if [[ -e "${link}" ]]; then
        if [[ -L "${link}" ]]; then
            echo "  Symlink exists: ${link} → $(readlink "${link}")"
        else
            echo "  Warning: ${link} exists as a real file/dir, skipping"
        fi
    else
        if [[ -e "${target}" ]]; then
            ln -s "${target}" "${link}"
            echo "  Linked: ${link} → ${target}"
        else
            echo "  Warning: target not found: ${target}"
        fi
    fi
done

echo ""
echo "Vault ready: ${VAULT_PATH}"
echo "Open in Obsidian: open '${VAULT_PATH}'"
