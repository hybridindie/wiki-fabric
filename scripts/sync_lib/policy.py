"""Sync policy: mode/evidence-PR settings + change-plane classification
(#124.5b). Pure logic — the most-tested surface; no git I/O here."""
import re
import socket
from datetime import date

# Plane classification via layout segments (single truth — a dir rename
# updates planes automatically; literal strings here were the drift class).
import layout as _layout

def _pfx(*names):
    return tuple(str(_layout.seg(n)) + "/" for n in names)

ATOM_PATHS = _pfx("evidence_claims", "concepts", "patterns", "anti_patterns",
                  "skills", "syntheses", "domains", "projects", "global",
                  "questions")
EVIDENCE_PATHS = _pfx("evidence_raw", "evidence_sources", "evidence_source_summaries",
                      "evidence_experiments", "evidence_traces", "evidence_inbox",
                      "evidence_insights", "evidence_memory")
REGISTRY_PATHS = _pfx("registry")

# #181: derived artifacts both machines regenerate wholesale — a merge
# conflict here is resolved by REGENERATING locally, never by the
# ours/theirs/union flow. Files (not dirs): explicit registry/ paths.
_DERIVED = ("registry/catalog.json", "registry/threads.json",
            "registry/wiki-graph.json", "registry/wiki-export-manifest.json")
DERIVED_REGENERABLE_PATHS = tuple(str(_layout.registry(None)) + name.split("/", 1)[1]
                                  if False else f"registry/{_f}" for _f, _layout in
                                  [("catalog.json", None), ("threads.json", None),
                                   ("wiki-graph.json", None), ("wiki-export-manifest.json", None)])

# #182 decision (machine-local): per-machine delivery/state planes that
# never travel and never conflict — the queues they summarize are the
# synced truth.
MACHINE_LOCAL_PATHS = _pfx("registry_receipts") + ("registry/pending-gate.md",)











import wf_common
from wf_common import github_repo_from_remote_url

import sys

def sync_mode(config=None):
    """sync.mode from fabric.yaml: 'solo' (default, sticky — direct push) or
    'team' (every push opens a PR)."""
    try:
        from fabric_config import get_config
        cfg = config or get_config()
        mode = str((cfg.get("sync") or {}).get("mode", "solo")).lower()
        return mode if mode in ("solo", "team") else "solo"
    except Exception:
        return "solo"


def evidence_prs_policy(config=None):
    """sync.evidence_prs: 'auto' (default — evidence-only PRs auto-merge on
    green CI) or 'review' (everything waits for a human)."""
    try:
        from fabric_config import get_config
        cfg = config or get_config()
        pol = str((cfg.get("sync") or {}).get("evidence_prs", "auto")).lower()
        return pol if pol in ("auto", "review") else "auto"
    except Exception:
        return "auto"


def classify_change(path_str):
    """'atom' | 'evidence' | 'registry' | 'other' — the PR merge policy input.
    A changed file set is as risky as its riskiest member (atoms dominate)."""
    p = path_str.lstrip('"').strip()
    if p.startswith(ATOM_PATHS):
        return "atom"
    if p.startswith(EVIDENCE_PATHS):
        return "evidence"
    if p.startswith(MACHINE_LOCAL_PATHS):
        return "machine-local"
    if p.startswith(DERIVED_REGENERABLE_PATHS):
        return "derived"
    if p.startswith(REGISTRY_PATHS):
        return "registry"
    return "other"


def classify_changes(paths):
    """Worst-case plane for a change set; empty set → 'registry' (bookkeeping)."""
    kinds = {classify_change(p) for p in paths}
    if "atom" in kinds or "other" in kinds:
        return "atom"  # unknown paths treated as atoms (fail closed)
    if "evidence" in kinds:
        return "evidence"
    return "registry"

def machine_name():
    """Short machine id for sync branch names (hostname, sanitized)."""
    import socket
    host = socket.gethostname().split(".")[0].lower()
    return re.sub(r"[^a-z0-9-]", "-", host)[:30] or "unknown"

def pr_branch_name():
    """sync/<machine>-<yyyymmdd-hhmm> — one branch per push. The machine
    name resolves through the MODULE (call-time — the #178 test-patch seam)."""
    import sys as _sys
    mod = _sys.modules.get(__name__)
    machine = (mod.machine_name() if mod and hasattr(mod, "machine_name") else machine_name())
    from datetime import datetime
    stamp = datetime.now().strftime("%Y%m%d-%H%M")
    return f"sync/{machine}-{stamp}"

def pr_merge_policy(changes):
    """'auto-merge' | 'review' for this push's file set (team mode).
    Resolves evidence_prs_policy through the MODULE (call-time binding —
    test-patches bind; the from-import copies kept for API compat)."""
    import sys as _sys
    mod = _sys.modules.get(__name__)
    pol = (mod.evidence_prs_policy() if mod else evidence_prs_policy())
    if pol == "review":
        return "review"
    if classify_changes([l[3:] for l in changes]) == "evidence":
        return "auto-merge"
    return "review"

def use_pr_mode(pr=False, no_pr=False):
    """--pr forces PR path, --no-pr forces direct; else the sticky
    fabric.yaml sync.mode decides (solo default). #100."""
    return pr or (sync_mode() == "team" and not no_pr)
