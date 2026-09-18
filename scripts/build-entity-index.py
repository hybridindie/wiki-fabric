#!/usr/bin/env python3
# build-entity-index.py — Build a code-symbol entity index from source repos
#
# Usage:
#   python3 scripts/build-entity-index.py                    # index all connected repos
#   python3 scripts/build-entity-index.py --repo my-project  # index one repo
#   python3 scripts/build-entity-index.py --dry-run          # show what would be indexed
#
# Parses Python (AST) and GDScript (regex) from connected project repos,
# produces global/entities/*.md pages with symbol→file:line mappings.
# Claims referencing these symbols get auditable code locators.

import sys
import re
import ast
import json
import argparse
from pathlib import Path
from datetime import date

sys.path.insert(0, str(Path(__file__).parent))
from fabric_config import get_config, FABRIC_ROOT, resolve_repo_path, get_all_repo_names, get_repo_graph_dir, get_ignores, is_ignored

VAULT_ROOT = FABRIC_ROOT
ENTITIES_DIR = VAULT_ROOT / "global" / "entities"

# Directories to skip
SKIP_DIRS = {".git", ".obsidian", ".opencode", "node_modules", ".venv", "venv",
             "__pycache__", ".godot", "graphify-out", "uv.lock", ".forge",
             ".github", ".claude", ".playwright-mcp"}

# File extensions to index
PY_EXTENSIONS = {".py"}
GD_EXTENSIONS = {".gd"}


def extract_python_symbols(file_path, repo_name):
    """Extract classes, functions, and constants from a Python file via AST."""
    try:
        source = file_path.read_text(encoding="utf-8", errors="replace")
        tree = ast.parse(source)
    except SyntaxError:
        return []

    rel_path = str(file_path)
    symbols = []

    # Top-level definitions
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.ClassDef):
            methods = [n.name for n in node.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
            symbols.append({
                "kind": "class",
                "name": node.name,
                "file": rel_path,
                "line": node.lineno,
                "repo": repo_name,
                "children": methods,
                "language": "python",
            })
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            symbols.append({
                "kind": "function",
                "name": node.name,
                "file": rel_path,
                "line": node.lineno,
                "repo": repo_name,
                "children": [],
                "language": "python",
            })
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id.isupper():
                    symbols.append({
                        "kind": "constant",
                        "name": target.id,
                        "file": rel_path,
                        "line": node.lineno,
                        "repo": repo_name,
                        "children": [],
                        "language": "python",
                    })

    return symbols


def extract_gdscript(file_path, repo_name):
    """Extract classes, functions, signals, and constants from a GDScript file via regex."""
    try:
        source = file_path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return []

    rel_path = str(file_path)
    symbols = []

    # class_name declarations
    for m in re.finditer(r'^class_name\s+(\w+)', source, re.MULTILINE):
        line_num = source[:m.start()].count('\n') + 1
        symbols.append({
            "kind": "class",
            "name": m.group(1),
            "file": rel_path,
            "line": line_num,
            "repo": repo_name,
            "children": [],
            "language": "gdscript",
        })

    # extends + class definitions (inner classes)
    for m in re.finditer(r'^class\s+(\w+):', source, re.MULTILINE):
        line_num = source[:m.start()].count('\n') + 1
        symbols.append({
            "kind": "inner_class",
            "name": m.group(1),
            "file": rel_path,
            "line": line_num,
            "repo": repo_name,
            "children": [],
            "language": "gdscript",
        })

    # func declarations
    for m in re.finditer(r'^func\s+(\w+)', source, re.MULTILINE):
        line_num = source[:m.start()].count('\n') + 1
        symbols.append({
            "kind": "function",
            "name": m.group(1),
            "file": rel_path,
            "line": line_num,
            "repo": repo_name,
            "children": [],
            "language": "gdscript",
        })

    # signal declarations
    for m in re.finditer(r'^signal\s+(\w+)', source, re.MULTILINE):
        line_num = source[:m.start()].count('\n') + 1
        symbols.append({
            "kind": "signal",
            "name": m.group(1),
            "file": rel_path,
            "line": line_num,
            "repo": repo_name,
            "children": [],
            "language": "gdscript",
        })

    # const declarations
    for m in re.finditer(r'^const\s+(\w+)', source, re.MULTILINE):
        line_num = source[:m.start()].count('\n') + 1
        symbols.append({
            "kind": "constant",
            "name": m.group(1),
            "file": rel_path,
            "line": line_num,
            "repo": repo_name,
            "children": [],
            "language": "gdscript",
        })

    return symbols


def index_repo(repo_name, repo_path, dry_run=False, ignores=None):
    """Walk a repo and extract all code symbols. fabric.yaml ignore rules apply."""
    if not repo_path.exists():
        print(f"  Repo not found: {repo_path}", file=sys.stderr)
        return []

    symbols = []
    files_indexed = 0
    ignores = ignores or {"globs": [], "compiled": []}

    for f in repo_path.rglob("*"):
        # Skip excluded dirs
        if any(part in SKIP_DIRS for part in f.parts):
            continue
        if not f.is_file():
            continue
        # fabric.yaml ignore: globs + regexes (relative to repo root)
        if is_ignored(f.relative_to(repo_path).as_posix(), ignores):
            continue

        ext = f.suffix
        if ext in PY_EXTENSIONS:
            syms = extract_python_symbols(f, repo_name)
            symbols.extend(syms)
        elif ext in GD_EXTENSIONS:
            syms = extract_gdscript(f, repo_name)
            symbols.extend(syms)

    return symbols


def write_entity_pages(symbols, repo_name, dry_run=False):
    """Group symbols by module/file and write entity pages."""
    ENTITIES_DIR.mkdir(parents=True, exist_ok=True)
    repo_path = REPO_PATHS[repo_name]

    # Group by file
    by_file = {}
    for sym in symbols:
        by_file.setdefault(sym["file"], []).append(sym)

    pages_created = 0
    for file_path, file_symbols in sorted(by_file.items()):
        # Create entity page slug from file path
        # e.g. mcp_server/harness.py → entity-mcp-server-harness
        slug = file_path.replace(str(repo_path.parent) + "/", "").replace("/", "-")
        slug = slug.rsplit(".", 1)[0]  # strip extension
        slug = re.sub(r'[^a-z0-9]+', '-', slug.lower()).strip('-')[:80]

        entity_path = ENTITIES_DIR / f"entity-{slug}.md"

        # Group symbols by kind
        by_kind = {}
        for sym in file_symbols:
            by_file.setdefault(sym["kind"], []).append(sym)
        by_kind = {}
        for sym in file_symbols:
            by_kind.setdefault(sym["kind"], []).append(sym)

        # Build symbol table
        symbol_rows = []
        for sym in sorted(file_symbols, key=lambda x: x["line"]):
            children = f" ({', '.join(sym['children'][:5])})" if sym.get("children") else ""
            symbol_rows.append(f"| {sym['kind']} | `{sym['name']}`{children} | L{sym['line']} |")

        repo_rel = Path(file_path).relative_to(REPO_PATHS[repo_name])

        content = f"""---
type: entity
title: {Path(file_path).name} symbols
repo: {repo_name}
file: {repo_path.name}/{repo_rel}
language: {file_symbols[0]["language"] if file_symbols else "unknown"}
symbol_count: {len(file_symbols)}
created: {date.today().isoformat()}
---

# Entity Index: `{Path(file_path).name}`

**Repo:** {repo_name} · **Path:** `{repo_rel}` · **Language:** {file_symbols[0]["language"] if file_symbols else "?"}

| Kind | Symbol | Line |
|------|--------|------|
{chr(10).join(symbol_rows)}
"""

        if not dry_run:
            entity_path.write_text(content)
            pages_created += 1

    return pages_created


def enrich_claims_with_code_locators(symbols, dry_run=False):
    """Post-process: enrich claims that mention indexed code symbols."""
    # Build a symbol lookup with repo-relative paths
    symbol_map = {}
    for sym in symbols:
        symbol_map.setdefault(sym["name"], []).append(sym)

    # Find claims mentioning indexed symbols
    enriched = 0
    for claim_path in (VAULT_ROOT / "evidence" / "claims").glob("claim-*.md"):
        text = claim_path.read_text()
        body = text

        # Find symbols mentioned in this claim
        mentioned = []
        for sym_name, occurrences in symbol_map.items():
            if sym_name in text and len(sym_name) > 3:  # skip short names
                first = occurrences[0]
                # Use repo-relative path
                file_rel = Path(first["file"]).relative_to(REPO_PATHS[first["repo"]])
                mentioned.append(f"`{sym_name}` ({first['repo']}:{file_rel}:{first['line']})")

        if mentioned and "code_symbols:" not in text:
            # Add code_symbols section to frontmatter (at top level, before closing ---)
            symbol_lines = "\n".join(f'  - "{s}"' for s in mentioned[:5])
            # Insert as top-level key before the last ---
            text = text.replace(
                "\n---\n\n",
                f"\ncode_symbols:\n{symbol_lines}\n---\n\n",
                1
            )
            if not dry_run:
                claim_path.write_text(text)
                enriched += 1

    return enriched


def main():
    parser = argparse.ArgumentParser(description="Build code-symbol entity index from source repos")
    parser.add_argument("--repo", help="Index only a specific repo (default: all connected)")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be indexed")
    parser.add_argument("--enrich", action="store_true", help="Also enrich claims with code locators")
    parser.add_argument("--skip-enrich", action="store_true", help="Skip claim enrichment")
    args = parser.parse_args()

    config = get_config()
    repos_to_index = [args.repo] if args.repo else get_all_repo_names(config)

    # Map repo name → resolved path (write_entity_pages and relative-path math
    # depend on this module-level mapping)
    global REPO_PATHS
    REPO_PATHS = {}
    for name in repos_to_index:
        rp = resolve_repo_path(config, name)
        if rp:
            REPO_PATHS[name] = rp

    print("=== Building entity index ===")
    print()

    all_symbols = []
    total_symbols = 0

    for repo_name in repos_to_index:
        repo_path = resolve_repo_path(config, repo_name)
        if not repo_path or not repo_path.exists():
            print(f"Skipping {repo_name}: repo not found at {repo_path}")
            continue

        symbols = index_repo(repo_name, repo_path, dry_run=False, ignores=get_ignores(config, repo_name))

        # Count by kind
        by_kind = {}
        for sym in symbols:
            by_kind[sym["kind"]] = by_kind.get(sym["kind"], 0) + 1

        print(f"  {repo_name}: {len(symbols)} symbols in {repo_path.name}")
        for kind, count in sorted(by_kind.items()):
            print(f"    {kind}: {count}")

        # Write entity pages
        if not args.dry_run:
            pages = write_entity_pages(symbols, repo_name)
            print(f"    → {pages} entity pages written")
        else:
            print(f"    → [DRY RUN] would write entity pages")

        all_symbols.extend(symbols)
        total_symbols += len(symbols)

    print(f"\nTotal symbols indexed: {total_symbols}")

    # Claim enrichment
    if not args.skip_enrich and all_symbols:
        print(f"\nEnriching claims with code locators...")
        enriched = enrich_claims_with_code_locators(all_symbols, args.dry_run)
        if enriched:
            print(f"  Enriched {enriched} claims with code_symbols")
        else:
            print(f"  No claims enriched (symbols not found in claim text)")

    if args.dry_run:
        print("\n[DRY RUN] No files written")


if __name__ == "__main__":
    main()