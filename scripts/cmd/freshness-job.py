#!/usr/bin/env python3
"""freshness-job.py — Scheduled upstream-freshness cycle (#84).

The corpus-freshness guarantee: hooks capture *local* commit drift on
active machines, but dormant machines let the team corpus carry silently
stale claims — nothing checked captured sources against the LIVE upstream
repos on a cadence. This runner is that check. Designed to run on the
corpus repo's CI (scheduled) or locally (`wf freshness`).

Per connected project (/repos/ in fabric.yaml):
  1. capture-git --repo owner/name --since-state   (new PRs/issues → evidence/raw/; sha256-gated writes)
  2. capture <project> --changed style doc sweep where a local path exists
  3. review --auto-reverify --verify-locators      (mechanical sha256+quote re-verification, 0 tokens)
  4. registry/pending-gate.md surfaces anything needing a human

Deterministic (0 tokens). Re-extraction and claim-writing remain opt-in
per project (repos.<slug>.extract routing) — humans gate canonical edits.

Exit code: 0 when clean; 1 when drift was found and recorded (gate-worthy);
2 on a hard environment failure (no fabric, no gh).
"""
import os
import re
import subprocess
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
for _d in (_HERE, _HERE.parent / "lib"):
    if str(_d) not in sys.path:
        sys.path.insert(0, str(_d))

from wf_common import TIMEOUT_API, TIMEOUT_SCRIPT, github_repo_from_remote_url  # noqa: E402
import fabric_config  # noqa: E402


def _derive_github_slug(repo_path: Path):
    """owner/name from a local repo checkout's origin remote (None elsewhere)."""
    try:
        url = subprocess.run(
            ["git", "-C", str(repo_path), "remote", "get-url", "origin"],
            capture_output=True, text=True, timeout=TIMEOUT_API,
        ).stdout.strip()
        return github_repo_from_remote_url(url)
    except (OSError, subprocess.TimeoutExpired):
        return None


def refresh_git_history(slug, repo_cfg, dry_run=False):
    """Step 1 per project: PR/issue history via capture-git --since-state.
    Route: explicit repos.<slug>.git → GitHub (gh CLI); a local path with a
    GitHub remote → GitHub; a local path without one → capture-git's local
    git-log route (CI runs need no gh auth for this path).

    Returns 'captured' | 'clean' | 'error:<detail>'."""
    script = _HERE / "capture-git.py"
    repo = repo_cfg.get("git") or None
    path = repo_cfg.get("path")
    local_path = None
    if path:
        p = Path(str(path)).expanduser()
        if not p.is_absolute():
            p = (fabric_config.FABRIC_ROOT / p)
        if p.is_dir() and p.exists() or (p / ".git").exists():
            local_path = p.resolve()
    if not repo and local_path:
        repo = _derive_github_slug(local_path)
    if not repo and not local_path:
        return "error:no-source (repos.<slug>.git, or a local path)"
    cmd = [sys.executable, str(script), slug, "--repo",
           str(local_path) if (local_path and not repo) else repo,
           "--since-state"]
    if dry_run:
        cmd.append("--dry-run")
    try:
        r = subprocess.run(cmd, capture_output=True, text=True,
                           timeout=TIMEOUT_SCRIPT)
    except subprocess.TimeoutExpired:
        return "error:capture-git timed out"
    out = (r.stdout or "") + (r.stderr or "")
    if r.returncode != 0:
        return f"error:{out.strip().splitlines()[-1][:120] if out.strip() else 'capture-git failed'}"
    print(out.strip())
    m = re.search(r"Capture summary:\s*(\d+)\s*new,\s*(\d+)\s*changed", out)
    if not m:
        return "error:no summary line from capture-git"
    new = int(m.group(1)) + int(m.group(2))
    return "captured" if new else "clean"


def reverify_claims(slug, dry_run=False):
    """Step 3 per project: mechanical re-verification. Returns (outcome, count)."""
    try:
        from review import scan  # same-dir; single staleness truth (#155 audit)
        report = scan()
    except Exception as e:
        return f"error:{e}", 0
    stale = report.get("overdue", []) + report.get("stale", [])
    if dry_run or not stale:
        return "clean", len(report.get("overdue", []))
    r = subprocess.run(
        [sys.executable, str(_HERE / "review.py"), "--auto-reverify",
         "--project", slug],
        capture_output=True, text=True, timeout=TIMEOUT_SCRIPT)
    if r.returncode != 0:
        return f"error:auto-reverify rc={r.returncode}", len(stale)
    print(r.stdout.strip())
    return "reverified", len(stale)


def main(argv=None):
    import argparse
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("projects", nargs="*", help="Project slugs (default: all connected)")
    parser.add_argument("--dry-run", action="store_true", help="Report drift, write nothing")
    parser.add_argument("--no-reverify", action="store_true", help="Skip step 3 (capture only)")
    args = parser.parse_args(argv)

    config = fabric_config.get_config()
    if config is None:
        print("no fabric — run: wf install", file=sys.stderr)
        return 2
    if not os.environ.get("CI") and subprocess.run(
            ["gh", "auth", "status"], capture_output=True,
            timeout=TIMEOUT_API).returncode != 0:
        print("gh not authenticated — GitHub capture will fail (run: gh auth login)",
              file=sys.stderr)

    all_repos = fabric_config.get_all_repo_names(config)
    slugs = args.projects or all_repos
    unknown = [s for s in slugs if s not in all_repos]
    if unknown:
        print(f"unknown project(s): {', '.join(unknown)} — connected: {', '.join(all_repos)}",
              file=sys.stderr)
        return 2

    drift_found = False
    for slug in slugs:
        rcfg = fabric_config.get_repo_config(config, slug)
        print(f"\n=== {slug} ===")
        git_out = refresh_git_history(slug, rcfg, dry_run=args.dry_run)
        print(f"  git-history: {git_out}")
        if git_out.startswith("error:"):
            print(f"  ({git_out})", file=sys.stderr)
        elif git_out == "captured":
            drift_found = True
        if not args.no_reverify:
            outcome, n = reverify_claims(slug, dry_run=args.dry_run)
            print(f"  reverify:    {outcome} ({n} overdue+stale)")
            if outcome.startswith("error:"):
                print(f"  ({outcome})", file=sys.stderr)
            elif outcome != "clean":
                drift_found = True

    if args.dry_run:
        print("\n(dry-run: nothing written)")
        return 1 if drift_found else 0
    print("\nNext: wf gate — review what the cycle flagged; wf sync push when "
          "the corpus changed.")
    return 1 if drift_found else 0


if __name__ == "__main__":
    sys.exit(main())