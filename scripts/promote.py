#!/usr/bin/env python3
# promote.py — CLI wrapper for the promote skill
#
# Usage: python3 scripts/promote.py [--review] [--dry-run]

import sys
import re
from pathlib import Path
from datetime import date, datetime
from wf_common import parse_frontmatter

VAULT_ROOT = Path(__file__).parent.parent
PROMOTION_QUEUE = VAULT_ROOT / "registry" / "promotion-queue.md"
PROMOTIONS_DIR = VAULT_ROOT / "registry" / "promotions"

def write_frontmatter(path, fm, body):
    import yaml
    frontmatter = yaml.dump(fm, sort_keys=False, allow_unicode=True)
    path.write_text(f"---\n{frontmatter}---\n{body}")


def list_pending_promotions():
    """List all promotion dossiers with status pending-review."""
    dossiers = []
    for dossier_path in PROMOTIONS_DIR.glob("promotion-*.md"):
        fm, _ = parse_frontmatter(dossier_path)
        if fm.get("status") == "pending-review":
            dossiers.append((dossier_path, fm))
    return dossiers


def list_recommended():
    """List recommended patterns."""
    patterns = []
    for pattern_path in (VAULT_ROOT / "patterns").glob("*.md"):
        fm, _ = parse_frontmatter(pattern_path)
        if fm.get("status") == "recommended":
            patterns.append((pattern_path, fm))
    return patterns


def promote_dossier(dossier_path, dry_run=False):
    """Promote a dossier from pending-review to recommended."""
    from fabric_config import get_config, compiler_eval_recorded
    ok, why = compiler_eval_recorded(get_config())
    if not ok:
        print(f"BLOCKED: {why}")
        print("Policy: promotion runs on the compiler model require a recorded compiler eval")
        print("(eval-stability G4). Model swaps are compiler changes — re-evaluate first.")
        return False
    # Attestation (OKF §10): run the sanctioned eval attester over the receipt.
    attester = VAULT_ROOT / "references" / "attesters" / "check-golden-eval.py"
    if attester.exists():
        import subprocess as _sp
        _cm = get_config()["llm"].get("compiler_model", "")
        r = _sp.run([_sys_executable(), str(attester), "--model", _cm],
                    capture_output=True, text=True)
        if r.returncode != 0:
            print(f"BLOCKED: eval attestation refused — {r.stdout.strip()}")
            print("Policy: the golden-eval attested computation must attest before promotion.")
            return False
        print(f"Attested: {r.stdout.strip()}")
    fm, body = parse_frontmatter(dossier_path)
    
    if fm.get("status") != "pending-review":
        print(f"Error: {dossier_path} is not pending-review (status: {fm.get('status')})")
        return False
    
    pattern_ref = fm.get("pattern_ref", "")
    anti_ref = fm.get("anti_pattern_ref", "")
    
    if not pattern_ref:
        print("Error: No pattern_ref in dossier")
        return False
    
    # Extract pattern slug
    pattern_match = re.search(r'\[\[pattern-([^\]]+)\]\]', pattern_ref)
    if not pattern_match:
        print(f"Error: Could not extract pattern slug from {pattern_ref}")
        return False
    pattern_slug = pattern_match.group(1)
    
    pattern_path = VAULT_ROOT / "patterns" / f"pattern-{pattern_slug}.md"
    anti_path = VAULT_ROOT / "anti-patterns" / f"anti-pattern-{pattern_slug}.md"
    
    if not dry_run:
        import sys as _sys
        _sys.path.insert(0, str(Path(__file__).parent))
        from fabric_config import get_config, actor
        _cfg = get_config()
        _human = actor(_cfg, "human")
        _at = date.today().isoformat()

        # Update pattern status + human verification (OKF trust tier: human-reviewed)
        if pattern_path.exists():
            pfm, pbody = parse_frontmatter(pattern_path)
            pfm["status"] = "recommended"
            verified = pfm.get("verified") or []
            verified.append({"by": _human, "at": _at, "reason": "promotion gate: maturity+independence review"})
            pfm["verified"] = verified
            write_frontmatter(pattern_path, pfm, pbody)
            print(f"Updated pattern: {pattern_path} (verified by {_human})")

        anti_path_actual = VAULT_ROOT / "anti-patterns" / f"anti-pattern-{pattern_slug}.md"
        if anti_path_actual.exists():
            afm, abody = parse_frontmatter(anti_path_actual)
            afm["status"] = "recommended"
            averified = afm.get("verified") or []
            averified.append({"by": _human, "at": _at, "reason": "promotion gate"})
            afm["verified"] = averified
            write_frontmatter(anti_path_actual, afm, abody)
            print(f"Updated anti-pattern: {anti_path_actual}")

        # Update dossier
        fm["status"] = "recommended"
        fm["reviewed"] = _at
        fm["reviewed_by"] = _human
        write_frontmatter(dossier_path, fm, dossier_path.read_text().split("\n---\n", 2)[2])
        
        # Update promotion queue
        update_promotion_queue(pattern_path.stem.replace("pattern-", ""), "recommended")
        
        # Update pattern index
        update_indexes()
        
        # Update skill index
        
        
        # Update promotion queue
        update_promotion_queue_file()

        print(f"Promoted pattern: {pattern_path.name}")
        # Self-describing next steps (graphify provenance + usage feedback)
        from fabric_config import is_integration_active, get_config as _gc
        if is_integration_active(get_config(), "graphify"):
            print("Next (graphify active): python3 scripts/graphify-bridge.py --enrich "
                  "— attach code provenance to code-adjacent patterns.")
        print("Track usage on the pattern page (usage: retrieved/applied counts) — "
              "a pattern read but never applied is too abstract.")
        return True
    else:
        print(f"[DRY RUN] Would promote: {dossier_path}")
        return True


def update_promotion_queue(pattern_slug, new_status):
    """Update promotion-queue.md"""
    queue_path = PROMOTION_QUEUE
    text = queue_path.read_text()
    
    # Update the table row
    old_row = f"| [[pattern-{pattern_slug}]] | 1 (observed)"
    new_row = f"| [[pattern-{pattern_slug}]] | 2 (recommended)"
    text = text.replace(old_row, new_row)
    
    # Update the "same two projects" note
    text = text.replace("(above)", f"[[promotion-{pattern_slug.replace('pattern-', '')}]]")
    
    Path(PROMOTION_QUEUE).write_text(text)


def update_indexes():
    """Registry views are derived: rebuild catalog.json from actual files."""
    import subprocess as _sp
    r = _sp.run([sys.executable, str(Path(__file__).parent / "rebuild-index.py")],
                capture_output=True, text=True)
    if r.returncode != 0:
        print(f"Warning: rebuild-index failed: {r.stderr[:200]}", file=sys.stderr)


def list_dossiers():
    """List all promotion dossiers."""
    print("Promotion dossiers:")
    for dossier_path in sorted(PROMOTIONS_DIR.glob("promotion-*.md")):
        fm, _ = parse_frontmatter(dossier_path)
        print(f"  {dossier_path.name}: {fm.get('status', 'unknown')} - {fm.get('title', 'Untitled')}")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Manage pattern promotions")
    parser.add_argument("--list", action="store_true", help="List all promotion dossiers")
    parser.add_argument("--promote", metavar="DOSSIER", help="Promote a specific dossier")
    parser.add_argument("--all", action="store_true", help="Promote all pending-review dossiers")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done")
    args = parser.parse_args()
    
    if args.list:
        list_dossiers()
        return
    
    if args.promote:
        dossier_path = PROMOTIONS_DIR / args.promote
        if not dossier_path.exists():
            dossier_path = VAULT_ROOT / "registry" / "promotions" / args.promote
        if not dossier_path.exists():
            print(f"Error: Dossier not found: {args.promote}", file=sys.stderr)
            sys.exit(1)
        promote_dossier(dossier_path, dry_run=args.dry_run)
        return
    
    if args.all:
        dossiers = list_pending_promotions()
        for dossier_path, _ in dossiers:
            promote_dossier(dossier_path, dry_run=args.dry_run)
        return
    
    parser.print_help()


if __name__ == "__main__":
    main()