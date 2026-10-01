#!/usr/bin/env python3
# thread_signals.py — Graph signals for mining (#103)
#
# Reads registry/threads.json (the #102 index) and answers the pairwise
# question mining needs: how strongly are two records connected by evidence
# structure rather than wording? Signals:
#
#   same_session   — both events came from the same captured session
#   files_overlap  — the sessions behind two events touched shared files
#   continuation   — one session continues the other (explicit related_sessions edge)
#
# All deterministic, 0 tokens, fail-open (absent/missing index → no signals,
# mining degrades to today's text-only behavior).

import sys
import sys as _s, pathlib as _p
_HERE = _p.Path(__file__).resolve().parent
for _dir in (_HERE, _HERE.parent / "lib"):
    if str(_dir) not in _s.path:
        _s.path.insert(0, str(_dir))
import json
from pathlib import Path
from fabric_config import CORPUS_ROOT

import layout

THREADS_PATH = layout.registry(CORPUS_ROOT) / "threads.json"


def load_index(path=None):
    """threads.json or None — every consumer treats None as 'no signals'."""
    try:
        return json.loads((path or THREADS_PATH).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def build_graph(index):
    """Lookup structures: session → node, file → [sessions], continuation pairs.
    All session ids normalized lowercase (events may carry mixed case)."""
    session_node = {}
    file_sessions = {}
    continuations = set()
    for n in (index or {}).get("nodes", []):
        sid = str(n.get("session", "")).strip().lower()
        if not sid:
            continue
        session_node[sid] = n
        for f in n.get("files_touched") or []:
            file_sessions.setdefault(str(f).strip('"').lower(), set()).add(sid)
    for e in (index or {}).get("edges", []):
        if e.get("type") == "continues":
            continuations.add((str(e.get("source_session", "")).strip().lower(),
                               str(e.get("target", "")).strip().lower()))
    return session_node, file_sessions, continuations


def thread_boost(event_a, event_b, graph):
    """(boost, reasons) for a pair of experience events.

    boost: additive, capped; 0 when the pair shares no thread structure.
    Deterministic: same inputs → same boost. Signals stack:
      same_session  +0.4  (same conversation)
      files_overlap +0.2  (shared file footprint)
      continuation  +0.3  (explicit session continuity edge)
    """
def thread_boost(event_a, event_b, graph):
    """(boost, reasons) for a pair of experience events.

    boost: additive, capped; 0 when the pair shares no thread structure.
    Deterministic: same inputs → same boost. Signals stack:
      same_session  +0.4  (same conversation)
      files_overlap +0.2  (shared file footprint)
      continuation  +0.3  (explicit session continuity edge)
    """
    session_node, file_sessions, continuations = graph
    reasons = []
    boost = 0.0

    sa = str(event_a.get("session") or "").strip().lower()
    sb = str(event_b.get("session") or "").strip().lower()

    if sa and sb:
        if sa == sb:
            boost += 0.4
            reasons.append("same_session")
        else:
            # file_sessions: file → {sessions}; shared = files both touched
            fa = {f for f, sessions in file_sessions.items() if sa in sessions}
            fb = {f for f, sessions in file_sessions.items() if sb in sessions}
            shared = fa & fb
            if shared:
                boost += 0.2
                reasons.append(f"files_overlap:{len(shared)}")
        if (sa, sb) in continuations or (sb, sa) in continuations:
            boost += 0.3
            reasons.append("continuation")
    return (min(boost, 0.9), reasons)


def thread_context(event_a, event_b, graph):
    """Human-readable thread context for judgment prompts (#103b): what the
    decision model should know about the pair beyond their text. Empty string
    when nothing connects them."""
    boost, reasons = thread_boost(event_a, event_b, graph)
    if not reasons:
        return ""
    parts = []
    if "same_session" in reasons:
        parts.append("both records come from the same captured session")
    if any(r.startswith("files_overlap") for r in reasons):
        parts.append("the sessions behind them touched shared files")
    if "continuation" in reasons:
        parts.append("one session explicitly continues the other")
    return f"[thread context: {'; '.join(parts)}]"


def classify_pair(event_a, event_b, graph, base_similarity, threshold):
    """Cluster-candidate decision for one pair, thread-aware (#103a).

    Returns (merge, reason). Text similarity still decides at the margin;
    thread signals rescue near-miss pairs (graph traversal feeds the
    decision, it does not replace the text gate entirely): a pair needs
    (base_similarity + boost) >= threshold — wording OR structure."""
    boost, reasons = thread_boost(event_a, event_b, graph)
    combined = base_similarity + boost
    if combined >= threshold:
        if base_similarity >= threshold:
            return (True, "text")
        return (True, "thread:" + ",".join(reasons))
    return (False, "")