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
    """sync/<machine>-<yyyymmdd-hhmm> — one branch per push."""
    from datetime import datetime
    stamp = datetime.now().strftime("%Y%m%d-%H%M")
    return f"sync/{machine_name()}-{stamp}"

def pr_merge_policy(changes):
    """'auto-merge' | 'review' for this push's file set (team mode)."""
    if evidence_prs_policy() == "review":
        return "review"
    if classify_changes([l[3:] for l in changes]) == "evidence":
        return "auto-merge"
    return "review"

def use_pr_mode(pr=False, no_pr=False):
    """--pr forces PR path, --no-pr forces direct; else the sticky
    fabric.yaml sync.mode decides (solo default). #100."""
    return pr or (sync_mode() == "team" and not no_pr)
