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

from fabric_config import get_config, FABRIC_ROOT, CORPUS_ROOT, get_all_repo_names, get_domain_signals, get_owner, OWNER_SENTINEL


# slugify: shared helper (wf_common) — local copies were the drift class; the
# collapse-with-dashes form the prompt flow wants is what wf_common.slugify does.
from wf_common import slugify

import layout


def find_fabric_root():
    # Content root — the canonical chain lives in fabric_config (composed of
    # paths.py primitives, #152). FABRIC_ROOT IS that chain, frozen at import.
    return FABRIC_ROOT


def find_harness_root():
    # Code root: where the scripts live (may differ from the fabric in
    # installed mode) — paths.py (#152).
    import paths
    return paths.find_harness_root()


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
    skills_dir = layout.skills(CORPUS_ROOT)
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
def prompt_yes_no(prompt_text, default=False):
    """Yes/no prompt. Returns bool."""
    dflt = "Y/n" if default else "y/N"
    val = input(f"  {prompt_text} [{dflt}]: ").strip().lower()
    if not val:
        return default
    return val in ("y", "yes")


def register_in_fabric_yaml(project_slug, project_root, owner="", args=None):
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
    entry = {
        "path": rel_path,
        "graph_dir": "graphify-out",
    }
    if owner:
        entry["owner"] = owner
    # Explicit routing flags are personal machine overrides (privacy tiering
    # may legitimately differ per teammate) — carried here, machine-local.
    # The SHARED routing comes from the overlay. get_repo_config: explicit
    # fabric.yaml keys win over the overlay.
    for k in ("extract", "synthesize", "dossier"):
        val = getattr(args, k, None) if args else None
        if val:
            entry[k] = val
            entry.setdefault("routing", {})[k] = val
    graph_dir = (getattr(args, "graph_dir", None) if args else None) or "graphify-out"
    entry["graph_dir"] = graph_dir
    repos[project_slug] = entry

    from fabric_config import save_config
    save_config(config, path=config_path)
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


def _detect_environment(config):
    """Phase 1: detect what we can (git identity, available domains/skills)."""
    config = get_config()

    git_name = git_config("user.name")
    git_email = git_config("user.email")
    available_domains = detect_available_domains()
    available_skills = detect_available_skills()
    existing_repos = get_all_repo_names(config)

    # Owner: the one chain (fabric_config.get_owner — #155-B: yaml > git >
    # sentinel 'you'); the interactive prompt below refines it in the UI layer.
    owner = get_owner(config)


    return {"git_name": git_name, "git_email": git_email,
            "available_domains": available_domains, "available_skills": available_skills,
            "existing_repos": existing_repos, "owner": owner}


def _collect_config(args, env):
    """Phase 2: resolve project root/name/slug/domains/skills/owner.
    Flags win over prompts; prompts only when a human is attached.
    Returns (project_root_str, project_name, project_slug, domains, skills, owner)."""
    available_domains = env["available_domains"]
    available_skills = env["available_skills"]
    git_name = env["git_name"]
    owner = env["owner"]

    # Explicit flags (--name/--slug/--domain/--skill/--extract/...) skip their
    # own prompt; when EVERYTHING material is flagged, skip the confirmation
    # too — a fully-specified invocation should never abort on a prompt
    # (sim finding: piped answers + flags aborted confusingly).
    everything_flagged = bool(args.name or args.slug or args.domain or args.skill
                               or args.extract or args.synthesize
                               or args.dossier or args.graph_dir)
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
    if not domains and not args.non_interactive and sys.stdin.isatty():
        # Default NONE: a new project starts clean — domains are self-building
        # (the ontology grows from this project's own evidence), and seeding
        # another repo's domains here would mix unrelated signals. Suggest
        # nothing; the owner opts in deliberately.
        domains = prompt_multi("Domains to load (none recommended — ontology self-builds)",
                               available_domains, default=[])
        if not domains:
            print("  (no domains — ontology will build from this project's evidence)")
    if not domains:
        domains = []

    # Skills
    skills = args.skill
    if not skills and not args.non_interactive and sys.stdin.isatty():
        # prompt only when a human is attached AND no explicit skill flags —
        # flag-driven automation (everything_flagged or partial flags) defaults
        default_skills = [s for s in available_skills if s == "serialize-and-verify-writes"]
        if not default_skills:
            default_skills = available_skills[:1]
        skills = prompt_multi("Skills to auto-load", available_skills, default=default_skills)
    if not skills:
        skills = ["serialize-and-verify-writes"]

    # Owner confirmation (only if not already in fabric.yaml)
    fabric_yaml_path = FABRIC_ROOT / "fabric.yaml"
    if not args.non_interactive and (not fabric_yaml_path.exists() or owner == "you"):
        new_owner = prompt_with_default("Your name (for promotion dossiers)", owner if owner != OWNER_SENTINEL else OWNER_SENTINEL)
        if new_owner != owner:
            # Update fabric.yaml (save_config invalidates the config cache, #153)
            try:
                from fabric_config import save_config
                import yaml as yaml_mod
                existing_yaml = yaml_mod.safe_load(fabric_yaml_path.read_text()) if fabric_yaml_path.exists() else {}
                existing_yaml["owner"] = new_owner
                save_config(existing_yaml, path=fabric_yaml_path)
                print(f"  Updated fabric.yaml owner → {new_owner}")
            except Exception:
                pass  # owner write failed → session-local value (config update is best-effort)
            owner = new_owner

    # Summary (only in interactive mode — let user confirm; a fully-flagged
    # invocation skips the confirmation: everything was explicit already)
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
        if not everything_flagged and not prompt_yes_no("Proceed with bootstrap?", default=True):
            print("Aborted.")
            sys.exit(0)
        print()

    return (project_root_str, project_name, project_slug, domains, skills, owner, everything_flagged)


def _bootstrap_git_init(args):
    """Phase 0: cd into the project root + git init when requested."""
    project_root = Path(args._project_root_str).resolve()
    project_root.mkdir(parents=True, exist_ok=True)
    os.chdir(project_root)
    args._project_root = project_root
    if args.init_git and not Path(".git").exists():
        run_cmd("git init -q")
        print("Initialized git repository")


def _bootstrap_overlay(args, project_name, project_slug, domains, skills, owner):
    """Phase 1: write .wiki-overlay.md. Returns the routing dict decided."""
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
    decided = {k: v for k, v in routing_keys.items() if v}
    if not decided:
        # derive from the fabric's decided llm config (cloud default)
        decided = {"extract": "cloud", "synthesize": "cloud", "dossier": "cloud"}
    routing_yaml = "# Decided routing (fabric llm config; per-repo overrides in machine fabric.yaml)\nrouting:\n"
    for k, v in decided.items():
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
    return decided


def _ensure_fabric_compiler_model(args):
    """First-bootstrap compiler-model decision (#155 audit: this block lived
    inline and referenced fabric_yaml_path — a local of _collect_config, a
    latent NameError on the no-compiler-model path)."""
    from fabric_config import get_config as _get_config
    _llm = (get_config() or {}).get("llm") or {}
    _compiler = _llm.get("compiler_model") or _llm.get("model") or ""
    if not _compiler and not args.non_interactive and sys.stdin.isatty():
        print()
        print("  No model decided in fabric.yaml yet — choose the compiler model")
        print("  (OpenAI-compatible id; local ids need llm.local_model too):")
        _compiler = input("    compiler model [deepseek-v4.1-flash:cloud]: ").strip() \
            or "deepseek-v4.1-flash:cloud"
        try:
            from fabric_config import save_config
            import yaml as yaml_mod
            fabric_yaml_path = FABRIC_ROOT / "fabric.yaml"
            _cfg = yaml_mod.safe_load(fabric_yaml_path.read_text()) if fabric_yaml_path.exists() else {}
            _cfg.setdefault("llm", {})["compiler_model"] = _compiler
            local_model = input("    local model id (blank to skip): ").strip()
            if local_model:
                _cfg["llm"]["local_model"] = local_model
            save_config(_cfg, path=fabric_yaml_path)
            print(f"  Updated fabric.yaml llm → compiler {_compiler}")
        except Exception as _e:
            print(f"  warn: could not write model to fabric.yaml: {_e}", file=sys.stderr)
    return _compiler


def _bootstrap_agent_configs(harness_root, fabric_root):
    """Phase 2: opencode config merge + plugin + multi-harness install."""
    WIKI_FABRIC_BLOCK = {
        "references": {
            "wiki-fabric": {
                "path": str(fabric_root),
                "description": "Global knowledge fabric (evidence-first wiki + cross-project promotion)"
            }
        },
        "instructions_add": [str(fabric_root / "AGENTS.md"), ".wiki-overlay.md"],
        "watcher_ignore_add": ["evidence/raw/**", ".obsidian/**"],
        "skills_paths_add": [str(harness_root / "system" / "opencode" / "skills")]  # harness assets, not corpus — guard-exempt
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
    _install_opencode_plugin(harness_root)
    _install_harness_assets(harness_root)


def _install_opencode_plugin(harness_root):
    """Phase 2b: the wiki-fabric opencode plugin (session-start nudge)."""
    plugin_src = harness_root / "system" / "opencode" / "plugins" / "wiki-fabric.js"
    plugin_dst = Path(".opencode") / "plugins" / "wiki-fabric.js"
    if plugin_src.exists() and not plugin_dst.exists():
        plugin_dst.parent.mkdir(parents=True, exist_ok=True)
        plugin_dst.write_text(plugin_src.read_text())
        print("Installed .opencode/plugins/wiki-fabric.js (session nudge)")


def _install_harness_assets(harness_root):
    """Phase 2c: always-on + skills into every detected agent harness."""
    try:
        harnesses_py = harness_root / "scripts" / "harness/harnesses.py"
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


def _bootstrap_gitignore_and_commit(args):
    """Phases 3-4: .gitignore additions + initial commit when requested."""
    gitignore = Path(".gitignore")
    if not gitignore.exists():
        gitignore.touch()
    gitignore_content = gitignore.read_text()
    for line in ["evidence/raw/", ".obsidian/", ".DS_Store", "*.pyc", "__pycache__/"]:
        if line not in gitignore_content:
            with open(".gitignore", "a") as f:
                f.write(line + "\n")
    print("Updated .gitignore")

    if args.init_git and not Path(".git").exists():
        run_cmd("git add -A")
        run_cmd("git commit -q -m 'chore: initial commit from wiki-fabric bootstrap'")
        print("Initialized git repository with initial commit")


def _stage_overlay_git(args, repo_root=None):
    """H4 (#180): the overlay ALWAYS reaches the project repo — 'versioned
    with the project repo' (configuration.md) was false for every bootstrap
    on a pre-existing repo: git add ran only under --init-git. The second
    machine's project clone then carries NO overlay (silent config loss).
    Stages + commits when the repo exists (best-effort, idempotent).
    repo_root: explicit target (tests; None = cwd, bootstrap's convention)."""
    _root = Path(repo_root) if repo_root else Path.cwd()
    overlay = _root / ".wiki-overlay.md"
    if not overlay.exists():
        return
    probe = subprocess.run(["git", "-C", str(_root), "rev-parse", "--is-inside-work-tree"],
                           capture_output=True, text=True)
    if probe.returncode != 0 or probe.stdout.strip() != "true":
        return  # not a git repo (--init-git's own add covers new repos)
    tracked = subprocess.run(["git", "-C", str(_root), "ls-files", "--", ".wiki-overlay.md"],
                             capture_output=True, text=True)
    if tracked.stdout.strip():
        return  # already tracked — nothing to do
    subprocess.run(["git", "-C", str(_root), "add", "--", ".wiki-overlay.md"], check=False)
    commit = subprocess.run(
        ["git", "-C", str(_root),
         "-c", "user.name=wiki-fabric", "-c", "user.email=wf@corpus.local",
         "commit", "-m",
         "chore: track .wiki-overlay.md (the fabric config travels with the repo — H4)"],
        capture_output=True, text=True)
    if commit.returncode == 0:
        print("Overlay committed (travels with the repo — H4)")
    else:
        print("Overlay STAGED (commit it with your next task commit — H4)")


def _bootstrap_fabric_side(fabric_root, harness_root, project_root, project_slug, project_name, owner, args, domains):
    """Phases 5-5b + 6: namespace, cold-start vocabulary, vault refresh,
    namespace README, fabric.yaml registration."""
    namespace_dir = fabric_root / "corpus" / "projects" / project_slug
    if not (fabric_root / "corpus").exists():
        # pre-corpus layout: content dirs live at the fabric root
        namespace_dir = fabric_root / "projects" / project_slug
    (namespace_dir / "experience-events").mkdir(parents=True, exist_ok=True)
    (namespace_dir / "decisions").mkdir(parents=True, exist_ok=True)
    print(f"Created project namespace: {namespace_dir}")

    domains = _cold_start_vocabulary(fabric_root, harness_root, project_root, project_slug, domains)
    _refresh_fabric_vault(fabric_root, harness_root)
    write_namespace_readme(namespace_dir, project_slug, project_name, owner, args.source_repo or [])
    register_in_fabric_yaml(project_slug, str(project_root), owner=owner, args=args)
    return namespace_dir


def _cold_start_vocabulary(fabric_root, harness_root, project_root, project_slug, domains):
    """Phase 5a: on the FIRST project (empty ontology), derive provisional
    domains from this project's structural evidence. Written as PROPOSALS
    (promote-domains --apply makes them ontology domains)."""
    try:
        ontology = fabric_root / "corpus" / "domains" / "ontology.md"
        ontology_has_domains = ontology.exists() and "## Domains" in ontology.read_text() \
            and bool(re.search(r"## Domains\n\n- ", ontology.read_text()))
        if not ontology_has_domains:
            import importlib.util as _ilu
            _spec = _ilu.spec_from_file_location(
                "propose_domains", harness_root / "scripts" / "cmd" / "propose-domains.py")
            _pd = _ilu.module_from_spec(_spec)
            _spec.loader.exec_module(_pd)
            detected = _pd.structural_domains(project_root)
            if detected:
                top = [d for d, _ in detected.most_common(3)]
                print(f"  Cold-start vocabulary: structural scan detected {top}")
                                # proposals are DOSSIERS (the sanctioned staging shape —
                # backtick bullets inside ## Domains parsed nowhere and looked
                # merged-but-weren't); promote-domains --apply merges them.
                prop_dir = None
                for cand in (fabric_root / "corpus" / "registry" / "domain-proposals",
                             fabric_root / "registry" / "domain-proposals"):
                    if cand.parent.exists():
                        prop_dir = cand
                        break
                if prop_dir is not None:
                    prop_dir.mkdir(parents=True, exist_ok=True)
                    for d in top:
                        dp = prop_dir / f"domain-{d}.md"
                        if dp.exists():
                            continue
                        dp.write_text(
                            f"---\ntype: change-set\ndomain: {d}\nstatus: proposed\n"
                            f"created: {date.today().isoformat()}\n---\n\n"
                            f"# Domain Proposal: {d}\n\n"
                            f"Structural scan of {project_slug} (bootstrap cold start).\n")
                    ontology.parent.mkdir(parents=True, exist_ok=True)
                    if not ontology.exists():
                        ontology.write_text(
                            '---\ntype: ontology\ntitle: Domain Ontology\n'
                            f'created: {date.today().isoformat()}\n---\n\n## Domains\n')
                    print(f"  Domain proposals staged: {top} (human review: promote-domains --apply)")
                return top
            else:
                print("  No structural signals detected — project runs without domains")
    except Exception as _e:
        print(f"  (domain bootstrap skipped: {_e})")
    return domains


def _refresh_fabric_vault(fabric_root, harness_root):
    """Phase 5b: fabric-side overlay view + refresh links."""
    try:
        vr = harness_root / "scripts" / "cmd/vault-refresh.py"
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


def _bootstrap_project_env(project_root, project_slug, args):
    """Phase 7: the project's .env.wiki-fabric (LLM configuration)."""
    llm_env_path = project_root / ".env.wiki-fabric"
    if not llm_env_path.exists():
        config = get_config()
        llm_env_path.write_text(f"""# Wiki Fabric LLM configuration
# Source these before running fabric scripts:
#   set -a; . .env.wiki-fabric; set +a
WIKI_LLM_OPS_MODEL={config["llm"]["ops_model"]}
WIKI_LLM_COMPILER_MODEL={config["llm"].get("compiler_model", "")}
""")
        print("Created .env.wiki-fabric (LLM configuration)")


def _bootstrap_sync_note():
    """Phase 8: corpus-awareness note (local-only vs team sync)."""
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


def _bootstrap_routing(args, project_slug):
    """Phase 8b (interactive): privacy tiering for extract/synthesize."""
    if not args.non_interactive and sys.stdin.isatty():
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
                from fabric_config import save_config
                save_config(_rc, path=_routing_cfg)
                print(f"  ✓ extract + synthesize routed local for {project_slug}")
            except Exception as e:
                print(f"  (routing write failed: {e})")


def _bootstrap_hook(args, project_root, project_slug):
    """Phase 9: git post-commit hook (default on — the freshness guarantee)."""
    if args.no_hook:
        print("Hook install skipped (--no-hook) — doc drift will wait for manual capture.")
        return
    import subprocess as _sp
    hooks_py = find_harness_root() / "scripts" / "harness/hooks.py"
    hook_cmd = [_sp.sys.executable, str(hooks_py), "install"]
    if args.hook_extract_claims:
        hook_cmd.append("--extract-claims")
    r = _sp.run(hook_cmd, cwd=project_root, capture_output=True, text=True)
    if r.returncode == 0:
        print(r.stdout.strip())
        print("Hook installed — doc drift now auto-captures on commit (WIKI_SKIP_HOOK=1 to skip per command).")
    else:
        print(f"Hook install failed: {r.stderr.strip()}", file=_sp.sys.stderr)


def _bootstrap_walkthrough(args, project_root, project_slug):
    """Interactive capture → ingest → query walkthrough."""
    if not args.non_interactive and sys.stdin.isatty():
        print()
        print("─── Onboarding walkthrough ───")
        print()
        if input(f"  Capture upstream docs now? [Y/n]: ").strip().lower() not in ("n", "no"):
            r = subprocess.run(
                [sys.executable, str(find_fabric_root() / "scripts" / "cmd/capture.py"),
                 project_slug, "--project-root", str(project_root)],
                capture_output=True, text=True)
            print(r.stdout.strip() or r.stderr.strip())
            captured_n = sum(1 for line in r.stdout.splitlines() if "matching" in line.lower())
            if input("\n  Ingest captured sources with LLM claim extraction? [Y/n]: ").strip().lower() not in ("n", "no"):
                ingest_cmd = [sys.executable, str(find_fabric_root() / "scripts" / "cmd/ingest.py"),
                              "--changed", project_slug, "--extract-claims"]
                if input("  Workers for concurrent extraction [8]: ").strip():
                    ingest_cmd += ["--workers", "8"]
                print("  (this may take a few minutes per document)")
                r2 = subprocess.run(ingest_cmd, capture_output=False, text=True)
                if input("\n  Run a test query to verify the fabric? [Y/n]: ").strip().lower() not in ("n", "no"):
                    q = input("  Question [what is this project about?]: ").strip() or "what is this project about?"
                    r3 = subprocess.run(
                        [sys.executable, str(find_fabric_root() / "scripts" / "cmd/query.py"), q],
                        capture_output=False, text=True)


def _bootstrap_summary(project_name, project_slug, owner, namespace_dir):
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


def _print_dry_run(args, project_root_str, project_name, project_slug, domains, skills, owner):
    """--dry-run: the plan, nothing written (issue #166)."""
    project_root = Path(project_root_str).resolve()
    fabric_root = find_fabric_root()
    namespace_dir = layout.projects(fabric_root)
    print("[DRY RUN] Bootstrap plan — nothing executed, nothing written\n")
    print(f"Project:   {project_name} ({project_slug})")
    print(f"Root:      {project_root}" + (" (git init)" if args.init_git and not (project_root / ".git").exists() else ""))
    print(f"Owner:     {owner}")
    print(f"Domains:   {', '.join(domains) or '(none)'}")
    print(f"Skills:    {', '.join(skills) or '(none)'}")
    print(f"Hook:      {'skipped (--no-hook)' if args.no_hook else 'git post-commit auto-capture' + (' + claim extraction' if args.hook_extract_claims else '')}")
    if args.extract or args.synthesize or args.dossier or args.graph_dir:
        routes = []
        if args.extract:
            routes.append(f"extract={args.extract}")
        if args.synthesize:
            routes.append(f"synthesize={args.synthesize}")
        if args.dossier:
            routes.append(f"dossier={args.dossier}")
        if args.graph_dir:
            routes.append(f"graph_dir={args.graph_dir}")
        print(f"Routing:   {', '.join(routes)}")
    namespace_dir = namespace_dir / project_slug
    print("\nWould create:")
    print(f"  {project_root}/.wiki-overlay.md          (overlay: namespace/domains/skills/source_repos)")
    if not (project_root / ".env.wiki-fabric").exists():
        print(f"  {project_root}/.env.wiki-fabric          (LLM config)")
    if args.init_git and not (project_root / ".git").exists():
        print(f"  {project_root}/.git                      (git init)")
    print(f"  {namespace_dir / 'experience-events'}/    (project namespace)")
    print(f"  {namespace_dir / 'decisions'}/")
    print(f"  {namespace_dir / 'README.md'}            (namespace readme)")
    print(f"  fabric.yaml                              (repos.{project_slug} entry)")
    print("\nNext after real run:")
    print(f"  wf capture {project_slug}")
    print(f"  wf ingest --changed {project_slug} --extract-claims")
    print(f"  wf query \"...\"")


def _execute_bootstrap(args, project_root_str, project_name, project_slug, domains, skills, owner, everything_flagged):
    """Bootstrap, phase-by-phase (#155 audit: was one 393-line function).
    Phase functions live above; this is the orchestrator + state threading."""
    if getattr(args, "dry_run", False):
        _print_dry_run(args, project_root_str, project_name, project_slug, domains, skills, owner)
        return
    args._project_root_str = project_root_str
    _bootstrap_git_init(args)
    project_root = args._project_root
    fabric_root = find_fabric_root()
    harness_root = find_harness_root()

    _ensure_fabric_compiler_model(args)
    _bootstrap_overlay(args, project_name, project_slug, domains, skills, owner)
    _bootstrap_agent_configs(harness_root, fabric_root)
    _bootstrap_gitignore_and_commit(args)
    _stage_overlay_git(args)  # H4: the overlay ALWAYS reaches the repo (the
    # second-machine path depends on it — git add alone (no commit; the
    # human's next commit carries it) when the repo predates bootstrap)
    namespace_dir = _bootstrap_fabric_side(fabric_root, harness_root, project_root, project_slug,
                                           project_name, owner, args, domains)
    _bootstrap_project_env(project_root, project_slug, args)
    _bootstrap_sync_note()
    _bootstrap_routing(args, project_slug)
    _bootstrap_hook(args, project_root, project_slug)
    _bootstrap_walkthrough(args, project_root, project_slug)
    _bootstrap_summary(project_name, project_slug, owner, namespace_dir)


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
    parser.add_argument("--dry-run", action="store_true", help="Print the plan (phases + files that would be created), write nothing")
    args = parser.parse_args()
    config = get_config()

    env = _detect_environment(config)
    owner = env["owner"]
    (project_root_str, project_name, project_slug, domains, skills, owner, everything_flagged) = _collect_config(args, env)
    _execute_bootstrap(args, project_root_str, project_name, project_slug, domains, skills, owner, everything_flagged)
    return 0


if __name__ == "__main__":
    main()