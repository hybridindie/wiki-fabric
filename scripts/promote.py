#!/usr/bin/env python3
# promote.py — CLI wrapper for the promote skill
#
# Usage: python3 scripts/promote.py [--review] [--dry-run]

import sys
import re
from pathlib import Path
from datetime import date, datetime

VAULT_ROOT = Path(__file__).parent.parent
PROMOTION_QUEUE = VAULT_ROOT / "registry" / "promotion-queue.md"
PROMOTIONS_DIR = VAULT_ROOT / "registry" / "promotions"
PATTERN_INDEX = VAULT_ROOT / "registry" / "pattern-index.md"
SKILL_INDEX = VAULT_ROOT / "registry" / "skill-index.md"

def parse_frontmatter(path):
    text = path.read_text(encoding="utf-8", errors="replace")
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.DOTALL)
    if not m:
        return {}, text
    raw, body = m.group(1), m.group(2)
    try:
        import yaml
        fm = yaml.safe_load(raw) or {}
    except Exception:
        fm = {}
    return fm, body


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
        update_pattern_index()
        
        # Update skill index
        update_skill_index()
        
        # Update promotion queue
        update_promotion_queue_file()
        
        print(f"Promoted pattern: {pattern_path.name}")
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


def update_pattern_index():
    """Update pattern-index.md"""
    index_path = VAULT_ROOT / "registry" / "pattern-index.md"
    text = PATTERN_INDEX.read_text()
    
    # Find the pattern row and update maturity
    # This is a simple approach - in reality you'd parse the table properly
    # For now, just ensure the pattern is listed as recommended
    if "pattern-single-writer-with-parity-check" in str(PATTERN_INDEX.read_text()):
        # Already there, just ensure it says recommended
        text = PATTERN_INDEX.read_text()
        text = text.replace("2 (candidate)", "2 (recommended)")
        PATTERN_INDEX.write_text(text)


def update_skill_index():
    skill_index = VAULT_ROOT / "registry" / "skill-index.md"
    text = skill_index.read_text()
    if "serialize-and-verify-writes" not in text:
        new_row = "| [[serialize-and-verify-writes]] | 2 (recommended) | [[pattern-single-writer-with-parity-check]] | available |"
        text = text.replace(
            "| Skill | Maturity | Pattern | Status |",
            f"| Skill | Maturity | Pattern | Status |\n|---|---|---|---|\n| [[serialize-and-verify-writes]] | 2 (recommended) | [[pattern-single-writer-with-parity-check]] | available |"
        )
    VAULT_ROOT.joinpath("registry/skill-index.md").write_text(text)


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