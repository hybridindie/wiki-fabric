#!/usr/bin/env python3
"""rules.py — the multi-project rules layer (#178).

A0 harvest: `wf rules harvest <project>` — the project's OWN rule files
(.claude/rules/*.md, AGENTS.md/CLAUDE.md `# ` sections) become staged
pattern candidates in patterns/_inbox/ (origin: rules-file; provenance =
file path + paths-globs as locator). Deterministic, 0 tokens; nothing
auto-promotes — the gate decides (promote-patterns).

The near-miss dedupe (G-J-gated, the #173 machinery) runs at harvest time:
a rule whose topic twin ALREADY sits in the inbox (from another project)
merges into it (provenance +1 source repo; the divergence note records the
delta) instead of duplicating.

B export: `wf rules export --for <project>` renders PROMOTED standing rules
to `.claude/rules/wiki-fabric/*.md` with `paths:` frontmatter derived from
each pattern's `applicability.includes`; idempotent; AGENTS.md @imports row
for non-Claude harnesses.
"""

import sys
import sys as _s, pathlib as _p
_HERE = _p.Path(__file__).resolve().parent
for _dir in (_HERE, _HERE.parent / "lib"):
    if str(_dir) not in _s.path:
        _s.path.insert(0, str(_dir))
import argparse
import hashlib
import re
from datetime import date
from pathlib import Path

from fabric_config import get_config, FABRIC_ROOT, get_repo_config
from wf_common import yaml_scalar, parse_frontmatter, project_slug
import layout

RULES_MARKER_START = "<!-- wiki-fabric-rules-start -->"
RULES_MARKER_END = "<!-- wiki-fabric-rules-end -->"


# === A0: harvest ============================================================

def _rule_files(repo: Path):
    """The project's own rule files: .claude/rules/**/*.md (the canonical
    path-scoped layer). Returns [(path, fm, body)]."""
    out = []
    rules_dir = repo / ".claude" / "rules"
    if rules_dir.is_dir():
        for p in sorted(rules_dir.rglob("*.md")):
            fm, body = parse_frontmatter(p)
            if not body.strip():
                continue
            out.append((p, fm, body))
    return out


def _rule_heading(body):
    m = re.search(r"^# (.+)$", body, re.M)
    return m.group(1).strip() if m else ""


def _rule_bullets(body):
    """The rule's numbered/bulleted constraint lines (the content the
    candidate carries verbatim)."""
    return [ln.strip() for ln in body.splitlines() if re.match(r"^(?:\d+\.|-) ", ln.strip())]


def _candidate_id(kind, statement):
    return f"{kind}-rule-{hashlib.sha256(statement.encode()).hexdigest()[:10]}"


def harvest(project, dry_run=False, judge=True):
    """Harvest one project's rule files → staged candidates (#178 A0).
    Returns (staged, merged, skipped) counts."""
    config = get_config()
    canonical = project_slug(project)
    rcfg = get_repo_config(config, canonical) or {}
    rp = rcfg.get("path")
    if not rp:
        print(f"no repo path for {project} (fabric.yaml/overlay)", file=sys.stderr)
        return 0, 0, 0
    repo = (FABRIC_ROOT / rp).resolve() if not Path(rp).is_absolute() else Path(rp).resolve()
    if not repo.is_dir():
        print(f"repo missing: {repo}", file=sys.stderr)
        return 0, 0, 0
    rules = _rule_files(repo)
    if not rules:
        print(f"{canonical}: no .claude/rules/ files — nothing to harvest")
        return 0, 0, 0
    inbox = layout.patterns_inbox(layout.VAULT_ROOT if hasattr(layout, "VAULT_ROOT") else _corpus_root())
    inbox.mkdir(parents=True, exist_ok=True)
    staged = merged = skipped = 0
    for path, fm, body in rules:
        heading = _rule_heading(body) or path.stem
        bullets = _rule_bullets(body)
        statement = heading if bullets else body.strip().splitlines()[0][:140]
        cid = _candidate_id("pattern", f"{canonical}:{statement}")
        dest = inbox / f"{cid}.md"
        if dest.exists():
            skipped += 1
            continue
        if dry_run:
            print(f"  [DRY] would stage {cid} ← {path.name}")
            staged += 1
            continue
        # near-miss vs the inbox: the divergent-twin check (G-J guarded)
        twin = _near_miss_twin(statement, "\n".join(bullets) or body, inbox, canonical, judge=judge)
        if twin:
            twin_path, prob = twin
            _merge_rule_candidate(twin_path, statement, bullets, path, canonical, prob)
            merged += 1
            print(f"  MERGED into {twin_path.stem} <- {canonical}/{path.name} (twin; delta recorded)")
            continue
        paths_globs = fm.get("paths") or []
        paths_yaml = "\n".join(f'  - "{g}"' for g in paths_globs) if paths_globs else "  # unscoped (always loads)"
        dest.write_text(f"""---
type: pattern
id: {cid}
title: {yaml_scalar(statement[:140])}
status: candidate
maturity: 1
origin: rules-file
project: {canonical}
source_rule: "{path.relative_to(repo)}"
paths_globs:
{paths_yaml}
provenance:
  - source: "{canonical}/{path.relative_to(repo)}"
    locator: "rule file ({'paths: ' + ', '.join(paths_globs[:2]) if paths_globs else 'unscoped'})"
    quote: {yaml_scalar((bullets[0] if bullets else statement)[:120])}
tags: [rules-harvest, inbox]
created: {date.today().isoformat()}
---

# {statement[:90]}

_Harvested from `{path.relative_to(repo)}` ({canonical}) — the project's own
hand-maintained rule, promoted into the corpus so it can travel._

## Rule

{chr(10).join(bullets) if bullets else body.strip()[:1200]}

**Review against the promotion checklist** (independence across projects,
applicability.includes = the paths-globs above). Apply via
promote-patterns --apply; the export layer then renders it back
path-scoped.
""")
        staged += 1
        print(f"  staged {cid} ← {path.name}")
    return staged, merged, skipped


def _norm_tokens(s):
    return set(re.findall(r"[a-z]{3,}", s.lower()))


def _jaccard(a, b):
    i, u = len(a & b), len(a | b)
    return i / u if u else 0.0


NEAR_MISS_MIN, NEAR_MISS_MAX = 0.15, 0.75


def _near_miss_twin(statement, rule_text, inbox, project, judge=True):
    """The closest already-staged rule candidate in the near-miss band
    (G-J-gated same_recurrence verdict — the #173 machinery). Returns
    (candidate_path, probability) or None."""
    try:
        from judgment import same_recurrence, judgment_eval_recorded
        if judge:
            ok, why = judgment_eval_recorded()
            if not ok:
                print(f"  (G-J gate not satisfied — twin-merge off: {why})")
                judge = False
    except ImportError:
        judge = False
    t_new = _norm_tokens(rule_text)
    for p in sorted(inbox.glob("pattern-rule-*.md")):
        body = p.read_text(encoding="utf-8", errors="replace")
        # compare the RULE content (the '## Rule' section or the body head)
        # — the whole-file compare dilutes the token set with template
        # prose and pushes real twins under the band (the #173 lesson)
        if "## Rule" in body:
            rule_part = body.split("## Rule", 1)[1].split("**", 1)[0]
        else:
            rule_part = body.split("---")[-1]
        sim = _jaccard(t_new, _norm_tokens(rule_part))
        if not (NEAR_MISS_MIN <= sim <= NEAR_MISS_MAX):
            continue
        if not judge:
            continue  # no judgment available → stage separately (never silent-merge)
        cand_stmt = re.sub(r"^#\s+.*$", "", body.split("**", 1)[0], flags=re.M).strip()
        same, prob = same_recurrence(statement, cand_stmt, repo=project,
                                     context="both are agent-workflow rule files harvested from project repos")
        if same:
            return p, prob
        print(f"  judged twin p={prob:.2f} -> keep separate ({p.stem})")
    return None


def _merge_rule_candidate(dest, statement, bullets, source_path, project, prob):
    """Merge a harvested twin into the existing candidate: provenance gains
    the source repo; the divergence note records the delta (the human gate
    resolves which phrasing wins; the loser's specifics land in
    counterexamples)."""
    text = dest.read_text(encoding="utf-8", errors="replace")
    fm_end = text.index("\n---", 4)
    fm = text[4:fm_end]
    lines = fm.splitlines()
    pstart = next((i for i, l in enumerate(lines) if l.startswith("provenance:")), None)
    prov = (f'  - source: "{project}/{source_path.name}"\n'
            f'    locator: "rule file (twin-merge; judged p={prob:.2f})"\n'
            f'    quote: {yaml_scalar((bullets[0] if bullets else statement)[:120])}')
    if pstart is None:
        lines += ["provenance:", prov]
    else:
        pend = pstart + 1
        while pend < len(lines) and (lines[pend].startswith("  ") or not lines[pend].strip()):
            pend += 1
        lines = lines[:pend] + [prov] + lines[pend:]
    text = "---\n" + "\n".join(lines) + "\n---\n" + text[fm_end + 4:]
    text = text.rstrip() + (f"\n\n**Merged twin** (judged p={prob:.2f}, from `{project}/{source_path.name}`): "
                            f"{statement}\n" + (chr(10).join("> " + b for b in bullets[:4]) + chr(10) if bullets else ""))
    dest.write_text(text, encoding="utf-8")


# === B: export (path-scoped render) ========================================

def export_rules(project, dry_run=False):
    """Render PROMOTED standing rules into the project's
    `.claude/rules/wiki-fabric/*.md` (#178 B): paths-frontmatter from the
    pattern's applicability.includes; idempotent writes (content-hash skip).
    Returns (written, skipped)."""
    corpus = _corpus_root()
    patterns_dir = layout.patterns(corpus)
    out_root = _project_repo_rules_dir(project) / "wiki-fabric"
    if not patterns_dir.is_dir():
        print("no corpus patterns/ — nothing promoted to render", file=sys.stderr)
        return 0, 0
    written = skipped = 0
    for pf in sorted(patterns_dir.glob("pattern-*.md")):
        fm, body = parse_frontmatter(pf)
        status = str(fm.get("status") or "").lower()
        if status not in ("recommended", "standard"):
            continue  # the managed layer renders the PROMOTED set only
        applies = _applies_to_project(fm, project, body)
        if not applies:
            continue  # a declared decline / project-scoped elsewhere
        content = rendered_rule_content(pf, fm, body)
        if content is None:
            continue
        dest = out_root / f"{pf.stem}.md"
        if dest.exists() and dest.read_text(encoding="utf-8", errors="replace") == content:
            skipped += 1
            continue
        if dry_run:
            print(f"  [DRY] would render {dest.name} (paths: {', '.join(includes[:2]) or 'always'})")
            written += 1
            continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(content, encoding="utf-8")
        written += 1
        print(f"  rendered {dest.name}")
    return written, skipped


def rendered_rule_content(pf, fm, body, project=None, declined=None):
    """The expected managed-file content for one promoted pattern (single
    truth shared by export + the parity guard — the guard compares THIS)."""
    includes = (fm.get("applicability") or {}).get("includes") or []
    paths_yaml = "\n".join(f'  - "{_glob_from_include(i)}"' for i in includes[:6]) or '  - "**/*"'
    title = str(fm.get("title") or pf.stem)
    return f"""---
paths:
{paths_yaml}
---
# {title}
_{fm.get('id', pf.stem)} (wiki-fabric managed — edit the pattern, not this file; it regenerates)_

{body.split("---")[-1].strip()[:2400]}
"""


def _applies_to_project(fm, project, body):
    """Scope filter: the pattern's project: field (absent = global) and the
    DECLINED set (overlay rules: pattern-id: declined)."""
    canonical = project_slug(project)
    declared = str(fm.get("project") or "").strip()
    if declared and declared != canonical:
        return False
    rcfg = get_repo_config(get_config(), canonical) or {}
    declined = set(rcfg.get("rules") or {})
    if pf_declines(fm, declined):
        return False
    return True


def pf_declines(fm, declined):
    return str(fm.get("id") or "") in declined


def _glob_from_include(inc):
    """applicability.includes (prose like 'src/api paths') → a paths: glob.
    A token that LOOKS like a path passes through; prose falls back to
    '**/*' (always-load beats a wrong filter)."""
    inc = str(inc).strip()
    if re.search(r"\.(py|ts|js|gd|toml|ya?ml|json|md)$", inc) or "/" in inc:
        g = re.search(r"[\w./\-*{}]+", inc)
        if g:
            return g.group(0)
    return "**/*"


def _corpus_root():
    from fabric_config import CORPUS_ROOT
    return CORPUS_ROOT


def _project_repo_rules_dir(project):
    canonical = project_slug(project)
    rcfg = get_repo_config(get_config(), canonical) or {}
    rp = rcfg.get("path")
    repo = (FABRIC_ROOT / rp) if rp and not Path(rp).is_absolute() else Path(rp or ".")
    return repo / ".claude" / "rules"


def main():
    parser = argparse.ArgumentParser(
        description="Harvest project rule files into the corpus / render promoted rules back (multi-project parity, #178)")
    sub = parser.add_subparsers(dest="op")
    p_h = sub.add_parser("harvest", help="Stage the project's own rule files as candidates (A0)")
    p_h.add_argument("project")
    p_h.add_argument("--dry-run", action="store_true")
    p_h.add_argument("--no-judge", action="store_true", help="Skip twin-merge judgments (stage separately)")
    p_e = sub.add_parser("export", help="Render promoted rules into the project (B)")
    p_e.add_argument("--for", dest="for_project", required=True)
    p_e.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    if args.op == "harvest":
        print(f"Harvesting rules for {args.project}...")
        s, m, k = harvest(args.project, dry_run=args.dry_run, judge=not args.no_judge)
        print(f"Harvest: {s} staged, {m} merged-twin, {k} already-staged"
              + (" [DRY RUN]" if args.dry_run else ""))
        print("Review: wf promote-patterns --list (the gate decides)")
        return 0
    if args.op == "export":
        w, k = export_rules(args.for_project, dry_run=args.dry_run)
        print(f"Export: {w} rendered, {k} unchanged"
              + (" [DRY RUN]" if args.dry_run else ""))
        return 0
    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())