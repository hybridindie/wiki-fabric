"""SkillOpt-epic S1 (#138): receipt↔outcome join → usage counts on pattern pages."""
import json
import sys
from pathlib import Path

REPO = Path(__file__).parent.parent
_SCRIPTS = (REPO / "scripts").resolve()
for _d in (_SCRIPTS / "cmd", _SCRIPTS / "lib", _SCRIPTS):
    if str(_d) not in sys.path:
        sys.path.insert(0, str(_d))

import utility as U


def _fabric(tmp):
    """pattern page + receipt + linked + unlinked experience events."""
    import fabric_config
    corpus = tmp / "corpus"
    proj = corpus / "projects" / "p1"
    receipts = proj / "receipts"
    receipts.mkdir(parents=True)
    patterns = corpus / "patterns"
    patterns.mkdir(parents=True)

    receipt = {
        "$schema": "wiki-fabric/receipt-v1",
        "receipt_id": "receipt-abc123",
        "task": "t",
        "selected": [
            {"path": "patterns/pattern-token-rotation.md", "id": "pattern-token-rotation"},
            {"path": "evidence/claims/claim-x.md", "id": "claim-x"},
        ],
    }
    (receipts / "receipt-abc123.json").write_text(json.dumps(receipt))

    (patterns / "pattern-token-rotation.md").write_text(
        "---\ntype: pattern\nid: pattern-token-rotation\ntitle: T\nstatus: candidate\n---\n\n# P\n")

    ee = proj / "experience-events"
    ee.mkdir(parents=True)
    # linked, positive outcome
    (ee / "ee-2026-09-28-a.md").write_text(
        "---\ntype: experience-event\nproject: p\nobserved_problem: x\n"
        "outcomes:\n  happy_path: PASS\nreceipt: receipt-abc123\n---\n\nbody\n")
    # linked, negative outcome
    (ee / "ee-2026-09-28-b.md").write_text(
        "---\ntype: experience-event\nproject: p\nobserved_problem: y\n"
        "outcomes:\n  happy_path: FAILED\nreceipt: receipt-abc123\n---\n\nbody\n")
    # unlinked (no receipt)
    (ee / "ee-2026-09-28-c.md").write_text(
        "---\ntype: experience-event\nproject: p\nobserved_problem: z\n---\n\nbody\n")

    return corpus


class TestJoin:
    def test_usage_written_from_linked_receipt(self, tmp_path, monkeypatch):
        monkeypatch.setattr(U, "CORPUS_ROOT", tmp_path / "corpus")
        _fabric(tmp_path)
        stats = U.compute()
        assert stats["events"] == 3
        assert stats["linked"] == 2
        assert stats["unlinked"] == 1
        page = tmp_path / "corpus" / "patterns" / "pattern-token-rotation.md"
        text = page.read_text()
        assert "usage:" in text
        assert "retrieved_count: 2" in text          # delivered twice
        assert "applied_count: 1" in text            # one positive outcome
        assert "successful_outcomes: 1" in text
        assert "last_validated:" in text

    def test_unlinked_counted_not_dropped(self, tmp_path, monkeypatch, capsys):
        monkeypatch.setattr(U, "CORPUS_ROOT", tmp_path / "corpus")
        _fabric(tmp_path)
        stats = U.compute()
        assert stats["unlinked"] == 1
        out = capsys.readouterr().out
        assert "unlinked" in out  # surfaced, not silent

    def test_claims_not_counted(self, tmp_path, monkeypatch):
        """Only pattern/skill pages count as adaptation layer — claims in the
        receipt are evidence, not pages to write usage onto."""
        monkeypatch.setattr(U, "CORPUS_ROOT", tmp_path / "corpus")
        _fabric(tmp_path)
        stats = U.compute()
        # only the pattern page was touched
        assert stats["pages_touched"] == 1
        assert not (tmp_path / "corpus" / "evidence" / "claims" / "claim-x.md").exists()

    def test_missing_receipt_reported(self, tmp_path, monkeypatch, capsys):
        monkeypatch.setattr(U, "CORPUS_ROOT", tmp_path / "corpus")
        _fabric(tmp_path)
        ee = tmp_path / "corpus" / "projects" / "p1" / "experience-events" / "ee-x.md"
        ee.parent.mkdir(parents=True, exist_ok=True)
        ee.write_text("---\ntype: experience-event\nreceipt: receipt-missing\n---\n\nx\n")
        stats = U.compute()
        assert "receipt-missing" in stats["missing_receipts"]

    def test_dry_run_writes_nothing(self, tmp_path, monkeypatch):
        monkeypatch.setattr(U, "CORPUS_ROOT", tmp_path / "corpus")
        _fabric(tmp_path)
        U.compute(dry_run=True)
        page = tmp_path / "corpus" / "patterns" / "pattern-token-rotation.md"
        assert "usage:" not in page.read_text()