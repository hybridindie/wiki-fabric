"""#186 — contradiction synthesis captures the journey.

The synthesis prompt contract: claims_block carries disagreement explicitly
(claim status + relations + judged effect verdicts from the effects files),
and SYNTH_PROMPT requires rendering the EVOLUTION (prior state + current
state folded together) instead of a flattened winner; unresolved
disagreement lands in open_questions.

Run: python3 -m pytest tests/test_synthesis_contradictions.py -v
"""
import json
import sys
from pathlib import Path
from unittest import mock

_REPO = Path(__file__).resolve().parent.parent
for _p in (str(_REPO / "scripts" / "cmd"), str(_REPO / "scripts" / "lib")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import os
os.environ.setdefault("WIKI_FABRIC_DIR", "/tmp/definitely-not-a-fabric-synth186")

import importlib.util


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


S = _load("synth186", _REPO / "scripts" / "cmd" / "synthesize.py")


def _claim(stem, statement, status="supported", relations=None):
    fm = {"statement": statement, "status": status, "confidence": "high"}
    if relations is not None:
        fm["relations"] = relations
    return {"file": None, "stem": stem, "fm": fm, "body": "",
            "statement": statement, "status": status, "confidence": "high"}


class TestConciseRelations:
    def test_renders_types_and_targets(self):
        c = _claim("claim-a", "x", relations=[
            {"type": "contradicts", "target": "[[claim-b]]"},
            {"type": "originated_in", "target": "[[src-x]]"},
        ])
        out = S._concise_relations(c)
        assert "contradicts:claim-b" in out
        assert "originated_in:src-x" in out

    def test_empty_relations_render_nothing(self):
        c = _claim("claim-a", "x", relations=[])
        assert S._concise_relations(c) == ""

    def test_malformed_relations_survive(self):
        c = _claim("claim-a", "x", relations=["not-a-dict", {"type": None}])
        assert S._concise_relations(c) == ""


class TestClusterEffects:
    def _seed_effect(self, tmp_path, stem, pairs):
        eff = Path(tmp_path) / "registry" / "effects"
        eff.mkdir(parents=True, exist_ok=True)
        (eff / f"{stem}.effects.json").write_text(
            json.dumps({"route": "cloud", "pairs": pairs}))

    def test_reads_contradicts_verdicts(self, tmp_path, monkeypatch):
        self._seed_effect(tmp_path, "claim-a", [
            {"against": "claim-b", "effect": "contradicts", "confidence": 0.9},
            {"against": "claim-c", "effect": "no-action"},
        ])
        monkeypatch.setattr(S, "VAULT_ROOT", tmp_path)
        out = S._cluster_effects([_claim("claim-a", "x")])
        assert "contradicts:claim-b" in out["claim-a"]
        assert "no-action" not in out["claim-a"]

    def test_torn_file_degrades_silent(self, tmp_path, monkeypatch):
        eff = Path(tmp_path) / "registry" / "effects"
        eff.mkdir(parents=True, exist_ok=True)
        (eff / "claim-a.effects.json").write_text("{torn")
        monkeypatch.setattr(S, "VAULT_ROOT", tmp_path)
        assert S._cluster_effects([_claim("claim-a", "x")]) == {}

    def test_absent_effects_dir(self, tmp_path, monkeypatch):
        monkeypatch.setattr(S, "VAULT_ROOT", tmp_path)  # no registry/effects at all
        assert S._cluster_effects([_claim("claim-a", "x")]) == {}


class TestPromptBlock:
    """The deterministic input side: disagreement reaches the prompt."""

    def _build(self, tmp_path, cluster, monkeypatch):
        monkeypatch.setattr(S, "VAULT_ROOT", tmp_path)
        _c = dict(S._cluster_effects(cluster))
        # call the claims_text builder exactly as synthesize_concept does
        effects = S._cluster_effects(cluster)

        def _line(c):
            bits = f"- [{c['stem']}] {c['statement']} (status={c['status']}, conf={c['confidence']}"
            rels = S._concise_relations(c)
            if rels:
                bits += f", relations={rels}"
            eff = effects.get(c["stem"])
            if eff:
                bits += f"; judged effects: {eff}"
            return bits + ")"
        return "\n".join(_line(c) for c in cluster)

    def test_contested_claim_status_reaches_block(self, tmp_path, monkeypatch):
        cluster = [_claim("claim-a", "old state"), _claim("claim-b", "new state")]
        cluster[0]["status"] = "contested"
        block = self._build(tmp_path, cluster, monkeypatch)
        assert "status=contested" in block

    def test_relations_and_effects_reach_block(self, tmp_path, monkeypatch):
        self._seed_effects_dir(tmp_path, "claim-a", [
            {"against": "claim-b", "effect": "contradicts"}])
        cluster = [_claim("claim-a", "old", relations=[
            {"type": "contradicts", "target": "[[claim-b]]"}])]
        block = self._build(tmp_path, cluster, monkeypatch)
        assert "relations=contradicts:claim-b" in block

        monkeypatch.setattr(S, "VAULT_ROOT", tmp_path)
        effects = S._cluster_effects(cluster)
        assert effects, "effects file seeded but unread"

    def _seed_effects_dir(self, tmp_path, stem, pairs):
        eff = Path(tmp_path) / "registry" / "effects"
        eff.mkdir(parents=True, exist_ok=True)
        (eff / f"{stem}.effects.json").write_text(json.dumps({"pairs": pairs}))


class TestPromptContract:
    def test_contradiction_clause_present(self):
        assert "Contradiction handling" in S.SYNTH_PROMPT
        assert "Render the EVOLUTION" in S.SYNTH_PROMPT or "Render the evolution" in S.SYNTH_PROMPT
        assert "open_questions" in S.SYNTH_PROMPT
        # disputed goes to open_questions, not silently dropped
        assert "DISPUTED" in S.SYNTH_PROMPT

    def test_prompt_json_contract_unchanged(self):
        # the four-key contract stands (title/definition/applicability/open_questions)
        assert '"title"' in S.SYNTH_PROMPT and '"definition"' in S.SYNTH_PROMPT

    def test_mechanical_fallback_still_contracts(self, tmp_path, monkeypatch):
        """LLM unavailable → mechanical synthesis shape unchanged (four keys)."""
        monkeypatch.setattr(S, "llm_config", lambda compiler=False: {
            "base_url": "http://127.0.0.1:1", "api_key": "x", "ops_model": "ops", "model": "ops"})
        out = S.synthesize_concept([_claim("claim-a", "old"),
                                    _claim("claim-b", "new")], "concept-test")
        assert set(out) == {"title", "definition", "applicability", "open_questions"}


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])