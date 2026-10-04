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
import layout

INBOX_DIR = layout.patterns_inbox(CORPUS_ROOT)
PATTERNS_DIR = layout.patterns(CORPUS_ROOT)
ANTI_PATTERNS_DIR = layout.anti_patterns(CORPUS_ROOT)


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
    """Move one inbox candidate into its canonical dir (status: candidate
    kept — the pattern maturity gates still apply from here). type:
    anti-pattern pages go to anti-patterns/ (they never landed there before —
    the unconditional patterns/ dest made promote.py unable to see them)."""
    fm, _ = parse_frontmatter(p)
    if fm.get("type") not in ("pattern", "anti-pattern"):
        print(f"Not a pattern/anti-pattern candidate: {p}")
        return False
    if fm.get("type") == "anti-pattern":
        dest = ANTI_PATTERNS_DIR / f"{fm.get('id') or p.stem}.md"
    else:
        dest = PATTERNS_DIR / f"{fm.get('id') or p.stem}.md"
    if dry_run:
        print(f"[dry-run] would move {p.name} -> {dest}")
        return True
    dest.parent.mkdir(parents=True, exist_ok=True)
    text = p.read_text(encoding="utf-8")
    text = text.replace("tags: [chat-mined, inbox]", "tags: [chat-mined]", 1)
    text = text.replace("tags: [rules-harvest, inbox]", "tags: [rules-harvest]", 1)
    dest.write_text(text, encoding="utf-8")
    p.unlink()
    # #178-B: a rules-harvested candidate RETIRES its source hand file (a
    # tombstone pointer replaces it — the corpus is the truth; the managed
    # export regenerates the rules file; the hand edit source is gone)
    if fm.get("origin") == "rules-file":
        _retire_source_rule(fm, dest)
    print(f"applied: {dest} — the pattern maturity gates now govern it (review_after applies)")
    return True


def _retire_source_rule(fm, canonical_path):
    """Replace the harvested rule's SOURCE file with a pointer to the corpus
    pattern (#178-B): the hand file's project repo + relative path from the
    provenance entry. Best-effort + loud: repo resolution failures print,
    never crash."""
    try:
        from fabric_config import FABRIC_ROOT, get_repo_config
        from wf_common import project_slug
        import re as _re
        provs = fm.get("provenance") or []
        if not provs or not isinstance(provs[0], dict):
            return
        src = str(provs[0].get("source") or "").strip('"')
        # the harvest writes 'repo/relative-path' (twin) or the relpath
        parts = src.split("/", 1)
        if len(parts) != 2:
            return  # no repo prefix → the file lives at an unknown root
        repo_name, rel = parts
        rcfg = get_repo_config(get_repo_config.__self__ if hasattr(get_repo_config, "__self__") else None, repo_name) \
            if False else get_repo_config(getattr(__import__("fabric_config"), "get_config")(), project_slug(repo_name))
        rp = (rcfg or {}).get("path") or ""
        repo = (FABRIC_ROOT / rp).resolve() if rp else None
        if not repo or not (repo / ".claude" / "rules").is_dir() and not (repo / rel).exists():
            return
        target = repo / rel
        if target.exists():
            target.write_text(f"""# RETIRED — promoted to the wiki-fabric corpus
# This rule file was harvested and promoted; the canonical version lives at
# `{canonical_path.name}` and the managed render regenerates it under
# .claude/rules/wiki-fabric/. Edit the PATTERN, not this file.
# (This pointer replaces the hand file — the corpus is the single truth; #178-B)
""")
            subprocess_git_add_commit(repo, target, canonical_path.name)
    except Exception as e:
        print(f"  (rule-retirement skipped: {e})", file=__import__("sys").stderr)


def subprocess_git_add_commit(repo, target, canonical_name):
    import subprocess
    subprocess.run(["git", "-C", str(repo), "add", "--", str(target.relative_to(repo))],
                   capture_output=True)
    subprocess.run(["git", "-C", str(repo), "commit", "-m",
                    f"chore: rule promoted to wiki-fabric corpus ({canonical_name}) — this file is a pointer now"],
                   capture_output=True)


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
    # Tombstone first (#140): rejection becomes negative evidence, not deletion
    try:
        from wiki_lib import tombstones as T
        from fabric_config import get_config, actor
        _cfg = get_config()
        fm_cand, _body = parse_frontmatter(p)
        sig = T._sig_tokens(_body or "")
        T.write_tombstone(CORPUS_ROOT, "chat-mined-pattern", fm_cand.get("id") or p.stem,
                          reason, sig, actor(_cfg, "process", model="promote-patterns"))
    except Exception as e:
        print(f"warn: tombstone not written: {e}", file=sys.stderr)
    p.unlink()
    print(f"rejected {qid}: {reason} (tombstone written to patterns/_rejected/)")
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