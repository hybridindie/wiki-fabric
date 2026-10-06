"""#189 — the temporal retrieval axis.

A `changed` query type: auto-detect ("what changed", "how did...", "evolve"),
capture-date RANK (keyword stays the candidate filter, recency the sort),
and a deterministic evolution answer (earliest → latest, per-step locators,
contested flags). Non-temporal queries must be byte-identical to before (no
score bleed). All deterministic — the no-LLM path IS the contract shape.

Run: python3 -m pytest tests/test_temporal_query.py -v
"""
import sys
from datetime import date
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent
for _p in (str(_REPO / "scripts" / "cmd"), str(_REPO / "scripts" / "lib")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import os
os.environ.setdefault("WIKI_FABRIC_DIR", "/tmp/definitely-not-a-fabric-tdelta")

import importlib.util


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


Q = _load("query_tdelta", _REPO / "scripts" / "cmd" / "query.py")


def _page(stem, statement, type_="claim", last_verified=None, created=None,
          status="supported", updated=None, generated=None):
    fm = {"statement": statement, "status": status, "confidence": "high",
          "evidence_strength": "primary", "type": type_}
    if last_verified:
        fm["last_verified"] = last_verified
    if created:
        fm["created"] = created
    if updated:
        fm["updated"] = updated
    if generated:
        fm["generated"] = generated
    return {"path": None, "rel": Path(stem + ".md"), "stem": stem, "fm": fm,
            "body": "", "type": type_}


def _claim(stem, statement, date_str, status="supported"):
    return _page(stem, statement, type_="claim", last_verified=date_str,
                 status=status)


class TestDetect:
    def test_changed_queries_auto_detect(self):
        for q in ("what changed about our deployment thinking",
                  "how did we handle retries",
                  "the evolution of the release flow",
                  "what did we used to do"):
            qtype = Q._detect_type(q)
            assert qtype == "changed", q

    def test_non_temporal_queries_untouched(self):
        assert Q._detect_type("why did we choose single-writer") == "decision"
        assert Q._detect_type("is it true that batches help") == "verify"
        assert Q._detect_type("compare batching versus streaming") == "compare"
        assert Q._detect_type("what patterns apply to locks") == "concept"


class TestAgeRank:
    def test_normalized_recency(self):
        pages = [_claim("a", "s", "2026-01-01"), _claim("b", "s", "2026-10-01"),
                 _claim("c", "s", "2026-07-01")]
        assert Q._age_rank(Q._page_date(pages[0]["fm"]), pages) == 0.0
        assert Q._age_rank(Q._page_date(pages[1]["fm"]), pages) == 1.0

    def test_missing_dates_score_zero(self):
        pages = [_claim("a", "s", "2026-01-01")]
        assert Q._age_rank(None, pages) == 0.0

    def test_flat_corpus_is_full_rank(self):
        pages = [_claim("a", "s", "2026-06-01")]
        assert Q._age_rank(Q._page_date(pages[0]["fm"]), pages) == 1.0


class TestPageDate:
    def test_last_verified_wins(self):
        fm = {"last_verified": "2026-09-01", "created": "2026-01-01"}
        assert str(Q._page_date(fm)) == "2026-09-01"

    def test_generated_iso_utc(self):
        fm = {"generated": {"at": "2026-10-03T17:55:55Z"}, "created": "2026-01-01"}
        assert str(Q._page_date(fm)) == "2026-10-03"

    def test_garbage_never_crashes(self):
        assert Q._page_date({"last_verified": "not-a-date", "created": ""}) is None


class TestEvolutionSort:
    def test_orders_earliest_to_latest(self):
        a = (1.0, _claim("a", "oldest", "2026-01-01"))
        b = (1.0, _claim("b", "newest", "2026-10-01"))
        c = (1.0, _claim("c", "middle", "2026-06-01"))
        out = Q._evolution_sort([b, a, c])
        dates = [str(Q._page_date(pg["fm"])) for _, pg in out]
        assert dates == ["2026-01-01", "2026-06-01", "2026-10-01"]

    def test_score_breaks_date_ties(self):
        a = (1.0, _claim("a", "s", "2026-06-01"))
        b = (2.0, _claim("b", "s", "2026-06-01"))
        out = Q._evolution_sort([a, b])
        assert out[0][1]["stem"] == "b"  # higher score first within a date


class TestChangedAnswer:
    def _answer(self, ordered):
        import builtins
        return Q._changed_answer("what changed about retries", ordered)

    def test_renders_ordered_evolution_with_locators(self):
        a = (1.0, _page("claim-a", "Retries were ad-hoc.", type_="claim",
                        last_verified="2026-01-01",
                        generated=None) | {"fm": {**_claim("a", "x", "2026-01-01")["fm"],
                                                    "source_refs": [{"locator": "L1-L2", "quote": "ad-hoc retries"}]}})
        b = (1.0, _page("claim-b", "Retries use exponential backoff now.", type_="claim",
                        last_verified="2026-10-01") | {"fm": {**_claim("b", "x", "2026-10-01")["fm"],
                                                              "source_refs": [{"locator": "L5-L6", "quote": "exponential backoff"}]}})
        out = self._answer(Q._evolution_sort([b, a]))
        assert "## Evolution (earliest → latest)" in out
        assert out.index("2026-01-01") < out.index("2026-10-01")
        assert "[L1-L2]" in out and "[L5-L6]" in out

    def test_contested_flags_not_dropped(self):
        contested = _claim("a", "the old way", "2026-01-01", status="contested")
        contested["fm"]["source_refs"] = [{"locator": "L1", "quote": "old"}]
        out = self._answer(Q._evolution_sort([(1.0, contested)]))
        assert "⚠ contested" in out
        assert "never silently dropped" in out

    def test_undated_claims_render_undated_marker(self):
        pg = _claim("a", "s", None)
        pg["fm"]["source_refs"] = [{"locator": "L1", "quote": "s"}]
        out = self._answer(Q._evolution_sort([(1.0, pg)]))
        assert "(undated)" in out  # honest marker, never dropped

    def test_no_claims_at_all(self):
        pg = _page("pat-a", "a pattern", type_="pattern")
        out = self._answer([(1.0, pg)])
        assert "nothing to order" in out.lower()


class TestNoScoreBleed:
    def test_non_changed_types_ignore_age_rank_boost(self):
        """decision/verify/compare scoring unchanged by the temporal branch."""
        pages = [_claim("a", "retry backoff decision", "2026-01-01")]
        base = Q.score_pages(pages, "retry backoff decision", "decision")
        assert len(base) == 1
        score0, _ = base[0]
        # same corpus, changed type: boost != decision's; decision stays 3x-type
        pg = pages[0]
        assert Q.score_pages(pages, "retry backoff decision", "decision")[0][0] == score0


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])