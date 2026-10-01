#!/usr/bin/env python3
"""wiki_lib/deepdives.py — graphify-rendered project deep dives (#145 / living-wiki S3).

Per connected project with an active code graph, renders deterministically
(0 LLM tokens):
  wiki/projects/<slug>/architecture.md   — god nodes + communities, mermaid
  wiki/projects/<slug>/components/<c>.md — one page per major community
  wiki/projects/<slug>/tour.md           — guided walk of the component graph

Every page carries a corpus-rev provenance stamp (the graph hash) — a stale
graph renders stale pages, so the stamp is load-bearing. Projects without
graphs are skipped (no empty shells).
"""

import json
import re
import sys
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "lib"))


from wf_common import claim_statement
from wiki_lib.diagrams import _mermaid_valid, MERMAID_REPAIR_COMMENT

_NOISE = ("test", "conftest", "fixture")


def _graph_path(slug):
    # canonical slug: graphify-bridge imports as comfyui_mcp-graph.json today,
    # canonical runs as comfyui-mcp-graph.json — bridge writes both forms; the
    # canonical form is authoritative (falls back to the raw form once, then
    # import migrates forward).
    from fabric_config import CORPUS_ROOT
    from wf_common import project_slug
    c = project_slug(slug)
    return CORPUS_ROOT / "global" / "graphs" / f"{c}-graph.json"


def _load_graph(slug):
    """(nodes, links, rev) for a project's graph, or (None, None, None)."""
    gp = _graph_path(slug)
    if not gp.exists():
        return None, None, None
    try:
        d = json.loads(gp.read_text(encoding="utf-8"))
    except Exception:
        return None, None, None
    nodes = d.get("nodes") or []
    links = d.get("links") or []
    rev = None
    hp = CORPUS_ROOT_HASH(slug)
    if hp and hp.exists():
        rev = hp.read_text(encoding="utf-8").strip()[:12]
    return nodes, links, rev


def CORPUS_ROOT_HASH(slug):
    from fabric_config import CORPUS_ROOT
    from wf_common import project_slug
    return CORPUS_ROOT / "global" / "graphs" / f"{project_slug(slug)}-graph.hash"


def _degree(nodes, links):
    """Count in+out degree. links may be dicts (graph) or (s,t,rel) tuples."""
    from collections import Counter
    deg = Counter()
    for l in links:
        if isinstance(l, tuple):
            s, t = l[0], l[1]
        else:
            s, t = l.get("source"), l.get("target")
        deg[s] += 1
        deg[t] += 1
    return deg


def _god_nodes(nodes, links, top_n=12):
    """Degree-ranked (id, label, degree), skipping test/conftest noise."""
    deg = _degree(nodes, links)
    out = []
    for nid, d in deg.most_common(top_n * 3):
        if len(out) >= top_n:
            break
        if any(k in nid.lower() for k in _NOISE):
            continue
        out.append((nid, nid.replace("_", " "), d))
    return out


def _major_communities(nodes, links, min_size=8, max_comms=8):
    """[(comm_id, name, member_nodes, intra_edges)] sorted by size desc."""
    sizes = {}
    for n in nodes:
        c = n.get("community")
        if c is not None:
            sizes[c] = sizes.get(c, 0) + 1
    majors = {c for c, s in sizes.items() if s >= min_size}
    if not majors and sizes:
        # tiny graphs: take the two largest so components always render
        majors = {c for c, _ in sorted(sizes.items(), key=lambda kv: -kv[1])[:2]}
    members = {}
    names = {}
    for n in nodes:
        c = n.get("community")
        if c in majors:
            members.setdefault(c, []).append(n)
            names.setdefault(c, n.get("community_name") or f"community-{c}")
    ncomm = {}
    for n in nodes:
        ncomm[n["id"]] = n.get("community")
    intra = {c: [] for c in members}
    for l in links:
        s, t = l.get("source"), l.get("target")
        cs, ct = ncomm.get(s), ncomm.get(t)
        if cs in members and ct in members:
            intra[cs].append((s, t, l.get("relation") or "links"))
    out = []
    for c in sorted(members, key=lambda c: -len(members[c]))[:max_comms]:
        intra[c].sort()
        intra[c] = intra[c][:40]  # deterministic cap
        out.append((c, names[c], members[c], intra[c]))
    return out


def _safe_id(nid):
    return re.sub(r"[^A-Za-z0-9_]", "_", nid)[:60] or "n"


def _mermaid(nodes, edges, title):
    """Mermaid flowchart from (nodes, edges). Validated; text fence on fail."""
    deg = _degree(nodes, edges)
    keep = [nid for nid, _ in deg.most_common(10)]
    label = {n["id"]: n.get("label") or n["id"] for n in nodes if n["id"] in set(keep)}
    lines = ["flowchart LR"]
    for nid in keep:
        lines.append(f'    {_safe_id(nid)}["{label.get(nid, nid)[:36]}"]')
    seen = set()
    for s, t, rel in edges:
        if s in label and t in label:
            key = (s, t)
            if key in seen:
                continue
            seen.add(key)
            lines.append(f"    {_safe_id(s)} -->|{rel[:20]}| {_safe_id(t)}")
    code = "\n".join(lines)
    if not _mermaid_valid(code):
        return f"<!-- {MERMAID_REPAIR_COMMENT.strip('<!-- -->')} -->\n```text\n{code}\n```"
    return f"```mermaid\n{code}\n```"


def _provenance(slug, rev, mode="mechanical"):
    return (f"generated: {{ by: \"process:deepdives\", at: \"{date.today().isoformat()}\" }}\n"
            f"graph_rev: {rev or 'unknown'}\n"
            f"review_after: {date.today().replace(year=date.today().year + 1).isoformat()}")


def _front(title, desc, slug, rev):
    return (f"---\ntype: index\ntitle: \"{title}\"\n"
            f"description: \"{desc}\"\n"
            f"{_provenance(slug, rev)}\n---\n\n")


def _claims_footnote(slug, max_n=8):
    """Related evidence claims (footnoted citations), matched by the canonical
    project slug (project_slug seam — underscore repo names join kebab claims)."""
    from fabric_config import CORPUS_ROOT
    from layout import claims_for_project
    glob = claims_for_project(CORPUS_ROOT, slug)
    claims = sorted(glob.parent.glob(glob.name))
    out = []
    for c in claims[:max_n]:
        st = claim_statement(c)
        if st:
            out.append(f"- [[{c.stem}]] — {st[:110]}")
    return out


def render_architecture(slug, nodes, links, rev, dry_run=False):
    deg = _degree(nodes, links)
    gods = _god_nodes(nodes, links)
    comms = _major_communities(nodes, links)
    lines = [_front(f"{slug}: Architecture", f"God nodes and communities of the {slug} code graph", slug, rev)]
    lines.append(f"# Architecture: {slug}\n")
    lines.append(f"Rendered from the graphify code graph — {len(nodes)} nodes, "
                 f"{len(links)} edges, {len(comms)} major communities (graph rev `{rev or 'unknown'}`).\n")
    lines.append("## God nodes (highest connectivity)\n")
    lines.append("| Node | Degree |")
    lines.append("|---|---|")
    for nid, label, d in gods:
        lines.append(f"| `{label}` | {d} |")
    lines.append("")
    lines.append("## Major components (communities)\n")
    lines.append("| Component | Nodes |")
    lines.append("|---|---|")
    for c, name, members, _ in comms:
        lines.append(f"| [[{slug}/{_slug(name)}|{name}]] | {len(members)} |")
    lines.append("")
    arch_edges = _top_edges(nodes, links)
    lines.append(_mermaid(nodes, arch_edges, f"{slug} architecture (top edges)"))
    lines.append("")
    claims = _claims_footnote(slug)
    if claims:
        lines.append("## Evidence claims citing this project\n")
        lines.extend(f"- {c}" for c in claims)
        lines.append("")
    return "\n".join(lines) + "\n"


def _slug(name):
    return re.sub(r"[^a-z0-9-]+", "-", str(name).lower()).strip("-")[:40] or "c"


def _top_edges(nodes, links, top=12):
    deg = _degree(nodes, links)
    nmap = {n["id"]: n for n in nodes}
    pairs = []
    for l in links:
        s, t = l.get("source"), l.get("target")
        if s in nmap and t in nmap and not any(k in s.lower() for k in _NOISE):
            pairs.append((s, t, l.get("relation") or "links"))
    # prefer edges touching god nodes
    deg = _degree(nodes, links)
    pairs.sort(key=lambda p: -(deg.get(p[0], 0) + deg.get(p[1], 0)))
    out, seen = [], set()
    for s, t, rel in pairs:
        if (s, t) in seen:
            continue
        seen.add((s, t))
        out.append((s, t, rel))
        if len(out) >= top:
            break
    return out


def render_component(slug, rev, comm_id, name, members, edges, links, dry_run=False):
    deg = _degree(members, edges)
    sub = [n for n in members]
    lines = [_front(f"{slug}: {name}",
                    f"Component community from the {slug} code graph", slug, rev)]
    lines.append(f"# Component: {name}\n")
    lines.append(f"{len(members)} nodes in this community (graph rev `{rev or 'unknown'}`).\n")
    top = sorted(members, key=lambda n: -deg.get(n["id"], 0))[:10]
    lines.append("## Key members\n")
    lines.append("| Node | Degree | File |")
    lines.append("|---|---|---|")
    for n in top:
        f = (n.get("source_file") or "").replace("\\", "/")
        lines.append(f"| `{n.get('label') or n['id']}` | {deg.get(n['id'], 0)} | {f} |")
    lines.append("")
    if edges:
        lines.append(_mermaid(members, edges, name))
        lines.append("")
    return "\n".join(lines) + "\n"


def render_tour(slug, nodes, links, rev, dry_run=False):
    comms = _major_communities(nodes, links)
    gods = _god_nodes(nodes, links, top_n=5)
    lines = [_front(f"{slug}: Guided tour", f"Reading order for the {slug} code graph", slug, rev)]
    lines.append(f"# Guided tour: {slug}\n")
    lines.append("Entry points first, core next, then the communities that hang off them. "
                 "Each step links its component page.\n")
    lines.append("## Start here (hubs)\n")
    for nid, label, d in gods:
        lines.append(f"1. `{nid}` — degree {d}")
    lines.append("")
    lines.append("## Then, in order\n")
    for i, (c, name, members, _) in enumerate(comms, 1):
        lines.append(f"{i}. [[{slug}/{_slug(name)}|{name}]] — {len(members)} nodes")
    lines.append("")
    return "\n".join(lines) + "\n"


def generate(slug, dry_run=False, wiki_root=None):
    """Render the deep-dive set for one project. Returns (pages_written, n_nodes).
    Skips silently (returns ([], 0)) when the project has no graph. The tree,
    headings, and wikilinks key on the CANONICAL slug (project_slug) — a raw
    underscore name rendered the same project into two wiki trees depending
    on which form the caller passed."""
    from wf_common import project_slug
    slug = project_slug(slug)
    nodes, links, rev = _load_graph(slug)
    if nodes is None or not nodes:
        return [], 0
    if wiki_root is None:
        from wiki_lib.generators import _wiki_root as wr
        wiki_root = wr()
    out_dir = wiki_root / "projects" / slug
    written = []

    arch = render_architecture(slug, nodes, links, rev)
    comp_dir = out_dir / "components"
    comp_pages = []
    comms = _major_communities(nodes, links)
    deg = _degree(nodes, links)
    for c, name, members, edges in comms:
        text = render_component(slug, rev, c, name, members, edges, links)
        comp_pages.append((comp_dir / f"{_slug(name)}.md", text))
    tour = render_tour(slug, nodes, links, rev)

    if not dry_run:
        comp_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "architecture.md").write_text(arch, encoding="utf-8")
        written.append(out_dir / "architecture.md")
        for p, text in comp_pages:
            p.write_text(text, encoding="utf-8")
            written.append(p)
        (out_dir / "tour.md").write_text(tour, encoding="utf-8")
        written.append(out_dir / "tour.md")
    return written, len(nodes)