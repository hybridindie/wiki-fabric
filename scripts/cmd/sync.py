#!/usr/bin/env python3
# sync.py — Share the corpus with a team via a git remote (source-of-truth sync)
#
# The corpus is your fabric's knowledge content: claims, sources, summaries,
# patterns, skills, concepts, experience events, decisions, syntheses, registry
# metadata. It syncs to a shared git remote so every machine (and teammate)
# reads the same source truth.
#
# The harness (scripts/, schemas/, templates/) does NOT sync — each machine
# updates it via `wf update` from the public repo. Content and code have
# different lifecycles and different remotes.
#
# Usage:
#   wf sync init <git-url>       # set up the content remote (standalone corpus repo)
#   wf sync status               # show local vs remote divergence
#   wf sync push                 # commit + push local content changes
#   wf sync pull                 # fetch + merge remote content; conflicts → review queue
#
# Conflict policy: same-path edits from two machines are moved to
# registry/conflicts/ with both versions preserved. Nothing is silently
# overwritten. Lint treats unresolved conflicts as errors until reviewed.

import os
import sys
import sys as _s, pathlib as _p
_HERE = _p.Path(__file__).resolve().parent
# Explicit import bootstrap: this script's own dir (same-dir siblings)
# + scripts/lib (shared modules). No shotgun path injection.
for _dir in (_HERE, _HERE.parent / "lib", _HERE.parent):
    if str(_dir) not in _s.path:
        _s.path.insert(0, str(_dir))
import re
import subprocess
import argparse
import shutil
from pathlib import Path
from datetime import date, datetime
import wf_common
from wf_common import git_sh as _git_sh, parse_frontmatter, yaml_scalar, TIMEOUT_GIT, TIMEOUT_API
from sync_lib import policy as _policy_mod
from sync_lib.policy import (sync_mode, evidence_prs_policy, classify_change,
                             classify_changes, pr_merge_policy, use_pr_mode,
                             machine_name, pr_branch_name)

def evidence_prs_policy_wrapper():
    """Call-time binding (the #178 flake): the from-import copy pinned at
    module load; tests patch the POLICY module — the call resolves THROUGH
    the module (patch-visible), not through the stale copy."""
    return _policy_mod.evidence_prs_policy()
from sync_lib.pr import (gh_run, gh_last_error, corpus_github_repo,
                         build_pr_body, push_via_pr,
                         change_set_manifests_for_range)

def sh(*args, cwd=None, timeout=TIMEOUT_GIT):
    return _git_sh(*args, cwd=str(cwd or VAULT_ROOT), timeout=timeout)
from fabric_config import FABRIC_ROOT
from fabric_config import CORPUS_ROOT, VAULT_ROOT

import layout
import paths  # scripts/lib — single resolver home (#152)

CONTENT_REMOTE_NAME = "corpus"
SYNC_BRANCH = "main"

# Directories that ARE the corpus (content). Everything else is harness or local.
CONTENT_PATHS = [
    "evidence/claims",
    "evidence/sources",
    "evidence/source-summaries",
    "evidence/experiments",
    "evidence/traces",
    "evidence/_inbox",
    "concepts",
    "patterns",
    "anti-patterns",
    "skills",
    "syntheses",
    "domains",
    "projects",
    "global/entities",
    "global/graphs",
    "registry",
]

MACHINE_LOCAL_SYNC_PATHS = [  # #181/#182 decisions: per-machine state (the queues are the truth)
    "registry/receipts",
    "registry/pending-gate.md",
]

LOCAL_ONLY_PATHS = [
    "fabric.yaml",       # machine-specific config
    "opencode.json",     # machine-specific editor config
    ".obsidian",         # editor workspace
    ".venv",             # python env
]

# === PR-mode plane classification (#100) ===
# Remote updates arrive as PRs — the PR is the change-set receipt (reviewable
# diff, actor trail, CI verdict). Evidence-plane PRs auto-merge on green CI;
# atom-plane PRs always wait for a human. Local-first is untouched: this gates
# distribution, not local commits.
def local_projects():
    """Project namespaces that exist locally."""
    pd = layout.projects(VAULT_ROOT)
    if not pd.exists():
        return set()
    return {p.name for p in pd.iterdir() if p.is_dir() and not p.name.startswith(".")}


def remote_projects():
    """Project namespaces that exist on the remote corpus."""
    listing = sh("ls-tree", "--name-only", f"{CONTENT_REMOTE_NAME}/main", "--", "projects/")
    if not listing:
        return set()
    return {l.strip().rstrip("/").split("/")[-1] for l in listing.splitlines() if l.strip()}


def namespace_diff(direction):
    """Project namespaces present only on one side. direction: 'remote-only' or 'local-only'."""
    lp, rp = local_projects(), remote_projects()
    if lp == rp:
        return set()
    return (rp - lp) if direction == "remote-only" else (lp - rp)


def describe_namespaces(names):
    """One-line description of each project namespace from its README frontmatter."""
    out = []
    for name in sorted(names):
        readme = layout.projects(VAULT_ROOT) / name / "README.md"
        title = name
        owner = ""
        if readme.exists():
            try:
                import yaml
                fm = yaml.safe_load(readme.read_text().split("---")[1]) or {}
                title = fm.get("title") or name
                owner = fm.get("owner") or ""
            except Exception:
                pass  # unparseable README → fall back to the dir name (below)
        out.append(f"  projects/{name}/ — {title}" + (f" (owner: {owner})" if owner else ""))
    return out


def git_status():
    # --untracked-files=all: plain porcelain collapses an untracked DIRECTORY
    # into one entry ('?? evidence/') — capture waves are exactly that shape,
    # so counts/commit-drift/status all under-counted. Renames: porcelain
    # 'R  old -> new' — the PATH the file lives at now is after ' -> '.
    out = sh("status", "--porcelain", "--untracked-files=all")
    lines = []
    for l in (out or "").splitlines():
        if not l.strip():
            continue
        if " -> " in l[3:]:
            l = l[:3] + l[3:].split(" -> ")[-1]
        lines.append(l)
    return lines


def is_content_path(path_str):
    p = path_str.lstrip('"').strip()
    for cp in MACHINE_LOCAL_SYNC_PATHS:  # per-machine planes never sync (#181/#182)
        if p == cp or p.startswith(cp + "/") or p.startswith(f'"{cp}/'):
            return False
    for cp in CONTENT_PATHS:
        if p == cp or p.startswith(cp + "/") or p.startswith(f'"{cp}/'):
            return True
    return False


def content_changes():
    """Uncommitted changes limited to corpus paths."""
    return [l for l in git_status() if is_content_path(l[3:])]


def get_remote():
    return sh("remote", "get-url", CONTENT_REMOTE_NAME)


def validate_fabric():
    """Refuse to sync a non-corpus directory. Under the standalone-repo model
    the CORPUS (VAULT_ROOT) is the git repo: valid = a .git present here (its
    own, init'd by sync init/migrate or a teammate clone) OR the legacy outer
    layout (outer .git tracks corpus/) — the migrate path handles that. A
    fresh corpus lacking the AGENTS.md marker gets it scaffolded."""
    harness = paths.find_harness_root()
    registry = layout.registry(VAULT_ROOT)
    registry.mkdir(parents=True, exist_ok=True)
    if not (VAULT_ROOT / "AGENTS.md").exists():
        src_ag = harness / "AGENTS.md"
        if src_ag.exists():
            shutil.copy(src_ag, VAULT_ROOT / "AGENTS.md")
            print(f"Scaffolded corpus/AGENTS.md (from harness) — sync marker")
    corpus_is_git = (VAULT_ROOT / ".git").exists()
    legacy_outer = (VAULT_ROOT.parent / ".git").exists()
    if not corpus_is_git and not legacy_outer:
        print("Error: the corpus is not a git repo — run: wf sync init <url> "
              "(or wf sync migrate for a legacy layout)", file=sys.stderr)
        sys.exit(1)

# === Commands ===


def migrate_team_config(dry_run=False):
    """#184-a: move team-true blocks OUT of the gitignored fabric.yaml: routing
    → the overlays (already supported by discovery), tuning → corpus/tuning.yaml,
    domain signals → the ontology ## Signals. machine fabric.yaml left
    machine-true (llm/owner/paths/vault). Deterministic; idempotent."""
    import yaml as _yaml
    config_file = FABRIC_ROOT / "fabric.yaml"
    if not config_file.exists():
        print("no machine fabric.yaml — nothing to migrate")
        return 0
    cfg = _yaml.safe_load(config_file.read_text()) or {}
    moved = []
    # 1. routing keys → the overlays (same values; overlay already carries them)
    repos = cfg.get("repos") or {}
    for slug, rcfg in list(repos.items()):
        if not isinstance(rcfg, dict):
            continue
        if dry_run:
            if any(k in rcfg for k in ("routing", "extract", "synthesize", "dossier")):
                moved.append(f"repos.{slug}.routing -> overlay")
            continue
        for key in ("routing", "extract", "synthesize", "dossier"):
            if key in rcfg:
                rcfg.pop(key, None)
                moved.append(f"repos.{slug}.{key} -> overlay")
    # 2. tuning → corpus/tuning.yaml
    tuning = cfg.get("tuning") or {}
    tf = _corpus_tuning_file()
    if tuning:
        if dry_run:
            moved.append("tuning -> corpus/tuning.yaml")
        else:
            moved.append("tuning -> corpus/tuning.yaml")
            existing = _yaml.safe_load(tf.read_text()) if tf.exists() else {}
            merged = {**existing, **tuning}
            tf.write_text(__import__("wf_common").dump_frontmatter(merged))
            cfg.pop("tuning")
    # 3. domain signals → the ontology ## Signals
    domains = cfg.get("domains") or {}
    onto = layout.domains(VAULT_ROOT) / "ontology.md"
    if domains and onto.exists():
        if dry_run:
            moved.append("domains.*.signals -> ontology ## Signals")
        else:
            moved.append("domains.*.signals -> ontology ## Signals")
            text = onto.read_text()
            block = "\n## Signals\n" if "## Signals" not in text else ""
            lines = [block]
            for name, d in sorted(domains.items()):
                sigs = sorted(set((d or {}).get("signals") or []))
                if sigs:
                    lines.append(f"- {name}: {', '.join(sigs)}")
            if len(lines) > 1 or block:
                text = text.rstrip() + "\n" + "\n".join(lines) + "\n"
                onto.write_text(text)
            cfg.pop("domains", None)
    if dry_run:
        print("[DRY]" if moved else "[DRY] nothing team-true in the machine config")
        for mm in moved:
            print(f"  would move: {mm}")
        return 0
    if not moved and not dry_run:
        print("machine config already machine-true")
        return 0
    if not dry_run:
        config_file.write_text(__import__("wf_common").dump_frontmatter(cfg))
    for mm in moved:
        print(f"  migrated: {mm}")
    print("#184-a: fabric.yaml is machine-true only; the team content travels "
          "(overlays + corpus/tuning.yaml + the ontology).")
    return 0


def seed_corpus_gitignore():
    """The machine-local plane contract (#181/#182 decisions, 2026-10-03):
    receipts + pending-gate = machine-local (the queues are the truth);
    .last-capture = the sanctioned per-capture-channel state marker; derived
    artifacts (regenerable, #181) stay tracked but the pull-side regen keeps
    them converging. Idempotent: existing lines never duplicate."""
    gi = VAULT_ROOT / ".gitignore"
    required = ["registry/receipts/", "registry/pending-gate.md",
                ".last-capture", ".DS_Store", "fabric.yaml", "secrets.env"]
    try:
        txt = gi.read_text() if gi.exists() else ""
        added = [ln for ln in required if ln not in txt.splitlines()]
        if added:
            header = "" if txt else ("# Machine-local planes + secrets (#181/#182): "
                                     "per-machine state never syncs\n")
            gi.write_text(txt.rstrip("\n") + "\n" + header + "\n".join(added) + "\n")
            print(f"(gitignore seeded: {len(added)} machine-local line(s))")
        return True
    except OSError:
        return False


def scaffold_gate_digest_workflow():
    """Write the daily gate-digest workflow (#174) into
    <corpus>/.github/workflows/ when absent — runs the gate on a cadence
    and pushes the summary through the notify adapters (webhook when
    configured; the manifest is always the record). Opt-in: repo var
    WIKI_FABRIC_GATE_NOTIFY=1. Deterministic, 0 tokens; nothing
    auto-promotes — a push is a bell, not a decision."""
    harness = Path(__file__).resolve().parent.parent.parent
    template = harness / "system" / "corpus" / "gate-digest-workflow.yml"
    wf_dir = VAULT_ROOT / ".github" / "workflows"
    wf_dir.mkdir(parents=True, exist_ok=True)
    target = wf_dir / "gate-digest.yml"
    if target.exists() or not template.exists():
        return False
    shutil.copy(template, target)
    print("Scaffolded CI workflow: .github/workflows/gate-digest.yml "
          "(daily decision digest; enable: repo var WIKI_FABRIC_GATE_NOTIFY=1)")
    return True


def scaffold_promotion_queue():
    """#160 S3: the promotion checklist sync init promises (system/skills/
    promote/SKILL.md; dossiers link [[promotion-queue]]). Scaffolds only when
    absent — a human-maintained file, never overwritten."""
    q = layout.registry(VAULT_ROOT) / "promotion-queue.md"
    if q.exists():
        return
    q.write_text("""---
type: registry
title: Promotion Queue
created: {d}
updated: {d}
---

# Promotion Queue

Human-maintained checklist of pattern candidates in flight (7-point review:
independence, recurrence, evidence quality, applicability, counterexamples,
cost-of-being-wrong, maturity). Dossiers live at `registry/promotions/`.

| Pattern | Maturity | Dossier | Observation note |
|---|---|---|---|
""".replace("{d}", date.today().isoformat()), encoding="utf-8")
    print(f"Scaffolded {q.relative_to(VAULT_ROOT)} (human-maintained checklist)")


def scaffold_ci_workflow():
    """Write the corpus CI workflow (lint 0-error gate + OKF floor + catalog
    freshness + conflict block) into <corpus>/.github/workflows/ when absent.
    The corpus is the team source of truth — every push should pass the
    governance floor, not just machines where someone remembers to run lint.
    Template ships with the harness (system/corpus/lint-workflow.yml); never
    overwrites an existing workflow (#'s vault-CI)."""
    harness = Path(__file__).resolve().parent.parent.parent
    template = harness / "system" / "corpus" / "lint-workflow.yml"
    wf_dir = VAULT_ROOT / ".github" / "workflows"
    wf_dir.mkdir(parents=True, exist_ok=True)
    target = wf_dir / "lint.yml"
    if target.exists() or not template.exists():
        return False
    shutil.copy(template, target)
    print("Scaffolded CI workflow: .github/workflows/lint.yml "
          "(corpus lint gate runs on every push)")
    return True


def scaffold_freshness_workflow():
    """Write the scheduled upstream-freshness workflow (#84) into
    <corpus>/.github/workflows/ when absent — capture upstream PR/issue
    drift + mechanical re-verification on a cron, evidence-plane only
    (0 tokens). Opt-in per repo variable WIKI_FABRIC_FRESHNESS=1."""
    harness = Path(__file__).resolve().parent.parent.parent
    template = harness / "system" / "corpus" / "freshness-workflow.yml"
    wf_dir = VAULT_ROOT / ".github" / "workflows"
    wf_dir.mkdir(parents=True, exist_ok=True)
    target = wf_dir / "freshness.yml"
    if target.exists() or not template.exists():
        return False
    shutil.copy(template, target)
    print("Scaffolded CI workflow: .github/workflows/freshness.yml "
          "(daily upstream-freshness cycle; enable: repo var WIKI_FABRIC_FRESHNESS=1)")
    return True


def scaffold_mining_workflow():
    """Write the scheduled chat-mining workflow (#172) into
    <corpus>/.github/workflows/ when absent — weekly distillation of
    chat transcripts into gated candidates (patterns/_inbox/), heuristic
    mode (0 tokens — CI stays LLM-free). Opt-in per repo variable
    WIKI_FABRIC_MINING=1. Independent of the freshness cycle (different
    planes); nothing auto-promotes — candidates wait for the human gate."""
    harness = Path(__file__).resolve().parent.parent.parent
    template = harness / "system" / "corpus" / "mining-workflow.yml"
    wf_dir = VAULT_ROOT / ".github" / "workflows"
    wf_dir.mkdir(parents=True, exist_ok=True)
    target = wf_dir / "mining.yml"
    if target.exists() or not template.exists():
        return False
    shutil.copy(template, target)
    print("Scaffolded CI workflow: .github/workflows/mining.yml "
          "(weekly chat-mining cadence; enable: repo var WIKI_FABRIC_MINING=1)")
    return True


def cmd_migrate(remote_url=None):
    """Legacy A-layout → standalone corpus repo (2026-10-01 model):
    the fabric's outer git tracked corpus/*; the standalone corpus/ gets its
    own git (content AT ROOT — no prefix), pushes to the team remote's main.
    The old remote corpus branch stays as archive."""
    if (VAULT_ROOT / ".git").exists():
        print("Already standalone (corpus/.git present) — nothing to migrate.")
        return
    outer = VAULT_ROOT.parent
    if not (outer / ".git").exists():
        print("No outer git tracking the corpus either — run: wf sync init <url>",
              file=sys.stderr)
        sys.exit(1)
    url = remote_url or (sh("remote", "get-url", CONTENT_REMOTE_NAME) or "")
    if url:
        # the scp-style ssh URL mis-reports on pushes from nested aliases —
        # normalize to ssh:// form once (measured: alias-push hits a GitHub
        # "not a valid repository name" error; ssh:// does not)
        m = re.match(r"^git@github\.com:([^/]+/.+)$", url)
        if m:
            url = f"ssh://git@github.com/{m.group(1)}"
        print(f"Corpus remote: {url}")
    sh("init", "-q", "-b", "main")
    sh("add", "-A")
    if subprocess.run(["git", "-c", "user.name=wiki-fabric", "-c",
                       "user.email=wf@corpus.local", "commit", "-q",
                       "-m", "migrate: standalone corpus repo"],
                      cwd=str(VAULT_ROOT), capture_output=True).returncode == 0:
        print("Committed the corpus (standalone history begins here)")
    if url:
        sh("remote", "add", CONTENT_REMOTE_NAME, url)
        print("Pushing to the team remote (branch: main)...")
        if sh("push", "-u", CONTENT_REMOTE_NAME, "HEAD:refs/heads/main") is None:
            print("Push failed (check access) — content is committed locally; "
                  "retry: wf sync push", file=sys.stderr)
    # outer: untrack corpus/ (worktree stays) + ignore
    subprocess.run(["git", "rm", "-r", "-q", "--cached", "corpus"],
                   cwd=str(outer), capture_output=True)
    gi = outer / ".gitignore"
    line = "corpus/"
    try:
        txt = gi.read_text() if gi.exists() else ""
        if line not in txt.splitlines():
            gi.write_text(txt.rstrip("\n") + f"\n{line}\n")
            subprocess.run(["git", "add", str(gi)], cwd=str(outer), capture_output=True)
            subprocess.run(["git", "commit", "-q", "-m", "migrate: corpus content moved to a standalone repo (corpus/)"],
                           cwd=str(outer), capture_output=True)
    except Exception as e:
        print(f"(outer gitignore update skipped: {e})")
    print()
    print("✓ Migration complete — the corpus is a standalone git repo at " + str(VAULT_ROOT))
    print("  Outer git: corpus/ untracked (machine config only). Old remote")
    print("  'corpus' branch is the archive; new distribution branch: main.")


def cmd_init(remote_url):
    """Lead machine: make the corpus a standalone git repo + publish it as
    the team's source of truth (remote root == corpus content, plain git)."""
    validate_fabric()
    scaffold_ci_workflow()
    scaffold_freshness_workflow()
    scaffold_mining_workflow()
    scaffold_gate_digest_workflow()
    seed_corpus_gitignore()
    scaffold_promotion_queue()
    layout.questions(VAULT_ROOT).mkdir(parents=True, exist_ok=True)  # #160 S4 plane scaffold

    # Verify the remote is reachable
    if sh("ls-remote", remote_url, "HEAD") is None and not remote_url.startswith("/"):
        print(f"Error: cannot reach remote {remote_url} (does it exist? do you have access?)", file=sys.stderr)
        sys.exit(1)

    if not (VAULT_ROOT / ".git").exists():
        sh("init", "-q", "-b", "main")
        print("Initialized the corpus as a standalone git repo")
    if sh("remote", "get-url", CONTENT_REMOTE_NAME) is None:
        sh("remote", "add", CONTENT_REMOTE_NAME, remote_url)

    # Commit everything (a fresh corpus has work to publish; an existing one
    # commits pending content so the push is complete)
    sh("add", "-A")
    if subprocess.run(["git", "-c", "user.name=wiki-fabric", "-c",
                       "user.email=wf@corpus.local", "commit", "-q",
                       "-m", "sync init: publish corpus",
                       "--allow-empty"], cwd=str(VAULT_ROOT),
                      capture_output=True).returncode == 0:
        print("Committed corpus content")
    if sh("push", "-u", CONTENT_REMOTE_NAME, "HEAD:refs/heads/main") is None:
        print("Error: push failed (check access rights)", file=sys.stderr)
        sys.exit(1)
    sh("fetch", CONTENT_REMOTE_NAME, "main")

    print()
    print(f"✓ Corpus remote configured: {CONTENT_REMOTE_NAME} → {remote_url}")
    print("  Teammates join with: wf install --corpus " + remote_url)

def cmd_setup(name=None, private=True, yes=False):
    """First-class corpus setup: create (or adopt) the GitHub corpus repo and
    wire + publish this fabric's corpus as the source of truth.

    Uses the gh CLI when available (detection + auth check); falls back to
    printing manual git instructions otherwise. Human-gated: prompts unless
    --yes."""
    validate_fabric()
    scaffold_ci_workflow()
    scaffold_freshness_workflow()
    scaffold_mining_workflow()
    scaffold_gate_digest_workflow()
    seed_corpus_gitignore()
    scaffold_promotion_queue()
    layout.questions(VAULT_ROOT).mkdir(parents=True, exist_ok=True)  # #160 S4 plane scaffold

    # 1. gh CLI detection + auth
    def _run(args, timeout=TIMEOUT_API):
        try:
            return subprocess.run(args, capture_output=True, text=True, timeout=timeout)
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return None

    gh = _run(["gh", "--version"])
    gh_ok = gh is not None and gh.returncode == 0
    if not gh_ok:
        print("gh CLI not found. Two options:", file=sys.stderr)
        print("  a) install gh: https://cli.github.com/ then `gh auth login`", file=sys.stderr)
        print("  b) create the corpus repo manually, then:", file=sys.stderr)
        print(f"     wf sync init git@github.com:<owner>/{name or 'wiki-fabric-corpus'}.git", file=sys.stderr)
        sys.exit(1)
    auth = _run(["gh", "auth", "status"])
    authed = auth is not None and auth.returncode == 0 and "not logged in" not in (auth.stderr or "")
    if not authed:
        print("gh is installed but not authenticated. Run: gh auth login", file=sys.stderr)
        sys.exit(1)
    who = _run(["gh", "api", "user", "--jq", ".login"])
    # gh identity IS the sync owner (the corpus remote lives in the gh user's
    # namespace); sentinel shared with get_owner's default (#155-B)
    owner = (who.stdout.strip() if who and who.returncode == 0 else "") or "you"
    print(f"gh CLI detected (authenticated as {owner})")

    # 2. repo name + creation gate
    name = name or "wiki-fabric-corpus"
    full = f"{owner}/{name}"
    existing = _run(["gh", "repo", "view", full, "--json", "name"])
    repo_exists = existing is not None and existing.returncode == 0
    if repo_exists:
        print(f"Corpus repo exists: {full} — adopting it")
    else:
        vis = "--private" if private else "--public"
        if not yes:
            resp = input(f"Create GitHub repo {full} ({'private' if private else 'public'})? [y/N]: ").strip().lower()
            if resp not in ("y", "yes"):
                print("Aborted. Create it later with: gh repo create "
                      f"{full} {vis} && wf sync init git@github.com:{full}.git")
                sys.exit(1)
        create = _run(["gh", "repo", "create", full, vis], timeout=60)
        # gh >= 2.x dropped --confirm; --json validates success differently
        if create is None or create.returncode != 0:
            # repo may already exist under a different visibility; check
            check = _run(["gh", "repo", "view", full, "--json", "name"])
            if check is None or check.returncode != 0:
                print(f"Error: could not create {full}: {(create.stderr or '')[-200:]}", file=sys.stderr)
                sys.exit(1)
        print(f"Created corpus repo: {full}")

    # 3. wire + publish
    remote_url = f"git@github.com:{full}.git"
    cmd_init(remote_url)
    print(f"\nCorpus published. Teammates join with:")
    print("  curl -fsSL https://raw.githubusercontent.com/hybridindie/wiki-fabric/main/scripts/wiki-fabric.sh | bash -s -- \\")
    print(f"    --corpus git@github.com:{full}.git")


def cmd_commit_drift(message=None, dry_run=False, quiet=False):
    """#160 S5: the drift-wave ritual, formalized. Hooks accumulate hook
    churn (capture/ingest/reverify/enrich writes) between human commits;
    this stages + commits it with a plane-classified summary (Atom/Evidence/
    Risky breakdown from sync policy). Local-only by design: you run
    `commit-drift` then `push` explicitly — never pushes.
    Exits 0 (nothing or committed), 1 (git failure)."""
    validate_fabric()
    _legacy_layout_check("commit-drift")
    from sync_lib import policy as _policy

    # porcelain: staged vs unstaged (drift is typically unstaged, but never
    # clobber a deliberate partial stage — merge them)
    # --untracked-files=all: porcelain collapses an untracked DIR into one
    # entry ('?? evidence/') — the drift wave is usually exactly that
    out = sh("status", "--porcelain", "--untracked-files=all") or ""
    changes = [l for l in out.splitlines() if l.strip()]
    if not changes:
        if not quiet:
            print("No drift to commit — the worktree is clean.")
        return 0

    paths = [l[3:].strip('"') for l in changes]
    by_plane = {}
    for _p in paths:
        kind = _policy.classify_change(_p)
        by_plane[kind] = by_plane.get(kind, 0) + 1
    plane = _policy.classify_changes(paths)
    plane_tag = {"atom": "knowledge-update", "evidence": "evidence-capture",
                 "registry": "registry-drift", "other": "knowledge-update"}[plane]

    counts = ", ".join(f"{v} {k}(s)" for k, v in sorted(by_plane.items()))
    sample = "; ".join(p for p in paths[:3])
    msg = message or (
        f"drift [{plane_tag}]: {counts} — "
        f"{sample}{' +{} more'.format(len(paths) - 3) if len(paths) > 3 else ''}")
    if dry_run:
        print(f"[dry-run] would commit {len(paths)} file(s) [{plane_tag}: {counts}]")
        print(f"  message: {msg}")
        return 0

    sh("add", "-A")
    # '--quiet' rc: 0 = no staged changes (git_sh: stdout '' — a real result),
    # 1 = staged changes (git_sh returns None). None == HAS staged changes.
    if sh("diff", "--cached", "--quiet") is None:
        pass  # staged changes present → proceed
    elif _staged_empty():
        if not quiet:
            print("Nothing staged after add -A — hook churn already committed upstream?")
        return 0
    # git_sh returns None on rc!=0 (hook reject, protected paths); '' on success
    r = sh("commit", "-q", "-m", msg)
    if r is None and not _committed():
        print(f"commit failed — inspect: git -C {VAULT_ROOT} status", file=sys.stderr)
        return 1
    if not quiet:
        print(f"Drift committed: {len(paths)} file(s) [{plane_tag}: {counts}]")
        print(f"  {msg[:120]}")
        print("Next: wf sync push (explicit — commit-drift never pushes)")
    return 0


def _staged_empty():
    return not (sh("diff", "--cached", "--name-only") or "").strip()


def _committed():
    return not (sh("status", "--porcelain") or "").strip()


def cmd_status():
    validate_fabric()
    remote = get_remote()
    if not remote:
        print("No corpus remote configured. Set one up: wf sync init <git-url>")
        sys.exit(1)

    sh("fetch", CONTENT_REMOTE_NAME, "main")
    local = sh("rev-parse", "HEAD")
    remote_head = sh("rev-parse", f"{CONTENT_REMOTE_NAME}/main")

    ahead = (sh("rev-list", "--count", f"{remote_head}..{local}") or "0").strip()
    behind = (sh("rev-list", "--count", f"{local}..{remote_head}") or "0").strip()

    print(f"Corpus remote: {CONTENT_REMOTE_NAME} → {remote}")
    print(f"Branch:        {SYNC_BRANCH}")
    print(f"Local:         ahead {ahead}, behind {behind}")
    if ahead != "0" or behind != "0":
        print()
        print("Run 'wf sync push' to publish local changes, or 'wf sync pull' to receive remote changes.")
    changes = content_changes()
    if changes:
        print(f"\nUncommitted corpus changes ({len(changes)}):")
        for c in changes[:10]:
            print(f"  {c}")
        if len(changes) > 10:
            print(f"  ... and {len(changes) - 10} more")

    conflicts = list_conflicts()
    if conflicts:
        print(f"\n⚠ Unresolved sync conflicts ({len(conflicts)}) in registry/conflicts/:")
        for c in conflicts:
            print(f"  {c}")
        print("Resolve each: wf sync resolve <conflict> --strategy ours|theirs|union")
        print("Then: wf sync push")

    # Project namespace visibility
    try:
        remote_only = namespace_diff("remote-only")
        if remote_only:
            print(f"\nNew projects on the corpus (pull to receive):")
            print("\n".join(describe_namespaces(remote_only)))
    except SystemExit:
        raise
    except Exception:
        pass  # ls-tree failures shouldn't break status


# === PR push path (#100) ===





















def _corpus_push():
    """Push the corpus repo's HEAD to its origin main (the standalone-repo
    model: no branch aliasing — the remote root IS the corpus)."""
    out = sh("push", CONTENT_REMOTE_NAME, "HEAD:refs/heads/main")
    return out
    # (None = failure; cmd_push's caller surfaces "remote has newer — pull first")


def _legacy_layout_check(operation):
    """The standalone-repo model (2026-10-01): a corpus WITHOUT its own .git
    but inside an outer repo tracking it is the LEGACY layout — sync ops
    would silently touch the OUTER git (wrong tree, prefix games). Loud
    one-time advice; the user runs: wf sync migrate."""
    if (VAULT_ROOT / ".git").exists():
        return
    outer = VAULT_ROOT.parent
    if not (outer / ".git").exists():
        return
    tracked = subprocess.run(["git", "ls-files", "corpus/"], cwd=str(outer),
                             capture_output=True, text=True).stdout.strip()
    if tracked:
        print(f"⚠  legacy layout detected (outer git tracks corpus/) — sync "
              f"{operation} would touch the OUTER repo. Run once: wf sync migrate",
              file=sys.stderr)


def cmd_push(message=None, pr=False, no_pr=False):
    validate_fabric()
    _legacy_layout_check("push")
    if not get_remote():
        print("No corpus remote. Run: wf sync init <git-url>", file=sys.stderr)
        sys.exit(1)

    # LOUD pre-check: fetch and compare. Pushing over a moved remote is the
    # multi-writer failure mode — be loud BEFORE the push, not after git
    # rejects it (#'s team-sync hardening).
    sh("fetch", CONTENT_REMOTE_NAME, "main")
    remote_head = sh("rev-parse", f"{CONTENT_REMOTE_NAME}/main")
    local_head = sh("rev-parse", "HEAD")
    # behind = remote has commits local lacks. Ancestor check, not sha
    # equality: after a sync pull (merge), local HEAD is a merge commit whose
    # sha differs from the remote head even though it CONTAINS it — a sha
    # equality check false-blocked every post-pull push (found in the
    # two-machine race test).
    behind = None
    ahead = 0
    if remote_head and local_head:
        anc = sh("merge-base", "--is-ancestor", f"{CONTENT_REMOTE_NAME}/main", "HEAD")
        if anc is not None:
            behind = 0
            ahead_n = sh("rev-list", "--count", f"{CONTENT_REMOTE_NAME}/main..HEAD")
            ahead = int(ahead_n) if ahead_n else 0
        else:
            behind = int(sh("rev-list", "--count", f"HEAD..{CONTENT_REMOTE_NAME}/main") or 0)
    if behind:  # None (unknown) or > 0
        print("", file=sys.stderr)
        print("══════════════════════════════════════════════════════", file=sys.stderr)
        print("  CORPUS OUT OF SYNC — the remote has moved", file=sys.stderr)
        print("══════════════════════════════════════════════════════", file=sys.stderr)
        if behind:
            print(f"  Your local corpus is BEHIND the team remote by {behind} commit(s):", file=sys.stderr)
            print("  teammates have published claims/patterns/decisions you don't have.", file=sys.stderr)
        if ahead and int(ahead) > 0:
            print(f"  You are also AHEAD by {ahead} commit(s) (your local work).", file=sys.stderr)
        print("", file=sys.stderr)
        print("  PUSH BLOCKED. First:", file=sys.stderr)
        print("    wf sync pull      # fetch + merge the team's knowledge", file=sys.stderr)
        print("    wf sync push      # then publish", file=sys.stderr)
        print("", file=sys.stderr)
        if behind:
            print("  If the merge conflicts, resolve via: wf sync resolve", file=sys.stderr)
        print("══════════════════════════════════════════════════════", file=sys.stderr)
        sys.exit(1)

    # Block push when conflicts are unresolved
    conflicts = list_conflicts()
    if conflicts:
        print(f"Error: {len(conflicts)} unresolved conflict(s) in registry/conflicts/ — resolve them first:", file=sys.stderr)
        print("  Resolve with: wf sync resolve <conflict> --strategy ours|theirs|union", file=sys.stderr)
        for c in conflicts:
            print(f"  {c}", file=sys.stderr)
        sys.exit(1)

    changes = content_changes()
    if not changes:
        print("No uncommitted corpus changes.")
        # #100 bug-fix (sim finding): team mode with nothing new still opened
        # a PR with an empty body — branch == corpus → "No commits between"
        # and gh_run swallowed the failure. Nothing to distribute: skip the
        # PR unless local is AHEAD of the remote (committed, unpushed work
        # from an earlier interrupted push still needs a PR).
        if use_pr_mode(pr=pr, no_pr=no_pr):
            remote_now = (sh("rev-parse", f"{CONTENT_REMOTE_NAME}/main") or "").strip()
            head_now = (sh("rev-parse", "HEAD") or "").strip()
            ahead_n = sh("rev-list", "--count", f"{remote_now}..{head_now}") if remote_now and head_now else "0"
            if (ahead_n or "0").strip() == "0":
                print("Nothing to distribute — skipping PR.")
                return
            print(f"Distributing {ahead_n.strip()} committed-but-unpushed commit(s) via PR.")
    else:
        for l in changes:
            p = l[3:].lstrip('"').rstrip('"')
            subprocess.run(["git", "add", "--", p], cwd=str(VAULT_ROOT))
        msg = message or f"sync {date.today().isoformat()} ({len(changes)} files)"
        # identity carries a fallback: runners/containers have no global git config
        if subprocess.run(["git", "-c", "user.name=wiki-fabric", "-c",
                           "user.email=wf@corpus.local", "commit", "-m", msg],
                          cwd=str(VAULT_ROOT), capture_output=True).returncode != 0:
            print("Error: commit failed (nothing to commit or hook rejected)", file=sys.stderr)
            sys.exit(1)
        print(f"Committed {len(changes)} corpus files: {msg}")

    head = sh("rev-parse", "HEAD")

    # Mode resolution (#100): --pr forces PR path, --no-pr forces direct;
    # otherwise the sticky fabric.yaml sync.mode decides (solo default).
    use_pr = use_pr_mode(pr=pr, no_pr=no_pr)
    if use_pr:
        push_via_pr(changes, message)
        return

    if _corpus_push() is None:
        print("Error: push rejected — remote has newer commits. Run: wf sync pull", file=sys.stderr)
        sys.exit(1)
    print("Pushed corpus to remote.")


def list_conflicts():
    conflicts_dir = layout.registry(VAULT_ROOT) / "conflicts"
    if not conflicts_dir.exists():
        return []
    return sorted(str(p.relative_to(VAULT_ROOT)) for p in conflicts_dir.glob("**/*.md"))




def _parse_conflict(conflict_file):
    """Extract the conflicted path + ours/theirs payloads from a conflict record."""
    fm, body = parse_frontmatter(conflict_file)
    path = fm.get("path") or ""
    ours = theirs = ""
    m_ours = re.search(r"## Ours \(this machine\)\n\n```\n(.*?)\n```", body, re.DOTALL)
    m_theirs = re.search(r"## Theirs \(remote\)\n\n```\n(.*?)\n```", body, re.DOTALL)
    if m_ours:
        ours = m_ours.group(1)
    if m_theirs:
        theirs = m_theirs.group(1)
    return path, ours, theirs, fm


def _show_conflict(path, ours, theirs):
    """#14: side-by-side display of both versions for the interactive flow."""
    import difflib
    print("")
    print(f"════ Sync conflict: {path} ══")
    print("")
    diff = list(difflib.unified_diff(
        ours.splitlines(), theirs.splitlines(),
        fromfile="ours (this machine)", tofile="theirs (remote)", lineterm=""))
    if diff:
        print("\n".join(diff[:40]))
        if len(diff) > 40:
            print(f"  … and {len(diff) - 40} more diff line(s)")
    else:
        print("  (ours) :", ours[:200])
        print("  (theirs):", theirs[:200])
    print("")


def _resolve_interactively(conflict, path, ours, theirs):
    """#14: the human resolver flow — show both versions, choose a strategy."""
    _show_conflict(path, ours, theirs)
    print("  Resolution options:")
    print("    ours   — keep this machine's version")
    print("    theirs — take the teammate's version")
    print("    union  — keep both (marked, dedup later)")
    print("    skip   — leave the conflict pending")
    while True:
        choice = input("  Resolve with [ours/theirs/union/skip]: ").strip().lower()
        if choice == "skip":
            print("Conflict left unresolved — the SYNC-CONFLICT gate stays up.")
            sys.exit(0)
        if choice in ("ours", "theirs", "union"):
            return choice
        print("  (pick ours, theirs, union, or skip)")


def cmd_resolve(conflict, strategy, message=None):
    """Resolution policy for sync conflicts (#'s team-sync hardening).

    The corpus never diminishes: the conflict record preserves both versions;
    resolution picks how the knowledge combines:
      ours   — keep this machine's version; the remote version is superseded
               (recorded in the file's history, retrievable)
      theirs — take the teammate's version (e.g. theirs was re-verified later)
      union  — keep both: the incoming content is APPENDED as a new section
               (claims: both extractions survive; dedup is a later judgment)
    The conflict record is deleted on resolve; lint's SYNC-CONFLICT gate
    unblocks; the resolution is committed so the push carries the decision.
    Interactive flow (#14): with no strategy given, show both versions and
    prompt for the choice (requires a TTY)."""
    conflict_file = VAULT_ROOT / conflict
    if strategy == "derived":
        # the conflict record's PATH is a derived artifact: regenerate it
        import re as _re
        rec_fm, _ = parse_frontmatter(conflict_file)
        derived_path = str(rec_fm.get("path") or "")
        if not derived_path:
            print(f"conflict record carries no path — cannot regen: {conflict}", file=sys.stderr)
            sys.exit(1)
        subprocess.run(["git", "checkout", "--theirs", "--", derived_path],
                       cwd=str(VAULT_ROOT), capture_output=True)
        subprocess.run(["git", "commit", "--no-edit", "-q"],
                       cwd=str(VAULT_ROOT), capture_output=True)
        _regen_derived()
        subprocess.run(["git", "add", "-A"], cwd=str(VAULT_ROOT), capture_output=True)
        subprocess.run(["git", "-c", "user.name=wiki-fabric", "-c", "user.email=wf@corpus.local",
                        "commit", "-q", "-m", f"sync resolve (derived): {derived_path} regenerated"],
                       cwd=str(VAULT_ROOT), capture_output=True)
        print(f"Derived artifact resolved by regen: {derived_path} — SYNC-CONFLICT cleared.")
        return
    if not conflict_file.exists() and conflict.startswith("corpus/"):
        # conflict paths are recorded relative to the VAULT root; VAULT_ROOT
        # is the corpus dir (nested layout) — the join doubles. Resolve
        # corpus/-prefixed paths against the vault shell.
        conflict_file = VAULT_ROOT.parent / conflict
    if not conflict_file.exists():
        print(f"Error: conflict file not found: {conflict}", file=sys.stderr)
        print("List conflicts with: wf sync status", file=sys.stderr)
        sys.exit(1)

    path, ours, theirs, fm = _parse_conflict(conflict_file)
    if not path:
        print("Error: conflict record has no target path", file=sys.stderr)
        sys.exit(1)

    # #14: interactive when no strategy — display + prompt
    if strategy is None:
        strategy = _resolve_interactively(conflict, path, ours, theirs)

    if strategy not in ("ours", "theirs", "union"):
        print(f"Error: strategy must be ours|theirs|union (got {strategy!r})", file=sys.stderr)
        sys.exit(1)
    conflict_file = VAULT_ROOT / conflict
    if not conflict_file.exists() and conflict.startswith("corpus/"):
        # conflict paths are recorded relative to the VAULT root; VAULT_ROOT
        # is the corpus dir (nested layout) — the join doubles. Resolve
        # corpus/-prefixed paths against the vault shell.
        conflict_file = VAULT_ROOT.parent / conflict
    if not conflict_file.exists():
        print(f"Error: conflict file not found: {conflict}", file=sys.stderr)
        print("List conflicts with: wf sync status", file=sys.stderr)
        sys.exit(1)
    if strategy not in ("ours", "theirs", "union"):
        print(f"Error: strategy must be ours|theirs|union (got {strategy!r})", file=sys.stderr)
        sys.exit(1)

    path, ours, theirs, fm = _parse_conflict(conflict_file)
    if not path:
        print("Error: conflict record has no target path", file=sys.stderr)
        sys.exit(1)

    target = VAULT_ROOT / path
    if not target.exists() and path.startswith("corpus/"):
        target = VAULT_ROOT.parent / path  # nested corpus layout (see above)
    today = date.today().isoformat()
    stamp = datetime.now().strftime("%Y-%m-%dT%H:%M")

    if strategy == "ours":
        # ours is already on disk (the merge aborted) — just confirm
        final = target.read_text(encoding="utf-8", errors="replace") if target.exists() else ours
        resolution = "kept ours"
    elif strategy == "theirs":
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(theirs, encoding="utf-8")
        final = theirs
        resolution = "took teammate's version"
    else:  # union
        target.parent.mkdir(parents=True, exist_ok=True)
        existing = target.read_text(encoding="utf-8", errors="replace") if target.exists() else ours
        # union for markdown corpus content: keep both blocks side by side,
        # labeled — the human (or next ingest pass) dedups substance
        final = existing.rstrip("\n") + "\n\n<!-- sync-union: from teammate (" + stamp + ") -->\n\n" + theirs
        target.write_text(final, encoding="utf-8")
        resolution = "union (both versions kept, marked)"

    # delete the conflict record
    conflict_file.unlink()

    # commit the resolution
    subprocess.run(["git", "add", "--", path, str(conflict_file)], cwd=str(VAULT_ROOT), capture_output=True)
    msg = f"sync resolve [{strategy}]: {path} ({stamp})"
    subprocess.run(["git", "-c", "user.name=wiki-fabric", "-c",
                    "user.email=wf@corpus.local", "commit", "-q", "-m", msg],
                   cwd=str(VAULT_ROOT), capture_output=True)

    print(f"Resolved [{strategy}]: {path} — {resolution}")
    print(f"Conflict record removed; SYNC-CONFLICT gate cleared for this file.")
    print("Next: wf sync pull — if the same file conflicts again, resolve with")
    print("  'ours' (your resolution already carries the union) — then push.")
def _corpus_tuning_file():
    """corpus/tuning.yaml — the team-true tuning plane (#184-a)."""
    return VAULT_ROOT / "tuning.yaml" if False else __import__("pathlib").Path(VAULT_ROOT) / "tuning.yaml"


def _regen_derived():
    """#181: regenerate the derived plane in place (catalog + threads) —
    both machines converge before the next push. Best-effort: regen failure
    is a LINT concern, never a pull failure."""
    from pathlib import Path as _P
    import subprocess as _sp
    ri = _P(__file__).parent / "rebuild-index.py"
    if ri.exists():
        try:
            env = {**os.environ, "WIKI_FABRIC_ROOT": str(VAULT_ROOT),
                   "WIKI_FABRIC_DIR": str(VAULT_ROOT)}
            r = _sp.run([sys.executable, str(ri)], cwd=str(VAULT_ROOT),
                        capture_output=True, text=True, timeout=TIMEOUT_API, env=env)
            if r.returncode == 0:
                print("  (derived artifacts regenerated: catalog + threads converged)")
            else:
                print(f"  (derived regen skipped: {(r.stderr or '').strip()[-80:]})", file=sys.stderr)
        except Exception as e:
            print(f"  (derived regen skipped: {e})", file=sys.stderr)


def cmd_pull():
    validate_fabric()
    _legacy_layout_check("pull")
    if not get_remote():
        print("No corpus remote. Run: wf sync init <git-url>", file=sys.stderr)
        sys.exit(1)

    sh("fetch", CONTENT_REMOTE_NAME, "main")
    remote_head = sh("rev-parse", f"{CONTENT_REMOTE_NAME}/main")
    local_head = sh("rev-parse", "HEAD")

    if remote_head == local_head:
        print("Already up to date.")
        return

    # First: commit local corpus changes so they participate in the merge
    changes = content_changes()
    if changes:
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        for l in changes:
            p = l[3:].lstrip('"').rstrip('"')
            subprocess.run(["git", "add", "--", p], cwd=str(VAULT_ROOT))
        subprocess.run(["git", "-c", "user.name=wiki-fabric", "-c",
                        "user.email=wf@corpus.local", "commit", "-m",
                        f"sync local changes before pull ({stamp})"],
                       cwd=str(VAULT_ROOT), capture_output=True)
        print(f"Committed {len(changes)} local corpus changes before merging.")

    pre_pull_local = local_projects()

    # Merge remote corpus branch (allow unrelated histories: two fabrics that
    # share a remote but no common ancestor are still the same corpus)
    today = date.today().isoformat()
    result = subprocess.run(
        ["git", "merge", f"{CONTENT_REMOTE_NAME}/main", "--no-edit", "--allow-unrelated-histories",
         "-m", f"sync pull from {CONTENT_REMOTE_NAME} ({today})"],
        cwd=str(VAULT_ROOT), capture_output=True, text=True,
    )
    if result.returncode == 0:
        print("Pulled and merged corpus.")
        # Report newly-arrived project namespaces (present remotely, absent locally before the pull)
        try:
            new_projects = local_projects() & (remote_projects() - pre_pull_local)
            if new_projects:
                print(f"\nNew project namespace(s) received:")
                print("\n".join(describe_namespaces(new_projects)))
                print("Next: wf status to see inventory, wf query to use them.")
        except Exception as e:
            print(f"  (post-pull namespace report skipped: {e})", file=sys.stderr)
        # #181: the derived plane regenerates here — both machines' copies
        # converge before the next push (cosmetic conflicts never queue)
        _regen_derived()
        return

    # Merge failed: collect conflicts — the DERIVED plane (policy
    # classification, #181) auto-resolves by theirs+regen (regen is the
    # truth; human review of catalog.json noise is meaningless) and the
    # merge can often complete with zero human steps.
    from sync_lib.policy import classify_change as _cls
    conflicts_seen = git_status()
    conflicted_all = [l[3:] for l in conflicts_seen if l.startswith("UU ") or l.startswith("AA ")]
    derived_conflicted = [p for p in conflicted_all if _cls(p) == "derived"]
    conflicted = [p for p in conflicted_all if p not in derived_conflicted]
    # CI-diagnosability: the pull always reports which branch it took
    print(f"  (pull conflicts: {conflicts_seen!r:.200} -> derived={derived_conflicted}, "
          f"content={len(conflicted)})")
    if derived_conflicted and not conflicted:
        for p in derived_conflicted:
            subprocess.run(["git", "checkout", "--theirs", "--", p],
                           cwd=str(VAULT_ROOT), capture_output=True)
        subprocess.run(["git", "commit", "--no-edit", "-q"],
                       cwd=str(VAULT_ROOT), capture_output=True)
        _regen_derived()
        subprocess.run(["git", "add", "-A"], cwd=str(VAULT_ROOT), capture_output=True)
        subprocess.run(["git", "-c", "user.name=wiki-fabric", "-c", "user.email=wf@corpus.local",
                        "commit", "-q", "-m", "sync pull: derived artifacts auto-regenerated"],
                       cwd=str(VAULT_ROOT), capture_output=True)
        print(f"Pull complete — {len(derived_conflicted)} derived artifact(s) auto-resolved "
              "by regen (no human step: the regenerated output is the truth).")
        return
    conflicts_dir = layout.registry(VAULT_ROOT) / "conflicts" / today
    conflicts_dir.mkdir(parents=True, exist_ok=True)

    for p in conflicted:
        # Ours (pre-merge) / theirs (incoming) / joint index file preserved
        ours = sh("show", f"HEAD~1:{p}") if sh("show", f"HEAD~1:{p}") is not None else ""
        theirs = sh("show", f"{CONTENT_REMOTE_NAME}/main:{p}") or ""
        slug = re.sub(r"[^a-z0-9]+", "-", p.lower()).strip("-")[:80]
        joint = VAULT_ROOT / p
        joint_text = joint.read_text(encoding="utf-8", errors="replace") if joint.exists() else ""

        out = conflicts_dir / f"{slug}.md"
        out.write_text(
            f"---\ntype: sync-conflict\npath: {p}\ndate: {today}\nstatus: unresolved\n---\n\n"
            f"# Sync conflict: {p}\n\n"
            f"Two machines changed this file. Review and keep the correct version.\n\n"
            f"## Ours (this machine)\n\n```\n{ours}\n```\n\n"
            f"## Theirs (remote)\n\n```\n{theirs}\n```\n\n"
            f"## Merged working copy (with conflict markers)\n\n```\n{joint_text}\n```\n",
            encoding="utf-8",
        )
        # Keep the merged file with markers for resolution
        print(f"  Conflict → {out.relative_to(VAULT_ROOT)}")

    # Abort the conflicted merge; the working tree stays clean, conflicts are queued
    subprocess.run(["git", "merge", "--abort"], cwd=str(VAULT_ROOT), capture_output=True)

    n = len(conflicted)
    print(f"\n{n} conflict(s) written to registry/conflicts/{date.today().isoformat}/ — merge aborted, nothing silently overwritten.")
    print("Review each conflict file, fix the source page, delete the conflict file, then: wf sync push")
    sys.exit(2)


def main():
    parser = argparse.ArgumentParser(description="Share the corpus via a git remote (source-of-truth sync)")
    parser.add_argument("command", choices=["setup", "init", "migrate", "migrate-team-config", "status", "push", "pull", "resolve", "commit-drift"], help="Sync operation")
    parser.add_argument("remote", nargs="?", help="Git URL for `init`")
    parser.add_argument("name", nargs="?", help="Corpus repo name for `setup` (default: wiki-fabric-corpus)")
    parser.add_argument("-m", "--message", help="Commit message for push")
    parser.add_argument("--public", action="store_true", help="setup: create the corpus repo public (default private)")
    parser.add_argument("--strategy", choices=["ours", "theirs", "union", "derived"], default=None, help="resolve: how to resolve the conflict (derived = regenerate the artifact locally — the #181 class; omit for the interactive flow, #14)")
    parser.add_argument("conflict_file", nargs="?", help="Conflict file (from registry/conflicts/) for `resolve`")
    parser.add_argument("--yes", "-y", action="store_true", help="setup: skip the creation prompt")
    parser.add_argument("--pr", action="store_true",
                        help="push: open a PR for this push even in solo mode (#100 receipts/ownership trail)")
    parser.add_argument("--no-pr", action="store_true",
                        help="push: direct push even in team mode (explicit opt-out)")
    parser.add_argument("--dry-run", action="store_true", help="commit-drift: show the plane + message, write nothing")
    parser.add_argument("--quiet", action="store_true", help="commit-drift: exit-0 report only when drift existed")
    args = parser.parse_args()

    if args.command == "setup":
        cmd_setup(name=args.name, private=not args.public, yes=args.yes)
    elif args.command == "init":
        if not args.remote:
            print("Error: `wf sync init` requires a git URL", file=sys.stderr)
            sys.exit(1)
        cmd_init(args.remote)
    elif args.command == "migrate":
        cmd_migrate(args.remote)
    elif args.command == "status":
        cmd_status()
    elif args.command == "push":
        cmd_push(args.message, pr=args.pr, no_pr=args.no_pr)
    elif args.command == "pull":
        cmd_pull()
    elif args.command == "commit-drift":
        cmd_commit_drift(message=args.message, dry_run=args.dry_run, quiet=args.quiet)
    elif args.command == "resolve":
        conflict = args.conflict_file or args.remote
        if not conflict:
            print("Error: `wf sync resolve` requires a conflict file (from registry/conflicts/)", file=sys.stderr)
            sys.exit(1)
        cmd_resolve(conflict, args.strategy)


if __name__ == "__main__":
    main()
