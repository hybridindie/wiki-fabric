#!/usr/bin/env python3
"""Prepare src/wiki_fabric/_harness for packaging (#118 phase-1).

Copies the harness tree (scripts/, system/, templates/, schemas/, references/,
evaluations/, global/, plus root-level config examples) into
src/wiki_fabric/_harness so setuptools ships it as package data.
Idempotent: wipes and re-copies.
"""
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
DEST = REPO / "src" / "wiki_fabric" / "_harness"

COPY_TOP = [
    "scripts",
    "system",
    "templates",
    "schemas",
    "references",
    "evaluations",
    "global",
]
COPY_FILES = [
    "okf-base.yaml",
    "fabric.yaml.example",
    "AGENTS.md",
    "index.md",
]
SKIP_DIRS = {"__pycache__", ".pytest_cache", ".venv", "node_modules", "wiki",
             # fabric content (gitignored) — never ships, even when present on disk
             "entities", "graphs"}


def main():
    if DEST.exists():
        shutil.rmtree(DEST)
    DEST.mkdir(parents=True)
    missing = [top for top in COPY_TOP if not (REPO / top).exists()]
    if missing:
        print(f"FATAL: packaged trees missing from repo: {missing}", file=sys.stderr)
        print("Run from a full checkout — a release built without these ships broken.",
              file=sys.stderr)
        return 1
    for top in COPY_TOP:
        src = REPO / top
        shutil.copytree(src, DEST / top,
                        ignore=shutil.ignore_patterns(*SKIP_DIRS, "*.pyc"))
    for f in COPY_FILES:
        src = REPO / f
        if src.exists():
            shutil.copy(src, DEST / f)
    n = sum(1 for p in DEST.rglob("*") if p.is_file())
    print(f"packaged harness tree: {n} files -> {DEST.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    main()
