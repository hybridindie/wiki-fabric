"""#174 — gate escalation aging + digest scaffold: pending promotions and
inbox candidates waiting past the threshold render ESCALATED (prose, manifest,
JSON); the corpus-CI digest scaffold is gated, deterministic, notify-on-
actionable; nothing in the push path promotes.
"""

import json
import os
import sys
from datetime import date, timedelta
from pathlib import Path
from unittest import mock

import yaml

_REPO = Path(__file__).resolve().parent.parent
for _p in (str(_REPO / "scripts" / "cmd"), str(_REPO / "scripts" / "lib")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

os.environ.setdefault("WIKI_FABRIC_DIR", "/tmp/definitely-not-a-fabric-aging")

import importlib.util as _ilu


def _load(name, path):
    spec = _ilu.spec_from_file_location(name, path)
    mod = _ilu.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def _mk_fabric(tmp_path):
    corpus = tmp_path / "corpus"
    for d in ("registry/promotions", "patterns/_inbox", "evidence/claims",
              "projects/proj/experience-events"):
        (corpus / d).mkdir(parents=True, exist_ok=True)
    (tmp_path / "fabric.yaml").write_text("repos:\n  proj:\n    path: ../proj\n")
    os.environ["WIKI_FABRIC_DIR"] = str(tmp_path)
    import fabric_config
    import importlib
    importlib.reload(fabric_config)
    return corpus


def _mk_gate(tmp_path, name="gate_aging"):
    """gate imports promote / promote-patterns by NAME (importlib) — their
    INBOX/PROMOTIONS dirs freeze at FIRST import; purge them so each tmp
    fabric re-resolves (the same seam review-gate tests use)."""
    import sys as _sys
    for mod in list(_sys.modules):
        if mod in ("promote", "promote-patterns", "promote-patterns-module"):
            del _sys.modules[mod]
    return _load(f"{name}_{id(tmp_path) % 99999}",
                 _REPO / "scripts" / "cmd" / "gate.py")


class TestAgeHelpers:
    def test_age_days_from_created(self, tmp_path):
        g = _mk_gate(tmp_path)
        assert g._age_days_impl({"created": date.today().isoformat()},
                                date.today()) == 0
        old = date.today() - timedelta(days=12)
        assert g._age_days_impl({"created": old.isoformat()}, date.today()) == 12

    def test_unparseable_age_is_none(self, tmp_path):
        g = _mk_gate(tmp_path)
        assert g._age_days_impl({}, date.today()) is None
        assert g._age_days_impl({"created": "not-a-date"}, date.today()) is None

    def test_escalation_threshold_from_tuning(self, tmp_path):
        g = _mk_gate(tmp_path)
        assert g._escalated({"created": (date.today() - timedelta(days=8)).isoformat()}) is True
        assert g._escalated({"created": (date.today() - timedelta(days=3)).isoformat()}) is False
        assert _escalated_unknown(g)
        # explicit threshold param (the tuning override seam): 14d threshold
        # → 8d-old is NOT escalated, 20d-old IS
        assert g._escalated({"created": (date.today() - timedelta(days=8)).isoformat()},
                            threshold=14) is False
        assert g._escalated({"created": (date.today() - timedelta(days=20)).isoformat()},
                            threshold=14) is True

    def test_escalated_none_age_never_fires(self, tmp_path):
        g = _mk_gate(tmp_path)
        assert g._escalated({}) is False
        assert g._escalated({"created": "garbage"}) is False


def _escalated_unknown(g):
    return g._escalated({"created": (date.today() - timedelta(days=99)).isoformat()}) is True


class TestEscalatedRendering:
    def _seed_pending(self, corpus, days_old):
        d = (date.today() - timedelta(days=days_old)).isoformat()
        p = corpus / "registry" / "promotions" / "promotion-esc-test.md"
        p.write_text(f"""---
type: promotion-dossier
id: promotion-esc-test
title: esc test
status: pending-review
created: {d}
---
""")
        return p

    def test_prose_shows_escalated(self, tmp_path, capsys):
        corpus = _mk_fabric(tmp_path)
        self._seed_pending(corpus, 20)
        g = _mk_gate(tmp_path, "gate_prose")
        prom = g.list_pending.promotions if hasattr(g, "list_pending") else None
        import promote as _prom
        sections, actionable = g.gate()
        assert actionable
        g._emit(sections, True)
        cap = capsys.readouterr()
        assert "ESCALATED" in cap.out

    def test_manifest_shows_escalated_and_age(self, tmp_path, capsys):
        corpus = _mk_fabric(tmp_path)
        p = self._seed_pending(corpus, 20)
        g = _mk_gate(tmp_path, "gate_manifest")
        sections, _ = g.gate()
        mp = corpus / "registry" / "pending-gate.md"
        g._write_manifest(mp, sections, True)
        text = mp.read_text()
        assert "ESCALATED" in text and "waiting 20d" in text

    def test_manifest_includes_candidates_section(self, tmp_path):
        """The pre-#174 gap: pattern candidates were prose-only — the
        manifest (the persisted record) never showed the inbox."""
        corpus = _mk_fabric(tmp_path)
        d = (date.today() - timedelta(days=2)).isoformat()
        c = corpus / "patterns" / "_inbox" / "pattern-chat-esc.md"
        c.write_text(f"""---
type: pattern
id: pattern-chat-esc
status: candidate
origin: chat-mined
created: {d}
---
""")
        g = _mk_gate(tmp_path, "gate_cands")
        sections, _ = g.gate()
        mp = corpus / "registry" / "pending-gate.md"
        g._write_manifest(mp, sections, True)
        text = mp.read_text()
        assert "Chat-mined pattern candidates" in text
        assert "pattern-chat-esc" in text
        assert "ESCALATED" not in text  # 2d < 7d threshold

    def test_json_carries_age_and_escalations(self, tmp_path, capsys):
        corpus = _mk_fabric(tmp_path)
        self._seed_pending(corpus, 20)
        g = _mk_gate(tmp_path, "gate_json")
        import sys as _sys
        with mock.patch.object(_sys, "argv", ["gate.py", "--json"]):
            try:
                g.main()
            except SystemExit:
                pass
        d = json.loads(capsys.readouterr().out)
        assert d["promotions"][0]["escalated"] is True
        assert d["promotions"][0]["age_days"] == 20
        assert d["escalation_threshold_days"] == 7
        assert "pattern-candidates" in d


class TestDigestScaffold:
    def test_scaffold_writes_gated_workflow(self, tmp_path):
        corpus = _mk_fabric(tmp_path)
        sync = _load(f"sync_digest_{id(tmp_path) % 99999}",
                     _REPO / "scripts" / "cmd" / "sync.py")
        assert sync.scaffold_gate_digest_workflow() is True
        wf = corpus / ".github" / "workflows" / "gate-digest.yml"
        assert wf.exists()
        d = yaml.safe_load(wf.read_text())
        assert list(d["jobs"]) == ["digest"]
        cond = d["jobs"]["digest"]["if"]
        assert "WIKI_FABRIC_GATE_NOTIFY" in cond

    def test_scaffold_idempotent(self, tmp_path):
        corpus = _mk_fabric(tmp_path)
        wf = corpus / ".github" / "workflows"
        wf.mkdir(parents=True, exist_ok=True)
        (wf / "gate-digest.yml").write_text("# human-owned\n")
        sync = _load(f"sync_digest2_{id(tmp_path) % 99999}",
                     _REPO / "scripts" / "cmd" / "sync.py")
        assert sync.scaffold_gate_digest_workflow() is False
        assert (wf / "gate-digest.yml").read_text() == "# human-owned\n"

    def test_digest_pipeline_never_promotes(self):
        d = yaml.safe_load((_REPO / "system" / "corpus" /
                            "gate-digest-workflow.yml").read_text())
        run = str(d["jobs"]["digest"]["steps"])
        assert "wf promote" not in run
        assert "--write-manifest" in run  # the manifest is the record