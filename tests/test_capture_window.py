"""Activity-bounded capture windows (capture-git.py) + sha256→claim staleness.

Run: python3 -m pytest tests/test_capture_window.py -v
"""

import sys
import importlib.util
from pathlib import Path

import pytest
import pathlib
import io
import contextlib

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


capture_git = _load_module("capture_git_window", Path(__file__).parent.parent / "scripts" / "cmd/capture-git.py")
effective_window = capture_git.effective_window
window_larger = capture_git.window_larger
since_date = capture_git.since_date
read_since_state = capture_git.read_since_state
write_since_state = capture_git.write_since_state


class TestWindowLarger:
    def test_shorter_is_not_larger(self):
        assert not window_larger("1w", "6m")

    def test_longer_is_larger(self):
        assert window_larger("1y", "6m")

    def test_equality(self):
        assert not window_larger("6m", "6m")


class TestEffectiveWindow:
    """Largest ladder window whose count fits the budget — shrinking the
    window instead of truncating the list."""

    def test_quiet_repo_keeps_requested_window(self):
        window, counts = effective_window(lambda iso: 3, "6m", 30)
        assert window == "6m"
        assert counts == {"6m": 3}

    def test_active_repo_shrinks_to_fitting_window(self):
        counts_by_iso = {}

        def count_fn(iso):
            # 100 in 6m, 90 in 3m, 80 in 1m ... 20 in 1w, 5 in 3d
            for w, n in (("6m", 100), ("3m", 90), ("1m", 80), ("2w", 50),
                         ("1w", 20), ("3d", 5), ("1d", 2)):
                if since_date(w) == iso:
                    counts_by_iso[w] = n
                    return n
            return 0

        window, counts = effective_window(count_fn, "6m", 30)
        assert window == "1w"
        assert counts_by_iso["1w"] == 20  # ladder stops at the first fitting window
        assert "3d" not in counts_by_iso  # no wasted probes past the fit

    def test_extreme_activity_narrows_to_1d(self):
        window, _ = effective_window(lambda iso: 500, "6m", 30)
        assert window == "1d"

    def test_budget_all_disables_reduction(self):
        for budget in ("all", None, ""):
            window, counts = effective_window(lambda iso: 9999, "6m", budget)
            assert window == "6m"
            assert counts == {}

    def test_uncountable_keeps_requested(self):
        window, counts = effective_window(lambda iso: None, "6m", 30)
        assert window == "6m"
        assert counts == {}

    def test_bad_budget_keeps_requested(self):
        window, _ = effective_window(lambda iso: 500, "6m", "lots")
        assert window == "6m"

    def test_superset_windows_not_reprobed(self):
        probed = []

        def count_fn(iso):
            probed.append(iso)
            return 200

        window, counts = effective_window(count_fn, "3m", 30)
        assert window == "1d"
        # 3m is the requested probe; nothing longer than 3m (6m) is probed
        assert all(iso >= since_date("3m") for iso in probed)

    def test_exact_budget_fits(self):
        window, _ = effective_window(lambda iso: 30, "6m", 30)
        assert window == "6m"


class TestSinceStateWindowStamp:
    """The chosen window travels in .last-capture; --since-state reads it back
    as its base so a quiet stretch never silently re-expands coverage."""

    def test_roundtrip_with_window(self, tmp_path, monkeypatch):
        monkeypatch.setattr(capture_git, "EVIDENCE_RAW", tmp_path)
        write_since_state("proj", window="1w")
        text = (tmp_path / "proj" / "git" / ".last-capture").read_text()
        assert "window=" in text
        assert read_since_state("proj").startswith("20")  # ISO date, not "1w"

    def test_window_value_roundtrips(self, tmp_path, monkeypatch):
        monkeypatch.setattr(capture_git, "EVIDENCE_RAW", tmp_path)
        write_since_state("proj", window="1w")
        iso = read_since_state("proj")
        assert iso == since_date("1w")

    def test_legacy_state_without_stamp(self, tmp_path, monkeypatch):
        monkeypatch.setattr(capture_git, "EVIDENCE_RAW", tmp_path)
        sp = tmp_path / "proj" / "git" / ".last-capture"
        sp.parent.mkdir(parents=True)
        sp.write_text("2026-09-01")
        assert read_since_state("proj") == "2026-09-01"

    def test_plain_write_still_date_only(self, tmp_path, monkeypatch):
        monkeypatch.setattr(capture_git, "EVIDENCE_RAW", tmp_path)
        write_since_state("proj")
        import re
        assert re.match(r"^\d{4}-\d{2}-\d{2}$", read_since_state("proj"))


class TestGhListWindowed:
    """Server-side window: --search narrows before --limit applies."""

    def test_search_form_used(self, monkeypatch):
        calls = []
        monkeypatch.setattr(capture_git, "gh",
                            lambda *a, expect_json=False: calls.append(a) or [])
        out = capture_git.gh_list_windowed("pr", "o/r", "2026-06-01", 30, "number", "merged")
        assert calls, "gh should be called"
        args = [str(x) for x in calls[0]]
        assert "--search" in args
        # the merged-window filter travels in the search string
        srch = args[args.index("--search") + 1]
        assert "merged:>=2026-06-01" in srch

    def test_fallback_when_search_fails(self, monkeypatch):
        responses = [[], None]  # search form fails -> unsearched list
        monkeypatch.setattr(capture_git, "gh",
                            lambda *a, expect_json=False: responses.pop(0))
        out = capture_git.gh_list_windowed("pr", "o/r", "2026-06-01", 30, "number", "merged")
        assert isinstance(out, list)


class TestMakeGithubCounter:
    def test_pr_counter_uses_merged(self, monkeypatch):
        captured = {}
        def fake_gh(*a, expect_json=False):
            captured["args"] = [str(x) for x in a]
            return {"total_count": 7}
        monkeypatch.setattr(capture_git, "gh", fake_gh)
        fn = capture_git.make_github_counter("o/r", "pr")
        assert fn("2026-06-01") == 7
        q = captured["args"][captured["args"].index("-f") + 1]
        assert "merged:>=2026-06-01" in q and "type:pr" in q

    def test_issue_counter_uses_updated(self, monkeypatch):
        captured = {}
        def fake_gh(*a, expect_json=False):
            captured["args"] = [str(x) for x in a]
            return {"total_count": 3}
        monkeypatch.setattr(capture_git, "gh", fake_gh)
        fn = capture_git.make_github_counter("o/r", "issue")
        assert fn("2026-06-01") == 3
        q = captured["args"][captured["args"].index("-f") + 1]
        assert "updated:>=2026-06-01" in q and "type:issue" in q

    def test_uncountable_returns_none(self, monkeypatch):
        monkeypatch.setattr(capture_git, "gh", lambda *a, expect_json=False: None)
        fn = capture_git.make_github_counter("o/r", "pr")
        assert fn("2026-06-01") is None


class TestStaleMarkDerivedClaims:
    """sha256 drift on the same raw path → old-revision claims go contested
    with stale_after=today (0 tokens, mechanical)."""

    @pytest.fixture()
    def fabric_env(self, tmp_path, monkeypatch):
        """Empty fabric skeleton: vault/evidence/{raw,sources,claims}."""
        vault = tmp_path / "vault"
        for sub in ("evidence/raw", "evidence/sources", "evidence/claims"):
            (vault / sub).mkdir(parents=True)
        monkeypatch.setattr(capture_git, "VAULT_ROOT", vault)  # not used here, but consistent
        ingest = _load_module("ingest_window", _SCRIPTS / "cmd/ingest.py")
        monkeypatch.setattr(ingest, "VAULT_ROOT", vault)
        monkeypatch.setattr(ingest, "args_dry_run", False)
        return ingest, vault

    @staticmethod
    def _seed(ingest, vault, name, sha, source_rel, claims=1):
        (vault / "evidence/sources" / f"src-{name}.md").write_text(
            f"---\ntype: source\nsource_path: {source_rel}\nsha256: {sha}\nstatus: ingested\n---\n")
        for i in range(claims):
            (vault / "evidence/claims" / f"claim-{name}-{i:03d}.md").write_text(
                f"---\ntype: claim\nstatus: supported\nconfidence: medium\n---\n")

    def test_drifted_source_stales_its_claims(self, fabric_env):
        ingest, vault = fabric_env
        raw = vault / "evidence/raw/p/git/pr-1.md"
        raw.parent.mkdir(parents=True)
        raw.write_text("rev2")
        self._seed(ingest, vault, "p-git-pr-1-md", "a" * 64, "evidence/raw/p/git/pr-1.md")
        stamped = ingest.stale_mark_derived_claims(raw, "b" * 64)
        assert stamped == 1
        text = (vault / "evidence/claims/claim-p-git-pr-1-md-000.md").read_text()
        assert "status: contested" in text
        assert "stale_after:" in text

    def test_same_hash_is_a_noop(self, fabric_env):
        ingest, vault = fabric_env
        raw = vault / "evidence/raw/p/pr-1.md"
        raw.parent.mkdir(parents=True)
        raw.write_text("rev1")
        self._seed(ingest, vault, "p-pr-1-md", "a" * 64, "evidence/raw/p/pr-1.md")
        assert ingest.stale_mark_derived_claims(raw, "a" * 64) == 0
        assert "status: supported" in (
            vault / "evidence/claims/claim-p-pr-1-md-000.md").read_text()

    def test_different_path_never_stales(self, fabric_env):
        ingest, vault = fabric_env
        self._seed(ingest, vault, "other", "a" * 64, "evidence/raw/other/pr-9.md")
        raw = vault / "evidence/raw/p/pr-1.md"
        raw.parent.mkdir(parents=True)
        raw.write_text("rev2")
        assert ingest.stale_mark_derived_claims(raw, "b" * 64) == 0

    def test_already_stale_claim_not_restamped(self, fabric_env):
        ingest, vault = fabric_env
        raw = vault / "evidence/raw/p/pr-1.md"
        raw.parent.mkdir(parents=True)
        raw.write_text("rev2")
        self._seed(ingest, vault, "p-git-pr-1-md", "a" * 64, "evidence/raw/p/git/pr-1.md")
        cp = vault / "evidence/claims/claim-p-git-pr-1-md-000.md"
        cp.write_text("---\ntype: claim\nstale_after: 2026-01-01\nstatus: contested\n---\n")
        assert ingest.stale_mark_derived_claims(raw, "b" * 64) == 0

    def test_superseded_claim_touched_not_required(self, fabric_env):
        """superseded claims already carry a pointer; the stamp does not
        resurrect or double-mark them (stale_after absent → flips via the
        supported/proposed regex; superseded status has neither → untouched)."""
        ingest, vault = fabric_env
        raw = vault / "evidence/raw/p/pr-1.md"
        raw.parent.mkdir(parents=True)
        raw.write_text("rev2")
        self._seed(ingest, vault, "p-pr-1-md", "a" * 64, "evidence/raw/p/pr-1.md")
        cp = vault / "evidence/claims/claim-p-pr-1-md-000.md"
        cp.write_text("---\ntype: claim\nstatus: superseded\nsuperseded_by: [[claim-x]]\n---\n")
        assert ingest.stale_mark_derived_claims(raw, "b" * 64) == 0
        assert "superseded" in cp.read_text()

    def test_new_source_no_record_noop(self, fabric_env):
        ingest, vault = fabric_env
        raw = vault / "evidence/raw/p/pr-new.md"
        raw.parent.mkdir(parents=True)
        raw.write_text("rev1")
        assert ingest.stale_mark_derived_claims(raw, "c" * 64) == 0

class TestGhCommentsPagination:
    """Thread capture follows pagination — the old single per_page=20 page
    truncated every long review thread (exactly where the 'why' lives)."""

    def test_follows_pages_until_short_page(self, monkeypatch):
        pages = {1: [{"created_at": f"2026-09-{d:02d}T00:00:00Z", "user": {"login": f"u{d}"}, "body": "x"} for d in range(1, 16)],
                 2: [{"created_at": "2026-09-25T00:00:00Z", "user": {"login": "last"}, "body": "y"}]}
        # 15 < per_page(50) on page 2's short page... page1 has 15 too — make page 1 FULL (50 per_page):
        pages[1] = [{"created_at": f"2026-09-{(d % 28) + 1:02d}T00:00:00Z", "user": {"login": f"u{d}"}, "body": "x"} for d in range(1, 51)]
        def fake_gh(*a, expect_json=False):
            args = [str(x) for x in a]
            page = int(args[1].split("&page=")[1].split("&")[0])
            return pages.get(page)
        monkeypatch.setattr(capture_git, "gh", fake_gh)
        comments, truncated = capture_git.gh_comments("o/r", 5)
        assert len(comments) == 51 and not truncated
        assert comments[-1]["user"]["login"] == "last"

    def test_reports_truncation_at_cap(self, monkeypatch):
        monkeypatch.setattr(capture_git, "gh", lambda *a, expect_json=True: [
            {"created_at": "2026-09-01T00:00:00Z", "user": {"login": "u"}, "body": "x"}] * 50)
        comments, truncated = capture_git.gh_comments("o/r", 5)
        assert len(comments) == 500 and truncated  # 10 pages * 50


class TestUntilWindow:
    """--until bounds the window's fresh side (backfill slices)."""

    def test_client_filter_excludes_at_until(self, tmp_path, monkeypatch):
        searches = []
        def fake_gh(*a, expect_json=False):
            args = [str(x) for x in a]
            if "--search" in args:
                searches.append(args[args.index("--search") + 1])
                # PR search (merged:>=...) is the first call
                return [{"number": 1, "mergedAt": "2026-05-01T00:00:00Z", "title": "old", "body": "", "state": "MERGED", "labels": [], "url": ""},
                        {"number": 2, "mergedAt": "2026-07-01T00:00:00Z", "title": "newer", "body": "", "state": "MERGED", "labels": [], "url": ""}]
            return []
        monkeypatch.setattr(capture_git, "gh", fake_gh)
        monkeypatch.setattr(capture_git, "EVIDENCE_RAW", tmp_path / "raw")
        stats = capture_git.capture_github("p", "o/r", "6m", "2026-06-01", 30, False, dry_run=True)
        pr_search = next(s for s in searches if "merged:>=" in s)
        assert "merged:<2026-06-01" in pr_search  # server-side until bound

    def test_no_until_untouched_behavior(self, tmp_path, monkeypatch):
        def fake_gh(*a, expect_json=False):
            return [{"number": 1, "mergedAt": "2026-07-01T00:00:00Z", "title": "t", "body": "", "state": "MERGED", "labels": [], "url": ""}]
        monkeypatch.setattr(capture_git, "gh", fake_gh)
        monkeypatch.setattr(capture_git, "EVIDENCE_RAW", tmp_path / "raw")
        stats = capture_git.capture_github("p", "o/r", "1w", None, 30, False, dry_run=True)
        assert {k: v for k, v in stats.items() if k != "threads_truncated"} == \
            {"new": 1, "changed": 0, "unchanged": 0}


class TestIngestBudget:
    """Bulk ingest budget: capture is activity-bounded; ingest must be
    extraction-bounded too (1 LLM call per source — an unbounded wave after
    a big capture detonates N extractions in one run)."""

    def _ingest(self):
        import importlib.util as _ilu
        spec = _ilu.spec_from_file_location("ing_b", _SCRIPTS / "cmd/ingest.py")
        m = importlib.util.module_from_spec(spec)
        sys.modules["ing_b"] = m
        spec.loader.exec_module(m)
        return m

    def test_budget_default_zero_no_cap(self):
        m = self._ingest()
        import fabric_config
        v = fabric_config.get_tuning({}, "ingest", "budget", 0)
        assert v == 0

    def test_bulk_slice_defers_rest(self, tmp_path, monkeypatch):
        m = self._ingest()
        files = [tmp_path / f"f{i}.md" for i in range(5)]
        for i, f in enumerate(files):
            f.write_text(f"---\ntype: x\nsha256: {'0'*64}\n---\n{i}")
        monkeypatch.setattr(m, "find_changed_sources", lambda p: files)
        monkeypatch.setattr(m, "args_dry_run", True)
        processed = []
        monkeypatch.setattr(m, "ingest_source", lambda f, *a, **k: processed.append(f.name) or True)
        # patch argv path: call main() with --changed p --budget 2 --dry-run
        monkeypatch.setattr(sys, "argv", ["ingest.py", "--changed", "p", "--budget", "2", "--dry-run"])
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            m.main()
        out = buf.getvalue()
        assert "Budget 2: processing 2 of 5" in out
        assert len(processed) == 2
        assert "re-run to continue" in out
