#!/usr/bin/env bash
# setup-vault.sh — Create an Obsidian vault as the utility's OUTPUT directory.
#
# Usage: bash scripts/setup-vault.sh [vault_path]
#
# The vault is the RESULT of wiki-fabric, never a mirror: it holds only content
# the utility generates (`wf export wiki`), never copies of the corpus. This
# script just scaffolds the empty directory + Obsidian workspace config.

set -euo pipefail

FABRIC_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# Default: vault sits beside the fabric (dirname of the fabric root) —
# wherever the fabric lives, the vault is created next to it
VAULT_PATH="${1:-$(dirname "${FABRIC_ROOT}")/vault}"

echo "=== Setting up Obsidian vault output dir ==="
echo "Fabric: ${FABRIC_ROOT}"
echo "Vault:  ${VAULT_PATH}"
echo ""

mkdir -p "${VAULT_PATH}"
# Preserve any existing .obsidian workspace config; scaffold the dir otherwise
mkdir -p "${VAULT_PATH}/.obsidian"

echo "Vault ready: ${VAULT_PATH}"
echo "Open in Obsidian: open '${VAULT_PATH}'"
echo "Generate its content with: wf export wiki   (or python3 scripts/cmd/export-wiki.py '${VAULT_PATH}')"
