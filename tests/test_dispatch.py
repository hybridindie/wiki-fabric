"""Unit tests for the pure-python wf dispatcher (phase 2 of #118)."""

import sys
from pathlib import Path
from unittest import mock

import sys, pathlib as _p
_SCRIPTS = (_p.Path(__file__).resolve().parent.parent / "scripts").resolve()
for _rel in ("cmd", "lib", "eval", "harness"):
    if str(_SCRIPTS / _rel) not in sys.path:
        sys.path.insert(0, str(_SCRIPTS / _rel))

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import wiki_fabric.dispatch as dispatch


class TestVerbs:
    def test_all_expected_verbs_registered(self):
        expected = {"query", "context", "gate", "thread", "lint", "ingest",
                    "review", "sync", "log", "capture", "export", "status",
                    "install", "update", "bootstrap", "vault", "doctor",
                    "rebuild-index", "integrations", "version", "hook",
                    "harness", "skill", "okf", "promote", "promote-domains",
                    "mine", "models", "repos"}
        assert expected <= set(dispatch.VERBS)

    def test_unknown_verb_rejected(self, capsys):
        rc = dispatch.main(["no-such-verb"])
        assert rc == 1
        assert "Unknown command" in capsys.readouterr().err

    def test_help_zero(self, capsys):
        assert dispatch.main(["help"]) == 0

    def test_version_flag(self, capsys):
        assert dispatch.main(["--version"]) == 0
        assert "wf 0." in capsys.readouterr().out

    def test_version_short_flag(self, capsys):
        assert dispatch.main(["-v"]) == 0
        assert "wf 0." in capsys.readouterr().out

    def test_help_command_routes_to_script_argparse(self, capsys):
        rc = dispatch.main(["help", "ingest"])
        assert rc == 0
        out = capsys.readouterr().out
        assert "--extract-claims" in out  # the script parser's own flags

    def test_help_unknown_suggests(self, capsys):
        rc = dispatch.main(["help", "ingets"])
        assert rc == 1
        err = capsys.readouterr().err
        assert "Unknown command" in err
        assert "Did you mean: wf ingest?" in err

    def test_unknown_verb_suggests(self, capsys):
        rc = dispatch.main(["ingets"])
        assert rc == 1
        assert "Did you mean: wf ingest?" in capsys.readouterr().err

    def test_help_dispatch_native_verb_falls_back(self, capsys):
        # a verb without a _SCRIPT_FOR_VERB entry: docstring fallback
        rc = dispatch.main(["help", "status"])
        assert rc == 0
        assert "wf status" in capsys.readouterr().out


class TestFindFabric:
    def test_env_override(self, tmp_path, monkeypatch):
        # the env must carry a fabric marker (fabric.yaml/corpus/evidence/projects):
        # an EMPTY $WIKI_FABRIC_DIR is a pending install target, not a fabric
        (tmp_path / "fabric.yaml").write_text("owner: t\n")
        monkeypatch.setenv("WIKI_FABRIC_DIR", str(tmp_path))
        assert dispatch.find_fabric() == tmp_path.resolve()

    def test_empty_env_dir_is_not_a_fabric(self, tmp_path, monkeypatch):
        monkeypatch.setenv("WIKI_FABRIC_DIR", str(tmp_path))
        assert dispatch.find_fabric() != tmp_path.resolve()

    def test_dev_sibling_vault(self, tmp_path, monkeypatch):
        harness = tmp_path / "harness"
        (harness / "scripts" / "cmd").mkdir(parents=True)
        (harness / "scripts" / "wiki-fabric.sh").write_text("#!/bin/sh\n")
        vault = tmp_path / "vault"
        (vault / "corpus").mkdir(parents=True)
        monkeypatch.setattr(dispatch, "harness_root", lambda: harness)
        monkeypatch.delenv("WIKI_FABRIC_DIR", raising=False)
        assert dispatch.find_fabric() == vault.resolve()

    def test_none_when_no_fabric(self, tmp_path, monkeypatch):
        # cwd deep in a dir with no fabric markers and no XDG default
        work = tmp_path / "empty"
        work.mkdir()
        monkeypatch.delenv("WIKI_FABRIC_DIR", raising=False)
        monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "no-xdg"))
        monkeypatch.chdir(work)
        # the real harness root may have a real sibling vault — point the walker away
        monkeypatch.setattr(dispatch, "harness_root", lambda: work)
        assert dispatch.find_fabric() is None


class TestCorpusRoot:
    def test_nested_corpus(self, tmp_path):
        (tmp_path / "corpus" / "evidence").mkdir(parents=True)
        (tmp_path / "corpus" / "evidence" / "claims").mkdir()
        (tmp_path / "corpus" / "evidence" / "claims" / "claim-x.md").write_text("x")
        assert dispatch.corpus_root(tmp_path) == tmp_path / "corpus"

    def test_legacy_layout(self, tmp_path):
        # legacy layout needs real content (empty skeletons resolve fresh — #e2e)
        (tmp_path / "evidence" / "raw").mkdir(parents=True)
        (tmp_path / "evidence" / "raw" / "doc.md").write_text("x")
        assert dispatch.corpus_root(tmp_path) == tmp_path


class TestCaptureRouting:
    def test_chat_subcommand(self, tmp_path, monkeypatch):
        calls = []
        monkeypatch.setattr(dispatch, "find_fabric", lambda: tmp_path)
        monkeypatch.setattr(dispatch, "_run_script",
                            lambda fdir, rel, *a, **kw: calls.append((rel, a)) or 0)
        dispatch.main(["capture", "chat", "proj", "--since", "30d"])
        assert calls[0][0] == "scripts/cmd/capture-chat.py"
        assert calls[0][1][:2] == ("proj", "--since")

    def test_git_capture(self, tmp_path, monkeypatch):
        calls = []
        monkeypatch.setattr(dispatch, "find_fabric", lambda: tmp_path)
        monkeypatch.setattr(dispatch, "_run_script",
                            lambda fdir, rel, *a, **kw: calls.append((rel, a)) or 0)
        dispatch.main(["capture", "demo", "--git", "owner/repo"])
        assert calls[0][0] == "scripts/cmd/capture-git.py"
        assert calls[0][1][:3] == ("demo", "--repo", "owner/repo")


class TestUpdateModes:
    def test_packaged_hints_uv_upgrade(self, capsys, monkeypatch):
        monkeypatch.setenv("WF_PACKAGED", "1")
        rc = dispatch.main(["update"])
        out = capsys.readouterr().out
        assert rc == 0
        assert "uv tool upgrade wiki-fabric" in out
        assert "wf sync pull" in out

    def test_dev_update_pulls(self, tmp_path, capsys, monkeypatch):
        monkeypatch.delenv("WF_PACKAGED", raising=False)
        monkeypatch.setattr(dispatch, "find_fabric", lambda: tmp_path)
        harness = tmp_path / "harness"
        (harness / "scripts" / "cmd").mkdir(parents=True)
        monkeypatch.setattr(dispatch, "harness_root", lambda: harness)
        runs = []
        monkeypatch.setattr(dispatch.subprocess, "run",
                            lambda *a, **kw: runs.append(a) or mock.Mock(returncode=0))
        monkeypatch.setattr(dispatch, "_run_script", lambda *a, **kw: 0)
        dispatch.main(["update"])
        assert any("pull" in str(a[0]) for a in runs)