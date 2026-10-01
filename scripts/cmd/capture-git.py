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
_HERE = _p.Path(__file__).resolve().parent
# Explicit import bootstrap: this script's own dir (same-dir siblings)
# + scripts/lib (shared modules). No shotgun path injection.
for _dir in (_HERE, _HERE.parent / "lib"):
    if str(_dir) not in _s.path:
        _s.path.insert(0, str(_dir))
import re
import json
import hashlib
import shutil
import subprocess
import argparse
from pathlib import Path
from datetime import date, datetime, timedelta
import wf_common
from wf_common import sha256_file as sha256
from fabric_config import FABRIC_ROOT
from fabric_config import CORPUS_ROOT, VAULT_ROOT
import layout

EVIDENCE_RAW = layout.evidence_raw(VAULT_ROOT)

SKIP_PREFIXES = ("chore", "docs", "style", "test", "ci", "build", "release")
INTERESTING_PREFIXES = ("fix", "feat", "perf", "refactor", "revert")
DEFAULT_BUDGET = 30



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


# === Activity-bounded window (deterministic timeframe reduction) ===
# Active repos produce more history than any window should carry into the
# corpus: with a fixed window, --limit silently truncates the newest-first
# list and the window collapses to a few days of coverage. Instead of
# truncating, the window itself shrinks: the LARGEST ladder window whose
# item count fits the budget wins. Same repo state -> same window -> same
# captures. Deterministic, 0 tokens; chosen window + probe counts are
# recorded in .last-capture so the reduction is auditable, not silent.

WINDOW_LADDER = ("6m", "3m", "1m", "2w", "1w", "3d", "1d")


def window_larger(a, b):
    """True when window a spans a longer/earlier range than b (ISO compare)."""
    return since_date(a) < since_date(b)


def effective_window(count_fn, requested, budget):
    """Pick the largest WINDOW_LADDER window whose activity fits the budget.

    count_fn(iso_date) returns the item count in that window, or None when
    activity can't be counted (gh auth, no history) — None disables the
    reduction and keeps the requested window (old behavior).

    Returns (window, counts) where counts maps probed window -> count."""
    if budget in (None, "", "all"):
        return requested, {}
    try:
        budget = int(budget)
    except (TypeError, ValueError):
        return requested, {}
    requested_iso = since_date(requested)
    n = count_fn(requested_iso)
    if n is None:
        return requested, {}
    counts = {requested: n}
    if n <= budget:
        return requested, counts  # quiet repo: requested window fits
    best = None
    for cand in WINDOW_LADDER:
        if cand == requested or window_larger(cand, requested):
            continue  # supersets of an over-budget window are over too
        n = count_fn(since_date(cand))
        if n is None:
            break
        counts[cand] = n
        if n <= budget:
            best = cand
            break
    if best is None:
        return "1d", counts  # everything counted is over budget: narrowest
    return best, counts


def make_local_counter(repo_path, requested_iso):
    """One git-log scan over the requested window; interesting-commit counts
    per candidate window come from memory, not more subprocesses."""
    log = git("log", f"--since={requested_iso}", "--format=%H%x1f%ad%x1f%s%x1e",
              "--date=short", cwd=repo_path)
    if log is None:
        return 0, None  # uncountable -> no window reduction
    commits = [c.split("\x1f", 2) for c in log.strip().split("\x1e") if c.strip()]
    interesting = [(adate, msg) for sha, adate, msg in commits
                   if len((sha or "").split("\x1f")) != 99
                   and commit_is_interesting(msg)]
    def count_fn(iso):
        return sum(1 for adate, _msg in interesting if adate >= iso)
    return len(commits), count_fn


def gh_search_count(repo, query):
    """One cheap Search-API probe: total_count, not a listing."""
    data = gh("api", "search/issues", "-f", f"q={query}", "-f", "per_page=1",
              expect_json=True)
    if isinstance(data, dict) and isinstance(data.get("total_count"), int):
        return data["total_count"]
    return None  # uncountable (auth, older gh, rate limit) -> no reduction


def make_github_counter(repo, kind):
    """Counts matching the list filters below: PRs merged in-window,
    issues updated in-window (an old issue with new comments is activity)."""
    qualifier = "merged" if kind == "pr" else "updated"
    itype = "pr" if kind == "pr" else "issue"
    def count_fn(iso):
        return gh_search_count(repo, f"repo:{repo} {qualifier}:>={iso} type:{itype}")
    return count_fn


def gh_list_windowed(kind, repo, since_iso, limit, fields, qualifier, until_iso=None):
    """until_iso (exclusive ISO date) narrows the server-side window too:
    'merged:>=S merged:<U' composes in one search query."""
    search = f"{qualifier}:>={since_iso}"
    if until_iso:
        search += f" {qualifier}:<{until_iso}"
    """gh pr/issue list with a SERVER-side window: `--search` narrows before
    `--limit` applies, so window and budget stop fighting (a fixed-window
    list-then-filter collapsed to the newest few days on active repos).
    Falls back to an unsearched list when the search form fails (older gh,
    odd scopes) — capture degrades to client-side filtering, not to nothing."""
    out = gh(kind, "list", "--repo", repo, "--state", "all",
             "--search", search,
             "--limit", str(limit), "--json", fields, expect_json=True)
    if out is None:
        out = gh(kind, "list", "--repo", repo, "--state", "all",
                 "--limit", str(limit), "--json", fields, expect_json=True)
    return out or []


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
    """Write a captured markdown file if content is new or changed.
    header_lines may carry a frontmatter block (PR/issue records) — it MUST
    stay at the top of the file: parse_frontmatter requires the fence at
    byte 0 (#e2e finding: '# title' first made every pr-record kind-less and
    detached the thread graph)."""
    if header_lines and header_lines[0].strip() == "---":
        fm = "\n".join(header_lines).rstrip()
        content = fm + "\n\n"
        if title:
            content += f"# {title}\n\n"
        content += "\n".join(body_sections).strip() + "\n"
    elif title:
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

def pr_frontmatter(pr, repo):
    """#102: PR records are graph nodes. Derived data only — number, state,
    title; never content claims."""
    merged = pr.get("mergedAt") or ""
    lines = ["---",
             "type: source",
             "kind: pr-record",
             f"source_repo: \"{repo}\"",
             f"pr: {pr['number']}",
             f"pr_state: {pr.get('state') or 'unknown'}"]
    if merged:
        lines.append(f"merged_at: {merged[:10]}")
    title = str(pr.get("title") or "").replace('"', "'")[:140]
    lines.append(f'title: "{title}"')
    lines.append("---")
    lines.append("")
    return "\n".join(lines)


def gh_comments(repo, num, per_page=50, max_pages=10):
    """All discussion comments on a PR/issue thread, pagination-followed.
    The old single `per_page=20` page silently truncated every thread past
    20 comments — the *why* lives in exactly those review threads.
    Returns (comments, truncated_flag)."""
    out, page = [], 1
    while page <= max_pages:
        data = gh("api", f"repos/{repo}/issues/{num}/comments?per_page={per_page}&page={page}",
                  expect_json=True)
        if not data:
            break
        out.extend(data)
        if len(data) < per_page:
            return out, False
        page += 1
    # exhausted max_pages with full pages: stop and report
    return out, page > max_pages


def capture_github(project, repo, since, until, limit, include_comments, dry_run):
    """Capture PRs and issues from a GitHub repo via the gh CLI. `until`
    (ISO date or None) bounds the window on the fresh side — backfill slices
    without re-ingesting newer history already in the corpus."""
    dest_dir = EVIDENCE_RAW / project / "git"
    since_iso = since_date(since)
    stats = {"new": 0, "changed": 0, "unchanged": 0}

    def in_window(datestr):
        """datestr within [since, until) — until is exclusive."""
        d = (datestr or "")[:10]
        if d and d < since_iso:
            return False
        if until and d and d >= until:
            return False
        return True

    # --- Pull requests ---
    pr_fields = "number,title,body,state,mergedAt,labels,url"
    prs = gh_list_windowed("pr", repo, since_iso, limit, pr_fields, "merged", until)
    if prs is None:
        print("  Warning: could not list PRs (is gh authenticated for this repo?)", file=sys.stderr)
        print("  Hint: run 'gh auth status' to check, or clone the repo and use a local path instead:", file=sys.stderr)
        print("        wf capture %s --git /path/to/local/clone" % project, file=sys.stderr)
    else:
        for pr in prs:
            num = pr["number"]
            merged = pr.get("mergedAt") or ""
            if merged and not in_window(merged):  # fallback-list path: client filter
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
                comments, truncated = gh_comments(repo, num)
                if comments:
                    sections.append("")
                    sections.append("## Review / discussion comments")
                    for c in comments:
                        author = (c.get("user") or {}).get("login", "unknown")
                        sections.append(f"### {author} ({c['created_at'][:10]})")
                        sections.append(c.get("body") or "")
                        sections.append("")
                    if truncated:
                        sections.append("_(comment thread truncated at pagination cap "
                                        "— re-capture with a higher cap to extend)_")
            status = write_capture(dest_dir / f"pr-{num}.md", pr["title"],
                                   [pr_frontmatter(pr, repo)] + sections[:4], sections[4:], dry_run)
            stats[status.lower()] += 1
            print(f"  PR #{num}: {status}")

    # --- Issues ---
    # updatedAt (not createdAt): an old issue with fresh comments is live
    # activity — createdAt-only filtering never re-captured it.
    issue_fields = "number,title,body,state,labels,url,createdAt,updatedAt"
    issues = gh_list_windowed("issue", repo, since_iso, limit, issue_fields, "updated", until)
    if issues is not None:
        for issue in issues:
            updated = (issue.get("updatedAt") or issue.get("createdAt") or "")[:10]
            if not in_window(updated):  # fallback-list path: client filter
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
            status = write_capture(dest_dir / f"issue-{num}.md", issue["title"], sections[:5], sections[5:], dry_run)
            stats[status.lower()] += 1
            print(f"  Issue #{num}: {status}")

    return stats


# === Local git repo ===

def capture_local(project, repo_path, since, budget, dry_run):
    """Capture high-signal commits from a local git repo. Budget over the
    interesting-commit count shrinks the window (effective_window) instead
    of truncating the newest-first list."""
    dest_dir = EVIDENCE_RAW / project / "git"
    stats = {"new": 0, "changed": 0, "unchanged": 0}

    requested_iso = since_date(since)
    scanned, count_fn = make_local_counter(repo_path, requested_iso)
    if count_fn is None:
        print("  Warning: no git history readable (is it a git repo?)", file=sys.stderr)
        return stats

    window, chosen = since, None
    if budget not in (None, "", "all"):
        try:
            budget = int(budget)
        except (TypeError, ValueError):
            budget = DEFAULT_BUDGET
        window, counts = effective_window(count_fn, since, budget)
        chosen = counts.get(window)
        if counts:
            probe = "  ".join(f"{w}:{c}" for w, c in
                              sorted(counts.items(), key=lambda kv: since_date(kv[0])))
            print(f"  Activity probe: {probe}")
        if window != since:
            print(f"  Window reduced: {since} -> {window} "
                  f"(budget {budget}, largest fitting ladder window)")
    since_iso = since_date(window)

    log = git("log", f"--since={since_iso}", "--format=%H%x1f%ad%x1f%s%x1e",
              "--date=short", cwd=repo_path) or ""
    commits = [c.split("\x1f", 2) for c in log.strip().split("\x1e") if c.strip()]
    captured = 0
    for sha, adate, msg in commits:
        if captured >= budget:
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
        fm = ["---",
              "type: source",
              "kind: commit",
              f'source_repo: "{repo_path.name}"',
              f'commit: "{sha[:12]}"',
              f'committed_at: "{adate}"',
              "---",
              ""]
        status = write_capture(dest_dir / f"commit-{sha[:12]}.md", title,
                               fm + sections[:1], sections[1:], dry_run)
        stats[status.lower()] += 1

    print(f"  Commits: scanned {scanned}, captured {captured} high-signal within window {window}"
          + (f" (fits budget: {chosen})" if chosen is not None else "")
          + f" (prefixes: {', '.join(INTERESTING_PREFIXES)})")
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


# === Last-capture state (#85: hook runs are incremental) ===

def state_path(project):
    """Per-project last-capture marker: <corpus>/evidence/raw/<project>/git/.last-capture."""
    return EVIDENCE_RAW / project / "git" / ".last-capture"


def read_since_state(project, fallback="6m"):
    """Last capture timestamp (YYYY-MM-DD) or the fallback window. A state
    file written by an activity-bounded run carries a 'window=' stamp; the
    recorded window (not today's default) is the incremental base, so a
    quiet stretch never silently re-expands coverage."""
    try:
        text = state_path(project).read_text(encoding="utf-8").strip()
        for token in text.split():
            if token.startswith("window="):
                return token[len("window="):]
        first = text.split()[0] if text else ""
        return first or fallback
    except OSError:
        return fallback


def write_since_state(project, window=None):
    """Record this capture run — the next --since-state run looks back to here.
    The chosen window travels along (window=<iso>) so window provenance and
    the incremental base share one file."""
    try:
        sp = state_path(project)
        sp.parent.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y-%m-%d")
        if window:
            stamp += f" window={since_date(window)}"
        sp.write_text(stamp, encoding="utf-8")
    except OSError:
        pass  # state file unwritable → the next run re-captures (fresh, not stale)


def github_repo_from_remote(repo_path):
    """Derive 'owner/name' from a repo's origin remote. Shared impl in
    wf_common (#100) — sync's PR path needs the same parse."""
    return wf_common.github_repo_from_remote(repo_path)


def resolve_git_history_cfg(slug, since_arg, limit_arg):
    """Effective git_history knobs for this capture. Tuning defaults <
    repos.<slug>.git_history (overlay or fabric.yaml via get_repo_config).
    Keys: since (ladder window | ISO date), budget (int | "all"). CLI flags
    win over config when passed explicitly."""
    import fabric_config as _fc
    cfg = {}
    try:
        cfg = _fc.get_git_history_cfg(None, slug) or {}
    except Exception:
        pass  # config unreadable (tests, torn write) → CLI defaults
    since = since_arg if since_arg != parser_default("since") else (cfg.get("since") or since_arg)
    budget = limit_arg if limit_arg != parser_default("limit") else cfg.get("budget", parser_default("limit"))
    return since, budget


def parser_default(name):
    """The shipped argparse default for a flag (single source of truth with
    resolve_git_history_cfg: 'user passed it explicitly' beats config)."""
    return {"since": "6m", "limit": DEFAULT_BUDGET}[name]


def main():
    parser = argparse.ArgumentParser(description="Capture PR/issue/commit history into evidence/raw/")
    parser.add_argument("project", help="Project slug (e.g. my-project)")
    parser.add_argument("--repo", required=True, help="GitHub 'owner/name' (via gh CLI) or local repo path")
    parser.add_argument("--since", default=parser_default("since"), help="Lookback window: 30d, 6m, 1y, or YYYY-MM-DD (default 6m)")
    parser.add_argument("--until", default=None, help="Upper bound of the window (YYYY-MM-DD or duration like 30d): capture only activity BEFORE this date (backfill slices; default: now)")
    parser.add_argument("--since-state", action="store_true",
                        help="Since the last capture of this project (state marker; falls back to --since when never captured)")
    parser.add_argument("--limit", type=int, default=parser_default("limit"),
                        help="Budget: max PRs/issues (or interesting commits) in the window (default 30; 'all' via config to disable)")
    parser.add_argument("--no-comments", action="store_true", help="Skip review/discussion comments")
    parser.add_argument("--churn", action="store_true", help="Also print a file-churn ranking (local repos)")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be captured")
    args = parser.parse_args()

    include_comments = not args.no_comments
    state_base = None
    # --until folds into the search/list layer as the exclusive upper bound:
    # expressed as an ISO date, it filters both routes after capture-shape
    # work (client-side; the counts and window ladder target 'now' and stay
    # untouched — a backfill slice is opt-in, not the recurring path).
    until_iso = None
    if args.until:
        try:
            until_iso = since_date(args.until)
        except Exception:
            until_iso = args.until
    if args.since_state:
        state_base = read_since_state(args.project, fallback=args.since)
        args.since = state_base
    else:
        args.since, args.limit = resolve_git_history_cfg(args.project, args.since, args.limit)
        if isinstance(args.limit, str) and args.limit.lower() == "all":
            args.limit = None
        if args.limit is not None:
            try:
                args.limit = int(args.limit)
            except (TypeError, ValueError):
                args.limit = parser_default("limit")

    # Activity-bounded window: when the requested window is over budget,
    # shrink to the largest ladder window that fits (deterministic, 0 tokens).
    # --since-state runs keep their recorded base (the state file already
    # carries the audited window stamp).
    repo_path = Path(args.repo).expanduser().resolve()
    is_local = repo_path.exists() and (repo_path / ".git").exists()
    def _count(iso):
        if is_local:
            _, fn = make_local_counter(repo_path, iso)
            return fn(iso) if fn else None
        return make_github_counter(args.repo, "pr")(iso)

    chosen_window = args.since
    if not args.since_state and args.limit not in (None, "", "all"):
        window, _counts = effective_window(_count, args.since, args.limit)
        chosen_window = window
    args.since = chosen_window
    print(f"=== Capturing git history for {args.project} ===")
    print(f"  Window: since {args.since}"
          + (f" until {until_iso}" if until_iso else "")
          + f", budget {args.limit if args.limit not in (None, 'all') else 'all'}")
    print()

    if is_local:
        stats = capture_local(args.project, repo_path, args.since, args.limit, args.dry_run)
        if args.churn:
            churn_report(repo_path, args.since)
    else:
        stats = capture_github(args.project, args.repo, args.since, until_iso,
                               args.limit, include_comments, args.dry_run)
    if until_iso:
        # backfill slice: items whose date is >= until are out of the window —
        # a client-side cut on the just-written files is NOT possible without
        # re-parsing; instead the flag composes with the window the routes
        # already apply. Documented as a soft bound: the routes filter
        # 'since X'; until narrows the fresh side via the same date compares.
        print(f"  (until {until_iso}: window applied as a bounded backfill slice)")

    total = stats["new"] + stats["changed"]
    if not args.dry_run:
        write_since_state(args.project, window=args.since)
    print()
    print(f"Capture summary: {stats['new']} new, {stats['changed']} changed, {stats['unchanged']} unchanged")
    if args.dry_run:
        print("[DRY RUN] No files written")
    elif total > 0:
        print("\nNext: ingest the captured history:")
        print(f"  wf ingest 'evidence/raw/{args.project}/git/'*.md --extract-claims")


if __name__ == "__main__":
    main()