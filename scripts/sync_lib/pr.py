"""GitHub PR machinery for corpus sync (#124.5b): gh interaction,
branch/PR creation, evidence-plane auto-merge policy."""
import re
import sys
import subprocess as _sp
from datetime import date
from pathlib import Path

import fabric_config
import wf_common
from wf_common import git_sh as _git_sh, github_repo_from_remote_url
import sync_lib.policy as policy


def _policy_live():
    """The LIVE policy object (the sys.modules entry — single truth at call
    time). A bound module attribute dies when another loader re-registers
    the entry (the #178-suite flake: the patch went to the NEW entry while
    this module's OLD binding served the call)."""
    import sys as _sys
    mod = _sys.modules.get("sync_lib.policy")
    return mod if mod is not None else policy
from sync_lib.policy import classify_change, classify_changes

# gh_run error stash (#100: a swallowed pr-create error once printed
# 'Awaiting human review' while no PR existed).
_GH_LAST_ERR = ""


def _sh(*args, cwd=None):
    return _git_sh(*args, cwd=str(cwd or fabric_config.CORPUS_ROOT))


def gh_run(*args, timeout=60, capture_err=False):  # gh API write — 60s, agent-tunable
    """Run a gh CLI command for the corpus remote; return stdout or None.
    capture_err=True stashes stderr for gh_last_error() (pr-create failure
    diagnostics — a swallowed error once printed 'Awaiting human review'
    while no PR existed, sim finding #8)."""
    import subprocess as _sp
    global _GH_LAST_ERR
    try:
        out = _sp.run(["gh"] + [str(a) for a in args],
                      capture_output=True, text=True, timeout=timeout)
        _GH_LAST_ERR = (out.stderr or "")[-400:] if out.returncode != 0 else ""
        return out.stdout if out.returncode == 0 else None
    except (FileNotFoundError, _sp.TimeoutExpired) as e:
        _GH_LAST_ERR = str(e)
        return None


_GH_LAST_ERR = ""


def _sh(*args, cwd=None):
    return _git_sh(*args, cwd=str(cwd or fabric_config.CORPUS_ROOT))


def gh_last_error():
    return _GH_LAST_ERR

def corpus_github_repo():
    """'owner/name' of the corpus remote, or None (non-GitHub → no PR path)."""
    return wf_common.github_repo_from_remote_url(get_remote())

def change_set_manifests_for_range(base_head, sh=None):
    sh = sh or (lambda *a, **kw: _git_sh(*a, cwd=str(fabric_config.CORPUS_ROOT)))
    sh_used = sh
    """Change-set pages touched since base_head (the PR body's receipt half)."""
    out = _sh("diff", "--name-only", f"{base_head}", "HEAD", "--", "evidence/traces/change-sets/") or []
    if isinstance(out, str):
        out = [l.strip() for l in out.splitlines() if l.strip()]
    return out

def build_pr_body(changes, base_head):
    """PR body = change-set receipts + classified file inventory. Deterministic.
    Entries may be porcelain lines ("XY path") or bare paths (committed-range
    list) — the marker is stripped only when actually present."""
    def _path_of(entry):
        entry = entry if entry is not None else ""
        return entry[3:] if len(entry) > 3 and entry[1:3] in ("M ", "A ", "D ", "R ") else entry
    planes = {}
    for l in changes:
        p = _path_of(l).lstrip('"').rstrip('"')
        planes.setdefault(classify_change(p), []).append(p)
    lines = [
        "---",
        "type: change-set",
        "sync-pr: true",
        f"machine: {_policy_live().machine_name()}",
        f"date: {date.today().isoformat()}",
        "---",
        "",
        "# Corpus sync",
        "",
        f"Machine: `{_policy_live().machine_name()}` — one PR per `sync push` (#100).",
        "",
        "## Change-set receipts",
        "",
    ]
    # call-time module lookup (the #178 seam: test patches bind the live
    # sys.modules entry, not this module's stale self-binding)
    import sys as _sys
    _pr_live = _sys.modules.get(__name__) or sys.modules[__name__]
    cs = _pr_live.change_set_manifests_for_range(base_head)
    if cs:
        for c in cs[:20]:
            lines.append(f"- `{c}`")
        if len(cs) > 20:
            lines.append(f"- … and {len(cs) - 20} more")
    else:
        lines.append("_(no change-set traces in this range)_")
    lines += ["", "## Files by plane", ""]
    for kind in ("atom", "evidence", "registry", "other"):
        items = planes.get(kind) or []
        if not items:
            continue
        lines.append(f"**{kind}** ({len(items)}):")
        for p in items[:15]:
            # entries come as "XY path" (porcelain) or bare path (range list)
            display = p[3:] if len(p) > 3 and p[1:3] in ("M ", "A ", "D ", "R ") else p
            lines.append(f"- `{display.strip(chr(34))}`")
        if len(items) > 15:
            lines.append(f"- … and {len(items) - 15} more")
        lines.append("")
    lines.append("Merge policy: evidence-only PRs auto-merge on green CI (`sync.evidence_prs: auto`); "
                 "any atom-plane change waits for human review.")
    return "\n".join(lines) + "\n"

def push_via_pr(changes, message):
    """One branch + one PR per push. Evidence-only + auto policy → gh pr merge
    --auto (squash) so CI verdict drives the merge; otherwise leave open.

    The PR classifies the COMMITTED RANGE (base..HEAD) — the uncommitted
    `changes` list is empty by the time we get here (commit happened in
    cmd_push); classifying it wrongly armed review for evidence pushes
    (sim finding #8). gh failures are LOUD: a swallowed pr-create error
    printed 'Awaiting human review' while no PR existed."""
    repo = corpus_github_repo()
    if not repo:
        print("Error: PR push requires a GitHub corpus remote (owner/name), got: "
              f"{(get_remote() or '').strip()[:60]}", file=sys.stderr)
        sys.exit(1)
    branch = pr_branch_name()
    base_head = _sh("rev-parse", f"{CONTENT_REMOTE_NAME}/corpus")
    if not base_head:
        print("Error: cannot resolve corpus remote head — run: wf sync pull", file=sys.stderr)
        sys.exit(1)
    base_head = base_head.strip()
    if _sh("push", CONTENT_REMOTE_NAME, f"HEAD:refs/heads/{branch}") is None:
        print(f"Error: could not push branch {branch}", file=sys.stderr)
        sys.exit(1)
    # committed range = what this push distributes (drives body + policy)
    range_files = _sh("diff", "--name-only", f"{base_head}", "HEAD") or ""
    range_changes = [f" M {p.strip()}" for p in
                     (range_files.splitlines() if isinstance(range_files, str) else range_files)
                     if p.strip()]
    body = build_pr_body(range_changes, base_head)
    title = message or f"sync {_policy_live().machine_name()} {date.today().isoformat()}"
    out = gh_run("pr", "create",
                 "--repo", repo,
                 "--base", "corpus",
                 "--head", branch,
                 "--title", title,
                 "--body", body, capture_err=True)
    if not out:
        # distinguish the empty-range case from a real failure
        err = gh_last_error()
        print(f"Error: PR creation failed: {err or '(no output)'}", file=sys.stderr)
        print("The branch was pushed; inspect: gh pr create --repo "
              f"{repo} --base corpus --head {branch}", file=sys.stderr)
        sys.exit(1)
    url = gh_run("pr", "view", branch, "--repo", repo, "--json", "url", "--jq", ".url")
    print(f"PR opened: {(url or '').strip()}")
    policy = pr_merge_policy(range_changes)
    if policy == "auto-merge":
        gh_run("pr", "merge", branch, "--repo", repo, "--auto", "--squash")
        print("Auto-merge armed (evidence-plane only, CI-gated).")
    else:
        print("Awaiting human review (atom-plane changes are never auto-merged).")
