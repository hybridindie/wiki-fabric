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
        "model": "qwen2.5-coder:7b",
    },
    "repos": {},
    "domains": {
        "agent-systems": {"signals": ["agent", "mcp", "fastmcp", "opencode", "claude"]},
        "godot-systems": {"signals": ["godot", "gdscript", "voxel"]},
        "web-systems": {"signals": ["fastapi", "flask", "react", "nextjs", "supabase", "postgresql"]},
    },
}


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
                if key in user_config:
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


def get_llm_config(config):
    """Return LLM configuration dict."""
    return config.get("llm", {})


def get_repo_graph_dir(config, repo_name):
    """Get the graphify graph directory for a repo."""
    repo_cfg = config.get("repos", {}).get(repo_name, {})
    return repo_cfg.get("graph_dir", "graphify-out")