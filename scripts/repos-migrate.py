#!/usr/bin/env python3
# repos-migrate.py — Fold explicit fabric.yaml per-repo config into each
# project's .wiki-overlay.md routing block (config-per-project migration).
#
# Usage:
#   python3 scripts/repos-migrate.py --dry-run    # show what would move
#   python3 scripts/repos-migrate.py --apply      # write overlays (fabric.yaml untouched)
#
# After applying, fabric.yaml repos entries can shrink to just `path:` (or be
# deleted entirely when the project is a discoverable sibling with default
# settings). The tool never deletes fabric.yaml keys — review + prune by hand.

import sys
import re
from pathlib import Path
from datetime import date

sys.path.insert(0, str(Path(__file__).parent))
from fabric_config import FABRIC_ROOT, get_config, get_repo_config, resolve_repo_path

MIGRATABLE = ("extract", "synthesize", "dossier", "graph_dir")


def overlay_path_for(config, slug):
    p = resolve_repo_path(config, slug)
    return p / ".wiki-overlay.md" if p else None


def plan(config):
    """Return [(slug, keys_to_move, overlay_path_or_None)]."""
    moves = []
    repos_cfg = config.get("repos") or {}
    for slug, entry in sorted(repos_cfg.items()):
        if not isinstance(entry, dict):
            continue
        keys = {k: v for k, v in entry.items() if k in MIGRATABLE}
        if not keys:
            continue
        moves.append((slug, keys, overlay_path_for(config, slug)))
    return moves


def apply_moves(moves, dry_run=True):
    from wf_common import parse_frontmatter
    for slug, keys, overlay_path in moves:
        if overlay_path is None or not overlay_path.exists():
            print(f"  {slug}: overlay not found at {overlay_path} — skipping")
            continue
        fm, body = parse_frontmatter(overlay_path)
        routing = dict(fm.get("routing") or {})
        for k, v in keys.items():
            if k in routing and routing[k] != v:
                print(f"  {slug}: CONFLICT routing.{k}: overlay={routing[k]!r} fabric.yaml={v!r} — keeping overlay value")
                continue
            routing[k] = v
        if dry_run:
            print(f"  {slug}: would set routing {routing} in {overlay_path}")
            continue
        fm["routing"] = routing
        fm["updated"] = date.today().isoformat()
        fm_yaml = yaml_safe_dump(fm)
        overlay_path.write_text(f"---\n{fm_yaml}---\n{body}")
        print(f"  {slug}: routing written to {overlay_path}")


def yaml_safe_dump(fm):
    import yaml
    return yaml.dump(fm, sort_keys=False, allow_unicode=True, default_flow_style=False)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Move per-repo config from fabric.yaml into project overlays")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    config = get_config()
    moves = plan(config)
    if not moves:
        print("Nothing to migrate: no explicit per-repo routing in fabric.yaml")
        return 0
    print(f"Migrating {len(moves)} repo(s):")
    if args.apply:
        apply_moves(moves, dry_run=False)
        print("\nfabric.yaml NOT modified — prune the moved keys (and path: entries for")
        print("discoverable siblings) when you've verified the overlays.")
    else:
        apply_moves(moves, dry_run=True)
        print("\n(dry run — use --apply to write)")
    return 0


if __name__ == "__main__":
    sys.exit(main())