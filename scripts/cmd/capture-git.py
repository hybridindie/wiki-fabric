#!/usr/bin/env python3
# capture-git.py — Capture PR/issue history and high-signal commits into evidence/raw/
#
# Git/PR history is a knowledge source: PR descriptions and review threads carry
# the *why* behind changes (problem → intervention rationale), issues carry the
# observed problems, and revert/fix commits seed anti-patterns. This script
# captures that history as markdown files into evidence/raw/<project>/git/ so
# the normal ingest pipeline can compile it into claims — unchanged.
#
# LLM extraction is expensive (1 call per source), so this script applies a
# deterministic pre-filter and only captures high-signal items:
#   - PRs and issues (with review/comment threads)
#   - Revert commits (failed interventions)
#   - Conventional commits: fix:, feat:, perf:, refactor: (skip chore:, docs:, style:, test:, ci:)
#
# Usage:
#   python3 scripts/cmd/capture-git.py <project-slug> --repo owner/name       # GitHub repo (gh CLI)
#   python3 scripts/cmd/capture-git.py <project-slug> --repo /path/to/repo    # Local git repo
#   python3 scripts/cmd/capture-git.py <project-slug> --repo /path --since 6m --limit 50
#   python3 scripts/cmd/capture-git.py <project-slug> --repo /path --dry-run  # Show what would be captured
#
# A local git repo path enables --churn to rank files by commit churn
# (which areas changed most) — useful for prioritizing what to capture/ingest.

import sys
import sys as _s, pathlib as _p
_B = _p.Path(__file__).resolve().parent
for _rel in ("", "cmd", "lib", "eval", "harness"):
    _s.path.insert(0, str(_B.parent / _rel))
import re
import json
import hashlib
import shutil
import subprocess
import argparse
from pathlib import Path
from datetime import date, datetime, timedelta
from fabric_config import FABRIC_ROOT
from fabric_config import CORPUS_ROOT
from fabric_config import CORPUS_ROOT

VAULT_ROOT = CORPUS_ROOT
EVIDENCE_RAW = VAULT_ROOT / "evidence" / "raw"

SKIP_PREFIXES = ("chore", "docs", "style", "test", "ci", "build", "release")
INTERESTING_PREFIXES = ("fix", "feat", "perf", "refactor", "revert")


def sha256(path):
    h = hashlib.sha256()
    h.update(Path(path).read_bytes())
    return h.hexdigest()


def gh(*args, expect_json=False):
    """Run a gh CLI command, return parsed JSON or stdout text."""
    try:
        out = subprocess.run(
            ["gh"] + [str(a) for a in args],
            capture_output=True, text=True, timeout=60,
        )
        if out.returncode != 0:
            return None
        if expect_json:
            return json.loads(out.stdout) if out.stdout.strip() else None
        return out.stdout
    except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError):
        return None


def git(*args, cwd):
    """Run a git command in cwd, return stdout or None."""
    try:
        out = subprocess.run(
            ["git"] + [str(a) for a in args],
            cwd=str(cwd), capture_output=True, text=True, timeout=30,
        )
        return out.stdout if out.returncode == 0 else None
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return None


def since_date(since):
    """Parse '6m', '30d', '2w', '1y' or a YYYY-MM-DD date into an ISO date string."""
    m = re.match(r"^(\d+)([dmyw])$", since.lower())
    if m:
        n, unit = int(m.group(1)), m.group(2)
        delta = {"d": timedelta(days=n), "w": timedelta(weeks=n),
                 "m": timedelta(days=30 * n), "y": timedelta(days=365 * n)}[unit]
        return (datetime.now() - delta).strftime("%Y-%m-%d")
    return since  # assume YYYY-MM-DD


def commit_is_interesting(message):
    """Deterministic filter: conventional-commit prefixes worth capturing."""
    first_line = message.split("\n", 1)[0].strip().lower()
    # explicit revert
    if first_line.startswith("revert") or "this reverts commit" in message.lower():
        return True
    m = re.match(r"^(\w+)(\([^)]*\))?!?:", first_line)
    if not m:
        return False  # non-conventional commits: skip
    return m.group(1) in INTERESTING_PREFIXES


def write_capture(dest, title, header_lines, body_sections, dry_run=False):
    """Write a captured markdown file if content is new or changed."""
    if title:
        content = f"# {title}\n\n" + "\n".join(header_lines).rstrip() + "\n\n" + "\n".join(body_sections).strip() + "\n"
    else:
        content = "\n".join(header_lines).rstrip() + "\n\n" + "\n".join(body_sections).strip() + "\n"
    dest.parent.mkdir(parents=True, exist_ok=True)
    new_hash = hashlib.sha256(content.encode()).hexdigest()
    existing = dest.read_text(encoding="utf-8") if dest.exists() else None
    status = "NEW" if existing is None else ("CHANGED" if sha256_str(existing) != new_hash else "unchanged")
    if status in ("NEW", "CHANGED") and not dry_run:
        dest.write_text(content, encoding="utf-8")
    return status


def sha256_str(s):
    return hashlib.sha256(s.encode()).hexdigest()


# === GitHub (gh CLI) ===

def capture_github(project, repo, since, limit, include_comments, dry_run):
    """Capture PRs and issues from a GitHub repo via the gh CLI."""
    dest_dir = EVIDENCE_RAW / project / "git"
    since_iso = since_date(since)
    stats = {"new": 0, "changed": 0, "unchanged": 0}

    # --- Pull requests ---
    prs = gh("pr", "list", "--repo", repo, "--state", "all", "--limit", str(limit),
             "--json", "number,title,body,state,mergedAt,labels,url", expect_json=True)
    if prs is None:
        print("  Warning: could not list PRs (is gh authenticated for this repo?)", file=sys.stderr)
        print("  Hint: run 'gh auth status' to check, or clone the repo and use a local path instead:", file=sys.stderr)
        print("        wf capture %s --git /path/to/local/clone" % project, file=sys.stderr)
    else:
        for pr in prs:
            merged = pr.get("mergedAt") or ""
            if merged and merged[:10] < since_iso:
                continue
            num = pr["number"]
            sections = [
                f"## Metadata",
                f"- PR: #{num} — {pr['title']}",
                f"- State: {pr.get('state')}{' (merged ' + merged[:10] + ')' if merged else ''}",
                f"- URL: {pr.get('url', '')}",
            ]
            labels = [l["name"] for l in (pr.get("labels") or [])]
            if labels:
                sections.append(f"- Labels: {', '.join(labels)}")
            sections.append("")
            sections.append(f"## Description")
            sections.append(pr.get("body") or "(no description)")
            if include_comments:
                comments = gh("api", f"repos/{repo}/issues/{num}/comments?per_page=20", expect_json=True)
                if comments:
                    sections.append("")
                    sections.append("## Review / discussion comments")
                    for c in comments:
                        author = (c.get("user") or {}).get("login", "unknown")
                        sections.append(f"### {author} ({c['created_at'][:10]})")
                        sections.append(c.get("body") or "")
                        sections.append("")
            status = write_capture(dest_dir / f"pr-{num}.md", pr["title"], sections[:4], sections[4:], dry_run)
            stats[status.lower()] += 1
            print(f"  PR #{num}: {status}")

    # --- Issues ---
    issues = gh("issue", "list", "--repo", repo, "--state", "all", "--limit", str(limit),
                "--json", "number,title,body,state,labels,url,createdAt", expect_json=True)
    if issues is not None:
        for issue in issues:
            if issue.get("createdAt", "")[:10] < since_iso:
                continue
            # gh issue list includes PRs; skip ones with a PR marker
            if any(k in (issue.get("body") or "") for k in ()) and False:
                continue
            num = issue["number"]
            sections = [
                f"## Metadata",
                f"- Issue: #{num} — {issue['title']}",
                f"- State: {issue.get('state')}",
                f"- URL: {issue.get('url', '')}",
            ]
            labels = [l["name"] for l in (issue.get("labels") or [])]
            if labels:
                sections.append(f"- Labels: {', '.join(labels)}")
            sections.append("")
            sections.append("## Report")
            sections.append(issue.get("body") or "(no body)")
            if include_comments:
                comments = gh("api", f"repos/{repo}/issues/{num}/comments?per_page=20", expect_json=True)
                if comments:
                    sections.append("")
                    sections.append("## Discussion")
                    for c in comments:
                        author = (c.get("user") or {}).get("login", "unknown")
                        sections.append(f"### {author} ({c['created_at'][:10]})")
                        sections.append(c.get("body") or "")
                        sections.append("")
            status = write_capture(dest_dir / f"issue-{num}.md", issue["title"], sections[:5], sections[5:], dry_run)
            stats[status.lower()] += 1
            print(f"  Issue #{num}: {status}")

    return stats


# === Local git repo ===

def capture_local(project, repo_path, since, limit, dry_run):
    """Capture high-signal commits from a local git repo."""
    dest_dir = EVIDENCE_RAW / project / "git"
    since_iso = since_date(since)
    stats = {"new": 0, "changed": 0, "unchanged": 0}

    log = git("log", f"--since={since_iso}", "-n", str(limit * 4), "--format=%H%x1f%ad%x1f%s%x1e",
              "--date=short", cwd=repo_path)
    if not log:
        print("  Warning: no git history readable (is it a git repo?)", file=sys.stderr)
        return stats

    commits = [c.split("\x1f", 2) for c in log.strip().split("\x1e") if c.strip()]
    captured = 0
    for sha, adate, msg in commits:
        if captured >= limit:
            break
        if not commit_is_interesting(msg):
            continue
        captured += 1
        # Full commit body + changed files for context
        body = git("show", "--format=%b", "--stat", sha, cwd=repo_path) or ""
        sections = [
            "## Metadata",
            f"- Commit: {sha[:12]} ({adate})",
            "",
            "## Message",
            body.strip() or "(no body)",
        ]
        title = f"commit {sha[:12]} ({adate}): {msg.splitlines()[0]}"
        status = write_capture(dest_dir / f"commit-{sha[:12]}.md", title, sections[:1], sections[1:], dry_run)
        stats[status.lower()] += 1

    print(f"  Commits: scanned {len(commits)}, captured {captured} high-signal (prefixes: {', '.join(INTERESTING_PREFIXES)})")
    return stats


# === Churn analysis (deterministic, prioritizes what to ingest) ===

def churn_report(repo_path, since, top=15):
    since_iso = since_date(since)
    log = git("log", f"--since={since_iso}", "--name-only", "--format=", cwd=repo_path)
    if not log:
        return
    counts = {}
    for line in log.splitlines():
        line = line.strip()
        if line:
            counts[line] = counts.get(line, 0) + 1
    ranked = sorted(counts.items(), key=lambda kv: -kv[1])[:top]
    print(f"\n  Highest-churn files since {since_iso} (prioritize ingesting these):")
    for path, n in ranked:
        print(f"    {n:4d}  {path}")


def main():
    parser = argparse.ArgumentParser(description="Capture PR/issue/commit history into evidence/raw/")
    parser.add_argument("project", help="Project slug (e.g. my-project)")
    parser.add_argument("--repo", required=True, help="GitHub 'owner/name' (via gh CLI) or local repo path")
    parser.add_argument("--since", default="6m", help="Lookback window: 30d, 6m, 1y, or YYYY-MM-DD (default 6m)")
    parser.add_argument("--limit", type=int, default=30, help="Max PRs/issues to fetch (default 30)")
    parser.add_argument("--no-comments", action="store_true", help="Skip review/discussion comments")
    parser.add_argument("--churn", action="store_true", help="Also print a file-churn ranking (local repos)")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be captured")
    args = parser.parse_args()

    include_comments = not args.no_comments

    print(f"=== Capturing git history for {args.project} ===")
    print(f"  Window: since {args.since}, limit {args.limit}")
    print()

    repo = Path(args.repo).expanduser().resolve()
    if repo.exists() and (repo / ".git").exists():
        stats = capture_local(args.project, repo, args.since, args.limit, args.dry_run)
        if args.churn:
            churn_report(repo, args.since)
    else:
        stats = capture_github(args.project, args.repo, args.since, args.limit, include_comments, args.dry_run)

    total = stats["new"] + stats["changed"]
    print()
    print(f"Capture summary: {stats['new']} new, {stats['changed']} changed, {stats['unchanged']} unchanged")
    if args.dry_run:
        print("[DRY RUN] No files written")
    elif total > 0:
        print("\nNext: ingest the captured history:")
        print(f"  wf ingest 'evidence/raw/{args.project}/git/'*.md --extract-claims")


if __name__ == "__main__":
    main()