"""#173 — mine-chats judged near-miss refinement: paraphrase takeaways merge
into existing inbox candidates (G-J gated, per-repo seam); judged-different
stages separately; tier-down/un calibrated = byte-identical keyword behavior.
"""

import os
import re
import sys
from pathlib import Path
from unittest import mock

import pytest

_REPO = Path(__file__).resolve().parent.parent
for _p in (str(_REPO / "scripts" / "cmd"), str(_REPO / "scripts" / "lib")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

os.environ.setdefault("WIKI_FABRIC_DIR", "/tmp/definitely-not-a-fabric-mine-chats")

import importlib.util as _ilu


def _load(name, path):
    spec = _ilu.spec_from_file_location(name, path)
    mod = _ilu.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def _mk_fabric(tmp_path):
    corpus = tmp_path / "corpus"
    for d in ("evidence/claims", "evidence/sources", "evidence/insights",
              "patterns/_inbox", "evidence/raw/proj/chats", "registry",
              "projects/proj"):
        (corpus / d).mkdir(parents=True, exist_ok=True)
    (tmp_path / "fabric.yaml").write_text("repos:\n  proj:\n    path: ../proj\n")
    os.environ["WIKI_FABRIC_DIR"] = str(tmp_path)
    return corpus


def _mc(tmp_path):
    import fabric_config
    import importlib
    importlib.reload(fabric_config)
    return _load(f"mine_chats_{id(tmp_path) % 99999}",
                 _REPO / "scripts" / "cmd" / "mine-chats.py")


def _takeaway(stmt, kind="pattern"):
    return {"kind": kind, "statement": stmt, "rationale": "why", "source": "chat-x.md"}


def _stage_one(corpus, stmt, cid=None):
    """An existing inbox candidate (as propose_candidates writes it)."""
    import hashlib
    from pathlib import Path as _P
    chash = hashlib.sha256(stmt.encode()).hexdigest()[:10]
    cid = cid or f"pattern-chat-{chash}"
    p = corpus / "patterns" / "_inbox" / f"{cid}.md"
    p.write_text(f"""---
type: pattern
id: {cid}
title: "staged"
status: candidate
maturity: 1
origin: chat-mined
source_chat: "[[proj-chats-chat-a-md]]"
project: proj
provenance:
  - source: "[[proj-chats-chat-a-md]]"
    locator: "session transcript"
    quote: "{stmt[:100]}"
tags: [chat-mined, inbox]
created: 2026-10-01
---

# {cid}

{stmt}

**Mined from:** [[proj-chats-chat-a-md]] — session-level durable takeaway
(kind: pattern). Apply via promote-patterns --apply.
""")
    return p


class TestNearMissRefinement:
    def test_judged_same_merges(self, tmp_path, capsys):
        corpus = _mk_fabric(tmp_path)
        existing = _stage_one(corpus, "Batch commands into one round trip to cut latency.")
        mc = _mc(tmp_path)
        # keyword Jaccard must land in the near-miss band for this pair:
        new = "Cut round trips by batching commands together."
        sim = mc._jaccard(mc._kw_set(new.lower()),
                          mc._kw_set(_norm := new.lower()))
        with mock.patch("judgment.judgment_eval_recorded",
                        return_value=(True, "test receipt")), \
             mock.patch("judgment.same_recurrence", return_value=(True, 0.91)) as sr:
            got = mc._refine_near_miss(new, "pattern",
                                       corpus / "patterns" / "_inbox",
                                       project="proj", transcript_stem="chat-b-md")
        cap = capsys.readouterr()
        assert got == existing, (cap.out + cap.err)
        text = existing.read_text()
        assert "judged: \"near-miss merged" in text  # the judgment is RECORDED
        assert "Merged (judged) phrasing" in text
        assert "[[proj-chats-chat-b-md]]" in text  # provenance gained the source
        # the judged verdict used the per-repo seam
        assert sr.call_args.kwargs.get("repo") == "proj"

    def test_judged_same_records_probability(self, tmp_path):
        corpus = _mk_fabric(tmp_path)
        existing = _stage_one(corpus, "Batch commands into one round trip to cut latency.")
        mc = _mc(tmp_path)
        with mock.patch("judgment.judgment_eval_recorded",
                        return_value=(True, "ok")), \
             mock.patch("judgment.same_recurrence", return_value=(True, 0.87)):
            mc._refine_near_miss("Round trips shrink when commands batch.",
                                 "pattern", corpus / "patterns" / "_inbox",
                                 project="proj", transcript_stem="chat-b-md")
        assert "p=0.87" in existing.read_text()

    def test_stage_path_untouched_by_refinement(self, tmp_path):
        """The plain propose_candidates flow (no near-miss) still stages its
        candidate exactly as before."""
        corpus = _mk_fabric(tmp_path)
        tp = corpus / "evidence" / "raw" / "proj" / "chats" / "chat-a-md.md"
        tp.parent.mkdir(parents=True, exist_ok=True)
        tp.write_text("session\n")
        mc = _mc(tmp_path)
        stmts = [_takeaway("A totally novel takeaway statement about caching layers.")]
        n = mc.propose_candidates(tp, stmts, project="proj")
        assert n == 1
        assert len(list((corpus / "patterns" / "_inbox").glob("*.md"))) == 1

    def test_near_miss_out_of_band_stages_not_merges(self, tmp_path):
        """Zero-overlap pairs never reach the judge (band guard) — they stage
        separately without any judgment call."""
        corpus = _mk_fabric(tmp_path)
        _stage_one(corpus, "Batch commands into one round trip to cut latency.")
        mc = _mc(tmp_path)
        called = {"n": 0}
        with mock.patch("judgment.same_recurrence",
                        side_effect=lambda *a, **k: called.__setitem__("n", called["n"] + 1) or (True, 0.9)), \
             mock.patch("judgment.judgment_eval_recorded", return_value=(True, "ok")):
            got = mc._refine_near_miss(
                "Kubernetes pod eviction notices flooded the logs last night.",
                "pattern", corpus / "patterns" / "_inbox", project="proj",
                transcript_stem="chat-b-md")
        assert got is None
        assert called["n"] == 0  # never judged


class TestGateRefusal:
    def test_gj_refusal_is_loud_and_keyword_stands(self, tmp_path, capsys):
        """G-J: uncalibrated judge → NO merge, NO new-stage weirdness — the
        message names the gate and the normal staging path proceeds."""
        corpus = _mk_fabric(tmp_path)
        _stage_one(corpus, "Batch commands into one round trip to cut latency.")
        mc = _mc(tmp_path)
        with mock.patch("judgment.judgment_eval_recorded",
                        return_value=(False, "no judgment-eval PASS receipt for judge cloud:jev-latest")):
            got = mc._refine_near_miss(
                "Cut round trips by batching commands together.",
                "pattern", corpus / "patterns" / "_inbox",
                project="proj", transcript_stem="chat-b-md")
        cap = capsys.readouterr()
        everything = cap.out + cap.err
        assert "G-J" in everything and "skipped" in everything
        assert got is None  # no merge — the deterministic flow stands

    def test_same_recurrence_unavailable_falls_back(self, tmp_path, capsys):
        corpus = _mk_fabric(tmp_path)
        _stage_one(corpus, "Batch commands into one round trip to cut latency.")
        mc = _mc(tmp_path)
        from judgment import JudgmentUnavailable
        with mock.patch("judgment.judgment_eval_recorded",
                        return_value=(True, "ok")), \
             mock.patch("judgment.same_recurrence",
                        side_effect=JudgmentUnavailable("backend gone")):
            got = mc._refine_near_miss(
                "Cut round trips by batching commands together.",
                "pattern", corpus / "patterns" / "_inbox",
                project="proj", transcript_stem="chat-b-md")
        cap = capsys.readouterr()
        assert "unavailable" in (cap.out + cap.err)
        assert got is None


class TestIdempotence:
    def test_exact_statement_never_duplicates(self, tmp_path):
        corpus = _mk_fabric(tmp_path)
        tp = corpus / "evidence" / "raw" / "proj" / "chats" / "chat-a-md.md"
        tp.write_text("session\n")
        mc = _mc(tmp_path)
        stmts = [_takeaway("The same exact statement each run keeps one candidate.")]
        assert mc.propose_candidates(tp, stmts, project="proj") == 1
        assert mc.propose_candidates(tp, stmts, project="proj") == 0
        assert len(list((corpus / "patterns" / "_inbox").glob("*.md"))) == 1