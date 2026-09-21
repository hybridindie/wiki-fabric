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
import re
import subprocess
import argparse
from pathlib import Path
from datetime import date, datetime
sys.path.insert(0, str(Path(__file__).parent))
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
    """Refuse to sync a non-fabric directory."""
    if not (VAULT_ROOT / "AGENTS.md").exists() or not (VAULT_ROOT / "registry").exists():
        print("Error: not in a wiki-fabric root (missing AGENTS.md + registry/)", file=sys.stderr)
        sys.exit(1)


# === Commands ===

def cmd_init(remote_url):
    validate_fabric()
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
        print("Resolve each, then: wf sync push")

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

    # Block push when conflicts are unresolved
    conflicts = list_conflicts()
    if conflicts:
        print(f"Error: {len(conflicts)} unresolved conflict(s) in registry/conflicts/ — resolve them first:", file=sys.stderr)
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
    parser.add_argument("command", choices=["init", "status", "push", "pull"], help="Sync operation")
    parser.add_argument("remote", nargs="?", help="Git URL for `init`")
    parser.add_argument("-m", "--message", help="Commit message for push")
    args = parser.parse_args()

    if args.command == "init":
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


if __name__ == "__main__":
    main()