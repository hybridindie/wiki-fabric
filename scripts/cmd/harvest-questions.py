#!/usr/bin/env python3
# harvest-questions.py — concept open_questions → proposed question pages (#88)
#
# Concepts carry an "## Open Questions" section (written by synthesize.py:
# what is unknown or unverified). That is the last anyone sees of them —
# no consumer surfaces them, so unknowns decay silently. This pass reads
# every concept's open questions and proposes `question` pages:
#
#   proposed (staging):  registry/question-proposals/question-<hash>.md
#   applied (human):     questions/question-<hash>.md  (priority + rationale)
#
# Deterministic (0 tokens). Hashed ids make re-harvest idempotent: a question
# already proposed/applied (by id) is skipped, never duplicated. Priority
# derives from the underlying claims' confidence (low confidence → higher
# priority: least-verified unknowns are the sharpest signal).
#
# Human-gated like domains: propose → gate lists → promote-questions --apply.
#
# Usage:
#   python3 scripts/cmd/harvest-questions.py [--dry-run] [--project <slug>]

import sys
import sys as _s, pathlib as _p
_HERE = _p.Path(__file__).resolve().parent
for _dir in (_HERE, _HERE.parent / "lib"):
    if str(_dir) not in _s.path:
        _s.path.insert(0, str(_dir))
import hashlib
import re
import argparse
from pathlib import Path
from datetime import date
from wf_common import parse_frontmatter, slugify, yaml_scalar
from fabric_config import CORPUS_ROOT, get_config, actor
from wf_common import now_iso_utc as _dt_iso

CONCEPTS_DIR = CORPUS_ROOT / "concepts"
PROPOSALS_DIR = CORPUS_ROOT / "registry" / "question-proposals"
QUESTIONS_DIR = CORPUS_ROOT / "questions"

OPEN_Q_HEADER = "## Open Questions"
OPEN_Q_NONE = ("_none identified_", "_None identified_")


def harvest_concept(concept_path, dry_run=False):
    """Propose question pages for one concept's open questions.
    Returns (proposed_count, skipped_count)."""
    fm, body = parse_frontmatter(concept_path)
    if fm.get("type") != "concept":
        return 0, 0
    stem = fm.get("id") or concept_path.stem
    claims = fm.get("claims") or []

    questions, in_section = [], False
    for line in body.splitlines():
        if line.startswith("## "):
            in_section = line.strip() == "## Open Questions"
            continue
        if in_section and line.strip().startswith("- "):
            q = line.strip()[2:].strip()
            # placeholders (templates, yaml artifacts) are not questions
            if not q or q in OPEN_Q_NONE or q.startswith("_") or q.startswith("{"):
                continue
            questions.append(q)

    if not questions:
        return 0, 0

    # Priority from the underlying claims' confidence (#88 shape): low/medium
    # confidence claims → P1 (unverified ground), high → P2 (backlog).
    confs = []
    for c in (claims or []):
        cp = CORPUS_ROOT / "evidence" / "claims" / f"{str(c).strip('[]').split('|')[0]}.md"
        if cp.exists():
            cfm, _ = parse_frontmatter(cp)
            if isinstance(cfm, dict):
                confs.append(str(cfm.get("confidence", "")).lower())
    low = sum(1 for c in confs if c in ("low", "medium")) if confs else 0
    priority = "P1" if (not confs or low) else "P2"

    proposed = skipped = 0
    for q in questions:
        qhash = hashlib.sha256(q.encode("utf-8")).hexdigest()[:10]
        qid = f"question-{qhash}"
        rel_target = PROPOSALS_DIR / f"{qid}.md"
        # already proposed or already applied → skip (idempotent)
        if rel_target_exists(qid):
            skipped += 1
            continue
        if dry_run:
            print(f"  [dry-run] would propose {qid}: {q[:70]}")
            proposed += 1
            continue
        PROPOSALS_DIR.mkdir(parents=True, exist_ok=True)
        rel_target = PROPOSALS_DIR / f"{qid}.md"
        rel_target.write_text(f"""---
type: question
id: {qid}
title: {yaml_scalar(q[:140])}
question: {yaml_scalar(q)}
priority: {priority}
rationale: "Open question raised by concept [[{stem}]] — what is unknown or unverified about it"
related:
  - "[[{stem}]]"
{actor_block()}status: proposed
created: {date.today().isoformat()}
---

# {qid}

{q}

**Raised by:** [[{stem}]] (concept open-questions harvest)
**Priority:** {priority} — derived from underlying claim confidence
**Answering:** a new claim with `relations: [{{type: answers, target: [[{qid}]]}}]` closes this question (flip status: answered)
""")
        proposed += 1
    return proposed, skipped


def rel_target_exists(qid):
    """Question already proposed (staging) or applied (canonical)."""
    return (PROPOSALS_DIR / f"{qid}.md").exists() or (QUESTIONS_DIR / f"{qid}.md").exists()


def actor_block():
    # One actor chain (#155-B): fabric_config.actor falls back internally —
    # no hand-built "agent/unknown/unknown" laundering a missing owner.
    _actor = actor(get_config(), "agent")
    return f'generated: {{ by: "{_actor}", at: "{_dt_iso()}" }}\n'


def harvest_all(project=None, dry_run=False):
    """Harvest every concept (optionally scoped to a project namespace)."""
    total_proposed = total_skipped = 0
    for cp in sorted(CONCEPTS_DIR.glob("concept-*.md")):
        if project and not cp.name.startswith(f"concept-{project}"):
            continue
        p, s = harvest_concept(cp, dry_run=dry_run)
        total_proposed += p
        total_skipped += s
        if p or s:
            print(f"{cp.stem}: {p} proposed, {s} already known")
    print(f"\nHarvest summary: {total_proposed} proposed, {total_skipped} known")
    if total_proposed and not dry_run:
        print("Next: wf gate lists them; apply with promote-questions --apply <id>")
    return total_proposed


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Harvest concept open_questions into proposed question pages (0 tokens)")
    parser.add_argument("--project", help="Scope to one project namespace")
    parser.add_argument("--dry-run", action="store_true", help="Show without writing")
    args = parser.parse_args()
    harvest_all(project=args.project, dry_run=args.dry_run)


if __name__ == "__main__":
    main()