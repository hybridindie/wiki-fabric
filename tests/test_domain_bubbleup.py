"""Domain bubble-up: concepts bound to ontology domains surface in the P2 tier.

Two bugs found when_domains "bubbled up" nothing (10,435 pages: 10,425 scope=global):
  1. select_context's P3/global branch hardcoded ('pattern','anti-pattern','skill')
     while the tier LIST declared 'concept' too — every concept silently never
     scored (no reason, no exclusion record) against the tier list's own contract.
  2. Concepts declare `domain: [godot-systems]` but scope-derivation is PATH-only
     (concepts/ → global): the declaration never promoted them to the domain tier,
     and the ontology listed zero approved domains besides.

Run: python3 -m pytest tests/test_domain_bubbleup.py -v
"""

import sys
import importlib.util
from pathlib import Path
from datetime import date

_SCRIPTS = (Path(__file__).resolve().parent.parent / "scripts").resolve()
for _rel in ("cmd", "lib", ""):
    _d = _SCRIPTS / _rel if _rel else _SCRIPTS
    if str(_d) not in sys.path:
        sys.path.insert(0, str(_d))

import context as ctx


def _page(posix, type_, body="", scope="global", **fm):
    return {"posix": posix, "rel": Path(posix), "stem": Path(posix).stem.lower(),
            "fm": fm, "body": body, "type": type_, "scope": scope, "path": Path("/c") / posix}


def _scope(pg):
    return pg["fm"].get("scope") or (
        "domain" if pg["posix"].startswith("domains/")
        else "project" if pg["posix"].startswith("projects/")
        else "global")


TODAY = date(2026, 10, 1)


def _pages():
    return [
        _page("domains/ontology.md", "ontology",
              body="## Domains\n- **godot** — game engine domain\n- **testing** — test domain\n\n"
                   "## Aliases\n- `godot-systems` -> `godot`\n",
              scope="domain"),
        _page("concepts/concept-godot-mesh.md", "concept",
              body="# Concept\nChunk meshing lives in the godot scene pipeline.",
              domain=["godot-systems"], status="supported", ),
        _page("concepts/concept-unbound.md", "concept",
              body="# Concept\nSomething about scheduling entirely different.",
              domain=["agent-systems"], status="supported", ),
        _page("patterns/pattern-godot-perf.md", "pattern",
              body="# Pattern\nKeep mesher allocation outside the frame loop.",
              status="recommended", ),
        _page("projects/godot-mcp/decisions/decision-x.md", "decision",
              body="# Decision\nUse server-side meshing.", scope="project"),
    ]


class TestOntologyDomains:
    def test_names_and_aliases_parsed(self):
        names = ctx._ontology_domains(_pages())
        assert "godot" in names and "testing" in names
        amap = getattr(ctx._ontology_domains, "aliases", {})
        assert amap.get("godot-systems") == "godot"

    def test_empty_ontology_binds_nothing(self):
        pages = [_page("domains/ontology.md", "ontology", body="## Domains\n")]
        assert ctx._ontology_domains(pages) == set()


class TestDomainBinding:
    def test_alias_declaration_resolves_canonical(self):
        pages = _pages()
        ctx._ontology_domains(pages)
        pg = [p for p in pages if p["posix"] == "concepts/concept-godot-mesh.md"][0]
        assert ctx._page_domain_canonical(pg, {"godot", "testing"}) == {"godot"}

    def test_unknown_domain_binds_nothing(self):
        pages = _pages()
        ctx._ontology_domains(pages)
        pg = [p for p in pages if p["posix"] == "concepts/concept-unbound.md"][0]
        # agent-systems declared but NOT an ontology domain (no alias, no bullet)
        assert ctx._page_domain_canonical(pg, {"godot", "testing"}) == set()


class TestConceptsMatchTierContract:
    """The P3/global branch predicate must derive from the tier LIST (single
    truth): a type declared in a tier can never be silently unscoreable."""

    def test_concept_p3_scored_when_not_domain_bound(self):
        pages = [p for p in _pages() if p["posix"] != "concepts/concept-godot-mesh.md"]
        pages.append(_page("concepts/concept-sched.md", "concept",
                           body="# Concept\nScheduling policy details.", status="supported",
                           scope="global"))
        sel, exc = ctx.select_context(pages, "scheduling policy overview", [], None, TODAY)
        p3 = [s for s in sel if s["priority"] == "P3-global"]
        assert any(s.get("path", "") == "concepts/concept-sched.md" for s in p3)

    def test_domain_bound_concept_scores_p2(self):
        sel, _ = ctx.select_context(_pages(), "godot chunk meshing", [], None, TODAY, max_items=50)
        p2 = [s for s in sel if s["priority"] == "P2-domain"]
        paths = [s.get("path", "") for s in p2]
        assert "concepts/concept-godot-mesh.md" in paths
        assert any("domain match" in (s.get("reason") or "") for s in p2)

    def test_p1_still_dominates(self):
        sel, _ = ctx.select_context(_pages(), "server-side meshing decision", [], None, TODAY, max_items=50)
        if any(s.get("path", "") == "projects/godot-mcp/decisions/decision-x.md" for s in sel):
            assert sel[0]["priority"] == "P1-project"


class TestExcludedRecordsComplete:
    """Every passed-over candidate carries an exclusion record (the silent-drop
    class must stay impossible to reintroduce)."""

    def test_no_matching_candidate_vanishes_without_record(self):
        # A non-matching page has no reason to appear (selection is relevance,
        # not inventory) — the silent-drop class was: a page whose TIER LIST
        # membership promised scoring but whose branch predicate refused it,
        # regardless of task match. So: every page that MATCHES the task must
        # appear in selected or excluded. Non-matching may be absent (correct).
        pages = _pages()
        sel, exc = ctx.select_context(pages, "godot mesher allocation unbound scheduling",
                                      [], None, TODAY, max_items=50)
        selected_paths = {s.get("path", "") for s in sel}
        excluded_paths = {e["path"] for e in exc}
        assert "domains/ontology.md" in excluded_paths  # vocabulary page: deliberate
        assert "concepts/concept-godot-mesh.md" in selected_paths  # matched, P2
        assert "concepts/concept-unbound.md" in selected_paths  # 'scheduling'/'unbound' body match, P3
        assert "patterns/pattern-godot-perf.md" in selected_paths  # matched, P3