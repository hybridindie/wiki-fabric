#!/usr/bin/env python3
# promote-domains.py — Human-gated application of domain proposals to the ontology.
#
# Mirrors promote.py: domain proposals are written by propose-domains.py as
# pending-review dossiers; this script merges ONE human-approved dossier into
# domains/ontology.md. No auto-apply.
#
# Usage:
#   python3 scripts/cmd/promote-domains.py --list                      # pending proposals
#   python3 scripts/cmd/promote-domains.py --apply <dossier-file>      # merge one
#   python3 scripts/cmd/promote-domains.py --apply <dossier-file> --dry-run

import sys
import sys as _s, pathlib as _p
_B = _p.Path(__file__).resolve().parent
for _rel in ("", "cmd", "lib", "eval", "harness"):
    _s.path.insert(0, str(_B.parent / _rel))
from pathlib import Path
from datetime import date

from fabric_config import CORPUS_ROOT, get_config
from wf_common import parse_frontmatter

ONTOLOGY_PATH = CORPUS_ROOT / "domains" / "ontology.md"
PROPOSALS_DIR = CORPUS_ROOT / "registry" / "domain-proposals"


def list_pending_proposals():
    out = []
    if not PROPOSALS_DIR.exists():
        return out
    for p in sorted(PROPOSALS_DIR.glob("domain-*.md")):
        fm, _ = parse_frontmatter(p)
        if fm.get("status") == "proposed":
            out.append((p, fm))
    return out


def add_domain_to_ontology(domain, desc):
    """Append a domain bullet under the '## Domains' section of ontology.md.

    Bootstraps a minimal ontology file if it doesn't exist yet, so apply works
    on a fresh fabric (the file is normally seeded at init)."""
    if not ONTOLOGY_PATH.exists():
        ONTOLOGY_PATH.parent.mkdir(parents=True, exist_ok=True)
        ONTOLOGY_PATH.write_text("---\ntype: ontology\ntitle: Domain Ontology\n---\n\n## Domains\n",
                                 encoding="utf-8")
    text = ONTOLOGY_PATH.read_text(encoding="utf-8")
    lines = text.split("\n")
    insert_idx = None
    for i, line in enumerate(lines):
        if line.rstrip() == "## Domains":
            insert_idx = i + 1
            break
        if line.startswith("## ") and line.rstrip() != "## Domains" and insert_idx is not None:
            break
        if line.startswith("## ") and insert_idx is None:
            insert_idx = i + 1
    if insert_idx is None:
        insert_idx = len(lines)
    bullet = f"- **{domain}** — {desc} (human-approved {date.today().isoformat()})"
    if any(f"**{domain}**" in l for l in lines):
        return False  # already present
    lines.insert(insert_idx, bullet)
    ONTOLOGY_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return True


def apply_proposal(dossier_path, dry_run=False):
    from fabric_config import actor
    fm, body = parse_frontmatter(dossier_path)
    if fm.get("status") != "proposed":
        print(f"Not a pending proposal (status={fm.get('status')})")
        return False
    domain = str(fm.get("domain", "")).strip()
    if not domain:
        print("No 'domain' field in dossier frontmatter")
        return False
    desc = domain.replace("-", " ")
    if dry_run:
        print(f"[DRY RUN] would add domain '{domain}' to {ONTOLOGY_PATH}")
        return True
    added = add_domain_to_ontology(domain, desc)
    if not added:
        print(f"Domain '{domain}' already in ontology; marking dossier merged anyway")
    _cfg = get_config()
    _human = actor(_cfg, "human")
    fm["status"] = "merged"
    fm["merged"] = date.today().isoformat()
    fm["merged_by"] = _human
    fm["ontology_ref"] = f"[[{ONTOLOGY_PATH.name}]]"
    import yaml as _y
    out = "---\n" + _y.dump(fm, sort_keys=False, allow_unicode=True) + "---\n" + (body or "")
    dossier_path.write_text(out, encoding="utf-8")
    print(f"Merged domain '{domain}' into ontology (by {_human})")
    return True


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Apply human-approved domain proposals")
    parser.add_argument("--list", action="store_true", help="List pending proposals")
    parser.add_argument("--apply", metavar="DOSSIER", help="Merge a specific proposal")
    parser.add_argument("--dry-run", action="store_true", help="Show without writing")
    args = parser.parse_args()

    if args.list:
        for p, fm in list_pending_proposals():
            print(f"  ✎ {p.name}  ({fm.get('title')})")
        return

    if args.apply:
        p = PROPOSALS_DIR / args.apply
        if not p.exists():
            p = Path(args.apply)
        if not p.exists():
            print(f"Dossier not found: {args.apply}")
            sys.exit(1)
        ok = apply_proposal(p, dry_run=args.dry_run)
        sys.exit(0 if ok else 1)

    parser.print_help()


if __name__ == "__main__":
    main()
