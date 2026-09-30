"""Unit tests for systemone.py — the shared System One decision-model surface.

Run: python3 -m pytest tests/test_systemone.py -v
All network calls are mocked; degrade contracts asserted without ollama.
"""

import os
import sys
import importlib.util
from pathlib import Path
from unittest import mock

_SCRIPTS = (Path(__file__).resolve().parent.parent / "scripts").resolve()
for _rel in ("cmd", "lib", "eval", "harness"):
    if str(_SCRIPTS / _rel) not in sys.path:
        sys.path.insert(0, str(_SCRIPTS / _rel))

import systemone
import pytest


def _cfg(judgment_on=True, base_url="http://localhost:11434/v1",
         judgment_local_model=None, llm_local_model=None):
    integrations = {}
    if judgment_on is not None:
        j = {"enabled": judgment_on, "route": "cloud", "cloud_model": "jev-latest"}
        if judgment_local_model:
            j["local_model"] = judgment_local_model
        integrations["judgment"] = j
    llm = {"base_url": base_url} if base_url else {}
    if llm_local_model:
        llm["local_model"] = llm_local_model
    return {"integrations": integrations, "llm": llm}


class TestUrlAndTags:
    def test_systemone_url_forms(self):
        assert systemone._systemone_url("http://localhost:11434/v1") == \
            "http://localhost:11434/v1/systemone"
        assert systemone._systemone_url("http://localhost:11434") == \
            "http://localhost:11434/v1/systemone"
        assert systemone._systemone_url("http://localhost:11434/v1/") == \
            "http://localhost:11434/v1/systemone"
        assert systemone._systemone_url("https://api.typesafe.dev") == \
            "https://api.typesafe.dev/v1/systemone"

    def test_hosted_farm_tags_refused(self):
        assert not systemone._ollama_tag_ok("glm-5.3-flash:cloud")
        assert not systemone._ollama_tag_ok("deepseek-v4.1-flash:cloud")
        assert not systemone._ollama_tag_ok("something:hosted")
        assert not systemone._ollama_tag_ok("something:remote")

    def test_port_strings_refused(self):
        assert not systemone._ollama_tag_ok("localhost:11434")
        assert not systemone._ollama_tag_ok("host:name:9999")

    def test_decision_family_accepted(self):
        assert systemone._ollama_tag_ok("tev1:latest")
        assert systemone._ollama_tag_ok("nimble:latest")
        assert systemone._ollama_tag_ok("tev1:4b")
        assert systemone._looks_like_ollama_tag("gemma4:e4b-fixed")

    def test_non_decision_tags_are_not_judges(self):
        # valid ollama tag but not System One-supported
        assert not systemone._ollama_tag_ok("qwen2.5-coder:7b")


class TestJudgeTagResolution:
    def _patch(self, cfg):
        import fabric_config
        return mock.patch.object(fabric_config, "get_config", return_value=cfg)

    def test_judgment_local_model_wins(self):
        with self._patch(_cfg(judgment_local_model="nimble:9b",
                              llm_local_model="gemma4:e4b-fixed")):
            assert systemone.judge_tag() == "nimble:9b"

    def test_llm_local_model_falls_back_to_default(self):
        with self._patch(_cfg(llm_local_model="gemma4:e4b-fixed")):
            assert systemone.judge_tag() == systemone.DEFAULT_JUDGE_TAG

    def test_hosted_farm_local_model_raises(self):
        with self._patch(_cfg(llm_local_model="glm-5.3-flash:cloud")):
            with pytest.raises(systemone.SystemOneUnavailable):
                systemone.judge_tag()

    def test_broken_config_still_defaults(self):
        with self._patch({"integrations": None, "llm": None}):
            assert systemone.judge_tag() == systemone.DEFAULT_JUDGE_TAG


class TestDegradeContracts:
    def _disable(self):
        return mock.patch.dict(os.environ, {"WIKI_SYSTEMONE_DISABLE": "1"})

    def test_rank_none_when_disabled(self):
        with self._disable():
            assert systemone.systemone_rank("q", [{"stem": "a", "body": "x"}]) is None

    def test_hop_none_when_disabled(self):
        with self._disable():
            assert systemone.systemone_hop("q", [("a", "contradicts", "c")]) is None

    def test_pair_none_when_disabled(self):
        with self._disable():
            assert systemone.systemone_pair("A", "B") is None

    def test_rank_none_when_no_fabric(self):
        import fabric_config
        with mock.patch.object(fabric_config, "get_config",
                               return_value=_cfg(base_url=None)):
            with mock.patch.object(systemone, "systemone_active", return_value=False):
                assert systemone.systemone_rank("q", [{"stem": "a", "body": "x"}]) is None

    def test_rank_none_when_call_fails(self):
        with mock.patch.object(systemone, "systemone_active", return_value=True), \
             mock.patch.object(systemone, "systemone",
                               side_effect=systemone.SystemOneUnavailable("down")):
            assert systemone.systemone_rank("q", [{"stem": "a", "body": "x"}]) is None

    def test_pair_none_when_call_fails(self):
        with mock.patch.object(systemone, "systemone_active", return_value=True), \
             mock.patch.object(systemone, "systemone",
                               side_effect=systemone.SystemOneUnavailable("down")):
            assert systemone.systemone_pair("A", "B") is None


class TestRankShape:
    def test_rank_parses_systemone_answers(self):
        resp = {"model": "tev1:latest",
                "answers": {"a": {"type": "noul", "noul": 0.91},
                            "b": {"type": "noul", "noul": 0.07}}}
        with mock.patch.object(systemone, "systemone_active", return_value=True), \
             mock.patch.object(systemone, "systemone", return_value=resp), \
             mock.patch.object(systemone, "judge_tag", return_value="tev1:latest"):
            r = systemone.systemone_rank(
                "why torn reads?",
                [{"stem": "a", "body": "single-writer fix"},
                 {"stem": "b", "body": "gpu raster"}])
        assert r == {"a": 0.91, "b": 0.07}

    def test_hop_parses_edge_scores(self):
        resp = {"answers": {"src": {"noul": 0.84}}}
        with mock.patch.object(systemone, "systemone_active", return_value=True), \
             mock.patch.object(systemone, "systemone", return_value=resp), \
             mock.patch.object(systemone, "judge_tag", return_value="tev1:latest"):
            r = systemone.systemone_hop("q?", [("src", "validated_in", "PR-877")])
        assert r == {"src": 0.84}

    def test_pair_choice_head(self):
        resp = {"answers": {"pair": {"choice": "contradicts",
                                     "probabilities": {"supports": 0.3, "contradicts": 0.5},
                                     "confidence": 0.08}}}
        with mock.patch.object(systemone, "systemone_active", return_value=True), \
             mock.patch.object(systemone, "systemone", return_value=resp), \
             mock.patch.object(systemone, "judge_tag", return_value="tev1:latest"):
            r = systemone.systemone_pair("A: memoized", "B: re-read at every hook")
        assert r["choice"] == "contradicts"
        assert r["probabilities"]["contradicts"] == 0.5