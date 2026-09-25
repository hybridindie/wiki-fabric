#!/usr/bin/env python3
# log-experience.py — Capture an experience event into the fabric
#
# Usage:
#   python3 scripts/cmd/log-experience.py --project my-project --problem "Risk agent had redundant checks" \
#     --intervention "Consolidated 3 checks into 1 validator" --outcome "150ms→23ms latency" \
#     --tags "my-project,performance"
#
#   Interactive mode (prompts for each field):
#   python3 scripts/cmd/log-experience.py --project my-project
#
#   From stdin (pipe a description):
#   echo "Fixed threading crash by adding mutex lock" | python3 scripts/cmd/log-experience.py --project my-project

import sys
import sys as _s, pathlib as _p
_HERE = _p.Path(__file__).resolve().parent
# Explicit import bootstrap: this script's own dir (same-dir siblings)
# + scripts/lib (shared modules). No shotgun path injection.
for _dir in (_HERE, _HERE.parent / "lib"):
    if str(_dir) not in _s.path:
        _s.path.insert(0, str(_dir))
import re
import yaml
import argparse
from pathlib import Path
from datetime import date
from wf_common import slugify
from fabric_config import FABRIC_ROOT
from fabric_config import CORPUS_ROOT
from fabric_config import CORPUS_ROOT

VAULT_ROOT = CORPUS_ROOT
PROJECTS_DIR = VAULT_ROOT / "projects"


def get_projects():
    """List available project namespaces."""
    if not PROJECTS_DIR.exists():
        return []
    return sorted(d.name for d in PROJECTS_DIR.iterdir()
                  if d.is_dir() and not d.name.startswith('_') and not d.name.startswith('.'))


def make_slug(problem, project):
    """Create a short slug from the problem text."""
    words = re.findall(r'[a-z]{3,}', problem.lower())
    slug = "-".join(words[:5])[:60]
    return f"{date.today().isoformat()}-{slug}"


def _actor():
    """Author actor: the owner logs their own experience (OKF human actor)."""
    from fabric_config import get_config, actor
    return actor(get_config(), "human")


def _now_iso():
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def write_event(project, problem, intervention, conditions, outcomes, evidence, tags):
    ns_dir = PROJECTS_DIR / project / "experience-events"
    ns_dir.mkdir(parents=True, exist_ok=True)

    slug = make_slug(problem, project)
    event_path = ns_dir / f"ee-{slug}.md"

    today = date.today().isoformat()

    # Build frontmatter
    lines = [
        "---",
        "type: experience-event",
        f"id: ee-{slug}",
        f"title: \"{problem[:80]}\"",
        f"description: \"Experience event in {project}: {problem[:100]}\"",
        f"generated: {{ by: \"{_actor()}\", at: \"{_now_iso()}\" }}",
        f"project: {project}",
        "domain: [agent-systems]",
        f"observed_problem: \"{problem}\"",
    ]

    if intervention:
        lines.append(f"intervention: \"{intervention}\"")

    lines.append("conditions:")
    for k, v in conditions.items():
        lines.append(f"    {k}: \"{v}\"")

    lines.append("outcomes:")
    for k, v in outcomes.items():
        lines.append(f"    {k}: \"{v}\"")

    lines.append("evidence: []")
    lines.append("confidence: medium")
    if tags:
        lines.append(f"tags: [{tags}]")
    lines.append(f"lineage: \"{project}\"")
    lines.append(f"created: {today}")
    lines.append(f"updated: {today}")
    lines.append("---")
    lines.append("")
    lines.append(f"# ee-{slug}")
    lines.append("")
    lines.append(f"## Problem")
    lines.append("")
    lines.append(problem)
    lines.append("")
    if intervention:
        lines.append(f"## Intervention")
        lines.append("")
        lines.append(intervention)
        lines.append("")
    lines.append(f"## Pattern signal")
    lines.append("")
    lines.append("_Fill in: what reusable pattern does this experience suggest?_")
    lines.append("")

    event_path.write_text("\n".join(lines))
    return event_path


def interactive_mode(project):
    """Prompt for each field."""
    print(f"=== Log Experience Event: {project} ===")
    print()

    problem = input("Observed problem (what went wrong / what did you notice?): ").strip()
    if not problem:
        print("Error: problem is required", file=sys.stderr)
        sys.exit(1)

    intervention = input("Intervention (what did you do about it?) [optional]: ").strip()

    print("\nConditions (key=value, comma-separated) [optional]:")
    print("  e.g. task_class=refactor, runtime=python-3.12, tool=my-cli")
    cond_input = input("  > ").strip()
    conditions = {}
    if cond_input:
        for pair in cond_input.split(","):
            if "=" in pair:
                k, v = pair.split("=", 1)
                conditions[k.strip()] = v.strip()

    print("\nOutcomes (key=value, comma-separated) [optional]:")
    print("  e.g. latency_ms=150→23, drawdown_incidents=3/week→0/week")
    out_input = input("  > ").strip()
    outcomes = {}
    if out_input:
        for pair in out_input.split(","):
            if "=" in pair:
                k, v = pair.split("=", 1)
                outcomes[k.strip()] = v.strip()

    tags = input("\nTags (comma-separated) [optional]: ").strip()

    return problem, intervention, conditions, outcomes, tags


def main():
    parser = argparse.ArgumentParser(description="Log an experience event into the fabric")
    parser.add_argument("--project", help="Project namespace (e.g. my-project)")
    parser.add_argument("--problem", help="Observed problem (one sentence)")
    parser.add_argument("--intervention", help="What was done about it [optional]")
    parser.add_argument("--conditions", help="key=value pairs, comma-separated [optional]")
    parser.add_argument("--outcomes", help="key=value pairs, comma-separated [optional]")
    parser.add_argument("--tags", help="Comma-separated tags [optional]")
    parser.add_argument("--list", action="store_true", help="List available projects")
    args = parser.parse_args()

    # List projects
    projects = get_projects()
    if args.list:
        print("Available project namespaces:")
        for p in projects:
            count = len(list((PROJECTS_DIR / p / "experience-events").glob("*.md"))) if (PROJECTS_DIR / p / "experience-events").exists() else 0
            print(f"  {p} ({count} events)")
        return

    # Resolve project
    project = args.project
    if not project:
        if projects:
            print(f"Available projects: {', '.join(projects)}")
            project = input("Project namespace: ").strip()
        else:
            print("Error: no project namespaces exist. Run bootstrap-project.py first.", file=sys.stderr)
            sys.exit(1)

    if project not in projects:
        print(f"Error: project '{project}' not found. Available: {projects}", file=sys.stderr)
        sys.exit(1)

    # Gather fields
    if args.problem:
        problem = args.problem
        intervention = args.intervention or ""
        conditions = {}
        if args.conditions:
            for pair in args.conditions.split(","):
                if "=" in pair:
                    k, v = pair.split("=", 1)
                    conditions[k.strip()] = v.strip()
        outcomes = {}
        if args.outcomes:
            for pair in args.outcomes.split(","):
                if "=" in pair:
                    k, v = pair.split("=", 1)
                    outcomes[k.strip()] = v.strip()
    else:
        # Interactive or stdin
        if not sys.stdin.isatty():
            # Piped input: use as problem description
            piped = sys.stdin.read().strip()
            if piped:
                problem = piped
                intervention = ""
                conditions = {}
                outcomes = {}
            else:
                problem, intervention, conditions, outcomes, _ = interactive_mode(project)
        else:
            problem, intervention, conditions, outcomes, tags_arg = interactive_mode(project)
            tags = tags_arg

    # Default tags
    tags = getattr(locals().get('tags_arg', None), 'strip', lambda: '')() if 'tags_arg' in locals() else (args.tags or "")

    # Write event
    event_path = write_event(project, problem, intervention, conditions, outcomes, [], tags)

    print(f"Logged experience event:")
    print(f"  {event_path.relative_to(VAULT_ROOT)}")
    print(f"  Project: {project}")
    print(f"  Problem: {problem[:80]}")
    if intervention:
        print(f"  Intervention: {intervention[:80]}")

    # Count events for this project
    ns_dir = PROJECTS_DIR / project / "experience-events"
    event_count = len(list(ns_dir.glob("*.md")))
    print(f"  Project total: {event_count} events")

    if event_count >= 2:
        print(f"\n  Tip: run `python3 scripts/cmd/mine-promotions.py` to check for cross-project patterns.")


if __name__ == "__main__":
    main()