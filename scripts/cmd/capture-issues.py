#!/usr/bin/env python3
# capture-issues.py — Tracker capture (#176): issues + comment threads as
# evidence (the #116 spike's proven shape — kind: issue-record).
#
# Usage:
#   python3 scripts/cmd/capture-issues.py <project-slug> --repo owner/name [--tracker github]
#   ... --since-state          # incremental from the last capture stamp
#   ... --since 6m --until 2026-01-01   # bounded backfill slice (separate flow, never composes with --since-state)
#   ... --limit 30             # budget: the window shrinks (effective_window), never truncates
#   ... --dry-run
#
# The spike (syntheses/spike-tracker-capture-signal-density.md) validated:
# issues carry the DESIGN RATIONALE no other channel records (PRs = what,
# chats = how, issues = why); shaping uses the issue-record frontmatter;
# comment threads carry the review arc (the same machinery capture-git ports).

import sys
import sys as _s, pathlib as _p
_HERE = _p.Path(__file__).resolve().parent
for _dir in (_HERE, _HERE.parent / "lib"):
    if str(_dir) not in _s.path:
        _s.path.insert(0, str(_dir))
import re
import hashlib
import json
import argparse
import subprocess
from datetime import datetime
from pathlib import Path

from fabric_config import get_config, FABRIC_ROOT
import layout

# the shared machinery lives in capture-git.py (dashed name) — spec-load it
# so this script works as both a subprocess entry and an importable module
import importlib.util as _ilu
_cg_path = _HERE / "capture-git.py"
_specs = _ilu.spec_from_file_location("capture_git", _cg_path)
capture_git = _ilu.module_from_spec(_specs)
sys.modules["capture_git"] = capture_git
_specs.loader.exec_module(capture_git)
cg = capture_git
VAULT_ROOT = capture_git.VAULT_ROOT
EVIDENCE_RAW = capture_git.EVIDENCE_RAW
gh_list_windowed = capture_git.gh_list_windowed
gh_comments = capture_git.gh_comments
since_date = capture_git.since_date
effective_window = capture_git.effective_window
make_github_counter = capture_git.make_github_counter
write_capture = capture_git.write_capture
read_since_state = capture_git.read_since_state
write_since_state = capture_git.write_since_state
state_path = capture_git.state_path

# deterministic density pre-filter (the spike): capture issues with discussion
# or acceptance criteria; skip drive-by chores. Extends as encountered.
INTERESTING_SIGNALS = [
    r"## (?:Report|Problem|Context|Design|Rationale|Proposal)",
    r"why\b", r"because\b", r"rationale", r"decision", r"rejected",
    r"acceptance criteri", r"tradeoff", r"alternative",
    r"should \b", r"must \b", r"invariant",
]
CHORE_SIGNALS = [
    r"^bump\b", r"^chore\b", r"typo", r"release v\d", r"^docs?:\s*(fix|typos?)\b",
]
MIN_BODY_LEN = 240  # shorter bodies without signals = chores


def issue_is_interesting(body, labels, comments_count):
    """Deterministic density filter (#116 spike): signal-bearing issues only.
    labels carry triage (epic/bug/enhancement = keep); text signals carry the
    rest; chore markers + tiny signal-less bodies skip."""
    joined = str(body or "").lower()
    if comments_count and comments_count > 0:
        return True  # a discussion thread IS signal (the review arc)
    for pat in CHORE_SIGNALS:
        if re.search(pat, joined[:200]):
            return False
    for pat in INTERESTING_SIGNALS:
        if re.search(pat, joined):
            return True
    return len(joined) >= MIN_BODY_LEN


def issue_frontmatter(issue, repo):
    lines = ["---",
             "type: source",
             "kind: issue-record",
             f'source_repo: "{repo}"',
             f"issue: {issue['number']}",
             f"issue_state: {issue.get('state') or 'unknown'}",
             f"created: {(issue.get('createdAt') or '')[:10]}"]
    closed = (issue.get("closedAt") or "")[:10]
    if closed:
        lines.append(f"closed_at: {closed}")
    title = str(issue.get("title") or "").replace('"', "'")[:140]
    lines.append(f'title: "{title}"')
    lines.append("---")
    lines.append("")
    return "\n".join(lines)


def capture_issue(project, issue, repo, dest_dir, include_comments, dry_run):
    """Shape + write ONE issue record (the spike's exact shape). Returns
    status + truncated flag."""
    num = issue["number"]
    sections = [
        "## Metadata",
        f"- Issue: #{num} — {issue.get('title', '')}",
        f"- State: {issue.get('state')}",
        f"- URL: {issue.get('url', '')}",
        f"- Updated: {(issue.get('updatedAt') or issue.get('createdAt') or '')[:10]}",
    ]
    labels = [l.get("name") for l in (issue.get("labels") or []) if isinstance(l, dict) and l.get("name")]
    if labels:
        sections.append(f"- Labels: {', '.join(labels)}")
    sections.append("")
    sections.append("## Report")
    sections.append(issue.get("body") or "(no body)")
    truncated = False
    if include_comments:
        comments, truncated = gh_comments(repo, num)
        if comments:
            sections.append("")
            sections.append("## Discussion")
            for c in comments:
                author = (c.get("user") or {}).get("login", "unknown")
                sections.append(f"### {author} ({c['created_at'][:10]})")
                sections.append(c.get("body") or "")
                sections.append("")
            if truncated:
                sections.append("_(comment thread truncated at pagination cap "
                                "— re-capture with a higher cap to extend)_")
    status = write_capture(dest_dir / f"issue-{num}.md", issue.get("title", ""),
                           issue_frontmatter(issue, repo).splitlines(),
                           sections, dry_run)
    return status, truncated


def capture_issues_github(project, repo, since_iso, until_iso, limit,
                          include_comments, dry_run):
    """The GitHub route: server-side windowed issue list → density filter →
    shaped records. Returns stats (mirror of capture_github's)."""
    dest_dir = EVIDENCE_RAW / project / "issues"
    stats = {"new": 0, "changed": 0, "unchanged": 0, "threads_truncated": 0}
    fields = "number,title,body,state,labels,url,createdAt,updatedAt,closedAt,comments"
    issues = gh_list_windowed("issue", repo, since_iso, limit, fields, "updated", until_iso)
    if issues is None:
        return stats
    for issue in issues:
        updated = (issue.get("updatedAt") or issue.get("createdAt") or "")[:10]
        if updated and updated < since_iso:
            continue  # client fallback filter
        if until_iso and updated and updated >= until_iso:
            continue
        c = issue.get("comments")
        n_comments = len(c) if isinstance(c, list) else int(c or 0)
        if not issue_is_interesting(issue.get("body"), issue.get("labels"), n_comments):
            continue
        status, truncated = capture_issue(project, issue, repo, dest_dir,
                                          include_comments, dry_run)
        stats[status.lower()] += 1
        if truncated:
            stats["threads_truncated"] += 1
        print(f"  Issue #{issue['number']}: {status}"
              + (" (thread truncated)" if truncated else ""))
    return stats


def main():
    parser = argparse.ArgumentParser(
        description="Capture tracker issues + comment threads into evidence/raw/ (#176)")
    parser.add_argument("project", help="Project slug (must be connected)")
    parser.add_argument("--repo", required=True, help="GitHub 'owner/name'")
    parser.add_argument("--tracker", default="github", choices=["github"],
                        help="Tracker kind (github proven; Linear deferred)")
    parser.add_argument("--since", default=None, help="Window: 30d/6m/1y or YYYY-MM-DD (default: --since-state's recorded window, else 6m)")
    parser.add_argument("--until", default=None, help="Upper bound (YYYY-MM-DD or 30d): one bounded backfill slice — separate flow, does not compose with --since-state")
    parser.add_argument("--since-state", action="store_true", help="Incremental from the last capture stamp")
    parser.add_argument("--limit", type=int, default=30, help="Budget (the window shrinks to fit, never truncates)")
    parser.add_argument("--no-comments", action="store_true", help="Skip discussion threads")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    # Unknown-slug guard (#167 contract shared with capture/capture-git)
    connected = set()
    try:
        import fabric_config as _fc
        connected = set(_fc.get_all_repo_names(_fc.get_config()))
    except Exception:
        connected = set()
    if connected and args.project not in connected:
        print(f"Error: '{args.project}' is not a connected project", file=sys.stderr)
        print(f"  connected: {', '.join(sorted(connected))}", file=sys.stderr)
        sys.exit(3)

    until_iso = None
    if args.until:
        try:
            until_iso = since_date(args.until)
        except Exception:
            until_iso = args.until

    if args.since_state:
        args.since = read_since_state(f"{args.project}-issues", fallback=args.since or "6m")
    else:
        args.since = args.since or "6m"

    # activity-bounded window (shrink-not-truncate; --since-state keeps its base)
    repo_path = Path(args.repo)
    def _count(iso):
        return make_github_counter(args.repo, "issue")(iso)
    if not args.since_state and args.limit:
        window, _counts = effective_window(_count, args.since, args.limit)
        args.since = window
    since_iso = since_date(args.since)

    print(f"=== Capturing tracker issues for {args.project} ===")
    print(f"  Window: since {args.since}"
          + (f" until {until_iso}" if until_iso else "")
          + f", budget {args.limit}")
    print()

    stats = capture_issues_github(args.project, args.repo, since_iso, until_iso,
                                  args.limit, not args.no_comments, args.dry_run)

    if not args.dry_run:
        write_since_state(f"{args.project}-issues", window=args.since,
                          truncated=stats.get("threads_truncated", 0))
    print()
    print(f"Capture summary: {stats['new']} new, {stats['changed']} changed, "
          f"{stats['unchanged']} unchanged"
          + (f", {stats['threads_truncated']} thread(s) truncated at the comment-page cap"
             if stats.get("threads_truncated") else ""))
    if args.dry_run:
        print("[DRY RUN] No files written")
    elif (stats["new"] + stats["changed"]) > 0:
        print("\nNext: ingest the captured issues:")
        print(f"  wf ingest 'evidence/raw/{args.project}/issues/'*.md --extract-claims")

    # Exit contract (the #167/#156 table): 2 = drift captured, 3 = unknown
    sys.exit(2 if (stats["new"] + stats["changed"]) > 0 else 0)


if __name__ == "__main__":
    main()