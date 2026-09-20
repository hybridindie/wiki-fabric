#!/usr/bin/env python3
# graphify-bridge.py — Optional graphify integration layer for the wiki fabric
#
# Usage:
#   python3 scripts/graphify-bridge.py --update            # Run graphify update on connected repos
#   python3 scripts/graphify-bridge.py --import            # Import graph structure into fabric
#   python3 scripts/graphify-bridge.py --diff              # Detect stale claims via graph diff
#   python3 scripts/graphify-bridge.py --status            # Show graphify integration status
#   python3 scripts/graphify-bridge.py --enrich            # Enrich claims with code_symbol edges
#
# Graphify adds structural intelligence at 0 token cost:
#   - Call/import/rationale edges between code symbols
#   - Community detection (concept boundaries)
#   - Staleness detection (graph diff between runs)
#
# This module is OPTIONAL — the fabric works without it. When present, it
# enhances query retrieval (graph expansion), concept clustering (communities),
# and staleness detection (graph diff).

import sys
import re
import json
import hashlib
import argparse
import subprocess
from pathlib import Path
from datetime import date
from collections import defaultdict, Counter

sys.path.insert(0, str(Path(__file__).parent))
from fabric_config import get_config, FABRIC_ROOT, resolve_repo_path, get_all_repo_names, get_repo_graph_dir
from wf_common import parse_frontmatter

VAULT_ROOT = FABRIC_ROOT
GRAPHS_DIR = VAULT_ROOT / "global" / "graphs"
CLAIMS_DIR = VAULT_ROOT / "evidence" / "claims"

# Relevant edge types for fabric expansion
EXPAND_EDGE_TYPES = {"calls", "imports", "imports_from", "uses", "references", "inherits"}
# Provenance edges (doc → code)
PROVENANCE_EDGE_TYPES = {"rationale_for"}


def get_graph_path(repo_name):
    """Get the graph.json path for a repo from fabric.yaml config."""
    config = get_config()
    repo_path = resolve_repo_path(config, repo_name)
    if not repo_path:
        return None
    graph_dir = get_repo_graph_dir(config, repo_name)
    graph_path = repo_path / graph_dir / "graph.json"
    return graph_path if graph_path.exists() else None


def load_graph(repo_name):
    """Load a graphify graph.json."""
    graph_path = get_graph_path(repo_name)
    if not graph_path:
        return None
    with open(graph_path) as f:
        return json.load(f)


def graph_hash(graph):
    """Compute a hash of the graph structure for diff detection."""
    nodes = sorted(n["id"] for n in graph.get("nodes", []))
    links = sorted(f"{l['source']}->{l['target']}:{l.get('relation', '')}" for l in graph.get("links", []))
    content = json.dumps({"nodes": nodes, "links": links}, sort_keys=True)
    return hashlib.sha256(content.encode()).hexdigest()[:16]


def _repo_targets(repos=None):
    """Resolve target repo names from fabric.yaml (repos: keys), optionally
    narrowed to the given subset. All commands previously read a REPO_CONFIG
    global that no longer exists; config is the single source of truth."""
    config = get_config()
    names = get_all_repo_names(config)
    if repos:
        return [r for r in names if r in repos]
    return names


def cmd_update(repos=None):
    """Run graphify update on connected repos (AST-only, 0 API cost)."""
    config = get_config()
    targets = repos or get_all_repo_names(config)
    for repo_name in targets:
        repo_path = resolve_repo_path(config, repo_name)
        if not repo_path or not repo_path.exists():
            print(f"  Skipping {repo_name}: repo not found")
            continue

        print(f"  Updating graph for {repo_name}...")
        try:
            result = subprocess.run(
                ["graphify", "update", "."],
                cwd=str(repo_path),
                capture_output=True,
                text=True,
                timeout=120,
            )
            if result.returncode == 0:
                graph_path = get_graph_path(repo_name)
                if graph_path:
                    g = load_graph(repo_name)
                    nodes = len(g.get("nodes", []))
                    links = len(g.get("links", []))
                    print(f"    OK: {nodes} nodes, {links} links")
                else:
                    print(f"    OK (graph.json not found at expected path)")
            else:
                print(f"    Warning: exit code {result.returncode}", file=sys.stderr)
        except FileNotFoundError:
            print(f"    graphify CLI not found; skipping update", file=sys.stderr)
        except subprocess.TimeoutExpired:
            print(f"    Timeout; skipping", file=sys.stderr)


def cmd_import(repos=None):
    """Import graph structure into fabric for query expansion."""
    GRAPHS_DIR.mkdir(parents=True, exist_ok=True)
    targets = _repo_targets(repos)

    for repo_name in targets:
        graph_path = get_graph_path(repo_name)
        if not graph_path:
            print(f"  Skipping {repo_name}: no graph.json")
            continue

        g = load_graph(repo_name)
        if not g:
            continue

        # Copy the graph into the fabric
        dest = GRAPHS_DIR / f"{repo_name}-graph.json"
        dest.write_text(json.dumps(g))
        h = graph_hash(g)
        nodes = len(g.get("nodes", []))
        links = len(g.get("links", []))
        communities = len(set(n.get("community_name", "") for n in g.get("nodes", []) if n.get("community_name")))
        print(f"  {repo_name}: {nodes} nodes, {links} links, {communities} communities → {dest.name} (hash: {h})")

        # Write a hash file for staleness detection
        hash_path = GRAPHS_DIR / f"{repo_name}-graph.hash"
        hash_path.write_text(h)


def cmd_enrich(repos=None):
    """Enrich claims with graphify edges (call graph, communities)."""
    targets = _repo_targets(repos)

    for repo_name in targets:
        graph_path = get_graph_path(repo_name)
        if not graph_path:
            print(f"  Skipping {repo_name}: no graph.json")
            continue

        g = load_graph(repo_name)
        if not g:
            continue

        # Build adjacency from edges
        edges_from = defaultdict(list)  # node_id → [edges]
        edges_to = defaultdict(list)
        node_by_id = {}
        for n in g.get("nodes", []):
            node_by_id[n["id"]] = n
        for l in g.get("links", []):
            edges_from[l["source"]].append(l)
            edges_to[l["target"]].append(l)

        # For each claim, find graphify nodes that match symbols in the claim text
        enriched = 0
        for claim_path in CLAIMS_DIR.glob("claim-*.md"):
            fm, body = parse_frontmatter(claim_path)
            text = fm.get("statement", "") + " " + body

            # Find graphify nodes matching text
            graph_neighbors = set()
            for node_id, node in node_by_id.items():
                label = node.get("label", "").lower()
                if label and len(label) > 3 and label in text.lower():
                    # Found a match — add its graphify neighbors
                    for edge in edges_from.get(node_id, []):
                        rel_type = edge.get("relation", "")
                        if rel_type in EXPAND_EDGE_TYPES or rel_type in PROVENANCE_EDGE_TYPES:
                            target_node = node_by_id.get(edge["target"], {})
                            target_label = target_node.get("label", edge["target"])
                            graph_neighbors.add(f"{rel_type}:{target_label}")

                    for edge in edges_to.get(node_id, []):
                        rel_type = edge.get("relation", "")
                        if rel_type in EXPAND_EDGE_TYPES:
                            source_node = node_by_id.get(edge["source"], {})
                            source_label = source_node.get("label", edge["source"])
                            graph_neighbors.add(f"called_by:{source_label}")

            if graph_neighbors and "graph_edges:" not in (claim_path.read_text()):
                # Add graph_edges to frontmatter
                edge_lines = "\n".join(f'  - "{e}"' for e in sorted(graph_neighbors)[:8])
                text = claim_path.read_text()
                text = text.replace(
                    "\n---\n\n",
                    f"\ngraph_edges:\n{edge_lines}\n---\n\n",
                    1
                )
                claim_path.write_text(text)
                enriched += 1

        print(f"  {repo_name}: enriched {enriched} claims with graph_edges")


def cmd_diff(repos=None):
    """Detect stale claims by comparing stored graph hash with current."""
    targets = _repo_targets(repos)
    stale_count = 0

    for repo_name in targets:
        graph_path = get_graph_path(repo_name)
        hash_path = GRAPHS_DIR / f"{repo_name}-graph.hash"

        if not graph_path:
            print(f"  {repo_name}: no graph (skip)")
            continue

        g = load_graph(repo_name)
        current_hash = graph_hash(g)

        if hash_path.exists():
            stored_hash = hash_path.read_text().strip()
            if current_hash != stored_hash:
                print(f"  {repo_name}: STALE (stored: {hash_path.read_text()[:8]}, current: {current_hash[:8]})")
                print(f"    → Run: graphify update + re-ingest affected claims")
                stale_count += 1
            else:
                print(f"  {repo_name}: fresh ({current_hash[:8]})")
        else:
            print(f"  {repo_name}: no stored hash (run --import first)")
            stale_count += 1

    if stale_count:
        print(f"\n{stale_count} repo(s) with stale graphs")


def cmd_status():
    """Show graphify integration status."""
    print("=== Graphify Integration Status ===")
    print()

    for repo_name in _repo_targets():
        graph_path = get_graph_path(repo_name)
        hash_path = GRAPHS_DIR / f"{repo_name}-graph.hash"

        if graph_path:
            g = load_graph(repo_name)
            nodes = len(g.get("nodes", [])) if g else 0
            links = len(g.get("links", [])) if g else 0
            communities = len(set(n.get("community_name", "") for n in g.get("nodes", []) if n.get("community_name"))) if g else 0
            h = graph_hash(g) if g else "?"

            stored = hash_path.read_text()[:8] if hash_path.exists() else "not imported"
            fresh = "✓" if hash_path.exists() and stored == h[:8] else "✗"

            print(f"  {repo_name:20} graph: {graph_path.name:20} nodes={nodes:5} links={links:5} communities={communities:3} fresh={fresh}")
        else:
            print(f"  {repo_name:20} no graph found (run graphify update in repo)")

    # Check if graphify CLI is available
    try:
        subprocess.run(["graphify", "--version"], capture_output=True, timeout=5)
        print(f"\n  graphify CLI: available")
    except (FileNotFoundError, subprocess.TimeoutExpired):
        print(f"\n  graphify CLI: NOT available")


def main():
    parser = argparse.ArgumentParser(description="Graphify bridge for the wiki fabric")
    parser.add_argument("--update", action="store_true", help="Run graphify update on connected repos")
    parser.add_argument("--import", dest="import_graphs", action="store_true", help="Import graph structure into fabric")
    parser.add_argument("--enrich", action="store_true", help="Enrich claims with graphify edges")
    parser.add_argument("--diff", action="store_true", help="Detect stale claims via graph hash diff")
    parser.add_argument("--status", action="store_true", help="Show integration status")
    parser.add_argument("--repo", help="Limit to a specific repo")
    parser.add_argument("--all", action="store_true", help="Run full pipeline: update → import → enrich → diff")
    args = parser.parse_args()

    # Gated integration: refuses to run unless enabled in fabric.yaml
    from fabric_config import get_config, is_integration_active
    config = get_config()
    if not is_integration_active(config, "graphify"):
        print("Graphify integration is not enabled.")
        print("Enable it in fabric.yaml:")
        print("  integrations:")
        print("    graphify:")
        print("      enabled: true")
        print("      graph_dir: graphify-out   # per-repo override supported in repos:")
        print("")
        print("Then run: wf install --with-graphify (or configure graph_dir per repo in repos:)")
        return

    repos = [args.repo] if args.repo else None

    if args.all:
        cmd_update(repos)
        print()
        cmd_import(repos)
        print()
        cmd_enrich(repos)
        print()
        cmd_diff(repos)
    elif args.update:
        cmd_update(repos)
    elif args.import_graphs:
        cmd_import(repos)
    elif args.enrich:
        cmd_enrich(repos)
    elif args.diff:
        cmd_diff(repos)
    elif args.status:
        cmd_status()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()