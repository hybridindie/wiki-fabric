#!/usr/bin/env python3
# capture.py — Capture knowledge-bearing files from upstream repos into evidence/raw/
#
# Usage:
#   python3 scripts/cmd/capture.py <project-slug>                    # Capture from all declared source_repos
#   python3 scripts/cmd/capture.py <project-slug> --repo <path>      # Capture from a specific repo
#   python3 scripts/cmd/capture.py <project-slug> --dry-run          # Show what would be captured
#
# Reads the project's .wiki-overlay.md source_repos config, copies matching
# files from the upstream repo into evidence/raw/<slug>/, computes sha256,
# and reports new/changed/unchanged files.

import sys
import sys as _s, pathlib as _p
_HERE = _p.Path(__file__).resolve().parent
# Explicit import bootstrap: this script's own dir (same-dir siblings)
# + scripts/lib (shared modules). No shotgun path injection.
for _dir in (_HERE, _HERE.parent / "lib"):
    if str(_dir) not in _s.path:
        _s.path.insert(0, str(_dir))
import re
import hashlib
import shutil
import yaml
import argparse
from pathlib import Path
from datetime import date

from fabric_config import get_config, get_ignores, is_ignored
from fabric_config import CORPUS_ROOT
from wf_common import parse_frontmatter
from fabric_config import FABRIC_ROOT
from fabric_config import CORPUS_ROOT

VAULT_ROOT = CORPUS_ROOT
PROJECTS_DIR = VAULT_ROOT / "projects"
EVIDENCE_RAW = VAULT_ROOT / "evidence" / "raw"


def get_config_safe():
    try:
        from fabric_config import get_config
        return get_config()
    except Exception:
        return {}


args_quiet = False


def sha256(path):
    h = hashlib.sha256()
    h.update(Path(path).read_bytes())
    return h.hexdigest()


def get_source_repos(project_slug):
    """Read source_repos from the project's .wiki-overlay.md in the fabric."""
    overlay_path = PROJECTS_DIR / project_slug / ".wiki-overlay.md"
    if not overlay_path.exists():
        # Also check project root (bootstrap puts it there)
        for candidate in PROJECTS_DIR.glob(f"{project_slug}*/.wiki-overlay.md"):
            overlay_path = candidate
            break

    if not overlay_path.exists():
        # Try the actual project root
        for d in PROJECTS_DIR.iterdir():
            if d.name == project_slug:
                # .wiki-overlay.md is in the project root, not in the fabric namespace
                break
        return []

    fm, _ = parse_frontmatter(overlay_path)
    return fm.get("source_repos", []) or []


def match_globs(repo_path, globs):
    """Find files in repo_path matching the glob patterns."""
    matched = []
    for pattern in globs:
        for f in repo_path.glob(pattern):
            if f.is_file() and not f.name.startswith("."):
                matched.append(f)
    return sorted(set(matched))  # deduplicate


def capture_project(project_slug, repo_filter=None, dry_run=False):
    """Capture knowledge-bearing files from source repos."""
    # Read .wiki-overlay.md from the PROJECT ROOT (not the fabric namespace)
    # The overlay is created by bootstrap in the project's root directory
    project_paths = [
        Path.cwd() if (Path.cwd() / ".wiki-overlay.md").exists() else None,
        Path(project_slug) if Path(project_slug).exists() else None,
        VAULT_ROOT.parent / project_slug,  # sibling of fabric
    ]

    overlay_path = None
    for pp in project_paths:
        if pp and pp.exists():
            candidate = pp / ".wiki-overlay.md"
            if candidate.exists():
                fm, _ = parse_frontmatter(candidate)
                # the overlay must declare the requested namespace — a cwd
                # overlay for a DIFFERENT project must not capture under this
                # slug (cwd bleed: harness root overlay vs requested project)
                if str(fm.get("namespace") or "") == project_slug:
                    overlay_path = candidate
                    break

    # Fallback: check fabric.yaml for repo config
    config_file = FABRIC_ROOT / "fabric.yaml"  # the vault shell, not corpus/
    if not overlay_path and config_file.exists():
        try:
            config = yaml.safe_load(config_file.read_text()) or {}
            repos_cfg = config.get("repos") or {}
            repo_cfg = (repos_cfg or {}).get(project_slug) or {}
            repo_path_str = repo_cfg.get("path", "")
            if repo_path_str:
                # repos paths resolve against FABRIC_ROOT (fabric.yaml lives
                # there; bootstrap writes relpath(project_root, FABRIC_ROOT))
                repo_path = (FABRIC_ROOT / repo_path_str).resolve()
                if repo_path.exists():
                    # prefer the overlay's declared source_repos/globs when
                    # present (the overlay is the project's config; the
                    # fabric.yaml entry only locates the repo)
                    overlay_fm, _ = parse_frontmatter(repo_path / ".wiki-overlay.md")
                    declared = overlay_fm.get("source_repos") if isinstance(overlay_fm, dict) else None
                    if declared:
                        return process_sources(project_slug, declared, repo_filter, dry_run,
                                               project_root=str(repo_path))
                    # Default globs if not specified in overlay
                    source_repos = [{
                        "path": str(repo_path),
                        "raw_path": f"evidence/raw/{project_slug}",
                        "globs": ["*.md", "docs/**/*.md", "AGENTS.md", "README.md", "CONTRIBUTING.md"],
                    }]
                    return process_sources(project_slug, source_repos, repo_filter, dry_run)
        except Exception:
            pass

    if not overlay_path:
        print(f"Error: no .wiki-overlay.md found for project '{project_slug}'", file=sys.stderr)
        print(f"  Searched: {project_paths}", file=sys.stderr)
        sys.exit(1)

    fm, _ = parse_frontmatter(overlay_path)
    source_repos = fm.get("source_repos", [])
    if not source_repos:
        # Self-capture fallback: the overlay lives inside the source repo itself,
        # so the repo is its own upstream. Capture the repo root with default globs.
        repo_root = overlay_path.parent
        print(f"  No source_repos declared — self-capturing from {repo_root}")
        source_repos = [{
            "path": str(repo_root),
            "raw_path": f"evidence/raw/{project_slug}",
            "globs": ["*.md", "AGENTS.md", "README.md", "CONTRIBUTING.md", "docs/**/*.md"],
        }]

    return process_sources(project_slug, source_repos, repo_filter, dry_run, project_root=str(overlay_path.parent))


def process_sources(project_slug, source_repos, repo_filter, dry_run=False, project_root=None):
    """Copy files from source repos into evidence/raw/<slug>/.

    Relative `path:` entries in source_repos resolve against `project_root`
    (the repo containing .wiki-overlay.md) when provided, else the fabric root.
    """
    raw_base = EVIDENCE_RAW / project_slug
    raw_base.mkdir(parents=True, exist_ok=True)

    total_new = 0
    total_changed = 0
    total_unchanged = 0

    for sr in source_repos:
        repo_path = Path(sr.get("path", sr) if isinstance(sr, dict) else sr)
        if not repo_path.is_absolute():
            base = Path(project_root) if project_root else VAULT_ROOT
            repo_path = (base / repo_path).resolve()

        raw_path_str = sr.get("raw_path", f"evidence/raw/{project_slug}") if isinstance(sr, dict) else f"evidence/raw/{project_slug}"
        # Normalize: raw_path may be "evidence/raw/<slug>" or just "<slug>"
        raw_dest = EVIDENCE_RAW / project_slug

        globs = sr.get("globs", ["*.md"]) if isinstance(sr, dict) else ["*.md"]

        repo_name = repo_path.name
        if repo_filter and repo_name != repo_filter and repo_filter not in str(repo_path):
            continue

        if not repo_path.exists():
            print(f"  Warning: repo not found: {repo_path}", file=sys.stderr)
            continue

        # Find matching files
        files = match_globs(repo_path, globs)
        # Exclude-side filter: fabric.yaml ignore globs/regexes (per project slug)
        ignores = get_ignores(get_config(), project_slug)
        before = len(files)
        files = [f for f in files if not is_ignored(f.relative_to(repo_path).as_posix(), ignores)]
        dropped = before - len(files)
        if dropped:
            print(f"    ignored {dropped} file(s) by fabric.yaml ignore rules")

        print(f"  {repo_name}: {len(files)} matching files")

        repo_dest = raw_dest / repo_name
        repo_dest.mkdir(parents=True, exist_ok=True)

        for f in files:
            # Compute relative path within the repo
            rel = f.relative_to(repo_path)
            dest = repo_dest / rel
            dest.parent.mkdir(parents=True, exist_ok=True)

            # Compute hash to detect changes
            src_hash = sha256(f)
            existing_hash = sha256(dest) if dest.exists() else None

            if existing_hash is None:
                status = "NEW"
            elif src_hash != existing_hash:
                status = "CHANGED"
            else:
                status = "unchanged"

            if status in ("NEW", "CHANGED"):
                if not dry_run:
                    shutil.copy2(f, dest)
                if status == "NEW":
                    total_new += 1
                else:
                    total_changed += 1
                    print(f"    {status}: {rel}")
            else:
                total_unchanged += 1

    print()
    print(f"Capture summary: {total_new} new, {total_changed} changed, {total_unchanged} unchanged")
    return total_new, total_changed


def main():
    parser = argparse.ArgumentParser(description="Capture knowledge-bearing files from upstream repos")
    parser.add_argument("project", help="Project slug (e.g. my-project)")
    parser.add_argument("--repo", help="Capture from a specific repo path (overrides overlay)")
    parser.add_argument("--project-root", help="Project root containing .wiki-overlay.md (used by hooks; resolves sibling lookup)")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be captured")
    parser.add_argument("--quiet", action="store_true", help="Only print the summary line (hook-friendly)")
    global args_quiet
    args = parser.parse_args()
    args_quiet = args.quiet

    if not args.quiet:
        print(f"=== Capturing sources for {args.project} ===")
        print()

    if args.repo:
        repo_path = Path(args.repo).resolve()
        if not repo_path.exists():
            print(f"Error: repo not found: {repo_path}", file=sys.stderr)
            sys.exit(1)
        source_repos = [{
            "path": str(repo_path),
            "raw_path": f"evidence/raw/{args.project}",
            "globs": ["*.md", "AGENTS.md", "README.md", "CONTRIBUTING.md", "docs/**/*.md"],
        }]
        new, changed = process_sources(args.project, source_repos, None, args.dry_run)
    elif args.project_root:
        root = Path(args.project_root).resolve()
        overlay = root / ".wiki-overlay.md"
        if not overlay.exists():
            print(f"Error: no .wiki-overlay.md in {root}", file=sys.stderr)
            sys.exit(1)
        fm, _ = parse_frontmatter(overlay)
        source_repos = fm.get("source_repos", [])
        if not source_repos:
            source_repos = [{
                "path": str(root),
                "raw_path": f"evidence/raw/{args.project}",
                "globs": ["*.md", "AGENTS.md", "README.md", "CONTRIBUTING.md", "docs/**/*.md"],
            }]
        new, changed = process_sources(args.project, source_repos, None, args.dry_run, project_root=str(root))
    else:
        new, changed = capture_project(args.project, dry_run=args.dry_run)

    if new + changed > 0 and not args.dry_run and not args.quiet:
        print(f"\nNext: ingest the captured sources:")
        print(f"  python3 scripts/cmd/ingest.py --extract-claims evidence/raw/{args.project}/<file>.md")

    if args.dry_run:
        print("\n[DRY RUN] No files written")

    # Exit code 2 when drift was captured — lets hooks decide to trigger ingest.
    sys.exit(2 if (new + changed) > 0 else 0)


if __name__ == "__main__":
    main()