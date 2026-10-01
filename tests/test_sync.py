"""Unit tests for sync.py — corpus sharing logic.

Run: python3 -m pytest tests/test_sync.py -v
"""

import os
import subprocess
import sys
import unittest
import unittest.mock as mock
import importlib.util
from pathlib import Path

import sys, pathlib as _p
_SCRIPTS = (_p.Path(__file__).resolve().parent.parent / "scripts").resolve()
for _rel in ("cmd", "lib", "eval", "harness"):
    if str(_SCRIPTS / _rel) not in sys.path:
        sys.path.insert(0, str(_SCRIPTS / _rel))


def _load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


sync = _load_module("sync", Path(__file__).parent.parent / "scripts" / "cmd/sync.py")


class TestContentPathFilter:
    def test_content_paths_match(self):
        assert sync.is_content_path("evidence/claims/claim-x.md")
        assert sync.is_content_path("patterns/pattern-x.md")
        assert sync.is_content_path("projects/my-project/experience-events/ee.md")
        assert sync.is_content_path("registry/catalog.json")
        assert sync.is_content_path("concepts/concept-x.md")

    def test_non_content_paths_excluded(self):
        assert not sync.is_content_path("fabric.yaml")
        assert not sync.is_content_path("opencode.json")
        assert not sync.is_content_path(".obsidian/app.json")
        assert not sync.is_content_path("README.md")
        assert not sync.is_content_path("scripts/cmd/ingest.py")
        assert not sync.is_content_path(".venv/lib/python/site-packages/x.py")

    def test_prefix_not_substring(self):
        # "evidence/claims-backup/" must NOT match "evidence/claims"
        assert not sync.is_content_path("evidence/claims-backup/x.md")


class TestContentChanges:
    def test_content_changes_filters_porcelain(self, tmp_path, monkeypatch):
        lines = [
            " M scripts/cmd/ingest.py",
            " M evidence/claims/claim-x.md",
            '?? "patterns/pattern y.md"',
            " M fabric.yaml",
        ]
        monkeypatch.setattr(sync, "git_status", lambda: lines)
        out = sync.content_changes()
        assert out == [" M evidence/claims/claim-x.md", '?? "patterns/pattern y.md"']

    def test_content_changes_empty(self, monkeypatch):
        monkeypatch.setattr(sync, "git_status", lambda: [])
        assert sync.content_changes() == []


class TestConflicts:
    def test_list_conflicts_empty(self, tmp_path, monkeypatch):
        monkeypatch.setattr(sync, "VAULT_ROOT", tmp_path)
        assert sync.list_conflicts() == []

    def test_list_conflicts_found(self, tmp_path, monkeypatch):
        monkeypatch.setattr(sync, "VAULT_ROOT", tmp_path)
        cdir = tmp_path / "registry" / "conflicts" / "2026-09-13"
        cdir.mkdir(parents=True)
        (cdir / "c1.md").write_text("---\nstatus: unresolved\n---\n")
        (cdir / "c2.md").write_text("---\nstatus: unresolved\n---\n")
        out = sync.list_conflicts()
        assert len(out) == 2
        assert all("registry/conflicts" in o for o in out)


class TestPlaneClassification:
    """#100: PR merge policy input — a change set is as risky as its riskiest file."""

    def test_evidence_plane(self):
        for p in ("evidence/raw/x.md", "evidence/sources/src-x.md",
                  "evidence/traces/change-sets/2026-01-01-x/manifest.md",
                  "evidence/insights/proj/i.md", "evidence/_inbox/n.md"):
            assert sync.classify_change(p) == "evidence", p

    def test_atom_plane(self):
        for p in ("evidence/claims/claim-x.md", "concepts/c.md", "patterns/p.md",
                  "anti-patterns/ap.md", "projects/proj/decisions/d.md",
                  "global/entities/e.md", "questions/q.md", "domains/ontology.md"):
            assert sync.classify_change(p) == "atom", p

    def test_registry_plane(self):
        assert sync.classify_change("registry/log.md") == "registry"
        assert sync.classify_change("registry/catalog.json") == "registry"

    def test_unknown_fails_closed(self):
        assert sync.classify_change("random/file.md") == "other"
        assert sync.classify_changes(["evidence/raw/a.md", "random/file.md"]) == "atom"

    def test_worst_case_wins(self):
        assert sync.classify_changes(["evidence/raw/a.md"]) == "evidence"
        assert sync.classify_changes(["evidence/raw/a.md", "patterns/p.md"]) == "atom"
        assert sync.classify_changes(["registry/log.md"]) == "registry"
        assert sync.classify_changes([]) == "registry"


class TestSyncModeConfig:
    def test_default_solo(self, monkeypatch):
        import fabric_config as fc
        monkeypatch.setattr(fc, "get_config", lambda: {}, raising=False)
        assert sync.sync_mode() == "solo"
        assert sync.evidence_prs_policy() == "auto"

    def test_team_and_review(self, monkeypatch):
        import fabric_config as fc
        cfg = {"sync": {"mode": "team", "evidence_prs": "review"}}
        monkeypatch.setattr(fc, "get_config", lambda: cfg, raise_=False) if False else None
        import unittest.mock as mock
        with mock.patch.object(fc, "get_config", lambda: cfg):
            assert sync.sync_mode() == "team"
            assert sync.evidence_prs_policy() == "review"

    def test_invalid_falls_back_solo(self, monkeypatch):
        import fabric_config as fc
        cfg = {"sync": {"mode": "banana", "evidence_prs": "maybe"}}
        import unittest.mock as mock
        with mock.patch.object(fc, "get_config", lambda: cfg):
            assert sync.sync_mode() == "solo"
            assert sync.evidence_prs_policy() == "auto"


class TestPrPolicy:
    def test_evidence_auto_by_default(self):
        changes = [" M evidence/raw/x.md", " M evidence/sources/y.md"]
        assert sync.pr_merge_policy(changes) == "auto-merge"

    def test_atom_always_review(self):
        changes = [" M evidence/raw/x.md", " M patterns/p.md"]
        import unittest.mock as mock
        with mock.patch.object(sync, "evidence_prs_policy", lambda: "auto"):
            assert sync.pr_merge_policy(changes) == "review"

    def test_review_setting_overrides_auto(self):
        import unittest.mock as mock
        import importlib
        policy_mod = importlib.import_module("sync_lib.policy")
        with mock.patch.object(policy_mod, "evidence_prs_policy", lambda: "review"):
            assert sync.pr_merge_policy([" M evidence/raw/x.md"]) == "review"


class TestPrBody:
    def test_body_embeds_manifest_and_planes(self, monkeypatch):
        import importlib
        policy_mod = importlib.import_module("sync_lib.policy")
        monkeypatch.setattr(policy_mod, "machine_name", lambda: "testbox")
        import importlib
        pr_mod = importlib.import_module("sync_lib.pr")
        monkeypatch.setattr(pr_mod, "change_set_manifests_for_range", lambda base: [
            "evidence/traces/change-sets/2026-09-27-x/manifest.md"])
        changes = [" M evidence/raw/a.md", " M evidence/claims/c.md", " M registry/log.md"]
        body = sync.build_pr_body(changes, "abc123")
        assert "type: change-set" in body
        assert "sync-pr: true" in body
        assert "machine: testbox" in body
        assert "2026-09-27-x" in body
        assert "**atom** (1):" in body
        assert "**evidence** (1):" in body
        assert "waits for human review" in body

    def test_branch_name_shape(self, monkeypatch):
        import importlib
        policy_mod = importlib.import_module("sync_lib.policy")
        monkeypatch.setattr(policy_mod, "machine_name", lambda: "testbox")
        import re
        assert re.match(r"^sync/testbox-\d{8}-\d{4}$", sync.pr_branch_name())

    def test_machine_name_sanitized(self):
        import socket, re
        name = sync.machine_name()
        assert re.match(r"^[a-z0-9-]{1,30}$", name)

class TestResolveInteractive:
    """#14: the resolver flow when no strategy is given."""

    @staticmethod
    def _conflict(tmp_path, monkeypatch):
        monkeypatch.setattr(sync, "VAULT_ROOT", tmp_path)
        cdir = tmp_path / "registry" / "conflicts" / "2026-09-27"
        cdir.mkdir(parents=True)
        (cdir / "c1.md").write_text(
            "---\ntype: sync-conflict\npath: evidence/claims/claim-x.md\ndate: 2026-09-27\nstatus: unresolved\n---\n\n"
            "# Sync conflict: evidence/claims/claim-x.md\n\n"
            "## Ours (this machine)\n\n```\nA version\n```\n\n"
            "## Theirs (remote)\n\n```\nB version\n```\n")
        (tmp_path / "evidence" / "claims").mkdir(parents=True, exist_ok=True)
        (tmp_path / "evidence" / "claims" / "claim-x.md").write_text("A version\n")
        return cdir / "c1.md"

    def test_interactive_picks_ours(self, tmp_path, monkeypatch, capsys):
        conflict = self._conflict(tmp_path, monkeypatch)
        monkeypatch.setattr("builtins.input", lambda _: "ours")
        sync.cmd_resolve(str(conflict), None)
        out = capsys.readouterr().out
        assert "Resolved [ours]" in out
        assert not conflict.exists()  # record consumed

    def test_interactive_skip_leaves_pending(self, tmp_path, monkeypatch, capsys):
        conflict = self._conflict(tmp_path, monkeypatch)
        monkeypatch.setattr("builtins.input", lambda _: "skip")
        with mock.patch("builtins.input", lambda _: "skip"):
            try:
                sync.cmd_resolve(str(conflict), None)
            except SystemExit as e:
                assert e.code == 0
        assert conflict.exists()  # left pending
        out = capsys.readouterr().out
        assert "SYNC-CONFLICT gate stays up" in out

    def test_interactive_shows_diff(self, tmp_path, monkeypatch, capsys):
        conflict = self._conflict(tmp_path, monkeypatch)
        answers = iter(["skip"])
        monkeypatch.setattr("builtins.input", lambda _: next(answers))
        try:
            sync.cmd_resolve(str(conflict), None)
        except SystemExit:
            pass
        out = capsys.readouterr().out
        assert "ours (this machine)" in out and "theirs (remote)" in out


class TestStandaloneCorpusModel(unittest.TestCase):
    """2026-10-01: the corpus is a standalone git repo (corpus/ owns the git;
    remote root == corpus content — no branch aliasing)."""

    def setUp(self):
        import tempfile, shutil, subprocess
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        fab = self.tmp / "fabric"
        corpus = fab / "corpus"
        (corpus / "registry" / "promotions").mkdir(parents=True)
        (corpus / "patterns").mkdir()
        (corpus / "patterns" / "pattern-demo.md").write_text(
            "---\ntype: pattern\n---\nbody\n")
        (corpus / "registry" / "catalog.json").write_text("{}")
        (fab / "AGENTS.md").write_text("---\ntype: index\n---\nmarker\n")
        (corpus / "AGENTS.md").write_text("---\ntype: index\n---\nmarker\n")
        subprocess.run(["git", "init", "-q", "-b", "main", str(fab)], check=True)
        subprocess.run(["git", "-C", str(fab), "add", "-A"], check=True)
        subprocess.run(["git", "-C", str(fab), "-c", "user.email=t@t",
                        "-c", "user.name=t", "commit", "-qm", "legacy"],
                       check=True, capture_output=True)
        self.fab, self.corpus = fab, corpus
        patches = [
            mock.patch.object(sync, "VAULT_ROOT", corpus),
            mock.patch.dict(os.environ, {"WIKI_FABRIC_DIR": str(fab)}),
        ]
        for p in patches:
            p.start(); self.addCleanup(p.stop)

    def test_migrate_creates_standalone_corpus(self):
        fab, corpus = self.fab, self.corpus
        sync.cmd_migrate(None)
        self.assertTrue((corpus / ".git").is_dir())
        head = subprocess.run(["git", "-C", str(corpus), "rev-parse", "HEAD"],
                              capture_output=True, text=True).stdout.strip()
        self.assertTrue(head, "corpus has its own history")
        tracked = subprocess.run(["git", "-C", str(fab), "ls-files", "corpus/"],
                                 capture_output=True, text=True).stdout.strip()
        self.assertFalse(tracked, "outer no longer tracks corpus content")
        self.assertIn("corpus/", (fab / ".gitignore").read_text())
        sync.cmd_migrate(None)  # double-migrate is a no-op (no raise)

    def test_migrate_wires_remote_and_pushes(self):
        import subprocess, tempfile
        remote = tempfile.mkdtemp()
        self.addCleanuplambda = None
        subprocess.run(["git", "init", "-q", "--bare", remote], check=True)
        sync.cmd_migrate(remote)
        r = subprocess.run(["git", "-C", str(self.corpus), "ls-remote", remote,
                            "refs/heads/main"], capture_output=True, text=True)
        self.assertIn("refs/heads/main", r.stdout)

    def test_push_after_migrate_no_legacy_warning(self):
        import tempfile
        remote = tempfile.mkdtemp()
        subprocess.run(["git", "init", "-q", "--bare", remote], check=True)
        sync.cmd_init(remote)
        (self.corpus / "patterns" / "pattern-two.md").write_text(
            "---\ntype: pattern\n---\nbody\n")
        sync.cmd_push("second")
        # reaching here without SystemExit + remote updated = no legacy block
        r = subprocess.run(["git", "-C", str(self.corpus), "ls-remote", remote,
                            "refs/heads/main"], capture_output=True, text=True)
        self.assertTrue(r.stdout.strip())

    def test_validate_fabric_rejects_non_git_content_dir(self):
        import shutil
        shutil.rmtree(self.fab / ".git", ignore_errors=True)
        shutil.rmtree(self.corpus / ".git", ignore_errors=True)
        with self.assertRaises(SystemExit) as ei:
            sync.validate_fabric()
        self.assertEqual(ei.exception.code, 1)
