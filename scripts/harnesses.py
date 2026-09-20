#!/usr/bin/env python3
# harnesses.py — Registry of supported agent harnesses and their integration
# surfaces. One spec per harness; `wf harness install` writes the wiki-fabric
# always-on block + skills into every detected harness.
#
# Integration surfaces (any combination per harness):
#   instructions : a markdown file the harness reads at session start
#   skills_dir   : a directory of SKILL.md folders the harness loads
#   config       : a structured config the harness merges (json/toml)
#   plugin       : a code plugin (js/ts) the harness executes
#
# The always-on block and skill content are harness-agnostic markdown — the
# only per-tool work is *where* files land.

import json
import os
import sys
from pathlib import Path

BLOCK_URL = "system/always-on/wiki-fabric-block.md"

# (key, display name, instruction files, skills dir, marker)
SPECS = [
    {
        "key": "claude",
        "name": "Claude Code",
        "instructions": ["CLAUDE.md", "AGENTS.md"],
        "user_instructions": [".claude/CLAUDE.md", "CLAUDE.md"],
        "skills_dir": ".claude/skills",          # .claude/skills/<name>/SKILL.md
        "detect": [".claude", "CLAUDE.md"],
    },
    {
        "key": "opencode",
        "name": "opencode",
        "instructions": ["AGENTS.md"],
        "config": "opencode.json",              # additive merge (bootstrap)
        "plugin": "system/opencode/plugins/wiki-fabric.js",
        "skills_dir": ".opencode/skill",        # .opencode/skill/<name>/SKILL.md
        "detect": ["opencode.json", ".opencode"],
    },
    {
        "key": "codex",
        "name": "OpenAI Codex CLI",
        "instructions": ["AGENTS.md"],          # read natively
        "config": "codex.toml",                 # ~ only; skip project merge
        "detect": [".codex", "AGENTS.md"],
        "user_only": True,                      # no project-level config merge
    },
    {
        "key": "copilot",
        "name": "GitHub Copilot",
        "instructions": [".github/copilot-instructions.md"],
        "detect": [".github/copilot-instructions.md", ".github"],
    },
    {
        "key": "gemini",
        "name": "Gemini CLI",
        "instructions": ["GEMINI.md"],
        "detect": ["GEMINI.md", ".gemini"],
    },
    {
        "key": "cursor",
        "name": "Cursor",
        "instructions": [".cursor/rules/wiki-fabric.mdc"],
        "detect": [".cursor"],
    },
    {
        "key": "aider",
        "name": "Aider",
        "instructions": ["CONVENTIONS.md"],
        "detect": [".aider*", "CONVENTIONS.md"],
    },
    {
        "key": "zed",
        "name": "Zed",
        "instructions": [".rules"],
        "detect": [".rules"],
    },
    {
        "key": "cline",
        "name": "Cline",
        "instructions": [".clinerules/wiki-fabric.md"],
        "detect": [".clinerules"],
    },
    {
        "key": "windsurf",
        "name": "Windsurf",
        "instructions": [".windsurf/rules/wiki-fabric.md"],
        "detect": [".windsurf"],
    },
    {
        "key": "pi",
        "name": "Pi",
        "instructions": ["AGENTS.md", "PI.md"],
        "detect": [".pi", "PI.md"],
    },
]


def spec_by_key(key):
    for spec in SPECS:
        if spec["key"] == key:
            return spec
    return None


def detect_installed(project_root):
    """Harnesses with a marker in this project. Returns [spec, ...] — always
    includes the AGENTS.md-reading tools (they read the file we write anyway)."""
    root = Path(project_root)
    found, agentic = [], []
    for spec in SPECS:
        hits = any(list(root.glob(pat)) for pat in spec.get("detect", []))
        if hits:
            found.append(spec)
        if "AGENTS.md" in spec.get("instructions", []):
            agentic.append(spec)
    for spec in agentic:
        if spec not in found:
            found.append(spec)
    return found


def marker_for(spec):
    """Managed-block marker: '## wiki-fabric (<harness-key>)'."""
    return f"## wiki-fabric ({spec['key']})"


def end_marker_for(spec):
    """Closing tag — deliberately does NOT contain marker_for text, so marker
    counting / splitting is unambiguous."""
    return f"<!-- /wiki-fabric:{spec['key']} -->"


def install_instructions(spec, project_root, block_text, force=False):
    """Marker-delimited append into each instruction file. Returns list of
    written paths."""
    written = []
    root = Path(project_root)
    for name in spec.get("instructions", []):
        f = root / name
        f.parent.mkdir(parents=True, exist_ok=True)
        text = f.read_text(encoding="utf-8") if f.exists() else ""
        marker = marker_for(spec)
        if marker in text and not force:
            continue  # already installed
        # strip any previous managed block, re-append fresh
        if marker in text:
            pre = text.split(marker)[0].rstrip() + "\n"
            text = pre
        block = f"{marker}\n{block_text.strip()}\n{end_marker_for(spec)}\n"
        f.write_text(text.rstrip() + "\n\n" + block if text.strip() else block,
                     encoding="utf-8")
        written.append(f)
    return written


def install_skills(spec, project_root, harness_root, force=False):
    """Copy system/skills/<name>/SKILL.md into the harness's skills dir.
    Only for harnesses that declare a skills_dir."""
    skills_rel = spec.get("skills_dir")
    if not skills_rel:
        return []
    src = Path(harness_root) / "system" / "skills"
    dst_root = Path(project_root) / skills_rel
    written = []
    if not src.is_dir():
        return written
    for skill_dir in sorted(src.iterdir()):
        sm = skill_dir / "SKILL.md"
        if not sm.is_file():
            continue
        dst = dst_root / skill_dir.name / "SKILL.md"
        if dst.exists() and not force:
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text(sm.read_text(encoding="utf-8"), encoding="utf-8")
        written.append(dst)
    return written


def install_plugin(spec, project_root, harness_root, force=False):
    plugin_rel = spec.get("plugin")
    if not plugin_rel:
        return []
    src = Path(harness_root) / plugin_rel
    if not src.is_file():
        return []
    dst = Path(project_root) / ".opencode" / "plugins" / src.name
    if dst.exists() and not force:
        return []
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
    return [dst]


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Install wiki-fabric into detected agent harnesses")
    parser.add_argument("action", nargs="?", default="status", choices=["install", "status"])
    parser.add_argument("--all", action="store_true", help="Install into every known harness (not just detected)")
    parser.add_argument("--only", help="Comma-separated harness keys")
    parser.add_argument("--force", action="store_true", help="Rewrite managed blocks even if present")
    parser.add_argument("--project-root", default=os.getcwd())
    parser.add_argument("--block-file", default=None, help="Always-on block text (default: system/always-on)")
    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()
    harness_root = Path(__file__).parent.parent
    block_path = Path(args.block_file) if args.block_file else harness_root / "system" / "always-on" / "wiki-fabric-block.md"
    body = body_from(block_path)

    if args.only:
        keys = [k.strip() for k in args.only.split(",")]
        targets = [spec_by_key(k) for k in keys]
        targets = [t for t in targets if t]
    elif args.all:
        targets = list(SPECS)
    else:
        targets = detect_installed(project_root)

    if args.action == "status":
        print(f"Project: {project_root}")
        print()
        for spec in SPECS:
            marker = marker_for(spec)
            hit = any(list(project_root.glob(pat)) for pat in spec.get("detect", []))
            installed = any(
                marker in (project_root / f).read_text(encoding="utf-8", errors="replace")
                for f in spec.get("instructions", [])
                if (project_root / f).exists()
            )
            state = "installed" if installed else ("detected" if hit else "—")
            print(f"  {spec['name']:22} {state}")
        return 0

    total = 0
    for spec in targets:
        written = install_instructions(spec, project_root, body, force=args.force)
        written += install_skills(spec, project_root, harness_root, force=args.force)
        written += install_plugin(spec, project_root, harness_root, force=args.force)
        if written:
            print(f"  {spec['name']}:")
            for w in written:
                print(f"    wrote {w.relative_to(project_root)}")
            total += len(written)
        else:
            print(f"  {spec['name']}: already installed (use --force to rewrite)")
    print(f"\n{total} file(s) written across {len(targets)} harness(es)")
    return 0


def body_from(block_path):
    """Strip frontmatter + template H1 from the always-on block template."""
    raw = Path(block_path).read_text(encoding="utf-8")
    body = raw.split("---", 2)[2] if raw.startswith("---") else raw
    lines = body.split("\n")
    # drop the template's own H1/comment lines describing the file itself
    out = []
    for i, line in enumerate(lines):
        if line.startswith("# wiki-fabric always-on block"):
            continue
        out.append(line)
    return "\n".join(out).strip()


if __name__ == "__main__":
    sys.exit(main())