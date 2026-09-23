"""Tests for wf_common shared helpers + adoption across scripts."""

import sys
import unittest
from pathlib import Path

import sys, pathlib as _p
_SCRIPTS = (_p.Path(__file__).resolve().parent.parent / "scripts").resolve()
for _rel in ("", "cmd", "lib", "eval", "harness"):
    sys.path.insert(0, str(_SCRIPTS / _rel))

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
        scripts = (Path(__file__).parent.parent / "scripts").rglob("*.py")
        offenders = []
        for s in scripts:
            if s.name in ("wf_common.py", "lint.py"):  # lint has the 3-tuple variant
                continue
            text = s.read_text()
            if "from wf_common import" not in text and "def parse_frontmatter" in text:
                offenders.append(s.name)
        assert offenders == [], f"scripts redefining parse_frontmatter without wf_common: {offenders}"

    def test_no_duplicate_norm_slugify_defs(self):
        scripts = (Path(__file__).parent.parent / "scripts").rglob("*.py")
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
        src = (Path(__file__).parent.parent / "scripts" / "cmd/bootstrap-project.py").read_text()
        assert "def slugify" in src


if __name__ == "__main__":
    unittest.main()

class TestUnifiedIgnorePatterns(unittest.TestCase):
    """ignore.patterns: one list, auto-classified (glob default, regex on
    metacharacters, `regex:` prefix as escape hatch)."""

    def _cfg(self, patterns, projects=None):
        cfg = {"ignore": {"patterns": patterns}}
        if projects:
            cfg["ignore"]["projects"] = projects
        return cfg

    def test_glob_default(self):
        from fabric_config import get_ignores, is_ignored
        ig = get_ignores(self._cfg(["vendor/**", "*.log"]))
        assert is_ignored("vendor/a/b/x.md", ig)
        assert is_ignored("deep/nested/x.log", ig)
        assert not is_ignored("src/x.md", ig)

    def test_regex_detected_by_metacharacter(self):
        from fabric_config import get_ignores, is_ignored
        ig = get_ignores(self._cfg([r"_archive\d+/"]))
        assert is_ignored("a/_archive2/old.md", ig)
        assert not is_ignored("a/archives/x.md", ig)

    def test_regex_explicit_prefix(self):
        from fabric_config import get_ignores, is_ignored
        # a literal glob-looking string forced to regex
        ig = get_ignores(self._cfg(["regex:temp.*\\d+\\.tmp$"]))
        assert is_ignored("cache/temp123.tmp", ig)
        assert not is_ignored("cache/temp.tmp", ig)

    def test_prefix_stripped_for_literal_glob_lookalike(self):
        from fabric_config import get_ignores, is_ignored
        # re: prefix on something with no metachars — still treated as regex
        ig = get_ignores(self._cfg(["re:^exact-prefix-"]))
        assert is_ignored("exact-prefix-file.md", ig)
        assert not is_ignored("prefix-file.md", ig)

    def test_per_repo_patterns(self):
        from fabric_config import get_ignores, is_ignored
        ig = get_ignores(self._cfg(["vendor/**"],
                                   {"my-repo": {"patterns": [r"_arch\d+/"]}}))
        ig_my = get_ignores(self._cfg(["vendor/**"],
                                      {"my-repo": {"patterns": [r"_arch\d+/"]}}), "my-repo")
        assert is_ignored("x/_arch3/y.md", ig_my)
        assert not is_ignored("vendor/a/x.md", ig) or is_ignored("vendor/a/x.md", ig_my)

    def test_mixed_explicit_and_unified(self):
        from fabric_config import get_ignores, is_ignored
        cfg = {"ignore": {"globs": ["g-only/**"], "regexes": [r"_e\d+re/"],
                          "patterns": ["p-glob/**", r"p-regex\d+/"]}}
        ig = get_ignores(cfg)
        assert is_ignored("g-only/x.md", ig)      # explicit glob
        assert is_ignored("a/_e1re/x.md", ig)      # explicit regex
        assert is_ignored("p-glob/x.md", ig)      # unified glob
        assert is_ignored("z/p-regex7/x.md", ig)  # unified regex

    def test_classify_direct(self):
        from fabric_config import _classify_ignore_pattern
        assert _classify_ignore_pattern("vendor/**") == ("glob", "vendor/**")
        assert _classify_ignore_pattern(r"\d+") == ("regex", r"\d+")
        assert _classify_ignore_pattern("regex:x*") == ("regex", "x*")
        assert _classify_ignore_pattern("re: foo+") == ("regex", "foo+")
        assert _classify_ignore_pattern("[abc].md") == ("glob", "[abc].md")


class TestLintIgnoreConfig(unittest.TestCase):
    def _check(self, cfg):
        from lint import check_ignore_config
        return check_ignore_config(cfg)

    def test_valid_patterns_clean(self):
        assert self._check({"ignore": {"patterns": ["vendor/**", r"\d+/", "regex:x"]}}) == []

    def test_invalid_regex_flagged(self):
        probs = self._check({"ignore": {"patterns": [r"broken(\d+/"]}})
        assert probs and "IGNORE-CONFIG" in probs[0] and "invalid regex" in probs[0]

    def test_explicit_regexes_also_checked(self):
        probs = self._check({"ignore": {"regexes": [r"bad(+stuff"]}})
        assert probs and "ignore.regexes" in probs[0]

    def test_per_project_checked(self):
        probs = self._check({"ignore": {"projects": {"p": {"patterns": [r"(\d"]}}}})
        assert probs and "ignore.projects.p" in probs[0]

    def test_empty_pattern_flagged(self):
        probs = self._check({"ignore": {"patterns": ["regex:", ""]}})
        assert len(probs) == 2
