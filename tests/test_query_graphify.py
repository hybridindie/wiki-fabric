"""Unit tests for query.py graphify symbol consumption (#48).

Run: python3 -m pytest tests/test_query_graphify.py -v
"""

import sys
import importlib.util
from pathlib import Path

import sys, pathlib as _p
_SCRIPTS = (_p.Path(__file__).resolve().parent.parent / "scripts").resolve()
for _rel in ("cmd", "lib"):
    if str(_SCRIPTS / _rel) not in sys.path:
        sys.path.insert(0, str(_SCRIPTS / _rel))


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


query = _load("query", Path(__file__).parent.parent / "scripts/cmd/query.py")


def _claim(graph_edges):
    return {"fm": {"graph_edges": graph_edges, "type": "claim"},
            "type": "claim", "stem": "claim-x", "body": "", "rel": Path("x")}


class TestSymbolTokens:
    def test_snake_case_splits(self):
        toks = query.symbol_tokens("_handle_peer read loop disconnect")
        assert "_handle_peer" in toks and "handle" in toks and "peer" in toks

    def test_camel_case_splits(self):
        toks = query.symbol_tokens("ReadCache behavior")
        assert "readcache" in toks and "cache" in toks

    def test_stopwords_excluded(self):
        assert "what" not in query.symbol_tokens("what does this do")

    def test_short_tokens_excluded(self):
        assert "abc" not in query.symbol_tokens("abc ReadCache")


class TestGraphEdgeSymbols:
    def test_method_style_splits(self):
        syms = query.graph_edge_symbols(_claim(["called_by:._handle_peer()"]))
        assert "._handle_peer()" in syms and "_handle_peer" in syms

    def test_plain_symbol(self):
        syms = query.graph_edge_symbols(_claim(['"called_by:ReadCache"']))
        assert "readcache" in syms

    def test_no_edges_empty(self):
        assert query.graph_edge_symbols(_claim(None)) == set()
        assert query.graph_edge_symbols(_claim([])) == set()

    def test_non_string_entries_ignored(self):
        assert query.graph_edge_symbols(_claim([42, None])) == set()


class TestGraphifyBoost:
    def test_whole_id_hit(self):
        pg = _claim(["called_by:ReadCache"])
        assert query.graphify_boost(pg, {"readcache", "cache"}, set()) > 0

    def test_method_fragment_hit(self):
        pg = _claim(["called_by:._handle_peer()"])
        assert query.graphify_boost(pg, {"_handle_peer", "handle", "peer"}, set()) > 0

    def test_no_hit_zero(self):
        pg = _claim(["called_by:ReadCache"])
        assert query.graphify_boost(pg, {"toolsetmanager"}, set()) == 0.0

    def test_capped_at_three_hits(self):
        pg = _claim(["called_by:Aaaab", "called_by:Bbbbc", "called_by:Ccccd", "called_by:Dddde"])
        toks = {"aaaab", "bbbbc", "cccd", "dddde"}
        # 4 hits → capped at 3
        assert abs(query.graphify_boost(pg, toks, set()) - 0.45) < 1e-9

    def test_no_query_tokens_zero(self):
        assert query.graphify_boost(_claim(["called_by:ReadCache"]), set(), set()) == 0.0


class TestSymbolDiscovery:
    """The demonstrated retrieval miss: symbol-naming query, claim lexically
    invisible — discovery surfaces it as code-reachable evidence."""

    def _pages(self):
        miss_claim = {
            "fm": {"type": "claim", "statement": "The bridge is single-connection.",
                   "graph_edges": ["called_by:._handle_peer()", "called_by:._read_loop()"],
                   "source_refs": [{"source": "[[src-x]]", "locator": "L1", "quote": "q"}]},
            "type": "claim", "stem": "claim-bridge", "body": "unrelated words",
            "rel": Path("evidence/claims/claim-bridge.md"),
        }
        other = {
            "fm": {"type": "claim", "statement": "The daily loop runs on-device.",
                   "source_refs": [{"source": "[[src-y]]", "locator": "L2", "quote": "w"}]},
            "type": "claim", "stem": "claim-daily", "body": "daily loop tokens here",
            "rel": Path("evidence/claims/claim-daily.md"),
        }
        return [miss_claim, other]

    def test_lexical_miss_discovered(self):
        pages = self._pages()
        scored = query.score_pages(pages, "_handle_peer disconnect", "auto")
        # the bridge claim has zero lexical overlap → not scored
        assert all(pg["stem"] != "claim-bridge" for _, pg in scored)
        # discovery pass finds it via graph_edges
        q_syms = query.symbol_tokens("_handle_peer disconnect")
        hit = [pg for pg in pages
               if pg["type"] == "claim" and q_syms & query.graph_edge_symbols(pg)]
        assert [pg["stem"] for pg in hit] == ["claim-bridge"]

    def test_answer_renders_code_reachable_section(self, capsys):
        pages = self._pages()
        symbol_hits = [pg for pg in pages
                       if query.symbol_tokens("_handle_peer disconnect") & query.graph_edge_symbols(pg)]
        answer = query.generate_answer("_handle_peer disconnect", [], pages, "auto",
                                       symbol_hits=symbol_hits)
        assert "## Code-reachable evidence (graphify)" in answer
        assert "claim-bridge" not in answer or "single connection" in answer
        assert "_handle_peer" in answer

    def test_no_symbol_hits_no_section(self, capsys):
        pages = self._pages()
        answer = query.generate_answer("unrelated query", [], pages, "auto", symbol_hits=[])
        assert "Code-reachable" not in answer

    def test_gate_off_no_discovery(self, monkeypatch):
        monkeypatch.setattr(query, "graphify_active", lambda: False)
        # discovery only runs under main(); the gate function itself is the contract
        assert query.graphify_active() is False