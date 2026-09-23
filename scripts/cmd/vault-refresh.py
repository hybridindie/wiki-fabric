#!/usr/bin/env python3
# vault-refresh.py — Manage the vault as a standalone OUTPUT directory for wiki-fabric.
#
# Usage:
#   python3 scripts/cmd/vault-refresh.py [VAULT_PATH]          # ensure output dir exists (idempotent)
#   python3 scripts/cmd/vault-refresh.py [VAULT_PATH] --check  # report only; exit 1 on drift
#
# The vault is the RESULT of the utility, never a mirror: wiki-fabric reads the
# corpus and WRITES generated content (the rendered wiki) here. It does not copy
# source content (evidence/, claims/, patterns/, projects/, registry/) into the
# vault — those live only in the fabric. Because the vault is standalone output,
# a machine can point vault.path at several targets (work vs personal).
#
# This script only scaffolds and audits the output directory. Generating the
# actual wiki content is `export-wiki.py` (`wf export wiki`). Drift here means
# the vault is missing its expected generated output, or carries stray files
# (e.g. symlinks copied from the older vault model).
#
# Exit codes: 0 = fresh (or scaffolded), 1 = drift detected (--check only).

import sys
import sys as _s, pathlib as _p
_B = _p.Path(__file__).resolve().parent
for _rel in ("", "cmd", "lib", "eval", "harness"):
    _s.path.insert(0, str(_B.parent / _rel))
import os
from pathlib import Path

from fabric_config import FABRIC_ROOT, get_config, get_vault_path

# Top-level entries the utility is responsible for generating into the vault.
# These are written by export-wiki.py (`wf export wiki`); vault-refresh only
# verifies their presence, never copies them.
EXPECTED_OUTPUT = [
    "wiki/index.md",
]

# Top-level names that should never appear in the vault: they are corpus content
# (mirrored in the old symlink/copy vault model) or harness files. Their presence
# signals a stale vault that should be regenerated, not a fresh one. The wiki/
# tree is NOT here — it is the generated output and is expected.
SIGNALS_STALE = [
    "AGENTS.md",
    "README.md",
    "patterns",
    "anti-patterns",
    "skills",
    "domains",
    "syntheses",
    "evidence",
    "registry",
    "projects",
]


def default_vault_path():
    return FABRIC_ROOT.parent / "vault"


def refresh(vault_path, check_only=False, quiet=False):
    vault = Path(vault_path).expanduser()
    problems = []
    created = 0

    def _say(msg):
        if not quiet:
            print(msg)

    # 1. Scaffold the output directory (idempotent).
    if not vault.exists():
        if check_only:
            problems.append(f"missing vault: {vault}")
            return 1
        vault.mkdir(parents=True, exist_ok=True)
        created += 1
        _say(f"  created vault: {vault}")
    (vault / ".obsidian").mkdir(parents=True, exist_ok=True)  # Obsidian workspace

    # 2. Verify expected generated output exists (the wiki front page at minimum).
    for rel in EXPECTED_OUTPUT:
        if not (vault / rel).exists():
            problems.append(f"missing generated output: {rel} — run `wf export wiki`")

    # 3. Flag stale vaults: corpus/harness content copied or symlinked in
    #    (from the older mirror model) should not be here. Never delete — the
    #    human decides; this just surfaces that the vault is not a fresh output.
    if vault.exists():
        for rel in SIGNALS_STALE:
            p = vault / rel
            if p.is_symlink() or p.exists():
                kind = "symlink" if p.is_symlink() else ("directory" if p.is_dir() else "file")
                problems.append(f"stale output present (mirror leftover): {rel} ({kind})")

    if problems:
        for p in problems:
            print(f"  drift: {p}", file=sys.stderr)
        if check_only:
            print(f"vault: {len(problems)} drift item(s)")
            return 1
        if not quiet:
            print(f"vault: {len(problems)} drift item(s) — review before next export")
        return 1  # presence of stale content is not auto-repaired; surfaces until cleaned
    if not quiet:
        print("vault: fresh" if not created else f"vault: scaffolded ({created} item(s))")
    return 0


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Scaffold/audit the vault output directory")
    parser.add_argument("vault_path", nargs="?", default=None)
    parser.add_argument("--check", action="store_true", help="report drift only; exit 1 if stale")
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()
    vault = args.vault_path or get_vault_path() or default_vault_path()
    return refresh(vault, check_only=args.check, quiet=args.quiet)


if __name__ == "__main__":
    sys.exit(main())
