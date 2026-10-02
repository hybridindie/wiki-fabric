"""S1 physical domain homes (#159): layout trio, migration, writer paths,
precedence-preserving context cap.

Run: python3 -m pytest tests/test_domain_homes.py -v
"""

import sys
import importlib.util
from pathlib import Path

import pytest

_SCRIPTS = (Path(__file__).resolve().parent.parent / "scripts").resolve()
for _rel in ("cmd", "lib", ""):
    _d = _SCRIPTS / _rel if _rel else _SCRIPTS
    if str(_d) not in sys.path:
        sys.path.insert(0, str(_d))

import layout
import ontology


class TestDomainHomeLayout:
    def test_home_trio_paths(self, tmp_path):
        assert layout.domain_home(tmp_path, "godot", "domain_concepts_home") == \
            tmp_path / "domains" / "godot" / "concepts"
        assert layout.domain_home(tmp_path, "godot", "domain_questions_home") == \
            tmp_path / "domains" / "godot" / "questions"
        assert layout.domain_home(tmp_path, "godot", "domain_syntheses_home") == \
            tmp_path / "domains" / "godot" / "syntheses"

    def test_undeclared_kind_rejected(self, tmp_path):
        with pytest.raises(KeyError):
            layout.domain_home(tmp_path, "godot", "concepts")  # not a segment id

    def test_canonical_name_expected(self, tmp_path):
        # the caller canonicalizes; layout composes literally
        assert layout.domain_home(tmp_path, "agent-systems", "domain_concepts_home") \
            .name == "concepts"


class TestRelocateConcepts:
    def _fabric(self, tmp_path, ontology_text="## Domains\n- **godot** — x\n\n## Aliases\n- `godot-systems` -> `godot`\n"):
        (tmp_path / "domains").mkdir(parents=True)
        (tmp_path / "domains" / "ontology.md").write_text(ontology_text)
        (tmp_path / "concepts").mkdir(parents=True)
        (tmp_path / "registry").mkdir(parents=True)
        rc = importlib.util.spec_from_file_location(
            "reloc", _SCRIPTS / "cmd/relocate-concepts.py")
        m = importlib.util.module_from_spec(rc)
        sys.modules["reloc"] = m
        rc.loader.exec_module(m)
        return m

    def test_alias_bound_concept_moves(self, tmp_path, monkeypatch):
        m = self._fabric(tmp_path)
        monkeypatch.setattr(m, "CORPUS_ROOT", tmp_path)
        src = tmp_path / "concepts" / "concept-mesh.md"
        src.write_text("---\ntype: concept\nid: concept-mesh\ndomain: [godot-systems]\nclaims:\n  - \"[[claim-a]]\"\n---\n\n# c\n")
        n = m.migrate()
        assert n == 1
        assert (tmp_path / "domains" / "godot" / "concepts" / "concept-mesh.md").exists()
        assert not src.exists()

    def test_unbound_stays_flat(self, tmp_path, monkeypatch):
        m = self._fabric(tmp_path)
        monkeypatch.setattr(m, "CORPUS_ROOT", tmp_path)
        src = tmp_path / "concepts" / "concept-vague.md"
        src.write_text("---\ntype: concept\nid: concept-vague\n---\n\n# c\n")
        assert m.migrate() == 0
        assert src.exists()

    def test_idempotent(self, tmp_path, monkeypatch):
        m = self._fabric(tmp_path)
        monkeypatch.setattr(m, "CORPUS_ROOT", tmp_path)
        src = tmp_path / "concepts" / "concept-mesh.md"
        src.write_text("---\ntype: concept\ndomain: [godot-systems]\nclaims:\n  - \"[[c]]\"\n---\n\n")
        m.migrate()
        assert m.migrate() == 0  # already home

    def test_declaration_order_picks_home(self, tmp_path, monkeypatch):
        m = self._fabric(
            tmp_path,
            "## Domains\n- **godot** — x\n- **agent-systems** — y\n\n## Aliases\n- `godot-systems` -> `godot`\n")
        monkeypatch.setattr(m, "CORPUS_ROOT", tmp_path)
        src = tmp_path / "concepts" / "concept-multi.md"
        src.write_text("---\ntype: concept\ndomain: [godot-systems, agent-systems]\nclaims:\n  - \"[[c]]\"\n---\n\n")
        m.migrate()
        assert (tmp_path / "domains" / "godot" / "concepts" / "concept-multi.md").exists()
        # frontmatter keeps the full binding
        txt = (tmp_path / "domains" / "godot" / "concepts" / "concept-multi.md").read_text()
        assert "godot-systems" in txt and "agent-systems" in txt


class TestSynthesizeDomainHomeWrite:
    def test_bound_concept_written_under_domain(self, tmp_path, monkeypatch):
        spec = importlib.util.spec_from_file_location("syn_h", _SCRIPTS / "cmd/synthesize.py")
        syn = importlib.util.module_from_spec(spec)
        sys.modules["syn_h"] = syn
        spec.loader.exec_module(syn)
        (tmp_path / "domains" / "godot" ).mkdir(parents=True)
        (tmp_path / "domains" / "ontology.md").write_text(
            "## Domains\n- **godot** — x\n\n## Aliases\n- `godot-systems` -> `godot`\n")
        monkeypatch.setattr(syn, "VAULT_ROOT", tmp_path)
        cluster = [{"stem": "claim-godot-agents-x-md", "statement": "mesher greedy",
                    "status": "supported", "confidence": "medium"}]
        path, _n = syn.write_concept_page("mesh-test", cluster, {"definition": "d"},
                                          dry_run=False) if "dry_run" in syn.write_concept_page.__code__.co_varnames else (None, None)
        # fallback: call the real signature and inspect the write path
        if path is None:
            # write_concept_page writes via VAULT_ROOT-derived layout; run and check
            import inspect
            path = syn.write_concept_page("mesh-test", cluster, {"definition": "d"})
        assert "domains" in str(path) and "godot" in str(path), str(path)


class TestTierSharedCap:
    """Precedence-preserving cap: P2 survives a P1 flood (a global cut always
    hid the domain tier on crowded tasks — the relocation's own payoff was
    unreachable). Absent tiers release their reservation; single-tier floods
    fill to max_items."""

    def _pages(self):
        pages = []
        import datetime
        for i in range(12):
            pages.append({"posix": f"evidence/claims/claim-c{i}.md", "rel": None,
                          "stem": f"claim-c{i}", "fm": {"status": "supported",
                          "source_refs": [{"quote": "x", "locator": "L1"}]}, "body": "token rotation " + str(i),
                          "type": "claim", "scope": "global", "path": None})
        pages.append({"posix": "domains/godot/concepts/concept-mesh.md", "rel": None,
                      "stem": "concept-mesh", "fm": {"status": "supported", "domain": ["godot"]},
                      "body": "# meshing pattern for godot scenes", "type": "concept",
                      "scope": "domain", "path": None})
        return pages, datetime

    def test_p2_survives_p1_flood(self):
        import context as ctx
        pages, _ = self._pages()
        sel, exc = ctx.select_context(pages, "godot meshing", [], None, __import__("datetime").date.today(), max_items=8)
        prios = {s["priority"] for s in sel}
        assert "P2-domain" in prios, [ (s["priority"], s.get("path")) for s in sel ]

    def test_single_tier_fills(self):
        import context as ctx
        pages, dt = self._pages()
        only_p3 = [p for p in pages if p["type"] != "concept"]
        # claims are P1; patterns P3 — with only P3 present, max filled
        p3s = [{"posix": f"patterns/p-{i}.md", "rel": None, "stem": f"p-{i}",
                "fm": {"status": "recommended"}, "body": "token rotation",
                "type": "pattern", "scope": "global", "path": None} for i in range(6)]
        sel, _ = ctx.select_context(p3s, "token rotation", [], None, dt.date(2026, 10, 1), max_items=3)
        assert len(sel) == 3

    def test_absent_tiers_release_reservation(self):
        import context as ctx
        pages, dt = self._pages()
        p3s = [{"posix": f"patterns/p-{i}.md", "rel": None, "stem": f"p-{i}",
                "fm": {"status": "recommended"}, "body": "token rotation",
                "type": "pattern", "scope": "global", "path": None}
               for i in range(2)]
        sel, _ = ctx.select_context(p3s, "token rotation", [], None, dt.date(2026, 10, 1), max_items=2)
        assert len(sel) == 2  # no phantom P1/P2 slots


class TestQuestionsDomainRouting:
    def test_bound_question_moves_under_domain(self, tmp_path, monkeypatch):
        _spec = importlib.util.spec_from_file_location("pq_h", _SCRIPTS / "cmd/promote-questions.py")
        pq = importlib.util.module_from_spec(_spec)
        sys.modules["pq_h"] = pq
        _spec.loader.exec_module(pq)
        (tmp_path / "domains").mkdir(parents=True, exist_ok=True)
        (tmp_path / "domains" / "ontology.md").write_text(
            "## Domains\n- **godot** — x\n")
        prop_dir = tmp_path / "registry" / "question-proposals"
        prop_dir.mkdir(parents=True)
        prop = prop_dir / "question-abc.md"
        prop.write_text("---\ntype: question\nid: question-abc\nquestion: why?\n"
                        "domain: [godot]\nstatus: proposed\n---\n\nbody\n")
        monkeypatch.setattr(pq, "CORPUS_ROOT", tmp_path)
        monkeypatch.setattr(pq, "PROPOSALS_DIR", prop_dir)
        monkeypatch.setattr(pq, "QUESTIONS_DIR", tmp_path / "questions")
        assert pq.apply_question(prop)
        assert (tmp_path / "domains" / "godot" / "questions" / "question-abc.md").exists()
        assert "status: open" in (tmp_path / "domains" / "godot" / "questions" / "question-abc.md").read_text()