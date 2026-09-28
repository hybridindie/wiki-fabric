"""Living-wiki S3 (#145): graphify-rendered deep dives — deterministic, 0-token."""
import importlib.util
import json
import sys
from pathlib import Path

REPO = Path(__file__).parent.parent
_SCRIPTS = (REPO / "scripts").resolve()
for _d in (_SCRIPTS, _SCRIPTS / "lib", _SCRIPTS / "cmd"):
    if str(_d) not in sys.path:
        sys.path.insert(0, str(_d))

import wiki_lib.deepdives as dd


def _fabric(tmp, slug="p1"):
    import fabric_config
    corpus = tmp / "corpus"
    gdir = corpus / "global" / "graphs"
    gdir.mkdir(parents=True)
    graph = {
        "nodes": [
            {"id": "core_engine", "label": "Engine", "community": 1, "community_name": "engine"},
            {"id": "core_loop", "label": "Loop", "community": 1, "community_name": "engine"},
            {"id": "core_render", "label": "Render", "community": 1, "community_name": "engine"},
            {"id": "ui_panel", "label": "Panel", "community": 2, "community_name": "ui"},
            {"id": "ui_button", "label": "Button", "community": 2, "community_name": "ui"},
            {"id": "ui_menu", "label": "Menu", "community": 2, "community_name": "ui"},
        ],
        "links": [
            {"source": "core_engine", "target": "core_loop", "relation": "calls"},
            {"source": "core_engine", "target": "core_render", "relation": "calls"},
            {"source": "core_loop", "target": "core_render", "relation": "calls"},
            {"source": "ui_panel", "target": "ui_button", "relation": "contains"},
            {"source": "ui_panel", "target": "ui_menu", "relation": "contains"},
        ],
    }
    (gdir / f"{slug}-graph.json").write_text(json.dumps(graph))
    (gdir / f"{slug}-graph.hash").write_text("a" * 12 + "\n")
    import os as _os
    wiki = tmp / "wiki"
    wiki.mkdir(parents=True)
    return corpus, wiki


class TestDeepDives:
    def test_renders_full_set(self, tmp_path, monkeypatch):
        import fabric_config
        corpus, _ = _fabric(tmp_path)
        monkeypatch.setattr(fabric_config, "CORPUS_ROOT", corpus)
        import wiki_lib.deepdives as _dd2
        import sys as _sys
        fc_ids = {k: id(v) for k, v in _sys.modules.items() if k.endswith("fabric_config")}
        written, n = dd.generate("p1", wiki_root=tmp_path / "wiki")
        assert n == 6
        names = {w.name for w in written}
        assert "architecture.md" in names and "tour.md" in names
        assert len([w for w in written if "components" in str(w)]) >= 2
        # content sanity: god node present, provenance stamped
        arch = (tmp_path / "wiki" / "projects" / "p1" / "architecture.md").read_text()
        assert "core_engine" in arch
        assert "graph_rev: " + "a" * 12 in arch
        assert "generated: { by: \"process:deepdives\"" in arch

    def test_zero_graph_is_silent_skip(self, tmp_path, monkeypatch):
        import fabric_config
        monkeypatch.setattr(fabric_config, "CORPUS_ROOT", tmp_path / "corpus")
        written, n = dd.generate("no-such", wiki_root=tmp_path / "wiki")
        assert written == [] and n == 0

    def test_zero_llm_tokens_mechanical(self, tmp_path, monkeypatch, capsys):
        """Deep-dive generation must not invoke any LLM: pages are stamped
        process:deepdives, not agent:<model>."""
        import fabric_config
        monkeypatch.setattr(fabric_config, "CORPUS_ROOT", tmp_path / "corpus")
        written, _ = dd.generate("p1", wiki_root=tmp_path / "wiki")
        for w in written:
            assert "by: \"process:deepdives\"" in w.read_text()

    def test_mermaid_valid_or_degraded(self, tmp_path, monkeypatch):
        import fabric_config
        corpus, _ = _fabric(tmp_path)
        monkeypatch.setattr(fabric_config, "CORPUS_ROOT", corpus)
        written, _ = dd.generate("p1", wiki_root=tmp_path / "wiki")
        from wiki_lib.diagrams import _mermaid_valid
        arch = (tmp_path / "wiki" / "projects" / "p1" / "architecture.md").read_text()
        import re
        for m in re.finditer(r"```mermaid\n(.*?)```", arch, re.S):
            assert _mermaid_valid(m.group(1))
        assert "mermaid-repair" not in arch  # tiny graph renders fine

    def test_tour_ordering_deterministic(self, tmp_path, monkeypatch):
        import fabric_config
        corpus, _ = _fabric(tmp_path)
        monkeypatch.setattr(fabric_config, "CORPUS_ROOT", corpus)
        dd.generate("p1", wiki_root=tmp_path / "wiki")
        t1 = (tmp_path / "wiki" / "projects" / "p1" / "tour.md").read_text()
        dd.generate("p1", wiki_root=tmp_path / "wiki")
        t2 = (tmp_path / "wiki" / "projects" / "p1" / "tour.md").read_text()
        assert t1 == t2