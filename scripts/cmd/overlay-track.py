#!/usr/bin/env python3
"""overlay-track.py — the H4 one-shot sweep (#180): stage + commit every
connected project's untracked .wiki-overlay.md (idempotent; already-tracked
repos skip). Deterministic, 0 tokens.

    python3 scripts/cmd/overlay-track.py [--dry-run]
"""

import subprocess
import sys as _s, pathlib as _p
_HERE = _p.Path(__file__).resolve().parent
for _dir in (_HERE, _HERE.parent / "lib"):
    if str(_dir) not in _s.path:
        _s.path.insert(0, str(_dir))
from pathlib import Path

import fabric_config as fc


def stage_overlay(repo: Path, dry_run: bool):
    overlay = repo / ".wiki-overlay.md"
    if not overlay.exists():
        return "no-overlay"
    probe = subprocess.run(["git", "-C", str(repo), "ls-files", "--", ".wiki-overlay.md"],
                           capture_output=True, text=True, timeout=15)
    if probe.stdout.strip():
        return "tracked"
    if dry_run:
        return "would-stage"
    subprocess.run(["git", "-C", str(repo), "add", "--", ".wiki-overlay.md"],
                   check=False, timeout=15)
    commit = subprocess.run(
        ["git", "-C", str(repo), "commit", "-m",
         "chore: track .wiki-overlay.md (the fabric config travels with the repo — H4/#180)"],
        capture_output=True, text=True, timeout=30)
    return "committed" if commit.returncode == 0 else "staged"


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Track every connected project's overlay (H4 sweep)")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    config = fc.get_config()
    names = fc.get_all_repo_names(config)
    if not names:
        print("No connected projects.", file=sys_err())
        return 1
    counts = {}
    for slug in names:
        rcfg = fc.get_repo_config(config, slug) or {}
        rp = rcfg.get("path")
        if not rp:
            print(f"  {slug}: no path (skipped)")
            continue
        repo = (fc.FABRIC_ROOT / rp).resolve() if not Path(rp).is_absolute() else Path(rp)
        if not repo.is_dir():
            print(f"  {slug}: repo missing ({repo})")
            continue
        out = stage_overlay(repo, args.dry_run)
        counts[out] = counts.get(out, 0) + 1
        print(f"  {slug}: {out}")
    verb = ("[DRY RUN] " if args.dry_run else "")
    print(verb + ", ".join(f"{v} {k}" for k, v in counts.items()))
    untracked = counts.get("no-overlay", 0)
    return 0


def sys_err():
    import sys
    return sys.stderr


if __name__ == "__main__":
    import sys
    sys.exit(main())