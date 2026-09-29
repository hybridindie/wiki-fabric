#!/usr/bin/env python3
# query.py — Query the evidence fabric
#
# Usage:
#   python3 scripts/cmd/query.py "Why does the bridge batch writes but pipeline reads?"
#   python3 scripts/cmd/query.py "What patterns apply to single-writer systems?" --verbose
#   python3 scripts/cmd/query.py "What did we decide about the bridge?" --type decision
#   python3 scripts/cmd/query.py "What should I investigate next?" --type gap
#
# Implements the retrieval policy from AGENTS.md:
#   | Query type             | Retrieval                                    |
#   |------------------------|----------------------------------------------|
#   | Exact repo/API         | lexical: index → source record → raw         |
#   | "What did we decide?"  | decisions + recency-weighted synthesis       |
#   | Cross-source synthesis | claims → relations → linked sources          |
#   | Claim verification     | claim registry + locators only               |
#   | Comparison (A vs B)    | experiment index filtered by environment     |
#   | "What to investigate?" | questions + unresolved contradictions        |
#
# Output: structured answer per the query protocol (bottom line / evidence /
# caveats / confidence / next action). Files as a synthesis page when --save.

import sys
import sys as _s, pathlib as _p
_HERE = _p.Path(__file__).resolve().parent
# Explicit import bootstrap: this script's own dir (same-dir siblings)
# + scripts/lib (shared modules). No shotgun path injection.
for _dir in (_HERE, _HERE.parent / "lib"):
    if str(_dir) not in _s.path:
        _s.path.insert(0, str(_dir))
import re
import yaml
import argparse
from pathlib import Path
from datetime import date
from collections import Counter
from wf_common import parse_frontmatter, norm
from fabric_config import FABRIC_ROOT
from fabric_config import CORPUS_ROOT, VAULT_ROOT

try:
    import yaml
    HAVE_YAML = True
except ImportError:
    HAVE_YAML = False



def concept_match(query_norm, text_norm):
    """Score how well a piece of text matches a query by concept overlap."""
    query_words = set(norm(query_norm).split())
    text_words = set(norm(text_norm).split())
    if not query_words:
        return 0.0
    stopwords = {"the", "a", "an", "is", "of", "to", "in", "and", "or", "for",
                 "on", "with", "at", "by", "from", "that", "this", "it", "as",
                 "be", "are", "was", "were", "what", "why", "how", "does", "do"}
    content_words = query_words - stopwords
    if not content_words:
        return 0.0
    overlap = len(content_words & text_words) / len(content_words)
    return overlap


# ---------------------------------------------------------------------------
# Retrieval layers
# ---------------------------------------------------------------------------

def load_pages():
    """Load all wiki pages into memory with their frontmatter and body."""
    # wiki/ + syntheses/ are the human-facing generated layer: prose paraphrase
    # that shouldn't be fed back to a model (skipped by the shared walk,
    # wf_common.corpus_walk — #155-C). The machine consumes the wiki's
    # edges via registry/wiki-graph.json, not the prose.
    from wf_common import corpus_walk
    pages = []
    for p, parts, rel in corpus_walk(VAULT_ROOT):
        fm, body = parse_frontmatter(p)
        pages.append({
            "path": p,
            "rel": rel,
            "stem": rel.stem.lower(),
            "fm": fm,
            "body": body,
            "type": fm.get("type", ""),
        })
    return pages


def graphify_active():
    """Gate for graph proximity ranking (#48): integrations.graphify.enabled."""
    try:
        from fabric_config import get_config, is_integration_active
        return is_integration_active(get_config(), "graphify")
    except Exception:
        return False


def graph_edge_symbols(pg):
    """Code symbols reachable from a claim via graphify enrichment: the
    `graph_edges` frontmatter entries ('called_by:X', 'inherits:Y', ...).
    Method-style entries ('._handle_peer()') split into parts so a query
    naming the method matches."""
    edges = pg["fm"].get("graph_edges")
    if isinstance(edges, str):
        edges = [edges]
    out = set()
    for e in edges or []:
        if not isinstance(e, str):
            continue
        s = e.strip().strip('"')
        if ":" not in s:
            continue
        sym = s.split(":", 1)[1].strip().lower()
        out.add(sym)
        for part in re.findall(r"[a-z_][a-z0-9_]*", sym):
            if len(part) >= 4:
                out.add(part)
    return out


def symbol_tokens(query):
    """Identifiers from the query: snake_case/camelCase fragments, method
    calls, and dotted paths — the tokens graph proximity can match against."""
    toks = set()
    for m in re.finditer(r"[A-Za-z_][A-Za-z0-9_]*", query):
        raw = m.group(0)
        if len(raw) < 4 or raw.lower() in _SYMBOL_STOPWORDS:
            continue
        # split snake_case and camelCase into parts + keep the whole id
        toks.add(raw.lower())
        for part in re.findall(r"[A-Z][a-z0-9]+|[a-z][a-z0-9]*", raw):
            if len(part) >= 4:
                toks.add(part.lower())
    return toks


_SYMBOL_STOPWORDS = {"what", "does", "this", "that", "with", "from", "have",
                     "when", "where", "should", "would", "there", "about"}


def load_thread_index():
    """registry/threads.json or None (#104 gate: absent → all thread features
    no-op cleanly, same pattern as graphify gating)."""
    try:
        import json as _json
        return _json.loads((VAULT_ROOT / "registry" / "threads.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


_LINEAGE_QUERY_WORDS = {"where", "origin", "provenance", "discussed", "session",
                        "thread", "came", "source", "decided", "pr", "conversation"}


def thread_lineage(query, expanded, query_type, index=None, pages=None):
    """#104b: for lineage-shaped queries (or decision queries), collect the
    thread neighborhood of the top claims — 'where did this come from'.
    Returns [(claim_page, node, edge_type)]. Gated on the thread index;
    deterministic; empty for thread-free corpora. index injectable for tests."""
    if index is None:
        index = load_thread_index()
    if not index:
        return []
    q_words = set(norm(query).split())
    lineage_shaped = bool(q_words & _LINEAGE_QUERY_WORDS) or query_type == "decision"
    if not lineage_shaped:
        return []
    if not expanded and pages is not None:
        # lineage-shaped but lexically empty ("where did this come from") —
        # anchor on the most recent provenance-carrying claims instead
        # (deterministic: load order is stable)
        candidates = [pg for pg in pages
                      if pg["type"] == "claim" and pg["fm"].get("relations")]
        expanded = [(0.0, pg) for pg in candidates[-8:][::-1]]
    if not expanded:
        return []
    from wf_common import slugify
    nodes = {str(n.get("session", "")).lower(): n for n in index.get("nodes", [])
             if n.get("session")}
    nodes_by_slug = {}
    for n in index.get("nodes", []):
        f = str(n.get("file", ""))
        raw_rel = f[len("evidence/raw/"):] if f.startswith("evidence/raw/") else f
        # ingest truncates slugs to 80 chars (sim finding #11) — index by the
        # truncated form so long chat-capture filenames join
        nodes_by_slug["src-" + slugify(raw_rel)[:80]] = n
        nodes_by_slug["src-" + slugify(raw_rel)] = n
    hits = []
    seen_nodes = set()
    for score, pg in expanded[:8]:
        if pg["type"] != "claim":
            continue
        rels = pg["fm"].get("relations") or []
        if not isinstance(rels, list):
            continue
        for r in rels:
            if not isinstance(r, dict) or r.get("type") not in ("originated_in", "decided_in", "validated_in"):
                continue
            target = str(r.get("target", "")).strip('"[]').lower()
            node = nodes_by_slug.get(target) or nodes.get(target)
            if node and id(node) not in seen_nodes:
                seen_nodes.add(id(node))
                hits.append((pg, node, r.get("type")))
    return hits


EMBED_INFO = None  # set by embed_boost: {"source", "n_vectors"} — answer reports it


def _embed_active():
    """Gate for the embeddings re-rank tier (#12): integrations.embeddings.enabled
    AND fastembed importable. Never fatal — the lexical+graph ranker stands alone."""
    try:
        from fabric_config import get_config, is_integration_active
        if not is_integration_active(get_config(), "embeddings"):
            return False
        import importlib.util as _u
        return _u.find_spec("fastembed") is not None
    except Exception:
        return False


def embed_boost(scores, pages, query):
    """Semantic re-rank signal (#12): cosine(query, claim) fused into the
    lexical score (0.5/0.5 min-max on the top-40 candidates). Off by default
    (integrations.embeddings); recorded in the answer when it ran."""
    from embed_index import load_or_build, embed_query
    from fabric_config import CORPUS_ROOT
    model, vectors, src = load_or_build(CORPUS_ROOT)
    if not vectors:
        return scores, None
    qe = embed_query(query)
    if qe is None:
        return scores, None
    import numpy as np
    from embed_index import cosine_top
    # rank ONLY the top-40 lexical candidates (query-time re-rank of top-K)
    top = scores[:40]
    if not top:
        return scores, None
    lex = np.array([s for s, _ in top], dtype=float)
    lex = (lex - lex.min()) / (lex.max() - lex.min() + 1e-9)
    sem = []
    id_set = {}
    for i, (_, pg) in enumerate(top):
        stem = Path(pg["path"]).stem if pg.get("path") else ""
        id_set[stem] = i
        v = vectors.get(stem)
        if v is None:
            sem.append(0.0)
            continue
        denom = (np.linalg.norm(qe) * np.linalg.norm(v)) or 1e-9
        sem.append(float(np.dot(np.asarray(qe), v) / denom))
    sem = np.array(sem, dtype=float)
    sem = (sem - sem.min()) / (sem.max() - sem.min() + 1e-9)
    fused = 0.5 * lex + 0.5 * sem
    order = np.argsort(-fused)
    reranked = [top[i] for i in order]
    reranked += scores[40:]
    global EMBED_INFO
    EMBED_INFO = {"source": src, "n_vectors": len(vectors)}
    return reranked, EMBED_INFO


def graphify_boost(pg, q_tokens, q_words):
    """Graph-proximity ranking signal (#48): a claim enriched with a symbol
    the query names is code-reachable — boost it modestly. Zero when the
    query names no symbols or the claim has no graph_edges. Deterministic."""
    if not q_tokens:
        return 0.0
    symbols = graph_edge_symbols(pg)
    if not symbols:
        return 0.0
    # whole-identifier hits count; part-hits (snake/camel fragments) count less
    hits = len(q_tokens & symbols)
    if not hits:
        return 0.0
    return 0.15 * min(hits, 3)


def score_pages(pages, query, query_type):
    """Score pages against the query, weighted by query type."""
    q_n = norm(query)
    q_words = set(q_n.split())
    scored = []

    for pg in pages:
        # Build searchable text from frontmatter + body
        text_parts = []
        for key in ("statement", "observed_problem", "intervention", "problem",
                     "solution", "title", "question"):
            val = pg["fm"].get(key, "")
            if val:
                text_parts.append(str(val))
        # First 500 chars of body
        text_parts.append(pg["body"][:500])

        full_text = " ".join(text_parts)
        t_n = norm(full_text)
        t_words = set(t_n.split())

        if not q_words:
            continue

        # Overlap score
        stopwords = {"the", "a", "an", "is", "of", "to", "in", "and", "or", "for",
                     "on", "with", "at", "by", "from", "that", "this", "it", "as",
                     "be", "are", "was", "were", "what", "why", "how", "does", "do",
                     "i", "should", "next", "investigate"}
        content_q = q_words - stopwords
        if not content_q:
            continue
        overlap = len(content_q & t_words) / len(content_q)

        if overlap < 0.15:
            continue

        # Type-based boosting per retrieval policy
        boost = 1.0
        if query_type == "decision":
            if pg["type"] == "decision":
                boost = 3.0
            elif pg["type"] == "experience-event":
                boost = 1.5
        elif query_type == "verify":
            if pg["type"] == "claim":
                boost = 3.0
        elif query_type == "gap":
            if pg["type"] == "question":
                boost = 3.0
            elif pg["type"] == "pattern":
                boost = 1.5
        elif query_type == "compare":
            if pg["type"] == "experiment":
                boost = 3.0
        elif query_type in ("auto", "concept"):
            if pg["type"] == "concept":
                boost = 2.0
            elif pg["type"] == "pattern":
                boost = 1.5
            elif pg["type"] == "claim":
                boost = 1.2

        # Recency boost (last_verified / created within 30 days)
        last_verified = pg["fm"].get("last_verified", "") or pg["fm"].get("updated", "")
        if last_verified:
            try:
                from datetime import datetime, timedelta
                lv = datetime.strptime(str(last_verified)[:10], "%Y-%m-%d")
                if lv >= datetime.now() - timedelta(days=30):
                    boost *= 1.2
            except ValueError:
                pass

        # Graph-proximity boost (#48, gated on integrations.graphify.enabled):
        # a claim whose graphify edges name a symbol the query mentions is
        # code-reachable — nudge it up. Additive, capped; deterministic.
        if graphify_active():
            boost += graphify_boost(pg, symbol_tokens(query), q_words)

        final_score = overlap * boost
        scored.append((final_score, pg))

    scored.sort(key=lambda x: -x[0])
    if _embed_active():
        scored, _info = embed_boost(scored, pages, query)
    return scored


def load_relations(pages):
    """Load claim relations for graph expansion."""
    relations = {}
    for pg in pages:
        if pg["type"] != "claim":
            continue
        rels = pg["fm"].get("relations", [])
        if isinstance(rels, list):
            for r in rels:
                if isinstance(r, dict) and "target" in r:
                    target = str(r["target"]).strip("[]").split("|")[0].lower()
                    relations.setdefault(pg["stem"], []).append({
                        "type": r.get("type", ""),
                        "target": target,
                    })
    return relations


def expand_graph(scored_pages, relations, pages, max_hops=1):
    """Expand results through claim relations (graph expansion)."""
    by_stem = {pg["stem"]: pg for pg in pages}
    seed_stems = {pg["stem"] for _, pg in scored_pages}
    scored_stems = {pg["stem"] for _, pg in scored_pages}
    expanded = set()

    for hop in range(max_hops):
        new_seeds = set()
        for stem in seed_stems:
            if stem in expanded:
                continue
            expanded.add(stem)
            for rel in relations.get(stem, []):
                target = rel["target"]
                if target in by_stem and target not in seed_stems:
                    new_seeds.add(target)
        if not new_seeds:
            break
        seed_stems |= new_seeds

    # Return expanded pages (preserve original scoring order, append graph hits)
    result = list(scored_pages)
    for stem in expanded:
        if stem not in scored_stems and stem in by_stem:
            result.append((0.1, by_stem[stem]))  # low score = graph-discovered
    return result


# ---------------------------------------------------------------------------
# Answer generation
# ---------------------------------------------------------------------------

def generate_answer(query, scored, pages, query_type, symbol_hits=None, thread_hits=None):
    """Produce a structured answer per the query protocol.

    symbol_hits (#48): claims discovered via graphify symbol proximity —
    code-reachable evidence that lexical scoring missed. Rendered as their
    own evidence tier, never ranked above lexical evidence.
    thread_hits (#104): (claim, node, edge_type) provenance neighborhoods —
    lineage display only, never scored."""
    q_sym_set = symbol_tokens(query)
    thread_hits = [t for t in (thread_hits or []) if isinstance(t, tuple) and len(t) == 3]
    symbol_hits = [pg for pg in (symbol_hits or []) if isinstance(pg, dict) and pg.get("fm")]
    if not scored and not symbol_hits and not thread_hits:
        return "No relevant pages found for this query."

    # Take top results
    top = scored[:10]
    seen = set()
    evidence_claims = []
    evidence_other = []
    patterns = []
    concepts = []
    questions = []

    for score, pg in top:
        stem = pg["stem"]
        if stem in seen:
            continue
        seen.add(stem)

        t = pg["type"]
        if t == "claim":
            refs = pg["fm"].get("source_refs", [{}])
            ref = refs[0] if isinstance(refs, list) and refs else {}
            loc = ref.get("locator", "?")
            quote = ref.get("quote", "")[:80]
            evidence_claims.append({
                "statement": pg["fm"].get("statement", ""),
                "locator": loc,
                "quote": quote,
                "source": ref.get("source", "?"),
                "status": pg["fm"].get("status", "?"),
                "confidence": pg["fm"].get("confidence", "?"),
                "evidence_strength": pg["fm"].get("evidence_strength", "?"),
                "score": score,
            })
        elif t == "pattern":
            patterns.append({
                "id": pg["fm"].get("id", stem),
                "title": pg["fm"].get("title", ""),
                "maturity": pg["fm"].get("maturity", "?"),
                "status": pg["fm"].get("status", "?"),
                "score": score,
            })
        elif t == "concept":
            concepts.append({
                "title": pg["fm"].get("title", stem),
                "score": score,
            })
        elif t == "question":
            questions.append({
                "title": pg["fm"].get("title", stem),
                "priority": pg["fm"].get("priority", "?"),
                "score": score,
            })
        else:
            evidence_other.append({
                "type": t,
                "stem": stem,
                "title": pg["fm"].get("title", stem),
                "score": score,
            })

    # Build the answer
    lines = []
    lines.append(f"## Bottom line")
    lines.append("")

    # Bottom line from the top claim or pattern
    if evidence_claims:
        top_claim = evidence_claims[0]
        lines.append(f"{top_claim['statement']}")
    elif patterns:
        lines.append(f"{patterns[0]['title']} ({patterns[0]['status']}, maturity {patterns[0]['maturity']})")
    elif concepts:
        lines.append(f"See [[{concepts[0]['title']}]] for the relevant concept.")
    else:
        lines.append("See evidence below for the most relevant findings.")

    lines.append("")

    # Evidence
    if evidence_claims:
        lines.append("## Evidence")
        lines.append("")
        for ec in evidence_claims[:6]:
            lines.append(f"- {ec['statement'][:100]}")
            lines.append(f"  [{ec['locator']}] quote: \"{ec['quote'][:60]}...\"")
            lines.append(f"  status={ec['status']} conf={ec['confidence']} ev={ec['evidence_strength']}")
            lines.append("")

    if symbol_hits:
        lines.append("## Code-reachable evidence (graphify)")
        lines.append("")
        lines.append("Claims whose code-symbol graph neighborhood matches this query:")
        lines.append("")
        for pg in symbol_hits[:4]:
            refs = pg["fm"].get("source_refs", [{}])
            ref = refs[0] if isinstance(refs, list) and refs else {}
            stmt = pg["fm"].get("statement", "")
            syms = sorted(graph_edge_symbols(pg) & q_sym_set or graph_edge_symbols(pg))[:3]
            lines.append(f"- {stmt[:100]}")
            lines.append(f"  [{ref.get('locator', '?')}] quote: \"{ref.get('quote', '')[:60]}...\"")
            lines.append(f"  symbols: {', '.join(f'`{s}`' for s in syms)}")
            lines.append("")

    if thread_hits:
        lines.append("## Lineage (evidence graph)")
        lines.append("")
        for claim_pg, node, edge_type in thread_hits[:4]:
            kind = node.get("kind", "?")
            if kind == "pr-record":
                label = f"PR #{node.get('pr')} [{node.get('pr_state', '')}]"
            else:
                label = f"session {node.get('session', '?')[:24]} ({node.get('harness', '?')})"
            lines.append(f"- {claim_pg['fm'].get('statement', '')[:80]}")
            lines.append(f"  provenance: {edge_type} → {node.get('file', '?')} — {label}")
            files = node.get("files_touched") or []
            if files:
                lines.append(f"  files touched: {', '.join(files[:5])}")
            lines.append("")

    if patterns:
        lines.append("## Patterns")
        lines.append("")
        for p in patterns[:3]:
            lines.append(f"- [[{p['id']}]] — {p['title']} ({p['status']}, maturity {p['maturity']})")
        lines.append("")

    if concepts:
        lines.append("## Concepts")
        lines.append("")
        for c in concepts[:3]:
            lines.append(f"- [[{c['title']}]]")
        lines.append("")

    # Other results
    if evidence_other:
        lines.append("## Related pages")
        lines.append("")
        for eo in evidence_other[:4]:
            lines.append(f"- [[{eo['stem']}]] ({eo['type']})")
        lines.append("")

    # Open questions
    if questions:
        lines.append("## Open questions")
        lines.append("")
        for q in questions[:3]:
            lines.append(f"- [[{q['title']}]] (priority: {q['priority']})")
        lines.append("")

    # Confidence assessment
    lines.append("## Confidence")
    if EMBED_INFO:
        lines.append("")
        lines.append(f"_(semantic re-rank active: {EMBED_INFO['n_vectors']} vectors, "
                     f"index {EMBED_INFO['source']})_")
    lines.append("")
    if evidence_claims:
        n_high = sum(1 for ec in evidence_claims if ec["confidence"] == "high")
        n_supported = sum(1 for ec in evidence_claims if ec["status"] == "supported")
        n_primary = sum(1 for ec in evidence_claims if ec["evidence_strength"] == "primary")
        n_sources = len(set(ec["source"] for ec in evidence_claims))
        lines.append(f"{len(evidence_claims)} claims cited: {n_supported} supported, {n_primary} primary evidence.")
        if n_sources >= 2:
            lines.append(f"Cross-validated across {n_sources} sources.")
        elif n_sources == 1:
            lines.append("Single source — consider corroborating.")
    else:
        lines.append("No claims found — answer based on patterns/concepts only.")
    lines.append("")

    # Suggested next action
    lines.append("## Suggested next action")
    lines.append("")
    if patterns and any(p["status"] == "candidate" for p in patterns):
        lines.append("A candidate pattern is pending review — promote it: `python3 scripts/cmd/promote.py --list`")
    elif questions:
        lines.append(f"Investigate: [[{questions[0]['title']}]] (priority: {questions[0]['priority']})")
    elif evidence_claims:
        lines.append("File this answer as a synthesis page if reusable: `--save` flag.")
    else:
        lines.append("Ingest more sources to build up the knowledge base.")
    lines.append("")

    return "\n".join(lines)


def save_synthesis(query, answer, pages):
    """Save the answer as a synthesis page."""
    synth_dir = VAULT_ROOT / "syntheses"
    synth_dir.mkdir(parents=True, exist_ok=True)

    slug = re.sub(r'[^a-z0-9]+', '-', norm(query))[:60]
    today = date.today().isoformat()
    synth_path = synth_dir / f"syn-{today}-{slug}.md"

    # Collect cited claims
    cited = []
    for line in answer.split("\n"):
        m = re.search(r'\[\[(claim-[^\]]+)\]\]', line)
        if m:
            cited.append(m.group(1))

    synth_path.write_text(f"""---
type: synthesis
title: "{query[:80]}"
tags: [synthesis, query]
created: {today}
claims:
{chr(10).join(f'  - "[[{c}]]"' for c in cited) if cited else "  []"}
---

# Synthesis: {query}

{answer}
""")
    print(f"Saved synthesis: {synth_path.relative_to(VAULT_ROOT)}")
    return synth_path


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Query the evidence fabric")
    parser.add_argument("query", help="Question to answer")
    parser.add_argument("--type", default="auto",
                        choices=["auto", "decision", "verify", "compare", "gap", "concept"],
                        help="Query type (determines retrieval policy)")
    parser.add_argument("--save", action="store_true", help="Save answer as a synthesis page")
    parser.add_argument("--verbose", action="store_true", help="Show scoring detail")
    args = parser.parse_args()

    pages = load_pages()

    # Auto-detect query type if not specified
    query_type = args.type
    if query_type == "auto":
        q = args.query.lower()
        if any(w in q for w in ["decide", "decision", "why did we", "chose"]):
            query_type = "decision"
        elif any(w in q for w in ["verify", "is it true", "does", "check"]):
            query_type = "verify"
        elif any(w in q for w in ["compare", "versus", " vs ", "difference"]):
            query_type = "compare"
        elif any(w in q for w in ["investigate", "gap", "what should", "missing", "next"]):
            query_type = "gap"
        else:
            query_type = "concept"

    if args.verbose:
        print(f"Query type: {query_type}", file=sys.stderr)
        print(f"Pages loaded: {len(pages)}", file=sys.stderr)

    scored = score_pages(pages, args.query, query_type)

    if args.verbose:
        print(f"Scored pages: {len(scored)}", file=sys.stderr)
        for score, pg in scored[:5]:
            print(f"  {score:.3f} [{pg['type']:20}] {pg['stem']}", file=sys.stderr)

    # Graph expansion through claim relations
    relations = load_relations(pages)
    expanded = expand_graph(scored, relations, pages)

    # Symbol proximity discovery (#48, gated on integrations.graphify.enabled):
    # a claim whose graphify edges name a symbol the query mentions is
    # code-reachable even when lexically invisible (the claim text never says
    # the symbol name — the enrichment does). Collected separately so the
    # answer can surface them as a dedicated evidence tier.
    symbol_hits = []
    if graphify_active():
        scored_stems = {pg["stem"] for _, pg in expanded}
        q_syms = symbol_tokens(args.query)
        if q_syms:
            for pg in pages:
                if pg["type"] != "claim" or pg["stem"] in scored_stems:
                    continue
                if q_syms & graph_edge_symbols(pg):
                    expanded.append((0.1, pg))
                    scored_stems.add(pg["stem"])
                    symbol_hits.append(pg)
            if args.verbose and symbol_hits:
                print(f"  symbol-discovered: {[pg['stem'] for pg in symbol_hits][:5]}", file=sys.stderr)

    if args.verbose:
        print(f"After graph expansion: {len(expanded)}", file=sys.stderr)

    # Thread lineage (#104, gated on threads.json existing): lineage-shaped
    # queries surface the evidence-graph neighborhood — session/PR provenance
    # for the top scored claims. Provenance display only, never ranked above
    # lexical evidence.
    thread_hits = thread_lineage(args.query, expanded, query_type, pages=pages)

    answer = generate_answer(args.query, expanded, pages, query_type,
                             symbol_hits=symbol_hits, thread_hits=thread_hits)
    print(answer)

    if args.save:
        save_synthesis(args.query, answer, pages)


if __name__ == "__main__":
    main()