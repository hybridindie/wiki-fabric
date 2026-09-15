"""Shared configuration for wiki-fabric scripts.

Reads fabric.yaml from the fabric root (or ~/.wiki-fabric/fabric.yaml fallback).
All scripts import `get_config()` instead of hardcoding repo paths, owner names,
or LLM settings.

fabric.yaml schema:
    owner: <your name>
    llm:
      base_url: http://localhost:11434/v1
      api_key: ollama
      model: qwen2.5-coder:7b
    repos:
      my-project:
        path: ../my-project          # relative to fabric root, or absolute
        graph_dir: graphify-out       # optional, for graphify integration
    domains:
      agent-systems:
        signals: [agent, mcp, fastmcp, opencode, claude]
      web-systems:
        signals: [fastapi, flask, react, nextjs, supabase, postgresql]
"""

import os
from pathlib import Path

try:
    import yaml
    HAVE_YAML = True
except ImportError:
    HAVE_YAML = False

FABRIC_ROOT = Path(__file__).parent.parent
CONFIG_FILENAME = "fabric.yaml"

# Defaults when no fabric.yaml exists
_DEFAULTS = {
    "owner": "you",
    "llm": {
        "base_url": "http://localhost:11434/v1",
        "api_key": "ollama",
        # ops model: cheap queries, capture, status
        "model": "qwen2.5-coder:7b",
        # compiler model: claim extraction, synthesis, promotion mining.
        # Policy (eval-stability G4): compiler runs need the most capable model —
        # cross-model extraction disagreement is capability-correlated.
        "compiler_model": "deepseek-v4.1-flash:cloud",
    },
    "repos": {},
    "integrations": {
        # Optional integrations; each is off until explicitly enabled here.
        # When active, skills/scripts gain graph-aware steps (see system/skills).
        "graphify": {"enabled": False, "graph_dir": "graphify-out"},
        "embeddings": {"enabled": False, "model": "all-MiniLM-L6-v2"},
    },
    "domains": {
        "agent-systems": {"signals": ["agent", "mcp", "fastmcp", "opencode", "claude"]},
        "godot-systems": {"signals": ["godot", "gdscript", "voxel"]},
        "web-systems": {"signals": ["fastapi", "flask", "react", "nextjs", "supabase", "postgresql"]},
    },
}


def get_integrations(config):
    """Merged integrations dict with defaults (enabled: False)."""
    merged = {}
    for name, cfg in _DEFAULTS.get("integrations", {}).items():
        merged[name] = dict(cfg)
        user_cfg = (config.get("integrations") or {}).get(name) or {}
        merged[name].update(user_cfg if isinstance(user_cfg, dict) else {})
    for name, cfg in (config.get("integrations") or {}).items():
        if name not in merged:
            merged[name] = cfg if isinstance(cfg, dict) else {"enabled": bool(cfg)}
    return merged


def is_integration_active(config, name):
    """True when an optional integration is explicitly enabled in fabric.yaml."""
    integ = get_integrations(config)
    return bool((integ.get(name) or {}).get("enabled", False))


def _find_config_file():
    """Find fabric.yaml in fabric root or home directory."""
    candidates = [
        FABRIC_ROOT / CONFIG_FILENAME,
        Path.home() / ".wiki-fabric" / CONFIG_FILENAME,
        Path.home() / CONFIG_FILENAME,
    ]
    for c in candidates:
        if c.exists():
            return c
    return None


def get_config():
    """Load fabric.yaml, merged with defaults. Returns dict."""
    config_file = _find_config_file()

    config = dict(_DEFAULTS)
    config["llm"] = dict(_DEFAULTS["llm"])
    config["repos"] = dict(_DEFAULTS.get("repos", {}))
    config["domains"] = dict(_DEFAULTS.get("domains", {}))

    if config_file and HAVE_YAML:
        try:
            user_config = yaml.safe_load(config_file.read_text()) or {}
            # Merge top-level keys
            for key in ("owner", "llm", "repos", "domains"):
                if key in user_config and user_config[key] is not None:
                    if isinstance(config.get(key), dict) and isinstance(user_config[key], dict):
                        config[key].update(user_config[key])
                    else:
                        config[key] = user_config[key]
        except Exception:
            pass

    # Env var overrides for LLM
    config["llm"]["base_url"] = os.environ.get("WIKI_LLM_BASE_URL", config["llm"]["base_url"])
    config["llm"]["api_key"] = os.environ.get("WIKI_LLM_API_KEY", config["llm"]["api_key"])
    config["llm"]["model"] = os.environ.get("WIKI_LLM_MODEL", config["llm"]["model"])
    config["llm"]["compiler_model"] = os.environ.get(
        "WIKI_LLM_COMPILER_MODEL", config["llm"].get("compiler_model") or config["llm"]["model"])

    return config


def resolve_repo_path(config, repo_name):
    """Resolve a repo path from fabric.yaml config (relative to fabric root or absolute)."""
    repo_cfg = config.get("repos", {}).get(repo_name, {})
    path_str = repo_cfg.get("path", "")
    if not path_str:
        return None
    p = Path(path_str)
    if p.is_absolute():
        return p
    return (FABRIC_ROOT / p).resolve()


def get_all_repo_names(config):
    """Return list of configured repo names."""
    return list(config.get("repos", {}).keys())


def get_domain_signals(config):
    """Return {domain_name: [signal, ...]} from config."""
    result = {}
    for domain, cfg in config.get("domains", {}).items():
        if isinstance(cfg, dict):
            result[domain] = cfg.get("signals", [])
        elif isinstance(cfg, list):
            result[domain] = cfg
    return result


def get_owner(config):
    """Return the configured owner name."""
    return config.get("owner", "you")


def get_llm_config(config, compiler=False):
    """Return LLM configuration dict. compiler=True returns the compiler model
    (falls back to llm.model when unset) — claim extraction, synthesis, and
    promotion mining must run on the policy-designated compiler model."""
    llm = dict(config.get("llm", {}))
    if compiler:
        cm = llm.get("compiler_model")
        if cm and cm.strip():
            llm["model"] = cm
    return llm


def compiler_eval_recorded(config, log_path=None):
    """True when registry/log.md contains a PASS compiler eval for the current
    compiler model (eval-stability G4 / eval.py). Promotion mining + promotion
    refuse without it — the model-sensitivity finding made model swaps compiler
    changes; this enforces the regression-guard rule."""
    import re
    llm = get_llm_config(config, compiler=True)
    compiler_model = llm.get("model", "")
    log_path = Path(log_path or (FABRIC_ROOT / "registry" / "log.md"))
    if not log_path.exists():
        return False, "no registry/log.md — run eval-stability/eval.py for the compiler model first"
    text = log_path.read_text()
    # accept: any eval-stability/eval entry naming the compiler model
    short = compiler_model.split(":")[0]
    block_re = re.compile(r"## \[[\d-]+\] (eval-stability|eval) \|.*?(?=\n## |\Z)", re.DOTALL)
    for m in block_re.finditer(text):
        block = m.group(0)
        if compiler_model in block or short in block:
            return True, f"compiler eval recorded for {compiler_model}"
    return False, (f"no compiler eval recorded for '{compiler_model}' — run: "
                   f"python3 scripts/eval-stability.py --models {compiler_model} --record")


def get_repo_graph_dir(config, repo_name):
    """Get the graphify graph directory for a repo."""
    repo_cfg = config.get("repos", {}).get(repo_name, {})
    return repo_cfg.get("graph_dir", "graphify-out")