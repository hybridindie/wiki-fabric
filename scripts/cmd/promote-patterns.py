#!/usr/bin/env python3
# promote-patterns.py — apply human-approved chat-mined pattern candidates (#89)
#
# The gated second half of mine-chats --propose: staged candidates in
# patterns/_inbox/ move to canonical patterns/ on --apply, or are rejected
# with a required reason (--reject). Mirrors promote-questions.py.
#
# Usage:
#   python3 scripts/cmd/promote-patterns.py --list
#   python3 scripts/cmd/promote-patterns.py --apply <candidate> [--dry-run]
#   python3 scripts/cmd/promote-patterns.py --reject <id> --reason "..."

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

INBOX_DIR = CORPUS_ROOT / "patterns" / "_inbox"
PATTERNS_DIR = CORPUS_ROOT / "patterns"


def list_pending():
    """Staged chat-mined candidates awaiting human review."""
    out = []
    if not INBOX_DIR.exists():
        return out
    for p in sorted(INBOX_DIR.glob("*.md")):
        fm, _ = parse_frontmatter(p)
        if str(fm.get("status", "")).lower() == "candidate":
            out.append((p, fm))
    return out


def apply_candidate(p, dry_run=False):
    """Move one inbox candidate into canonical patterns/ (status: candidate
    kept — the pattern maturity gates still apply from here)."""
    fm, _ = parse_frontmatter(p)
    if fm.get("type") != "pattern":
        print(f"Not a pattern candidate: {p}")
        return False
    cid = fm.get("id") or p.stem
    dest = PATTERNS_DIR / f"{cid}.md"
    if dry_run:
        print(f"[dry-run] would move {p.name} -> {dest}")
        return True
    dest.parent.mkdir(parents=True, exist_ok=True)
    text = p.read_text(encoding="utf-8")
    text = text.replace("tags: [chat-mined, inbox]", "tags: [chat-mined]", 1)
    dest.write_text(text, encoding="utf-8")
    p.unlink()
    print(f"applied: {dest} — the pattern maturity gates now govern it (review_after applies)")
    return True


def reject_candidate(qid, reason, dry_run=False):
    """Reject: delete the staging page; the reason goes in the log."""
    p = INBOX_DIR / f"{qid}.md"
    if not p.exists():
        p = Path(qid)
    if not p.exists():
        print(f"Candidate not found: {qid}")
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
    parser = argparse.ArgumentParser(description="Apply/reject chat-mined pattern candidates (human-gated)")
    parser.add_argument("--list", action="store_true", help="List pending candidates")
    parser.add_argument("--apply", metavar="CANDIDATE", help="Apply a specific candidate (id)")
    parser.add_argument("--reject", metavar="ID", help="Reject a candidate (requires --reason)")
    parser.add_argument("--reason", help="Rejection reason (required with --reject)")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if args.list:
        pending = list_pending()
        for p, fm in pending:
            print(f"  ✎ {p.stem}  ({fm.get('origin', 'chat-mined')}) "
                  f"{str(fm.get('title', ''))[:70]}")
        if not pending:
            print("  (no pending candidates — mine with: wf mine chats <project> --propose)")
        return

    if args.apply:
        p = INBOX_DIR / (args.apply if args.apply.endswith(".md") else f"{args.apply}.md")
        if not p.exists():
            print(f"Candidate not found: {args.apply}")
            sys.exit(1)
        ok = apply_candidate(p, dry_run=args.dry_run)
        sys.exit(0 if ok else 1)

    if args.reject:
        ok = reject_candidate(args.reject, args.reason, dry_run=args.dry_run)
        sys.exit(0 if ok else 1)

    parser.print_help()


if __name__ == "__main__":
    main()