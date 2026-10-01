"""Layout module (Tier-2 single truth) + bug-fix regressions.

Run: python3 -m pytest tests/test_layout.py -v
"""

import sys
import importlib.util
from pathlib import Path

import pytest

_SCRIPTS = (Path(__file__).resolve().parent.parent / "scripts").resolve()
for _rel in ("cmd", "lib"):
    if str(_SCRIPTS / _rel) not in sys.path:
        sys.path.insert(0, str(_SCRIPTS / _rel))

import layout


class TestSegments:
    def test_every_declared_dir_has_accessor_coverage(self):
        # accessors exist for the dirs producers write into
        for name in ("evidence_raw", "evidence_sources", "evidence_claims",
                     "patterns", "anti_patterns", "registry", "projects"):
            seg = layout.seg(name)
            assert isinstance(seg, Path) and not seg.is_absolute()

    def test_undeclared_name_raises(self):
        with pytest.raises(KeyError):
            layout.seg("evidence/claims")  # dotted literal = exactly the bug class

    def test_make_composes_root(self, tmp_path):
        assert layout.make(tmp_path, "evidence_claims") == tmp_path / "evidence" / "claims"

    def test_root_injection_beats_default(self, tmp_path):
        assert layout.claims(tmp_path) == tmp_path / "evidence" / "claims"
        assert layout.claims(None) == layout.claims()  # default → fabric_config

    def test_claim_glob_contract(self, tmp_path):
        g = layout.claims_for_source(tmp_path, "p-git-pr-1-md")
        assert str(g).endswith("claim-p-git-pr-1-md-*.md")
        assert str(g).startswith(str(tmp_path / "evidence" / "claims"))

    def test_raw_slug_shape(self, tmp_path):
        assert layout.raw_slug_dir(tmp_path, "p") == tmp_path / "evidence" / "raw" / "p"
        assert layout.raw_slug_dir(tmp_path, "p", "git") == tmp_path / "evidence" / "raw" / "p" / "git"

    def test_prefixes_are_the_join_contract(self):
        assert layout.PREFIXES["source"] == "src-"
        assert layout.PREFIXES["source_summary"] == "sum-"
        assert layout.PREFIXES["claim"] == "claim-"


def _load(name):
    spec = importlib.util.spec_from_file_location(name, _SCRIPTS / f"cmd/{name}.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


class TestAntiPatternApplyPath:
    """Regression: anti-pattern candidates were unconditionally dropped into
    patterns/ — promote.py looks in anti-patterns/ and never saw them."""

    def test_anti_pattern_applies_to_anti_patterns_dir(self, tmp_path, monkeypatch):
        pp = _load("promote-patterns")
        monkeypatch.setattr(pp, "CORPUS_ROOT", tmp_path)
        monkeypatch.setattr(pp, "ANTI_PATTERNS_DIR", tmp_path / "anti-patterns")
        inbox = tmp_path / "patterns" / "_inbox"
        inbox.mkdir(parents=True)
        cand = inbox / "anti-pattern-chat-x.md"
        cand.write_text("---\ntype: anti-pattern\nid: anti-pattern-chat-x\n"
                        "tags: [chat-mined, inbox]\n---\n\nbody\n")
        ok = pp.apply_candidate(cand)
        assert ok
        dest = tmp_path / "anti-patterns" / "anti-pattern-chat-x.md"
        assert dest.exists()
        assert not cand.exists()
        assert "tags: [chat-mined]" in dest.read_text()

    def test_pattern_still_applies_to_patterns_dir(self, tmp_path, monkeypatch):
        pp = _load("promote-patterns")
        monkeypatch.setattr(pp, "CORPUS_ROOT", tmp_path)
        monkeypatch.setattr(pp, "PATTERNS_DIR", tmp_path / "patterns")
        inbox = tmp_path / "patterns" / "_inbox"
        inbox.mkdir(parents=True)
        cand = inbox / "pattern-chat-y.md"
        cand.write_text("---\ntype: pattern\nid: pattern-chat-y\n"
                        "tags: [chat-mined, inbox]\n---\n\nbody\n")
        assert pp.apply_candidate(cand)
        assert (tmp_path / "patterns" / "pattern-chat-y.md").exists()


class TestPromotionQueueFailSoft:
    """Regression: promote called update_promotion_queue_file() (undefined)
    and update_promotion_queue crashed when the human-maintained checklist
    was absent — a promotion died after its writes."""

    def test_missing_queue_is_failsoft(self, tmp_path, monkeypatch):
        pr = _load("promote")
        monkeypatch.setattr(pr, "PROMOTION_QUEUE", tmp_path / "registry" / "promotion-queue.md")
        (tmp_path / "registry").mkdir()
        pr.update_promotion_queue("demo", "recommended")  # must not raise

    def test_existing_queue_row_updates(self, tmp_path, monkeypatch):
        pr = _load("promote")
        qp = tmp_path / "registry" / "promotion-queue.md"
        qp.parent.mkdir(parents=True)
        qp.write_text("| [[pattern-demo]] | 1 (observed) |\n")
        monkeypatch.setattr(pr, "PROMOTION_QUEUE", qp)
        pr.update_promotion_queue("demo", "recommended")
        assert "| [[pattern-demo]] | 2 (recommended)" in qp.read_text()


class TestEffectsLocation:
    """Regression: verdict json sat beside claims in evidence/claims/ —
    machine artifacts live in registry/effects/ (layout rule 2)."""

    def test_write_report_targets_registry_effects(self, tmp_path, monkeypatch):
        import json as _json
        ve = _load("verify-effects")
        import layout as _layout
        claim = tmp_path / "evidence" / "claims" / "claim-x-000.md"
        out = ve.write_report(claim, {"pairs": []}, registry_root=tmp_path)
        assert out == tmp_path / "registry" / "effects" / "claim-x-000.effects.json"
        assert _json.loads(out.read_text())["pairs"] == []