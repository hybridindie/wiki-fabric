#!/usr/bin/env python3
# synthesize.py — Cluster related claims into concept pages via LLM
#
# Usage:
#   python3 scripts/synthesize.py                    # synthesize all unsynthesized claims
#   python3 scripts/synthesize.py --dry-run          # show clusters without writing
#   python3 scripts/synthesize.py --min-claims 3     # min claims per concept
#
# Clusters claims by concept-overlap, then asks the LLM to synthesize each
# cluster into a type:concept page that draws ONLY from linked claims.

import os
import sys
import re
import yaml
import json
import hashlib
from pathlib import Path
from datetime import date
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent))
from fabric_config import FABRIC_ROOT
from fabric_config import CORPUS_ROOT
from fabric_config import CORPUS_ROOT
from extract_backends import llm_config
from fabric_config import get_local_model
from wf_common import parse_frontmatter, norm

VAULT_ROOT = CORPUS_ROOT
CLAIMS_DIR = VAULT_ROOT / "evidence" / "claims"
CONCEPTS_BASE = VAULT_ROOT

MIN_CLAIMS = 2


def load_claims():
    """Load all claims with their frontmatter and body."""
    claims = []
    for f in sorted(CLAIMS_DIR.glob("claim-*.md")):
        fm, body = parse_frontmatter(f)
        claims.append({
            "file": f,
            "stem": f.stem,
            "fm": fm,
            "body": body,
            "statement": fm.get("statement", ""),
            "status": fm.get("status", ""),
            "confidence": fm.get("confidence", ""),
            "evidence_strength": fm.get("evidence_strength", ""),
        })
    return claims


def load_existing_concepts():
    """Load already-synthesized concepts to avoid duplicates."""
    concepts = []
    for p in VAULT_ROOT.rglob("concepts/*.md"):
        if p.name == ".gitkeep":
            continue
        fm, body = parse_frontmatter(p)
        concepts.append({
            "path": p,
            "stem": p.stem,
            "fm": fm,
            "claims": fm.get("claims", []),
        })
    return concepts


def cluster_claims(claims, threshold=0.25):
    """Cluster claims by concept-overlap of their statements."""
    # Compute pairwise similarity
    n = len(claims)
    stmt_norms = [norm(c["statement"]) for c in claims]

    # Union-Find clustering
    parent = list(range(n))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    def union(i, j):
        pi, pj = find(i), find(j)
        if pi != pj:
            parent[pi] = pj

    for i in range(n):
        for j in range(i + 1, n):
            si = set(stmt_norm[i].split())
            sj = set(stmt_norm[j].split())
            if not si or not sj:
                continue
            stopwords = {"the", "a", "an", "is", "of", "to", "in", "and", "or",
                         "for", "on", "with", "at", "by", "from", "that", "this",
                         "it", "as", "be", "are", "was", "were", "per", "not",
                         "must", "can", "cannot", "only", "all", "each", "when"}
            si_c = si - stopwords
            sj_c = sj - stopwords
            if not si_c or not sj_c:
                continue
            overlap = len(si_c & sj_c) / max(len(si_c), len(sj_c))
            if overlap >= threshold:
                union(i, j)

    # Group by root
    clusters = defaultdict(list)
    for i in range(n):
        clusters[find(i)].append(i)

    # Filter by min size
    valid = []
    for root, indices in clusters.items():
        if len(indices) >= MIN_CLAIMS:
            valid.append([claims[i] for i in indices])

    return valid


def generate_concept_slug(cluster, existing_stems):
    """Generate a concept slug from the cluster's common theme."""
    # Extract common words from all statements
    all_words = []
    for c in cluster:
        words = set(norm(c["statement"]).split())
        stopwords = {"the", "a", "an", "is", "of", "to", "in", "and", "or", "for",
                     "on", "with", "at", "by", "from", "that", "this", "it", "as",
                     "be", "are", "was", "were", "per", "not", "must", "can",
                     "cannot", "only", "all", "each"}
        all_words.append(words - stopwords)

    if not all_words:
        return "concept-misc"

    # Find intersection (common theme)
    common = set.intersection(*all_words) if len(all_words) > 1 else all_words[0]
    common = sorted(common)

    if common:
        slug = "-".join(common[:4])
    else:
        # Fallback: union of most frequent
        from collections import Counter
        word_counts = Counter()
        for words in all_words:
            word_counts.update(words)
        common = [w for w, _ in word_counts.most_common(4)]
        slug = "-".join(common[:4])

    slug = slug[:60]
    # Ensure uniqueness
    base = slug
    idx = 1
    while slug in existing_stems:
        idx += 1
        slug = f"{base}-{idx}"
    return slug


SYNTH_PROMPT = """Synthesize the following related claims into a single concept definition.

The concept must draw ONLY from these claims - do not add external knowledge.

Claims:
{claims_block}

Output format (STRICT):
{{
  "title": "<Short concept name, 3-6 words>",
  "definition": "<2-3 sentence explanation drawing only from the claims above>",
  "applicability": [<list of conditions where this applies>],
  "open_questions": [<list of what is unknown or unverified>]
}}

Return ONLY the JSON object."""


def synthesize_concept(cluster, concept_slug):
    """Use LLM to synthesize a concept from a cluster of claims.

    Backend: WIKI_LLM_BACKEND=mlx (set by main() for local routes) runs the
    synthesis on-device via local_llm.generate; otherwise the OpenAI-compatible
    endpoint. Falls back to mechanical synthesis when the local backend is
    unavailable."""
    claims_text = "\n".join(
        f"- [{c['stem']}] {c['statement']} (status={c['status']}, conf={c['confidence']})"
        for c in cluster
    )
    prompt = SYNTH_PROMPT.replace("{claims_block}", claims_text)

    if os.environ.get("WIKI_LLM_BACKEND", "").lower() == "mlx":
        local_model = os.environ.get("WIKI_MLX_MODEL") or get_local_model()
        try:
            from local_llm import generate as local_generate
            output = local_generate(prompt, local_model, max_tokens=int(
                os.environ.get("WIKI_LOCAL_MAX_TOKENS", "4096")))
            m = re.search(r'\{.*\}', output, re.DOTALL)
            if m:
                return json.loads(m.group())
            print(f"local synthesis: no JSON object in output ({local_model})",
                  file=sys.stderr)
        except Exception as e:
            print(f"local synthesis failed ({local_model}): {e} — falling back",
                  file=sys.stderr)

    cfg = llm_config()
    try:
        import openai
        base_url = os.environ.get("WIKI_LLM_BASE_URL", cfg["base_url"])
        api_key = os.environ.get("WIKI_LLM_API_KEY", cfg["api_key"])
        model = os.environ.get("WIKI_LLM_MODEL", cfg["model"])

        client = openai.OpenAI(base_url=base_url, api_key=api_key)
        response = client.chat.completions.create(
            model=model,
            temperature=0.1,
            messages=[
                {"role": "system", "content": "You are a knowledge synthesizer. Synthesize related claims into concept definitions. Draw ONLY from the provided claims. Return ONLY a valid JSON object."},
                {"role": "user", "content": prompt}
            ]
        )
        output = response.choices[0].message.content
        m = re.search(r'\{.*\}', output, re.DOTALL)
        if m:
            return json.loads(m.group())
    except Exception as e:
        print(f"LLM synthesis failed: {e}", file=sys.stderr)

    # Fallback: mechanical synthesis (no LLM)
    return {
        "title": concept_slug.replace("-", " ").title(),
        "definition": f"Concept synthesized from {len(cluster)} related claims. See linked claims for details.",
        "applicability": [],
        "open_questions": [],
    }


def write_concept_page(concept_slug, cluster, synthesis, domain):
    """Write a type:concept page."""
    today = date.today().isoformat()
    claim_links = "\n".join(f'  - "[[{c["stem"]}]]"' for c in cluster)

    # Find domain from cluster claims (keyword heuristic against known domains)
    domains = set()
    for c in cluster:
        stem = c["stem"].lower()
        if any(k in stem for k in ("godot", "game", "engine", "chunk", "scene")):
            domains.add("godot-systems")
        else:
            domains.add("agent-systems")
    if not domains:
        domains.add("agent-systems")
    domain_list = sorted(domains)

    # Determine output path based on primary domain
    primary_domain = domain_list[0] if domain_list else "agent-systems"
    concepts_dir = VAULT_ROOT / "concepts"
    concepts_dir.mkdir(parents=True, exist_ok=True)
    concept_path = concepts_dir / f"concept-{concept_slug}.md"

    # Build applicability section
    applicability = synthesis.get("applicability", [])
    app_lines = "\n".join(f"- {a}" for a in applicability) if applicability else "_(to be determined)_"

    # Build open questions section
    oq = synthesis.get("open_questions", [])
    oq_lines = "\n".join(f"- {q}" for q in oq) if oq else "_None identified_"

    # Source coverage
    statuses = {}
    for c in cluster:
        statuses[c["status"]] = statuses.get(c["status"], 0) + 1

    concept_path.write_text(f"""---
type: concept
title: {synthesis.get("title", concept_slug.replace("-", " ").title())}
domain: [{", ".join(domain_list)}]
claims:
{chr(10).join(f'  - "[[{c["stem"]}]]"' for c in cluster)}
created: {today}
---

# Concept: {synthesis.get("title", concept_slug.replace("-", " ").title())}

## Definition

{synthesis.get("definition", "")}

## Supporting Claims ({len(cluster)})

| Claim | Statement | Status | Confidence |
|-------|-----------|--------|------------|
{chr(10).join(f'| [[{c["stem"]}]] | {c["statement"][:60]} | {c["status"]} | {c["confidence"]} |' for c in cluster)}

## Applicability

{app_lines}

## Open Questions

{oq_lines}

## Status Distribution

{chr(10).join(f'- {k}: {v}' for k, v in statuses.items())}
""")

    return concept_path


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Synthesize claims into concept pages")
    parser.add_argument("--dry-run", action="store_true", help="Show clusters without writing")
    parser.add_argument("--min-claims", type=int, default=2, help="Minimum claims per concept")
    parser.add_argument("--threshold", type=float, default=0.25, help="Concept-overlap threshold")
    parser.add_argument("--project", default=None, help="Project slug for stage routing")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    # Stage routing: synthesize sees sanitized claims — per-repo privacy override
    from fabric_config import get_stage_route, is_local_route, get_config, ensure_local_model
    _cfg = get_config()
    if args.project:
        _model = get_stage_route(_cfg, args.project, "synthesize")
        if is_local_route(_cfg, args.project, "synthesize"):
            os.environ["WIKI_LLM_BACKEND"] = "mlx"
            os.environ["WIKI_MLX_MODEL"] = _model
            ensure_local_model(_model, config=_cfg)  # offer download if missing
        else:
            os.environ["WIKI_LLM_BACKEND"] = ""
            os.environ["WIKI_LLM_MODEL"] = _model
    else:
        # No --project: cloud compiler path (synthesis is compiler work).
        os.environ["WIKI_LLM_BACKEND"] = ""

    global MIN_CLAIMS
    MIN_CLAIMS = args.min_claims

    claims = load_claims()
    existing = load_existing_concepts()

    print(f"Loaded {len(claims)} claims, {len(existing)} existing concepts")

    # Exclude claims already covered by existing concepts
    covered_stems = set()
    for ec in existing:
        for claim_link in ec["fm"].get("claims", []):
            stem = str(claim_link).strip("[]").split("|")[0].lower()
            covered_stems.add(stem)

    available = [c for c in claims if c["stem"] not in covered_stems]
    print(f"Available for synthesis: {len(available)} (excluded {len(covered_stems)} already in concepts)")

    if len(available) < MIN_CLAIMS:
        print("Not enough available claims for synthesis.")
        return

    # Cluster
    clusters = cluster_by_concept(available, args.threshold)

    print(f"Found {len(clusters)} clusters (>= {MIN_CLAIMS} claims)")
    print()

    existing_stems = {ec["stem"] for ec in existing}

    for i, cluster in enumerate(clusters):
        slug = generate_concept_slug(cluster, existing_stems)
        existing_stems.add(slug)

        print(f"Cluster {i+1}: {slug}")
        for c in cluster:
            print(f"  - {c['stem']}: {c['statement'][:70]}")

        if args.dry_run:
            continue

        # Synthesize via LLM
        print(f"  Synthesizing via LLM...")
        synthesis = synthesize_concept(cluster, slug)

        # Write concept page
        concept_path = write_concept_page(slug, cluster, synthesis, "agent-systems")
        print(f"  Created: {concept_path.relative_to(VAULT_ROOT)}")
        print()

    if args.dry_run:
        print("[DRY RUN] No files written")


def cluster_by_concept(claims, threshold):
    """Cluster claims by concept-overlap (extracted for testability)."""
    n = len(claims)
    parent = list(range(n))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    def union(i, j):
        pi, pj = find(i), find(j)
        if pi != pj:
            parent[pi] = pj

    stopwords = {"the", "a", "an", "is", "of", "to", "in", "and", "or", "for",
                 "on", "with", "at", "by", "from", "that", "this", "it", "as",
                 "be", "are", "was", "were", "per", "not", "must", "can",
                 "cannot", "only", "all", "each"}

    for i in range(n):
        for j in range(i + 1, n):
            si = set(norm(claims[i]["statement"]).split()) - stopwords
            sj = set(norm(claims[j]["statement"]).split()) - stopwords
            if not si or not sj:
                continue
            overlap = len(si & sj) / max(len(si), len(sj))
            if overlap >= threshold:
                union(i, j)

    clusters = defaultdict(list)
    for i in range(n):
        clusters[find(i)].append(i)

    valid = []
    for root, indices in clusters.items():
        if len(indices) >= MIN_CLAIMS:
            valid.append([claims[i] for i in indices])

    return valid


if __name__ == "__main__":
    main()