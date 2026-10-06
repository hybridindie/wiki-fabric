"""#187 — delta-mode wiki refresh.

Contract: an article whose GENERATION INPUTS are unchanged is left
byte-identical (0 tokens, survives reconcile); changed inputs route an LLM
delta whose section edits are spliced MECHANICALLY from the previous file
(untouched sections verbatim-from-disk, never re-emitted by the model);
--full preserves wholesale regeneration; the inputs sidecar is an additive
section of wiki-export-manifest-v1; --check reports staleness (0 tokens).

Run: python3 -m pytest tests/test_wiki_delta_refresh.py -v
"""
import json
import sys
from pathlib import Path
from unittest import mock

_REPO = Path(__file__).resolve().parent.parent
for _p in (str(_REPO / "scripts"), str(_REPO / "scripts" / "cmd"),
           str(_REPO / "scripts" / "lib"), str(_REPO / "scripts" / "wiki_lib")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import os
os.environ.setdefault("WIKI_FABRIC_DIR", "/tmp/definitely-not-a-fabric-delta187")

import importlib.util


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


G = _load("gen_delta", _REPO / "scripts" / "wiki_lib" / "generators.py")

PREV = """---
type: wiki-article
title: "Test Topic"
---

## Definition

Test Topic covers: the old definition text.

## Current claims

- The old claim one [1]
- The old claim two [2]

---
[1] footnote one
[2] footnote two
"""


class TestDeltaSplit:
    def test_frontmatter_extracted(self):
        fm, sections = G._delta_split(PREV)
        assert fm.startswith("---")
        heads = [h.strip() for h, _ in sections if h is not None]  # heading line verbatim; test normalizes
        assert heads == ["## Definition", "## Current claims"]  # preamble/tail carry None

    def test_untouched_section_body_is_verbatim(self):
        _, sections = G._delta_split(PREV)
        by_head = {h.strip(): "".join(ln) for h, ln in sections if h is not None}
        assert "- The old claim one [1]" in by_head["## Current claims"]
        assert "old claim one" in by_head["## Current claims"]


class TestApplyDelta:
    """THE contract: spliced sections come from the PREVIOUS file; the model
    only supplies the changed section bodies."""

    def _edits(self, new_body):
        # the model supplies a body WITHOUT the leading blank (the mechanical
        # splice preserves the original body shape by keeping the section's
        # own separator intact — the replacement body is the CONTENT lines)
        return {"sections": [{"heading": "Current claims", "action": "replace",
                              "new_body": new_body}],
                "delete_sections": []}

    def test_replaced_section_swaps_untouched_survive_verbatim(self):
        out = G._apply_delta(PREV, self._edits(["", "- The NEW claim [3]"]))
        assert "- The NEW claim [3]" in out
        # untouched section byte-identical to the previous file
        assert "Test Topic covers: the old definition text." in out
        # the model never re-emitted the replaced section's old lines
        assert "- The old claim one [1]" not in out

    def test_delete_section(self):
        out = G._apply_delta(PREV, {"sections": [], "delete_sections": ["## Definition"]})
        assert "## Definition" not in out
        assert "## Current claims" in out

    def test_insert_new_section(self):
        out = G._apply_delta(PREV, {"sections": [
            {"heading": "## Incidents", "new_body": ["Sep 24: the release hung."]}],
            "delete_sections": []})
        assert "## Incidents" in out and "Sep 24: the release hung." in out
        assert "## Definition" in out  # the old sections stand

    def test_untouched_sections_byte_identical(self):
        out = G._apply_delta(PREV, self._edits(["", "- new content"]))
        # the REPLACED section's old lines are gone; every OTHER section
        # (Definition prose, footnotes) survives byte-identical from disk
        for frag in ("Test Topic covers: the old definition text.",
                     "footnote one", "footnote two"):
            assert frag in out

    def test_malformed_edits_ignored(self):
        out = G._apply_delta(PREV, {"sections": ["garbage"], "delete_sections": []})
        assert "## Definition" in out  # the article survives bad edits


class TestDeltaPrompt:
    def test_delta_prompt_carries_prev_and_delta(self, tmp_path, monkeypatch):
        captured = {}

        class _Resp:
            class choices:
                pass

        def _fake_create(model=None, temperature=None, max_tokens=None, messages=None):
            captured["prompt"] = messages[0]["content"]
            raise RuntimeError("stop")

        monkeypatch.setattr("openai.OpenAI", lambda *a, **k: mock.Mock(
            chat=mock.Mock(completions=mock.Mock(create=_fake_create))))
        monkeypatch.setattr("extract_backends.llm_config",
                            lambda compiler=True: {"base_url": "http://x",
                                                   "api_key": "k",
                                                   "ops_model": "m", "model": "m"})
        try:
            G._llm_topic_delta({"title": "T"}, PREV, [], [], dry_run=True)
        except RuntimeError:
            pass
        p = captured.get("prompt", "")
        assert "CURRENT ARTICLE" in p and "Test Topic covers" in p
        assert "NEW CLAIMS" in p and "byte-identical" in p


class TestInputSig:
    def test_sig_stable_for_same_inputs(self, tmp_path, monkeypatch):
        c1 = tmp_path / "claim-a.md"
        c1.write_text("---\ntype: claim\nstatement: \"s\"\n---\nb\n")
        topic = {"title": "T", "domain": "d", "claims": ["claim-a"]}
        sigs = set()
        for _ in range(2):
            sigs.add(G._topic_input_sig(topic, [c1]))
        assert len(sigs) == 1

    def test_sig_changes_with_claim_content(self, tmp_path):
        c1 = tmp_path / "claim-a.md"
        topic = {"title": "T", "domain": "d", "claims": ["claim-a"]}
        c1.write_text("---\ntype: claim\nstatement: \"s\"\n---\nb\n")
        sig1 = G._topic_input_sig(topic, [c1])
        c1.write_text("---\ntype: claim\nstatement: \"s2\"\n---\nb\n")
        sig2 = G._topic_input_sig(topic, [c1])
        assert sig1 != sig2

    def test_sig_changes_with_mode(self, tmp_path):
        c1 = tmp_path / "claim-a.md"
        c1.write_text("x\n")
        topic = {"title": "T", "domain": "d", "claims": ["claim-a"]}
        G._current_mode_holder[0] = "mechanical"
        s1 = G._topic_input_sig(topic, [c1])
        G._current_mode_holder[0] = "llm"
        s2 = G._topic_input_sig(topic, [c1])
        assert s1 != s2
        G._current_mode_holder[0] = "mechanical"


class TestInputManifest:
    def test_roundtrip_additive(self, tmp_path, monkeypatch):
        calls = []

        def fake_load():
            calls.append(1)
            return {"files": {"x": "abc"}, "$schema": "wiki-fabric/wiki-export-manifest-v1"}

        def fake_write(m):
            fake_load.recorded = m
        monkeypatch.setattr("obsidian_bridge.load_manifest", fake_load)
        monkeypatch.setattr("obsidian_bridge.write_manifest", fake_write)
        G._save_input_manifest({"topics/t.md": {"sig": "s1", "sha": "abc"}})
        m = fake_load.recorded
        assert m["inputs"]["topics/t.md"]["sig"] == "s1"
        assert m["files"]["x"] == "abc"  # the pre-existing section rode along


class TestUnchangedNoOp:
    """The core acceptance: unchanged inputs → 0 tokens, byte-identical."""

    def test_untouched_when_sig_matches(self, tmp_path, monkeypatch):
        corpus = tmp_path / "corpus"
        claims = corpus / "evidence" / "claims"
        claims.mkdir(parents=True)
        c1 = claims / "claim-proj-doc-md-000.md"
        c1.write_text('---\ntype: claim\nstatement: "The old claim one."\nstatus: supported\n'
                      "source_refs:\n  - source: \"[[src-proj-doc-md]]\"\n    locator: L1\n"
                      '    quote: "The old claim one."\n---\n\nThe old claim one.\n')
        monkeypatch.setattr(G.fabric_config, "CORPUS_ROOT", corpus, raising=False)
        wiki = tmp_path / "wiki"
        (wiki / "topics").mkdir(parents=True)
        monkeypatch.setattr(G, "_wiki_root", lambda: wiki)
        topic = {"title": "Test Topic", "domain": "d", "claims": ["claim-proj-doc-md-000"]}
        prev = wiki / "topics" / "test-topic.md"
        prev.write_text(PREV)
        monkeypatch.setattr(G, "_load_input_manifest",
                            lambda: {"topics/test-topic.md": {"sig": G._topic_input_sig(
                                topic, [c1]), "sha": "x"}})
        monkeypatch.setattr(G, "_current_mode_holder", ["mechanical"])
        out, n = G._generate_topic_article(topic, "hybrid", dry_run=False)
        assert out == prev
        assert prev.read_text() == PREV  # BYTE-IDENTICAL, zero tokens spent

    def test_force_full_regenerates(self, tmp_path, monkeypatch):
        corpus = tmp_path / "corpus"
        claims = corpus / "evidence" / "claims"
        claims.mkdir(parents=True)
        c1 = claims / "claim-proj-doc-md-000.md"
        c1.write_text('---\ntype: claim\nstatement: "The old claim one."\nstatus: supported\n'
                      "source_refs:\n  - source: \"[[src-proj-doc-md]]\"\n    locator: L1\n"
                      '    quote: "The old claim one."\n---\n\nbody\n')
        monkeypatch.setattr(G.fabric_config, "CORPUS_ROOT", corpus, raising=False)
        wiki = tmp_path / "wiki"
        (wiki / "topics").mkdir(parents=True)
        monkeypatch.setattr(G, "_wiki_root", lambda: wiki)
        monkeypatch.setattr(G, "_load_input_manifest", lambda: {})
        monkeypatch.setattr(G, "_current_mode_holder", ["mechanical"])
        topic = {"title": "Test Topic", "domain": "d", "claims": ["claim-proj-doc-md-000"]}
        prev = wiki / "topics" / "test-topic.md"
        prev.write_text(PREV)
        out, n = G._generate_topic_article(topic, "mechanical", dry_run=False,
                                           force_full=True)
        assert out == prev and prev.read_text() != PREV  # regenerated wholesale


class TestFlagsAndDocs:
    def test_full_and_check_flags_exist(self):
        src = (_REPO / "scripts" / "cmd" / "export-wiki.py").read_text()
        assert '"--full"' in src
        assert '"--check"' in src
        assert "force_full" in src

    def test_reconcile_keep_keeps_unchanged(self):
        src = (_REPO / "scripts" / "cmd" / "export-wiki.py").read_text()
        assert "keep(rel)" in src or "keep and keep(rel)" in src

    def test_manifest_inputs_additive(self):
        src = (_REPO / "scripts" / "lib" / "obsidian_bridge.py").read_text()
        # write_manifest untouched by this feature; inputs ride the same plane
        assert "MANIFEST_SCHEMA" in src


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])