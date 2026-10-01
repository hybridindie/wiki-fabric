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

try:
    import sys as _sys
    _sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / 'scripts' / 'lib'))
except Exception:
    pass

import layout

# --- script/asset resolution (dev tree or packaged _harness) --------------

# Subprocess timeout tiers — mirror wf_common.TIMEOUT_* (packaged dispatch
# must not import wf_common for constants; the values are pinned by the
# dispatch-agreement tests).
TIMEOUT_SCRIPT = 600

_PACKAGED = Path(__file__).resolve().parent / "_harness"


def harness_root() -> Path:
    """The shipped tool tree (scripts/, system/, templates/...).
    Packaged _harness first, then this file's own position (dev checkout),
    then the standard install home ($HOME/wiki-fabric — when the dispatch
    itself is imported from elsewhere, e.g. the MCP server in another venv)."""
    if (_PACKAGED / "scripts").exists():
        return _PACKAGED
    here_parent = Path(__file__).resolve().parent.parent.parent
    if (here_parent / "scripts" / "wiki-fabric.sh").exists():
        return here_parent
    home_harness = Path.home() / ".wiki-fabric"
    if (home_harness / "scripts" / "wiki-fabric.sh").exists():
        return home_harness
    return here_parent


def _paths_mod():
    """Import the shipped paths.py resolution layer (dev tree or packaged
    _harness). Bare `from paths import ...` only works when the harness lib
    is already on sys.path (tests do this) — packaged wf must self-locate."""
    lib = harness_root() / "scripts" / "lib"
    if str(lib) not in sys.path:
        sys.path.insert(0, str(lib))
    import paths
    return paths


def find_fabric() -> Path | None:
    """Fabric root (content + config). Chain (paths.py #152, single truth):
      1. $WIKI_FABRIC_DIR  2. cwd walk (harness trees skipped)  3. dev
      sibling vault  4. XDG default. Returns None when no fabric exists
      (commands needing content fail cleanly)."""
    p = _paths_mod()
    found = p.env_fabric_root() or p.walk_for_fabric(Path.cwd())
    if found:
        return found
    # dev sibling vault (anchored at THIS dispatcher's harness root — tests
    # and packaged mode monkeypatch harness_root())
    found = p.sibling_vault_of(harness_root())
    if found:
        return found.resolve()
    return p.xdg_fabric_root()


def corpus_root(fabric_dir: Path) -> Path:
    """CORPUS_ROOT resolution (delegates to paths.py, #152)."""
    return _paths_mod().find_corpus_root(fabric_dir)


def _python(fabric_dir: Path | None) -> str:
    """Interpreter preference: a venv next to the fabric, else sys.executable
    (this tool's own interpreter — it carries the deps)."""
    if fabric_dir:
        venv = fabric_dir / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
        if venv.exists():
            return str(venv)
    return sys.executable


def _run_script(fabric_dir: Path | None, rel: str, *args: str, timeout: int = TIMEOUT_SCRIPT) -> int:
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
@verb("freshness")
def _freshness(argv): return _simple_script("scripts/cmd/freshness-job.py", argv)
@verb("eval")
def _eval(argv):
    """Golden-corpus/behavior/stability/real-repo/PR-replay evaluations.
    Usage: wf eval {behavior|stability|golden|real|pr} [flags...]"""
    sub = argv[0] if argv else "behavior"
    scripts = {"behavior": "scripts/eval/eval-behavior.py",
               "stability": "scripts/eval/eval-stability.py",
               "golden": "scripts/eval/eval.py",
               "real": "scripts/eval/eval-real-repo.py",
               "pr": "scripts/eval/eval-pr-replay.py"}
    script = scripts.get(sub)
    if script is None:
        raise SystemExit("wf eval {behavior|stability|golden|real|pr}")
    return _simple_script(script, argv[1:])


@verb("graphify")
def _graphify(argv):
    """The graphify integration cycle. Usage: wf graphify {all|import|enrich|diff|status}
    The sub-verb maps to the bridge's flag form (its argparse is flag-based
    — no positional subcommand)."""
    fdir = find_fabric()
    script = "scripts/harness/graphify-bridge.py"
    sub = argv[0] if argv else "status"
    if sub.startswith("-"):              # passthrough: flags already given
        return _run_script(fdir, script, *argv)
    if sub not in ("all", "import", "enrich", "diff", "status"):
        raise SystemExit("wf graphify {all|import|enrich|diff|status}")
    return _run_script(fdir, script, f"--{sub}", *argv[1:])
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


@verb("configure")
def _configure(argv):
    return _run_script(find_fabric(), "scripts/cmd/configure.py", *argv)


@verb("apply-changeset")
def _apply_changeset(argv):
    return _run_script(find_fabric(), "scripts/cmd/apply_changeset.py", *argv)


@verb("utility")
def _utility(argv):
    return _run_script(find_fabric(), "scripts/cmd/utility.py", *argv)


@verb("publish")
def _publish(argv):
    return _run_script(find_fabric(), "scripts/cmd/publish-wiki.py", *argv)


@verb("verify-effects")
def _verify_effects(argv):
    return _run_script(find_fabric(), "scripts/cmd/verify-effects.py", *argv)


@verb("wiki-generate")
def _wiki_generate(argv):
    return _run_script(find_fabric(), "scripts/cmd/wiki_generate.py", *argv)


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
    """Vault for the status report — paths.py is the single resolver home
    (#152). Honors WIKI_FABRIC_VAULT (dispatch's copy silently ignored it)
    then fabric.yaml vault.path, then "the vault IS the fabric"."""
    return _paths_mod().find_vault_dir_for_fabric(fabric_dir)


@verb("status")
def _status(argv):
    fdir = _require_fabric()
    print("")
    print("════════════════════════════════════════════")
    print("   Wiki Fabric — Status")
    print("════════════════════════════════════════════")
    print("")
    print(f"\033[0;32m✓\033[0m  Fabric: {fdir}")

    # Vault freshness — audit the layout-aware default the resolver names
    # (single truth; vault-refresh delegates to the same fabric_config rule —
    # status, refresh, and the standalone checker agree on the tree).
    vault = _vault_dir(fdir)
    refresh_target = vault
    if refresh_target.is_dir():
        r = subprocess.run([_python(fdir), str(_harness("scripts/cmd/vault-refresh.py")),
                            str(refresh_target), "--check", "--quiet"], capture_output=True)
        if r.returncode == 0 and (refresh_target / "index.md").exists():
            print(f"\033[0;32m✓\033[0m  Vault:  {refresh_target} (fresh)")
        else:
            print(f"\033[1;33m⚠\033[0m  Vault:  {refresh_target} (structure drift — run: wf vault)")
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
                    from fabric_config import find_local_model_path, _is_ollama_tag
                    import shutil as _sh
                    if _is_ollama_tag(local_model):
                        # ollama-served tag: local tier comes from the server
                        print(f"\033[0;32m✓\033[0m  Local:  {local_model} (ollama-served)")
                    elif find_local_model_path(local_model) or os.path.isdir(os.path.expanduser(local_model)):
                        print(f"\033[0;32m✓\033[0m  Local:  {local_model} (cached)")
                    else:
                        print(f"\033[1;33m⚠\033[0m  Local:  {local_model} (not downloaded — run: wf models ensure)")
                except Exception:
                    pass  # local-model check is cosmetic — status must not break on it
        except Exception as _e:
            # status degrades to "not configured" rather than crashing (audit)
            print(f"\033[1;33m⚠\033[0m  LLM:    config unreadable ({_e})")


    # Inventory
    croot = corpus_root(fdir)
    counts = {}
    for name, pattern in (("Claims", "evidence/claims/claim-*.md"),
                          ("Sources", "evidence/sources/src-*.md"),
                          ("Concepts", "concepts/concept-*.md"),
                          ("Patterns", "patterns/pattern-*.md"),
                          ("Entity pages", "global/entities/entity-*.md")):
        counts[name] = len(list(croot.glob(pattern)))
    projects = sum(1 for d in (layout.projects(croot)).iterdir() if d.is_dir()) if (layout.projects(croot)).is_dir() else 0
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

    # Gate (HITL) — loud: a status that hides pending decisions isn't status
    try:
        sys.path.insert(0, str(harness_root() / "scripts" / "cmd"))
        import gate as _gate_mod
        sections, actionable = _gate_mod.gate()
    except Exception:
        sections, actionable = {}, False
    if actionable:
        parts = [f"{k}: {len(v[1]) if isinstance(v, tuple) else v}"
                 for k, v in sections.items()
                 if isinstance(v, tuple) and v[1] or (not isinstance(v, tuple) and v)]
        print(f"\033[1;33m⚠\033[0m  Gate:   pending — {', '.join(parts) or 'items'} → wf gate")
    else:
        print("\033[0;32m✓\033[0m  Gate:   clear")

    # Graphify
    graphs = layout.global_graphs(croot)
    if graphs.is_dir() and any(graphs.glob("*.json")):
        print("\033[0;32m✓\033[0m  Graphify: graphs imported")
    else:
        print("ℹ  Graphify: not configured (optional)")
    print("")
    return 0


@verb("integrations")
def _integrations(argv):
    """Integration report — single truth is fabric_config.is_integration_active
    (#155-A: an inner yaml-parse copy was shadowed and a module-level regex
    grep re-implemented the same check, disagreeing with the config layer)."""
    fdir = _require_fabric()
    try:
        sys.path.insert(0, str(harness_root() / "scripts" / "lib"))
        from fabric_config import get_config, is_integration_active
        cfg = get_config()
        enabled = lambda name: is_integration_active(cfg, name)  # noqa: E731
    except Exception:
        try:
            import yaml
            cfg = yaml.safe_load((fdir / "fabric.yaml").read_text()) or {}
        except Exception:
            cfg = {}
        enabled = lambda name: bool(  # noqa: E731
            ((cfg.get("integrations") or {}).get(name) or {}).get("enabled"))
    print("")
    print(f"Optional integrations (config: {fdir}/fabric.yaml → integrations:)")
    print("")
    if enabled("graphify"):
        print("\033[0;32m✓\033[0m  graphify: ENABLED (call-graph staleness, claim enrichment, graph expansion)")
        print("     commands: graphify-bridge.py --all | --diff | --status")
    else:
        print("ℹ  graphify: inactive")
        print("     enable: wf update --with-graphify (or fabric.yaml integrations.graphify.enabled: true)")
        print("     effect when active: skills gain graph staleness/enrichment steps; query gains call-graph expansion")
    print("")
    if enabled("obsidian"):
        print("\033[0;32m✓\033[0m  obsidian: ENABLED (two-way vault: harvest-before-export, REST export via --push)")
        try:
            _run_script(fdir, "scripts/cmd/obsidian_status.py")
        except Exception:
            pass  # obsidian status detail is cosmetic — the ENABLED line already printed
    else:
        print("ℹ  obsidian: inactive")
        print("     enable: fabric.yaml integrations.obsidian.enabled: true (Local REST API plugin required)")
        print("     effect when active: export harvests human wiki edits as evidence before regenerating; --push writes via REST")
    print("")
    return 0


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
    install_dir = Path.home() / ".wiki-fabric"
    # explicit env override wins (matches find_fabric's rule 1)
    env_dir = os.environ.get("WIKI_FABRIC_DIR")
    if env_dir:
        install_dir = Path(env_dir).expanduser()
    with_graphify = False
    corpus_url = None
    vault_path = None
    it = iter(argv)
    for a in it:
        if a == "--repo":
            repo_url = next(it)
        elif a == "--dir":
            install_dir = Path(next(it))
        elif a == "--with-graphify":
            with_graphify = True
        elif a == "--corpus":
            corpus_url = next(it)
        elif a == "--vault":
            vault_path = next(it)

    print("")
    print("═══════════════════════════════════════════")
    print("   Wiki Fabric — Install")
    print("═══════════════════════════════════════════")
    # Contract: an EXPLICIT --dir never short-circuits — that's the user
    # saying "create the fabric HERE" (the CI seed flow hit this:
    # find_fabric resolved an ambient fabric and the --dir target silently
    # got nothing). Only the AMBIENT resolution short-circuits.
    explicit_dir = "--dir" in (argv or [])
    if not explicit_dir and find_fabric() is not None:
        print(f"\033[0;32m✓\033[0m  Fabric already exists — run: wf status")
        print("   To point commands at another fabric: export WIKI_FABRIC_DIR=<path>")
        return 0
    if not install_dir.exists():
        install_dir.mkdir(parents=True)
    from .skeleton import ensure_fabric_skeleton
    ensure_fabric_skeleton(install_dir, with_graphify=with_graphify)
    # parity with the bash install: the fabric IS a git repo from the first
    # command — sync init needs commits to publish the initial corpus, and
    # local history lets you diff/revert knowledge.
    if not (install_dir / ".git").exists():
        # outer git = machine-local shell ONLY (fabric.yaml history). Content
        # lives in the standalone corpus/ repo (sync init/migrate/teammate
        # clone) — corpus/ is ignored here from day one.
        gi = install_dir / ".gitignore"
        if "corpus/" not in (gi.read_text() if gi.exists() else ""):
            with open(gi, "a") as f:
                f.write("corpus/\n")
        subprocess.run(["git", "init", "-q"], cwd=install_dir,
                       capture_output=True)
        subprocess.run(["git", "add", "-A"], cwd=install_dir, capture_output=True)
        # identity: the ambient fabric's owner (the corpus sync name) —
        # NEVER a bare _owner reference (undefined-var bug, wheel-smoke catch)
        try:
            from fabric_config import get_owner  # via skeleton-primed path
        except Exception:
            get_owner = None
        _owner = None
        try:
            sys.path.insert(0, str(Path(__file__).resolve().parent
                                   / "_harness" / "scripts" / "lib"))
            from fabric_config import get_config, get_owner
            _owner = get_owner(get_config())
        except Exception:
            _owner = None
        if subprocess.run(["git", "-c", f"user.name={_owner or 'wf'}",
                           "-c", f"user.email={_owner or 'wf'}@fabric.local",
                           "commit", "-q", "-m", "chore: initialize fabric"],
                          cwd=install_dir, capture_output=True).returncode == 0:
            print("\033[0;32m✓\033[0m  Fabric initialized as a git repo (corpus sync ready)")
    if vault_path:
        vault_line = (Path(install_dir) / "fabric.yaml")
        txt = vault_line.read_text()
        vault_line.write_text(txt.rstrip("\n") + f"\n\nvault:\n  path: {vault_path}\n")
        print(f"\033[0;32m✓\033[0m  Vault location pinned: {vault_path}")
    if corpus_url:
        print("")
        env = {**os.environ, "WIKI_FABRIC_DIR": str(install_dir)}
        # teammate probe FIRST (parity with the bash two-way gate): a corpus
        # branch on the remote + no local knowledge content ⇒ join (fetch +
        # checkout) — never push an empty corpus over the team's source of truth.
        probe = subprocess.run(["git", "ls-remote", corpus_url,
                                "refs/heads/main"], env=env,
                               capture_output=True, text=True)
        remote_corpus = probe.stdout.strip()
        # parity with the bash gate: scaffold/markup files (AGENTS/README/
        # index; the ontology seed) are NOT knowledge content — a fresh
        # skeleton must JOIN the team, not publish over the source of truth
        _scaffold = {"AGENTS.md", "README.md", "index.md", "ontology.md"}
        corpus_dir = install_dir / "corpus"
        local_content = corpus_dir.is_dir() and any(
            p.is_file() and p.name not in _scaffold
            for p in corpus_dir.rglob("*.md"))
        if remote_corpus and not local_content:
            # the corpus IS a standalone repo: clone it in place — content at
            # corpus/ root, origin wired, ready for push/pull (no checkout gymnastics)
            import shutil as _shutil
            tmp_clone = install_dir.parent / (install_dir.name + "-corpus-join")
            if tmp_clone.exists():
                _shutil.rmtree(tmp_clone)
            clone = subprocess.run(["git", "clone", "--depth", "50", corpus_url,
                                    str(tmp_clone)], env=env, capture_output=True, text=True)
            # rename origin → corpus (the name every later sync op resolves)
            if clone.returncode == 0:
                subprocess.run(["git", "-C", str(tmp_clone), "remote", "rename",
                                "origin", "corpus"], capture_output=True)
            if clone.returncode == 0:
                # replace the scaffolded corpus with the team's
                corpus_dir = install_dir / "corpus"
                if corpus_dir.exists():
                    _shutil.rmtree(corpus_dir)
                _shutil.move(str(tmp_clone), str(corpus_dir))
                print("\033[0;32m✓\033[0m  Team corpus cloned — the fabric carries the team's knowledge")
                print("")
                return _install_print_next(install_dir)
            print("couldn't clone the corpus remote (access?) — fabric starts "
                  "empty (wf sync pull later)", file=sys.stderr)
            print("")
            return _install_print_next(install_dir)
        r = subprocess.run([sys.executable, str(_harness("scripts/cmd/sync.py")),
                            "init", corpus_url], env=env)
        if r.returncode != 0:
            print("corpus init failed — fabric usable without the remote; "
                  "run: wf sync init <url> later", file=sys.stderr)
    print("")
    print("\033[0;32m✓\033[0m  Fabric initialized")
    print("")
    return _install_print_next(install_dir)


def _install_print_next(install_dir):
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
        # scaffold the vault output dir (python — cross-platform)
        vp = Path(vault_path)
        vp.mkdir(parents=True, exist_ok=True)
        (vp / ".obsidian").mkdir(parents=True, exist_ok=True)
        print(f"Vault ready: {vp}")
        print("Generate its content with: wf export wiki")
        return _run_script(_require_fabric(), "scripts/cmd/vault-refresh.py", vault_path, *rest)
    fdir = _require_fabric()
    vault = _vault_dir(fdir)
    if "--check" in argv:
        return _run_script(fdir, "scripts/cmd/vault-refresh.py", "--check",
                           *[a for a in argv if a != "--check"])
    return _run_script(fdir, "scripts/cmd/vault-refresh.py", str(vault),
                       *[a for a in argv if not a.startswith("-")])
