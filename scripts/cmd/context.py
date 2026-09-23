#!/usr/bin/env python3
# context.py — Compile a task-specific context manifest from the corpus (0 tokens)
#
# Deterministic context assembly per AGENTS.md's scope model:
#   Agent Context = Global Policies + Domain Knowledge + Project Constraints + Task Evidence
#
# Selection is explainable by construction: every included (and excluded) artifact
# carries a reason. No LLM, no scoring magic — priority order, path overlap, tag
# match, text match, and status/staleness filters.
#
# Usage:
#   wf context --task "Add token rotation to the OAuth service" --paths services/auth
#   wf context --task "..." --project my-project          # pin a project namespace
#   wf context --task "..." --paths a/b --paths c/d       # multiple code paths
#   wf context --task "..." --format json                 # machine manifest
#
# Priority order (highest first): project decisions/claims → domain patterns →
# global patterns/policies → concepts. Superseded artifacts are excluded;
# REVIEW-AFTER-stale artifacts are demoted with a warning.

import sys
import sys as _s, pathlib as _p
_B = _p.Path(__file__).resolve().parent
for _rel in ("", "cmd", "lib", "eval", "harness"):
    _s.path.insert(0, str(_B.parent / _rel))
import re
import json
import argparse
from pathlib import Path
from datetime import date

try:
    import yaml
    HAVE_YAML = True
except ImportError:
    HAVE_YAML = False

from fabric_config import FABRIC_ROOT
from fabric_config import CORPUS_ROOT
from fabric_config import CORPUS_ROOT
from fabric_config import get_config, get_ignores, is_ignored
from wf_common import parse_frontmatter

VAULT_ROOT = CORPUS_ROOT

# wiki/ is the OpenWiki-style human-facing layer: its prose is a paraphrase of
# claims (drift risk + context bloat if fed back to a model). The machine
# consumes its *edges* via the citation graph (registry/wiki-graph.json),
# never the prose. syntheses/ is similarly human-facing generated prose.
SKIP_PARTS = {".git", ".obsidian", ".opencode", "__pycache__", ".venv", "venv",
              "templates", "schemas", "evaluations", "raw", "traces", "system", "tests",
              "examples", "wiki", "syntheses"}
SKIP_FILES = {"index.md", "log.md", "catalog.json", "README.md", "CONTRIBUTING.md", "AGENTS.md"}


def load_corpus():
    """Load all catalogable corpus pages with derived scope."""
    pages = []
    for p in VAULT_ROOT.rglob("*.md"):
        rel = p.relative_to(VAULT_ROOT)
        parts = rel.parts
        if any(x in SKIP_PARTS for x in parts):
            continue
        if rel.name in SKIP_FILES or rel.name.endswith("README.md"):
            continue
        posix = rel.as_posix()
        if posix.startswith("evidence/traces"):
            continue
        if "raw" in parts:
            continue
        fm, body = parse_frontmatter(p)
        scope = fm.get("scope") or (
            "domain" if posix.startswith("domains/")
            else "project" if posix.startswith("projects/")
            else "global"
        )
        pages.append({
            "path": p,
            "rel": rel,
            "posix": posix,
            "stem": rel.stem.lower(),
            "fm": fm or {},
            "body": body,
            "type": (fm or {}).get("type", ""),
            "scope": scope,
        })
    return pages


def tokens(text):
    """Lowercase word tokens, crudely stemmed (rotation→rotat, rotating→rotat)
    so morphological variants still match. Pure string ops — 0 tokens."""
    import re
    out = set()
    for w in re.findall(r"[a-z0-9][a-z0-9_-]{2,}", text.lower()):
        out.add(w)
        # cheap suffix strip: -tion/-ting/-ing/-ed/-s + e-restoration (caching→cache)
        for suf, add in (("tion", ""), ("ting", ""), ("ing", "e"), ("ed", "e"), ("s", "")):
            if w.endswith(suf) and len(w) - len(suf) >= 4:
                out.add(w[: -len(suf)])
                if add:
                    out.add(w[: -len(suf)] + add)
                break
    return out


def is_stale(fm, today):
    """review_after in the past → stale. Returns days overdue or 0."""
    ra = fm.get("review_after")
    if not ra:
        return 0
    import datetime as _dt
    try:
        if isinstance(ra, _dt.date):
            review = ra
        else:
            review = _dt.date.fromisoformat(str(ra).strip()[:10])
        overdue = (today - review).days
        return overdue if overdue > 0 else 0
    except (ValueError, TypeError):
        return 0


def select_context(pages, task, paths, project, today, max_items=20):
    """Deterministic selection: project > domain > global, each with a reason.

    Returns (selected, excluded):
      selected: [{page fields..., reason, priority}]
      excluded: [{stem, path, reason}]
    """
    task_toks = tokens(task)
    path_list = [p.strip().strip("/").lower() for p in paths if p.strip()]
    selected, excluded = [], []

    def body_tokens(page):
        # Body tokens (capped for speed) — used for tag/text matching
        return tokens(page["body"][:2000])

    # ---- Exclusion pass (cheap status/staleness filters) ----
    candidates = []
    for pg in pages:
        t = pg["type"]
        fm = pg["fm"]
        status = str(fm.get("status") or "").lower()

        if t == "claim":
            # claims normally ride along via concepts/patterns that reference them;
            # but strongly task-matching claims are direct task evidence — keep as
            # candidates (tier P1-project evidence).
            candidates.append((pg, 0))
            continue
        if t not in ("pattern", "anti-pattern", "skill", "concept", "decision", "experience-event", "question"):
            excluded.append({"stem": pg["stem"], "path": pg["posix"],
                             "reason": f"not a context artifact (type: {t or 'unknown'})"})
            continue
        if status == "superseded":
            excluded.append({"stem": pg["stem"], "path": pg["posix"], "reason": "superseded"})
            continue
        if status == "deprecated":
            excluded.append({"stem": pg["stem"], "path": pg["posix"], "reason": "deprecated"})
            continue

        overdue = is_stale(fm, today)
        if overdue and t in ("pattern", "anti-pattern", "skill"):
            excluded.append({"stem": pg["stem"], "path": pg["posix"],
                             "reason": f"stale: review_after overdue {overdue} days — review before relying on it"})
            continue

        candidates.append((pg, overdue))

    # ---- Priority tiers ----
    tiers = [
        ("P1-project", ("decision", "experience-event")),
        ("P2-domain", ("pattern", "anti-pattern", "skill", "question")),
        ("P3-global", ("pattern", "anti-pattern", "skill", "concept")),
    ]

    scored = []
    for pg, overdue in candidates:
        scope = pg["scope"]
        fm = pg["fm"]
        reason = None
        priority = None

        if scope == "project":
            # Match: project pinned, or task/body text overlap, or path overlap with namespace
            if project and project.lower() in pg["posix"]:
                reason = f"project match: {project}"
                priority = "P1-project"
            else:
                # text overlap with task
                overlap = task_toks & body_tokens(pg)
                if len(overlap) >= 2:
                    reason = f"task text match: {', '.join(sorted(overlap)[:4])}"
                    priority = "P1-project"
        elif scope == "global" and pg["type"] == "claim":
            # direct task evidence: a claim whose statement matches the task
            overlap = task_toks & body_tokens(pg)
            if len(overlap) >= 2:
                reason = f"task evidence (claim): {', '.join(sorted(overlap)[:4])}"
                priority = "P1-project"
        elif scope == "domain":
            toks = task_toks & (body_tokens(pg) | tokens(pg["stem"]))
            if len(toks) >= 1 and any(len(t) >= 4 for t in toks):
                reason = f"domain match: {', '.join(sorted(toks)[:3])}"
                priority = "P2-domain"
        else:  # global
            # Policies/patterns apply broadly: include the significant ones
            # (patterns, anti-patterns, skills) that textually relate OR are canonical
            status = str(fm.get("status") or "").lower()
            if pg["type"] in ("pattern", "anti-pattern", "skill") and status in ("", "recommended", "standard", "candidate"):
                toks = task_toks & (body_tokens(pg) | tokens(pg["stem"]))
                if len(toks) >= 1 and any(len(t) >= 4 for t in toks):
                    reason = f"global pattern match: {', '.join(sorted(toks)[:3])}"
                    priority = "P3-global"

        if priority:
            # Path relevance boosts within-tier ordering
            path_hit = any(pp and pp in pg["posix"] for pp in path_list) if path_list else False
            scored.append({"pg": pg, "reason": reason, "priority": priority,
                           "stale": overdue, "path_hit": path_hit})

    # Order: priority tier → path hit → staleness (fresh first) → stem
    tier_order = {"P1-project": 0, "P2-domain": 1, "P3-global": 2}
    scored.sort(key=lambda s: (tier_order.get(s["priority"], 9), not s["path_hit"], -s["stale"], s["pg"]["stem"]))

    for s in scored[:max_items]:
        pg = s["pg"]
        item = {
            "id": str(pg["fm"].get("id") or pg["stem"]),
            "stem": pg["stem"],
            "path": pg["posix"],
            "type": pg["type"],
            "scope": pg["scope"],
            "reason": s["reason"],
            "priority": s["priority"],
        }
        item["trust_tier"] = trust_tier(pg["fm"])
        if s["stale"]:
            item["warning"] = f"review_after overdue {s['stale']} day(s)"
        sa = pg["fm"].get("stale_after")
        if sa:
            item["stale_after"] = str(sa)
            try:
                import datetime as _dt
                _v = str(sa).strip()[:10]
                if _dt.date.today().isoformat() >= _v:
                    _w = "stale_after reached — verify before relying on it"
                    item["warning"] = (item["warning"] + "; " if item.get("warning") else "") + _w
            except (ValueError, IndexError):
                pass
        if pg["fm"].get("title"):
            item["title"] = pg["fm"]["title"]
        selected.append(item)
    if len(scored) > max_items:
        for s in scored[max_items:]:
            excluded.append({"stem": s["pg"]["stem"], "path": s["pg"]["posix"],
                             "reason": f"beyond --max {max_items}"})

    return selected, excluded


def trust_tier(fm):
    """OKF v0.2 §5.3 trust tier from verified[]: human-reviewed >
    machine-confirmed > unverified. Advisory signal, not access control."""
    v = fm.get("verified")
    if isinstance(v, dict):
        v = [v]
    if not v:
        return "unverified"
    if any(isinstance(x, dict) and str(x.get("by", "")).startswith("human:")
           for x in v):
        return "human-reviewed"
    return "machine-confirmed"


def body_tokens(page):
    import re
    return set(re.findall(r"[a-z0-9][a-z0-9_-]{2,}", page["body"][:2000].lower()))


def render_markdown(task, paths, project, selected, excluded):
    lines = [
        "# Context Manifest",
        "",
        f"- **Task:** {task}",
    ]
    if paths:
        lines.append(f"- **Code paths:** {', '.join(paths)}")
    if project:
        lines.append(f"- **Project:** {project}")
    lines += ["- **Compiled:** deterministic selection (0 tokens) — every item carries a reason", ""]

    if selected:
        lines.append("## Selected")
        lines.append("")
        tier_names = {"P1-project": "Project (highest precedence)", "P2-domain": "Domain", "P3-global": "Global"}
        cur = None
        for it in selected:
            if it["priority"] != cur:
                cur = it["priority"]
                lines.append(f"### {tier_names.get(cur, cur)}")
                lines.append("")
            warn = f" ⚠ {it['warning']}" if it.get("warning") else ""
            tier = it.get("trust_tier", "unverified")
            badge = {"human-reviewed": "trust: human-reviewed",
                     "machine-confirmed": "trust: machine-confirmed"}.get(tier, "")
            badge_part = f" `{badge}`" if badge else ""
            lines.append(f"- [[{it['stem']}]] — *{it['reason']}*{badge_part}{warn}")
        lines.append("")

    lines.append("## Excluded")
    lines.append("")
    if excluded:
        for it in excluded[:15]:
            lines.append(f"- `{it['path']}` — {it['reason']}")
        if len(excluded) > 15:
            lines.append(f"- ... and {len(excluded) - 15} more")
    else:
        lines.append("_(nothing excluded)_")
    lines.append("")

    lines.append("## Precedence")
    lines.append("")
    lines.append("When artifacts conflict: project decisions override domain patterns,")
    lines.append("domain patterns override global policies. Cite the artifact you followed.")
    return "\n".join(lines) + "\n"


def integrations_state():
    """Report optional-integration state for manifest transparency."""
    try:
        from fabric_config import get_config, is_integration_active
        cfg = get_config()
        return {
            "graphify": is_integration_active(cfg, "graphify"),
            "embeddings": is_integration_active(cfg, "embeddings"),
        }
    except Exception:
        return {"graphify": False, "embeddings": False}


def render_json(task, paths, project, selected, excluded):
    return json.dumps({
        "task": task,
        "paths": paths,
        "project": project,
        "compiled": date.today().isoformat(),
        "integrations": integrations_state(),
        "selected": selected,
        "excluded": excluded,
        "precedence": ["project", "domain", "global"],
    }, indent=2)


def main():
    parser = argparse.ArgumentParser(description="Compile a task-specific context manifest (0 tokens)")
    parser.add_argument("--task", required=True, help="What the agent is about to do")
    parser.add_argument("--paths", action="append", default=[], help="Code path(s) the task touches (repeatable)")
    parser.add_argument("--project", help="Pin a project namespace (projects/<slug>/)")
    parser.add_argument("--format", choices=("markdown", "json"), default="markdown")
    parser.add_argument("--max", type=int, default=20, help="Max selected artifacts (default 20)")
    args = parser.parse_args()

    pages = load_corpus()
    selected, excluded = select_context(pages, args.task, args.paths, args.project, date.today(), args.max)

    if args.format == "json":
        print(render_json(args.task, args.paths, args.project, selected, excluded))
    else:
        print(render_markdown(args.task, args.paths, args.project, selected, excluded))
    return 0


if __name__ == "__main__":
    sys.exit(main())