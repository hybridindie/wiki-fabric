"""#180 (H4) — overlays always travel: bootstrap stages+commits, doctor
checks, the overlay-track sweep, the per-record find_changed_sources fix
(same-content files across repos must not mask real drift), the skip-path
record-hash refresh.
"""

import os
import subprocess
import sys
from pathlib import Path
from unittest import mock

import pytest

_REPO = Path(__file__).resolve().parent.parent
for _p in (str(_REPO / "scripts" / "cmd"), str(_REPO / "scripts" / "lib")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

os.environ.setdefault("WIKI_FABRIC_DIR", "/tmp/definitely-not-a-fabric-h4")


def _git_repo(tmp_path, name, with_overlay=True, commit_overlay=False):
    repo = tmp_path / name
    repo.mkdir()
    subprocess.run(["git", "init", "-q", "-b", "main"], cwd=repo, check=True)
    subprocess.run(["git", "-C", str(repo), "-c", "user.email=t@t", "-c",
                    "user.name=t", "config", "user.email", "t@t"], check=True)
    if with_overlay:
        (repo / ".wiki-overlay.md").write_text(
            f"---\nproject: {name}\nnamespace: {name}\n---\n\n# {name}\n")
    (repo / ".gitignore").write_text("secrets.env\n")
    if with_overlay and commit_overlay:
        subprocess.run(["git", "-C", str(repo), "add", ".wiki-overlay.md"], check=True)
        subprocess.run(["git", "-C", str(repo), "commit", "-qm", "seed"], check=True)
    elif not commit_overlay:
        subprocess.run(["git", "-C", str(repo), "add", ".gitignore"], check=True)
        subprocess.run(["git", "-C", str(repo), "commit", "-qm", "seed"], check=True)
    return repo


def _harness(tmp_path, names):
    (tmp_path / "fabric.yaml").write_text(
        "repos:\n" + "".join(f"  {n}:\n    path: {n}\n" for n in names))  # fixture: repos INSIDE the fabric dir
    os.environ["WIKI_FABRIC_DIR"] = str(tmp_path)
    os.environ["WIKI_FABRIC_ROOT"] = str(tmp_path)
    sys.modules.pop("fabric_config", None)  # any earlier fixture's frozen roots
    import fabric_config
    import importlib
    importlib.reload(fabric_config)
    for n in names:  # each name must resolve as a sibling repo directory
        if not (tmp_path / n).is_dir():
            (tmp_path / n).mkdir()


def _boot(tmp_path):
    import importlib.util as ilu
    spec = ilu.spec_from_file_location(f"boot_{id(tmp_path) % 99999}",
                                       _REPO / "scripts/cmd/bootstrap-project.py")
    mod = ilu.module_from_spec(spec)
    sys.modules[f"boot_{id(tmp_path) % 99999}"] = mod
    spec.loader.exec_module(mod)
    return mod


class TestBootstrapStagesOverlay:
    def test_stage_overlay_commits_tracked(self, tmp_path):
        """A PRE-EXISTING repo bootstrap: the overlay ends UP TRACKED."""
        repo = _git_repo(tmp_path, "proj-a")
        _harness(tmp_path, ["proj-a"])
        boot = _boot(tmp_path)
        args = mock.Mock()
        args._project_root = repo
        boot._stage_overlay_git(args, repo)  # explicit target (no cwd leak)
        out = subprocess.run(["git", "-C", str(repo), "ls-files", "--", ".wiki-overlay.md"],
                             capture_output=True, text=True)
        assert ".wiki-overlay.md" in out.stdout
        log = subprocess.run(["git", "-C", str(repo), "log", "--oneline", "-2"],
                             capture_output=True, text=True).stdout
        assert "track .wiki-overlay.md" in log  # the H4 commit landed

    def test_skips_when_already_tracked(self, tmp_path, capsys):
        _git_repo(tmp_path, "proj-b", commit_overlay=True)
        _harness(tmp_path, ["proj-b"])
        boot = _boot(tmp_path)
        boot._stage_overlay_git(mock.Mock(), tmp_path / "proj-b")
        assert "committed" not in capsys.readouterr().out  # idempotent no-op


class TestDoctorCheck:
    def test_untracked_named(self, tmp_path):
        _git_repo(tmp_path, "proj-c")  # overlay untracked
        _git_repo(tmp_path, "proj-d", commit_overlay=True)  # tracked
        _harness(tmp_path, ["proj-c", "proj-d"])
        sys.modules.pop("fabric_config", None)
        import fabric_config
        import importlib
        importlib.reload(fabric_config)
        lint = _load_mod("lint_h4", _REPO / "scripts/cmd/lint.py")
        r = lint.check_overlay_tracked(fabric_config.get_config())
        assert any("proj-c" in pp and "OVERLAY-UNTRACKED" in pp for pp in r), r
        assert not any("proj-d" in pp for pp in r)


def _load_mod(name, path):
    import importlib.util as ilu
    spec = ilu.spec_from_file_location(name, path)
    mod = ilu.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


class TestSweep:
    def test_overlay_track_sweep(self, tmp_path):
        """The one-shot sweep stages+commits every untracked overlay."""
        _git_repo(tmp_path, "proj-e", commit_overlay=True)
        _git_repo(tmp_path, "proj-f")
        _harness(tmp_path, ["proj-e", "proj-f"])
        sweep = _load_mod("overlay_track", _REPO / "scripts/cmd/overlay-track.py")
        with mock.patch.object(sys, "argv", ["overlay-track.py"]):
            rc = sweep.main()
        assert rc == 0
        tracked = subprocess.run(
            ["git", "-C", str(tmp_path / "proj-f"), "ls-files", "--", ".wiki-overlay.md"],
            capture_output=True, text=True).stdout
        assert ".wiki-overlay.md" in tracked

    def test_sweep_dry_run(self, tmp_path):
        _git_repo(tmp_path, "proj-g")
        _harness(tmp_path, ["proj-g"])
        sweep = _load_mod("overlay_track_dry", _REPO / "scripts/cmd/overlay-track.py")
        out = sweep.stage_overlay(tmp_path / "proj-g", dry_run=True)
        assert out == "would-stage"
        tracked = subprocess.run(
            ["git", "-C", str(tmp_path / "proj-g"), "ls-files", "--", ".wiki-overlay.md"],
            capture_output=True, text=True).stdout
        assert tracked == ""


class TestPerRecordChangedSources:
    """The #180 incidental find: find_changed_sources compares each raw file
    against ITS OWN record — same CONTENT in another repo's record (harness
    installs copy identical CLAUDE.md bytes) never masks real drift."""

    def test_shared_hash_not_masking(self, tmp_path):
        corpus = tmp_path / "corpus"
        for d in ("evidence/raw/proj-a", "evidence/raw/proj-b", "evidence/sources"):
            (corpus / d).mkdir(parents=True)
        (tmp_path / "fabric.yaml").write_text("repos:\n  proj-a:\n    path: ../a\n")
        os.environ["WIKI_FABRIC_DIR"] = str(tmp_path)
        import fabric_config, importlib
        importlib.reload(fabric_config)
        # identical harness-installed content in both repos
        for slug in ("proj-a", "proj-b"):
            (corpus / "evidence" / "raw" / slug / ".wiki-overlay.md").write_text(
                "SAME BYTES\n")
        from wf_common import slugify, sha256_file
        from pathlib import Path as P
        ing = _load_mod("ing_test", _REPO / "scripts/cmd/ingest.py")
        SAME = sha256_file(corpus / "evidence" / "raw" / "proj-a" / ".wiki-overlay.md")
        # proj-a record: current hash ✓ (up to date)
        (corpus / "evidence" / "sources" / f"src-{slugify('proj-a/.wiki-overlay.md')}.md").write_text(
            "sha256: " + SAME + "\nsource_path: evidence/raw/proj-a/.wiki-overlay.md\n")
        # proj-b record: STALE hash (the drift!) — different from the shared content hash
        (corpus / "evidence" / "sources" / f"src-{slugify('proj-b/.wiki-overlay.md')}.md").write_text(
            "sha256: " + "a" * 64 + "\nsource_path: evidence/raw/proj-b/.wiki-overlay.md\n")
        with mock.patch.object(ing, "VAULT_ROOT", corpus):
            changed = ing.find_changed_sources("proj-b")
            assert [f.parent.name for f in changed] == ["proj-b"]  # the DRIFT found
            # and proj-a (record == current) reads clean despite the shared pool
            assert ing.find_changed_sources("proj-a") == []


class TestSkipPathHashRefresh:
    def test_refresh_own_record_on_shared_content_skip(self, tmp_path):
        """The anti-loop SKIP against ANOTHER project's record refreshes the
        OWN record's stale hash — the ledger update, not a re-ingest."""
        corpus = tmp_path / "corpus"
        for d in ("evidence/raw/proj-a", "evidence/raw/proj-b", "evidence/sources"):
            (corpus / d).mkdir(parents=True)
        (tmp_path / "fabric.yaml").write_text("repos:\n  proj-a:\n    path: ../a\n")
        os.environ["WIKI_FABRIC_DIR"] = str(tmp_path)
        import fabric_config, importlib
        importlib.reload(fabric_config)
        ing = _load_mod("ing_skip", _REPO / "scripts/cmd/ingest.py")
        from wf_common import slugify
        SAME = "b" * 64
        # proj-b's record carries the CURRENT (shared) hash — the skip matcher
        (corpus / "evidence" / "sources" / f"src-{slugify('proj-b/.wiki-overlay.md')}.md").write_text(
            "sha256: " + SAME + "\nsource_path: evidence/raw/proj-b/.wiki-overlay.md\n")
        # proj-a's OWN record: stale hash
        own = (corpus / "evidence" / "sources" / f"src-{slugify('proj-a/.wiki-overlay.md')}.md")
        own.write_text("sha256: " + "c" * 64 + "\nsource_path: evidence/raw/proj-a/.wiki-overlay.md\n")
        src = corpus / "evidence" / "raw" / "proj-a" / ".wiki-overlay.md"
        src.write_text("")
        import hashlib
        # make the on-disk hash match the SHARED one (proj-b's): write real bytes
        payload = "same installed content\n"
        src.write_text(payload)
        own_hash_payload = hashlib.sha256(payload.encode()).hexdigest()
        (corpus / "evidence" / "sources" / f"src-{slugify('proj-b/.wiki-overlay.md')}.md").write_text(
            "sha256: " + own_hash_payload + "\nsource_path: evidence/raw/proj-b/.wiki-overlay.md\n")
        with mock.patch.object(ing, "VAULT_ROOT", corpus):
            ok = ing.ingest_source(src, extract_claims=False, model=None,
                                   dry_run=False, namespace="proj-a")
        # the skip happened (content already ingested under proj-b) AND the
        # OWN record's hash was refreshed to match reality
        assert own.read_text().count(own_hash_payload) == 1
        assert ok is False  # skipped, refreshed (the ledger hygiene path)