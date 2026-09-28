"""wf — the full-python dispatcher (phase 2 of #118).

Replaces the bash orchestrator: every verb maps to the shipped script it
always ran, executed with the right interpreter (a venv next to the fabric
when one exists, else this tool's interpreter). The bash orchestrator's
careful UX (status inventory, install/update flows) is ported verbatim in
this package; the corpus stays git-native (content ≠ code).

Windows: pure python — no bash dependency anywhere in the dispatch path.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import Callable

# --- script/asset resolution (dev tree or packaged _harness) --------------

_PACKAGED = Path(__file__).resolve().parent / "_harness"


def harness_root() -> Path:
    """The shipped tool tree (scripts/, system/, templates/...)."""
    if (_PACKAGED / "scripts").exists():
        return _PACKAGED
    return Path(__file__).resolve().parent.parent.parent


def find_fabric() -> Path | None:
    """Fabric root (content + config) — mirrors fabric_config's chain and the
    bash find_fabric, ordered the same way:
      1. $WIKI_FABRIC_DIR  2. cwd-sibling vault (dev)  3. XDG default.
    Returns None when no fabric exists (commands needing content fail cleanly)."""
    env = os.environ.get("WIKI_FABRIC_DIR")
    if env and Path(env).expanduser().is_dir():
        return Path(env).expanduser().resolve()
    cwd = Path.cwd()
    for d in (cwd, *cwd.parents):
        if (d / "scripts" / "wiki-fabric.sh").exists() and (d / "scripts" / "cmd").is_dir():
            break  # harness tree: not a fabric
        if (d / "fabric.yaml").exists() or (d / "evidence").exists() or (d / "projects").exists():
            return d.resolve()
    # dev sibling vault
    sibling = harness_root().parent / "vault"
    if (sibling / "corpus").exists() or (sibling / "evidence").exists():
        return sibling
    xdg = os.environ.get("XDG_DATA_HOME") or str(Path.home() / ".local" / "share")
    default = Path(xdg) / "wiki-fabric"
    if default.is_dir():
        return default
    return None


def corpus_root(fabric_dir: Path) -> Path:
    """CORPUS_ROOT resolution (mirrors fabric_config): nested corpus/ when
    present, else the fabric root itself (pre-corpus layout)."""
    corpus = fabric_dir / "corpus"
    if (corpus / "evidence").exists() or (corpus / "fabric.yaml").exists():
        return corpus
    if (fabric_dir / "evidence").exists() or (fabric_dir / "projects").exists():
        return fabric_dir
    return corpus


def _python(fabric_dir: Path | None) -> str:
    """Interpreter preference: a venv next to the fabric, else sys.executable
    (this tool's own interpreter — it carries the deps)."""
    if fabric_dir:
        venv = fabric_dir / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
        if venv.exists():
            return str(venv)
    return sys.executable


def _run_script(fabric_dir: Path | None, rel: str, *args: str, timeout: int = 600) -> int:
    """run_script() equivalent: run a shipped script with the right python,
    inheriting stdout/stderr (the tool UX is the script's UX)."""
    script = _harness(rel)
    interpreter = _python(fabric_dir)
    result = subprocess.run([interpreter, str(script), *args], timeout=timeout)
    return result.returncode


def _harness(rel: str) -> Path:
    """Path to a shipped script."""
    p = harness_root() / rel
    if not p.exists():
        raise SystemExit(f"wiki-fabric: broken install — missing {rel}")
    return p


def _fail(msg: str) -> int:
    print(msg, file=sys.stderr)
    return 1


# === Verbs ================================================================

VERBS: dict[str, Callable] = {}


def verb(*names):
    def register(fn):
        for v in names:
            VERBS[v] = fn
        return fn
    return register


def _require_fabric() -> Path:
    fdir = find_fabric()
    if fdir is None:
        print("Fabric not found. Run: wf install", file=sys.stderr)
        raise SystemExit(1)
    return fdir


def _simple_script(rel: str, argv: list[str], timeout: int = 600) -> int:
    """Verbs that pass argv straight through to a shipped script."""
    fdir = find_fabric()
    return _run_script(fdir, rel, *argv, timeout=timeout)


# content verbs (argv passthrough)
@verb("query")
def _query(argv): return _simple_script("scripts/cmd/query.py", argv)
@verb("thread")
def _thread(argv): return _simple_script("scripts/cmd/thread.py", argv)
@verb("ingest")
def _ingest(argv): return _simple_script("scripts/cmd/ingest.py", argv)
@verb("review")
def _review(argv): return _simple_script("scripts/cmd/review.py", argv)
@verb("gate")
def _gate(argv): return _simple_script("scripts/cmd/gate.py", argv)
@verb("promote-domains")
def _promote_domains(argv): return _simple_script("scripts/cmd/promote-domains.py", argv)
@verb("promote-patterns")
def _promote_patterns(argv): return _simple_script("scripts/cmd/promote-patterns.py", argv)
@verb("propose-domains")
def _propose_domains(argv): return _simple_script("scripts/cmd/propose-domains.py", argv)
@verb("harvest-questions")
def _harvest_questions(argv): return _simple_script("scripts/cmd/harvest-questions.py", argv)
@verb("promote-questions")
def _promote_questions(argv): return _simple_script("scripts/cmd/promote-questions.py", argv)
@verb("sync")
def _sync(argv): return _simple_script("scripts/cmd/sync.py", argv)


@verb("context")
def _context(argv):
    fdir = find_fabric()
    if not argv or argv[0] in ("-h", "--help"):
        print('Usage: wf context --task "<task>" [--paths <code/path>] '
              "[--project <slug>] [--format json] [--max N]", file=sys.stderr)
        return 1
    return _run_script(fdir, "scripts/cmd/context.py", *argv)


@verb("lint")
def _lint(argv):
    fdir = find_fabric()
    if "--okf" in argv:
        return _run_script(fdir, "scripts/cmd/lint.py", *argv)
    target = next((a for a in argv if not a.startswith("-")), None)
    if target is None:
        argv = [str(corpus_root(fdir))] + argv
    return _run_script(fdir, "scripts/cmd/lint.py", *argv)


@verb("doctor")
def _doctor(argv):
    return _run_script(find_fabric(), "scripts/cmd/doctor.py", *argv)


@verb("rebuild-index")
def _rebuild_index(argv):
    return _run_script(find_fabric(), "scripts/cmd/rebuild-index.py", *argv)


@verb("utility")
def _utility(argv):
    return _run_script(find_fabric(), "scripts/cmd/utility.py", *argv)


@verb("publish")
def _publish(argv):
    return _run_script(find_fabric(), "scripts/cmd/publish-wiki.py", *argv)


@verb("log")
def _log(argv):
    return _run_script(find_fabric(), "scripts/cmd/log-experience.py", *argv)


@verb("capture")
def _capture(argv):
    if argv and argv[0] == "chat":
        rest = argv[1:]
        if not rest:
            print("Usage: wf capture chat <project-slug> [--since 30d] "
                  "[--limit 20] [--harness opencode|claude|codex|gemini|all] [--dry-run]",
                  file=sys.stderr)
            return 1
        return _run_script(find_fabric(), "scripts/cmd/capture-chat.py", *rest)
    if not argv:
        print("Usage: wf capture <project-slug> [--repo <path>] [--git <owner/name>]",
              file=sys.stderr)
        return 1
    fdir = find_fabric()
    # git-capture passthrough: capture <slug> --git <repo> ...
    if "--git" in argv or "--repo" in argv:
        project = argv[0]
        grepo = argv[argv.index("--git") + 1] if "--git" in argv else argv[argv.index("--repo") + 1]
        return _run_script(fdir, "scripts/cmd/capture-git.py", project, "--repo", grepo,
                           *argv[2:] if len(argv) > 2 else [])
    return _run_script(fdir, "scripts/cmd/capture.py", *argv)


@verb("export")
def _export(argv):
    if argv and argv[0] == "wiki":
        return _run_script(find_fabric(), "scripts/cmd/export-wiki.py", *argv[1:])
    print("Usage: wf export wiki [--push] [--project <slug>] [--dry-run]", file=sys.stderr)
    return 1


@verb("hook")
def _hook(argv):
    sub = argv[0] if argv else "status"
    return _run_script(find_fabric(), "scripts/harness/hooks.py", sub, *argv[1:])


@verb("claude")
def _claude(argv):
    sub = argv[0] if argv else "install"
    return _run_script(find_fabric(), "scripts/harness/harnesses.py", sub, *argv[1:])


@verb("harness")
def _harness_verb(argv):
    sub = argv[0] if argv else "status"
    return _run_script(find_fabric(), "scripts/harness/harnesses.py", sub, *argv[1:])


@verb("skill")
def _skill(argv):
    return _run_script(find_fabric(), "scripts/harness/skill.py", *argv)


@verb("okf")
def _okf(argv):
    sub = argv[0] if argv else "export"
    script = {"export": "scripts/cmd/okf_export.py", "import": "scripts/cmd/okf_import.py"}.get(sub)
    if script is None:
        print("Usage: wf okf {export|import} [options]", file=sys.stderr)
        return 1
    return _run_script(find_fabric(), script, *argv[1:])


@verb("promote")
def _promote(argv):
    if argv and argv[0] == "promote":
        argv = argv[1:]
    return _run_script(find_fabric(), "scripts/cmd/promote.py", *argv)


@verb("mine")
def _mine(argv):
    if argv and argv[0] == "chats":
        return _run_script(find_fabric(), "scripts/cmd/mine-chats.py", *argv[1:])
    if argv and argv[0] == "promotions":
        return _run_script(find_fabric(), "scripts/cmd/mine-promotions.py", *argv[1:])
    print("Usage: wf mine chats <project> [--llm] [--dry-run] | wf mine promotions [--judge] [--min-projects N]", file=sys.stderr)
    return 1


@verb("models")
def _models(argv):
    if argv and argv[0] == "ensure":
        return _run_script(find_fabric(), "scripts/cmd/ensure-local-model.py", *argv[1:])
    print("Usage: wf models ensure [--yes]", file=sys.stderr)
    return 1


@verb("repos")
def _repos(argv):
    if argv and argv[0] == "migrate":
        return _run_script(find_fabric(), "scripts/cmd/repos-migrate.py", *argv[1:])
    print("Usage: wf repos migrate [options]", file=sys.stderr)
    return 1

# === Ported orchestration verbs (cmd_status, version, integrations) ========

def _ok(msg):
    import shutil
    if sys.stdout.isatty() and shutil.which("tput"):
        pass
    print(msg)


def _warn(msg):
    print(f"\033[1;33m{msg}\033[0m" if sys.stdout.isatty() else msg)


def _info(msg):
    print(msg)


def _vault_dir(fabric_dir: Path) -> Path:
    try:
        import yaml
        cfg = yaml.safe_load((fabric_dir / "fabric.yaml").read_text()) or {}
        vp = (cfg.get("vault") or {}).get("path")
        if vp:
            p = Path(vp)
            return p if p.is_absolute() else (fabric_dir / p).resolve()
    except Exception:
        pass
    return fabric_dir.parent / "vault"


@verb("status")
def _status(argv):
    fdir = _require_fabric()
    print("")
    print("════════════════════════════════════════════")
    print("   Wiki Fabric — Status")
    print("════════════════════════════════════════════")
    print("")
    print(f"\033[0;32m✓\033[0m  Fabric: {fdir}")

    # Vault freshness
    vault = _vault_dir(fdir)
    if vault.is_dir():
        r = subprocess.run([_python(fdir), str(_harness("scripts/cmd/vault-refresh.py")),
                            str(vault), "--check", "--quiet"], capture_output=True)
        if r.returncode == 0:
            print(f"\033[0;32m✓\033[0m  Vault:  {vault} (fresh)")
        else:
            print(f"\033[1;33m⚠\033[0m  Vault:  {vault} (structure drift — run: wf vault)")
    else:
        print("\033[1;33m⚠\033[0m  Vault:  not set up (run: wf vault)")

    # CLI state (packaged tool = always current: install ≡ behavior)
    if os.environ.get("WF_PACKAGED") == "1":
        from . import __version__
        print(f"\033[0;32m✓\033[0m  CLI:    packaged (uv tool, v{__version__})")
    else:
        print("\033[0;34mℹ\033[0m  CLI:    dev mode (running from harness)")

    # LLM config
    fabric_yaml = fdir / "fabric.yaml"
    if fabric_yaml.exists():
        try:
            import yaml
            cfg = yaml.safe_load(fabric_yaml.read_text()) or {}
            llm = cfg.get("llm") or {}
            model = llm.get("model") or "not configured"
            compiler = llm.get("compiler_model") or model
            print(f"\033[0;32m✓\033[0m  LLM:    {model}")
            print(f"\033[0;32m✓\033[0m  Compiler: {compiler} (claim extraction, synthesis, promotion)")
            local_model = llm.get("local_model")
            if local_model:
                try:
                    sys.path.insert(0, str(harness_root() / "scripts" / "lib"))
                    from fabric_config import find_local_model_path
                    import shutil as _sh
                    if find_local_model_path(local_model) or os.path.isdir(os.path.expanduser(local_model)):
                        print(f"\033[0;32m✓\033[0m  Local:  {local_model} (cached)")
                    else:
                        print(f"\033[1;33m⚠\033[0m  Local:  {local_model} (not downloaded — run: wf models ensure)")
                except Exception:
                    pass
        except Exception:
            pass

    # Inventory
    croot = corpus_root(fdir)
    counts = {}
    for name, pattern in (("Claims", "evidence/claims/claim-*.md"),
                          ("Sources", "evidence/sources/src-*.md"),
                          ("Concepts", "concepts/concept-*.md"),
                          ("Patterns", "patterns/pattern-*.md"),
                          ("Entity pages", "global/entities/entity-*.md")):
        counts[name] = len(list(croot.glob(pattern)))
    projects = sum(1 for d in (croot / "projects").iterdir() if d.is_dir()) if (croot / "projects").is_dir() else 0
    print("")
    print("  Inventory:")
    print(f"    Claims:             {counts['Claims']}")
    print(f"    Sources:            {counts['Sources']}")
    print(f"    Concepts:           {counts['Concepts']}")
    print(f"    Patterns:           {counts['Patterns']}")
    print(f"    Projects connected: {projects}")
    try:
        sys.path.insert(0, str(harness_root() / "scripts" / "lib"))
        import fabric_config as fc
        discovered = len(fc.get_discovered_repos(fc.get_config()))
    except Exception:
        discovered = 0
    print(f"    Discovered:         {discovered} (overlay auto-discovery)")
    print(f"    Entity pages:       {counts['Entity pages']}")

    # Lint health
    print("")
    r = subprocess.run([_python(fdir), str(_harness("scripts/cmd/lint.py")), str(croot)],
                       capture_output=True)
    if r.returncode == 0:
        print("\033[0;32m✓\033[0m  Lint: clean")
    else:
        print("\033[1;33m⚠\033[0m  Lint: has errors")

    # Graphify
    graphs = croot / "global" / "graphs"
    if graphs.is_dir() and any(graphs.glob("*.json")):
        print("\033[0;32m✓\033[0m  Graphify: graphs imported")
    else:
        print("ℹ  Graphify: not configured (optional)")
    print("")
    return 0


@verb("integrations")
def _integrations(argv):
    fdir = _require_fabric()
    yaml_text = (fdir / "fabric.yaml").read_text()
    print("")
    print(f"Optional integrations (config: {fdir}/fabric.yaml → integrations:)")
    print("")
    def _enabled(name):
        try:
            import yaml
            cfg = yaml.safe_load(yaml_text) or {}
            return bool(((cfg.get("integrations") or {}).get(name) or {}).get("enabled"))
        except Exception:
            return False
    if _enabled("graphify", yaml_text):
        print("\033[0;32m✓\033[0m  graphify: ENABLED (call-graph staleness, claim enrichment, graph expansion)")
        print("     commands: graphify-bridge.py --all | --diff | --status")
    else:
        print("ℹ  graphify: inactive")
        print("     enable: wf update --with-graphify (or fabric.yaml integrations.graphify.enabled: true)")
        print("     effect when active: skills gain graph staleness/enrichment steps; query gains call-graph expansion")
    print("")
    if _enabled("obsidian", yaml_text):
        print("\033[0;32m✓\033[0m  obsidian: ENABLED (two-way vault: harvest-before-export, REST export via --push)")
        try:
            _run_script(fdir, "scripts/cmd/obsidian_status.py")
        except Exception:
            pass
    else:
        print("ℹ  obsidian: inactive")
        print("     enable: fabric.yaml integrations.obsidian.enabled: true (Local REST API plugin required)")
        print("     effect when active: export harvests human wiki edits as evidence before regenerating; --push writes via REST")
    print("")
    return 0


def _enabled(name: str, yaml_text: str) -> bool:
    import re
    m = re.search(rf"^\s+{name}:.*?enabled: true", yaml_text, re.MULTILINE | re.DOTALL)
    return m is not None


@verb("version")
def _version(argv):
    from . import __version__
    print(f"wf {__version__} (harness: {harness_root()})")
    state = "package" if os.environ.get("WF_PACKAGED") == "1" else "dev mode"
    print(f"installed CLI: {state}")
    return 0


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] in ("help", "--help", "-h"):
        _print_help()
        return 0
    fn = VERBS.get(argv[0])
    if fn is None:
        print(f"✗  Unknown command: {argv[0]}", file=sys.stderr)
        print("Run: wf help", file=sys.stderr)
        return 1
    return fn(argv[1:])


def _print_help():
    print("")
    print("════════════════════════════════════════════")
    print("   Wiki Fabric CLI")
    print("════════════════════════════════════════════")
    print("")
    print(f"Usage: wf <command> [options]")
    print("")
    print("Commands:")
    for v in sorted(VERBS):
        print(f"  {v}")
    print("  install [--repo URL] [--dir DIR]   Install fabric from repo URL")
    print("  update                             Pull latest + rebuild entity index")
    print("Run: wf help <command> for usage details.")
    print("")


# === Install + update (ported cmd_install / cmd_update) ====================

FABRIC_REPO = "https://github.com/hybridindie/wiki-fabric.git"


@verb("install")
def _install(argv):
    """Install = ensure the python deps exist for the *fabric* the user will
    build (uv-first). The TOOL is already installed (uv owns it); what a
    fresh fabric needs is: content skeleton + config + corpus git setup."""
    repo_url = FABRIC_REPO
    install_dir = Path.cwd() / "wiki-fabric"
    # explicit env override wins (matches find_fabric's rule 1)
    env_dir = os.environ.get("WIKI_FABRIC_DIR")
    if env_dir:
        install_dir = Path(env_dir).expanduser()
    with_graphify = False
    it = iter(argv)
    for a in it:
        if a == "--repo":
            repo_url = next(it)
        elif a == "--dir":
            install_dir = Path(next(it))
        elif a == "--with-graphify":
            with_graphify = True

    print("")
    print("═══════════════════════════════════════════")
    print("   Wiki Fabric — Install")
    print("═══════════════════════════════════════════")
    if find_fabric() is not None:
        print(f"\033[0;32m✓\033[0m  Fabric already exists — run: wf status")
        print("   To point commands at another fabric: export WIKI_FABRIC_DIR=<path>")
        return 0
    if not install_dir.exists():
        install_dir.mkdir(parents=True)
    from .skeleton import ensure_fabric_skeleton
    ensure_fabric_skeleton(install_dir, with_graphify=with_graphify)
    print("")
    print("\033[0;32m✓\033[0m  Fabric initialized")
    print("")
    print("Next steps:")
    print(f"  1. Add repos to {install_dir}/fabric.yaml")
    print("  2. wf bootstrap /path/to/my-project")
    print("  3. wf capture <slug>   # docs + PR history")
    print("  4. wf query \"...\"      # ask questions")
    print("  5. Team sharing: wf sync init <git-url>")
    return 0


@verb("update")
def _update(argv):
    # packaged mode: the tool is uv-owned
    if os.environ.get("WF_PACKAGED") == "1":
        print("")
        print("This `wf` is the packaged tool — upgrade with:")
        print("  uv tool upgrade wiki-fabric")
        print("")
        print("The corpus (content) is NOT part of the package: team content")
        print("updates via `wf sync pull` / `wf sync push` (git-native).")
        return 0
    # dev mode: the harness is a git checkout — pull it
    fdir = _require_fabric()
    harness = harness_root()
    print("")
    print(f"Updating harness at {harness}...")
    r = subprocess.run(["git", "-C", str(harness), "pull", "--rebase", "origin", "main"])
    if r.returncode != 0:
        return 1
    print("\033[0;32m✓\033[0m  Pulled latest")
    # refresh hooks + entity index + catalog (the useful parts of cmd_update)
    croot = corpus_root(fdir)
    _run_script(fdir, "scripts/cmd/build-entity-index.py", "--skip-enrich")
    _run_script(fdir, "scripts/harness/hooks.py", "reinstall", "--repos-from-config")
    _run_script(fdir, "scripts/cmd/rebuild-index.py")
    print("\033[0;32m✓\033[0m  Update complete")
    return 0


@verb("bootstrap")
def _bootstrap(argv):
    if not argv:
        print("Usage: wf bootstrap <project-path>", file=sys.stderr)
        return 1
    print("")
    return _run_script(_require_fabric(), "scripts/cmd/bootstrap-project.py", *argv)


@verb("vault")
def _vault(argv):
    # ported cmd_vault: explicit path wins; else let vault-refresh resolve
    if argv and not argv[0].startswith("-"):
        vault_path = argv[0]
        _check = "--check" in argv
        rest = [a for a in argv[1:] if a != "--check"]
        if _check:
            return _run_script(_require_fabric(), "scripts/cmd/vault-refresh.py",
                               vault_path, "--check", *rest)
        # scaffold: setup-vault.sh + refresh
        subprocess.run(["bash", str(_harness("scripts/setup-vault.sh")), vault_path],
                       capture_output=True)
        return _run_script(_require_fabric(), "scripts/cmd/vault-refresh.py", vault_path, *rest)
    fdir = _require_fabric()
    vault = _vault_dir(fdir)
    if "--check" in argv:
        return _run_script(fdir, "scripts/cmd/vault-refresh.py", "--check",
                           *[a for a in argv if a != "--check"])
    return _run_script(fdir, "scripts/cmd/vault-refresh.py", str(vault),
                       *[a for a in argv if not a.startswith("-")])
