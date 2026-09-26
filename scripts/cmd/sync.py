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
#   wf sync init <git-url>       # set up the content remote (creates corpus branch)
#   wf sync status               # show local vs remote divergence
#   wf sync push                 # commit + push local content changes
#   wf sync pull                 # fetch + merge remote content; conflicts → review queue
#
# Conflict policy: same-path edits from two machines are moved to
# registry/conflicts/ with both versions preserved. Nothing is silently
# overwritten. Lint treats unresolved conflicts as errors until reviewed.

import sys
import sys as _s, pathlib as _p
_HERE = _p.Path(__file__).resolve().parent
# Explicit import bootstrap: this script's own dir (same-dir siblings)
# + scripts/lib (shared modules). No shotgun path injection.
for _dir in (_HERE, _HERE.parent / "lib"):
    if str(_dir) not in _s.path:
        _s.path.insert(0, str(_dir))
import re
import subprocess
import argparse
import shutil
from pathlib import Path
from datetime import date, datetime
from wf_common import parse_frontmatter
from fabric_config import FABRIC_ROOT
from fabric_config import CORPUS_ROOT
from fabric_config import CORPUS_ROOT

VAULT_ROOT = CORPUS_ROOT
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

LOCAL_ONLY_PATHS = [
    "fabric.yaml",       # machine-specific config
    "opencode.json",     # machine-specific editor config
    ".obsidian",         # editor workspace
    ".venv",             # python env
]


def sh(*args, cwd=None):
    """Run a git command; return stdout or None on failure."""
    try:
        out = subprocess.run(
            ["git"] + [str(a) for a in args],
            cwd=str(cwd or VAULT_ROOT), capture_output=True, text=True, timeout=120,
        )
        return out.stdout if out.returncode == 0 else None
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return None


def local_projects():
    """Project namespaces that exist locally."""
    pd = VAULT_ROOT / "projects"
    if not pd.exists():
        return set()
    return {p.name for p in pd.iterdir() if p.is_dir() and not p.name.startswith(".")}


def remote_projects():
    """Project namespaces that exist on the remote corpus."""
    listing = sh("ls-tree", "--name-only", f"{CONTENT_REMOTE_NAME}/corpus", "--", "projects/")
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
        readme = VAULT_ROOT / "projects" / name / "README.md"
        title = name
        owner = ""
        if readme.exists():
            try:
                import yaml
                fm = yaml.safe_load(readme.read_text().split("---")[1]) or {}
                title = fm.get("title") or name
                owner = fm.get("owner") or ""
            except Exception:
                pass
        out.append(f"  projects/{name}/ — {title}" + (f" (owner: {owner})" if owner else ""))
    return out


def git_status():
    out = sh("status", "--porcelain")
    return [l for l in (out or "").splitlines() if l.strip()]


def is_content_path(path_str):
    p = path_str.lstrip('"').strip()
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
    """Refuse to sync a non-fabric directory. A fresh corpus may lack the
    AGENTS.md marker — scaffold it from the harness rather than failing
    (same gap install-time teammate onboarding hit; the corpus needs the
    marker for git validation, the harness clone has the source)."""
    registry = VAULT_ROOT / "registry"
    registry.mkdir(parents=True, exist_ok=True)
    if not (VAULT_ROOT / "AGENTS.md").exists():
        harness = Path(__file__).resolve().parent.parent.parent
        src_ag = harness / "AGENTS.md"
        if src_ag.exists():
            shutil.copy(src_ag, VAULT_ROOT / "AGENTS.md")
            print(f"Scaffolded corpus/AGENTS.md (from harness) — sync marker")
    if not (VAULT_ROOT / "AGENTS.md").exists() or not registry.exists():
        print("Error: not in a wiki-fabric root (missing AGENTS.md + registry/)", file=sys.stderr)
        sys.exit(1)


# === Commands ===



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


def cmd_init(remote_url):
    validate_fabric()
    scaffold_ci_workflow()
    if get_remote():
        print(f"Corpus remote already set: {get_remote()}")
        print(f"Change it with: git remote set-url {CONTENT_REMOTE_NAME} <url>")
        sys.exit(1)

    # Verify the remote is reachable and is (or can be) a corpus
    ok = sh("ls-remote", remote_url, "HEAD") is not None
    if not ok:
        print(f"Error: cannot reach remote {remote_url} (does it exist? do you have access?)", file=sys.stderr)
        sys.exit(1)

    sh("remote", "add", CONTENT_REMOTE_NAME, remote_url)

    # Push the full corpus as the initial source of truth
    print(f"Pushing initial corpus to {remote_url} (branch: corpus)...")
    local_head = sh("rev-parse", "HEAD")
    if not local_head:
        print("Error: local repo has no commits — commit your fabric first", file=sys.stderr)
        sys.exit(1)
    if sh("push", CONTENT_REMOTE_NAME, f"{local_head.strip()}:refs/heads/corpus") is None:
        print("Error: push failed (check access rights)", file=sys.stderr)
        sh("remote", "remove", CONTENT_REMOTE_NAME)
        sys.exit(1)
    sh("fetch", CONTENT_REMOTE_NAME, "corpus")

    print()
    print(f"✓ Corpus remote configured: {CONTENT_REMOTE_NAME} → {remote_url}")
    print("  Team members: clone your fabric, then:")
    print(f"    git remote add corpus {remote_url}")
    print(f"    git fetch corpus corpus && git checkout corpus")




def cmd_setup(name=None, private=True, yes=False):
    """First-class corpus setup: create (or adopt) the GitHub corpus repo and
    wire + publish this fabric's corpus as the source of truth.

    Uses the gh CLI when available (detection + auth check); falls back to
    printing manual git instructions otherwise. Human-gated: prompts unless
    --yes."""
    validate_fabric()
    scaffold_ci_workflow()

    # 1. gh CLI detection + auth
    def _run(args, timeout=30):
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


def cmd_status():
    validate_fabric()
    remote = get_remote()
    if not remote:
        print("No corpus remote configured. Set one up: wf sync init <git-url>")
        sys.exit(1)

    sh("fetch", CONTENT_REMOTE_NAME, "corpus")
    local = sh("rev-parse", "HEAD")
    remote_head = sh("rev-parse", f"{CONTENT_REMOTE_NAME}/corpus")

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


def cmd_push(message=None):
    validate_fabric()
    if not get_remote():
        print("No corpus remote. Run: wf sync init <git-url>", file=sys.stderr)
        sys.exit(1)

    # LOUD pre-check: fetch and compare. Pushing over a moved remote is the
    # multi-writer failure mode — be loud BEFORE the push, not after git
    # rejects it (#'s team-sync hardening).
    sh("fetch", CONTENT_REMOTE_NAME, "corpus")
    remote_head = sh("rev-parse", f"{CONTENT_REMOTE_NAME}/corpus")
    local_head = sh("rev-parse", "HEAD")
    # behind = remote has commits local lacks. Ancestor check, not sha
    # equality: after a sync pull (merge), local HEAD is a merge commit whose
    # sha differs from the remote head even though it CONTAINS it — a sha
    # equality check false-blocked every post-pull push (found in the
    # two-machine race test).
    behind = None
    ahead = 0
    if remote_head and local_head:
        anc = sh("merge-base", "--is-ancestor", f"{CONTENT_REMOTE_NAME}/corpus", "HEAD")
        if anc is not None:
            behind = 0
            ahead_n = sh("rev-list", "--count", f"{CONTENT_REMOTE_NAME}/corpus..HEAD")
            ahead = int(ahead_n) if ahead_n else 0
        else:
            behind = int(sh("rev-list", "--count", f"HEAD..{CONTENT_REMOTE_NAME}/corpus") or 0)
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
    else:
        for l in changes:
            p = l[3:].lstrip('"').rstrip('"')
            subprocess.run(["git", "add", "--", p], cwd=str(VAULT_ROOT))
        msg = message or f"sync {date.today().isoformat()} ({len(changes)} files)"
        if subprocess.run(["git", "commit", "-m", msg], cwd=str(VAULT_ROOT), capture_output=True).returncode != 0:
            print("Error: commit failed (nothing to commit or hook rejected)", file=sys.stderr)
            sys.exit(1)
        print(f"Committed {len(changes)} corpus files: {msg}")

    head = sh("rev-parse", "HEAD")
    if sh("push", CONTENT_REMOTE_NAME, f"{head.strip()}:refs/heads/corpus") is None:
        print("Error: push rejected — remote has newer commits. Run: wf sync pull", file=sys.stderr)
        sys.exit(1)
    print("Pushed corpus to remote.")


def list_conflicts():
    conflicts_dir = VAULT_ROOT / "registry" / "conflicts"
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
    unblocks; the resolution is committed so the push carries the decision."""
    validate_fabric()
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
    subprocess.run(["git", "commit", "-q", "-m", msg], cwd=str(VAULT_ROOT), capture_output=True)

    print(f"Resolved [{strategy}]: {path} — {resolution}")
    print(f"Conflict record removed; SYNC-CONFLICT gate cleared for this file.")
    print("Next: wf sync pull — if the same file conflicts again, resolve with")
    print("  'ours' (your resolution already carries the union) — then push.")
def cmd_pull():
    validate_fabric()
    if not get_remote():
        print("No corpus remote. Run: wf sync init <git-url>", file=sys.stderr)
        sys.exit(1)

    sh("fetch", CONTENT_REMOTE_NAME, "corpus")
    remote_head = sh("rev-parse", f"{CONTENT_REMOTE_NAME}/corpus")
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
        subprocess.run(["git", "commit", "-m", f"sync local changes before pull ({stamp})"],
                       cwd=str(VAULT_ROOT), capture_output=True)
        print(f"Committed {len(changes)} local corpus changes before merging.")

    pre_pull_local = local_projects()

    # Merge remote corpus branch (allow unrelated histories: two fabrics that
    # share a remote but no common ancestor are still the same corpus)
    today = date.today().isoformat()
    result = subprocess.run(
        ["git", "merge", f"{CONTENT_REMOTE_NAME}/corpus", "--no-edit", "--allow-unrelated-histories",
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
        except Exception:
            pass
        return

    # Merge failed: collect conflicts
    conflicted = [l[3:] for l in git_status() if l.startswith("UU ") or l.startswith("AA ")]
    conflicts_dir = VAULT_ROOT / "registry" / "conflicts" / today
    conflicts_dir.mkdir(parents=True, exist_ok=True)

    for p in conflicted:
        # Ours (pre-merge) / theirs (incoming) / joint index file preserved
        ours = sh("show", f"HEAD~1:{p}") if sh("show", f"HEAD~1:{p}") is not None else ""
        theirs = sh("show", f"{CONTENT_REMOTE_NAME}/corpus:{p}") or ""
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
    parser.add_argument("command", choices=["setup", "init", "status", "push", "pull", "resolve"], help="Sync operation")
    parser.add_argument("remote", nargs="?", help="Git URL for `init`")
    parser.add_argument("name", nargs="?", help="Corpus repo name for `setup` (default: wiki-fabric-corpus)")
    parser.add_argument("-m", "--message", help="Commit message for push")
    parser.add_argument("--public", action="store_true", help="setup: create the corpus repo public (default private)")
    parser.add_argument("--strategy", choices=["ours", "theirs", "union"], default=None, help="resolve: how to resolve the conflict")
    parser.add_argument("conflict_file", nargs="?", help="Conflict file (from registry/conflicts/) for `resolve`")
    parser.add_argument("--yes", "-y", action="store_true", help="setup: skip the creation prompt")
    args = parser.parse_args()

    if args.command == "setup":
        cmd_setup(name=args.name, private=not args.public, yes=args.yes)
    elif args.command == "init":
        if not args.remote:
            print("Error: `wf sync init` requires a git URL", file=sys.stderr)
            sys.exit(1)
        cmd_init(args.remote)
    elif args.command == "status":
        cmd_status()
    elif args.command == "push":
        cmd_push(args.message)
    elif args.command == "pull":
        cmd_pull()
    elif args.command == "resolve":
        conflict = args.conflict_file or args.remote
        if not conflict:
            print("Error: `wf sync resolve` requires a conflict file (from registry/conflicts/)", file=sys.stderr)
            sys.exit(1)
        cmd_resolve(conflict, args.strategy)


if __name__ == "__main__":
    main()