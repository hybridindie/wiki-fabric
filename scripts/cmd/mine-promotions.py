#!/usr/bin/env python3
# mine-promotions.py — Mine promotion candidates from experience events
#
# Usage: python3 scripts/cmd/mine-promotions.py [--min-projects N] [--output-dir DIR] [--use-embeddings] [--model MODEL] [--dry-run]

import sys
import sys as _s, pathlib as _p
_HERE = _p.Path(__file__).resolve().parent
# Explicit import bootstrap: this script's own dir (same-dir siblings)
# + scripts/lib (shared modules). No shotgun path injection.
for _dir in (_HERE, _HERE.parent / "lib"):
    if str(_dir) not in _s.path:
        _s.path.insert(0, str(_dir))
import re
try:
    import yaml
    HAVE_YAML = True
except ImportError:
    HAVE_YAML = False
import json
import hashlib
from pathlib import Path
from collections import defaultdict
from datetime import datetime
from datetime import timedelta
from wf_common import parse_frontmatter
from fabric_config import FABRIC_ROOT
from fabric_config import CORPUS_ROOT
from fabric_config import CORPUS_ROOT

try:
    from sentence_transformers import SentenceTransformer
    HAS_EMBEDDINGS = True
except ImportError:
    HAS_EMBEDDINGS = False

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    np = None
    HAS_NUMPY = False

VAULT_ROOT = CORPUS_ROOT

EXPERIENCE_DIR = VAULT_ROOT / "projects"
PROMOTIONS_DIR = VAULT_ROOT / "registry" / "promotions"
PROMOTION_QUEUE = VAULT_ROOT / "registry" / "promotion-queue.md"

MIN_PROJECTS = 2
OUTPUT_DIR = PROMOTIONS_DIR


def escape_yaml(value):
    """Escape string for safe YAML inclusion."""
    if '[' in value or ']' in value or ':' in value or '#' in value or '"' in value:
        return '"' + value.replace('"', '\\"') + '"'
    return value


def get_event_embedding(event, model=None):
    """Generate embedding for an experience event."""
    text = f"Problem: {event.get('observed_problem', '')}\nIntervention: {event.get('intervention', '')}\nOutcome: {event.get('outcomes', {})}"
    if model is None:
        # Fallback: simple hash-based pseudo-embedding
        text_hash = hashlib.md5(text.encode()).digest()
        return [float(b) / 255.0 for b in text_hash]
    return model.encode(text)


def cluster_events_semantic(events, min_projects=2, model=None, threshold=0.7):
    """Cluster experience events using semantic similarity."""
    if len(events) < 2:
        return {}
    if not HAS_NUMPY:
        return cluster_events_keyword(events, min_projects)
    
    # Generate embeddings
    embeddings = []
    valid_events = []
    for ev in events:
        try:
            emb = get_event_embedding(ev, model)
            embeddings.append(emb)
            valid_events.append(ev)
        except Exception:
            continue
    
    if len(valid_events) < 2:
        return {}
    
    # Simple clustering: greedy agglomerative with threshold
    clusters = []
    used = set()
    
    for i, ev in enumerate(valid_events):
        if i in used:
            continue
        
        cluster = [i]
        used.add(i)
        
        for j in range(i + 1, len(valid_events)):
            if j in used:
                continue
            
            # Cosine similarity
            a = np.array(embeddings[i])
            b = np.array(embeddings[j])
            if np.linalg.norm(a) > 0 and np.linalg.norm(b) > 0:
                sim = np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
                if sim >= threshold:
                    cluster.append(j)
                    used.add(j)
        
        clusters.append(cluster)
    
    # Filter by minimum independent projects
    valid_clusters = {}
    for idx, cluster_indices in enumerate(clusters):
        events_in_cluster = [valid_events[i] for i in cluster_indices]
        projects = set(ev.get("project", "") for ev in events_in_cluster)
        if len(projects) >= min_projects:
            valid_clusters[f"cluster_{idx}"] = events_in_cluster
    
    return valid_clusters


def cluster_events_keyword(events, min_projects=2, _keyword_threshold=None):
    """Fallback: keyword-based clustering with semantic expansion and Jaccard similarity."""
    if _keyword_threshold is None:
        from fabric_config import get_tuning as _gt
        _keyword_threshold = _gt(None, "mining", "keyword_threshold", 0.05)
    domain_synonyms = {
        "threading": ["concurrency", "parallel", "sync", "async", "mutex", "lock", "race", "deadlock"],
        "batching": ["batch", "composite", "bundle", "group"],
        "caching": ["cache", "memoize", "memo", "buffer"],
        "pipeline": ["pipeline", "stream", "flow", "parallel"],
        "baseline": ["baseline", "reference", "ground truth", "oracle"],
        "verification": ["verify", "validate", "check", "assert", "test"],
        "crash": ["crash", "fail", "error", "exception", "abort"],
        "single-writer": ["single-threaded", "serial", "sequential", "mutex", "lock"],
    }
    
    def expand_keywords(text):
        words = set(re.findall(r'\b[a-z]{3,}\b', text.lower()))
        expanded = set(words)
        for word in words:
            for key, syns in domain_synonyms.items():
                if key in word or word in key:
                    expanded.update(syns)
        expanded.update(words)
        return expanded
    
    # Compute expanded keyword sets for each event
    event_keywords = []
    for ev in events:
        problem = ev.get("observed_problem", "").lower()
        intervention = ev.get("intervention", "").lower()
        keywords = set()
        for text in [problem, intervention]:
            words = re.findall(r'\b[a-z]{3,}\b', text.lower())
            keywords.update(words)
        
        expanded = set()
        for word in keywords:
            expanded.add(word)
            for key, syns in domain_synonyms.items():
                if key in word or word in key:
                    expanded.update(syns)
        expanded.update(keywords)
        event_keywords.append((ev, expanded))
    
    # Cluster by Jaccard similarity of expanded keywords
    clusters = defaultdict(list)
    used = set()
    
    for i, (ev_i, kw_i) in enumerate(event_keywords):
        if i in used:
            continue
        cluster = [i]
        used.add(i)
        
        for j, (ev_j, kw_j) in enumerate(event_keywords):
            if j in used:
                continue
            # Jaccard similarity
            intersection = len(kw_i & kw_j)
            union = len(kw_i | kw_j)
            similarity = intersection / union if union > 0 else 0
            
            if similarity >= _keyword_threshold:  # tuning: mining.keyword_threshold
                cluster.append(j)
                used.add(j)
        
        if len(cluster) >= MIN_PROJECTS:
            projects = set(event_keywords[idx][0].get("project", "") for idx in cluster)
            if len(projects) >= MIN_PROJECTS:
                cluster_key = f"cluster_{hashlib.md5(str(sorted(cluster)).encode()).hexdigest()[:8]}"
                clusters[cluster_key] = [event_keywords[idx][0] for idx in cluster]
    
    return clusters


def extract_experience_events():
    """Extract all experience events from projects/*/experience-events/"""
    events = []
    for exp_file in (VAULT_ROOT / "projects").rglob("experience-events/*.md"):
        fm, body = parse_frontmatter(exp_file)
        if fm.get("type") == "experience-event":
            fm["_file"] = exp_file
            fm["_body"] = body
            events.append(fm)
    return events


def parse_frontmatter(path):
    text = path.read_text(encoding="utf-8", errors="replace")
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.DOTALL)
    if not m:
        return {}, text
    raw, body = m.group(1), m.group(2)
    if HAVE_YAML:
        try:
            fm = yaml.safe_load(raw) or {}
        except Exception:
            fm = {}
    else:
        fm = {}
        for line in raw.splitlines():
            mm = re.match(r"([\w-]+):\s*(.*)$", line)
            if mm:
                fm[mm.group(1)] = mm.group(2).strip().strip("'\"") or None
    return fm, body


def cluster_events(events, min_projects=2, use_embeddings=True, model=None, threshold=0.7):
    """Cluster experience events using semantic similarity or keyword fallback."""
    if len(events) < 2:
        return {}
    
    if use_embeddings and HAS_EMBEDDINGS:
        try:
            return cluster_events_semantic(events, min_projects, model)
        except Exception as e:
            print(f"Embedding clustering failed, falling back to keywords: {e}")
    
    return cluster_events_keyword(events, min_projects)


def cluster_events_judged(events, min_projects=2, threshold=None):
    """Judgment refinement over the keyword pass (#29 slice 3): pairs whose
    expanded-keyword Jaccard is a NEAR-MISS (0 < sim < keyword threshold) get
    a decision-model verdict — 'same recurring pattern?' — and judged-same
    pairs merge into one cluster. Judgment records probabilities; the
    deterministic keyword result is the fallback when the tier is disabled.
    threshold=None => judgment.MINING_THRESHOLD_DEFAULT (0.8, live-calibrated)."""
    from judgment import same_recurrence, judgment_route, JudgmentUnavailable
    try:
        route = judgment_route()
    except JudgmentUnavailable as e:
        print(f"Judgment tier unavailable, keeping keyword clusters: {e}")
        return cluster_events_keyword(events, min_projects)

    base = cluster_events_keyword(events, min_projects)

    def _text(ev):
        return (f"Problem: {ev.get('observed_problem', '')} | "
                f"Intervention: {ev.get('intervention', '')} | "
                f"Outcome: {ev.get('outcomes', '')}")

    # Rebuild keyword pairs that did NOT cluster together
    assigned = {}
    for ck, evs in base.items():
        for ev in evs:
            assigned[ev.get("_file")] = ck

    for i in range(len(events)):
        for j in range(i + 1, len(events)):
            ea, eb = events[i], events[j]
            if assigned.get(ea.get("_file")) == assigned.get(eb.get("_file")) and \
                    assigned.get(ea.get("_file")) is not None:
                continue
            same, p = same_recurrence(_text(ea), _text(eb), threshold=threshold)
            mark = "MERGE" if same else "keep-split"
            print(f"  judged {ea.get('project','?')}+{eb.get('project','?')}: p={p:.3f} -> {mark}")
            if same:
                base = _merge_clusters(base, ea, eb, assigned)
                assigned = {}
                for ck, evs in base.items():
                    for ev in evs:
                        assigned[ev.get("_file")] = ck
    print(f"Judgment route: {route} | merge threshold: {threshold}")

    # ---- Judged SPLIT pass (#41): keyword clusters can be over-merged (the
    # 0.05 keyword threshold is deliberately loose for recall). For each
    # cluster with >1 event, judge each member against the cluster
    # representative (the event with the most keyword overlap to the rest);
    # members judged DIFFERENT are demoted back to singletons. Merge-only
    # asymmetry fixed: refinement is now symmetrical, both recorded.
    base = _split_incoherent_clusters(base, _text, threshold, route)
    return base


def _cluster_representative(evs, keyword_sets=None):
    """The member most similar to the rest of its cluster (highest mean
    pairwise keyword Jaccard); falls back to the first event."""
    if len(evs) <= 2:
        return evs[0]
    sets = [set(re.findall(r'\b[a-z]{3,}\b',
                           (ev.get("observed_problem", "") + " " + ev.get("intervention", "")).lower()))
            for ev in evs]
    best, best_score = evs[0], -1.0
    for i in range(len(evs)):
        sims = []
        for j in range(len(evs)):
            if i == j:
                continue
            u = sets[i] | sets[j]
            sims.append(len(sets[i] & sets[j]) / len(u) if len(u) else 0.0)
        mean = sum(sims) / len(sims) if sims else 0.0
        if mean > best_score:
            best, best_score = evs[i], mean
    return best


def _split_incoherent_clusters(base, _text, threshold, route):
    """Demote members judged DIFFERENT from their cluster's representative.
    Singletons left behind are simply unassigned (available for later merges
    but not part of any dossier)."""
    from judgment import same_recurrence
    for ck in list(base.keys()):
        evs = base[ck]
        if len(evs) <= 1:
            continue
        rep = _cluster_representative(evs)
        keep, demote = [], []
        for ev in evs:
            if ev is rep:
                keep.append(ev)
                continue
            same, p = same_recurrence(_text(rep), _text(ev), threshold=threshold)
            (keep if same else demote).append(ev)
            print(f"  judged split {ck[:18]}: rep+{ev.get('project','?')} p={p:.3f} -> "
                  f"{'keep' if same else 'DEMOTE'}")
        if demote:
            if keep:
                base[ck] = keep
            else:
                del base[ck]
            print(f"  split {ck[:18]}: {len(keep)} kept, {len(demote)} demoted")
    return base


def _merge_clusters(base, ea, eb, assigned):
    """Merge the clusters holding ea and eb. When both are unassigned singletons
    (the keyword pass dropped them), a judged-same pair *forms* a new cluster —
    the min-projects filter is re-applied afterward by the caller."""
    ca, cb = assigned.get(ea.get("_file")), assigned.get(eb.get("_file"))
    if not ca and not cb:
        base[f"cluster_judged_{hashlib.md5((ea.get('_file','') + eb.get('_file','')).encode()).hexdigest()[:8]}"] = [ea, eb]
        return base
    if not cb:
        # ea's cluster absorbs the unassigned eb
        base[ca].append(eb)
        return base
    if not ca:
        base[cb].append(ea)
        return base
    if ca == cb:
        return base
    base[ca].extend(base[cb])
    del base[cb]
    return base


def escape_yaml(value):
    """Escape string for safe YAML inclusion."""
    if '[' in value or ']' in value or ':' in value or '#' in value or '"' in value:
        return '"' + value.replace('"', '\\"') + '"'
    return value


def _mine_actor(model=None):
    """Actor for dossier generation: agent/<owner>/<dossier-model>."""
    from fabric_config import get_config, actor
    return actor(get_config(), "agent", model=model)


def generate_dossier(cluster_key, events, local_model=None):
    """Generate a promotion dossier markdown. local_model set => the cluster
    routed local; the actor records the on-device model actually in use."""
    projects = set(ev.get("project", "") for ev in events)
    domains = set()
    for ev in events:
        domains.update(ev.get("domain", []))
    
    outcomes = []
    for ev in events:
        outcomes_str = str(ev.get("outcomes", {}))
        if "PASS" in outcomes_str or "positive" in str(ev.get("outcomes", {})).lower():
            outcomes.append("positive")
        elif "FAIL" in outcomes_str or "negative" in str(ev.get("outcomes", {})).lower():
            outcomes.append("negative")
    
    has_positive = "positive" in outcomes
    has_negative = "negative" in outcomes
    
    if has_positive and has_negative:
        pattern_type = "mixed"
    elif has_positive:
        pattern_type = "success"
    elif has_negative:
        pattern_type = "failure"
    else:
        pattern_type = "neutral"
    
    pattern_slug = f"pattern-{cluster_key}"
    anti_slug = f"anti-pattern-{cluster_key}"
    
    _at = datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')
    dossier = f"""---
type: promotion-dossier
id: promotion-{cluster_key}
title: "Promotion proposal: {cluster_key.replace('_', '-')}"
description: "Cross-project promotion dossier mined from independent projects"
generated: {{ by: "{_mine_actor(model=local_model)}", at: "{_at}" }}
status: pending-review
created: {datetime.now().strftime('%Y-%m-%d')}
pattern_ref: "[[pattern-{cluster_key}]]"
anti_pattern_ref: "[[anti-pattern-{cluster_key}]]"
---

# Promotion Dossier: {cluster_key.replace('_', '-').title()}

## Candidate

[[pattern-{cluster_key}]] — Pattern extracted from {len(set(ev.get('project', '') for ev in events))} independent projects.

## Supporting experiences

"""
    
    for ev in events:
        project = ev.get("project", "unknown")
        outcome = "success" if "positive" in str(ev.get("outcomes", {})).lower() else "failure" if "negative" in str(ev.get("outcomes", {})).lower() else "neutral"
        stem = ev.get("_file")
        ref = f"[[{Path(stem).stem if stem else 'ee-unknown'}]]"
        dossier += f"- {ref} — the **{outcome}** mode ({ev.get('observed_problem', '')[:100]}...)\n"
    
    from fabric_config import get_config as _gc
    _owner = (_gc() or {}).get("owner", "you")
    dossier += f"""

The {len(set(ev.get('project', '') for ev in events))} projects are independent (different domains/repos) but share the **same underlying invariant**: {{TODO: describe invariant}}.

## Shared conditions

- {{TODO: list shared conditions}}

## Confounding factors

1. {{TODO: list confounding factors}}

## Proposed boundary (applicability)

**Include**:
- {{TODO: list includes}}

**Exclude**:
- {{TODO: list excludes}}

## Proposed asset changes

1. Create global pattern: `global/patterns/pattern-{cluster_key}.md`
2. Create global anti-pattern: `global/anti-patterns/anti-pattern-{cluster_key}.md`
3. Create skill: `global/skills/{cluster_key}.md`
4. Create template: `global/templates/experiment-{cluster_key}.md`

## Required review

**Human owner: {_owner}.** Promote on next review. Checklist (from [[promotion-queue]]):
- [ ] Independence: do the supporting experience-events share a lineage? (No → OK.)
- [ ] Evidence: are claims in `source_refs` actually entailed by cited locators?
- [ ] Applicability: are `includes`/`excludes` conditions correct and non-vacuous?
- [ ] Counterexamples: listed and acknowledged?
- [ ] Tradeoff: cost/benefit stated?
- [ ] Asset changes: which `global/` entries does promotion create/update?
- [ ] Owner: user — user. Promote only when all pass.

## Promotion decision

```
Status:        pending-review
Reviewed by:   user
Review date:   _
Maturity:      1 (observed) → _ (recommended / standard / deprecated)
Notes:         Auto-generated from {len(set(ev.get('project', '') for ev in events))} project experience events. Requires human review.
```

"""
    return dossier


def generate_pattern_file(cluster_key, events):
    """Generate a pattern file template."""
    projects = list(set(ev.get("project", "") for ev in events))
    
    def escape_yaml(value):
        """Escape string for safe YAML inclusion."""
        if '[' in value or ']' in value or ':' in value or '#' in value or '"' in value:
            return '"' + value.replace('"', '\\"') + '"'
        return value
    
    # Build the pattern file content using string concatenation to avoid f-string indentation issues
    lines = []
    lines.append("---")
    lines.append(f"type: pattern")
    lines.append(f"id: pattern-{cluster_key}")
    lines.append(f"title: {cluster_key.replace('_', '-').title()}")
    lines.append("scope: global")
    lines.append("domain: [agent-systems]")
    lines.append("status: candidate")
    lines.append("maturity: 1")
    lines.append("maturity_evidence:")
    
    for ev in events:
        project = ev.get("project", "unknown")
        kind = "success-pattern" if "positive" in str(ev.get("outcomes", {})).lower() else "failure-mode"
        lines.append(f"  - project: {project}")
        lines.append(f"    kind: {kind}")
        stem = ev.get("_file")
        ref = f"[[{Path(stem).stem if stem else 'ee-unknown'}]]"
        lines.append(f"    ref: {escape_yaml(ref)}")
    
    lines.append("applicability:")
    lines.append("   includes:")
    lines.append('       - "TODO: describe when this pattern applies"')
    lines.append('       - "A deterministic baseline exists to compare the mutated state against."')
    lines.append('       - "The agent has write tool access to the system of record."')
    lines.append("   excludes:")
    lines.append('       - "Purely read-only pipelines (nothing to gate or verify)."')
    lines.append('       - "Open-ended creative/authoring tasks with no baseline."')
    lines.append('problem: "An agent driving a single-writer system can silently corrupt state by racing, skipping a verification step, or treating \'happy path passes\' as \'all passes\'. For example, a stress test that passes at rest but fails under concurrent load is the concrete instance."')
    lines.append("forces:")
    lines.append('    - "Iteration is desirable but unsafe mutations are worse."')
    lines.append('    - "Human review bandwidth is limited."')
    lines.append('    - "A system that passes at rest may still corrupt under realistic concurrency or load."')
    lines.append('    - "A deterministic baseline is often the cheapest completion verifier that exists."')
    lines.append("solution:")
    lines.append('    - "Treat the system\'s mutator as the single writer: serialize all writes, parallelize only reads."')
    lines.append('    - "Batch ordered writes (one tool call, many sub-commands, each with its own transactional semantic)."')
    lines.append('    - "Cache reads per-session, invalidate on write; reads only, never mutations."')
    lines.append('    - "For each consequential write, run a deterministic baseline (sync reference, snapshot comparison, contract test) and verify parity before declaring completion."')
    lines.append('    - "Stress the verifier under load: a baseline that passes at rest may fail under concurrency If stress fails, fix the writer or the verifier."')
    lines.append("consequences:")
    lines.append("  benefits:")
    lines.append('    - "Detect silent corruption under stress rather than by production failure."')
    lines.append('    - "Completion criteria are unambiguous and mechanically checkable."')
    lines.append('    - "Bounded blast radius — a failed verification aborts the change set."')
    lines.append("  costs:")
    lines.append('    - "Baseline maintenance cost."')
    lines.append('    - "Verification adds latency to every consequential change."')
    lines.append("evidence:")
    lines.append('    - ref: <experience-event-slug>')
    lines.append('      kind: direct-experience')
    lines.append('      outcome: positive')
    lines.append('    - ref: <experience-event-slug>')
    lines.append('      kind: direct-experience')
    lines.append('      outcome: negative')
    lines.append("counterexamples: []")
    lines.append("related:")
    lines.append(f'    - {escape_yaml("[[anti-pattern-unverified-parallel-writes]]")}')
    lines.append(f'    - {escape_yaml("[[concept-single-writer-serialization]]")}')
    lines.append(f"review_after: {(datetime.now().replace(month=datetime.now().month+3)).strftime('%Y-%m-%d') if datetime.now().month <= 9 else (datetime.now().replace(year=datetime.now().year+1, month=datetime.now().month-9)).strftime('%Y-%m-%d')}")
    lines.append("tags: [agent, threading, serialization, verifier, parity, single-writer]")
    lines.append("---")
    lines.append("")
    lines.append(f"# Pattern: {cluster_key.replace('_', '-').title()}")
    lines.append("")
    lines.append("> **Status: candidate, maturity 1** — auto-generated from experience events.")
    lines.append("")
    lines.append("## Pattern")
    lines.append("")
    lines.append("When an agent is driving a system that is **naturally a single writer**")
    lines.append("(editor, actor, queue, engine):")
    lines.append("- serialize all writes; parallelize only the reads;")
    lines.append("- batch the writes with transactional semantics per sub-command;")
    lines.append("- verify consequential changes by a **deterministic baseline pairing**;")
    lines.append("- stress that verifier under load — a baseline that passes at rest may fail under")
    lines.append("   concurrency.")
    lines.append("")
    lines.append("## Why this is maturity 1")
    lines.append("")
    lines.append("One project observed the failure mode under stress; another observed the success pattern.")
    lines.append("")
    lines.append("## Applicability")
    lines.append("")
    lines.append("**Applies** when:")
    lines.append("- the agent has write access to a single-writer system, AND")
    lines.append("- the system has a **deterministic reference** the mutated state can be paired against, AND")
    lines.append("    the task involves multi-step mutation of the record.")
    lines.append("")
    lines.append("**Does not apply** to:")
    lines.append("- purely read-only pipelines;")
    lines.append("- open-ended creative/authoring tasks with no baseline.")
    lines.append("")
    lines.append("## Consequences")
    lines.append("")
    lines.append("- **Benefit**: silent corruption is caught before production; completion is")
    lines.append("   unambiguous; bounded blast radius when verification fails.")
    lines.append("- **Cost**: baseline maintenance cost.")
    lines.append("   - \"Verification adds latency on consequential writes.\"")
    lines.append("")
    lines.append("## Counterexamples")
    lines.append("")
    lines.append("None yet. Watch for:")
    lines.append("- Systems whose baseline is **not reproducible** (e.g. depends on wall-clock")
    lines.append("   timestamps, OS-specific state).")
    lines.append("- Multi-writer architectures where the \"single writer\" assumption is false by")
    lines.append("   design.")
    lines.append("- Systems where a baseline is **expensive** (e.g. full game simulation) — then")
    lines.append("   the verifier must be **sampled**, not run on every write.")
    lines.append("")
    lines.append("## Review")
    lines.append("")
    lines.append(f"After {(datetime.now().replace(month=datetime.now().month+3)).strftime('%Y-%m-%d') if datetime.now().month <= 9 else (datetime.now().replace(year=datetime.now().year+1, month=datetime.now().month-9)).strftime('%Y-%m-%d')}. Reassess if a third independent project confirms or refutes the pattern.")
    
    return "\n".join(lines)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Mine promotion candidates from experience events")
    parser.add_argument("--min-projects", type=int, default=2, help="Minimum independent projects for a cluster")
    parser.add_argument("--output-dir", default=str(PROMOTIONS_DIR), help="Output directory for dossiers")
    parser.add_argument("--use-embeddings", action="store_true", help="Use semantic embeddings for clustering")
    parser.add_argument("--judge", action="store_true",
                        help="Refine near-miss cluster pairs with the judgment tier (integrations.judgment)")
    parser.add_argument("--model", default="all-MiniLM-L6-v2", help="Embedding model (sentence-transformers)")
    parser.add_argument("--dry-run", action="store_true", help="Don't write files, just show what would be done")
    args = parser.parse_args()
    
    global MIN_PROJECTS, OUTPUT_DIR
    MIN_PROJECTS = args.min_projects or get_tuning(config, 'mining', 'min_projects', 2)
    OUTPUT_DIR = Path(args.output_dir)
    
    print(f"Mining promotions (min projects: {MIN_PROJECTS}, embeddings: {args.use_embeddings})...")
    
    events = extract_experience_events()
    print(f"Found {len(events)} experience events")

    if args.judge:
        clusters = cluster_events_judged(events, MIN_PROJECTS)
    else:
        clusters = cluster_events(events, MIN_PROJECTS, use_embeddings=args.use_embeddings)
    print(f"Found {len(clusters)} clusters with >= {MIN_PROJECTS} projects")
    
    for cluster_key, events in clusters.items():
        print(f"\nCluster: {cluster_key} ({len(events)} events, {len(set(ev.get('project', '') for ev in events))} projects)")
        for ev in events:
            print(f"  - {ev.get('project', 'unknown')}: {ev.get('title', 'untitled')[:60]}")
    
    if args.dry_run:
        print("\n[DRY RUN] No files written")
        return
    
    # Compiler-eval gate (policy: model swaps are compiler changes). Dry-run exempt.
    from fabric_config import (get_config, compiler_eval_recorded,
                               get_stage_route, is_local_route, ensure_local_model)
    _cfg = get_config()
    ok, why = compiler_eval_recorded(_cfg)
    if not ok:
        print(f"BLOCKED: {why}")
        print("Policy: dossier generation requires a recorded compiler eval for the compiler model.")
        print("Run: python3 scripts/eval/eval-stability.py --models <compiler-model> --record")
        sys.exit(2)

    # Dossier stage routing: when every project in a cluster routes its dossier
    # stage local, generate on-device (experience events may be sensitive).
    # Mixed clusters (any cloud) stay on the compiler model — a dossier's
    # evidence pool is only as private as its least-private input.
    def _route_for_cluster(cluster_events):
        projects = sorted({ev.get("project", "") for ev in cluster_events})
        for p in projects:
            if not is_local_route(_cfg, p, "dossier"):
                return None, None
        return "local", get_stage_route(_cfg, projects[0], "dossier") if projects else None

    _local_model = None
    if clusters:
        all_events = [ev for evs in clusters.values() for ev in evs]
        _local, _m = _route_for_cluster(all_events)
        # Pre-flight: front-load the download prompt before generation starts.
        if _local == "local":
            ensure_local_model(_m, config=_cfg)
            _local_model = _m

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for cluster_key, events in clusters.items():
        # Generate dossier (local when every contributing project routes local)
        route, model_for_cluster = _route_for_cluster(events)
        if route == "local":
            _actor_model = model_for_cluster
        else:
            _actor_model = _cfg.get("llm", {}).get("compiler_model") or _cfg.get("llm", {}).get("model") or "unknown"
        dossier = generate_dossier(cluster_key, events, model_for_cluster if route == "local" else None)
        dossier_path = Path(args.output_dir) / f"promotion-{cluster_key}.md"
        dossier_path.write_text(dossier)
        print(f"Created dossier: {dossier_path} (route: {route or 'cloud'})")
        
        # Generate pattern file
        pattern_content = generate_pattern_file(cluster_key, events)
        pattern_path = VAULT_ROOT / "patterns" / f"pattern-{cluster_key}.md"
        pattern_path.parent.mkdir(parents=True, exist_ok=True)
        pattern_path.write_text(pattern_content)
        print(f"Created pattern: {pattern_path}")
        
        print(f"  → Created promotion dossier and pattern for '{cluster_key}'")

    # Self-describing next step: graphify enrichment (when active) belongs in
    # the command flow, not just skill prose.
    if _local_model is None or True:
        from fabric_config import is_integration_active
        if is_integration_active(_cfg, "graphify"):
            print("\nNext (graphify active): python3 scripts/harness/graphify-bridge.py --enrich "
                  "— attaches code provenance to code-adjacent dossiers before review.")


if __name__ == "__main__":
    main()