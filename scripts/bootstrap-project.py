#!/usr/bin/env python3
"""
bootstrap-project.py — Set up a new project to use the global Wiki Fabric

Intelligently detects:
  - Owner name from git config (user.name)
  - LLM config from fabric.yaml or environment
  - Available domains from existing ontology
  - Available skills from global/skills/
  - Whether this is a git repo already

Prompts for anything it can't detect, offering sensible defaults.
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from datetime import date
import re

sys.path.insert(0, str(Path(__file__).parent))
from fabric_config import get_config, FABRIC_ROOT, get_all_repo_names, get_domain_signals


def slugify(text):
    return re.sub(r'--+', '-', re.sub(r'[^a-z0-9]', '-', text.lower())).strip('-')


def find_fabric_root():
    script_dir = Path(__file__).parent.resolve()
    return script_dir.parent


def run_cmd(cmd, cwd=None, check=True):
    result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
    if check and result.returncode != 0:
        raise subprocess.CalledProcessError(result.returncode, cmd, result.stdout, result.stderr)
    return result


def git_config(key):
    """Read a git config value (e.g. user.name), return None if not set."""
    try:
        result = subprocess.run(
            ["git", "config", "--global", key],
            capture_output=True, text=True, timeout=5,
        )
        val = result.stdout.strip()
        return val if val else None
    except Exception:
        return None


def detect_available_domains():
    """Load available domains from fabric.yaml config."""
    config = get_config()
    return sorted(get_domain_signals(config).keys())


def detect_available_skills():
    """Load available skills from the fabric's skills directory."""
    skills_dir = FABRIC_ROOT / "skills"
    if not skills_dir.exists():
        return []
    return sorted(
        f.stem.replace(".md", "") for f in skills_dir.glob("*.md") if f.name != ".gitkeep"
    )


def prompt_with_default(prompt_text, default=None, required=False):
    """Prompt with a default value. Returns the value."""
    if default:
        val = input(f"  {prompt_text} [{default}]: ").strip()
        return val if val else default
    else:
        val = input(f"  {prompt_text}: ").strip()
        while required and not val:
            val = input(f"  {prompt_text} (required): ").strip()
        return val


def prompt_multi(prompt_text, options, default=None):
    """Prompt for multi-select from a list of options. Returns list."""
    print(f"  {prompt_text}:")
    for i, opt in enumerate(options, 1):
        marker = " ←" if default and opt in default else ""
        print(f"    {i}. {opt}{marker}")
    val = input("  Enter numbers or names (comma-separated, empty for default): ").strip()
    if not val:
        return default or []
    result = []
    for part in val.split(","):
        part = part.strip()
        if part.isdigit():
            idx = int(part) - 1
            if 0 <= idx < len(options):
                result.append(options[idx])
        elif part in options:
            result.append(part)
    return result if result else (default or [])


def prompt_yn(prompt_text, default=False):
    """Yes/no prompt. Returns bool."""
    dflt = "Y/n" if default else "y/N"
    val = input(f"  {prompt_text} [{dflt}]: ").strip().lower()
    if not val:
        return default
    return val in ("y", "yes")


def prompt_yes_no(prompt_text, default=False):
    """Yes/no prompt. Returns bool."""
    dflt = "Y/n" if default else "y/N"
    val = input(f"  {prompt_text} [{dflt}]: ").strip().lower()
    if not val:
        return default
    return val in ("y", "yes")


def register_in_fabric_yaml(project_slug, project_root):
    """Add the project to fabric.yaml so all scripts can find it."""
    config_path = FABRIC_ROOT / "fabric.yaml"
    if not config_path.exists():
        print("Warning: fabric.yaml not found; project not registered in config", file=sys.stderr)
        return

    try:
        import yaml
        config = yaml.safe_load(config_path.read_text()) or {}
    except Exception:
        config = {}

    repos = config.setdefault("repos", {})
    rel_path = os.path.relpath(project_root, FABRIC_ROOT)
    repos[project_slug] = {
        "path": rel_path,
        "graph_dir": "graphify-out",
    }

    config_path.write_text(yaml.dump(config, default_flow_style=False, sort_keys=False))
    print(f"Registered {project_slug} in fabric.yaml (path: {rel_path})")


def main():
    parser = argparse.ArgumentParser(
        description="Bootstrap a new project with Wiki Fabric",
        epilog="Run without flags for interactive mode with sensible defaults."
    )
    parser.add_argument("project_root", nargs="?", help="Path to project root directory")
    parser.add_argument("--name", help="Human-readable project name")
    parser.add_argument("--slug", help="Project slug (namespace)")
    parser.add_argument("--domain", action="append", help="Domain to load (repeatable)")
    parser.add_argument("--skill", action="append", help="Global skill to auto-load (repeatable)")
    parser.add_argument("--source-repo", action="append", help="Upstream repo: path:raw_path:globs")
    parser.add_argument("--init-git", action="store_true", help="Initialize git repo")
    parser.add_argument("--non-interactive", action="store_true", help="Skip prompts, use defaults")
    args = parser.parse_args()

    # === Phase 1: Detect what we can ===
    config = get_config()

    git_name = git_config("user.name")
    git_email = git_config("user.email")
    available_domains = detect_available_domains()
    available_skills = detect_available_skills()
    existing_repos = get_all_repo_names(config)

    # Owner: git config > fabric.yaml > prompt
    owner = config.get("owner", "you")
    if owner == "you" and git_name:
        owner = git_name

    # === Phase 2: Prompt for what we need ===
    if not args.non_interactive:
        print("╔════════════════════════════════════════════╗")
        print("║   Wiki Fabric — Project Bootstrap          ║")
        print("╚════════════════════════════════════════════╝")
        print()
    else:
        print("=== Bootstrapping project (non-interactive) ===")
        print()

    # Project root
    project_root_str = args.project_root
    if not project_root_str and not args.non_interactive:
        project_root_str = prompt_with_default("Project root directory", os.getcwd())
    if not project_root_str:
        print("Error: project-root required", file=sys.stderr)
        sys.exit(1)
    project_root = Path(project_root_str).resolve()

    # Project name
    project_name = args.name
    if not project_name and not args.non_interactive:
        default_name = project_root.name if project_root.exists() else project_root_str
        project_name = prompt_with_default("Project name", default_name)
    if not project_name:
        project_name = project_root.name if project_root.exists() else project_root_str

    # Project slug
    project_slug = args.slug
    if not project_slug and not args.non_interactive:
        default_slug = slugify(project_name)
        project_slug = prompt_with_default("Project slug (namespace)", default_slug)
    if not project_slug:
        project_slug = slugify(project_name)

    # Domains
    domains = args.domain
    if not domains and not args.non_interactive:
        domains = prompt_multi("Domains to load", available_domains, default=["agent-systems"])
    if not domains:
        domains = ["agent-systems"]

    # Skills
    skills = args.skill
    if not skills and not args.non_interactive:
        default_skills = [s for s in available_skills if s == "serialize-and-verify-writes"]
        if not default_skills:
            default_skills = available_skills[:1]
        skills = prompt_multi("Skills to auto-load", available_skills, default=default_skills)
    if not skills:
        skills = ["serialize-and-verify-writes"]

    # Owner confirmation (only if not already in fabric.yaml)
    fabric_yaml_path = FABRIC_ROOT / "fabric.yaml"
    if not args.non_interactive and (not fabric_yaml_path.exists() or owner == "you"):
        new_owner = prompt_with_default("Your name (for promotion dossiers)", git_name or "you")
        if new_owner != owner:
            # Update fabric.yaml
            try:
                import yaml as yaml_mod
                existing_yaml = yaml_mod.safe_load(fabric_yaml_path.read_text()) if fabric_yaml_path.exists() else {}
                existing_yaml["owner"] = new_owner
                fabric_yaml_path.write_text(yaml_mod.dump(existing_yaml, default_flow_style=False, sort_keys=False))
                print(f"  Updated fabric.yaml owner → {new_owner}")
            except Exception:
                pass
            owner = new_owner

    # Summary (only in interactive mode — let user confirm)
    if not args.non_interactive:
        print()
        print("  ── Configuration ──")
        print(f"  Project:    {project_name}")
        print(f"  Slug:       {project_slug}")
        print(f"  Root:       {project_root}")
        print(f"  Domains:    {', '.join(domains)}")
        print(f"  Skills:     {', '.join(skills)}")
        print(f"  Owner:      {owner}")
        print()
        if not prompt_yes_no("Proceed with bootstrap?", default=True):
            print("Aborted.")
            sys.exit(0)
        print()

    # === Phase 3: Execute ===
    project_root = Path(project_root_str).resolve()
    project_root.mkdir(parents=True, exist_ok=True)
    os.chdir(project_root)

    # Git init if needed
    if args.init_git and not Path(".git").exists():
        run_cmd("git init -q")
        print("Initialized git repository")

    # 1. Create .wiki-overlay.md
    domains_yaml = "\n".join(f"  - {d}" for d in domains)
    skills_yaml = "\n".join(f"  - {s}" for s in skills) if skills else "  # - serialize-and-verify-writes"
    today = date.today().isoformat()

    source_repos = args.source_repo or []
    if source_repos:
        source_repos_yaml = ""
        for repo in source_repos:
            path, raw_path, globs = repo.split(":", 2)
            globs_list = globs.split(",")
            globs_yaml = "\n".join(f'      - "{g}"' for g in globs_list)
            source_repos_yaml += f"""  - path: {path}
    raw_path: {raw_path}
    globs:
{globs_yaml}
"""
    else:
        source_repos_yaml = """  # - path: ../upstream-repo
  #   raw_path: evidence/raw/upstream-repo
  #   globs:
  #     - "*.md"
  #     - "docs/**/*.md"
"""

    overlay_content = f"""---
project: {project_name}
namespace: {project_slug}
description: {project_name}
owner: {owner}
domains:
{domains_yaml}
skills:
{skills_yaml}
source_repos:
{source_repos_yaml}
created: {today}
updated: {today}
---

# Project Overlay: {project_name}

This file configures how the global Wiki Fabric connects to this project.
"""
    Path(".wiki-overlay.md").write_text(overlay_content)
    print("Created .wiki-overlay.md")

    # 2. Create/Update opencode config (additive merge)
    WIKI_FABRIC_BLOCK = {
        "references": {
            "wiki-fabric": {
                "path": "~/wiki-fabric",
                "description": "Global knowledge fabric (evidence-first wiki + cross-project promotion)"
            }
        },
        "instructions_add": ["~/wiki-fabric/AGENTS.md", ".wiki-overlay.md"],
        "watcher_ignore_add": ["evidence/raw/**", ".obsidian/**"],
        "skills_paths_add": ["~/wiki-fabric/system/.opencode/skills"]
    }

    oc_candidates = [Path("opencode.json"), Path(".opencode/opencode.json")]
    oc_path = next((c for c in oc_candidates if c.exists()), None)

    if oc_path:
        import json as json_mod
        try:
            existing = json_mod.loads(oc_path.read_text())
        except Exception:
            existing = {}

        refs = existing.setdefault("references", {})
        for key, val in WIKI_FABRIC_BLOCK["references"].items():
            refs.setdefault(key, val)
        instrs = existing.setdefault("instructions", [])
        for item in WIKI_FABRIC_BLOCK["instructions_add"]:
            if item not in instrs:
                instrs.append(item)
        watcher = existing.setdefault("watcher", {})
        ignores = watcher.setdefault("ignore", [])
        for item in WIKI_FABRIC_BLOCK["watcher_ignore_add"]:
            if item not in ignores:
                ignores.append(item)
        skills_cfg = existing.setdefault("skills", {})
        paths = skills_cfg.setdefault("paths", [])
        for item in WIKI_FABRIC_BLOCK["skills_paths_add"]:
            if item not in paths:
                paths.append(item)

        oc_path.write_text(json_mod.dumps(existing, indent=2))
        print(f"Merged wiki-fabric config into {oc_path}")
    else:
        config = {
            "$schema": "https://opencode.ai/config.json",
            "references": WIKI_FABRIC_BLOCK["references"],
            "instructions": WIKI_FABRIC_BLOCK["instructions_add"],
            "watcher": {"ignore": WIKI_FABRIC_BLOCK["watcher_ignore_add"]},
            "skills": {"paths": WIKI_FABRIC_BLOCK["skills_paths_add"]}
        }
        Path("opencode.json").write_text(json.dumps(config, indent=2))
        print("Created opencode.json")

    # 3. Create .gitignore additions
    gitignore = Path(".gitignore")
    if not gitignore.exists():
        gitignore.touch()
    gitignore_content = gitignore.read_text()
    for line in ["evidence/raw/", ".obsidian/", ".DS_Store", "*.pyc", "__pycache__/"]:
        if line not in gitignore_content:
            with open(".gitignore", "a") as f:
                f.write(line + "\n")
    print("Updated .gitignore")

    # 4. Initial commit if requested
    if args.init_git and not Path(".git").exists():
        run_cmd("git add -A")
        run_cmd("git commit -q -m 'chore: initial commit from wiki-fabric bootstrap'")
        print("Initialized git repository with initial commit")

    # 5. Create project namespace in the fabric
    namespace_dir = find_fabric_root() / "projects" / project_slug
    (namespace_dir / "experience-events").mkdir(parents=True, exist_ok=True)
    (namespace_dir / "decisions").mkdir(parents=True, exist_ok=True)
    print(f"Created project namespace: {namespace_dir.relative_to(find_fabric_root())}")

    # 6. Register in fabric.yaml
    register_in_fabric_yaml(project_slug, str(project_root))

    # 7. Create LLM config file for the project
    llm_env_path = project_root / ".env.wiki-fabric"
    if not llm_env_path.exists():
        config = get_config()
        llm_env_path.write_text(f"""# Wiki Fabric LLM configuration
# Source these before running fabric scripts:
#   set -a; . .env.wiki-fabric; set +a
WIKI_LLM_BASE_URL={config["llm"]["base_url"]}
WIKI_LLM_API_KEY={config["llm"]["api_key"]}
WIKI_LLM_MODEL={config["llm"]["model"]}
""")
        print("Created .env.wiki-fabric (LLM configuration)")

    print(f"""
=== Project bootstrap complete ===

Project:   {project_name} ({project_slug})
Owner:     {owner}
Namespace: {namespace_dir.relative_to(find_fabric_root())}

Created files:
  .wiki-overlay.md          - Project overlay config
  .env.wiki-fabric          - LLM config (source before running fabric scripts)
  .gitignore                - Updated with wiki-fabric ignores

Next steps:
  1. Capture sources: cp upstream docs → evidence/raw/{project_slug}/
  2. Ingest: python3 ~/wiki-fabric/scripts/ingest.py --extract-claims evidence/raw/{project_slug}/<doc>.md
  3. Log experience: python3 ~/wiki-fabric/scripts/log-experience.py --project {project_slug}
  4. Verify: python3 ~/wiki-fabric/scripts/lint.py .
  5. Ask questions: python3 ~/wiki-fabric/scripts/query.py "..."
""")


if __name__ == "__main__":
    main()