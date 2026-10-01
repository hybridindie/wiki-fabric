#!/usr/bin/env python3
# export-wiki.py — Generate the human-layer wiki from the evidence corpus.
#
# Produces narrative articles (OpenWiki style) into the vault:
#   wiki/topics/<topic>.md      — mechanism-first, cross-project
#   wiki/projects/<project>.md  — narrative per-repo summary
#   wiki/domains/               — domain hubs (table of contents)
#   wiki/index.md               — staleness dashboard + recent changes
#
# Articles are ASSEMBLED VIEWS over claims — never copied content.
# Claims are cited as numbered footnotes. Generation mode configurable
# per project (mechanical | llm | hybrid) in fabric.yaml wiki.generation.
#
# Staleness: 3-tier citation surfacing (current / ⚠ due / archived).
#
# Usage:
#   python3 scripts/cmd/export-wiki.py [--project <slug>] [--dry-run]
#        [--mode mechanical|llm|hybrid]

import sys
import sys as _s, pathlib as _p
_HERE = _p.Path(__file__).resolve().parent
# Explicit import bootstrap: this script's own dir (same-dir siblings)
# + scripts/lib (shared modules). No shotgun path injection.
for _dir in (_HERE, _HERE.parent / "lib", _HERE.parent):
    if str(_dir) not in _s.path:
        _s.path.insert(0, str(_dir))
import re
import os
import json
from pathlib import Path
from datetime import date, datetime, timedelta

from fabric_config import FABRIC_ROOT, CORPUS_ROOT, get_config, get_all_repo_names, get_repo_config, get_vault_path, actor
from wf_common import now_iso_utc
from wiki_lib.diagrams import MERMAID_REPAIR_COMMENT, _mermaid_valid, _validate_and_repair_diagrams
from wiki_lib.generators import (_enrich_page, _staleness, _cite_claim,
                                 _llm_topic_article, _llm_project_article,
                                 _generate_topic_article, _generate_project_article,
                                 _generate_index, _generate_domain_hubs, _claim_tier)
from wiki_lib.edges import _compute_wiki_edges, emit_citation_graph

TODAY = date.today()

# Provenance stamp for every generated wiki page (OKF §5 / LangChain-OpenWiki style).
# The agent actor is the compiler model that wrote the prose; mechanical pages are
# stamped as a process. `by` carries the full actor; `at` is an ISO-8601 instant.
def _wiki_root():
    """The wiki output dir — the LAYOUT-AWARE default resolver rule
    (fabric_config._default_vault_root: nested corpus → corpus/wiki). An
    explicit vault.path NAMES the wiki root directly (no /wiki appending —
    that double-nested wiki/wiki in corpus layouts)."""
    from fabric_config import _default_vault_root
    return _default_vault_root()


def select_topics(min_claims=None):
    """Group claims by concept → topics with enough evidence become articles."""
    if min_claims is None:
        from fabric_config import get_tuning
        min_claims = get_tuning(None, "export", "topic_min_claims", 6)
    topics = []
    for c in sorted((CORPUS_ROOT / "concepts").glob("concept-*.md")):
        s = c.read_text(encoding="utf-8", errors="replace")
        title = re.search(r"^title: (.+)$", s, re.MULTILINE)
        dom = re.search(r"^domain: \[(.*?)\]", s, re.MULTILINE)
        claims = re.findall(r'\[\[(claim-[^\]]+)\]\]', s)
        if len(claims) >= min_claims:
            topics.append({
                "file": c, "title": title.group(1).strip() if title else c.stem,
                "domain": dom.group(1) if dom else "agent-systems",
                "claims": claims, "body": s.split("---", 2)[2] if s.startswith("---") else s,
            })
    for t in topics:
        t["slug"] = re.sub(r"[^a-z0-9-]+", "-", t["title"].lower()).strip("-")
    return topics

def _reconcile_wiki_dir(subdir, dry_run=False):
    """Delete stale generated pages in a wiki subdir so a run always reflects
    current evidence (the vault is the RESULT, never an accumulating mirror).
    Returns count of files present (removed in non-dry-run)."""
    d = _wiki_root() / subdir
    if not d.exists():
        return 0
    removed = 0
    for p in d.glob("*.md"):
        removed += 1
        if dry_run:
            continue
        try:
            p.unlink()
        except OSError:
            pass  # best-effort reconcile — page regenerates on next run
    return removed


def _concepts_exist():
    """True when the concept layer is already populated. export regenerates topics
    from existing concepts and does NOT re-synthesize on every run (concept
    synthesis is ~1 LLM call per cluster; bounded to first-run/repair)."""
    return (CORPUS_ROOT / "concepts").exists() and list(
        (CORPUS_ROOT / "concepts").glob("concept-*.md"))


def _synthesize_concepts(config, dry_run=False):
    """Restore the concept layer (which topics are built from) before selecting
    topics — but ONLY when concepts are missing/stale, so routine exports are
    cheap. Gated on the compiler eval; returns count of concepts synthesized."""
    if _concepts_exist():
        return 0
    try:
        import synthesize as _syn
        written = _syn.synthesize_uncovered(cfg=config, dry_run=dry_run)
        return len(written)
    except Exception as e:
        print(f"  SKIP concept synthesis (unavailable): {e}", file=sys.stderr)
        return 0


def _rebuild_catalog(dry_run=False):
    """Reconcile registry/catalog.json to what is actually on disk (part C).
    Returns True on success."""
    try:
        import importlib.util as _ilu
        _spec = _ilu.spec_from_file_location(
            "rebuild_index",
            str(Path(__file__).parent / "rebuild-index.py"))
        _ri = _ilu.module_from_spec(_spec); _spec.loader.exec_module(_ri)
        root = CORPUS_ROOT
        _ri.VAULT_ROOT = root
        _ri.INDEX_PATH = root / "registry" / "catalog.json"
        categories = _ri.scan_vault()
        registry = _ri.build_catalog(categories)
        if dry_run:
            return True
        _ri.write_catalog(registry)
        return True
    except Exception:
        return False


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Generate the human-layer wiki from the evidence corpus")
    parser.add_argument("--project", help="Generate for one project only")
    parser.add_argument("--deep-dives", action="store_true",
                        help="Also render graphify deep dives (architecture/components/tour) for connected projects (#145)")
    parser.add_argument("--mode", default=None, choices=["mechanical", "llm", "hybrid"],
                       help="Override generation mode (default: fabric.yaml wiki.generation)")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--push", action="store_true",
                        help="Write generated notes through the Obsidian Local REST API (#112; requires integrations.obsidian)")
    args = parser.parse_args()

    config = get_config()
    mode = args.mode or (config.get("wiki", {}).get("generation", {}).get("default") or "hybrid")

    print(f"=== Generating wiki ({mode}) ===")

    # (H) Harvest-before-export (#112): human edits to wiki notes land as
    # evidence BEFORE regeneration overwrites them. No-op when the obsidian
    # integration is off (graphify gating pattern).
    try:
        from obsidian_bridge import harvest_before_export
        harvest = harvest_before_export(dry_run=args.dry_run, project=args.project)
        if harvest.get("harvested"):
            print(f"  harvested: {harvest['harvested']} human-edited note(s) → evidence/raw/"
                  f"{(args.project or 'vault')}/obsidian/")
        elif harvest.get("reason"):
            print(f"  harvest: {harvest['reason']}")
    except Exception as e:
        print(f"  harvest skipped: {e}", file=sys.stderr)

    # (B) Reconcile: clear stale generated pages so the output reflects current
    # evidence, never an accumulating set of orphans.
    n_remove_t = _reconcile_wiki_dir("topics", dry_run=args.dry_run)
    n_remove_p = _reconcile_wiki_dir("projects", dry_run=args.dry_run)
    n_remove_d = _reconcile_wiki_dir("domains", dry_run=args.dry_run)

    # (A) Restore the concept layer (topics are built FROM concepts).
    #     Gated on the compiler eval; 0-token clustering, LLM synthesis.
    n_concepts = _synthesize_concepts(config, dry_run=args.dry_run)
    if n_remove_t or n_remove_p:
        print(f"  reconciled: removed {n_remove_t} stale topic(s), {n_remove_p} stale project(s)")

    topics = select_topics()
    projects = get_all_repo_names(config)
    print(f"  Topics: {len(topics)} ({n_concepts} concept(s) synthesized) | Projects: {len(projects)}")
    print()

    # Cross-page network: real relations derivable from evidence (shared
    # sources/claims). Feeds both the per-page "Related" links and the graph.
    page_edges, node_index = _compute_wiki_edges(topics, projects)

    n_topics = 0
    for t in topics:
        out, n = _generate_topic_article(t, mode, dry_run=args.dry_run)
        if out:
            n_topics += 1
            if not args.dry_run:
                _enrich_page(out, config, mode, related_links=page_edges.get(t["slug"], []))
            print(f"  topic: {out.name} ({n} claims)")

    n_projects = 0
    project_counts = []
    for proj in projects:
        out, n = _generate_project_article(proj, config, dry_run=args.dry_run, mode=mode)
        project_counts.append((proj, n))
        if out:
            n_projects += 1
            if not args.dry_run:
                _enrich_page(out, config, mode, related_links=page_edges.get(proj, []))
            print(f"  project: {out.name} ({n} current claims)")

    index = _generate_index(topics, project_counts, dry_run=args.dry_run)

    # Domain hub pages: navigational structure grouping topics by domain.
    n_domains = 0
    hubs = _generate_domain_hubs(topics, dry_run=args.dry_run)
    n_domains = len(hubs)
    if hubs:
        print(f"  domain hub(s): {n_domains}")

    # Deep dives (#145): graphify-rendered architecture/components/tour pages.
    n_dd_pages = 0
    if args.deep_dives:
        from wiki_lib.deepdives import generate as _dd, _graph_path
        dd_root = _wiki_root() / "projects"
        active = set(get_all_repo_names(config))
        # canonical slugs: repo names may be underscore-form (comfyui_mcp);
        # every deep-dive tree + graph file keys on the canonical kebab slug.
        from wf_common import project_slug as _psl
        canonical = {_psl(p) for p in active}
        # reconcile: remove deep-dive trees for projects with no graph/repo
        # (compare CANONICAL forms — raw-form membership left two trees for
        # one project whenever the config key's form changed between runs)
        if dd_root.is_dir() and not args.dry_run:
            for sub in sorted(dd_root.glob("*/")):
                if _psl(sub.name) not in canonical or not _graph_path(_psl(sub.name)).exists():
                    for sub_p in sorted(sub.rglob("*.md")):
                        try:
                            sub_p.unlink()
                        except OSError:
                            pass  # best-effort (same reconcile contract as _reconcile_wiki_dir)
        for proj in sorted(active):
            try:
                written, n_nodes = _dd(_psl(proj), dry_run=args.dry_run)
                if written:
                    n_dd_pages += len(written)
                    print(f"  deep-dive: {proj} — {len(written)} page(s) from {n_nodes} nodes")
            except Exception as e:
                print(f"  deep-dive skipped for {proj}: {e}", file=sys.stderr)

    # Machine value of the human wiki: the citation edges, as deterministic JSON.
    graph_path = emit_citation_graph(topics, get_all_repo_names(config), dry_run=args.dry_run)

    # (C) Reconcile the machine index to disk.
    if _rebuild_catalog(dry_run=args.dry_run):
        print("  rebuilt: registry/catalog.json")

    # Human exploration is done in Obsidian's native Graph view (which renders the
    # [[wikilinks]] between generated wiki pages); no separate HTML viewer.
    print(f"\n{'[DRY RUN] ' if args.dry_run else ''}Generated {n_topics} topic article(s), "
          f"{n_projects} project article(s), 1 index"
          + (f", {n_dd_pages} deep-dive page(s)" if args.deep_dives else ""))
    if not args.dry_run:
        print(f"Citation graph: {graph_path}")
        # (P) REST write path (#112d): when --push and the integration is on,
        # mirror the fresh wiki through the Local REST API (better transport
        # across sync boundaries; file-copy stays the fallback and default).
        if args.push:
            try:
                from obsidian_bridge import _integration_cfg, check_server, push_notes
                cfg = _integration_cfg()
                if cfg is None:
                    print("  --push ignored: integrations.obsidian not enabled", file=sys.stderr)
                elif not check_server(cfg):
                    print("  --push failed: server not reachable (is Obsidian running?)", file=sys.stderr)
                    return 1
                else:
                    wiki_root = _wiki_root()
                    notes = [(str(p.relative_to(wiki_root)), p.read_text(encoding="utf-8"))
                             for p in sorted(wiki_root.rglob("*.md"))]
                    written, failed = push_notes(notes)
                    print(f"  pushed: {written} note(s) via REST ({failed} failed)")
            except Exception as e:
                print(f"  push failed: {e}", file=sys.stderr)
                return 1
        # (R) Record the fresh output in the export manifest (#112): the next
        # harvest diff is against THIS content.
        try:
            from obsidian_bridge import record_export
            record_export(_wiki_root())
        except Exception as e:
            print(f"  export manifest not recorded: {e}", file=sys.stderr)
    print(f"Wiki: {_wiki_root()}/")
    return 0


if __name__ == "__main__":
    sys.exit(main())