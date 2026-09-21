#!/usr/bin/env python3
# rebuild-index.py — Rebuild registry/catalog.json from actual vault files
#
# Usage: python3 scripts/rebuild-index.py

import sys
import re
from pathlib import Path
from datetime import date, datetime, timezone
import json

try:
    import yaml
    HAVE_YAML = True
except ImportError:
    HAVE_YAML = False

sys.path.insert(0, str(Path(__file__).parent))
from fabric_config import get_config, get_ignores, is_ignored
from wf_common import parse_frontmatter

VAULT_ROOT = Path(__file__).parent.parent
INDEX_PATH = VAULT_ROOT / "registry" / "catalog.json"

SKIP_PARTS = {".git", ".obsidian", ".opencode", "__pycache__", ".venv", "venv", "node_modules", "templates", "schemas", "evaluations", "system", "examples", "scripts", "tests"}
SKIP_DIRS_IN_EVIDENCE = {"raw", "traces"}

LINK_RE = re.compile(r"\[\[([^\]|]+)(?:\|[^\]]+)?\]\]")


def first_summary_line(body):
    """Extract a one-line summary from the body, stripping wikilinks."""
    for line in body.split("\n"):
        line = line.strip()
        if line and not line.startswith("#") and not line.startswith("---") and not line.startswith("[["):
            # Strip wikilinks and markdown emphasis for a clean summary
            clean = re.sub(r'\[\[([^\]|]+)(?:\|[^\]]+)?\]\]', r'\1', line)
            clean = re.sub(r'\*\*([^*]+)\*\*', r'\1', clean)
            clean = clean[:100]
            return clean
    return ""


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


def main():
    import argparse
    import os
    parser = argparse.ArgumentParser(description="Rebuild registry catalog (catalog.json)")
    parser.add_argument("--json", action="store_true", help="Print the JSON registry to stdout instead of writing files")
    parser.add_argument("--root", default=None, help="Fabric root (default: repo parent of this script, or $WIKI_FABRIC_ROOT)")
    args = parser.parse_args()

    global VAULT_ROOT, INDEX_PATH
    VAULT_ROOT = Path(args.root or os.environ.get("WIKI_FABRIC_ROOT", VAULT_ROOT)).resolve()
    INDEX_PATH = VAULT_ROOT / "registry" / "catalog.json"

    categories = scan_vault()
    registry = build_catalog(categories)

    catalog_path = write_catalog(registry)

    total = registry["total"]
    print(f"Rebuilt {catalog_path.relative_to(VAULT_ROOT)}")
    print(f"  Pages cataloged: {total}")
    for name, count in sorted(registry["counts"].items()):
        print(f"  {name}: {count}")

    if args.json:
        print(json.dumps(registry, indent=2))


if __name__ == "__main__":
    main()