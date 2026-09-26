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
import sys as _s, pathlib as _p
_HERE = _p.Path(__file__).resolve().parent
# Explicit import bootstrap: this script's own dir (same-dir siblings)
# + scripts/lib (shared modules). No shotgun path injection.
for _dir in (_HERE, _HERE.parent / "lib"):
    if str(_dir) not in _s.path:
        _s.path.insert(0, str(_dir))
from pathlib import Path
from datetime import date
import re

from fabric_config import get_config, FABRIC_ROOT, CORPUS_ROOT, get_all_repo_names, get_domain_signals


def slugify(text):
    return re.sub(r'--+', '-', re.sub(r'[^a-z0-9]', '-', text.lower())).strip('-')


def find_fabric_root():
    # Content root: honors WIKI_FABRIC_DIR via fabric_config; falls back to the
    # harness parent in dev mode.
    try:
        from fabric_config import FABRIC_ROOT
        return FABRIC_ROOT
    except Exception:
        return Path(__file__).parent.resolve().parent


def find_harness_root():
    # Code root: where the scripts live (may differ from the fabric in
    # installed mode).
    try:
        from fabric_config import HARNESS_ROOT
        return HARNESS_ROOT
    except Exception:
        return Path(__file__).parent.resolve().parent


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
    skills_dir = CORPUS_ROOT / "skills"
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

    # "repos:" followed only by comments parses as None — setdefault won't
    # replace an existing None key, so coerce explicitly.
    repos = config.get("repos")
    if not isinstance(repos, dict):
        repos = {}
    config["repos"] = repos
    rel_path = os.path.relpath(project_root, FABRIC_ROOT)
    repos[project_slug] = {
        "path": rel_path,
        "graph_dir": "graphify-out",
    }

    config_path.write_text(yaml.dump(config, default_flow_style=False, sort_keys=False))
    print(f"Registered {project_slug} in fabric.yaml (path: {rel_path})")


def get_corpus_remote():
    """Return the corpus remote URL if the fabric is wired for team sync."""
    try:
        result = subprocess.run(
            ["git", "remote", "get-url", "corpus"],
            cwd=str(FABRIC_ROOT), capture_output=True, text=True, timeout=10,
        )
        return result.stdout.strip() if result.returncode == 0 else None
    except Exception:
        return None


def write_namespace_readme(namespace_dir, project_slug, project_name, owner, source_repos):
    """Write a small README into the project namespace — it syncs to the corpus
    so teammates can see what this project is without asking."""
    readme = namespace_dir / "README.md"
    if readme.exists():
        return
    try:
        import yaml as _yaml
        config = _yaml.safe_load((FABRIC_ROOT / "fabric.yaml").read_text()) or {}
    except Exception:
        config = {}
    repos = (config.get("repos") or {}).get(project_slug, {})
    upstream = repos.get("path", "")
    repos_yaml = upstream or "_(none yet — add source_repos to .wiki-overlay.md)_"
    readme.write_text(f"""---
type: registry
project: {project_slug}
title: {project_name}
created: {__import__('datetime').date.today().isoformat()}
owner: {owner}
---

# Project: {project_name}

Namespace `projects/{project_slug}/` — bootstrapped by `{owner}` on the machine that owns this corpus entry.

## Purpose

{project_name} connected to the shared fabric.

## Upstream sources

- {repos_yaml}

## Layout

- `experience-events/` — structured observations (problem → intervention → outcome)
- `decisions/` — ADR-like technical choices
""")
    print(f"Wrote namespace README: {readme.relative_to(FABRIC_ROOT)}")


def main():
    parser = argparse.ArgumentParser(
        description="Bootstrap a new project with Wiki Fabric",
        epilog="Interactive walkthrough: overlay, routing, hooks, capture, ingest, query. Without flags: prompts at each step. Use --non-interactive to skip."
    )
    parser.add_argument("project_root", nargs="?", help="Path to project root directory")
    parser.add_argument("--name", help="Human-readable project name")
    parser.add_argument("--slug", help="Project slug (namespace)")
    parser.add_argument("--domain", action="append", help="Domain to load (repeatable)")
    parser.add_argument("--skill", action="append", help="Global skill to auto-load (repeatable)")
    parser.add_argument("--source-repo", action="append", help="Upstream repo: path:raw_path:globs")
    parser.add_argument("--extract", default=None, help="Stage route: local | cloud | model id (raw docs — highest sensitivity)")
    parser.add_argument("--synthesize", default=None, help="Stage route: local | cloud | model id (sanitized claims)")
    parser.add_argument("--dossier", default=None, help="Stage route: local | cloud | model id (experience events)")
    parser.add_argument("--graph-dir", default=None, help="Per-repo graphify graph dir (default: integrations.graphify.graph_dir)")
    parser.add_argument("--init-git", action="store_true", help="Initialize git repo")
    parser.add_argument("--no-hook", action="store_true", help="Skip the git post-commit hook (default: installed, capture-only)")
    parser.add_argument("--hook-extract-claims", action="store_true", help="Hook also runs LLM claim extraction on drift")
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
        routing_keys = {"extract": args.extract, "synthesize": args.synthesize,
                        "dossier": args.dossier, "graph_dir": args.graph_dir}
        if any(v for v in routing_keys.values()):
            routes = ", ".join(f"{k}={v}" for k, v in routing_keys.items() if v)
            print(f"  Routing:    {routes}")
        else:
            print(f"  Routing:    all stages cloud (default)")
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

    # Per-project LLM routing + integration config (lives in the overlay so it
    # versions with the project repo; fabric.yaml stays fabric-global).
    routing_keys = {"extract": args.extract, "synthesize": args.synthesize,
                    "dossier": args.dossier, "graph_dir": args.graph_dir}
    if not args.non_interactive and not any(v for v in routing_keys.values()):
        # Interactive routing prompt (privacy tiering) unless flags given
        print()
        print("  LLM routing for this project (stage: where raw docs / claims /")
        print("  experience events are compiled — privacy + quality tiering):")
        print("    1) cloud — compiler model, fastest [default]")
        print("    2) local — on-device (GGUF/MLX), zero egress")
        for stage in ("extract", "synthesize", "dossier"):
            choice = input(f"    {stage} [1]: ").strip()
            if choice == "2":
                routing_keys[stage] = "local"
        print()
    routing_yaml = ""
    if any(v for v in routing_keys.values()):
        routing_yaml = "# LLM stage routing + integration (per-project; overrides fabric defaults)\nrouting:\n"
        for k, v in routing_keys.items():
            if v:
                routing_yaml += f"  {k}: {v}\n"
        routing_yaml += "\n"

    overlay_content = f"""---
project: {project_name}
namespace: {project_slug}
description: {project_name}
owner: {owner}
domains:
{domains_yaml}
skills:
{skills_yaml}
{routing_yaml}source_repos:
{source_repos_yaml}
created: {today}
updated: {today}
---

# Project Overlay: {project_name}

This file configures how the global Wiki Fabric connects to this project —
including LLM stage routing and integration settings. It is the project's
config; the fabric discovers it (see fabric.yaml repos.auto_discover).
"""
    Path(".wiki-overlay.md").write_text(overlay_content)
    print("Created .wiki-overlay.md")

    # 2. Create/Update opencode config (additive merge)
    # Resolve harness/fabric locations at bootstrap time (never hard-code
    # home-relative guesses — the harness may live anywhere).
    harness_root = find_harness_root()
    fabric_root = find_fabric_root()
    WIKI_FABRIC_BLOCK = {
        "references": {
            "wiki-fabric": {
                "path": str(fabric_root),
                "description": "Global knowledge fabric (evidence-first wiki + cross-project promotion)"
            }
        },
        "instructions_add": [str(fabric_root / "AGENTS.md"), ".wiki-overlay.md"],
        "watcher_ignore_add": ["evidence/raw/**", ".obsidian/**"],
        "skills_paths_add": [str(harness_root / "system" / "opencode" / "skills")]
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

    # 2b. Install the wiki-fabric opencode plugin (session-start nudge)
    plugin_src = find_harness_root() / "system" / "opencode" / "plugins" / "wiki-fabric.js"
    plugin_dst = Path(".opencode") / "plugins" / "wiki-fabric.js"
    if plugin_src.exists() and not plugin_dst.exists():
        plugin_dst.parent.mkdir(parents=True, exist_ok=True)
        plugin_dst.write_text(plugin_src.read_text())
        print("Installed .opencode/plugins/wiki-fabric.js (session nudge)")

    # 2c. Multi-harness support: install always-on + skills into every detected
    # agent harness (Claude Code, Codex, Copilot, Cursor, Gemini CLI, ...).
    try:
        harnesses_py = find_harness_root() / "scripts" / "harness/harnesses.py"
        if harnesses_py.exists():
            import importlib.util as _hlu
            hspec = _hlu.spec_from_file_location("harnesses", str(harnesses_py))
            hmod = _hlu.module_from_spec(hspec)
            hspec.loader.exec_module(hmod)
            targets = hmod.detect_installed(Path.cwd())
            if targets:
                block = hmod.body_from(harness_root / "system" / "always-on" / "wiki-fabric-block.md")
                n = 0
                for spec in targets:
                    written = hmod.install_instructions(spec, Path.cwd(), block)
                    written += hmod.install_skills(spec, Path.cwd(), harness_root)
                    for w in written:
                        print(f"  harness [{spec['name']}]: {w.relative_to(Path.cwd())}")
                    n += len(written)
                if n:
                    print(f"Configured {len(targets)} agent harness(es) ({n} files)")
    except Exception as e:
        print(f"  (harness setup skipped: {e})", file=sys.stderr)

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

    # 5. Create project namespace in the fabric (corpus content root —
    # every consumer resolves projects/ under CORPUS_ROOT; FABRIC_ROOT
    # is the vault shell, not the content root)
    namespace_dir = find_fabric_root() / "corpus" / "projects" / project_slug
    if not (find_fabric_root() / "corpus").exists():
        # pre-corpus layout: content dirs live at the fabric root
        namespace_dir = find_fabric_root() / "projects" / project_slug
    (namespace_dir / "experience-events").mkdir(parents=True, exist_ok=True)
    (namespace_dir / "decisions").mkdir(parents=True, exist_ok=True)
    print(f"Created project namespace: {namespace_dir}")

    # 5a. Cold-start vocabulary: on the FIRST project (empty ontology), derive
    # provisional domains from this project's own structural evidence — the
    # vocabulary builds itself rather than shipping hardcoded defaults.
    # Written as PROPOSALS: they become ontology domains after human review
    # (promote-domains --apply), or are used as this project's routing scope.
    try:
        ontology = fabric_root / "corpus" / "domains" / "ontology.md"
        ontology_has_domains = ontology.exists() and "## Domains" in ontology.read_text() \
            and bool(re.search(r"## Domains\n\n- ", ontology.read_text()))
        if not ontology_has_domains:
            import importlib.util as _ilu
            _spec = _ilu.spec_from_file_location(
                "propose_domains", fabric_root / "scripts" / "cmd" / "propose-domains.py")
            _pd = _ilu.module_from_spec(_spec)
            _spec.loader.exec_module(_pd)
            detected = _pd.structural_domains(project_root)
            if detected:
                top = [d for d, _ in detected.most_common(3)]
                print(f"  Cold-start vocabulary: structural scan detected {top}")
                # provisional domains: recorded in the ontology doc as proposed
                header = ('---\ntype: ontology\ntitle: Domain Ontology\n'
                          f'created: {date.today().isoformat()}\n---\n\n## Domains\n')
                onto_src = ontology.read_text() if ontology.exists() else header
                if "## Domains" in onto_src:
                    onto_src = onto_src.replace(
                        "## Domains",
                        "## Domains\n\n"
                        + "\n".join(f"- `{d}` (proposed, structural scan of {project_slug})"
                                    for d in top) + "\n",
                        1)
                    ontology.parent.mkdir(parents=True, exist_ok=True)
                    ontology.write_text(onto_src)
                    print(f"  Ontology: proposed {top} (human review: promote-domains --apply)")
                # route this project to its detected domains
                domains = top
            else:
                print("  No structural signals detected — project runs without domains")
    except Exception as _e:
        print(f"  (domain bootstrap skipped: {_e})")

    # 5b. Vault freshness: write the fabric-side overlay view + refresh links
    try:
        harness_root = find_harness_root()
        vr = fabric_root / "scripts" / "cmd/vault-refresh.py"
        if vr.exists():
            import importlib.util as _ilu
            spec = _ilu.spec_from_file_location("vault_refresh", str(vr))
            vrmod = _ilu.module_from_spec(spec)
            spec.loader.exec_module(vrmod)
            vault_path = vrmod.default_vault_path()
            if vault_path.exists():
                vrmod.refresh(vault_path)
    except Exception as e:
        print(f"  (vault refresh skipped: {e})", file=sys.stderr)

    # 5a. Namespace README → syncs to the corpus so teammates see what this project is
    write_namespace_readme(namespace_dir, project_slug, project_name, owner, args.source_repo or [])

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

    # 8. Corpus awareness: is this fabric wired for team sync?
    corpus_remote = get_corpus_remote()
    if corpus_remote:
        print(f"Corpus remote detected: {corpus_remote}")
        print(f"This project is local-only until you run: wf sync push")
        print(f"Teammates receive it on their next: wf sync pull")
    else:
        print("Note: no corpus remote configured — this project is local-only.")
        print("To share it with a team (gh CLI creates + publishes the corpus repo):")
        print("  wf sync setup          # creates <owner>/wiki-fabric-corpus (private) and publishes")
        print("  wf sync init <git-url> # or point at an existing repo, then: wf sync push")

    # 8b. Extraction routing (interactive): privacy tiering per stage
    import sys as _sys
    if not args.non_interactive and _sys.stdin.isatty():
        print()
        print("  Extraction routing for this project:")
        print("    cloud = deepseek (4-6s/doc, default)")
        print("    local = gemma4 MLX (34s/doc, zero egress — for sensitive repos)")
        if input("  Route extraction/synthesis LOCAL (privacy)? [y/N]: ").strip().lower() in ("y", "yes"):
            _routing_cfg = find_fabric_root() / "fabric.yaml"
            try:
                import yaml as _yaml
                _rc = _yaml.safe_load(_routing_cfg.read_text()) or {}
                _repos = _rc.get("repos") or {}
                _rcfg = _repos.get(project_slug) or {}
                _rcfg["extract"] = "local"
                _rcfg["synthesize"] = "local"
                _repos[project_slug] = _rcfg
                _rc["repos"] = _repos
                _yaml.safe_dump(_rc, open(_routing_cfg, "w"), sort_keys=False, allow_unicode=True)
                print(f"  ✓ extract + synthesize routed local for {project_slug}")
            except Exception as e:
                print(f"  (routing write failed: {e})")

    # 9. Git hook (default on — the freshness guarantee depends on it):
    # post-commit captures doc drift (0 tokens); --no-hook skips;
    # --hook-extract-claims additionally compiles drift with the LLM.
    if args.no_hook:
        print("Hook install skipped (--no-hook) — doc drift will wait for manual capture.")
    else:
        import subprocess as _sp
        hooks_py = find_fabric_root() / "scripts" / "harness/hooks.py"
        hook_cmd = [_sp.sys.executable, str(hooks_py), "install"]
        if args.hook_extract_claims:
            hook_cmd.append("--extract-claims")
        r = _sp.run(hook_cmd, cwd=project_root, capture_output=True, text=True)
        if r.returncode == 0:
            print(r.stdout.strip())
            print("Hook installed — doc drift now auto-captures on commit (WIKI_SKIP_HOOK=1 to skip per command).")
        else:
            print(f"Hook install failed: {r.stderr.strip()}", file=_sp.sys.stderr)

    # Interactive walkthrough: offer capture + ingest + verify now
    import sys as _sys
    if not args.non_interactive and _sys.stdin.isatty():
        print()
        print("─── Onboarding walkthrough ───")
        print()
        if input(f"  Capture upstream docs now? [Y/n]: ").strip().lower() not in ("n", "no"):
            r = subprocess.run(
                [_sys.executable, str(find_fabric_root() / "scripts" / "cmd/capture.py"),
                 project_slug, "--project-root", str(project_root)],
                capture_output=True, text=True)
            print(r.stdout.strip() or r.stderr.strip())
            captured_n = sum(1 for line in r.stdout.splitlines() if "matching" in line.lower())
            if input("\n  Ingest captured sources with LLM claim extraction? [Y/n]: ").strip().lower() not in ("n", "no"):
                ingest_cmd = [_sys.executable, str(find_fabric_root() / "scripts" / "cmd/ingest.py"),
                              "--changed", project_slug, "--extract-claims"]
                if input("  Workers for concurrent extraction [8]: ").strip():
                    ingest_cmd += ["--workers", "8"]
                print("  (this may take a few minutes per document)")
                r2 = subprocess.run(ingest_cmd, capture_output=False, text=True)
                if input("\n  Run a test query to verify the fabric? [Y/n]: ").strip().lower() not in ("n", "no"):
                    q = input("  Question [what is this project about?]: ").strip() or "what is this project about?"
                    r3 = subprocess.run(
                        [_sys.executable, str(find_fabric_root() / "scripts" / "cmd/query.py"), q],
                        capture_output=False, text=True)

    print(f"""
=== Project bootstrap complete ===

Project:   {project_name} ({project_slug})
Owner:     {owner}
Namespace: {namespace_dir.relative_to(find_fabric_root())}

Created files:
  .wiki-overlay.md          - Project overlay config
  .env.wiki-fabric          - LLM config (source before running fabric scripts)
  .gitignore                - Updated with wiki-fabric ignores

Ongoing:
  wf capture {project_slug}        # re-capture upstream docs (or auto via hook)
  wf query "..."                   # ask the fabric questions
  wf log --project {project_slug}  # log experience events (feeds promotion)
  wf lint                          # health check (0 errors before commit)
""")


if __name__ == "__main__":
    main()