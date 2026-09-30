#!/usr/bin/env python3
# okf_export.py — Render the fabric (or a scope) as a portable OKF v0.2 bundle.
#
# Usage:
#   python3 scripts/cmd/okf_export.py --out ./bundle [--scope all|global|<project|domain slug>]
#
# Deterministic: same fabric -> same bundle bytes (modulo the export log entry).
# Wikilinks resolve to bundle-relative markdown links; claim source_refs render
# as OKF sources[] + keyed footnotes; unknown fabric fields are preserved.
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

from fabric_config import CORPUS_ROOT, VAULT_ROOT, get_export_excludes

# Corpus is the export source root; the bundle's harness dirs (schemas/,
# system/, references/) are appended by scope from the harness, not here.
LINK_RE = re.compile(r"\[\[([^\]|]+)(?:\|[^\]]+)?\]\]")
RESERVED = {"index.md", "log.md"}

# Scopes that carry concepts (evidence claims ride along under their scope root)
SCOPE_ROOTS = {
    "all": None,
    "global": ("patterns", "anti-patterns", "skills", "concepts", "global",
               "schemas", "registry", "evidence", "system", "domains", "projects"),
}


def _fm_link(m, link_map):
    """Inline-link resolver for YAML scalars: replace [[stem]] with the path."""
    stem = m.group(1).strip()
    target = resolve_link(stem, link_map)
    if target is None or "<" in stem:
        return m.group(0)
    return f"{target}"


def stem_to_path_map(scope_roots, ig=None):
    """Stem -> list of bundle-relative paths (first wins on export)."""
    ig = ig or _user_ignores()
    index = {}
    ig = _user_ignores()
    for root in scope_roots:
        for p in root.rglob("*.md"):
            rel = p.relative_to(VAULT_ROOT)
            if any(x in rel.parts for x in (".git", ".venv", "node_modules", "__pycache__", ".okflint", ".pytest_cache")):
                continue
            if _ignored_by_config(rel, ig):
                continue
            index.setdefault(rel.stem.lower(), []).append(rel.as_posix())
    return index


def _user_ignores(fabric_root=None):
    """The fabric's ignore: config (#151/#153) — the SAME predicate lint uses;
    a page invisible to lint must never leak into the portable bundle. With an
    explicit --root, that root's fabric.yaml governs (a --root bundle export
    must honor the bundle's own config, not the ambient machine's)."""
    try:
        import yaml
        if fabric_root:
            cfg_file = Path(fabric_root) / "fabric.yaml"
            if cfg_file.exists():
                raw = (yaml.safe_load(cfg_file.read_text()) or {}).get("ignore") or {}
            else:
                raw = {}
            from fabric_config import get_ignores as _gi
            return _gi({"ignore": raw})
        from fabric_config import get_config, get_ignores
        return get_ignores(get_config())
    except Exception:
        return {"globs": [], "regexes": [], "compiled": []}


def _ignored_by_config(rel, ig):
    from fabric_config import is_ignored
    try:
        return is_ignored(rel.as_posix(), ig)
    except Exception:
        return False


def resolve_link(stem, link_map):
    paths = link_map.get(stem.lower())
    if not paths:
        return None
    return "/" + paths[0]


def convert_links(text, link_map):
    """[[stem]] -> [stem](/path.md); unknown stems stay as plain text."""
    def repl(m):
        stem = m.group(1).strip()
        target = resolve_link(stem, link_map)
        if target is None or stem.lower() in {"claim-<claim-slug>", "decision-<slug>"} or "<" in stem or "..." in stem:
            return m.group(0)  # keep placeholder/placeholder-ish as-is
        return f"[{stem}]({target})"
    return LINK_RE.sub(repl, text)


def render_sources(claim_fm, link_map):
    """Claim source_refs -> OKF sources[] + footnote bodies (keyed by source id)."""
    refs = claim_fm.get("source_refs") or []
    sources, footnotes = [], []
    for i, ref in enumerate(refs, 1):
        if not isinstance(ref, dict):
            continue
        src = str(ref.get("source", ""))
        stem = src.strip("[[]]").split("|")[0]
        sid = f"wf-{stem}"
        entry = {"id": sid, "resource": resolve_link(stem, link_map) or f"/{stem}"}
        if ref.get("locator"):
            entry["locator"] = str(ref["locator"])
        if ref.get("quote"):
            entry["quote"] = str(ref["quote"])[:200]
        sources.append(entry)
        footnotes.append(f"[^{sid}]: {stem}")
    return sources, footnotes


def export(out_dir, scope="all", dry_run=False, root=None):
    out = Path(out_dir).resolve()
    if root:
        global VAULT_ROOT
        VAULT_ROOT = Path(root).resolve()
    if dry_run:
        print(f"[DRY RUN] would export to {out}")
        return 0

    # Scope roots
    if scope == "all":
        roots = [VAULT_ROOT]
    elif scope == "global":
        roots = [VAULT_ROOT / d for d in ("patterns", "anti-patterns", "skills", "concepts", "global", "registry", "schemas", "system", "evidence") if (VAULT_ROOT / d).exists()]
    else:
        one = [VAULT_ROOT / "projects" / scope, VAULT_ROOT / "evidence" / "raw" / scope]
        roots = [r for r in one if r.exists()]
        if not roots:
            print(f"Error: unknown scope {scope!r}", file=sys.stderr)
            return 1

    ig = _user_ignores(VAULT_ROOT if root else None)
    link_map = stem_to_path_map(roots, ig)
    concept_count = 0

    for root in roots:
        for p in root.rglob("*.md"):
            rel = p.relative_to(VAULT_ROOT)
            parts = rel.parts
            posix_str = rel.as_posix()
            if _ignored_by_config(rel, ig):
                continue
            user_excludes = tuple(x.lstrip("./") for x in get_export_excludes())
            if any(x in parts for x in (".git", ".venv", "node_modules", "__pycache__", ".okflint", ".pytest_cache", ".obsidian", ".opencode")):
                continue
            excluded_by_user = False
            for pat in user_excludes:
                pat = str(pat).rstrip("*").rstrip("/")
                if pat and posix_str.startswith(pat):
                    excluded_by_user = True
                    break
            if excluded_by_user:
                continue
            if rel.name in ("AGENTS.md", "CLAUDE.md", "README.md", "CONTRIBUTING.md", "LICENSE", "index.md", "log.md"):
                continue
            # test scaffolds + violation fixtures are not bundle concepts
            posix_str = rel.as_posix()
            if posix_str.startswith(("evaluations/", "tests/", "scripts/", ".okflint/", ".pytest_cache/")):
                continue
            # Raw captures + non-concept files export verbatim under references/
            # (OKF §6.3: references/ mirrors external material; not concept docs)
            text = p.read_text(encoding="utf-8", errors="replace")
            m = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.DOTALL)
            if not m:
                dest = out / "references" / rel
                if not dry_run:
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    dest.write_text(text)
                concept_count += 1
                continue
            fm, body = m.group(1), m.group(2)
            try:
                fmd = yaml.safe_load(fm) or {}
            except yaml.YAMLError:
                fmd = {}
            body2 = convert_links(body, link_map)

            # claim: source_refs -> sources[] + footnotes
            fmd2 = dict(fmd)
            if fmd.get("type") == "claim" and fmd.get("source_refs"):
                sources, footnotes = render_sources(fmd, link_map)
                if sources:
                    fmd2["sources"] = sources
                    body2 = body2.rstrip() + "\n\n" + "\n".join(footnotes) + "\n"

            from wf_common import dump_frontmatter
            fm_yaml = dump_frontmatter(fmd2)
            # Wikilinks inside frontmatter values resolve too (resource, source_refs)
            fm_yaml = LINK_RE.sub(lambda m: _fm_link(m, link_map), fm_yaml)
            dest = out / rel
            if not dry_run:
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_text(f"---\n{fm_yaml}---\n{body2}")
            concept_count += 1

    # index.md per top dir + root index with okf_version
    if not dry_run:
        (out / "index.md").write_text(
            "---\nokf_version: \"0.2\"\n---\n\n# Wiki Fabric Export\n\n"
            f"Scope: {scope}. Exported {date.today().isoformat()}.\n\n"
            "Concepts live in mirrored subdirectories; each directory carries an index.md.\n")
    print(f"exported {concept_count} concept docs -> {out} (scope: {scope})")
    return 0


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Export fabric as a portable OKF v0.2 bundle")
    parser.add_argument("--out", required=True, help="Output bundle directory")
    parser.add_argument("--scope", default="all", help="all | global | <project-slug | domain-name>")
    parser.add_argument("--root", default=None, help="Fabric root (default: repo parent of this script)")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    return export(args.out, args.scope, args.dry_run, args.root)


if __name__ == "__main__":
    sys.exit(main())