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
_HERE = _p.Path(__file__).resolve().parent
# Explicit import bootstrap: this script's own dir (same-dir siblings)
# + scripts/lib (shared modules). No shotgun path injection.
for _dir in (_HERE, _HERE.parent / "lib"):
    if str(_dir) not in _s.path:
        _s.path.insert(0, str(_dir))
import os
from pathlib import Path

from fabric_config import FABRIC_ROOT, CORPUS_ROOT, get_config, get_vault_path

# Top-level entries the utility is responsible for generating into the vault.
# These are written by export-wiki.py (`wf export wiki`); vault-refresh only
# verifies their presence, never copies them.
EXPECTED_OUTPUT = [
    "index.md",  # the wiki front page (at the vault/output root; #e2e fix —
                 # was 'wiki/index.md', doubling when vault = corpus/wiki)
]

# Top-level names that should never appear in the vault OUTPUT: corpus content
# atoms (mirrored in the old symlink/copy vault model) or harness files. Their
# presence signals a stale vault that should be regenerated, not a fresh one.
# NOTE the wiki generator's OWN output subdirs (topics/, projects/<slug>/ deep
# dives, domains/ hubs — living-wiki S3) are GENERATED now and expected (#e2e
# finding: the old mirror-era list flagged real output as stale).
SIGNALS_STALE = [
    "AGENTS.md",
    "README.md",
    "patterns",
    "anti-patterns",
    "skills",
    "syntheses",
    "evidence",
    "registry",
]


def default_vault_path():
    """Single truth: fabric_config's layout-aware default (the resolver and
    the audit must agree — #151/#152 class)."""
    from fabric_config import _default_vault_root
    return _default_vault_root()


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
    # vault.path unset (None) means "the vault IS the fabric" — but with the
    # corpus-nested layout the OUTPUT root is corpus/wiki, not the fabric root
    # (audit there; #e2e finding: refresh audited the wrong tree).
    from fabric_config import get_config, is_integration_active
    if get_vault_path() is None or not Path(str(get_vault_path())).is_relative_to(CORPUS_ROOT / "wiki"):
        vp = str(get_vault_path())
        if vp in (str(FABRIC_ROOT), "None"):
            vault = default_vault_path()
    return refresh(vault, check_only=args.check, quiet=args.quiet)


if __name__ == "__main__":
    sys.exit(main())
