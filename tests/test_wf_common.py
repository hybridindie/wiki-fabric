"""Tests for wf_common shared helpers + adoption across scripts."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from wf_common import parse_frontmatter, slugify, norm, sha256_file


class TestParseFrontmatter(unittest.TestCase):
    def test_basic(self, ):
        import tempfile
        with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False) as f:
            f.write("---\ntype: claim\nid: claim-x\n---\n\nBody text.")
            p = Path(f.name)
        fm, body = parse_frontmatter(p)
        assert fm["type"] == "claim" and fm["id"] == "claim-x"
        assert "Body text." in body

    def test_missing_block_returns_text(self):
        import tempfile
        with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False) as f:
            f.write("Just prose, no frontmatter.")
            p = Path(f.name)
        fm, body = parse_frontmatter(p)
        assert fm == {} and body == "Just prose, no frontmatter."

    def test_broken_yaml_falls_back(self):
        import tempfile
        with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False) as f:
            f.write("---\ntitle: [unclosed\n  bad: {yaml\n---\n\nBody.")
            p = Path(f.name)
        fm, body = parse_frontmatter(p)
        assert fm == {} and "Body." in body

    def test_empty_frontmatter(self):
        import tempfile
        with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False) as f:
            f.write("---\n---\n\nBody.")
            p = Path(f.name)
        fm, body = parse_frontmatter(p)
        assert fm == {}


class TestHelpers(unittest.TestCase):
    def test_slugify(self):
        assert slugify("Hello World — Test!") == "hello-world-test"
        assert slugify("  ") == ""

    def test_norm(self):
        assert norm("The Sky, is BLUE") == "the sky is blue"
        assert norm(None) == ""

    def test_sha256_file(self):
        import hashlib, tempfile
        with tempfile.NamedTemporaryFile("wb", delete=False) as f:
            f.write(b"hello")
            p = Path(f.name)
        assert sha256_file(p) == hashlib.sha256(b"hello").hexdigest()


class TestScriptsUseSharedHelpers(unittest.TestCase):
    """The duplication fix: these scripts must import from wf_common, not
    re-define their own copies."""

    def test_no_duplicate_parse_frontmatter_defs(self):
        scripts = (Path(__file__).parent.parent / "scripts").glob("*.py")
        offenders = []
        for s in scripts:
            if s.name in ("wf_common.py", "lint.py"):  # lint has the 3-tuple variant
                continue
            text = s.read_text()
            if "from wf_common import" not in text and "def parse_frontmatter" in text:
                offenders.append(s.name)
        assert offenders == [], f"scripts redefining parse_frontmatter without wf_common: {offenders}"

    def test_no_duplicate_norm_slugify_defs(self):
        scripts = (Path(__file__).parent.parent / "scripts").glob("*.py")
        offenders = []
        for s in scripts:
            if s.name in ("wf_common.py", "bootstrap-project.py"):  # bp has a variant
                continue
            text = s.read_text()
            if "def norm(s):" in text or "def slugify(text):" in text:
                offenders.append(s.name)
        assert offenders == [], f"scripts redefining norm/slugify: {offenders}"

    def test_bootstrap_keeps_variant(self):
        """bootstrap-project's slugify collapses double dashes — intentionally local."""
        src = (Path(__file__).parent.parent / "scripts" / "bootstrap-project.py").read_text()
        assert "def slugify" in src


if __name__ == "__main__":
    unittest.main()