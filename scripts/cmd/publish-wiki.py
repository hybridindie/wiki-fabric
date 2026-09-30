#!/usr/bin/env python3
# publish-wiki.py — publish the generated wiki as a static site (#146 / living-wiki S4).
#
# Stages the wiki output into a Quartz v4 checkout and builds HTML. The wiki
# output stays canonical (vault/wiki/); this is a VIEW, not the canonical form.
# Deterministic: same wiki content → same site bytes (Quartz's build is
# content-driven; the manifest below gates the *decision* to rebuild).
#
# No-op discipline: caller checks wiki-export-manifest.json first — a clean
# run produces zero content diff and commits nothing.
#
# Usage:
#   python3 scripts/cmd/publish-wiki.py [--quartz-dir DIR] [--out DIR] [--dry-run] [--no-build]
#
# Local:  python3 scripts/cmd/publish-wiki.py            (quartz auto-cloned to
#         <out>/_quartz if missing; content copied; build emitted to <out>/public)
# CI:     clone quartz at a pinned SHA, run this script with --quartz-dir.

import sys
import sys as _s, pathlib as _p
_HERE = _p.Path(__file__).resolve().parent
for _dir in (_HERE, _HERE.parent / "lib", _HERE.parent):
    if str(_dir) not in _s.path:
        _s.path.insert(0, str(_dir))

import argparse
import shutil
import subprocess
import json
from pathlib import Path

from fabric_config import get_config
from wf_common import now_iso_utc

# Pinned Quartz revision (reproducible builds; bump deliberately).
QUARTZ_REPO = "https://github.com/jackyzha0/quartz.git"
QUARTZ_REF = "v4.5.2"


def _wiki_root():
    # layout-aware default (parity with export-wiki/generators — an explicit
    # vault.path names the wiki root directly; no /wiki append)
    from fabric_config import _default_vault_root
    return _default_vault_root()


def _default_site_root():
    """Published site lives beside the wiki root (per-layout, resolver-named)."""
    from fabric_config import _default_vault_root
    return _default_vault_root().parent / "site"


def ensure_quartz(quartz_dir, dry_run=False):
    """Clone (or refresh) the pinned Quartz checkout."""
    q = Path(quartz_dir)
    if q.exists() and (q / "package.json").exists():
        return q
    if dry_run:
        return q
    print(f"  quartz: cloning {QUARTZ_REPO}@{QUARTZ_REF} → {q}")
    subprocess.run(["git", "clone", "--depth", "1", "--branch", QUARTZ_REF,
                    QUARTZ_REPO, str(q)], check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return q


def stage_content(quartz_dir, wiki_root, dry_run=False):
    """Replace quartz/content with the wiki output (index + projects/ + topics/).
    The quartz default sample content is removed — the site is wiki-only."""
    q = Path(quartz_dir)
    content = q / "content"
    if not dry_run:
        if content.exists():
            shutil.rmtree(content)
        shutil.copytree(wiki_root, content)
    n = sum(1 for _ in Path(wiki_root).rglob("*.md"))
    return n


def build(quartz_dir, out_dir, dry_run=False):
    q = Path(quartz_dir)
    if dry_run:
        print("  [dry-run] would npm install + quartz build")
        return None
    node_modules = q / "node_modules"
    if not node_modules.exists():
        subprocess.run(["npm", "i", "--no-audit", "--no-fund"], cwd=q, check=True,
                       stdout=subprocess.DEVNULL)
    r = subprocess.run(["npx", "quartz", "build"], cwd=q, capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stdout[-2000:], file=sys.stderr)
        print(r.stderr[-2000:], file=sys.stderr)
        raise RuntimeError(f"quartz build failed ({r.returncode})")
    produced = q / "public"
    out = Path(out_dir)
    if out.resolve() != produced.resolve():
        if out.exists():
            shutil.rmtree(out)
        shutil.move(str(produced), str(out))
    print(f"  built: {out} (static site)")
    return out


def main():
    parser = argparse.ArgumentParser(description="Publish the wiki as a static site (Quartz v4)")
    parser.add_argument("--quartz-dir", default=None,
                        help="Quartz checkout (default: <out>/_quartz, cloned at a pinned ref)")
    parser.add_argument("--out", default=None,
                        help="Publish root (default: <vault>/site)")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    wiki_root = _wiki_root()
    if not wiki_root.is_dir() or not list(wiki_root.glob("*.md")):
        print("No wiki output to publish — run: wf export wiki", file=sys.stderr)
        return 1
    out_root = Path(args.out) if args.out else _default_site_root()
    out_root = Path(out_root)
    out_root.mkdir(parents=True, exist_ok=True)
    quartz_dir = Path(args.quartz_dir) if args.quartz_dir else out_root / "_quartz"

    print("Publishing wiki → static site")
    ensure_quartz(quartz_dir, dry_run=args.dry_run)
    stage_content(quartz_dir, wiki_root, dry_run=args.dry_run)
    out = build(quartz_dir, out_root / "public", dry_run=args.dry_run)
    if not args.dry_run:
        print(f"  site: {out_root / 'public'}/")
    return 0


if __name__ == "__main__":
    sys.exit(main())