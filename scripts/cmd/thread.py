#!/usr/bin/env python3
# thread.py — Evidence-graph thread lookup (#104)
#
# `wf thread <session-or-claim-id>` — the deterministic audit surface for the
# thread index (#102): what claims came from this session/PR, what files the
# session touched, which sessions it continues. 0 tokens; pure threads.json +
# frontmatter reads. Gate: absent/stale index → clean no-op with a hint.
#
# Usage:
#   python3 scripts/cmd/thread.py <id>            # neighborhood for one node
#   python3 scripts/cmd/thread.py <id> --json     # machine-readable
#   python3 scripts/cmd/thread.py --stats         # index inventory

import sys
import sys as _s, pathlib as _p
_HERE = _p.Path(__file__).resolve().parent
for _dir in (_HERE, _HERE.parent / "lib"):
    if str(_dir) not in _s.path:
        _s.path.insert(0, str(_dir))
import json
import argparse
import re
from pathlib import Path
from wf_common import parse_frontmatter
from fabric_config import CORPUS_ROOT

import layout

THREADS_PATH = layout.registry(CORPUS_ROOT) / "threads.json"


def load_index():
    """threads.json or None (absent/unreadable → clean no-op upstream)."""
    try:
        return json.loads(THREADS_PATH.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def resolve_node(index, needle):
    """The node matching a session id, pr number, or file stem
    (case-insensitive). PR forms: 597 / pr 597 / pr-597 / #597 (#e2e: the
    natural two-word form never matched)."""
    n = str(needle).strip().lower()
    m = re.match(r"^(?:pr[ -]?|#)(\d+)$", n)
    pr_num = m.group(1) if m else (n if n.isdigit() else None)
    for node in index.get("nodes", []):
        if str(node.get("session", "")).lower() == n:
            return node
        if pr_num is not None and str(node.get("pr")) == pr_num:
            return node
        stem = Path(node.get("file", "")).stem.lower()
        if stem == n:
            return node
    return None


def claim_edges_for(index, node):
    """Claim edges terminating at this node — matched on session id and the
    slug forms ingest generates from the capture path. ingest truncates the
    slug to 80 chars AFTER slugify (then .rstrip('-') normalization loses the
    trailing dash), so exact-form matching breaks on long chat filenames
    (sim finding #11) — prefix match covers every truncation variant."""
    from wf_common import slugify
    out = []
    n_file = str(node.get("file", "")).lower()
    n_session = str(node.get("session", "")).lower()
    raw_rel = n_file
    if raw_rel.startswith("evidence/raw/"):
        raw_rel = raw_rel[len("evidence/raw/"):]
    prefix = "src-" + slugify(raw_rel)[:80]
    for e in index.get("edges", []):
        if e.get("type") not in ("originated_in", "decided_in", "validated_in"):
            continue
        target = str(e.get("target", "")).lower().strip()
        if target == n_session or target == prefix or (
                target.startswith("src-") and prefix.startswith(target) and len(target) >= 60):
            out.append(e)
    return out


def related_sessions_for(index, node):
    """Session continuity edges (continues) touching this node."""
    out = []
    sid = str(node.get("session", ""))
    for e in index.get("edges", []):
        if e.get("type") != "continues":
            continue
        if str(e.get("source_session", "")) == sid or str(e.get("target", "")) == sid:
            out.append(e)
    return out


def neighborhood(index, needle):
    """The deterministic thread neighborhood for one node id. None when the
    needle matches nothing or the index is missing."""
    if not index:
        return None
    node = resolve_node(index, needle)
    if node is None:
        return None
    return {
        "node": node,
        "claim_edges": claim_edges_for(index, node),
        "related": related_sessions_for(index, node),
    }


def render(nb):
    node = nb["node"]
    lines = []
    kind = node.get("kind", "?")
    title = node.get("session") or f"PR #{node.get('pr')}"
    lines.append(f"Thread: {title}  ({kind}, project: {node.get('project', '?')})")
    lines.append(f"  file: {node.get('file', '?')}")
    if kind == "pr-record":
        lines.append(f"  pr: #{node.get('pr')} [{node.get('pr_state')}] repo: {node.get('source_repo', '?')}")
        if node.get("merged_at"):
            lines.append(f"  merged: {node['merged_at']}")
    else:
        lines.append(f"  harness: {node.get('harness', '?')}")
    files = node.get("files_touched") or []
    if files:
        lines.append(f"  files touched ({len(files)}):")
        for f in files[:10]:
            lines.append(f"    - {f}")
        if len(files) > 10:
            lines.append(f"    … and {len(files) - 10} more")
    if nb["claim_edges"]:
        lines.append(f"  claims ({len(nb['claim_edges'])}):")
        for e in nb["claim_edges"][:10]:
            lines.append(f"    - {e['claim']}  ({e['type']})")
    if nb["related"]:
        lines.append("  related sessions:")
        for e in nb["related"][:10]:
            if str(e.get("source_session", "")) == str(node.get("session", "")):
                lines.append(f"    → continues: {e.get('target')}")
            else:
                lines.append(f"    ← continued by: {e.get('source_session')}")
    return "\n".join(lines)


def _stats(index):
    nodes = index.get("nodes", [])
    edges = index.get("edges", [])
    chats = sum(1 for n in nodes if n.get("kind") == "chat-session")
    prs = sum(1 for n in nodes if n.get("kind") == "pr-record")
    claim_edges = sum(1 for e in edges if e.get("type") != "continues")
    continuations = sum(1 for e in edges if e.get("type") == "continues")
    print(f"Thread index: {THREADS_PATH}")
    print(f"  nodes: {len(nodes)} ({chats} chat sessions, {prs} PR records)")
    print(f"  edges: {len(edges)} ({claim_edges} claim-provenance, {continuations} continuations)")


def main():
    parser = argparse.ArgumentParser(description="Thread neighborhood lookup (0 tokens)")
    parser.add_argument("id", nargs="?", help="Session id, PR number, or capture file stem")
    parser.add_argument("--json", action="store_true", help="Machine-readable output")
    parser.add_argument("--stats", action="store_true", help="Index summary")
    args = parser.parse_args()

    index = load_index()
    if index is None:
        print("No thread index (registry/threads.json) — run: wf rebuild-index", file=sys.stderr)
        return 2

    if args.stats:
        _stats(index)
        return 0

    if not args.id:
        parser.print_help()
        return 2

    nb = neighborhood(index, args.id)
    if nb is None:
        print(f"No thread node matches {args.id!r} (sessions, PR numbers, or file stems)", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(nb, indent=2, default=str))
    else:
        print(render(nb))
    return 0


if __name__ == "__main__":
    sys.exit(main())