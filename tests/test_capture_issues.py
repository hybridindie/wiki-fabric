"""#176 — tracker capture: shaping (issue-record), density pre-filter,
windowing/idempotence, exit contract, thread-index join.
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

os.environ.setdefault("WIKI_FABRIC_DIR", "/tmp/definitely-not-a-fabric-capi")


def _mk_fabric(tmp_path, slug="proj"):
    corpus = tmp_path / "corpus"
    (corpus / "evidence" / "raw" / slug / "issues").mkdir(parents=True)
    (corpus / "registry").mkdir(parents=True, exist_ok=True)
    (tmp_path / "fabric.yaml").write_text(f"repos:\n  {slug}:\n    path: ../{slug}\n")
    os.environ["WIKI_FABRIC_DIR"] = str(tmp_path)
    os.environ["WIKI_FABRIC_ROOT"] = str(tmp_path)  # script-level override seam
    import fabric_config
    import importlib
    importlib.reload(fabric_config)
    return corpus


def _ci(tmp_path):
    import importlib.util as ilu
    spec = ilu.spec_from_file_location(f"ci_{id(tmp_path) % 99999}",
                                       _REPO / "scripts" / "cmd" / "capture-issues.py")
    mod = ilu.module_from_spec(spec)
    sys.modules[f"ci_{id(tmp_path) % 99999}"] = mod
    spec.loader.exec_module(mod)
    return mod


ISSUE_RICH = {"number": 12, "title": "Epic: the token rotation design",
              "body": ("## Rationale\n\nWe rotate tokens because session keys leak; "
                       "rejected the alternative (never-expire) because audit demands rotation. "
                       "Acceptance criteria listed in the linked PR."),
              "state": "CLOSED", "labels": [{"name": "epic"}],
              "url": "https://x/12", "createdAt": "2026-09-01T00:00:00Z",
              "updatedAt": "2026-09-20T00:00:00Z", "closedAt": "2026-09-21T00:00:00Z",
              "comments": 4}
ISSUE_CHORE = {"number": 13, "title": "typo in readme",
               "body": "fix: typo", "state": "CLOSED", "labels": [],
               "url": "", "createdAt": "2026-09-10T00:00:00Z",
               "updatedAt": "2026-09-10T00:00:00Z", "closedAt": "2026-09-10T00:00:00Z",
               "comments": 0}


class TestDensityFilter:
    def test_signal_body_kept(self, tmp_path):
        ci = _ci(tmp_path)
        assert ci.issue_is_interesting(ISSUE_RICH["body"], ISSUE_RICH["labels"], 4) is True

    def test_discussion_thread_kept(self, tmp_path):
        ci = _ci(tmp_path)
        assert ci.issue_is_interesting("short", [], 2) is True

    def test_chore_skipped(self, tmp_path):
        ci = _ci(tmp_path)
        assert ci.issue_is_interesting("bump dep version to fix typo", [], 0) is False

    def test_tiny_body_without_signals_skipped(self, tmp_path):
        ci = _ci(tmp_path)
        assert ci.issue_is_interesting("x" * 10, [], 0) is False

    def test_min_body_len_kept(self, tmp_path):
        ci = _ci(tmp_path)
        long_body = ("we rejected the naive approach because the audit trail "
                     "needs to name the rejecting actor and the reason at "
                     "merge time; here is the rationale and the decision")
        assert ci.issue_is_interesting(long_body, [], 0) is True


class TestShaping:
    def test_issue_record_frontmatter(self, tmp_path):
        corpus = _mk_fabric(tmp_path)
        ci = _ci(tmp_path)
        fm = ci.issue_frontmatter(ISSUE_RICH, "hybridindie/wiki-fabric")
        assert "kind: issue-record" in fm
        assert "issue: 12" in fm and "issue_state: CLOSED" in fm
        assert "closed_at: 2026-09-21" in fm
        assert 'source_repo: "hybridindie/wiki-fabric"' in fm

    def test_capture_issue_writes_record(self, tmp_path):
        corpus = _mk_fabric(tmp_path)
        ci = _ci(tmp_path)
        with mock.patch.object(ci, "gh_comments", return_value=([], False)):
            status, trunc = ci.capture_issue("proj", ISSUE_RICH,
                                             "hybridindie/wiki-fabric",
                                             corpus / "evidence" / "raw" / "proj" / "issues",
                                             include_comments=True, dry_run=False)
        assert status == "NEW" and trunc is False
        rec = corpus / "evidence" / "raw" / "proj" / "issues" / "issue-12.md"
        text = rec.read_text()
        assert text.startswith("---")  # frontmatter first (the #e2e rule)
        assert "## Report" in text and "Rationale" in text

    def test_thread_truncation_flagged_in_page(self, tmp_path):
        corpus = _mk_fabric(tmp_path)
        ci = _ci(tmp_path)
        comments = [{"user": {"login": "a"}, "created_at": "2026-09-02T00:00:00Z",
                     "body": f"comment {i}"} for i in range(3)]
        with mock.patch.object(ci, "gh_comments", return_value=(comments, True)):
            status, trunc = ci.capture_issue("proj", ISSUE_RICH, "r/x",
                                             corpus / "evidence" / "raw" / "proj" / "issues",
                                             True, False)
        assert trunc is True
        assert "truncated at pagination cap" in (corpus / "evidence" / "raw" / "proj" / "issues" / "issue-12.md").read_text()


class TestWindowing:
    def test_github_route_filters_and_counts(self, tmp_path):
        corpus = _mk_fabric(tmp_path)
        ci = _ci(tmp_path)
        with mock.patch.object(ci, "gh_list_windowed",
                               return_value=[ISSUE_RICH, ISSUE_CHORE]), \
             mock.patch.object(ci, "gh_comments", return_value=([], False)):
            stats = ci.capture_issues_github("proj", "r/x", "2026-08-01", None,
                                             30, True, dry_run=True)
        assert stats["new"] == 1  # the chore filtered
        assert stats["threads_truncated"] == 0

    def test_until_exclusive_client_filter(self, tmp_path):
        corpus = _mk_fabric(tmp_path)
        ci = _ci(tmp_path)
        with mock.patch.object(ci, "gh_list_windowed",
                               return_value=[ISSUE_RICH]), \
             mock.patch.object(ci, "gh_comments", return_value=([], False)):
            stats = ci.capture_issues_github("proj", "r/x", "2026-08-01",
                                             "2026-09-02", 30, True, dry_run=True)
        assert stats["new"] == 0  # updated 2026-09-20 >= until → excluded

    def test_state_stamp_separate_namespace(self, tmp_path):
        """Issue captures write their own state stamp (proj-issues) — never
        clobbering the git channel's (proj) .last-capture."""
        corpus = _mk_fabric(tmp_path)
        ci = _ci(tmp_path)
        from capture_git import write_since_state, read_since_state, state_path
        write_since_state("proj-issues", window="1w", truncated=2)
        stamp = state_path("proj-issues").read_text()
        assert "truncated=2" in stamp and "window=" in stamp
        # the git-side namespace is untouched
        assert not state_path("proj").exists()


class TestExitContract:
    def test_unknown_slug_exits_3(self, tmp_path):
        _mk_fabric(tmp_path)
        env = {**os.environ, "WIKI_FABRIC_DIR": str(tmp_path),
               "PATH": "/usr/bin:/bin:/usr/local/bin", "HOME": str(Path.home())}
        r = subprocess.run([sys.executable, str(_REPO / "scripts/cmd/capture-issues.py"),
                            "no-such", "--repo", "x/y", "--dry-run"],
                           env=env, capture_output=True, text=True, timeout=60)
        assert r.returncode == 3
        assert "not a connected project" in r.stderr
        assert "proj" in r.stderr

    def test_summary_exit_0_when_clean(self, tmp_path, capsys):
        corpus = _mk_fabric(tmp_path)
        ci = _ci(tmp_path)
        with mock.patch.object(ci, "gh_list_windowed", return_value=[]), \
             mock.patch.object(ci, "write_since_state", lambda *a, **k: None):
            with mock.patch.object(sys, "argv",
                                   ["capture-issues.py", "proj", "--repo", "x/y", "--dry-run"]):
                import contextlib, io
                try:
                    with contextlib.redirect_stdout(io.StringIO()):
                        rc = ci.main()
                    rc_out = rc
                except SystemExit as e:
                    rc_out = e.code
        assert rc_out == 0  # nothing captured → clean exit (the summary text
        # is pinned by the live-integration run)

    def test_capture_dispatch_routes_issues(self):
        sys.path.insert(0, str(_REPO / "src"))
        import wiki_fabric.dispatch as d
        src = (_REPO / "src" / "wiki_fabric" / "dispatch.py").read_text()
        assert 'argv[0] == "issues"' in src  # the capture case routes issues


class TestThreadJoin:
    def test_rebuild_index_includes_issue_records(self, tmp_path):
        corpus = _mk_fabric(tmp_path)
        rec = corpus / "evidence" / "raw" / "proj" / "issues" / "issue-12.md"
        rec.write_text("""---
type: source
kind: issue-record
source_repo: "x/y"
issue: 12
issue_state: CLOSED
created: 2026-09-01
closed_at: 2026-09-21
title: "the design"
---

# t
""")
        ri = _ri_load(str(id(corpus)))
        ri.VAULT_ROOT = corpus  # the reader's frozen root (paths freeze at import)
        out, n_nodes, n_edges = ri.build_thread_index()
        d = __import__("json").loads(out.read_text())
        kinds = [n.get("kind") for n in d.get("nodes", [])]
        assert "issue-record" in kinds, kinds


def _ri_load(name_suffix=""):
    import importlib.util as ilu
    name = f"ri_{name_suffix}"
    # purge any earlier load — rebuild-index freezes VAULT_ROOT at import
    sys.modules.pop(name, None)
    spec = ilu.spec_from_file_location(name,
                                       _REPO / "scripts" / "cmd" / "rebuild-index.py")
    mod = ilu.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


class TestIngestTier:
    def test_issue_records_share_decay_family(self):
        import ingest as ing
        assert ing.SOURCE_REVIEW_TIERS["issue-record"] == 30

    def test_source_kind_for_issues_path(self):
        import ingest as ing
        assert ing.source_kind("evidence/raw/proj/issues/issue-12.md") == "issue-record"