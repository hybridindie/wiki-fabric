#!/usr/bin/env python3
# rebuild-index.py — Rebuild registry/catalog.json from actual vault files
#
# Usage: python3 scripts/cmd/rebuild-index.py

import sys
import sys as _s, pathlib as _p
_HERE = _p.Path(__file__).resolve().parent
# Explicit import bootstrap: this script's own dir (same-dir siblings)
# + scripts/lib (shared modules). No shotgun path injection.
for _dir in (_HERE, _HERE.parent / "lib"):
    if str(_dir) not in _s.path:
        _s.path.insert(0, str(_dir))
import re
from pathlib import Path
from datetime import date, datetime, timezone
import json

try:
    import yaml
    HAVE_YAML = True
except ImportError:
    HAVE_YAML = False

from fabric_config import get_config, get_ignores, is_ignored, CORPUS_ROOT
from wf_common import parse_frontmatter, SKIP_PARTS


def _default_root():
    """Root to index — paths.py (#152). The harness tree is NEVER a fabric
    (its patterns/evidence dirs are gitkeeped skeletons): the veto comes
    first, then the isolated-fabric heuristic for eval-stability's flat
    temp fabrics. --root / WIKI_FABRIC_ROOT still override in main()."""
    from paths import find_corpus_root, is_harness_tree
    own = (Path(__file__).resolve().parent).parent.parent  # scripts/cmd -> scripts -> fabric root
    if is_harness_tree(own):
        return find_corpus_root(own)
    # Isolated-fabric heuristic (eval-stability copies the script into a flat
    # temp fabric): content dirs at the root AND no corpus/ subdir.
    if (own / "patterns").is_dir() or (own / "evidence").is_dir():
        if not (own / "corpus").is_dir():
            return own  # isolated fabric (content at its root)
    return find_corpus_root(own)


# The catalog is a corpus artifact; the old harness-root default detached it
# from the corpus.
VAULT_ROOT = _default_root()
INDEX_PATH = VAULT_ROOT / "registry" / "catalog.json"

# SKIP_PARTS: shared corpus-walk exclusion set (wf_common, #155-C) — the
# catalog should see the same corpus the retrievers see. Extra, index-only
# skips live in scan_vault below.
SKIP_DIRS_IN_EVIDENCE = {"raw", "traces"}

LINK_RE = re.compile(r"\[\[([^\]|]+)(?:\|[^\]]+)?\]\]")
def scan_vault():
    """Walk the vault and categorize pages by directory."""
    categories = {
        "sources": [],
        "source_summaries": [],
        "claims": [],
        "concepts": [],
        "experience_events": [],
        "patterns": [],
        "anti_patterns": [],
        "skills": [],
        "decisions": [],
        "promotions": [],
        "other": [],
    }

    _ig = get_ignores(get_config())
    for p in VAULT_ROOT.rglob("*.md"):
        rel = p.relative_to(VAULT_ROOT)
        parts = rel.parts
        if is_ignored(rel.as_posix(), _ig):
            continue

        # Skip system dirs
        if any(x in SKIP_PARTS for x in parts):
            continue
        # Skip raw captures (immutable, not cataloged)
        if "raw" in parts:
            continue
        # Skip evaluation fixtures
        if "evaluations" in parts:
            continue
        # Skip traces (change-sets are audit artifacts)
        if "traces" in parts:
            continue
        # Skip entity pages (too many, reference-only)
        if "entities" in parts and "global" in parts:
            continue

        fm, body = parse_frontmatter(p)
        stem = rel.stem.lower()
        entry = (stem, rel, fm, body)

        rel_str = rel.as_posix()

        if rel_str.startswith("evidence/sources/"):
            categories["sources"].append(entry)
        elif rel_str.startswith("evidence/source-summaries/"):
            categories["source_summaries"].append(entry)
        elif rel_str.startswith("evidence/claims/"):
            categories["claims"].append(entry)
        elif "experience-events" in rel_str:
            categories["experience_events"].append(entry)
        elif "decisions" in rel_str:
            categories["decisions"].append(entry)
        elif rel_str.startswith("concepts/") or "domains/" in parts[:2] and "concepts" in parts:
            categories["concepts"].append(entry)
        elif rel_str.startswith("patterns/"):
            categories["patterns"].append(entry)
        elif rel_str.startswith("anti-patterns/"):
            categories["anti_patterns"].append(entry)
        elif rel_str.startswith("skills/"):
            categories["skills"].append(entry)
        elif rel_str.startswith("registry/promotions/"):
            categories["promotions"].append(entry)
        elif rel.name in ("catalog.json", "log.md", "README.md", "CONTRIBUTING.md", "AGENTS.md"):
            continue  # skip hubs and meta files
        else:
            categories["other"].append(entry)

    return categories


def build_catalog(categories):
    """Single machine registry: registry/catalog.json.

    Replaces: catalog.md, index.json, catalog.json, catalog.json,
    catalog.json. Written by scripts, read by scripts/agents — JSON because
    it is never hand-authored (OKF rule: script-written + script-read -> JSON).
    """
    import json

    def entry(stem, rel, fm):
        fm = fm or {}
        d = {
            "id": str(fm.get("id") or stem),
            "stem": stem,
            "path": str(rel),
            "type": fm.get("type"),
            "title": fm.get("title"),
            "scope": (fm or {}).get("scope") or (
                "domain" if rel.as_posix().startswith("domains/")
                else "project" if rel.as_posix().startswith("projects/")
                else "global"
            ),
        }
        if fm.get("description"):
            d["description"] = str(fm["description"])
        elif fm.get("statement"):
            d["description"] = str(fm["statement"])[:140]
        for field in ("status", "maturity", "confidence", "review_after", "last_verified",
                      "stale_after", "sha256", "source_path", "summary"):
            v = fm.get(field)
            if v is None:
                continue
            d[field] = v.isoformat() if hasattr(v, "isoformat") else v
        return d

    pages = []
    counts = {}
    for name, entries in sorted(categories.items()):
        if entries:
            counts[name] = len(entries)
        for stem, rel, fm, _body in entries:
            page = entry(stem, rel, fm)
            page["category"] = name
            pages.append(page)
    pages.sort(key=lambda p: (p.get("category") or "", p["stem"]))

    registry = {
        "$schema": "wiki-fabric/registry-v1",
        # date-grain (not seconds): makes rebuilds byte-deterministic (G2 gate),
        # while still conveying freshness to consumers
        "generated": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "total": len(pages),
        "counts": dict(sorted(counts.items())),
        "pages": pages,
    }
    return registry


def write_catalog(registry):
    import json
    out = VAULT_ROOT / "registry" / "catalog.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(registry, indent=2, ensure_ascii=False))
    return out


def build_thread_index():
    """#102: derive registry/threads.json from evidence/ alone — chat/PR
    records are graph nodes (frontmatter: kind, session, project,
    files_touched, pr), claims join via originated_in/decided_in relations.
    Rebuildable, no hand-maintenance; absent captures → clean no-op."""
    from wf_common import parse_frontmatter as _pf
    raw = VAULT_ROOT / "evidence" / "raw"
    nodes = []
    if raw.is_dir():
        for p in sorted(raw.rglob("*.md")):
            fm, _ = parse_frontmatter(p)
            kind = fm.get("kind")
            if kind not in ("chat-session", "pr-record"):
                continue
            node = {
                "file": p.relative_to(VAULT_ROOT).as_posix(),
                "kind": kind,
                "project": fm.get("project", ""),
                "session": str(fm.get("session") or ""),
                "harness": fm.get("harness", ""),
            }
            if kind == "pr-record":
                node["pr"] = fm.get("pr")
                node["pr_state"] = fm.get("pr_state", "")
                node["source_repo"] = fm.get("source_repo", "")
            files = fm.get("files_touched") or []
            if isinstance(files, list):
                node["files_touched"] = [str(f).strip('"') for f in files][:20]
            if fm.get("merged_at"):
                node["merged_at"] = str(fm["merged_at"])[:10]
            rel_sessions = fm.get("related_sessions") or []
            if isinstance(rel_sessions, list) and rel_sessions:
                node["related_sessions"] = [str(s).strip('"') for s in rel_sessions][:20]
            nodes.append(node)

    # claims → session/PR edges (from claim frontmatter relations)
    # target slug must match ingest's truncation (source_slug[:80]) — long
    # chat-capture filenames otherwise never join (sim finding #11)
    edges = []
    claims_dir = VAULT_ROOT / "evidence" / "claims"
    if claims_dir.is_dir():
        for cp in sorted(claims_dir.glob("claim-*.md")):
            fm, _ = parse_frontmatter(cp)
            rels = fm.get("relations") or []
            if not isinstance(rels, list):
                continue
            for r in rels:
                if not isinstance(r, dict):
                    continue
                if r.get("type") in ("originated_in", "decided_in", "validated_in"):
                    target = str(r.get("target", "")).strip('"[]')
                    edges.append({
                        "claim": cp.stem.lower(),
                        "type": r.get("type"),
                        "target": target[:83],  # 'src-' + 80-char slug cap
                    })

    # session ↔ session continuity edges (#102c)
    for node in nodes:
        for other in node.get("related_sessions", []):
            edges.append({
                "claim": None,
                "type": "continues",
                "source_session": node.get("session", ""),
                "target": other,
            })
    index = {
        "$schema": "wiki-fabric/threads-v1",
        "generated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "node_count": len(nodes),
        "edge_count": len(edges),
        "nodes": nodes,
        "edges": edges,
    }
    out = VAULT_ROOT / "registry" / "threads.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(index, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return out, len(nodes), len(edges)


def main():
    import argparse
    import os
    parser = argparse.ArgumentParser(description="Rebuild registry catalog (catalog.json)")
    parser.add_argument("--json", action="store_true", help="Print the JSON registry to stdout instead of writing files")
    parser.add_argument("--root", default=None, help="Fabric root (default: repo parent of this script, or $WIKI_FABRIC_ROOT)")
    parser.add_argument("--no-threads", action="store_true", help="Skip the thread index build (#102)")
    args = parser.parse_args()

    global VAULT_ROOT, INDEX_PATH
    import os as _os
    root_arg = args.root or _os.environ.get("WIKI_FABRIC_ROOT")
    if not root_arg:
        # canonical resolution (fabric_config chain) — the module default can
        # land on the harness when run from the toolbox repo (#e2e finding)
        from fabric_config import CORPUS_ROOT
        root_arg = str(CORPUS_ROOT)
    VAULT_ROOT = Path(root_arg).resolve()
    INDEX_PATH = VAULT_ROOT / "registry" / "catalog.json"

    categories = scan_vault()
    registry = build_catalog(categories)

    catalog_path = write_catalog(registry)

    total = registry["total"]
    print(f"Rebuilt {catalog_path.relative_to(VAULT_ROOT)}")
    print(f"  Pages cataloged: {total}")
    for name, count in sorted(registry["counts"].items()):
        print(f"  {name}: {count}")

    if not args.no_threads:
        tpath, nn, ne = build_thread_index()
        print(f"  Threads: {nn} node(s), {ne} edge(s) → {tpath.name}")

    if args.json:
        print(json.dumps(registry, indent=2))


if __name__ == "__main__":
    main()