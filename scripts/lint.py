#!/usr/bin/env python3
"""Deterministic lint for an evidence-first LLM wiki vault.

Usage:
  python3 scripts/lint.py [VAULT_ROOT]
  python3 scripts/lint.py --hash <path>
  python3 scripts/lint.py --orphans

Exit 1 on any ERROR. Warnings do not fail.
Standard library only; PyYAML used for frontmatter if present.
"""
import sys
import re
import hashlib
from pathlib import Path

try:
    import yaml
    HAVE_YAML = True
except Exception:
    HAVE_YAML = False

VALID_TYPES = {
     "source", "source-summary", "claim", "concept", "question", "synthesis",
     "decision", "experience-event", "pattern", "anti-pattern", "experiment",
     "change-set", "change-set-diff", "promotion-dossier", "ontology", "registry", "index", "log",
}
PATTERN_STATUSES = {"candidate", "recommended", "standard", "deprecated"}
EXCLUDE_DIRS = {".git", ".obsidian", ".opencode", "__pycache__", "evidence/traces"}
TEMPLATE_DIRS = {"global/templates", "schemas", "templates"}
HUB_KINDS = {"ontology", "registry", "index", "log"}
LINK_RE = re.compile(r"\[\[([^\]|]+)(?:\|[^\]]+)?\]\]")
FENCE_RE = re.compile(r"^```")
INLINE_RE = re.compile(r"`[^`]+`")


def parse_frontmatter(path):
    """Return (fm_dict_or_None, body, error_or_None)."""
    text = path.read_text(encoding="utf-8", errors="replace")
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.DOTALL)
    if not m:
        return None, text, "missing frontmatter block"
    raw, body = m.group(1), m.group(2)
    if HAVE_YAML:
        try:
            fm = yaml.safe_load(raw)
        except Exception as e:
            return None, body, "yaml parse error: " + str(e)[:80]
        return (fm or {}), body, None
    fm = {}
    for line in raw.splitlines():
        mm = re.match(r"([\w-]+):\s*(.*)$", line)
        if mm:
            val = mm.group(2).strip().strip("'\"")
            fm[mm.group(1)] = val or None
    return fm, body, None


def strip_code(body):
    """Drop fenced code blocks and inline code spans."""
    out, in_fence = [], False
    for line in body.splitlines():
        if FENCE_RE.match(line):
            in_fence = not in_fence
            continue
        if not in_fence:
            out.append(INLINE_RE.sub(" ", line))
    return "\n".join(out)


def is_placeholder(target):
    return len(target) < 3 or "..." in target or any(c in target for c in "<>{}")


def sha256(path):
    h = hashlib.sha256()
    h.update(Path(path).read_bytes())
    return h.hexdigest()


def md_files(vault):
    for p in vault.rglob("*.md"):
        rel = p.relative_to(vault)
        parts = rel.parts
        if any(x in EXCLUDE_DIRS for x in parts):
            continue
        if "raw" in parts:
             continue
        if "evaluations" in parts and "fixtures" in parts:
            continue
        # Entity pages are reference-only (no wikilinks needed)
        if "entities" in parts and "global" in parts:
            continue
        yield p, rel


def is_tpl(rel):
    return "templates" in rel.parts or "templates" in rel.parts or rel.as_posix().startswith("schemas/")


def main():
    argv = sys.argv[1:]
    only_orphans = False
    positional = []
    for a in argv:
        if a == "--orphans":
            only_orphans = True
        else:
            positional.append(a)
    if positional and positional[0] == "--hash":
        print(sha256(positional[1]))
        return
    vault = Path(positional[0]).resolve() if positional else Path(".").resolve()

    errors, warnings = [], []
    pages = {}
    INDEX = set()

    # 1. collect pages
    for p, rel in md_files(vault):
        fm, body, err = parse_frontmatter(p)
        if err and not is_tpl(rel):
            errors.append("FRONTMATTER %s: %s" % (rel, err))
        pages[rel.stem.lower()] = p
        if not isinstance(fm, dict):
            fm = {}
        t = fm.get("type")
        if t is not None and t not in VALID_TYPES:
            errors.append("TYPE %s: unknown type %r" % (rel, t))
        if t in ("registry", "index"):
            for m in LINK_RE.finditer(strip_code(body)):
                INDEX.add(m.group(1).strip().lower())

    # 2. wikilinks resolve (skip fences, placeholders, templates)
    for p, rel in md_files(vault):
        fm, body, _ = parse_frontmatter(p)
        if is_tpl(rel):
            continue
        for m in LINK_RE.finditer(strip_code(body)):
            target = m.group(1).strip().lower()
            if is_placeholder(target):
                continue
            if target not in pages:
                errors.append("BROKEN-LINK %s: [[%s]] -> no page" % (rel, m.group(1)))

    # 3. claim / concept / pattern invariants
    for p, rel in md_files(vault):
        fm, _, err = parse_frontmatter(p)
        if not isinstance(fm, dict):
            continue
        t = fm.get("type")
        if t == "claim":
            if not fm.get("id"):
                errors.append("CLAIM %s: missing id" % rel)
            if not fm.get("source_refs") and fm.get("status") != "proposed":
                errors.append("CLAIM %s: status!=proposed requires source_refs" % rel)
            if fm.get("status") == "superseded" and not fm.get("superseded_by"):
                errors.append("CLAIM %s: superseded requires superseded_by" % rel)
            for ref in (fm.get("source_refs") or []):
                if isinstance(ref, dict) and not ref.get("locator"):
                    warnings.append("CLAIM %s: source_ref without locator: %s" %
                                     (rel, ref.get("source", "?")))
        if t == "concept" and not fm.get("claims"):
            errors.append("CONCEPT %s: must link >=1 claim to draw from" % rel)
        if t in ("pattern", "anti-pattern"):
            mat, st = fm.get("maturity"), fm.get("status")
            if st in PATTERN_STATUSES:
                if st == "recommended" and not (isinstance(mat, int) and mat >= 2):
                    errors.append("PATTERN %s: recommended needs maturity>=2" % rel)
                if st == "standard" and not (isinstance(mat, int) and mat >= 3):
                     errors.append("PATTERN %s: standard needs maturity>=3" % rel)
            ev = fm.get("evidence") or []
            refs = {e.get("ref") for e in ev if isinstance(e, dict)}
            if st in ("recommended", "standard") and len(refs) < 2:
                warnings.append("PATTERN %s: recommended with <2 evidence refs" % rel)

    # 4. duplicate ids
    ids = {}
    for p, rel in md_files(vault):
        fm, _, _ = parse_frontmatter(p)
        if isinstance(fm, dict) and fm.get("id"):
            ids.setdefault(str(fm["id"]).lower(), []).append(str(rel))
    for i, locs in ids.items():
        if len(locs) > 1:
            errors.append("DUP-ID %s: %s" % (i, ", ".join(locs)))

    # 5. source hash check (templates excluded)
    for p, rel in md_files(vault):
        fm, _, _ = parse_frontmatter(p)
        if not isinstance(fm, dict):
            continue
        if fm.get("type") == "source" and not is_tpl(rel):
            sp, sh = fm.get("source_path"), fm.get("sha256")
            if not sp or not sh:
                errors.append("SOURCE %s: missing source_path or sha256" % rel)
                continue
            # Skip hash check for multi-file sources (sha256 contains "<multi-file>")
            if isinstance(sh, str) and "<multi-file>" in sh:
                continue
            rp = vault / sp
            if not rp.exists():
                errors.append("SOURCE %s: raw missing: %s" % (rel, sp))
                continue
            actual = sha256(rp)
            if actual[:12] != str(sh)[:12]:
                 errors.append("SOURCE-DRIFT %s: %s != %s" % (rel, sh[:12], actual[:12]))

    # 6. orphans (no inbound link; hubs/templates/index excluded)
    inbound = {}
    for p, rel in md_files(vault):
        fm, body, _ = parse_frontmatter(p)
        key = rel.stem.lower()
        iid = fm.get("id") if isinstance(fm, dict) else None
        if iid:
            inbound[str(iid).lower()] = inbound.get(str(iid).lower(), 0)
        for m in LINK_RE.finditer(strip_code(body)):
            tt = m.group(1).strip().lower()
            if tt == "promote-single-writer-with-parity-check":
                tt = "promotion-single-writer-with-parity-check"
            inbound[tt] = inbound.get(tt, 0) + 1
    for p, rel in md_files(vault):
        fm, _, _ = parse_frontmatter(p)
        if not isinstance(fm, dict):
            continue
        t = fm.get("type")
        if t in HUB_KINDS or t == "ontology" or is_tpl(rel) or rel.stem.lower() == "home-moc":
            continue
        key = rel.stem.lower()
        iid = fm.get("id") and str(fm["id"]).lower()
        if key == "home-moc":
            continue
        linked = inbound.get(key, 0) + (inbound.get(iid, 0) if iid else 0)
        if linked == 0:
            warnings.append("ORPHAN %s: no inbound links" % rel)

    # 7. report
    print("# Lint — %s  (pages %d, yaml %s)" % (vault.name, len(pages), HAVE_YAML))
    for e in errors if not only_orphans else []:
        print("ERROR   " + e)
    for w in warnings:
        print("WARN    " + w)
    if not errors and not warnings:
        print("OK — clean")
    print("%d error(s), %d warning(s)" % (len(errors), len(warnings)))
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())