"""Unit tests for the receipts closed loop (#87).

wf log --receipt linkage, gate --deliveries surface, schema contract.

Run: python3 -m pytest tests/test_receipts_loop.py -v
"""

import json
import sys
import importlib.util
from pathlib import Path

import sys, pathlib as _p
_SCRIPTS = (_p.Path(__file__).resolve().parent.parent / "scripts").resolve()
for _rel in ("cmd", "lib", "eval", "harness"):
    if str(_SCRIPTS / _rel) not in sys.path:
        sys.path.insert(0, str(_SCRIPTS / _rel))


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


logx = _load("log_experience", Path(__file__).parent.parent / "scripts/cmd/log-experience.py")
gate = _load("gate_mod", Path(__file__).parent.parent / "scripts/cmd/gate.py")


RECEIPT = {
    "$schema": "wiki-fabric/receipt-v1",
    "receipt_id": "receipt-abc123def456",
    "task": "fix the login timeout",
    "compiled": "2026-09-26",
    "namespace": "projects/demo",
    "revision": "abc",
    "selected": [],
    "excluded": [],
    "precedence": ["project", "domain", "global"],
}


class TestLogReceipt:
    def test_receipt_recorded_in_frontmatter(self, tmp_path):
        logx.PROJECTS_DIR = tmp_path / "projects"
        path = logx.write_event(
            "demo", "login times out", "added retry",
            {"task_class": "bugfix"}, {}, [], "", receipt="receipt-abc123def456")
        text = path.read_text()
        assert 'receipt: "receipt-abc123def456"' in text

    def test_receipt_id_prefix_normalized(self, tmp_path):
        logx.PROJECTS_DIR = tmp_path / "projects"
        path = logx.write_event(
            "demo", "flaky retry", None,
            {}, {}, [], "", receipt="abc123def456")
        assert 'receipt: "receipt-abc123def456"' in path.read_text()

    def test_no_receipt_keeps_frontmatter_clean(self, tmp_path):
        logx.PROJECTS_DIR = tmp_path / "projects"
        path = logx.write_event("demo", "plain event", None, {}, {}, [], "")
        assert "receipt:" not in path.read_text()


class TestGateDeliveries:
    def _receipt_dir(self, tmp_path, rid, task, compiled, namespace="projects/demo"):
        d = tmp_path / "registry" / "receipts"
        d.mkdir(parents=True, exist_ok=True)
        data = {**RECEIPT, "receipt_id": rid, "task": task,
                "compiled": compiled, "namespace": namespace}
        (d / f"{rid}.json").write_text(json.dumps(data))
        return d

    def test_recent_deliveries_reads_receipts(self, tmp_path, monkeypatch):
        from fabric_config import CORPUS_ROOT
        monkeypatch.setattr(gate, "CORPUS_ROOT", tmp_path) if hasattr(gate, "CORPUS_ROOT") else None
        import fabric_config as fc
        monkeypatch.setattr(fc, "CORPUS_ROOT", tmp_path)
        self._receipt_dir(tmp_path, "receipt-aaa", "task one", "2026-09-25")
        self._receipt_dir(tmp_path, "receipt-bbb", "task two", "2026-09-26")
        out = gate._recent_deliveries()
        assert [d["receipt_id"] for d in out] == ["receipt-bbb", "receipt-aaa"], "newest first"

    def test_dedup_across_registry_and_projects(self, tmp_path, monkeypatch):
        import fabric_config as fc
        monkeypatch.setattr(fc, "CORPUS_ROOT", tmp_path)
        data = {**RECEIPT, "receipt_id": "receipt-dup", "compiled": "2026-09-25"}
        d = tmp_path / "registry" / "receipts"
        d.mkdir(parents=True)
        (d / "receipt-dup.json").write_text(json.dumps(data))
        pd = tmp_path / "projects" / "demo" / "receipts"
        pd.mkdir(parents=True)
        (pd / "receipt-dup.json").write_text(json.dumps(data))
        out = gate._recent_deliveries()
        assert len(out) == 1

    def test_empty_returns_empty(self, tmp_path, monkeypatch):
        import fabric_config as fc
        monkeypatch.setattr(fc, "CORPUS_ROOT", tmp_path)
        assert gate._recent_deliveries() == []

    def test_emit_deliveries_output(self, capsys):
        gate._emit_deliveries([{"receipt_id": "receipt-x", "namespace": "projects/demo",
                                "compiled": "2026-09-26", "task": "fix thing"}])
        out = __import__("io").StringIO if False else None
        captured = capsys.readouterr().out
        assert "receipt-x" in captured
        assert "was the manifest right?" in captured

    def test_emit_empty_hint(self, capsys):
        gate._emit_deliveries([])
        captured = capsys.readouterr().out
        assert "--write-receipt" in captured


class TestReceiptLinkageInEvent:
    """The event frontmatter field is the mining payoff surface: receipt ↔ ee."""

    def test_event_schema_has_receipt_field_documented(self):
        schema = (Path(__file__).parent.parent / "schemas" / "frontmatter.md").read_text()
        assert "receipt" in schema