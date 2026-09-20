"""Tests for multi-harness support (harnesses.py)."""

import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
sys.path.insert(0, str(Path(__file__).parent.parent))

from harnesses import (SPECS, body_from, detect_installed, install_instructions,
                       install_skills, marker_for, spec_by_key)

REPO = Path(__file__).parent.parent
BLOCK = body_from(REPO / "system" / "always-on" / "wiki-fabric-block.md")


class TestSpecs(unittest.TestCase):
    def test_all_have_key_and_instructions(self):
        for spec in SPECS:
            assert spec["key"] and spec.get("instructions"), spec["key"]

    def test_agentic_tools_read_agents_md(self):
        for key in ("claude", "opencode", "codex", "pi"):
            spec = spec_by_key(key)
            assert spec and "AGENTS.md" in spec["instructions"], key

    def test_copilot_uses_github_dir(self):
        spec = spec_by_key("copilot")
        assert ".github/copilot-instructions.md" in spec["instructions"]

    def test_skills_dirs_declared_for_skill_harnesses(self):
        for key in ("claude", "opencode"):
            assert spec_by_key(key).get("skills_dir"), key


class TestDetection(unittest.TestCase):
    def test_detects_markers(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / ".claude").mkdir()
            (root / "GEMINI.md").touch()
            keys = [s["key"] for s in detect_installed(root)]
            assert "claude" in keys and "gemini" in keys

    def test_agentic_always_included(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            keys = [s["key"] for s in detect_installed(Path(d))]
            assert "claude" in keys and "codex" in keys  # AGENTS.md readers


class TestInstall(unittest.TestCase):
    def setUp(self):
        import tempfile
        self.tmp = Path(tempfile.mkdtemp())

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_install_writes_managed_block(self):
        spec = spec_by_key("claude")
        written = install_instructions(spec, self.tmp, BLOCK)
        assert written
        text = (self.tmp / "CLAUDE.md").read_text()
        assert marker_for(spec) in text
        assert "wf context" in text  # the actual instruction
        assert "always-on block" not in text  # template H1 stripped

    def test_idempotent(self):
        spec = spec_by_key("copilot")
        install_instructions(spec, self.tmp, BLOCK)
        assert install_instructions(spec, self.tmp, BLOCK) == []  # no rewrite

    def test_force_rewrites_cleanly(self):
        spec = spec_by_key("claude")
        install_instructions(spec, self.tmp, BLOCK)
        install_instructions(spec, self.tmp, BLOCK + "\nnew line", force=True)
        text = (self.tmp / "CLAUDE.md").read_text()
        assert text.count(marker_for(spec)) == 1
        assert "new line" in text

    def test_skills_installed_for_skill_harnesses(self):
        spec = spec_by_key("claude")
        written = install_skills(spec, self.tmp, REPO)
        assert written
        for w in written:
            assert w.exists() and "SKILL.md" in str(w)

    def test_no_skills_for_instruction_only(self):
        spec = spec_by_key("copilot")
        assert install_skills(spec, self.tmp, REPO) == []

    def test_cursor_uses_mdc(self):
        spec = spec_by_key("cursor")
        install_instructions(spec, self.tmp, BLOCK)
        assert (self.tmp / ".cursor" / "rules" / "wiki-fabric.mdc").exists()


if __name__ == "__main__":
    unittest.main()