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

CONFIG_TEMPLATE = """owner: {owner}
llm:
  base_url: http://localhost:11434/v1
  api_key: ollama
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
    cfg_path = fabric_dir / "fabric.yaml"
    if not cfg_path.exists():
        extra = ""
        if with_graphify:
            extra = "\nintegrations:\n  graphify:\n    enabled: true\n    graph_dir: graphify-out\n"
        import subprocess as _sp
        try:
            owner = _sh("git", "config", "--global", "user.name") or "you"
        except Exception:
            owner = "you"
        cfg_path.write_text(CONFIG_TEMPLATE.format(owner=owner, extra=extra))
        print(f"\033[0;32m✓\033[0m  Created {cfg_path}")
    return fabric_dir


def _sh(cmd):
    import subprocess
    try:
        return subprocess.run(cmd.split(), capture_output=True, text=True).stdout.strip()
    except Exception:
        return None
