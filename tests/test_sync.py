"""Unit tests for sync.py — corpus sharing logic.

Run: python3 -m pytest tests/test_sync.py -v
"""

import sys
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