#!/usr/bin/env python3
# skill.py — Universal skill loader: print the procedure for a workflow.
#
# Works on EVERY harness (no skill support required): the agent runs
#   wf skill ingest       # full procedure
#   wf skill --list       # one-line summaries
# whenever it's about to run one of those workflows. Native skills
# (Claude Code .claude/skills, opencode .opencode/skill) remain the
# lazy-loaded path where supported; this is the universal fallback.

import sys
import sys as _s, pathlib as _p
_B = _p.Path(__file__).resolve().parent
for _rel in ("", "cmd", "lib", "eval", "harness"):
    _s.path.insert(0, str(_B.parent / _rel))
from pathlib import Path

HARNESS_ROOT = Path(__file__).resolve().parent.parent.parent
SKILLS_DIR = HARNESS_ROOT / "system" / "skills"


def _parse_skill(path):
    """Return (name, description, body)."""
    text = path.read_text(encoding="utf-8", errors="replace")
    name = path.parent.name
    desc = ""
    body = text
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) >= 3:
            for line in parts[1].splitlines():
                if line.startswith("description:"):
                    desc = line.split(":", 1)[1].strip().strip('"')
                    break
            body = parts[2]
    return name, desc, body.strip()


def list_skills():
    if not SKILLS_DIR.is_dir():
        print("No skills directory found.", file=sys.stderr)
        return 1
    print("Available skills (wf skill <name> prints the full procedure):")
    print()
    for d in sorted(SKILLS_DIR.iterdir()):
        sm = d / "SKILL.md"
        if not sm.is_file():
            continue
        name, desc, _ = _parse_skill(sm)
        print(f"  {name:10} {desc}")
    return 0


def show(name):
    sm = SKILLS_DIR / name / "SKILL.md"
    if not sm.is_file():
        print(f"Unknown skill: {name}", file=sys.stderr)
        print("Run: wf skill --list", file=sys.stderr)
        return 1
    _, _, body = _parse_skill(sm)
    print(body)
    return 0


def main():
    import argparse
    parser = argparse.ArgumentParser(
        description="Print the procedure for a wiki-fabric workflow (universal across agent harnesses)")
    parser.add_argument("name", nargs="?", help="Skill name (ingest, promote, ...)")
    parser.add_argument("--list", action="store_true", help="List available skills")
    args = parser.parse_args()

    if args.list or not args.name:
        return list_skills()
    return show(args.name)


if __name__ == "__main__":
    sys.exit(main())