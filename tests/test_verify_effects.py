"""Judged effect verification at ingest (#29 wiring A): independent second
opinion on claim effect classification — kills the self-preference conflict."""
import json
import sys
import importlib.util
from pathlib import Path

REPO = Path(__file__).parent.parent
_SCRIPTS = (REPO / "scripts").resolve()
for _d in (_SCRIPTS, _SCRIPTS / "lib", _SCRIPTS / "cmd"):
    if str(_d) not in sys.path:
        sys.path.insert(0, str(_d))

import judgment as J
import pytest


class TestEffectVerdict:
    def test_options_carry_criteria_to_laya(self, monkeypatch):
        """The laya choice head requires criteria — options must reach
        _laya_engine (regression: _ask_laya used to strip them)."""
        captured = {}
        monkeypatch.setattr(J, "_laya_engine", lambda qs: captured.setdefault("qs", qs) or (_fake_judge := None) or (object(), "test"))
        import pytest
        from judgment import JudgmentUnavailable

        def fake_engine(qs):
            captured["qs"] = qs
            raise J.JudgmentUnavailable("stop")

        monkeypatch.setattr(J, "_laya_engine", fake_engine)
        try:
            J.effect_verdict("new claim text", "existing claim text")
        except J.JudgmentUnavailable:
            pass
        qs = captured["qs"][0]
        assert qs["kind"] == "choice"
        assert len(qs["options"]) == len(J.EFFECT_OPTIONS)
        assert qs["options"][0]["name"] == "supports"

    def test_choice_requires_nonempty_criteria(self, monkeypatch):
        from judgment import JudgmentUnavailable
        with pytest.raises(JudgmentUnavailable, match="needs non-empty criteria"):
            J._laya_engine([{"name": "q", "kind": "choice", "question": "x",
                             "options": []}])

    def test_effect_verdict_maps_value(self, monkeypatch):
        monkeypatch.setattr(J, "choice",
                            lambda *a, **k: {"value": "contradicts", "confidence": 0.8})
        v = J.effect_verdict("new", "existing")
        assert v["effect"] == "contradicts" and v["confidence"] == 0.8


class TestPool:
    def test_pool_prefers_same_source_then_project(self, tmp_path, monkeypatch):
        import fabric_config
        corpus = tmp_path / "corpus"
        claims = corpus / "evidence" / "claims"
        claims.mkdir(parents=True)
        # same-source claims + other project claims
        same = []
        for i in range(3):
            p = claims / f"claim-proj-doc-md-{i:03d}.md"
            p.write_text(f"---\ntype: claim\nstatement: \"s{i}\"\n"
                         'source_refs:\n  - source: "[[src-proj-doc-md]]"\n---\n\nb\n')
            same.append(p)
        other = claims / "claim-other-repo-md-000.md"
        other.write_text("---\ntype: claim\nstatement: \"o\"\n---\n\nb\n")
        import fabric_config as fc
        monkeypatch.setattr(fc, "CORPUS_ROOT", corpus, raising=False)
        pool = J.related_claim_pool(same[0])
        stems = [p.stem for p in pool]
        assert "claim-other-repo-md-000" not in stems  # other project excluded
        assert len(stems) >= 2  # same-source siblings included


class TestDisabledTier:
    def test_cli_exits_cleanly_when_disabled(self, tmp_path, monkeypatch, capsys):
        spec = importlib.util.spec_from_file_location(
            "verify_effects", _SCRIPTS / "cmd" / "verify-effects.py")
        ve = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(ve)
        import judgment as J
        monkeypatch.setattr(J, "is_judgment_active", lambda *a, **k: False)
        with pytest.raises(SystemExit) as ei:
            ve.main()
        assert ei.value.code == 2