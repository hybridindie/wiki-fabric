#!/usr/bin/env python3
"""remember.py — the friction-free memory intake (#177 S6, the auto-memory
lesson): `wf remember <project> --note "..." --kind feedback` lands a
memory-note page — one line, 0 tokens, no LLM, no claim-grade ceremony.

Memory notes are EPHEMERAL by design (auto-expire: default 30d, kind-
dependent); mining reads them as INPUT — a note that repeats across
sessions/projects becomes a promotion candidate (the friction-free path
from correction → pattern). Notes are NOT claims: no source ritual, no
staleness ladder — expiry is the lifecycle.

Kinds (the auto-memory four, lifted):
  feedback   corrections you gave the agent / approaches it confirmed (45d)
  project    ongoing work + decisions mid-flight the code can't show (30d)
  user       operator standing preferences (90d — machine-true, longest)
  reference  where things live outside the repo (90d)
"""

import sys
import sys as _s, pathlib as _p
_HERE = _p.Path(__file__).resolve().parent
for _dir in (_HERE, _HERE.parent / "lib"):
    if str(_dir) not in _s.path:
        _s.path.insert(0, str(_dir))
import argparse
import hashlib
import re
from datetime import date, timedelta
from pathlib import Path

from fabric_config import get_config, get_owner, actor
from wf_common import yaml_scalar, now_iso_utc, project_slug
import layout


KIND_EXPIRY = {"feedback": 45, "project": 30, "user": 90, "reference": 90}
KINDS = tuple(KIND_EXPIRY)


def note_slug(note, kind):
    words = re.findall(r"[a-z]{3,}", note.lower())
    return f"{kind}-" + "-".join(words[:4])[:40]


def write_note(project, note, kind="project", lineage=None, dry_run=False,
               expires=None):
    """Write one memory-note page. Idempotent: the same note text under the
    same project/kind never duplicates (sha-slug). Returns (path, created?)."""
    out_dir = _memory_dir()
    out_dir.mkdir(parents=True, exist_ok=True)
    _project = project_slug(project)
    sid = f"mn-{_project}-{note_slug(note, kind)}"
    sid += "-" + hashlib.sha256(f"{project}:{note}".encode()).hexdigest()[:6]
    dest = out_dir / f"{sid}.md"
    if dest.exists():
        return dest, False
    if dry_run:
        print(f"[DRY] would write {dest.name}")
        return dest, True
    _kind = kind if kind in KIND_EXPIRY else "project"
    exp = expires or (date.today() + timedelta(days=KIND_EXPIRY[_kind])).isoformat()
    who = actor(get_config(), "agent")
    dest.write_text(f"""---
type: memory-note
id: {sid}
title: {yaml_scalar(note[:120])}
description: {yaml_scalar(f"memory note ({_kind}) in {_project}: {note[:100]}")}
generated: {{ by: "{who}", at: "{now_iso_utc()}" }}
project: {_project}
kind: {_kind}
note: {yaml_scalar(note)}
lineage: "{_project}"
expires: {exp}
tags: [memory-note, {_kind}]
created: {date.today().isoformat()}
---

# mn: {note[:80]}

{note}
""")
    return dest, True


def _memory_dir():
    return layout.memory(None)


def expire_notes(dry_run=False, project=None):
    """The ephemeral contract: memory notes past their `expires:` are DELETED
    (not archived — they were never evidence-grade). Mining/promotion surfaces
    read notes before expiry; a promoted candidate carries the note's content
    forward. Returns (expired_count, kept_count)."""
    d = _memory_dir()
    if not d.is_dir():
        return 0, 0
    from wf_common import parse_frontmatter
    expired = kept = 0
    today = date.today()
    for f in sorted(d.glob("mn-*.md")):
        fm, _ = parse_frontmatter(f)
        if project and str(fm.get("project") or "") != project:
            continue
        raw = str(fm.get("expires") or "")[:10]
        try:
            exp = date.fromisoformat(raw)
        except Exception:
            exp = today - timedelta(days=1)  # missing expires = already stale
        if exp < today:
            if not dry_run:
                f.unlink()
            expired += 1
        else:
            kept += 1
    return expired, kept


def main():
    parser = argparse.ArgumentParser(
        description="Log a memory note (friction-free intake, #177 S6)")
    parser.add_argument("project", nargs="?", default=None, help="Project slug")
    parser.add_argument("--note", default=None, help="The note (one line)")
    parser.add_argument("--kind", default="project", choices=KINDS,
                        help="feedback | project | user | reference (default project)")
    parser.add_argument("--expires", default=None, help="Override the kind's default expiry (YYYY-MM-DD)")
    parser.add_argument("--list", action="store_true", help="List standing notes")
    parser.add_argument("--expire", action="store_true", help="Run the expiry sweep (0 tokens)")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if args.list:
        d = _memory_dir()
        if d.is_dir():
            from wf_common import parse_frontmatter
            for f in sorted(d.glob("mn-*.md")):
                fm, _ = parse_frontmatter(f)
                print(f"  {f.name}  [{fm.get('kind')}|{fm.get('project')}] {str(fm.get('note'))[:70]}")
        return 0

    if args.expire:
        expired, kept = expire_notes(dry_run=args.dry_run, project=args.project)
        print(f"Expiry sweep: {expired} expired, {kept} standing" +
              (" [DRY RUN]" if args.dry_run else ""))
        return 0

    if not args.note or not args.project:
        parser.error("provide --note <text> and a project (or use --list / --expire)")
    dest, created = write_note(args.project, args.note, kind=args.kind,
                               dry_run=args.dry_run, expires=args.expires)
    if created:
        print(f"Remembered: {dest.name} [{args.kind}] (expires {args.expires or KIND_EXPIRY.get(args.kind, 30)}d)")
        print("Mining reads standing notes; repeated notes become promotion candidates.")
    else:
        print(f"Already remembered: {dest.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())