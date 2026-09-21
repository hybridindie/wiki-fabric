#!/usr/bin/env python3
# export-wiki.py — Generate the human-layer wiki from the evidence corpus.
#
# Produces narrative articles (OpenWiki style) into the vault:
#   wiki/topics/<topic>.md      — mechanism-first, cross-project
#   wiki/projects/<project>.md  — narrative per-repo summary
#   wiki/domains/               — domain hubs (table of contents)
#   wiki/index.md               — staleness dashboard + recent changes
#
# Articles are ASSEMBLED VIEWS over claims — never copied content.
# Claims are cited as numbered footnotes. Generation mode configurable
# per project (mechanical | llm | hybrid) in fabric.yaml wiki.generation.
#
# Staleness: 3-tier citation surfacing (current / ⚠ due / archived).
#
# Usage:
#   python3 scripts/export-wiki.py [--project <slug>] [--dry-run]
#        [--mode mechanical|llm|hybrid]

import sys
import re
from pathlib import Path
from datetime import date, datetime, timedelta

sys.path.insert(0, str(Path(__file__).parent))
from fabric_config import FABRIC_ROOT, get_config, get_all_repo_names, get_repo_config

TODAY = date.today()

# === staleness classification ===
def _staleness(review_after, stale_after):
    """Returns (tier, label, days) where tier is 1=current, 2=due, 3=stale."""
    def _parse(s):
        try:
            from datetime import datetime as dt
            return dt.strptime(str(s).strip()[:10], "%Y-%m-%d").date()
        except Exception:
            return None
    ra = _parse(review_after) if review_after else None
    sa = _parse(stale_after) if stale_after else None
    due = ra or sa
    if not due:
        return 1, None, 0
    overdue = (TODAY - due).days
    if overdue > 90 or (sa and sa <= TODAY):
        return 3, f"stale since {due}", overdue
    if overdue > 0:
        return 2, f"review overdue {overdue}d", overdue
    return 1, None, 0

def _cite_claim(claim_path, idx):
    """Format a footnote citation for a claim. Returns (inline_ref, footnote)."""
    s = claim_path.read_text(encoding="utf-8", errors="replace")
    m = re.search(r"^title: (.+)$|^statement: \"?([^\n]{10,})", s, re.MULTILINE)
    title = (m.group(1) or m.group(2) or "")[:80].strip() if m else claim_path.stem
    ra = re.search(r"review_after: (\S+)", s)
    sa = re.search(r"stale_after: (\S+)", s)
    tier, _, overdue = _staleness(ra.group(1) if ra else None, sa.group(1) if sa else None)
    if tier == 2:
        return f"⚠️[{idx}]", f"[{idx}] {claim_path.stem.replace('claim-','').replace('-',' ')} — {title} ⚠️ review overdue {overdue}d"
    return f"[{idx}]", f"[{idx}] {claim_path.stem} — {title}"

# === topic selection: concepts with >= N claims become topic articles ===
def select_topics(min_claims=6):
    """Group claims by concept → topics with enough evidence become articles."""
    topics = []
    for c in sorted((FABRIC_ROOT / "concepts").glob("concept-*.md")):
        s = c.read_text(encoding="utf-8", errors="replace")
        title = re.search(r"^title: (.+)$", s, re.MULTILINE)
        dom = re.search(r"^domain: \[(.*?)\]", s, re.MULTILINE)
        claims = re.findall(r'\[\[(claim-[^\]]+)\]\]', s)
        if len(claims) >= min_claims:
            topics.append({
                "file": c, "title": title.group(1).strip() if title else c.stem,
                "domain": dom.group(1) if dom else "agent-systems",
                "claims": claims, "body": s.split("---", 2)[2] if s.startswith("---") else s,
            })
    for t in topics:
        t["slug"] = re.sub(r"[^a-z0-9-]+", "-", t["title"].lower()).strip("-")
    return topics


def _project_slug_from_claim(claim_stem):
    m = re.match(r"claim-([a-z0-9-]+?)-", claim_stem)
    return m.group(1) if m else "unknown"


def _generate_topic_article(topic, mode="mechanical", dry_run=False):
    """Generate one topic article from a concept + its claims."""
    title = topic["title"]
    slug = re.sub(r"[^a-z0-9-]+", "-", title.lower()).strip("-")
    claims = []
    for cs in topic["claims"]:
        cp = FABRIC_ROOT / "evidence" / "claims" / f"{cs}.md"
        if cp.exists():
            claims.append(cp)
    if not claims:
        return None, 0
    # staleness tiers
    current, flagged, stale = [], [], []
    for cp in claims:
        s = cp.read_text(encoding="utf-8", errors="replace")
        ra = re.search(r"review_after: (\S+)", s)
        sa = re.search(r"stale_after: (\S+)", s)
        tier, _, _ = _staleness(ra.group(1) if ra else None, sa.group(1) if sa else None)
        statement = re.search(r'statement: "?([^\n]+)', s)
        st = statement.group(1) if statement else ""
        if tier == 3:
            stale.append((cp, st))
        elif tier == 2:
            flagged.append((cp, st))
        else:
            current.append((cp, st))

    lines = [
        "---",
        f"type: wiki-article",
        f"title: \"{title}\"",
        f"domain: [{topic['domain']}]",
        f"review_after: {(TODAY + timedelta(days=120)).isoformat()}",
        f"---",
        f"",
        f"# {title}",
        f"",
    ]
    footnotes = []
    idx = 1
    if current:
        seen_statements = set()
        lines.append(f"{len(current)} current claim(s) support this topic.")
        lines.append("")
        for cp, st in current:
            st_short = st[:80]
            if st_short in seen_statements:
                continue
            seen_statements.add(st_short)
            ref, note = _cite_claim(cp, idx)
            lines.append(f"- {st[:140]} {ref}")
            footnotes.append(note)
            idx += 1
    if flagged:
        lines.append("")
        lines.append(f"## ⚠️ Due for review ({len(flagged)})")
        for cp, st in flagged[:10]:
            ref, note = _cite_claim(cp, idx)
            lines.append(f"- {st[:140]} ⚠️{ref}")
            footnotes.append(note)
            idx += 1
    if stale:
        lines.append("")
        lines.append(f"## Archived (stale)")
        lines.append("<details><summary>These claims informed the topic but may no longer be accurate.</summary>")
        lines.append("")
        for cp, st in stale[:10]:
            ref, note = _cite_claim(cp, idx)
            lines.append(f"- {st[:140]} [{idx}]")
            footnotes.append(note)
            idx += 1
        lines.append("</details>")

    lines.append("")
    lines.append("---")
    lines.append("")
    for fn in footnotes:
        lines.append(fn)
    lines.append("")
    lines.append(f"_Generated from the evidence fabric on {TODAY.isoformat()}. "
                 f"Citations link to claims in evidence/claims/._")

    article = "\n".join(lines) + "\n"
    out_dir = FABRIC_ROOT / "wiki" / "topics"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{slug}.md"
    if not dry_run:
        out_path.write_text(article, encoding="utf-8")
    return out_path, len(claims)


def _generate_project_article(project, config, dry_run=False):
    """Generate a project narrative summary from claims + decisions."""
    rc = get_repo_config(config, project)
    if not rc:
        return None, 0
    claims = sorted((FABRIC_ROOT / "evidence" / "claims").glob(f"claim-{project}-*.md"))
    claims += sorted((FABRIC_ROOT / "evidence" / "claims").glob(f"claim-{project.replace('-', '_')}*.md"))
    # dedup
    seen = set()
    claims = [c for c in claims if not (c.stem in seen or seen.add(c.stem))]
    if not claims:
        return None, 0
    # staleness
    current, flagged, stale = [], [], []
    for cp in claims:
        s = cp.read_text(encoding="utf-8", errors="replace")
        ra = re.search(r"review_after: (\S+)", s)
        sa = re.search(r"stale_after: (\S+)", s)
        tier, _, _ = _staleness(ra.group(1) if ra else None, sa.group(1) if sa else None)
        statement = re.search(r'statement: "?([^\n]+)', s)
        st = statement.group(1) if statement else ""
        if tier == 3:
            stale.append((cp, st))
        elif tier == 2:
            flagged.append((cp, st))
        else:
            current.append((cp, st))

    # decisions
    decisions_dir = FABRIC_ROOT / "projects" / project / "decisions"
    decisions = sorted((decisions_dir := FABRIC_ROOT / "projects" / project / "decisions").glob("*.md")) if decisions_dir.is_dir() else []

    slug = re.sub(r"[^a-z0-9-]+", "-", project).strip("-")
    lines = [
        "---",
        f"type: index",
        f"title: \"{project}: What We Learned\"",
        f"review_after: {(TODAY + timedelta(days=180)).isoformat()}",
        f"---",
        f"",
        f"# {project}: What We Learned",
        f"",
        f"## Current state",
        f"",
        f"{len(current)} verified claim(s) from {len(claims)} analyzed sources.",
    ]
    if flagged:
        lines.append(f"⚠️ {len(flagged)} claim(s) due for review.")
    if stale:
        lines.append(f"❌ {len(stale)} claim(s) stale (archived below).")
    lines += ["", "## Key findings", ""]
    for cp, st in current[:15]:
        ref, note = _cite_claim(cp, len(footnotes) + 1 if 'footnotes' in dir() else 1)
        if 'footnotes' not in dir():
            footnotes = []
        lines.append(f"- {st[:140]} {ref}")
        footnotes.append(note)
    if decisions:
        lines += ["", "## Binding decisions", ""]
        for d in decisions:
            fm_title = re.search(r"^title: (.+)$", d.read_text(), re.MULTILINE)
            lines.append(f"- {fm_title.group(1) if fm_title else d.stem}")
    if stale:
        lines += ["", "## Archived (stale)", ""]
        for cp, st in stale[:10]:
            lines.append(f"- {st[:120]}")
    lines.append("")
    article = "\n".join(lines) + "\n"
    out_dir = FABRIC_ROOT / "wiki" / "projects"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{project}.md"
    if not dry_run:
        out_path.write_text(article, encoding="utf-8")
    return out_path, len(current)


def _generate_index(topics, projects, dry_run=False):
    """Wiki front page: staleness dashboard + topic/project index."""
    report = _scan_staleness()
    lines = [
        "---",
        f"type: index",
        f"title: \"Wiki\"",
        f"generated: {TODAY.isoformat()}",
        f"---",
        f"",
        f"# Wiki",
        f"",
        f"## Review Status",
        f"",
        f"- ✅ Current: {report['current']}",
        f"- ⚠️ Due for review: {len(report['due'])}",
        f"- ⚠️ Overdue: {len(report['overdue'])}",
        f"- ❌ Archived: {len(report['stale'])}",
        f"",
        f"## Topics",
        f""]
    for t in topics:
        lines.append(f"- [[{t['slug']}]] — {t['title']} ({len(t['claims'])} claims)")
    lines += ["", "## Projects", ""]
    for p in projects:
        lines.append(f"- [[{p[0]}]] — {p[0]} ({p[1]} claims)")
    lines += ["", f"_Generated by `wf export wiki` on {TODAY.isoformat()}._"]
    out = FABRIC_ROOT / "wiki" / "index.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    if not dry_run:
        out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out


def _scan_staleness():
    try:
        from review import scan
        return scan()
    except Exception:
        return {"current": 0, "due": [], "overdue": [], "stale": []}


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Generate the human-layer wiki from the evidence corpus")
    parser.add_argument("--project", help="Generate for one project only")
    parser.add_argument("--mode", default=None, choices=["mechanical", "llm", "hybrid"],
                       help="Override generation mode (default: fabric.yaml wiki.generation)")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    config = get_config()
    mode = args.mode or (config.get("wiki", {}).get("generation", {}).get("default") or "hybrid")

    topics = select_topics()
    projects = get_all_repo_names(config)

    print(f"=== Generating wiki ({mode}) ===")
    print(f"  Topics: {len(topics)} | Projects: {len(projects)}")
    print()

    n_topics = 0
    for t in topics:
        out, n = _generate_topic_article(t, mode, dry_run=args.dry_run)
        if out:
            n_topics += 1
            print(f"  topic: {out.name} ({n} claims)")

    n_projects = 0
    for proj in get_all_repo_names(config):
        if proj == "wiki-fabric":
            continue
        out, n = _generate_project_article(proj, config, dry_run=args.dry_run)
        if out:
            n_projects += 1
            print(f"  project: {out.name} ({n} current claims)")

    index = _generate_index(topics, [(p, 0) for p in get_all_repo_names(config)], dry_run=args.dry_run)
    print(f"\n{'[DRY RUN] ' if args.dry_run else ''}Generated {n_topics} topic article(s), "
          f"{n_projects} project article(s), 1 index")
    print(f"Wiki: {FABRIC_ROOT / 'wiki'}/")
    return 0


if __name__ == "__main__":
    sys.exit(main())