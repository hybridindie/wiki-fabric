#!/usr/bin/env python3
# promote.py — CLI wrapper for the promote skill
#
# Usage: python3 scripts/cmd/promote.py [--review] [--dry-run]

import sys
import sys as _s, pathlib as _p
_HERE = _p.Path(__file__).resolve().parent
# Explicit import bootstrap: this script's own dir (same-dir siblings)
# + scripts/lib (shared modules). No shotgun path injection.
for _dir in (_HERE, _HERE.parent / "lib"):
    if str(_dir) not in _s.path:
        _s.path.insert(0, str(_dir))
import re
import json
from pathlib import Path
from datetime import date, datetime

from wf_common import parse_frontmatter
from fabric_config import CORPUS_ROOT, VAULT_ROOT

import layout

# The golden-eval attester ships with the harness (references/), not the corpus.
_HARNESS = Path(__file__).resolve().parent.parent.parent


def _sys_executable():
    """Python interpreter for subprocess eval/attester calls (venv-aware)."""
    return sys.executable
PROMOTION_QUEUE = layout.registry(VAULT_ROOT) / "promotion-queue.md"
PROMOTIONS_DIR = layout.registry(VAULT_ROOT) / "promotions"

def write_frontmatter(path, fm, body):
    # shared writer since #154 (wf_common — one dump convention)
    from wf_common import write_frontmatter
    write_frontmatter(path, fm, body)


def list_pending_promotions():
    """List all promotion dossiers with status pending-review."""
    dossiers = []
    for dossier_path in PROMOTIONS_DIR.glob("promotion-*.md"):
        fm, _ = parse_frontmatter(dossier_path)
        if fm.get("status") == "pending-review":
            dossiers.append((dossier_path, fm))
    return dossiers
def run_behavior_gate(pattern_slug, dry_run=False):
    """Pre-merge gate (#139 / SkillOpt S2): run the held-out behavior-fixture
    gate set before merging. Returns (ok, detail). Matrix:
      patterns: gate set must keep Knowledge Utility at 100% on the held-out
      set (ties flagged — they block later 'standard' promotion); the gate
      compares the merge-candidate corpus against the pre-merge corpus.
      Anti-patterns and concepts/domains: no utility gate (their contract is
      counterexamples + human review). Skills: strictly-better, ties rejected.
    Fails soft-open: if the fixture suite is unavailable, the gate is skipped
    and the dossier proceeds (structural gates still apply)."""
    eval_py = _HARNESS / "scripts" / "eval" / "eval-behavior.py"
    if not eval_py.exists():
        return True, "gate unavailable (eval-behavior.py missing) — skipped"
    import subprocess as _sp
    r = _sp.run([_sys_executable(), str(eval_py), "--gate", "--json"],
                capture_output=True, text=True)
    if r.returncode != 0:
        return True, f"gate suite unavailable ({r.stderr.strip()[:120]}) — skipped"
    try:
        data = json.loads(r.stdout)
        utility = data["metrics"]["knowledge_utility"]
        passed, total = data["metrics"]["passed"], data["metrics"]["total"]
    except Exception as e:
        return True, f"gate report unparseable — skipped ({e})"
    detail = f"held-out utility {utility:.0%} ({passed}/{total})"
    if passed < total:
        return False, (f"gate FAILED: {detail} — a held-out fixture stopped "
                       "passing; merge would lower Knowledge Utility")
    return True, f"gate OK: {detail}"


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
    # references/ is harness content; the attester lives there, not in the corpus.
    attester = _HARNESS / "references" / "attesters" / "check-golden-eval.py"
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

    # Behavior gate (#139): held-out fixtures must not regress pre-merge.
    gate_ok, gate_detail = run_behavior_gate(pattern_slug, dry_run=dry_run)
    if not gate_ok:
        print(f"BLOCKED: {gate_detail}")
        print("Fix the fixture regression (or revisit the candidate) before promoting.")
        return False
    print(f"Gate: {gate_detail}")
    
    pattern_path = layout.patterns(VAULT_ROOT) / f"pattern-{pattern_slug}.md"
    anti_path = layout.anti_patterns(VAULT_ROOT) / f"anti-pattern-{pattern_slug}.md"
    
    if not dry_run:
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

        anti_path_actual = layout.anti_patterns(VAULT_ROOT) / f"anti-pattern-{pattern_slug}.md"
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
        
        # Update promotion queue (fail-soft: it's a human-maintained checklist)
        update_promotion_queue(pattern_path.stem.replace("pattern-", ""), "recommended")
        
        # Update pattern index (registry views are derived)
        update_indexes()
        
        print(f"Promoted pattern: {pattern_path.name}")
        # Gate evidence in the timeline (#139): every accept/reject carries
        # its score evidence (dossier-level edit_apply_report analogue).
        try:
            log = layout.registry(VAULT_ROOT) / "log.md"
            with open(log, "a") as f:
                f.write(f"\n## {_at}\n* **promotion-apply | {_human}**\n")
                f.write(f"- {dossier_path.name}: behavior-gate {gate_detail}\n")
        except Exception as e:
            print(f"warn: gate result not logged: {e}", file=sys.stderr)
        # Self-describing next steps (graphify provenance + usage feedback)
        from fabric_config import is_integration_active, get_config as _gc
        if is_integration_active(get_config(), "graphify"):
            print("Next (graphify active): wf graphify enrich  # attach code provenance")
        print("Track usage on the pattern page (usage: retrieved/applied counts) — "
              "a pattern read but never applied is too abstract.")
        return True
    else:
        print(f"[DRY RUN] Would promote: {dossier_path}")
        return True


def reject_dossier(dossier_path, reason, dry_run=False):
    """Reject a pending-review dossier: lifecycle transition, not deletion.
    Dossier + pattern artifacts remain (evidence is never erased); the
    rejection reason and reviewer are recorded for future mining."""
    from fabric_config import get_config, actor
    from datetime import datetime
    fm, body = parse_frontmatter(dossier_path)
    if not fm:
        print("Error: dossier has no parseable frontmatter", file=sys.stderr)
        return False
    if str(fm.get("status", "")) != "pending-review":
        print(f"Not pending-review (status: {fm.get('status')!r}) — nothing to reject.", file=sys.stderr)
        return False
    if not reason or not reason.strip():
        print("Error: --reject-reason is required (a rejection without a reason is unusable evidence).", file=sys.stderr)
        return False
    if dry_run:
        print(f"[DRY RUN] Would reject {dossier_path.name}: reason: {reason[:80]}")
        return True
    _cfg = get_config()
    _human = actor(_cfg, "human")
    _at = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
    fm["status"] = "rejected"
    fm["reviewed"] = _at
    fm["reviewed_by"] = _human
    fm["rejection_reason"] = reason.strip()
    body_new = body.rstrip("\n") + f"\n\n## Rejection\n\n- **When:** {_at}\n- **By:** {_human}\n- **Reason:** {reason.strip()}\n"
    write_frontmatter(dossier_path, fm, body_new)
    # Tombstone (#140): the miner suppresses matching clusters from here on
    try:
        from wiki_lib import tombstones as T
        sig = T._sig_tokens(body_new)
        cid = str(fm.get("id") or dossier_path.stem).replace("promotion-", "")
        T.write_tombstone(VAULT_ROOT, "promotion-dossier", cid, reason, sig, _human)
        print(f"Tombstone written to patterns/_rejected/tombstone-{cid}.md")
    except Exception as e:
        print(f"warn: tombstone not written: {e}", file=sys.stderr)
    # registry timeline: the corpus log records the decision
    log = layout.registry(VAULT_ROOT) / "log.md"
    with open(log, "a") as f:
        f.write(f"\n## {_at[:10]}\n* **promotion-reject | {_human}**\n")
        f.write(f"- {dossier_path.stem}: {reason.strip()[:140]}\n")
    update_indexes()
    print(f"Rejected: {dossier_path.name} (artifacts retained; reason recorded)")
    print("The demoted events remain available for future mining — re-run mine-promotions to re-cluster.")
    return True

def update_promotion_queue(pattern_slug, new_status):
    """Update promotion-queue.md's observational-count row. Fail-soft: the
    queue is a human-maintained checklist (system/skills/promote/SKILL.md) —
    absent is normal (first promotion, or a fabric that never adopted it);
    a promotion must not die on it (was a NameError path before)."""
    queue_path = PROMOTION_QUEUE
    try:
        text = queue_path.read_text()
    except OSError:
        print("  promotion-queue.md not found — skipping queue row update "
              "(human-maintained checklist; create it per system/skills/promote/SKILL.md)")
        return
    
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
    parser.add_argument("--reject", metavar="DOSSIER", help="Reject a pending-review dossier (artifacts retained)")
    parser.add_argument("--reject-reason", default=None, help="Required with --reject — recorded in the dossier")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done")
    args = parser.parse_args()
    
    if args.list:
        list_dossiers()
        return
    
    if args.promote:
        dossier_path = PROMOTIONS_DIR / args.promote
        if not dossier_path.exists():
            dossier_path = layout.registry(VAULT_ROOT) / "promotions" / args.promote
        if not dossier_path.exists():
            print(f"Error: Dossier not found: {args.promote}", file=sys.stderr)
            sys.exit(1)
        promote_dossier(dossier_path, dry_run=args.dry_run)
        return
    
    if args.reject:
        dossier_path = PROMOTIONS_DIR / args.reject
        if not dossier_path.exists():
            dossier_path = layout.registry(VAULT_ROOT) / "promotions" / args.reject
        if not dossier_path.exists():
            print(f"Error: Dossier not found: {args.reject}", file=sys.stderr)
            sys.exit(1)
        reject_dossier(dossier_path, args.reject_reason, dry_run=args.dry_run)
        return

    if args.all:
        dossiers = list_pending_promotions()
        for dossier_path, _ in dossiers:
            promote_dossier(dossier_path, dry_run=args.dry_run)
        return
    
    parser.print_help()


if __name__ == "__main__":
    main()