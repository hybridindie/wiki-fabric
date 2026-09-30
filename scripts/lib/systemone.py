#!/usr/bin/env python3
"""systemone.py — System One decision-model surface shared by the retrieval tiers.

Local-first: ollama serves the full System One wire protocol locally
(POST /v1/systemone — same protocol as TypeSafe's Jev cloud, no auth on
localhost). Supported models: the Tev/Nimble decision family (the server
rejects others: "use a local Nimble or Tev GGUF model").

Retrieval use cases (empirically calibrated, 2026-09-30):
  - systemone_rank(): batch relevance rerank of lexical candidates —
    sharp separation on diverse candidates (0.97 direct / 0.03 unrelated)
    where set-overlap scoring gives collisions identical scores.
  - systemone_hop(): per-edge traversal gate for graph expansion.
  - systemone_pair(): claim-pair relation classifier (supports /
    contradicts / supersedes) for review-queue triage.

Every call: localhost only (egress-free), latency-budgeted, and
degrades to None (caller's lexical order stands) on any failure. The
decision model is a judge, never a content writer — humans gate
canonical edits (AGENTS.md rule 5).
"""
import os
import re
import sys
import json as _json
import pathlib as _p

_HERE = _p.Path(__file__).resolve().parent
for _d in (_HERE, _HERE.parent / "lib"):
    if str(_d) not in sys.path:
        sys.path.insert(0, str(_d))

from wf_common import RETRIEVAL, TIMEOUT_API  # noqa: E402

# System One model gates
SYSTEMONE_JUDGE_PREFIXES = ("tev", "nimble")   # ollama's server-side gate
HOSTED_FARM_TAGS = ("cloud", "hosted", "remote")  # ollama's hosted farm — egress, NEVER local
DEFAULT_JUDGE_TAG = "tev1:latest"              # 4B, fast, deterministic keep-warm

_LATENCY_BUDGET_MS = 2000   # fusion tier ceiling; exceeded → lexical order stands


def _systemone_url(base_url):
    """Normalize any base (host, /v1-suffix forms) to the /v1/systemone URL."""
    b = str(base_url or "").rstrip("/")
    if b.endswith("/v1"):
        b = b[:-3]
    return b + "/v1/systemone"


def _looks_like_ollama_tag(tag):
    """Tag shape (indifferent to local/cloud): bare <name>:<tail>."""
    m = str(tag or "")
    return ":" in m and "/" not in m and not m.startswith(":")


def _ollama_tag_ok(tag, prefixes=SYSTEMONE_JUDGE_PREFIXES):
    m = str(tag or "")
    if ":" not in m or "/" in m:
        return False
    tail = m.rsplit(":", 1)[1].lower()
    if tail in HOSTED_FARM_TAGS:
        return False
    if not re.match(r"[a-z0-9][a-z0-9._-]*", tail) or tail.isdigit():
        return False  # host:port
    low = m.lower()
    return low.startswith(prefixes)


def judge_tag():
    """The System One tag: judgment.local_model → llm.local_model (when a
    supported server tag) → DEFAULT_JUDGE_TAG."""
    try:
        from fabric_config import get_config
        cfg = get_config()
        candidates = [(((cfg.get("integrations") or {}).get("judgment") or {}).get("local_model")),
                      (cfg.get("llm") or {}).get("local_model")]
        for m in candidates:
            if m and str(m).strip():
                if _ollama_tag_ok(m):
                    return str(m).strip()
                if _looks_like_ollama_tag(m):
                    if str(m).rsplit(":", 1)[1].lower() in HOSTED_FARM_TAGS:
                        raise SystemOneUnavailable(
                            f"tag {m!r} routes over the network (hosted farm) — "
                            f"not a local judge; use a Tev/Nimble tag")
                    return DEFAULT_JUDGE_TAG  # valid server tag, not System One
        return DEFAULT_JUDGE_TAG
    except SystemOneUnavailable:
        raise
    except Exception:
        return DEFAULT_JUDGE_TAG


class SystemOneUnavailable(RuntimeError):
    """The decision-model route is disabled/unreachable — callers degrade."""


def systemone(base_url, model, state, questions, timeout_ms=None, headers=None):
    """The one System One POST. Raises SystemOneUnavailable on failure."""
    import urllib.request
    body = {"model": model, "state": state or "", "questions": questions}
    req = urllib.request.Request(
        _systemone_url(base_url),
        data=_json.dumps(body).encode(),
        headers={"Content-Type": "application/json", **(headers or {})})
    timeout = (timeout_ms / 1000) if timeout_ms else TIMEOUT_API
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return _json.loads(resp.read().decode())
    except Exception as e:
        raise SystemOneUnavailable(f"systemone call failed ({model}): {e}")


def systemone_active():
    """Fusion-tier gate: integrations.judgment.enabled AND an ollama base_url
    configured (localhost tier). Env WIKI_SYSTEMONE_DISABLE=1 = hard off.
    Route choice is honored: a fabric that picked route:"cloud" keeps its
    verdicts on TypeSafe — the fusion tier routes the POST wherever the
    fabric decided (systemone_rank's placement logic stays the caller's)."""
    if os.environ.get("WIKI_SYSTEMONE_DISABLE") == "1":
        return False
    try:
        from fabric_config import get_config, is_integration_active
        cfg = get_config()
        if not is_integration_active(cfg, "judgment"):
            return False
        return bool((cfg.get("llm") or {}).get("base_url"))
    except Exception:
        return False


def _base_url():
    from fabric_config import get_config
    return (get_config().get("llm") or {}).get("base_url") or "http://localhost:11434/v1"


def systemone_rank(query, pages, keys=None, instructions=None,
                   budget_ms=_LATENCY_BUDGET_MS):
    """Batch relevance rerank: P(page answers the query) for each candidate.

    pages: [{stem, text}] (stem is the join key)
    keys: optional list of stems to keep (others: dropped)
    Returns {stem: p} — None when the route is inactive/unreachable.

    Latency shape (tev1:latest, keep-warm localhost): ~70ms/page batched;
    top-10 ≈ 0.7s. The caller decides placement — this module never
    re-ranks unilaterally.
    """
    if not pages:
        return {}
    if not systemone_active():
        return None
    keys = list(keys) if keys is not None else [p["stem"] for p in pages]
    by_stem = {p["stem"]: p.get("body") or p.get("text") or "" for p in pages}
    stems = [s for s in keys if s in by_stem]
    if not stems:
        return None
    model = judge_tag()
    state = (f"QUERY: {query}\n\n" +
             "\n\n".join(f"PAGE[{s}]: {by_stem[s][:900]}" for s in stems))
    questions = {s: {"type": "noul",
                     "instructions": instructions or
                     "Does this page answer the query?",
                     "criteria": {"false": "different subject even if words overlap",
                                  "true": "answers what was asked"}}
                 for s in stems}
    try:
        import time
        start = time.monotonic()
        out = systemone(_base_url(), model, state, questions,
                        timeout_ms=max(budget_ms, 500))
        elapsed = (time.monotonic() - start) * 1000
        answers = out.get("answers") or {}
        result = {}
        for s in stems:
            a = answers.get(s) or {}
            v = a.get("noul")
            result[s] = float(v) if v is not None else None
        if elapsed > budget_ms and all(v is None or v < 0.05 for v in result.values()):
            return None  # slow AND useless → lexical order stands
        return result
    except SystemOneUnavailable:
        return None


def systemone_hop(query, edges, budget_ms=_LATENCY_BUDGET_MS):
    """Per-edge traversal gate: P(following this edge serves the query).

    edges: [(stem, rel_type, rel_context)]
    Returns {stem: p|None}; None when inactive."""
    if not systemone_active():
        return None
    model = judge_tag()
    described = "\n".join(f"EDGE[{s}] --{t}--> " + (c or "context unavailable")
                          for s, t, c in edges)
    state = f"QUERY: {query}\n\n{described}"
    questions = {s: {"type": "noul",
                     "instructions": "Should retrieval follow this relation edge for the query?",
                     "criteria": {"false": "relation is incidental (same doc, same project, superseded)",
                                  "true": "edge plausibly carries the answer forward"}}
                 for s, _, _ in edges}
    try:
        out = systemone(_base_url(), model, state, questions,
                        timeout_ms=max(budget_ms, 500))
        return {s: (float((out.get("answers") or {}).get(s, {}).get("noul"))
                    if (out.get("answers") or {}).get(s, {}).get("noul") is not None else None)
                for s, _, _ in edges}
    except SystemOneUnavailable:
        return None


_SYSTEMONE_REL_OPTIONS = {
    "supports": "second claim corroborates/covers the first",
    "contradicts": "both claims cannot hold at once",
    "supersedes": "second claim is a newer revision replacing the first",
    "unrelated": "the claims describe different things without interaction",
}


def systemone_pair(claim_a, claim_b, budget_ms=_LATENCY_BUDGET_MS):
    """Claim-pair relation classifier (System One choice head).

    Returns {'choice': str, 'probabilities': {...}, 'confidence': f} —
    None when inactive/unsupported kind.

    Triage use: feed contradictions into the review queue (contested
    states are the representation — this proposes, humans decide)."""
    if not systemone_active():
        return None
    model = judge_tag()
    state = f"CLAIM-A: {claim_a[:1200]}\n\nCLAIM-B: {claim_b[:1200]}"
    q = {"pair": {"type": "choice",
                  "instructions": "Both claims describe the same subject area. Classify their interaction:",
                  "criteria": _SYSTEMONE_REL_OPTIONS}}
    try:
        out = systemone(_base_url(), model, state, q,
                        timeout_ms=max(budget_ms, 500))
        a = (out.get("answers") or {}).get("pair") or {}
        return {"choice": str(a.get("choice", "")),
                "probabilities": a.get("probabilities"),
                "confidence": a.get("confidence")}
    except SystemOneUnavailable:
        return None