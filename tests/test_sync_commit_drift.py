"""#160 S5: wf sync commit-drift — the drift-wave ritual, formalized.

Run: python3 -m pytest tests/test_sync_commit_drift.py -v
"""
import sys
import importlib.util
import subprocess
from pathlib import Path

import pytest

_SCRIPTS = (Path(__file__).resolve().parent.parent / "scripts").resolve()
for _rel in ("cmd", "lib", "sync_lib", ""):
    _d = _SCRIPTS / _rel if _rel else _SCRIPTS
    if str(_d) not in sys.path:
        sys.path.insert(0, str(_d))


def _git_corpus(tmp_path):
    import fabric_config
    corpus = tmp_path / "corpus"
    corpus.mkdir()
    subprocess.run(["git", "init", "-q", "-b", "main"], cwd=corpus, check=True)
    subprocess.run(["git", "config", "user.email", "t@t"], cwd=corpus, check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=corpus, check=True)
    (corpus / "AGENTS.md").write_text("---\ntype: index\n---\n\n# x\n")
    subprocess.run(["git", "add", "-A"], cwd=corpus, check=True)
    subprocess.run(["git", "commit", "-qm", "seed"], cwd=corpus, check=True)
    monkey = fabric_config
    return corpus


def _load():
    spec = importlib.util.spec_from_file_location("sy_cd", _SCRIPTS / "cmd/sync.py")
    m = importlib.util.module_from_spec(spec)
    sys.modules["sy_cd"] = m
    spec.loader.exec_module(m)
    return m


class TestCommitDrift:
    def test_clean_tree_exit_zero(self, tmp_path, monkeypatch):
        corpus = _git_corpus(tmp_path)
        import fabric_config as fc
        sy = _load()
        monkeypatch.setattr(sy, "VAULT_ROOT", corpus)
        monkeypatch.setattr(fc, "CORPUS_ROOT", corpus, raising=False)
        assert sy.cmd_commit_drift(quiet=False) == 0

    def test_drift_committed_with_plane_summary(self, tmp_path, monkeypatch):
        corpus = _git_corpus(tmp_path)
        import fabric_config as fc
        sy = _load()
        monkeypatch.setattr(sy, "VAULT_ROOT", corpus)
        monkeypatch.setattr(fc, "CORPUS_ROOT", corpus, raising=False)
        (corpus / "evidence" / "raw" / "p").mkdir(parents=True)
        (corpus / "evidence" / "raw" / "p" / "doc.md").write_text("drift")
        (corpus / "evidence" / "claims").mkdir(parents=True)
        (corpus / "evidence" / "claims" / "claim-p-doc-md-000.md").write_text("---\ntype: claim\n---\n")
        rc = sy.cmd_commit_drift()
        assert rc == 0
        out = subprocess.run(["git", "log", "-1", "--format=%s"], cwd=corpus,
                             capture_output=True, text=True).stdout
        assert "drift [" in out and "evidence(s)" in out and "atom(s)" in out
        assert not (subprocess.run(["git", "status", "--porcelain"], cwd=corpus,
                                   capture_output=True, text=True).stdout.strip())

    def test_dry_run_writes_nothing(self, tmp_path, monkeypatch):
        corpus = _git_corpus(tmp_path)
        import fabric_config as fc
        sy = _load()
        monkeypatch.setattr(sy, "VAULT_ROOT", corpus)
        monkeypatch.setattr(fc, "CORPUS_ROOT", corpus, raising=False)
        (corpus / "evidence" / "claims").mkdir(parents=True)
        (corpus / "evidence" / "claims" / "claim-x-000.md").write_text("---\ntype: claim\n---\n")
        buf = __import__("io").StringIO()
        with __import__("contextlib").redirect_stdout(buf):
            rc = sy.cmd_commit_drift(dry_run=True)
        assert rc == 0 and "would commit" in buf.getvalue()
        assert (subprocess.run(["git", "status", "--porcelain"], cwd=corpus,
                               capture_output=True, text=True).stdout.strip())  # untouched
        assert len(subprocess.run(["git", "log", "--oneline"], cwd=corpus,
                                  capture_output=True, text=True).stdout.splitlines()) == 1  # still just seed
