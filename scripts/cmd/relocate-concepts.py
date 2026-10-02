#!/usr/bin/env python3
# relocate-concepts.py — S1/#159: physical domain relocation.
#
# The Scope→home contract (ontology ## Scope → home mapping, docs/site/cli.md,
# ingest SKILL) declares domains/<domain>/{concepts,questions,syntheses} as
# the homes for domain-bound pages. Pages were flat under concepts/; this
# moves each domain-bound concept to its canonical domain home, alias-folded
# through the shared ontology parser. Deterministic 0 tokens, idempotent
# (already-moved is a no-op), dry-run-able, logged to registry/log.md.
#
# Wikilinks survive: every [[link]] is stem-based (no paths), so moving a page
# never breaks a reference; the catalog (registry/catalog.json) is derived and
# re-built after the run.
#
# Usage:
#   python3 scripts/cmd/relocate-concepts.py --dry-run
#   python3 scripts/cmd/relocate-concepts.py

import sys
import sys as _s, pathlib as _p
_HERE = _p.Path(__file__).resolve().parent
for _dir in (_HERE, _HERE.parent / "lib"):
    if str(_dir) not in _s.path:
        _s.path.insert(0, str(_dir))
import argparse
import re
from pathlib import Path

import layout
import ontology as _o
from wf_common import parse_frontmatter
from fabric_config import CORPUS_ROOT, VAULT_ROOT, get_config, actor


def domain_bindings(topics_domain):
    """Spelled domains of one page (raw string form from frontmatter) — shared
    parser handles list/str + aliases. Returns canonical name list."""
    onto = _o.parse((layout.domains(CORPUS_ROOT) / "ontology.md")
                    .read_text(encoding="utf-8", errors="replace")
                    if (layout.domains(CORPUS_ROOT) / "ontology.md").exists() else "")
    return sorted(_o.canonicalize(topics_domain or [], onto))


def migrate(dry_run=False):
    onto_path = layout.domains(CORPUS_ROOT) / "ontology.md"
    if not onto_path.exists():
        print("No ontology — nothing to bind (run propose/promote-domains first)")
        return 0
    onto = _o.parse(onto_path.read_text(encoding="utf-8", errors="replace"))
    if not onto["domains"]:
        print("Ontology declares no domains — nothing to bind")
        return 0

    claims_glob_dir = layout.concepts(CORPUS_ROOT)
    moved, kept, skipped = 0, 0, 0
    for cp in sorted(claims_glob_dir.glob("concept-*.md")):
        fm, _ = parse_frontmatter(cp)
        raw = fm.get("domain") or []
        if isinstance(raw, str):
            raw = [x.strip() for x in raw.strip("[]").split(",")]
        declared = [str(d).strip() for d in raw if str(d).strip()]
        canon = {}
        for d in declared:  # declaration order = primary order (sorted() lied)
            for c in _o.canonicalize(d, onto):
                canon.setdefault(c, d)
        if not canon:
            skipped += 1
            continue
        primary = next(iter(canon))
        if len(canon) > 1:
            print(f"  multi-domain {cp.name}: binds {primary} (home) + "
                  f"{[k for k in canon if k != primary]} (frontmatter stays full)")
        dest_dir = layout.domain_home(CORPUS_ROOT, primary, "domain_concepts_home")
        dest = dest_dir / cp.name
        if dest.parent == cp.parent:
            kept += 1
            continue  # already relocated
        if dry_run:
            print(f"[DRY] {cp.relative_to(CORPUS_ROOT)} → {dest.relative_to(CORPUS_ROOT)}")
            moved += 1
            continue
        dest_dir.mkdir(parents=True, exist_ok=True)
        cp.rename(dest)
        moved += 1
        print(f"moved {cp.name} → {dest_dir.relative_to(CORPUS_ROOT)}/")

    if moved and not dry_run:
        # derived index: rebuild so views/scope pick up the new truth
        import subprocess
        r = subprocess.run([sys.executable, str(_HERE / "rebuild-index.py")],
                           capture_output=True, text=True)
        if r.returncode != 0:
            print(f"warn: rebuild-index failed: {r.stderr[:200]}", file=sys.stderr)
        _log(moved, skipped)
    print(f"\nRelocation: {moved} moved, {kept} already home, {skipped} unbound (stay flat)")
    return moved


def _log(moved, skipped):
    try:
        log_path = layout.registry(CORPUS_ROOT) / "log.md"
        with open(log_path, "a") as f:
            from datetime import date
            f.write(f"\n## {date.today().isoformat()}\n* **relocate-concepts | "
                    f"{actor(get_config(), 'process', model='relocate-concepts')}**\n")
            f.write(f"- S1/#159 Scope→home migration: {moved} concept(s) → domains/<domain>/concepts/ "
                    f"({skipped} unbound kept flat)\n")
    except Exception as e:
        print(f"warn: log append failed: {e}", file=sys.stderr)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Relocate domain-bound concepts to domains/<domain>/concepts/ (S1/#159)")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    moved = migrate(dry_run=args.dry_run)
    return 0


if __name__ == "__main__":
    main()