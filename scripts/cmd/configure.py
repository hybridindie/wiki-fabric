#!/usr/bin/env python3
# configure.py — First-run fabric configuration (the python walkthrough).
#
# Replaces the bash interview (#15-adjacent / uv-first): covers the full
# fabric.yaml surface — owner, LLM model/endpoint, secrets.env scaffold,
# integrations (judgment/embeddings/obsidian/graphify), domains, vault, sync —
# cross-platform (no bash, no *nix assumptions). Deterministic defaults at
# every step; Enter accepts.
#
# Usage:
#   python3 scripts/cmd/configure.py [fabric-root] [--non-interactive] [--json]
#
# Secrets: written to <fabric>/secrets.env (KEY=VALUE, gitignored) — never
# into fabric.yaml. fabric.yaml stays shareable.

import sys
import sys as _s, pathlib as _p
_HERE = _p.Path(__file__).resolve().parent
for _dir in (_HERE, _HERE.parent / "lib", _HERE.parent):
    if str(_dir) not in _s.path:
        _s.path.insert(0, str(_dir))

import argparse
import platform
import re
from pathlib import Path

HAVE_YAML = True
try:
    import yaml
except ImportError:
    HAVE_YAML = False


def _ask(prompt, default=None):
    """One-line read; Enter accepts the default."""
    suffix = f" [{default}]" if default not in (None, "") else ": "
    if not sys.stdin.isatty():
        return default
    val = input(f"{prompt} {suffix}").strip() if default in (None, "") \
        else input(f"{prompt} [{default}]: ").strip()
    return val if val else default


def _choice(prompt, options, default_idx=1):
    """Numbered choice menu; Enter accepts default. Returns the chosen value."""
    if not sys.stdin.isatty():
        return options[default_idx - 1]
    print(prompt)
    for i, (label, _) in enumerate(options, 1):
        print(f"    {i}) {label}" + ("  [default]" if i == default_idx else ""))
    choice = input(f"  Choice [{default_idx}]: ").strip()
    idx = int(choice) if choice.isdigit() and 1 <= int(choice) <= len(options) else default_idx
    return options[idx - 1][1]


def _platform_local_model():
    # ollama-served gemma4 = the default local tier (server-local, egress-free);
    # offline/on-device HF GGUF elsewhere (get_local_model contract)
    return "gemma4:e4b-fixed" if platform.system() == "Darwin" else "unsloth/gemma-4-e4b-it-GGUF"


def _write_secrets(fabric_root, entries):
    """Merge KEY=VALUE pairs into <fabric>/secrets.env (preserve existing)."""
    p = Path(fabric_root) / "secrets.env"
    existing = {}
    if p.exists():
        for line in p.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                existing[k.strip()] = v.strip()
    existing.update(entries)
    body = "# Machine-local secrets (gitignored) — real env vars win over this file\n"
    body += "".join(f"{k}={v}\n" for k, v in sorted(existing.items()))
    p.write_text(body, encoding="utf-8")
    return p


def run(fabric_root: Path, args):
    """Interactive walkthrough; returns the fabric.yaml dict."""
    cfg_path = fabric_root / "fabric.yaml"
    cfg = {}
    if cfg_path.exists() and HAVE_YAML:
        import yaml as _yaml
        cfg = _yaml.safe_load(cfg_path.read_text(encoding="utf-8")) or {}

    git_name = ""
    try:
        git_name = __import__("subprocess").run(
            ["git", "config", "--global", "user.name"],
            capture_output=True, text=True).stdout.strip()
    except Exception:
        pass  # git identity absent → interactive prompt supplies owner

    print()
    print("════════════════════════════════════════════")
    print("   Wiki Fabric — First-Run Setup")
    print("════════════════════════════════════════════")
    print()
    print("  Configures fabric.yaml (shareable) + secrets.env (machine-local).")
    print("  Press Enter to accept [defaults] at each step.\n")

    secrets_to_write = {}

    # 1. Owner
    owner = _ask("Your name/handle (identity; also in secrets if you like)",
                 cfg.get("owner") or git_name or "you")
    cfg["owner"] = owner

    # 2. LLM endpoint + key
    ep = _choice("  LLM endpoint — any OpenAI-compatible API works:", [
        ("Ollama (local)  localhost:11434 — default", "http://localhost:11434/v1"),
        ("LM Studio       localhost:1234/v1", "http://localhost:1234/v1"),
        ("vLLM            localhost:8000/v1", "http://localhost:8000/v1"),
        ("OpenRouter      openrouter.ai/api/v1 (needs key)", "https://openrouter.ai/api/v1"),
        ("Together AI     api.together.xyz/v1 (needs key)", "https://api.together.ai/v1"),
        ("Custom endpoint", None),
    ])
    base_url = ep or cfg.get("llm", {}).get("base_url") or "http://localhost:11434/v1"
    if base_url is None:
        base_url = _ask("  Base URL",
                        cfg.get("llm", {}).get("base_url", "http://localhost:11434/v1"))
    needs_key = "localhost" not in base_url
    llm_key = None
    if needs_key:
        llm_key = _ask("  API key for this provider", "").strip() or None
    model = _ask("  Ops model (queries/capture; cheap)",
                 cfg.get("llm", {}).get("model", "qwen2.5-coder:7b"))
    compiler = _ask("  Compiler model (claim extraction, synthesis)",
                    cfg.get("llm", {}).get("compiler_model", "deepseek-v4.1-flash:cloud"))
    from fabric_config import DEFAULT_LOCAL_MODELS
    local_default = DEFAULT_LOCAL_MODELS.get(sys.platform,
                                             DEFAULT_LOCAL_MODELS["default"])
    local_model = _ask("  Local model (local-tier routing; ollama tag or HF id)",
                       cfg.get("llm", {}).get("local_model") or local_default)
    if llm_key:
        secrets_to_write["WIKI_LLM_API_KEY"] = llm_key
        llm_key_ref = "WIKI_LLM_API_KEY (secrets.env)"
    elif "localhost" in base_url:
        llm_key_ref = "ollama (local — no key needed)"
    else:
        llm_key_ref = _ask("  Env var name holding the key", "WIKI_LLM_API_KEY")
    cfg["llm"] = {"base_url": base_url, "api_key": llm_key_ref or "ollama",
                  "model": model, "compiler_model": compiler,
                  "local_model": local_model}

    # 3. Judgment tier
    judge_on = _choice("\n  Judgment tier — calibrated judging"
                       "\n  for mining + eval gates + ingest verification:", [
        ("off — deterministic only (default; add later)", False),
        ("on — ollama decision models local (tev1/nimble, no key, no egress)", "ollama"),
        ("on — Jev cloud (~$0.0004/call, key needed)", "cloud"),
        ("on — Laya local (Apple Silicon, on-device)", "local-laya-mlx"),
        ("on — Laya local cross-platform (pip laya, CPU)", "laya-torch"),
        ("on — generic local (llm.local_model JSON verdicts)", "generic"),
    ], 1)
    cfg.setdefault("integrations", {})
    if judge_on is True or judge_on is False or judge_on == "off":
        cfg["integrations"]["judgment"] = {"enabled": False, "route": "cloud",
                                           "cloud_model": "jev-latest",
                                           "local_backend": "laya"}
    else:
        route = "cloud" if judge_on == "cloud" else "local"
        backend = {"laya-mlx": "laya", "laya-torch": "laya",
                   "ollama": "ollama"}.get(judge_on, "generic") \
            if judge_on not in ("laya-mlx", "laya-torch", "ollama") else \
            {"laya-mlx": "laya", "laya-torch": "laya", "ollama": "ollama"}[judge_on]
        entry = {"enabled": True, "route": route}
        if route == "cloud":
            key = _ask("  TypeSafe API key (stored in secrets.env)", "").strip()
            if key:
                secrets_to_write["TYPESAFE_API_KEY"] = key
            else:
                key = _ask("  Env var name for the Jev key", "TYPESAFE_API_KEY")
            cfg["integrations"]["judgment"] = {
                "enabled": True, "route": "cloud",
                "cloud_model": _ask("  Jev model", "jev-latest")}
        elif backend == "ollama":
            model = _ask("  Ollama decision model (pull with ollama pull <tag>)",
                         "tev1:latest").strip() or "tev1:latest"
            cfg["integrations"]["judgment"] = {
                "enabled": True, "route": "local", "local_backend": "ollama",
                "local_model": model}
        else:
            cfg["integrations"]["judgment"] = {
                "enabled": True, "route": "local", "local_backend": backend}
        if key:
            pass
    # key env note for cloud
    if cfg["integrations"].get("judgment", {}).get("route") == "cloud" \
            and "TYPESAFE_API_KEY" in secrets_to_write:
        cfg["integrations"]["judgment"].pop("api_key", None)  # never a literal

    # 4. Embeddings
    emb_on = _choice("\n  Semantic re-rank boost (fastembed, offline, ~5ms/query;", [
        ("off — default (shipped; thin gain at small corpus)", False),
        ("on — fusion re-rank on wf query (top-40)", True),
    ], 1)
    cfg["integrations"]["embeddings"] = {
        "enabled": bool(emb_on), "model": "all-MiniLM-L6-v2"}

    # 5. Graphify
    graphify = _choice("\n  Graphify (code graphs + navigation; needs a graph dir per repo):", [
        ("off", False),
        ("on", True),
    ], 1)
    cfg["integrations"]["graphify"] = {
        "enabled": bool(graphify), "graph_dir": "graphify-out"}

    # 6. Obsidian
    obs_on = _choice("\n  Obsidian two-way vault (REST push/harvest; needs the Local REST plugin):", [
        ("off", None),
        ("on — configure now", {
            "api_url": "https://127.0.0.1:27124",
            "api_key_env": "OBSIDIAN_REST_KEY"}),
    ], 1)
    if obs_on:
        url = _ask("  Obsidian Local REST url", "https://127.0.0.1:27124")
        cfg["integrations"]["obsidian"] = {
            "enabled": True, "api_url": url, "api_key_env": "OBSIDIAN_REST_KEY"}
        key = _ask("  REST key (stored in secrets.env as OBSIDIAN_REST_KEY)", "").strip()
        if key:
            secrets_to_write["OBSIDIAN_REST_KEY"] = key

    # 7. Vault
    vault = _ask("\n  Vault path (content root; default: sibling of fabric dir)",
                 str(fabric_root.parent / "vault"))
    if vault and vault != str(fabric_root.parent / "vault"):
        cfg["vault"] = {"path": vault}

    # 8. Team sync
    sync_on = _choice("\n  Team sync (one corpus remote; PR-gated in team mode):", [
        ("solo — single machine [default]", "solo"),
        ("team with existing remote", "team"),
        ("team + let me scaffold the corpus repo now (needs gh cli)", "setup"),
    ], 1)
    if sync_on in ("team", "setup"):
        cfg["sync"] = {"mode": "team", "evidence_prs": "auto"}
        remote = _ask("  Corpus remote (git URL)", "").strip()
        if remote:
            cfg["sync"]["corpus_url"] = remote

    # 9. Domains: default none — self-building
    keep = _choice("\n  Domain signals (self-building vocabulary; a new fabric starts with the defaults):", [
        ("keep default domain signals", True),
        ("let me add/edit signals now (YAML lines)", False),
    ], 1)
    if keep is False and sys.stdin.isatty():
        print("  Enter one 'name: signal,signal' per line; blank line to finish:")
        signals = {}
        while True:
            line = input("    ").strip()
            if not line:
                break
            name, _, vals = line.partition(":")
            signals[name.strip()] = [v.strip() for v in vals.split(",") if v.strip()]
        if signals:
            cfg["domains"] = signals

    # 10. secrets.env write
    if secrets_to_write:
        p = _write_secrets(fabric_root, secrets_to_write)
        print(f"\n  secrets written: {p}")

    return cfg, secrets_to_write


def main():
    ap = argparse.ArgumentParser(description="First-run fabric configuration walkthrough")
    ap.add_argument("fabric_root", nargs="?", default=None)
    ap.add_argument("--non-interactive", action="store_true",
                    help="print the current config as the walkthrough would resolve it")
    ap.add_argument("--dry-run", action="store_true", help="show, don't write")
    args = ap.parse_args()

    if args.fabric_root:
        fabric_root = Path(args.fabric_root)
    else:
        # default: the fabric dir (where fabric.yaml lives / would live)
        from fabric_config import _find_config_file
        found = _find_config_file()
        fabric_root = (Path(found).parent if found
                       else Path.home() / ".local" / "share" / "wiki-fabric")
    if not HAVE_YAML:
        print("pyyaml required", file=sys.stderr)
        return 2
    import yaml as _yaml
    existing = {}
    p = fabric_root / "fabric.yaml"
    if p.exists():
        existing = _yaml.safe_load(p.read_text(encoding="utf-8")) or {}

    if args.dry_run or not sys.stdin.isatty():
        import json
        print("Non-interactive: resolving from existing fabric.yaml + defaults.")
        print(json.dumps(existing, indent=1)[:1200])
        return 0

    import json
    from fabric_config import save_config
    cfg, _secrets = run(fabric_root, args)
    save_config(cfg, path=fabric_root / "fabric.yaml")
    print(f"\nConfigured: {fabric_root / 'fabric.yaml'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())