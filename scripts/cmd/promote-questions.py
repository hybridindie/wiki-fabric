#!/usr/bin/env python3
# promote-questions.py — apply human-approved question proposals (#88)
#
# The human-gated second half of harvest-questions: staged proposals in
# registry/question-proposals/ move to canonical questions/ on --apply,
# or are rejected with a required reason (--reject, mirroring the
# promotion reject path).
#
# Usage:
#   python3 scripts/cmd/promote-questions.py --list
#   python3 scripts/cmd/promote-questions.py --apply <id.md>   [--dry-run]
#   python3 scripts/cmd/promote-questions.py --reject <id> --reason "..."

import sys
import sys as _s, pathlib as _p
_HERE = _p.Path(__file__).resolve().parent
for _dir in (_HERE, _HERE.parent / "lib"):
    if str(_dir) not in _s.path:
        _s.path.insert(0, str(_dir))
import argparse
from pathlib import Path
from datetime import date
from wf_common import parse_frontmatter
from fabric_config import CORPUS_ROOT

import layout

PROPOSALS_DIR = layout.registry(CORPUS_ROOT) / "question-proposals"
QUESTIONS_DIR = layout.questions(CORPUS_ROOT)


def list_pending():
    out = []
    if not PROPOSALS_DIR.exists():
        return out
    for p in sorted(PROPOSALS_DIR.glob("question-*.md")):
        fm, _ = parse_frontmatter(p)
        if str(fm.get("status", "")).lower() == "proposed":
            out.append((p, fm))
    return out


def list_open_questions():
    """Canonical open questions (the surfaced layer)."""
    out = []
    if not QUESTIONS_DIR.exists():
        return out
    for p in sorted(QUESTIONS_DIR.glob("question-*.md")):
        fm, _ = parse_frontmatter(p)
        if str(fm.get("status", "")).lower() in ("", "open"):
            out.append((p, fm))
    return out


def apply_question(p, dry_run=False):
    """Merge one proposal into canonical questions/ (status: open)."""
    fm, body = parse_frontmatter(p)
    if fm.get("type") != "question":
        print(f"Not a question page: {p}")
        return False
    qid = fm.get("id") or p.stem
    # S1/#159 trio: domain-bound questions live under domains/<d>/questions/
    # (canonical via the shared parser); unbound go flat. Same contract the
    # concept relocation follows.
    import ontology as _o
    dest_dir = QUESTIONS_DIR
    try:
        onto = _o.parse((layout.domains(CORPUS_ROOT) / "ontology.md")
                        .read_text(encoding="utf-8", errors="replace")
                        if (layout.domains(CORPUS_ROOT) / "ontology.md").exists() else "")
        raw = fm.get("domain") or []
        if isinstance(raw, str):
            raw = [x.strip() for x in raw.strip("[]").split(",")]
        canon = sorted(_o.canonicalize([str(d).strip() for d in raw if str(d).strip()], onto))
        if canon:
            dest_dir = layout.domain_home(CORPUS_ROOT, canon[0], "domain_questions_home")
    except (OSError, KeyError):
        pass  # vocabulary-less corpus: flat (the lint gate explains)
    dest = dest_dir / f"{qid}.md"
    if dry_run:
        print(f"[dry-run] would move {p.name} -> {dest}")
        return True
    dest.parent.mkdir(parents=True, exist_ok=True)
    text = p.read_text(encoding="utf-8")
    text = text.replace("status: proposed", "status: open", 1)
    dest.write_text(text, encoding="utf-8")
    p.unlink()
    print(f"applied: {dest}")
    return True


def reject_question(qid, reason, dry_run=False):
    """Reject a proposal: delete the staging page, log the reason."""
    p = PROPOSALS_DIR / f"{qid}.md"
    if not p.exists():
        p = Path(qid)
    if not p.exists():
        print(f"Proposal not found: {qid}")
        return False
    if not str(reason or "").strip():
        print("--reject requires a reason (the audit trail must say why)")
        return False
    if dry_run:
        print(f"[dry-run] would reject {p.name}: {reason}")
        return True
    p.unlink()
    print(f"rejected {qid}: {reason}")
    return True


def main():
    parser = argparse.ArgumentParser(description="Apply human-approved question proposals")
    parser.add_argument("--list", action="store_true", help="List pending proposals")
    parser.add_argument("--open", action="store_true", help="List canonical open questions")
    parser.add_argument("--apply", metavar="PROPOSAL", help="Apply a specific proposal (id or path)")
    parser.add_argument("--reject", metavar="ID", help="Reject a proposal (requires --reason)")
    parser.add_argument("--reason", help="Rejection reason (required with --reject)")
    parser.add_argument("--dry-run", action="store_true", help="Show without writing")
    args = parser.parse_args()

    if args.list:
        pending = list_pending()
        for p, fm in pending:
            print(f"  ✎ {p.stem}  (P: {fm.get('priority')}) {str(fm.get('question', ''))[:70]}")
        if not pending:
            print("  (no pending question proposals)")
        return

    if args.open:
        open_qs = list_open_questions()
        for p, fm in open_qs:
            print(f"  ? {p.stem}  ({fm.get('priority')}) {str(fm.get('question', ''))[:70]}")
        if not open_qs:
            print("  (no open questions)")
        return

    if args.apply:
        p = PROPOSALS_DIR / args.apply if not args.apply.endswith(".md") else Path(args.apply)
        if not p.exists():
            p = Path(args.apply)
        if not p.exists():
            print(f"Proposal not found: {args.apply}")
            sys.exit(1)
        ok = apply_question(p, dry_run=args.dry_run)
        sys.exit(0 if ok else 1)

    if args.reject:
        ok = reject_question(args.reject, args.reason, dry_run=args.dry_run)
        sys.exit(0 if ok else 1)

    parser.print_help()


if __name__ == "__main__":
    main()