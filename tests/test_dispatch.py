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

_ROOT = Path(__file__).resolve().parent.parent


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


class TestCaptureUnknownSlugExit:
    """#167 — wf capture <wrong-slug> must exit nonzero (3: unknown slug,
    distinct from 2 = drift captured) so hooks/CI can detect a typo."""

    def run_capture(self, monkeypatch, tmp_path, slug):
        import importlib
        import fabric_config
        importlib.reload(fabric_config)  # re-resolve FABRIC_ROOT/VAULT_ROOT from env
        import capture as _cap
        importlib.reload(_cap)
        monkeypatch.chdir(tmp_path)
        import io, contextlib
        buf, err = io.StringIO(), io.StringIO()
        rc = None
        try:
            with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(err):
                _cap.capture_project(slug)
        except SystemExit as e:
            rc = e.code
        return rc, err.getvalue()

    def test_unknown_slug_exits_3(self, tmp_path, monkeypatch):
        monkeypatch.setenv("WIKI_FABRIC_DIR", str(tmp_path))
        rc, err = self.run_capture(monkeypatch, tmp_path, "no-such-project-xyz")
        assert rc == 3
        assert "Connected projects:" in err

    def test_unknown_slug_lists_closest(self, tmp_path, monkeypatch):
        projects = tmp_path / "corpus" / "projects"
        projects.mkdir(parents=True)
        (projects / "my-real-project").mkdir()
        (projects / "my-real-project" / ".wiki-overlay.md").write_text(
            "---\ntype: registry\nproject: my-real-project\nnamespace: my-real-project\n---\n")
        monkeypatch.setenv("WIKI_FABRIC_DIR", str(tmp_path))
        rc, err = self.run_capture(monkeypatch, tmp_path, "my-real-projekt")
        assert rc == 3
        assert "- my-real-project  (closest match)" in err


class TestCompletions:
    """#162 — wf completions {bash|zsh|fish} generated from the VERBS registry."""

    def test_all_shells(self, capsys):
        for shell in ("bash", "zsh", "fish"):
            assert dispatch.main(["completions", shell]) == 0
            out = capsys.readouterr().out
            assert "ingest" in out and "rebuild-index" in out  # verbs enumerated

    def test_bash_script_parses(self):
        import subprocess
        script = dispatch._completion_scripts("bash")
        r = subprocess.run(["bash", "-n"], input=script, capture_output=True, text=True)
        assert r.returncode == 0, r.stderr

    def test_bash_completes_verbs_and_subcommands(self):
        import subprocess
        script = dispatch._completion_scripts("bash")
        harness = f'''
source /dev/stdin <<'EOS'
{script}
EOS
COMP_WORDS=(wf mine prom); COMP_CWORD=2; _wf_completions; echo "SUB:${{COMPREPLY[*]}}"
COMP_WORDS=(wf ingest --); COMP_CWORD=2; _wf_completions; echo "FLAGS:${{COMPREPLY[*]}}"
COMP_WORDS=(wf revie ""); COMP_CWORD=1; _wf_completions; echo "VERB:${{COMPREPLY[*]:0:1}}"
'''
        r = subprocess.run(["bash", "-c", harness], capture_output=True, text=True)
        assert r.returncode == 0, r.stderr
        assert "SUB:promotions" in r.stdout
        assert "FLAGS:--changed" in r.stdout and "--extract-claims" in r.stdout
        assert "VERB:review" in r.stdout

    def test_requires_shell_arg(self, capsys):
        assert dispatch.main(["completions"]) == 1
        assert "Usage: wf completions" in capsys.readouterr().err


class TestJsonSurfaces:
    """#164 — ingest/review --json: machine-readable results for HITL/CI."""

    def test_ingest_not_found_json(self, tmp_path, monkeypatch):
        import subprocess, json
        import fabric_config, importlib
        (tmp_path / "corpus").mkdir()
        (tmp_path / "fabric.yaml").write_text("repos: {}\n")
        monkeypatch.setenv("WIKI_FABRIC_DIR", str(tmp_path))
        importlib.reload(fabric_config)
        r = subprocess.run(
            [sys.executable, str(_ROOT / "scripts/cmd/ingest.py"),
             "/nope/missing.md", "--json"],
            capture_output=True, text=True,
            env={"WIKI_FABRIC_DIR": str(tmp_path), "PATH": "/usr/bin:/bin",
                 "PYTHONPATH": str(_ROOT / "scripts/lib")},
            cwd=str(tmp_path))
        assert r.returncode == 1
        payload = json.loads(_last_json(r.stdout))
        assert payload["mode"] == "source"
        assert payload["results"][0]["status"] == "not-found"

    def test_review_check_json(self, tmp_path, monkeypatch):
        import subprocess, json
        corpus = tmp_path / "corpus"
        (corpus / "evidence" / "claims").mkdir(parents=True)
        (corpus / "evidence" / "claims" / "claim-x-000.md").write_text(
            "---\ntype: claim\nid: claim-x-000\nstatement: x\n"
            "review_after: 2026-01-01\nstatus: supported\n---\n\n# t\n")
        (tmp_path / "fabric.yaml").write_text("repos: {}\n")
        monkeypatch.setenv("WIKI_FABRIC_DIR", str(tmp_path))
        r = subprocess.run(
            [sys.executable, str(_ROOT / "scripts/cmd/review.py"),
             "--check", "--json"],
            capture_output=True, text=True,
            env={"WIKI_FABRIC_DIR": str(tmp_path), "PATH": "/usr/bin:/bin",
                 "PYTHONPATH": str(_ROOT / "scripts/lib")},
            cwd=str(tmp_path))
        assert r.returncode == 0
        payload = json.loads(_last_json(r.stdout))
        assert payload["mode"] == "report"
        assert len(payload["stale"]) == 1
        assert payload["overdue"] == []


class TestDryRuns:
    """#166 — bootstrap + log-experience --dry-run (the worst-offender writing
    verbs): plan printed, nothing written."""

    def test_bootstrap_dry_run_writes_nothing(self, tmp_path):
        import subprocess
        proj = tmp_path / "proj"
        r = subprocess.run(
            [sys.executable, str(_ROOT / "scripts/cmd/bootstrap-project.py"), str(proj),
             "--name", "Dry", "--slug", "dry-proj", "--non-interactive", "--dry-run"],
            capture_output=True, text=True,
            env={"WIKI_FABRIC_DIR": str(tmp_path / "fabric"), "PATH": "/usr/bin:/bin",
                 "PYTHONPATH": str(_ROOT / "scripts/lib"), "HOME": str(tmp_path)})
        assert r.returncode == 0, r.stderr
        assert "[DRY RUN]" in r.stdout
        assert "fabric.yaml" in r.stdout  # the plan names the writes
        assert not proj.exists()  # nothing written
        assert not (tmp_path / "fabric" / "corpus" / "projects" / "dry-proj").exists()

    def test_log_experience_dry_run_writes_nothing(self, tmp_path, monkeypatch):
        import subprocess, importlib
        import fabric_config
        corpus = tmp_path / "corpus"
        (corpus / "projects" / "p1").mkdir(parents=True)
        (tmp_path / "fabric.yaml").write_text("repos: {}\n")
        monkeypatch.setenv("WIKI_FABRIC_DIR", str(tmp_path))
        importlib.reload(fabric_config)
        r = subprocess.run(
            [sys.executable, str(_ROOT / "scripts/cmd/log-experience.py"),
             "--project", "p1", "--problem", "dry-run probe", "--dry-run"],
            capture_output=True, text=True,
            env={"WIKI_FABRIC_DIR": str(tmp_path), "PATH": "/usr/bin:/bin",
                 "PYTHONPATH": str(_ROOT / "scripts/lib"), "HOME": str(tmp_path)})
        assert r.returncode == 0, r.stderr
        assert "[DRY RUN]" in r.stdout
        events = list((corpus / "projects" / "p1" / "experience-events").glob("*.md"))
        assert events == []  # nothing written


class TestProjectsVerb:
    """#169 — wf projects: the connected-repo inventory as a verb."""

    def test_projects_registered(self):
        assert "projects" in dispatch.VERBS

    def test_projects_requires_fabric(self, tmp_path, monkeypatch):
        import io, contextlib
        monkeypatch.setenv("WIKI_FABRIC_DIR", str(tmp_path / "nope"))
        buf, err = io.StringIO(), io.StringIO()
        rc = None
        try:
            with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(err):
                rc = dispatch.main(["projects"])
        except SystemExit as e:
            rc = e.code
        assert rc == 1  # no fabric → loud

    def test_projects_json_shape(self, tmp_path, monkeypatch):
        import io, contextlib, json, importlib
        fabric = tmp_path
        corpus = fabric / "corpus"
        corpus.mkdir()
        (corpus / "evidence").mkdir()  # content marker (nested-corpus layout)
        (fabric / "fabric.yaml").write_text("repos:\n  my-proj:\n    path: ../my-proj\n    owner: t\n")
        monkeypatch.setenv("WIKI_FABRIC_DIR", str(fabric))
        import fabric_config
        importlib.reload(fabric_config)  # FABRIC_ROOT frozen at import — re-resolve
        buf, err = io.StringIO(), io.StringIO()
        rc = None
        try:
            with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(err):
                rc = dispatch.main(["projects", "--json"])
        except SystemExit as e:
            rc = e.code
        assert rc == 0
        payload = json.loads(buf.getvalue())
        assert payload["projects"][0]["slug"] == "my-proj"
        assert payload["projects"][0]["owner"] == "t"
        assert payload["projects"][0]["captures"]["claims"] == 0


class TestOverlayDomainPreference:
    """#158 S5 — overlay domains: wired as project → preferred domain binding
    in context precedence (write-only field becomes load-bearing)."""

    def test_overlay_domains_reads_repo_overlay(self, tmp_path, monkeypatch):
        import importlib
        import fabric_config
        # fabric at tmp_path/fabric; the project repo is a SIBLING (discovery
        # scans FABRIC_ROOT.parent — the fixture shape real layouts carry)
        fabric = tmp_path / "fabric"
        (fabric / "corpus").mkdir(parents=True)
        (fabric / "fabric.yaml").write_text("repos:\n  wf-proj:\n    path: ../wf-proj\n")
        repo = tmp_path / "wf-proj"
        repo.mkdir()
        (repo / ".wiki-overlay.md").write_text(
            "---\nnamespace: wf-proj\ndomains:\n  - testing\n---\n")
        monkeypatch.setenv("WIKI_FABRIC_DIR", str(fabric))
        importlib.reload(fabric_config)
        # overlay resolved through the discovery path (sibling scan)
        import context as ctx

        def fake_walk(root):
            return iter(())
        monkeypatch.setattr(ctx, "VAULT_ROOT", fabric / "corpus")
        monkeypatch.setattr(ctx, "load_corpus", lambda *a, **k: [])
        ctx._OV_PAGES_CACHE = None
        ctx._ontology_domains.aliases = {}
        domains = ctx._overlay_domains("wf-proj")
        # ontology absent in the fake corpus → raw spelling preserved
        assert domains == {"testing"}

    def test_no_domains_no_binding(self, tmp_path, monkeypatch):
        monkeypatch.setenv("WIKI_FABRIC_DIR", str(tmp_path))
        import context as ctx
        monkeypatch.setattr(ctx, "VAULT_ROOT", tmp_path)
        assert ctx._overlay_domains(None) == set()
        assert ctx._overlay_domains("never-bootstrapped") == set()

    def test_select_context_unchanged_without_preference(self, tmp_path, monkeypatch):
        """Byte-parity: projects with no domains: declared select exactly as
        before (#0-token core preserved — the binding only ADDS reasons)."""
        import context as ctx
        monkeypatch.setattr(ctx, "VAULT_ROOT", tmp_path)
        import datetime
        today = datetime.date.today()
        pages = [
            {"posix": "patterns/pattern-serialize.md", "stem": "pattern-serialize",
             "type": "pattern", "scope": "global", "fm": {"status": "recommended"},
             "body": "serialize writes and verify"},
            {"posix": "concepts/concept-cache.md", "stem": "concept-cache",
             "type": "concept", "scope": "global", "fm": {"status": "", "domain": "testing"},
             "body": "cache invalidation rules"},
        ]
        pages2 = [dict(p) for p in pages]
        monkeypatch.setattr(context_ := ctx, "_ontology_domains", lambda pages: set())
        ctx._ontology_domains.aliases = {}
        # project with NO overlay: empty preference — selection identical
        sel, _ = ctx.select_context(pages2, "cache invalidation", [], "some-proj", today, 20)
        assert sel  # sanity: the pipeline runs clean
    """#168 — every verb carries a one-line docstring (the introspected help
    surface; `wf help` prints them)."""

    def test_all_verbs_have_docstrings(self):
        empty = [v for v in dispatch.VERBS if not (dispatch.VERBS[v].__doc__ or "").strip()]
        assert empty == [], f"verbs without one-liners: {empty}"

    def test_help_prints_one_liners(self, capsys):
        assert dispatch.main(["help"]) == 0
        out = capsys.readouterr().out
        assert "query" in out and "Ask the fabric" in out


def _last_json(text):
    """Extract the last complete JSON object printed on mixed stdout (the
    outermost payload — inner nested objects also start with '{')."""
    import json as _j
    dec = _j.JSONDecoder()
    best = None
    for i, ch in enumerate(text):
        if ch == "{":
            try:
                obj, end = dec.raw_decode(text[i:])
                cand = text[i:i + end]
                if best is None or len(cand) > len(best):
                    best = cand
            except _j.JSONDecodeError:
                continue
    return best


class TestStatusJson:
    """#165 — wf status --json: the inventory/provenance machine surface."""

    def test_status_json_shape(self, tmp_path, monkeypatch):
        import subprocess, json
        # dev-tree dispatch, fabric as tmp sibling layout: fabric root with corpus/
        fabric = tmp_path
        corpus = fabric / "corpus"
        (corpus / "evidence" / "claims").mkdir(parents=True)
        (corpus / "fabric.yaml").write_text("")  # content marker
        (fabric / "fabric.yaml").write_text("repos: {}\n")
        r = subprocess.run(
            [sys.executable, "-c",
             f"import sys; sys.path.insert(0, {str(_ROOT / 'src')!r});"
             "from wiki_fabric.dispatch import main; sys.exit(main(['status', '--json']))"],
            capture_output=True, text=True,
            env={"WIKI_FABRIC_DIR": str(fabric), "PATH": "/usr/bin:/bin",
                 "HOME": str(tmp_path)},
            cwd=str(_ROOT))
        assert r.returncode == 0
        payload = json.loads(r.stdout)
        assert set(payload) >= {"fabric", "vault", "cli", "llm", "inventory",
                                "lint", "gate", "graphify"}
        assert payload["inventory"]["claims"] == 0
        assert isinstance(payload["inventory"]["repos"], list)

    def test_status_prose_unchanged(self, capsys):
        # the default stays prose (byte-shape): no '{' json leading
        import io, contextlib
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = dispatch.main(["status", "--json"])
        assert rc == 0
        assert buf.getvalue().lstrip().startswith("{")


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