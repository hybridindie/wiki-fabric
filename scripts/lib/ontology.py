"""ontology.py — single truth for the domain ontology's machine-readable shape.

The ontology (domains/ontology.md, type: ontology) is the corpus's domain
vocabulary: canonical names (## Domains bullets), alternate spellings
(## Aliases: `alias` -> `canonical`), and the shared tag lexicon (## Shared
tag set). Before this module, each consumer parsed its own dialect — context
knew aliases, propose-domains didn't (re-proposing alias spellings as new
domains), synthesize hardcoded a keyword heuristic, lint had no vocabulary
gate. One parser, one resolver; every consumer imports from here.

Ontology shape (written by promote-domains --apply; seeded once per fabric):

    ## Domains
    - **godot** — game engine domain (human-approved 2026-10-01)

    ## Aliases
    - `godot-systems` -> `godot`

    ## Shared tag set (lowercase)
    - Cross-cutting: `agent`, `mcp`, ...

A page's `domain:` frontmatter ([godot-systems]) resolves to the canonical
name (godot) through the alias map — pages never need re-tagging when the
vocabulary renames; the map is the compatibility layer.
"""
import re

_BULLET_RE = re.compile(r"-\s+\*\*([a-z0-9][a-z0-9-]*)\*\*")
_ALIAS_RE = re.compile(r"-\s+`?([a-z0-9][a-z0-9-]*)`?\s*(?:->|←)\s*`?([a-z0-9][a-z0-9-]*)`?")
_TAG_LINE_RE = re.compile(r"-\s+[A-Za-z-]+:\s*(.+)$")


def parse(text_or_body):
    """Parse ontology text → {'domains': set, 'aliases': {alias: canonical},
    'tags': set}. Sections are line-scoped (## Domains / ## Aliases / ## Shared
    tag set); malformed sections parse to what they can — consumers degrade
    (empty vocabulary binds nothing, the honest gate)."""
    domains, aliases, tags = set(), {}, set()
    section = None
    for line in (text_or_body or "").splitlines():
        s = line.strip()
        if s.startswith("## "):
            section = s.lstrip("# ").strip().lower()
            continue
        if s.startswith("##") or not s:
            continue
        if section == "domains":
            m = _BULLET_RE.match(s)
            if m:
                domains.add(m.group(1))
        elif section == "aliases":
            m = _ALIAS_RE.match(s)
            if m:
                aliases[m.group(1)] = m.group(2)
        elif section is not None and section.startswith("shared tag"):
            m = _TAG_LINE_RE.match(s)
            if m:
                tags.update(t.strip().strip("`") for t in m.group(1).split(",") if t.strip())
    return {"domains": domains, "aliases": aliases, "tags": tags}


def canonicalize(declared, onto):
    """declared domain spelling(s) → canonical name(s) via the alias map.
    Unknown declarations resolve to nothing (vocabulary gate stays honest:
    a page declaring an un-approved domain binds nowhere). Accepts a single
    string, a list, or a set."""
    if isinstance(declared, str):
        declared = [declared]
    out = set()
    for d in declared or ():
        d = str(d).strip()
        if not d:
            continue
        c = onto["aliases"].get(d, d)
        if c in onto["domains"]:
            out.add(c)
    return out


def all_spellings(onto):
    """Canonical names + alias keys — every matchable spelling (retrieval,
    propose-domains known-checks, lint vocabulary matching)."""
    return onto["domains"] | set(onto["aliases"].keys())