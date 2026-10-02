#!/usr/bin/env python3
"""migrate-project-tree.py — #158 S4 one-shot: canonicalize a project's raw-form
path trees + addressing fields to the canonical slug (project_slug seam).

Moves (git mv semantics via plain rename — the corpus is git):
  projects/<raw>/            → projects/<canonical>/   (ee- ids carry no slug — verified)
  evidence/raw/<raw>/        → evidence/raw/<canonical>/
Rewrites (field-addressing only; upstream prose is NEVER touched):
  ee- frontmatter project:/lineage:            <raw> → <canonical>
  source-record source_path:/resource:         evidence/raw/<raw>/ → evidence/raw/<canonical>/
  overlay .wiki-overlay.md namespace:          <raw> → <canonical>
  fabric.yaml repos: <raw>: → <canonical>:      (keys only; path: is the real repo dir name)
Idempotent: a run whose moves are already done is a no-op (reports already-canonical).
"""

import argparse
import re
import sys
import sys as _s, pathlib as _p
_HERE = _p.Path(__file__).resolve().parent
for _dir in (_HERE, _HERE.parent / "lib"):
    if str(_dir) not in _s.path:
        _s.path.insert(0, str(_dir))
from pathlib import Path

from fabric_config import FABRIC_ROOT, CORPUS_ROOT
from wf_common import project_slug, parse_frontmatter
import layout


def _move_tree(src: Path, dst: Path, dry: bool):
    if not src.exists():
        return "absent"
    if dst.exists():
        return "collision"
    if dry:
        print(f"  move {src} -> {dst}")
        return "moved"
    dst.parent.mkdir(parents=True, exist_ok=True)
    src.rename(dst)
    return "moved"


def _rewrite_file(path: Path, pattern, repl, dry: bool, label: str):
    if not path.exists():
        return 0
    text = path.read_text(encoding="utf-8", errors="replace")
    new, n = pattern.subn(repl, text)
    if n and not dry:
        path.write_text(new, encoding="utf-8")
    if n:
        print(f"    {label}: {path.name} ({n} field line{'s' if n != 1 else ''})")
    return n


def main():
    import argparse
    parser = argparse.ArgumentParser(description="#158 S4: rename a project's raw-form trees to the canonical slug")
    parser.add_argument("raw_slug", help="the raw (non-canonical) project slug, e.g. comfyui_mcp")
    parser.add_argument("--dry-run", action="store_true", help="Print the plan, write nothing")
    args = parser.parse_args()
    raw = args.raw_slug
    canonical = project_slug(raw)
    if raw == canonical:
        print(f"'{raw}' is already canonical — nothing to do")
        return 0

    print(f"#158 S4 migration: {raw} -> {canonical}" + (" [DRY RUN]" if args.dry_run else ""))
    moved_state = []

    # 1. projects tree
    moved_state.append(("projects tree",
                        _move_tree(layout.projects(CORPUS_ROOT) / raw,
                                   layout.projects(CORPUS_ROOT) / canonical, args.dry_run)))
    # 2. raw capture tree
    moved_state.append(("raw tree",
                        _move_tree(layout.evidence_raw(CORPUS_ROOT) / raw,
                                   layout.evidence_raw(CORPUS_ROOT) / canonical, args.dry_run)))

    for name, state in moved_state:
        print(f"  {name}: {state}")
    if "collision" in [s for _, s in moved_state]:
        print("DESTINATION EXISTS — resolve by hand, aborting", file=sys.stderr)
        return 1

    old_raw_frag = re.escape(f"evidence/raw/{raw}/")
    new_raw_frag = f"evidence/raw/{canonical}/"
    field_line = re.compile(r'^(source_path: )' + old_raw_frag + r'(.*)$', re.M)
    resource_line = re.compile(r'^(resource: ")' + old_raw_frag + r'([^"]*)(")$', re.M)
    ee_project_line = re.compile(rf'^(project: ){re.escape(raw)}$', re.M)
    ee_lineage_line = re.compile(rf'^(lineage: ){re.escape(raw)}$', re.M)
    ee_lineage_quoted = re.compile(rf'^(lineage: "){re.escape(raw)}(")$', re.M)
    ee_id_hint = re.compile(rf'^(description: "Experience event in ){re.escape(raw)}(:)', re.M)

    # 3. source records: source_path/resource field lines
    n_src = 0
    for rec in layout.sources(CORPUS_ROOT).glob(f"src-{canonical}-*.md"):
        n_src += _rewrite_file(rec, field_line, r'\g<1>' + new_raw_frag + r'\g<2>', args.dry_run, "source_path")
        n_src += _rewrite_file(rec, resource_line, r'\g<1>' + new_raw_frag + r'\g<2>\g<3>', args.dry_run, "resource")
    print(f"  source records rewritten: {n_src} lines")

    # 4. ee- frontmatter in the (moved) project tree — in dry-run the move
    # hasn't happened, so probe BOTH locations
    n_ee = 0
    ee_root_dry = (layout.projects(CORPUS_ROOT) / canonical if not args.dry_run
                   else layout.projects(CORPUS_ROOT) / raw)
    for ee in ee_root_dry.rglob("ee-*.md"):
        n_ee += _rewrite_file(ee, ee_project_line, r'\g<1>' + canonical, args.dry_run, "project")
        n_ee += _rewrite_file(ee, ee_lineage_line, r'\g<1>' + canonical, args.dry_run, "lineage")
        n_ee += _rewrite_file(ee, ee_lineage_quoted, r'\g<1>' + canonical + r'\g<2>', args.dry_run, "lineage")
        n_ee += _rewrite_file(ee, ee_id_hint, r'\g<1>' + canonical + r'\g<2>', args.dry_run, "description")
    print(f"  experience events rewritten: {n_ee} lines")

    # 5. overlay namespace: (the SOURCE repo's overlay — lives at the repo root)
    repo_cfg_path = FABRIC_ROOT / "fabric.yaml"
    overlay_path = None
    if repo_cfg_path.exists():
        import yaml
        try:
            cfg = yaml.safe_load(repo_cfg_path.read_text()) or {}
            path_str = (cfg.get("repos") or {}).get(raw, {}).get("path")
            if path_str:
                cand = (FABRIC_ROOT / path_str).resolve()
                if (cand / ".wiki-overlay.md").exists():
                    overlay_path = cand / ".wiki-overlay.md"
        except Exception:
            pass
    if overlay_path:
        n_ov = _rewrite_file(overlay_path,
                             re.compile(rf'^(namespace: ){re.escape(raw)}$', re.M),
                             r'\g<1>' + canonical, args.dry_run, "overlay namespace")
        n_ov += _rewrite_file(overlay_path,
                              re.compile(rf'^(project: ){re.escape(raw)}$', re.M),
                              r'\g<1>' + canonical, args.dry_run, "overlay project")
        print(f"  overlay rewritten: {n_ov} lines")

    # 6. fabric.yaml repos KEY (path: value untouched — the real dir is raw-named)
    if repo_cfg_path.exists() and not args.dry_run:
        import yaml
        cfg = yaml.safe_load(repo_cfg_path.read_text()) or {}
        repos = cfg.get("repos") or {}
        if raw in repos and canonical not in repos:
            repos[canonical] = repos.pop(raw)
            cfg["repos"] = repos
            repo_cfg_path.write_text(
                yaml.safe_dump(cfg, sort_keys=False, default_flow_style=False),
                encoding="utf-8")
            print(f"  fabric.yaml: repos.{raw} -> repos.{canonical}")
        elif raw not in repos:
            print("  fabric.yaml: no raw-form key (already canonical?)")
    elif args.dry_run and repo_cfg_path.exists():
        import yaml
        cfg = yaml.safe_load(repo_cfg_path.read_text()) or {}
        if raw in (cfg.get("repos") or {}):
            print(f"  fabric.yaml: repos.{raw} -> repos.{canonical} (key only)")

    print("\nPost-migration (run by hand):")
    print("  wf rebuild-index        # catalog carries projects/<raw> paths")
    print("  wf export wiki --rebuild 2>/dev/null || wf export wiki   # wiki-export-manifest")
    print("  wf lint                 # 0 errors")
    print("  wf review --verify-sources --dry-run   # 81 source paths must read 'fresh', not 'gone'")
    return 0


if __name__ == "__main__":
    sys.exit(main())