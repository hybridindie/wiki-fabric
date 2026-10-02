#!/usr/bin/env python3
# context.py — Compile a task-specific context manifest from the corpus (0 tokens)
#
# Deterministic context assembly per AGENTS.md's scope model:
#   Agent Context = Global Policies + Domain Knowledge + Project Constraints + Task Evidence
#
# Selection is explainable by construction: every included (and excluded) artifact
# carries a reason. No LLM, no scoring magic — priority order, path overlap, tag
# match, text match, and status/staleness filters.
#
# Usage:
#   wf context --task "Add token rotation to the OAuth service" --paths services/auth
#   wf context --task "..." --project my-project          # pin a project namespace
#   wf context --task "..." --paths a/b --paths c/d       # multiple code paths
#   wf context --task "..." --format json                 # machine manifest
#   wf context --task "..." --write-receipt               # persist delivery receipt
#
# Receipts (--write-receipt): persist the manifest as an auditable artifact —
#   schema wiki-fabric/receipt-v1, id derived from the manifest payload (same
#   corpus + task => same id; re-running overwrites in place, no dupes).
#   Partitioned by namespace: projects/<p>/receipts/ when pinned, else
#   registry/receipts/. The receipt path goes to stderr; stdout stays the
#   manifest, byte-identical with or without the flag. 0 tokens.
#
# Priority order (highest first): project decisions/claims → domain patterns →
# global patterns/policies → concepts. Superseded artifacts are excluded;
# REVIEW-AFTER-stale artifacts are demoted with a warning.

import sys
import sys as _s, pathlib as _p
_HERE = _p.Path(__file__).resolve().parent
# Explicit import bootstrap: this script's own dir (same-dir siblings)
# + scripts/lib (shared modules). No shotgun path injection.
for _dir in (_HERE, _HERE.parent / "lib"):
    if str(_dir) not in _s.path:
        _s.path.insert(0, str(_dir))
import re
import json
import hashlib
import argparse
from pathlib import Path
from datetime import date

try:
    import yaml
    HAVE_YAML = True
except ImportError:
    HAVE_YAML = False

from fabric_config import FABRIC_ROOT
from wf_common import tokens, RETRIEVAL
import ontology as _ontology_mod
from fabric_config import CORPUS_ROOT, VAULT_ROOT
from fabric_config import get_config, get_ignores, is_ignored, get_tuning
from wf_common import parse_frontmatter

import layout


# corpus walk exclusions are shared (wf_common.SKIP_PARTS/corpus_walk, #155-C)


def load_corpus():
    """Load all catalogable corpus pages with derived scope."""
    from wf_common import corpus_walk
    pages = []
    for p, parts, rel in corpus_walk(VAULT_ROOT):
        posix = rel.as_posix()
        if "raw" in parts:
            continue
        fm, body = parse_frontmatter(p)
        scope = fm.get("scope") or (
            "domain" if posix.startswith("domains/")
            else "project" if posix.startswith("projects/")
            else "global"
        )
        pages.append({
            "path": p,
            "rel": rel,
            "posix": posix,
            "stem": rel.stem.lower(),
            "fm": fm or {},
            "body": body,
            "type": (fm or {}).get("type", ""),
            "scope": scope,
        })
    return pages




def is_stale(fm, today):
    """review_after in the past → stale. Returns days overdue or 0."""
    ra = fm.get("review_after")
    if not ra:
        return 0
    import datetime as _dt
    try:
        if isinstance(ra, _dt.date):
            review = ra
        else:
            review = _dt.date.fromisoformat(str(ra).strip()[:10])
        overdue = (today - review).days
        return overdue if overdue > 0 else 0
    except (ValueError, TypeError):
        return 0


def _load_policy_profile(name="default-coding-agent"):
    """Load a compilation policy profile (policy-profile-v1). Returns None
    when absent or invalid — select_context falls back to built-ins
    (byte-identical shipped behavior). Profiles are versioned artifacts;
    behavior evals validate any profile before it can ship (#66)."""
    from pathlib import Path as _P
    p = _HERE.parent.parent / "system" / "policy-profiles" / f"{name}.yaml"
    try:
        import yaml as _yaml
        d = _yaml.safe_load(p.read_text())
        if d.get("schema") != "wiki-fabric/policy-profile-v1":
            return None
        return d
    except Exception:
        return None


args_judge_borderline = False  # --judge-borderline in main() (#29 item 4)


def _page_domains(pg):
    """The page's declared domain(s): `domain: [a, b]` (list/str) or null.
    Declaration, not path — pages under domains/ derive scope by path upstream."""
    d = pg["fm"].get("domain") or ()
    if isinstance(d, str):
        return {d.strip().strip("[]").split(",")[0].strip()}
    if isinstance(d, list):
        return {str(x).strip() for x in d if str(x).strip()}
    return set()


def _ontology_domains(pages):
    """Thin shim over the shared ontology parser (scripts/lib/ontology.py —
    one parse dialect every consumer imports). Finds domains/ontology.md in
    the page set; returns matchable spellings; alias map rides on the fn for
    _page_domain_canonical."""
    for pg in pages:
        if pg["posix"] == "domains/ontology.md":
            onto = _ontology_mod.parse(pg["body"])
            _ontology_domains.aliases = onto["aliases"]
            return _ontology_mod.all_spellings(onto)
    _ontology_domains.aliases = {}
    return set()


def _page_domain_canonical(pg, domain_names):
    """The page's declared domains → canonical names through the shared
    resolver. A declaration naming an unknown/aliasless domain binds to
    nothing (the vocabulary gate stays honest)."""
    alias_map = getattr(_ontology_domains, "aliases", {})
    onto = {"aliases": alias_map, "domains": domain_names - set(alias_map.keys())}
    return _ontology_mod.canonicalize(_page_domains(pg), onto)


def _overlay_domains(project):
    """The pinned project's preferred domains (overlay `domains:` — #158 S5:
    bootstrap writes it; THIS is the read that makes it load-bearing).
    Returns canonical spellings through the ontology when the corpus has one.
    The overlay lives in the PROJECT repo (discovery: get_discovered_repos);
    the corpus projects/<slug>/ tree carries no copy."""
    if not project:
        return set()
    from wf_common import project_slug
    try:
        from fabric_config import get_discovered_repos, get_repo_config
        config = get_config()
        canonical = project_slug(project)
        cfg = get_repo_config(config, canonical) or {}
        overlay_path = cfg.get("overlay_path") or ""
        candidates = []
        if overlay_path:
            candidates.append(Path(overlay_path))
        candidates.append(layout.projects(VAULT_ROOT) / canonical / ".wiki-overlay.md")
    except Exception:
        candidates = [layout.projects(VAULT_ROOT) / project / ".wiki-overlay.md"]
    fm, _ = (None, None)
    for cand in candidates:
        if cand and Path(cand).exists():
            fm, _ = parse_frontmatter(Path(cand))
            break
    if not fm:
        return set()
    d = fm.get("domains") or ()
    if isinstance(d, str):
        raw = {d.strip()}
    else:
        raw = {str(x).strip() for x in (d or ()) if str(x).strip()}
    if not raw:
        return set()
    # fold through the ontology vocabulary (canonical names + aliases)
    onto = {"aliases": getattr(_ontology_domains, "aliases", {}),
            "domains": _ontology_domains(_load_pages_for_vocab())}
    return _ontology_mod.canonicalize(raw, onto) or raw


_OV_PAGES_CACHE = None


def _load_pages_for_vocab():
    """Minimal page list for ontology resolution (the same walk load_corpus
    does, trimmed to domains/). Cache once per process."""
    global _OV_PAGES_CACHE
    if _OV_PAGES_CACHE is None:
        pages = []
        from wf_common import corpus_walk
        for p, parts, rel in corpus_walk(VAULT_ROOT):
            posix = rel.as_posix()
            if posix.endswith("domains/ontology.md"):
                pages.append({"posix": posix, "body": p.read_text(encoding="utf-8", errors="replace")})
                break
        _OV_PAGES_CACHE = pages
    return _OV_PAGES_CACHE


def select_context(pages, task, paths, project, today, max_items=20):
    """Deterministic selection: project > domain > global, each with a reason.

    Returns (selected, excluded):
      selected: [{page fields..., reason, priority}]
      excluded: [{stem, path, reason}]
    """
    task_toks = tokens(task)
    path_list = [p.strip().strip("/").lower() for p in paths if p.strip()]
    domain_names = _ontology_domains(pages)
    # #158 S5: the project overlay's domains: — a project-declared preference
    # binding. Global pages bound to a PREFERRED domain ride P2 (the domain
    # tier) instead of P3, with the reason saying why (deterministic; 0 tokens).
    preferred = _overlay_domains(project)
    selected, excluded = [], []

    def body_tokens(page):
        # Body tokens (capped for speed) — used for tag/text matching
        return tokens(page["body"][:2000])

    # ---- Exclusion pass (cheap status/staleness filters) ----
    candidates = []
    for pg in pages:
        t = pg["type"]
        fm = pg["fm"]
        status = str(fm.get("status") or "").lower()

        if t == "claim":
            # claims normally ride along via concepts/patterns that reference them;
            # but strongly task-matching claims are direct task evidence — keep as
            # candidates (tier P1-project evidence).
            candidates.append((pg, 0))
            continue
        if t not in ("pattern", "anti-pattern", "skill", "concept", "decision", "experience-event", "question", "commitment"):
            excluded.append({"stem": pg["stem"], "path": pg["posix"],
                             "reason": f"not a context artifact (type: {t or 'unknown'})"})
            continue
        if status == "superseded":
            excluded.append({"stem": pg["stem"], "path": pg["posix"], "reason": "superseded"})
            continue
        if status == "expired":
            # #160 S2: upstream vanished (raw deleted) — the record is a
            # tombstone with provenance, never retrieval input
            excluded.append({"stem": pg["stem"], "path": pg["posix"], "reason": "expired (upstream gone)"})
            continue
        if status == "deprecated":
            excluded.append({"stem": pg["stem"], "path": pg["posix"], "reason": "deprecated"})
            continue
        if t == "commitment" and status in ("done", "cancelled"):
            # completed/cancelled obligations no longer bind future work
            excluded.append({"stem": pg["stem"], "path": pg["posix"],
                             "reason": f"commitment {status}"})
            continue

        overdue = is_stale(fm, today)
        if overdue and t in ("pattern", "anti-pattern", "skill"):
            excluded.append({"stem": pg["stem"], "path": pg["posix"],
                             "reason": f"stale: review_after overdue {overdue} days — review before relying on it"})
            continue

        candidates.append((pg, overdue))

    # ---- Priority tiers ----
    # v1 policy profile (system/policy-profiles/default-coding-agent.yaml):
    # the tier→type mapping is data. A profile that fails to load/parses
    # falls back to these built-ins — byte-identical behavior.
    tiers = [
        ("P1-project", ("decision", "experience-event")),
        ("P2-domain", ("pattern", "anti-pattern", "skill", "question")),
        ("P3-global", ("pattern", "anti-pattern", "skill", "concept")),
    ]
    tier_order = {"P1-project": 0, "P2-domain": 1, "P3-global": 2}
    profile = _load_policy_profile()
    if profile:
        tiers = [(t, tuple(types)) for t, types in profile["tiers"].items()]
        tier_order = {t: i for i, t in enumerate(profile["tier_order"])}

    scored = []
    for pg, overdue in candidates:
        scope = pg["scope"]
        fm = pg["fm"]
        reason = None
        priority = None

        if pg["type"] == "commitment":
            # Prospective memory: an open obligation surfaces when its trigger
            # plausibly matches the task (trigger + body tokens vs task tokens).
            # Commitments are project-scoped by nature; a pending obligation
            # binds the current task like a decision (P1).
            trig_toks = tokens(str(fm.get("trigger") or ""))
            toks = task_toks & (trig_toks | body_tokens(pg) | tokens(pg["stem"]))
            if len(toks) >= 1 and any(len(t) >= 4 for t in toks):
                reason = f"prospective match: {', '.join(sorted(toks)[:3])}"
                priority = "P1-project"
        elif scope == "project":
            # Match: project pinned, or task/body text overlap, or path overlap with namespace
            if project and project.lower() in pg["posix"]:
                reason = f"project match: {project}"
                priority = "P1-project"
            else:
                # text overlap with task
                overlap = task_toks & body_tokens(pg)
                if len(overlap) >= 2:
                    reason = f"task text match: {', '.join(sorted(overlap)[:4])}"
                    priority = "P1-project"
        elif scope == "global" and pg["type"] == "claim":
            # direct task evidence: a claim whose statement matches the task.
            # Stopword guard: "the, tool" is not evidence of relevance —
            # require at least one CONTENT token (>=5 chars) in the overlap
            # (#e2e finding: every claim listed on generic tasks otherwise).
            overlap = task_toks & body_tokens(pg)
            _content = [t for t in overlap if len(t) >= 5]
            if len(overlap) >= 2 and _content:
                reason = f"task evidence (claim): {', '.join(sorted(_content)[:4])}"
                priority = "P1-project"
        elif scope == "domain":
            toks = task_toks & (body_tokens(pg) | tokens(pg["stem"]))
            if len(toks) >= 1 and any(len(t) >= 4 for t in toks):
                reason = f"domain match: {', '.join(sorted(toks)[:3])}"
                priority = "P2-domain"
        elif scope == "global" and (_page_domain_canonical(pg, domain_names)
                                    or pg["type"] == "ontology"):
            # DOMAIN-BOUND global page: a concept/pattern whose `domain:` field
            # names an ontology-known domain (or the ontology itself) is a
            # domain-tier artifact by declaration — the ontology is the
            # vocabulary, the field is the binding. Pages merely STORED in
            # concepts/ are global (path-scope); the declaration is what
            # promotes them into P2. This closes the bubble-up gap: all 34
            # concepts carried domain: but scope-derivation is path-only.
            toks = task_toks & (body_tokens(pg) | tokens(pg["stem"]))
            if len(toks) >= 1 and any(len(t) >= 4 for t in toks):
                bound = _page_domain_canonical(pg, domain_names)
                if bound & preferred:
                    # project-overlay domain preference (#158 S5): the bound
                    # domain is one the project declared — P2 with the
                    # binding named (project > domain > global honored)
                    reason = (f"project domain preference: {', '.join(sorted(bound & preferred))} "
                              f"(overlay domains:) — match: {', '.join(sorted(toks)[:3])}")
                    priority = "P2-domain"
                else:
                    reason = f"domain match: {', '.join(sorted(toks)[:3])}"
                    priority = "P2-domain"
        else:  # global
            # Policies/patterns apply broadly: include the significant ones
            # that textually relate. Types derive from the P3 TIER LIST (single
            # truth — the hardcoded ('pattern','anti-pattern','skill') tuple
            # omitted 'concept', which the tier list declares, so every concept
            # silently never scored: no reason, no exclusion record).
            status = str(fm.get("status") or "").lower()
            p3_types = next((set(types) for t, types in tiers if t.endswith("global")), set())
            if pg["type"] in p3_types and status in ("", "recommended", "standard", "candidate", "proposed", "supported"):
                toks = task_toks & (body_tokens(pg) | tokens(pg["stem"]))
                if len(toks) >= 1 and any(len(t) >= 4 for t in toks):
                    reason = f"global match ({pg['type']}): {', '.join(sorted(toks)[:3])}"
                    priority = "P3-global"

        if priority:
            # Path relevance boosts within-tier ordering
            path_hit = any(pp and pp in pg["posix"] for pp in path_list) if path_list else False
            scored.append({"pg": pg, "reason": reason, "priority": priority,
                           "stale": overdue, "path_hit": path_hit})

    # Order: priority tier → path hit → staleness (fresh first) → stem
    scored.sort(key=lambda s: (tier_order.get(s["priority"], 9), not s["path_hit"], -s["stale"], s["pg"]["stem"]))

    # Precedence-preserving cap (#159 S1): the plain scored[:max_items] cut let
    # a large P1 claim flood hide the domain tier entirely (P2 is the OVERRIDE
    # tier — precedence language says it outranks global policies; a cap that
    # never shows it is a lie under crowd). Reserve: P1 keeps its headroom but
    # P2/P3 get guaranteed slots when they scored (floor(tier share), min 2 for
    # P2 when P1 would take everything).
    def _tier_cut():
        by_tier = {}
        for s in scored:
            by_tier.setdefault(s["priority"], []).append(s)
        p2, p3 = by_tier.get("P2-domain") or [], by_tier.get("P3-global") or []
        p1 = by_tier.get("P1-project") or []
        # no conflict → old behavior byte-identical
        if not p2 and not p3:
            return scored[:max_items]
        # absent tiers release their reservation to the present ones; the
        # fills below also top up from lower tiers when an upper tier has
        # fewer members than its share
        reserve2 = max(2, max_items // 5) if p2 else 0
        reserve3 = max(1, max_items // 10) if p3 else 0
        p2_share = min(len(p2), reserve2)
        p3_share = min(len(p3), reserve3)
        p1_share = min(len(p1), max_items - p2_share - p3_share)
        # top-up pass: unused reservations flow down (P1 flood) / up (P2/P3)
        used = p1_share + p2_share + p3_share
        spare = max_items - used
        if spare > 0:
            rest1 = p1[p1_share:p1_share + spare]; p1_share += len(rest1)
            spare -= len(rest1)
            if spare > 0:
                rest2 = p2[p2_share:p2_share + spare]; p2_share += len(rest2)
                spare -= len(rest2)
            if spare > 0:
                rest3 = p3[p3_share:p3_share + spare]; p3_share += len(rest3)
        out = p1[:p1_share] + p2[:p2_share] + p3[:p3_share]
        demoted = [s for s in scored if s not in out]
        out.sort(key=lambda s: (tier_order.get(s["priority"], 9), not s["path_hit"],
                                -s["stale"], s["pg"]["stem"]))
        for s in demoted:
            excluded.append({"stem": s["pg"]["stem"], "path": s["pg"]["posix"],
                             "reason": f"beyond --max {max_items} (tier-shared cut)"})
        return out

    for s in _tier_cut():
        pg = s["pg"]
        item = {
            "id": str(pg["fm"].get("id") or pg["stem"]),
            "stem": pg["stem"],
            "path": pg["posix"],
            "type": pg["type"],
            "scope": pg["scope"],
            "reason": s["reason"],
            "priority": s["priority"],
        }
        item["trust_tier"] = trust_tier(pg["fm"])
        # #104c: thread provenance — delivered items with evidence-plane edges
        # carry where they came from ("discussed in / decided in")
        rels = pg["fm"].get("relations") or []
        if isinstance(rels, list):
            for r in rels:
                if isinstance(r, dict) and r.get("type") in ("originated_in", "decided_in", "validated_in"):
                    item.setdefault("provenance", []).append(
                        {"type": r.get("type"), "target": str(r.get("target", ""))})
                    break
        if s["stale"]:
            item["warning"] = f"review_after overdue {s['stale']} day(s)"
        # #90b: delivered patterns carry their known boundaries — the agent
        # sees where the pattern does NOT apply before following it
        if pg["type"] in ("pattern", "anti-pattern"):
            ces = pg["fm"].get("counterexamples") or []
            if isinstance(ces, list) and ces:
                item["counterexamples"] = [str(c).strip('"') for c in ces][:3]
        if pg["type"] == "commitment":
            item["trigger"] = str(pg["fm"].get("trigger") or "")
            if pg["fm"].get("owner"):
                item["owner"] = str(pg["fm"]["owner"])
            due = pg["fm"].get("due")
            if due:
                item["due"] = str(due)
                try:
                    import datetime as _dt
                    if _dt.date.today().isoformat() > str(due).strip()[:10]:
                        _w = f"commitment overdue (due {due})"
                        item["warning"] = (item["warning"] + "; " if item.get("warning") else "") + _w
                except (ValueError, IndexError):
                    pass  # malformed due date → no overdue warning (not a crash)
        sa = pg["fm"].get("stale_after")
        if sa:
            item["stale_after"] = str(sa)
            try:
                import datetime as _dt
                _v = str(sa).strip()[:10]
                if _dt.date.today().isoformat() >= _v:
                    _w = "stale_after reached — verify before relying on it"
                    item["warning"] = (item["warning"] + "; " if item.get("warning") else "") + _w
            except (ValueError, IndexError):
                pass  # malformed stale_after → no staleness warning (not a crash)
        if pg["fm"].get("title"):
            item["title"] = pg["fm"]["title"]
        selected.append(item)
    if len(scored) > max_items:
        # Borderline judged re-rank (#29 item 4): when the judgment tier is
        # active, candidates just past the --max cut (within 35% of the cut
        # score) get one noul relevance judgment each — cheap, per-item,
        # recorded. Judged-relevant items swap into 'selected' (max +2);
        # everything else keeps the deterministic decision. Never fatal.
        promoted_stems = set()
        # borderline = same priority tier as the last selected item (the cut
        # is tier-ordered, so same-tier = genuinely borderline inclusion)
        if scored:
            cut_tier = scored[max_items - 1]["priority"]
            borderline = [i for i, s in enumerate(scored[max_items:])
                          if s["priority"] == cut_tier][:4]
        else:
            borderline = []
        swapped = 0
        if scored and borderline and args_judge_borderline:
            try:
                from judgment import noul, is_judgment_active
                if is_judgment_active():
                    promoted_ids = []
                    for i in borderline:
                        s = scored[i]
                        if swapped >= RETRIEVAL["judged_max_promotions"]:
                            break
                        p = noul("Is this artifact relevant to the stated task?",
                                 (f"TASK: {task}\n\nARTIFACT: "
                                  f"{s['pg']['path']}\n"
                                  f"{(s['pg'].get('fm') or {}).get('statement') or (s['pg'].get('fm') or {}).get('problem') or ''}"))
                        excluded.append({"stem": s["pg"]["stem"], "path": s["pg"]["posix"],
                                         "reason": f"beyond --max {max_items}"
                                                   + (f" — judged-relevant, promoted"
                                                      if p >= RETRIEVAL["judged_relevant_p"] else
                                                      f" (judged: p={p:.2f}, not promoted)")})
                        if p >= RETRIEVAL["judged_relevant_p"]:
                            s["judged_p"] = p
                            selected.append(_judged_item(s, "judged-relevant", task))
                            swapped += 1
                            promoted_stems.add(s["pg"]["stem"])
            except Exception:
                pass  # tier unavailable → deterministic boundary stands
        for s in scored[max_items:]:
            if s["pg"]["stem"] in promoted_stems:
                continue  # judged-relevant item was promoted, not excluded
            excluded.append({"stem": s["pg"]["stem"], "path": s["pg"]["posix"],
                             "reason": f"beyond --max {max_items}"})

    return selected, excluded


def _judged_item(s, reason, task):
    """Item dict for a judged-promoted borderline candidate — full shape to
    match the selected-manifest contract (id/stem/path/type/scope/reason/
    priority + judged metadata for the receipt)."""
    pg = s["pg"]
    fm = pg.get("fm") or {}
    item = {
        "id": str(fm.get("id") or pg["stem"]),
        "stem": pg["stem"],
        "path": pg.get("posix", ""),
        "type": pg["type"],
        "scope": pg["scope"],
        "reason": f"{reason} (judged p={s.get('judged_p', 0):.2f})",
        "priority": s["priority"],
    }
    if fm.get("title"):
        item["title"] = fm["title"]
    return item


def trust_tier(fm):
    """OKF v0.2 §5.3 trust tier from verified[]: human-reviewed >
    machine-confirmed > unverified. Advisory signal, not access control."""
    v = fm.get("verified")
    if isinstance(v, dict):
        v = [v]
    if not v:
        return "unverified"
    if any(isinstance(x, dict) and str(x.get("by", "")).startswith("human:")
           for x in v):
        return "human-reviewed"
    return "machine-confirmed"


def code_navigation(task, project=None, max_files=None):
    """Graphify-gated navigation: map task tokens → code symbols in the
    connected repo's graphify graph → ranked file shortlist. 0 tokens (pure
    graph lookups); the harness still opens the files itself. Empty when the
    integration is off or no graph exists."""
    try:
        from fabric_config import (get_config, is_integration_active,
                                   get_all_repo_names, get_repo_config,
                                   resolve_repo_path, get_tuning)
        cfg = get_config()
        if not is_integration_active(cfg, "graphify"):
            return None
        if max_files is None:
            max_files = int(get_tuning(cfg, "context", "nav_max_files", 5))
        toks = [t for t in re.findall(r"[a-z0-9]{3,}", (task or "").lower())]
        if not toks:
            return None
        pinned = (project or "").strip().lower()
        entries = []
        for repo in get_all_repo_names(cfg):
            repo_cfg = get_repo_config(cfg, repo)
            if not is_integration_active(cfg, "graphify"):
                continue
            path = resolve_repo_path(cfg, repo)
            if not path:
                continue
            graph_dir = repo_cfg.get("graph_dir") or "graphify-out"
            graph_path = path / graph_dir / "graph.json"
            if not graph_path.exists():
                continue
            try:
                g = json.loads(graph_path.read_text())
            except Exception:
                continue  # corrupt/unreadable graph → no symbol expansion for this page
            hits = [n for n in g.get("nodes", [])
                    if n.get("source_file") and n.get("_callable")
                    and any(t in str(n.get("id", "")).lower() for t in toks)]
            if not hits:
                continue
            # Cross-project noise guard (#e2e finding): generic task tokens
            # (tool, add, test) match symbols in EVERY repo's graph. A repo
            # earns a nav section only when the task names it (slug token)
            # or the caller pinned it — unless its hits are dense enough to
            # be genuinely task-specific (>=15% of its callable nodes).
            from wf_common import project_slug
            _psl = project_slug(repo)
            task_names_repo = repo.lower() in toks or _psl in toks
            total_callable = sum(1 for n in g.get("nodes", []) if n.get("_callable") and n.get("source_file"))
            # dense = task-specific enough to stand without the pin: >= 8 hits
            # AND >= 5% of the repo's callable nodes (fixture graphs are small)
            dense = total_callable and len(hits) >= 8 and (len(hits) / total_callable) >= 0.05
            pinned_or_named = pinned == repo.lower() or task_names_repo
            if not pinned_or_named and not dense:
                continue
            files = {}
            for n in hits:
                f = n.get("source_file")
                if f:
                    files[f] = files.get(f, 0) + 1
            ranked = sorted(files.items(), key=lambda x: -x[1])[:max_files]
            entries.append({"repo": repo,
                            "symbols_matched": len(hits),
                            "files": [{"path": f, "symbol_count": c} for f, c in ranked]})
        # #54: pinned project's repo leads; remaining repos rank by symbol
        # matches (name tie-break keeps byte-identical re-runs).
        entries.sort(key=lambda e: (0 if e["repo"].lower() == pinned else 1,
                                    -e["symbols_matched"], e["repo"]))
        return entries or None
    except Exception:
        return None


def body_tokens(page):
    import re
    return set(re.findall(r"[a-z0-9][a-z0-9_-]{2,}", page["body"][:2000].lower()))


def render_markdown(task, paths, project, selected, excluded, nav=None):
    try:
        _excluded_cap = int(get_tuning(get_config(), "context", "excluded_cap", 15))
    except Exception:
        _excluded_cap = 15
    lines = [
        "# Context Manifest",
        "",
        f"- **Task:** {task}",
    ]
    if paths:
        lines.append(f"- **Code paths:** {', '.join(paths)}")
    if project:
        lines.append(f"- **Project:** {project}")
    lines += ["- **Compiled:** deterministic selection (0 tokens) — every item carries a reason", ""]

    if nav:
        lines.append("## Code navigation (graphify)")
        lines.append("")
        lines.append("Symbols matching the task, ranked by file — open these first:")
        lines.append("")
        for r in nav:
            lines.append(f"### {r['repo']} ({r['symbols_matched']} symbol matches)")
            lines.append("")
            for f in r["files"]:
                lines.append(f"- `{f['path']}` — {f['symbol_count']} matching symbols")
            lines.append("")

    if selected:
        lines.append("## Selected")
        lines.append("")
        tier_names = {"P1-project": "Project (highest precedence)", "P2-domain": "Domain", "P3-global": "Global"}
        cur = None
        for it in selected:
            if it["priority"] != cur:
                cur = it["priority"]
                lines.append(f"### {tier_names.get(cur, cur)}")
                lines.append("")
            warn = f" ⚠ {it['warning']}" if it.get("warning") else ""
            tier = it.get("trust_tier", "unverified")
            badge = {"human-reviewed": "trust: human-reviewed",
                     "machine-confirmed": "trust: machine-confirmed"}.get(tier, "")
            badge_part = f" `{badge}`" if badge else ""
            lines.append(f"- [[{it['stem']}]] — *{it['reason']}*{badge_part}{warn}")
            for p in it.get("provenance") or []:
                verb = {"originated_in": "discussed in", "decided_in": "decided in",
                        "validated_in": "validated in"}.get(p.get("type"), p.get("type"))
                lines.append(f"  *{verb}: {p.get('target', '')}*")
            for ce in it.get("counterexamples") or []:
                lines.append(f"  ⚠ does not apply: {ce}")
        lines.append("")

    lines.append("## Excluded")
    lines.append("")
    if excluded:
        for it in excluded[:_excluded_cap]:
            lines.append(f"- `{it['path']}` — {it['reason']}")
        if len(excluded) > _excluded_cap:
            lines.append(f"- ... and {len(excluded) - _excluded_cap} more")
    else:
        lines.append("_(nothing excluded)_")
    lines.append("")

    lines.append("## Precedence")
    lines.append("")
    lines.append("When artifacts conflict: project decisions override domain patterns,")
    lines.append("domain patterns override global policies. Cite the artifact you followed.")
    return "\n".join(lines) + "\n"


def integrations_state():
    """Report optional-integration state for manifest transparency."""
    try:
        from fabric_config import get_config, is_integration_active
        cfg = get_config()
        return {
            "graphify": is_integration_active(cfg, "graphify"),
            "embeddings": is_integration_active(cfg, "embeddings"),
        }
    except Exception:
        return {"graphify": False, "embeddings": False}


def _manifest_payload(task, paths, project, selected, excluded, today):
    """Canonical dict the manifest and receipt are both built from."""
    # ---- Graphify-gated code navigation (0 tokens): task → symbols → files
    nav = code_navigation(task, project)
    manifest = {
        "task": task,
        "paths": paths,
        "project": project,
        "compiled": today.isoformat(),
        "integrations": integrations_state(),
        "selected": selected,
        "excluded": excluded,
        "precedence": ["project", "domain", "global"],
    }
    if nav:
        manifest["code_navigation"] = nav
    return manifest


def receipt_id(manifest):
    """Content-derived receipt id: sha256 of the canonical manifest payload.

    Same corpus + task + flags => same id => re-running --write-receipt
    overwrites in place instead of accumulating dupes. Byte-stable: sorted
    keys, fixed separators."""
    payload = {k: v for k, v in manifest.items() if k != "$schema"}
    digest = hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return f"receipt-{digest[:12]}"


def _corpus_revision():
    """Git HEAD sha of the corpus (the vault is the sync unit); null when not
    a git repo. Receipts record *which* corpus revision they compiled against
    so an audit can re-run the exact compile."""
    try:
        import subprocess as _sp
        out = _sp.run(["git", "rev-parse", "HEAD"], cwd=VAULT_ROOT,
                      capture_output=True, text=True, timeout=5)
        if out.returncode == 0:
            return out.stdout.strip()
    except Exception:
        pass  # git unavailable in this harness → None (caller's default)
    return None


def build_receipt(manifest, rid, fabric_root, project):
    """receipt-v1 envelope: the manifest payload + provenance + location."""
    receipt = dict(manifest)
    receipt["$schema"] = "wiki-fabric/receipt-v1"
    receipt["receipt_id"] = rid
    receipt["manifest"] = "wiki-fabric/context-manifest-v1"
    receipt["fabric_root"] = fabric_root.name
    receipt["namespace"] = f"projects/{project}" if project else "registry"
    receipt["revision"] = _corpus_revision()
    return receipt


def write_receipt(manifest, project):
    """Persist the delivery receipt. Returns (path, id). Never throws —
    a receipt failure must not fail the compile."""
    try:
        rid = receipt_id(manifest)
        if project:
            base = layout.projects(VAULT_ROOT) / project / "receipts"
        else:
            base = layout.registry(VAULT_ROOT) / "receipts"
        base.mkdir(parents=True, exist_ok=True)
        out = base / f"{rid}.json"
        out.write_text(json.dumps(build_receipt(manifest, rid, VAULT_ROOT, project),
                                  indent=2, sort_keys=True) + "\n")
        return out, rid
    except Exception as e:
        print(f"warn: receipt not written: {e}", file=sys.stderr)
        return None, None


def main():
    global args_judge_borderline
    parser = argparse.ArgumentParser(description="Compile a task-specific context manifest (0 tokens)")
    parser.add_argument("--task", required=True, help="What the agent is about to do")
    parser.add_argument("--paths", action="append", default=[], help="Code path(s) the task touches (repeatable)")
    parser.add_argument("--project", help="Pin a project namespace (projects/<slug>/)")
    parser.add_argument("--format", choices=("markdown", "json"), default="markdown")
    parser.add_argument("--max", type=int, default=20, help="Max selected artifacts (default 20)")
    parser.add_argument("--write-receipt", action="store_true",
                        help="Persist the manifest as a receipt (schema receipt-v1); path on stderr")
    parser.add_argument("--judge-borderline", action="store_true",
                        help="#29: judgment tier re-ranks borderline beyond--max candidates (requires integrations.judgment; per-item receipt record)")
    args = parser.parse_args()
    args_judge_borderline = args.judge_borderline

    pages = load_corpus()
    selected, excluded = select_context(pages, args.task, args.paths, args.project, date.today(), args.max)
    manifest = _manifest_payload(args.task, args.paths, args.project, selected, excluded, date.today())
    nav = manifest.get("code_navigation")

    if args.write_receipt:
        rpath, rid = write_receipt(manifest, args.project)
        if rpath:
            print(f"receipt: {rpath} ({rid})", file=sys.stderr)

    if args.format == "json":
        print(json.dumps({"$schema": "wiki-fabric/context-manifest-v1", **manifest}, indent=2))
    else:
        print(render_markdown(args.task, args.paths, args.project, selected, excluded, nav))
    return 0


if __name__ == "__main__":
    sys.exit(main())