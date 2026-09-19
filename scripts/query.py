#!/usr/bin/env python3
# query.py — Query the evidence fabric
#
# Usage:
#   python3 scripts/query.py "Why does the bridge batch writes but pipeline reads?"
#   python3 scripts/query.py "What patterns apply to single-writer systems?" --verbose
#   python3 scripts/query.py "What did we decide about the bridge?" --type decision
#   python3 scripts/query.py "What should I investigate next?" --type gap
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
import re
import yaml
import argparse
from pathlib import Path
from datetime import date
from collections import Counter
from wf_common import parse_frontmatter, norm

try:
    import yaml
    HAVE_YAML = True
except ImportError:
    HAVE_YAML = False

VAULT_ROOT = Path(__file__).parent.parent


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
    SKIP_PARTS = {".git", ".obsidian", ".opencode", "__pycache__", "templates",
                  "schemas", "evaluations", "raw", "traces"}
    pages = []
    for p in VAULT_ROOT.rglob("*.md"):
        rel = p.relative_to(VAULT_ROOT)
        parts = rel.parts
        if any(x in SKIP_PARTS for x in parts):
            continue
        if rel.name in ("index.md", "log.md", "README.md", "CONTRIBUTING.md", "AGENTS.md"):
            continue
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

        final_score = overlap * boost
        scored.append((final_score, pg))

    scored.sort(key=lambda x: -x[0])
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

def generate_answer(query, scored, pages, query_type):
    """Produce a structured answer per the query protocol."""
    if not scored:
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
        lines.append("A candidate pattern is pending review — promote it: `python3 scripts/promote.py --list`")
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

    if args.verbose:
        print(f"After graph expansion: {len(expanded)}", file=sys.stderr)

    answer = generate_answer(args.query, expanded, pages, query_type)
    print(answer)

    if args.save:
        save_synthesis(args.query, answer, pages)


if __name__ == "__main__":
    main()