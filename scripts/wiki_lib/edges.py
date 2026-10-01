"""Wiki cross-page edges + the citation graph (#124.5a)."""
import re
import json
from datetime import date, timedelta
from pathlib import Path

import fabric_config
from fabric_config import get_config, get_all_repo_names, actor, get_vault_path
from wiki_lib.generators import _staleness, _claim_tier
from wf_common import now_iso_utc

TODAY = date.today()
def _compute_wiki_edges(topics, projects, min_shared=2):
    """Compute the wiki's cross-page network from grounded latent edges.

    `topics` and `projects` are the dicts produced by select_topics() /
    gathered project configs; both expose `.slug` and `claims`. Returns
    (page_edges, node_index):
      page_edges: {slug: [{"target", "kind", "weight"}, ...]} — the wikilinks a
        page should carry (topic->topic via shared source, topic<->project via
        shared claim). `kind` is "source" or "claim"; weight is shared count.
      node_index: {slug: {"type": "topic"|"project", "title"}}
    These edges are REAL relations derivable from evidence, never invented.
    """
    # Normalize projects: may be passed as slugs (from main) or dicts.
    def _proj_claims(p):
        if isinstance(p, str):
            from layout import claims_for_project
            glob = claims_for_project(fabric_config.CORPUS_ROOT, p)
            return [c.stem for c in glob.parent.glob(glob.name)]
        return [c.get("id") if isinstance(c, dict) else c for c in p.get("claims", [])]

    def _proj_slug(p):
        return p if isinstance(p, str) else p["slug"]

    # claim -> topic slugs
    claim_topics = {}
    for t in topics:
        for c in t["claims"]:
            cid = c.get("id") if isinstance(c, dict) else c
            claim_topics.setdefault(cid, set()).add(t["slug"])
    # claim -> project slugs
    claim_projects = {}
    for p in projects:
        pslug = _proj_slug(p)
        for cid in _proj_claims(p):
            if cid:
                claim_projects.setdefault(cid, set()).add(pslug)
    # claim -> source
    claim_source = {}
    for cp in (fabric_config.CORPUS_ROOT / "evidence" / "claims").glob("claim-*.md"):
        m = re.search(r'resource: "\[\[(src-[^\]]+)\]\]"',
                      cp.read_text(encoding="utf-8", errors="replace"))
        if m:
            claim_source[cp.stem] = m.group(1)

    # topic -> set of sources it cites (for topic-topic via shared source)
    topic_sources = {}
    for cid, src in claim_source.items():
        for t in claim_topics.get(cid, ()):
            topic_sources.setdefault(t, set()).add(src)

    page_edges = {t["slug"]: [] for t in topics}
    page_edges.update({_proj_slug(p): [] for p in projects})
    node_index = {t["slug"]: {"type": "topic", "title": t["title"]} for t in topics}
    node_index.update({_proj_slug(p): {"type": "project", "title": _proj_slug(p)} for p in projects})

    # topic <-> topic via shared source (>= min_shared)
    topic_slugs = [t["slug"] for t in topics]
    for i in range(len(topic_slugs)):
        for j in range(i + 1, len(topic_slugs)):
            a, b = topic_slugs[i], topic_slugs[j]
            shared = len(topic_sources.get(a, set()) & topic_sources.get(b, set()))
            if shared >= min_shared:
                page_edges[a].append({"target": b, "kind": "source", "weight": shared})
                page_edges[b].append({"target": a, "kind": "source", "weight": shared})

    # topic <-> project via shared claim
    for cid in set(claim_topics) & set(claim_projects):
        for t in claim_topics[cid]:
            for p in claim_projects[cid]:
                page_edges[t].append({"target": p, "kind": "claim", "weight": 1})
                page_edges[p].append({"target": t, "kind": "claim", "weight": 1})

    # dedupe + sort by weight desc
    for slug, edges in page_edges.items():
        by_key = {}
        for e in edges:
            key = e["target"]
            prev = by_key.get(key)
            if prev is None:
                by_key[key] = dict(e)
            else:
                by_key[key]["weight"] += e["weight"]
        page_edges[slug] = sorted(by_key.values(), key=lambda e: -e["weight"])
    return page_edges, node_index

# === staleness classification ===
def emit_citation_graph(topics, projects, dry_run=False):
    """Write registry/wiki-graph.json — the MACHINE-READABLE value of the wiki.

    The wiki's prose is human-facing; never feed it back to a model. Its
    machine value is the derived structure — the explicit node/edge network:
      nodes[]: every wiki page (topic/project) + source provenance
      edges[]: topic->claim, project->claim, claim->source, and the computed
               topic<->topic / topic<->project cross-page relations (grounded
               in shared sources/claims, never invented)
    So a GraphRAG/visualizer can represent the network without re-reading prose.

    Legacy keys (topics/projects/claim_sources) are retained for back-compat.
    """
    import json

    claim_sources = {}
    for cp in sorted((fabric_config.CORPUS_ROOT / "evidence" / "claims").glob("claim-*.md")):
        s = cp.read_text(encoding="utf-8", errors="replace")
        m = re.search(r'resource: "\[\[(src-[^\]]+)\]\]"', s)
        claim_sources[cp.stem] = m.group(1) if m else None

    graph = {
        "generated": TODAY.isoformat(),
        "type": "wiki-graph",
        "nodes": [],
        "edges": [],
        "topics": [],
        "projects": [],
        "claim_sources": claim_sources,
    }

    node_ids = set()

    def _add_node(nid, label, ntype, **extra):
        if nid in node_ids:
            return
        node_ids.add(nid)
        n = {"id": nid, "label": label, "type": ntype, **extra}
        graph["nodes"].append(n)

    def _add_edge(source, target, rel, **extra):
        graph["edges"].append({"source": source, "target": target,
                               "relation": rel, **extra})

    # pages as nodes; links topic/project -> claim -> source as edges
    for t in topics:
        _add_node(f"topic:{t['slug']}", t["title"], "topic", domain=t.get("domain"), claims=len(t["claims"]))
        t_claims = []
        for cs in t["claims"]:
            cp = fabric_config.CORPUS_ROOT / "evidence" / "claims" / f"{cs}.md"
            if not cp.exists():
                continue
            tier = _claim_tier(cp)
            t_claims.append({"id": cs, "tier": tier})
            _add_node(f"claim:{cs}", cs, "claim", tier=tier)
            _add_edge(f"topic:{t['slug']}", f"claim:{cs}", "cites", tier=tier)
            src = claim_sources.get(cs)
            if src:
                _add_node(f"src:{src}", src, "source")
                _add_edge(f"claim:{cs}", f"src:{src}", "traces_to")
        graph["topics"].append({"slug": t["slug"], "title": t["title"],
                                "domain": t["domain"], "claims": t_claims})
    for proj in projects:
        p_claims = []
        from layout import claims_for_project
        from wf_common import project_slug as _psl
        c_glob = claims_for_project(fabric_config.CORPUS_ROOT, proj)
        for cp in sorted(c_glob.parent.glob(c_glob.name)):
            tier = _claim_tier(cp)
            p_claims.append({"id": cp.stem, "tier": tier})
            _add_node(f"claim:{cp.stem}", cp.stem, "claim", tier=tier)
            _add_edge(f"project:{proj}", f"claim:{cp.stem}", "cites", tier=tier)
        if p_claims:
            _add_node(f"project:{proj}", proj, "project", claims=len(p_claims))
            graph["projects"].append({"slug": _psl(proj), "claims": p_claims})

    # cross-page relations (topic<->topic, topic<->project)
    page_edges, _ = _compute_wiki_edges(topics, projects)
    proj_slugs = {p["slug"] for p in projects} if projects and not isinstance(projects[0], str) else set(projects)
    for slug, edges in page_edges.items():
        kind = "project" if slug in proj_slugs else "topic"
        src = f"{kind}:{slug}"
        for e in edges:
            tkind = "project" if e["target"] in proj_slugs else "topic"
            _add_edge(src, f"{tkind}:{e['target']}", e["kind"], weight=e["weight"])

    out_path = fabric_config.CORPUS_ROOT / "registry" / "wiki-graph.json"
    if not dry_run:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(graph, indent=2), encoding="utf-8")
    return out_path
