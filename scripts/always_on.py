#!/usr/bin/env python3
# always_on.py — write/remove the wiki-fabric always-on instruction block in
# CLAUDE.md / AGENTS.md (project or user level). Modeled on graphify's
# `claude install` / `graphify claude install`.
#
# Usage:
#   python3 scripts/always_on.py install [--file CLAUDE.md|AGENTS.md] [--user]
#   python3 scripts/always_on.py uninstall [--file ...] [--user]
#   python3 scripts/always_on.py status [--file ...] [--user]

import re
import sys
import argparse
from pathlib import Path

BLOCK_START = "## wiki-fabric"
MARKER_START = "<!-- wiki-fabric-always-on-start -->"
MARKER_END = "<!-- wiki-fabric-always-on-end -->"

_FABRIC_ROOT = Path(__file__).parent.parent
_tpl = (_FABRIC_ROOT / "system" / "always-on" / "wiki-fabric-block.md").read_text(
    encoding="utf-8"
).strip()
# Strip the template's own frontmatter (lint contract only); the managed block
# is instructions, not a fabric note.
_tpl = re.sub(r"^---\n.*?\n---\n", "", _tpl, flags=re.DOTALL).strip()
_BLOCK_TEMPLATE = _tpl


def _target(path_arg: str | None, user: bool) -> Path:
    if path_arg:
        return Path(path_arg)
    if user:
        candidates = [Path.home() / ".claude" / "CLAUDE.md", Path.home() / "CLAUDE.md"]
        for c in candidates:
            if c.exists():
                return c
        return candidates[0]
    # project level: AGENTS.md preferred, CLAUDE.md fallback
    for name in ("AGENTS.md", "CLAUDE.md"):
        if Path(name).exists():
            return Path(name)
    return Path("AGENTS.md")


def _block_text() -> str:
    return f"{MARKER_START}\n{_BLOCK_TEMPLATE.strip()}\n{MARKER_END}"


def _has_marker(content: str) -> bool:
    return MARKER_START in content


def install(path: Path) -> str:
    if path.exists():
        content = path.read_text(encoding="utf-8")
        if "wiki-fabric" in content and not _has_marker(content):
            return f"already registered in {path} (wiki-fabric mentioned; no marker — skipping to avoid duplication)"
        if _has_marker(content):
            # refresh in place (block content may have been updated)
            new = re.sub(
                rf"{re.escape(MARKER_START)}.*?{re.escape(MARKER_END)}",
                _block_text(), content, flags=re.DOTALL,
            )
            if new == content:
                return f"already installed in {path}"
            path.write_text(new, encoding="utf-8")
            return f"updated block in {path}"
        new = content.rstrip() + "\n\n" + _block_text() + "\n"
        path.write_text(new, encoding="utf-8")
        return f"appended block to {path}"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_block_text() + "\n", encoding="utf-8")
    return f"created {path}"


def uninstall(path: Path) -> str:
    if not path.exists():
        return f"no {path} — nothing to remove."
    content = path.read_text(encoding="utf-8")
    if not _has_marker(content):
        return f"wiki-fabric block not found in {path}."
    new = re.sub(rf"{re.escape(MARKER_START)}.*?{re.escape(MARKER_END)}\n?", "", content, flags=re.DOTALL).strip()
    path.write_text(new + "\n", encoding="utf-8")
    return f"removed block from {path}"


def status(path: Path) -> str:
    if not path.exists():
        return f"{path}: not present (not installed)"
    content = path.read_text(encoding="utf-8")
    out = ""
    if _has_marker(content):
        out += f"{path}: installed"
    elif "wiki-fabric" in content:
        out += f"{path}: wiki-fabric mentioned but no managed block"
    else:
        out += f"{path}: not installed"
    # other detected managed blocks (co-existence audit)
    others = []
    for tool, marker in (("graphify", "## graphify"), ("opencode", "## opencode")):
        if marker in content and "wiki-fabric" not in content:
            others.append(marker[2:])
        elif marker in content:
            others.append(marker)
    others = sorted(set(others) - {"## wiki-fabric"})
    if others:
        out += f"\nother managed blocks detected: {', '.join(others)}"
    return out


def main():
    parser = argparse.ArgumentParser(description="wiki-fabric always-on instructions")
    parser.add_argument("cmd", choices=["install", "uninstall", "status"])
    parser.add_argument("--file", help="Target file (default: AGENTS.md/CLAUDE.md project-level, ~/.claude/CLAUDE.md with --user)")
    parser.add_argument("--user", action="store_true", help="Install at user level (~/.claude/CLAUDE.md)")
    args = parser.parse_args()

    target = _target(args.file, args.user)
    if args.cmd == "install":
        print(install(target))
    elif args.cmd == "uninstall":
        print(uninstall(target))
    else:
        print(status(target))


if __name__ == "__main__":
    main()