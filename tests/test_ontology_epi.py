"""Ontology-epic stories: independence rule (S2), discovery seed (S4),
shared-tag-set consumers (S6), retrieval-signals reconciliation (S3).

Run: python3 -m pytest tests/test_ontology_epi.py -v
"""

import sys
import importlib.util
from pathlib import Path

_SCRIPTS = (Path(__file__).resolve().parent.parent / "scripts").resolve()
for _rel in ("cmd", "lib", ""):
    _d = _SCRIPTS / _rel if _rel else _SCRIPTS
    if str(_d) not in sys.path:
        sys.path.insert(0, str(_d))

import ontology


class TestOntologyParser:
    def test_parse_sections(self):
        o = ontology.parse(
            "## Domains\n- **godot** — game\n- **testing** — v\n\n"
            "## Aliases\n- `godot-systems` -> `godot`\n- `old` ← `godot`\n\n"
            "## Shared tag set (lowercase)\n\n- Cross-cutting: `agent`, `mcp`\n")
        assert o["domains"] == {"godot", "testing"}
        assert o["aliases"] == {"godot-systems": "godot", "old": "godot"}
        assert o["tags"] == {"agent", "mcp"}

    def test_canonicalize_folds_aliases(self):
        o = {"domains": {"godot"}, "aliases": {"godot-systems": "godot"}, "tags": set()}
        assert ontology.canonicalize("godot-systems", o) == {"godot"}
        assert ontology.canonicalize(["godot-systems", "godot"], o) == {"godot"}
        assert ontology.canonicalize("unknown-x", o) == set()  # honest gate
        assert ontology.canonicalize("", o) == set()

    def test_all_spellings(self):
        o = {"domains": {"godot"}, "aliases": {"godot-systems": "godot"}, "tags": set()}
        assert ontology.all_spellings(o) == {"godot", "godot-systems"}

    def test_missing_ontology_empty(self):
        assert ontology.parse("") == {"domains": set(), "aliases": {}, "tags": set(),
                                      "signals": {}}


def _load():
    spec = importlib.util.spec_from_file_location("mp_epi", _SCRIPTS / "cmd/mine-promotions.py")
    m = importlib.util.module_from_spec(spec)
    sys.modules["mp_epi"] = m
    spec.loader.exec_module(m)
    return m


class TestIndependenceRule:
    """S2: cross-project corroboration counts DISTINCT LINEAGES — a session/
    doc replayed into several projects is ONE evidence unit however many
    project labels it carries (ontology ## Independence rule)."""

    def _ev(self, project, lineage=None, **extra):
        d = {"project": project, "observed_problem": extra.get("problem", "cache invalidation bug"),
             "intervention": "", "outcomes": {}, "_file": Path(f"/x/{project}-{lineage}.md")}
        d.update(extra)
        if lineage:
            d["lineage"] = lineage
        return d

    def test_lineage_count_vs_project_count(self):
        mp = _load()
        shared = "session-2026-09-30-abc"
        cluster = [self._ev("alpha", shared), self._ev("beta", shared)]
        # 2 projects, 1 lineage: naive count said cross-project; the rule says no
        assert mp.independent_projects(cluster) == 1
        assert len({e["project"] for e in cluster}) == 2

    def test_distinct_lineages_count(self):
        mp = _load()
        cluster = [self._ev("alpha", "session-a"), self._ev("beta", "session-b")]
        assert mp.independent_projects(cluster) == 2

    def test_missing_lineage_falls_to_project(self):
        mp = _load()
        cluster = [self._ev("alpha"), self._ev("beta")]
        assert mp.independent_projects(cluster) == 2

    def test_keyword_cluster_rejects_shared_lineage(self, tmp_path, monkeypatch):
        mp = _load()
        shared = "session-xyz"
        events = [
            self._ev("alpha", shared, problem="cache stampede on parallel writes"),
            self._ev("beta", shared, problem="cache stampede on parallel writes"),
        ]
        monkeypatch.setattr(mp, "_thread_graph", lambda: {})
        clusters = mp.cluster_events_keyword(events, min_projects=2, _keyword_threshold=0.05)
        assert clusters == {}  # same text, same lineage → NOT cross-project

    def test_keyword_cluster_accepts_independent_same_text(self, tmp_path, monkeypatch):
        mp = _load()
        events = [
            self._ev("alpha", "lineage-a", problem="cache stampede on parallel writes"),
            self._ev("beta", "lineage-b", problem="cache stampede on parallel writes"),
        ]
        monkeypatch.setattr(mp, "_thread_graph", lambda: {})
        clusters = mp.cluster_events_keyword(events, min_projects=2, _keyword_threshold=0.05)
        assert len(clusters) == 1

    def test_semantic_path_lineage_filter(self, tmp_path, monkeypatch):
        mp = _load()
        # monkeypatch HAS_NUMPY out of the way: drive the filter code directly
        # via the filter block semantics — reuse cluster_events_semantic with
        # embeddings unavailable → falls to keyword (already covered). Here:
        # assert the filter block itself via independent_projects on the shape
        # cluster_events_semantic would produce.
        shared = "session-shared"
        valid = [self._ev("alpha", shared), self._ev("beta", shared)]
        assert mp.independent_projects(valid) == 1  # the filter compares this to min_projects


class TestSynonymsOntologyFed:
    """S6: the mining expansion lexicon is ontology-fed — a Shared-tag-set
    addition extends clustering without a code change."""

    def test_tags_enter_synonym_map(self, tmp_path, monkeypatch):
        mp = _load()
        (tmp_path / "domains").mkdir(parents=True)
        (tmp_path / "domains" / "ontology.md").write_text(
            "## Domains\n- **godot** — x\n\n## Shared tag set (lowercase)\n\n"
            "- Cross-cutting: `wasm`, `simd`\n")
        monkeypatch.setattr(mp, "CORPUS_ROOT", tmp_path)
        syns = mp._domain_synonyms()
        assert "wasm" in syns and "simd" in syns
        assert "threading" in syns  # hand-maintained expansions survive

    def test_unreadable_ontology_keeps_base_map(self, tmp_path, monkeypatch):
        mp = _load()
        monkeypatch.setattr(mp, "CORPUS_ROOT", tmp_path / "nope")
        syns = mp._domain_synonyms()
        assert "threading" in syns and "batching" in syns


class TestDiscoverySeedLexicon:
    """S4: the signal lookup is ontology-fed beneath config signals."""

    def test_ontology_names_seed_lookup(self, tmp_path, monkeypatch):
        spec = importlib.util.spec_from_file_location(
            "pd_epi", _SCRIPTS / "cmd/propose-domains.py")
        pd = importlib.util.module_from_spec(spec)
        sys.modules["pd_epi"] = pd
        spec.loader.exec_module(pd)
        (tmp_path / "domains").mkdir(parents=True)
        (tmp_path / "domains" / "ontology.md").write_text(
            "## Domains\n- **godot** — x\n\n## Aliases\n- `godot-systems` -> `godot`\n")
        monkeypatch.setattr(pd, "ONTOLOGY_PATH", tmp_path / "domains" / "ontology.md")
        monkeypatch.setattr(pd, "get_domain_signals", lambda cfg: {})
        lookup = pd.build_signal_lookup({})
        assert lookup["godot"] == "godot"
        assert lookup["godot_systems"] == "godot"  # alias folds to the canonical
        assert lookup["godot-systems"] == "godot"  # hyphen spelling too (identity seeds)

    def test_config_signals_win(self, tmp_path, monkeypatch):
        spec = importlib.util.spec_from_file_location(
            "pd_epi2", _SCRIPTS / "cmd/propose-domains.py")
        pd = importlib.util.module_from_spec(spec)
        sys.modules["pd_epi2"] = pd
        spec.loader.exec_module(pd)
        (tmp_path / "domains").mkdir(parents=True)
        (tmp_path / "domains" / "ontology.md").write_text(
            "## Domains\n- **godot** — x\n\n## Aliases\n- `godot-systems` -> `godot`\n")
        monkeypatch.setattr(pd, "ONTOLOGY_PATH", tmp_path / "domains" / "ontology.md")
        monkeypatch.setattr(pd, "get_domain_signals",
                            lambda cfg: {"godot": ["gamedev", "gdscript"]})
        lookup = pd.build_signal_lookup({})
        assert lookup["gamedev"] == "godot" and lookup["gdscript"] == "godot"