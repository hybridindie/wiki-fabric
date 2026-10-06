#!/usr/bin/env python3
# synthesize.py — Cluster related claims into concept pages via LLM
#
# Usage:
#   python3 scripts/cmd/synthesize.py                    # synthesize all unsynthesized claims
#   python3 scripts/cmd/synthesize.py --dry-run          # show clusters without writing
#   python3 scripts/cmd/synthesize.py --min-claims 3     # min claims per concept
#
# Clusters claims by concept-overlap, then asks the LLM to synthesize each
# cluster into a type:concept page that draws ONLY from linked claims.

import os
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
import json
import hashlib
from pathlib import Path
from datetime import date
from collections import defaultdict

from fabric_config import FABRIC_ROOT, get_tuning
from fabric_config import CORPUS_ROOT, VAULT_ROOT
from extract_backends import llm_config, LLM_TEMPERATURE
from fabric_config import get_local_model
from wf_common import STOPWORDS, parse_frontmatter, norm

import layout
import ontology as _ontology_sp


def _ontology_for_vocab():
    """Load the corpus ontology for vocabulary binding (canonical domains +
    aliases + shared tags). Missing ontology → empty vocabulary → no domain
    field (honest unbound)."""
    onto_path = layout.domains(VAULT_ROOT) / "ontology.md"
    try:
        return _ontology_sp.parse(onto_path.read_text(encoding="utf-8", errors="replace"))
    except OSError:
        return {"domains": set(), "aliases": {}, "tags": set()}

# Generic words filtered from concept NAMES (distinct from retrieval STOPWORDS —
# here they pollute a title, not a score; #155 audit: was two inline copies)
CONCEPT_NAME_FILTER = STOPWORDS | {
    "per", "not", "must", "can", "cannot", "only", "all", "each",
}

CLAIMS_DIR = layout.claims(VAULT_ROOT)
CONCEPTS_BASE = VAULT_ROOT

MIN_CLAIMS = get_tuning(None, 'synthesize', 'min_claims', 2)


def load_claims(project=None):
    """Load claims with their frontmatter and body. `project` scopes to that
    project's claim files (#171: --project restricted the synthesis output,
    not the clustering input — the O(n²) ran over the whole corpus either way)."""
    from wf_common import claim_prefix_for_project
    pattern = (claim_prefix_for_project(project) + "-*.md") if project else "claim-*.md"
    claims = []
    for f in sorted(CLAIMS_DIR.glob(pattern)):
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
def _concise_relations(claim):
    """Non-empty relations in compact form: type:target (deterministic
    input for the synthesis prompt's contradiction clause)."""
    rels = (claim["fm"].get("relations") or []) if isinstance(claim["fm"], dict) else []
    out = []
    for r in rels:
        if isinstance(r, dict) and r.get("type"):
            tgt = str(r.get("target", "")).replace("[[", "").replace("]]", "")
            out.append(f"{r['type']}:{tgt[:40]}")
    return ", ".join(out)


def _cluster_effects(cluster):
    """judged effects from registry/effects/<claim-stem>.effects.json —
    {claim_stem: "contradicts: <target-stem>"}. layout.effects is the single
    path truth; unreadable/torn files degrade to silence (never fatal)."""
    out = {}
    try:
        eff_dir = layout.effects(VAULT_ROOT)
    except Exception:
        return out
    for c in cluster:
        f = eff_dir / f"{c['stem']}.effects.json"
        if not f.exists():
            continue
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            continue
        marks = []
        for pair in (data.get("pairs") or []):
            eff = pair.get("effect")
            if eff in ("contradicts", "supersedes"):
                marks.append(f"{eff}:{str(pair.get('against', ''))[:40]}")
        if marks:
            out[c["stem"]] = "; ".join(marks[:3]) + (f" (+{len(marks)-3})" if len(marks) > 3 else "")
    return out


def generate_concept_slug(cluster, existing_stems):
    """Generate a concept slug from the cluster's common theme."""
    # Extract common words from all statements
    all_words = []
    for c in cluster:
        words = set(norm(c["statement"]).split())
        stopwords = CONCEPT_NAME_FILTER
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

Contradiction handling (#186 — REQUIRED when the claims disagree):
- If a claim is `status=contested`, or the claims contain contradicts/supersedes
  markers, do NOT silently pick a winner. Render the EVOLUTION: state the prior
  belief and the current state together ("previously held X; as of <newer
  evidence>, Y — the correction matters because ..."), folding the prior state
  into the definition rather than dropping it. The disputed aspect is recorded,
  not overwritten.
- Unresolved disagreement (both claims still supported, no newer tiebreak) is
  NOT a settled definition: name it in open_questions.

Output format (STRICT):
{{
  "title": "<Short concept name, 3-6 words>",
  "definition": "<2-3 sentence explanation drawing only from the claims above>",
  "applicability": [<list of conditions where this applies>],
  "open_questions": [<list of what is unknown, unverified, or DISPUTED (live contradictions)>]
}}

Return ONLY the JSON object."""


def synthesize_concept(cluster, concept_slug):
    """Use LLM to synthesize a concept from a cluster of claims.

    Backend: WIKI_LLM_BACKEND=mlx (set by main() for local routes) runs the
    synthesis on-device via local_llm.generate; otherwise the OpenAI-compatible
    endpoint. Falls back to mechanical synthesis when the local backend is
    unavailable."""
    # A union-find cluster can over-connect and balloon into thousands of claims
    # (a 205K-char prompt that on-device prefill chokes on). Cap the claims the
    # synthesis prompt carries: use the highest-confidence members, and note any
    # omitted count so the concept still links the full cluster downstream.
    CAP = int(os.environ.get("WIKI_SYNTH_MAX_CLAIMS", "60"))
    used = sorted(cluster, key=lambda c: {"high": 0, "medium": 1, "low": 2}.get(c.get("confidence"), 1))[:CAP]
    # #186: the claims block carries disagreement explicitly — status +
    # relations on the claim itself plus any contradicts/supersedes verdicts
    # recorded in the effects files (the judged second opinion). The prompt
    # contract renders the evolution instead of a flattened winner.
    _effects = _cluster_effects(used)
    def _line(c):
        bits = f"- [{c['stem']}] {c['statement']} (status={c['status']}, conf={c['confidence']}"
        rels = _concise_relations(c)
        if rels:
            bits += f", relations={rels}"
        eff = _effects.get(c["stem"])
        if eff:
            bits += f"; judged effects: {eff}"
        return bits + ")"
    claims_text = "\n".join(_line(c) for c in used)
    if len(cluster) > len(used):
        claims_text += f"\n(_and {len(cluster)-len(used)} more related claims, see concept claims list_)"
    prompt = SYNTH_PROMPT.replace("{claims_block}", claims_text)

    if os.environ.get("WIKI_LLM_BACKEND", "").lower() == "mlx":
        local_model = os.environ.get("WIKI_MLX_MODEL") or get_local_model()
        try:
            from local_llm import generate as local_generate
            # A concept synthesis is a compact JSON (~200-400 tokens); on-device
            # decode is ~15-20 tok/s so leaving the cap high lets the model ramble
            # to thousands of tokens, turning 129 clusters into hours. Cap it tight.
            output = local_generate(prompt, local_model, max_tokens=int(
                os.environ.get("WIKI_LOCAL_MAX_TOKENS", "450")))
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
        model = os.environ.get("WIKI_LLM_OPS_MODEL") or os.environ.get("WIKI_LLM_MODEL", cfg["ops_model"] or cfg["model"])

        client = openai.OpenAI(base_url=base_url, api_key=api_key)
        response = client.chat.completions.create(
            model=model,
            temperature=LLM_TEMPERATURE,
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


def _detect_domains(cluster, onto):
    """Domain binding from the ONTOLOGY vocabulary (was: a hardcoded keyword
    heuristic stamping alias spellings — godot-systems/agent-systems — onto
    every concept regardless of the ontology). Match order, all alias-aware:
    1. each claim's own project/stem tokens against ontology domain names +
       shared tag set (claim mentioning 'godot' → domain 'godot' if known)
    2. fallback: the shared tag set token with the strongest stem match
    3. nothing matches → NO domain field (unbound; the lint vocabulary gate
       and context both treat unbound honestly — a hardcode was worse: it
       bound every concept to a vocabulary that could be wrong)."""
    from wf_common import tokens as _tok
    spellings = _ontology_sp.all_spellings(onto)
    canon = {a: c for a, c in onto["aliases"].items()}
    canon.update({d: d for d in onto["domains"]})
    hits = set()
    for c in cluster:
        toks = _tok(str(c.get("stem", "")) + " " + str(c.get("statement", ""))[:400])
        for sp in sorted(spellings):
            if sp in toks or any(sp in t for t in toks if len(t) >= len(sp) >= 4):
                hits.add(canon.get(sp, sp))
    return sorted(h for h in hits if h in onto["domains"])[:3]


def write_concept_page(concept_slug, cluster, synthesis, domain=None):
    """Write a type:concept page. Legacy `domain` arg ignored (was a hardcoded
    'agent-systems' stamp every call site passed); ontology vocabulary rules."""
    today = date.today().isoformat()
    claim_links = "\n".join(f'  - "[[{c["stem"]}]]"' for c in cluster)

    domains = _detect_domains(cluster, _ontology_for_vocab())
    # Physical home (S1/#159, Scope→home contract): a domain-bound concept
    # lives in domains/<canonical-domain>/concepts/; unbound concepts stay in
    # the flat concepts/ dir (the lint vocabulary gate flags their domain as
    # unbound — relocation happens via the same migration as the corpus bulk).
    primary_domain = domains[0] if domains else None
    if primary_domain:
        concepts_dir = layout.domain_home(VAULT_ROOT, primary_domain, "domain_concepts_home")
    else:
        concepts_dir = layout.concepts(VAULT_ROOT)
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
title: {_concept_title_scalar(synthesis, concept_slug)}{chr(10) + "domain: [" + ", ".join(domains) + "]" if domains else ""}
claims:
{chr(10).join(f'  - "[[{c["stem"]}]]"' for c in cluster)}
created: {today}
---

# Concept: {_concept_title(synthesis, concept_slug)}

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



def _concept_title(synthesis, concept_slug):
    """Concept display title (LLM-provided or slug-derived)."""
    title = str((synthesis or {}).get("title") or concept_slug.replace("-", " ").title())
    return title


def _concept_title_scalar(synthesis, concept_slug):
    """Frontmatter-safe title scalar (#e2e finding: 'Epic: One graph...' — an
    unquoted colon broke yaml on every concept with a colon in the title)."""
    from wf_common import yaml_scalar
    return yaml_scalar(_concept_title(synthesis, concept_slug))

def synthesize_uncovered(cfg=None, threshold=0.4, min_claims=2, dry_run=False, project=None):
    """Synthesize concept pages for claims not yet covered by any concept.

    Reusable entrypoint (used by `wf export wiki` to restore the human layer from
    atoms): cluster claims by concept overlap, synthesize each cluster into a
    `concept-*.md` page via the compiler model, and return the written paths.
    Deterministic clustering; synthesis is LLM (compiler). Honors the compiler
    eval gate: refuse to synthesize when the compiler model has no recorded eval.

    `project` scopes clustering+synthesis to that project's claims (#171):
    a project-scoped export must not pay — or LLM-spend — for corpus-wide
    clusters it won't write. Clusters spanning OTHER projects (mixtures) are
    excluded by the same scoping, matching the page filter.

    Synthesis runs on the cloud compiler model (concept synthesis benefits from
    the strongest available model). Returns list of written concept paths (empty
    when gate blocked or nothing new).
    """
    from fabric_config import get_config as _gc, compiler_eval_recorded
    if cfg is None:
        cfg = _gc()

    ok, why = compiler_eval_recorded(cfg)
    if not ok:
        print(f"  SKIP concept synthesis: {why}", file=sys.stderr)
        return []

    global MIN_CLAIMS
    MIN_CLAIMS = min_claims
    # Synthesis is compiler work: run on the cloud compiler model for quality.
    os.environ["WIKI_LLM_BACKEND"] = ""
    os.environ.pop("WIKI_MLX_MODEL", None)

    claims = load_claims(project=project)
    existing = load_existing_concepts()
    covered_stems = set()
    for ec in existing:
        for link in ec["fm"].get("claims", []):
            covered_stems.add(str(link).strip("[]").split("|")[0].lower())
    available = [c for c in claims if c["stem"] not in covered_stems]
    if len(available) < MIN_CLAIMS:
        return []

    clusters = cluster_by_concept(available, threshold)
    existing_stems = {ec["stem"] for ec in existing}
    written = []
    for cluster in clusters:
        slug = generate_concept_slug(cluster, existing_stems)
        existing_stems.add(slug)
        if dry_run:
            continue
        synthesis = synthesize_concept(cluster, slug)
        path = write_concept_page(slug, cluster, synthesis)
        written.append(path)
        print(f"  concept: {path.name} ({len(cluster)} claims)", file=sys.stderr)
    return written


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Synthesize claims into concept pages")
    parser.add_argument("--dry-run", action="store_true", help="Show clusters without writing")
    parser.add_argument("--min-claims", type=int, default=2, help="Minimum claims per concept")
    parser.add_argument("--threshold", type=float, default=0.4, help="Concept-overlap threshold (higher = tighter concepts)")
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
            os.environ["WIKI_LLM_OPS_MODEL"] = _model
    else:
        # No --project: cloud compiler path (synthesis is compiler work).
        os.environ["WIKI_LLM_BACKEND"] = ""

    global MIN_CLAIMS
    MIN_CLAIMS = args.min_claims

    claims = load_claims(project=args.project)
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
        concept_path = write_concept_page(slug, cluster, synthesis)
        print(f"  Created: {concept_path.relative_to(VAULT_ROOT)}")
        print()

    if args.dry_run:
        print("[DRY RUN] No files written")


def cluster_by_concept(claims, threshold):
    """Cluster claims by concept-overlap (extracted for testability).

    #171: the O(n²) loop re-ran norm() (a regex sub) on BOTH statements per
    pair — 39M regex calls at 6k claims, minutes inside `export`. Stems are
    computed once per claim; an inverted index proposes only pairs SHARING a
    content token (identical semantics: zero-token-overlap pairs can never
    reach the threshold, so skipping them changes no cluster membership)."""
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

    stopwords = CONCEPT_NAME_FILTER

    stems = []
    inverted = defaultdict(list)  # token -> claim indices carrying it
    for i, c in enumerate(claims):
        toks = set(norm(c["statement"]).split()) - stopwords
        if not toks:
            stems.append(frozenset())
            continue
        stems.append(toks)
        for t in toks:
            inverted[t].append(i)

    for i in range(n):
        si = stems[i]
        if not si:
            continue
        # candidate pool: claims sharing at least one token with i (deduped,
        # j > i only — the union-find loop is order-irrelevant)
        seen = set()
        for t in si:
            for j in inverted[t]:
                if j > i and j not in seen:
                    seen.add(j)
        for j in seen:
            sj = stems[j]
            if not sj:
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