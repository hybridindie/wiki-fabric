"""Unit tests for capture-git.py deterministic logic.

Run: python3 -m pytest tests/test_capture_git.py -v
"""

import sys
import importlib.util
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))


def _load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


capture_git = _load_module("capture_git", Path(__file__).parent.parent / "scripts" / "capture-git.py")
commit_is_interesting = capture_git.commit_is_interesting
since_date = capture_git.since_date
write_capture = capture_git.write_capture
sha256_str = capture_git.sha256_str


class TestCommitFilter:
    def test_revert_commit_is_interesting(self):
        assert commit_is_interesting("Revert \"feat: add caching layer\"")

    def test_revert_body_marker(self):
        assert commit_is_interesting("fix: something\n\nThis reverts commit abc1234.")

    def test_conventional_fix_is_interesting(self):
        assert commit_is_interesting("fix(auth): handle expired tokens")

    def test_conventional_feat_is_interesting(self):
        assert commit_is_interesting("feat: add batch writes")

    def test_conventional_perf_is_interesting(self):
        assert commit_is_interesting("perf(query): index claims")

    def test_chore_is_skipped(self):
        assert not commit_is_interesting("chore: bump deps")

    def test_docs_is_skipped(self):
        assert not commit_is_interesting("docs: update readme")

    def test_style_is_skipped(self):
        assert not commit_is_interesting("style: format")

    def test_ci_is_skipped(self):
        assert not commit_is_interesting("ci: bump actions version")

    def test_non_conventional_is_skipped(self):
        assert not commit_is_interesting("some random commit message")

    def test_merge_commit_is_skipped(self):
        assert not commit_is_interesting("Merge pull request #6 from someone/patch-1")

    def test_scope_with_bang_is_interesting(self):
        assert commit_is_interesting("fix!: breaking change")


class TestSinceDate:
    def test_days(self):
        assert "d" in since_date("30d") or since_date("30d").count("-") == 2

    def test_months_parses_to_date(self):
        import re
        assert re.match(r"^\d{4}-\d{2}-\d{2}$", since_date("6m"))

    def test_years_parses_to_date(self):
        import re
        assert re.match(r"^\d{4}-\d{2}-\d{2}$", since_date("1y"))

    def test_explicit_date_passthrough(self):
        assert since_date("2026-01-01") == "2026-01-01"

    def test_uppercase_suffix(self):
        import re
        assert re.match(r"^\d{4}-\d{2}-\d{2}$", since_date("6M"))


class TestWriteCapture:
    def test_creates_new_file(self, tmp_path):
        dest = tmp_path / "pr-1.md"
        status = write_capture(dest, "Title", ["## Metadata", "- x"], ["Body"], dry_run=False)
        assert status == "NEW"
        assert dest.exists()
        assert "# Title" in dest.read_text()

    def test_idempotent_second_write(self, tmp_path):
        dest = tmp_path / "pr-1.md"
        write_capture(dest, "Title", ["## Metadata"], ["Body"], dry_run=False)
        status = write_capture(dest, "Title", ["## Metadata"], ["Body"], dry_run=False)
        assert status == "unchanged"

    def test_detects_change(self, tmp_path):
        dest = tmp_path / "pr-1.md"
        write_capture(dest, "Title", ["## Metadata"], ["Body"], dry_run=False)
        status = write_capture(dest, "Title", ["## Metadata"], ["New body"], dry_run=False)
        assert status == "CHANGED"

    def test_dry_run_writes_nothing(self, tmp_path):
        dest = tmp_path / "pr-1.md"
        status = write_capture(dest, "Title", ["## Metadata"], ["Body"], dry_run=True)
        assert status == "NEW"
        assert not dest.exists()

    def test_content_hash_consistency(self):
        assert sha256_str("abc") == sha256_str("abc")
        assert sha256_str("abc") != sha256_str("abd")