"""Tests for review.py — staleness scan, verify, auto-reverify."""

import sys
import unittest
from pathlib import Path
from unittest import mock

REPO = Path(__file__).parent.parent

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestScan(unittest.TestCase):
    def test_scan_finds_stamps(self):
        import importlib.util as ilu
        spec = ilu.spec_from_file_location("rv", REPO / "scripts" / "review.py")
        rv = ilu.module_from_spec(spec); spec.loader.exec_module(rv)
        report = rv.scan()
        assert "due" in report and "overdue" in report and "stale" in report
        # CI has no claims (evidence/ gitignored); skip if empty
        claim_dir = REPO / "evidence" / "claims"
        if not claim_dir.exists() or not list(claim_dir.glob("claim-*.md")):
            raise unittest.SkipTest("no claims in fabric (CI)")
        assert report["current"] + len(report["due"]) + len(report["overdue"]) + len(report["stale"]) > 0

    def test_parse_date(self):
        import importlib.util as ilu
        spec = ilu.spec_from_file_location("rv", REPO / "scripts" / "review.py")
        rv = ilu.module_from_spec(spec); spec.loader.exec_module(rv)
        import datetime
        d = rv._parse_date("2026-09-21")
        assert d == datetime.date(2026, 9, 21)
        assert rv._parse_date("garbage") is None


class TestAutoReverify(unittest.TestCase):
    def test_auto_reverify_mechanism(self):
        import importlib.util as ilu
        spec = ilu.spec_from_file_location("rv", REPO / "scripts" / "review.py")
        rv = ilu.module_from_spec(spec); spec.loader.exec_module(rv)
        # the function exists and is callable
        assert callable(rv.auto_reverify)
        # dry-run doesn't write
        # (real test needs fabric content — skip if no claims)
        claim_dir = Path(__file__).parent.parent / "evidence" / "claims"
        if not claim_dir.exists() or not list(claim_dir.glob("*.md")):
            raise unittest.SkipTest("no claims in fabric")


if __name__ == "__main__":
    unittest.main()
