"""Fresh-fabric content skeleton (the ensure_directories port)."""
from __future__ import annotations

import shutil
from pathlib import Path

FABRIC_REPO = "https://github.com/hybridindie/wiki-fabric.git"

DIRECTORIES = [
    "corpus/evidence/raw",
    "corpus/evidence/claims",
    "corpus/evidence/sources",
    "corpus/evidence/source-summaries",
    "corpus/evidence/experiments",
    "corpus/evidence/traces/change-sets",
    "corpus/evidence/_inbox",
    "corpus/registry/promotions",
    "corpus/registry/domain-proposals",
    "corpus/registry/conflicts",
    "corpus/patterns",
    "corpus/anti-patterns",
    "corpus/skills",
    "corpus/concepts",
    "corpus/domains",
    "corpus/projects",
    "corpus/syntheses",
    "corpus/global/entities",
    "corpus/global/graphs",
]

# The ONE config template (#153) — canonical shape lives in
# fabric_config.DEFAULT_TEMPLATE; this alias keeps the shipped skeleton
# dependency-light (renders via the harness lib when importable).
def _canonical_template(owner="you", with_graphify=False, extra=""):
    try:
        import sys as _sys, pathlib as _pl
        _lib = pathlib.Path(__file__).resolve().parent / "_harness" / "scripts" / "lib"
        if not _lib.is_dir():
            _lib = pathlib.Path(__file__).resolve().parent.parent.parent / "scripts" / "lib"
        if str(_lib) not in _sys.path:
            _sys.path.insert(0, str(_lib))
        from fabric_config import render_config_template
        return render_config_template(owner=owner, with_graphify=with_graphify, extra=extra)
    except Exception:
        return CONFIG_TEMPLATE.format(owner=owner, extra=extra)


CONFIG_TEMPLATE = """owner: {owner}
llm:
  base_url: http://localhost:11434/v1
  api_key: ollama
  local_model: gemma4:e4b-fixed
  model: qwen2.5-coder:7b
  compiler_model: deepseek-v4.1-flash:cloud

repos: {{}}

domains:
  agent-systems:
    signals: [agent, mcp, fastmcp, opencode, claude]
  web-systems:
    signals: [fastapi, flask, react, nextjs, supabase, postgresql]
{extra}
"""


def ensure_fabric_skeleton(fabric_dir, owner="sim", with_graphify=False):
    """Create the content skeleton + a starter fabric.yaml. Idempotent."""
    import yaml
    if owner == "sim":
        # the one owner chain (#155-B): fabric_config OWNER_SENTINEL default;
        # fall back to git identity directly (packaged mode has no harness
        # lib importable — and _sh takes ONE joined string, not argv)
        try:
            import sys as _sys
            _lib = pathlib.Path(__file__).resolve().parent / "_harness" / "scripts" / "lib"
            if not _lib.is_dir():
                _lib = pathlib.Path(__file__).resolve().parent.parent.parent / "scripts" / "lib"
            if _lib.is_dir() and str(_lib) not in _sys.path:
                _sys.path.insert(0, str(_lib))
            from fabric_config import get_config, get_owner, OWNER_SENTINEL
            owner = get_owner(get_config()) or OWNER_SENTINEL
        except Exception:
            owner = _sh("git config --global user.name") or "you"
    fabric_dir = Path(fabric_dir)
    fabric_dir.mkdir(parents=True, exist_ok=True)
    for d in DIRECTORIES:
        (fabric_dir / d).mkdir(parents=True, exist_ok=True)
    ag = fabric_dir / "AGENTS.md"
    if not ag.exists():
        # the sync-validation marker
        harness = Path(__file__).resolve().parent.parent.parent
        src = harness / "AGENTS.md"
        packaged = Path(__file__).resolve().parent / "_harness" / "AGENTS.md"
        src = src if src.exists() else packaged
        if src.exists():
            shutil.copy(src, ag)
    # content floor: the domain ontology seed (parity with the bash install
    # flow — without it a fresh corpus is "empty" by the lint contract)
    onto = fabric_dir / "corpus" / "domains" / "ontology.md"  # scaffold seed, pre-layout root — guard-exempt
    if not onto.exists():
        onto.parent.mkdir(parents=True, exist_ok=True)
        onto.write_text("""---
type: ontology
title: Domain Ontology
---

# Domain Ontology

The ontology is living — `wf propose-domains` discovers new domains from
evidence signals; proposals merge only after human review
(`wf promote-domains --apply`). Per-fabric artifact (synced via `wf sync`).

## Domains

- `agent-systems`
""")
    cfg_path = fabric_dir / "fabric.yaml"
    if not cfg_path.exists():
        extra = ""
        if with_graphify:
            extra = "\nintegrations:\n  graphify:\n    enabled: true\n    graph_dir: graphify-out\n"
        cfg_path.write_text(_canonical_template(owner=owner, with_graphify=with_graphify, extra=extra))
        print(f"\033[0;32m✓\033[0m  Created {cfg_path}")
    return fabric_dir


def _sh(cmd):
    import subprocess
    try:
        return subprocess.run(cmd.split(), capture_output=True, text=True).stdout.strip()
    except Exception:
        return None
