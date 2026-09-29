"""main()-level tests for the mine verbs (#150).

The mine-chats break: main() reached `return 0` without ever invoking the
mining loop (the loop sat after propose_candidates' return — unreachable).
test_mine_inbox covers propose_candidates directly; nothing covered main().
These tests drive main() end-to-end with a seeded transcript.
"""

import sys
import importlib.util
from pathlib import Path
from unittest import mock

import sys, pathlib as _p
_SCRIPTS = (_p.Path(__file__).resolve().parent.parent / "scripts").resolve()
for _rel in ("cmd", "lib", "eval", "harness"):
    if str(_SCRIPTS / _rel) not in sys.path:
        sys.path.insert(0, str(_SCRIPTS / _rel))


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


mc = _load("mine_chats_main", Path(__file__).parent.parent / "scripts/cmd/mine-chats.py")


def _seed_corpus(tmp_path):
    """A corpus with one captured chat transcript of durable content."""
    (tmp_path / "evidence" / "raw" / "seedproj" / "chats").mkdir(parents=True)
    (tmp_path / "patterns").mkdir(exist_ok=True)
    (tmp_path / "evidence" / "insights").mkdir(parents=True, exist_ok=True)
    transcript = tmp_path / "evidence" / "raw" / "seedproj" / "chats" / "chat-2026-09-29-demo.md"
    transcript.write_text(
        "# Chat session demo\n\n"
        "- The build cache must be invalidated after writes because stale reads "
        "served stale data; the rule is idempotent rebuilds, and the system "
        "does not tolerate incremental patches. CI was green at 3pm.\n"
        "- Pattern: serialize writes to single-writer systems because parallel "
        "writes to one queue corrupt ordering. Never write in parallel here.\n")
    return tmp_path


def _run_main(monkeypatch, tmp_path, *argv):
    monkeypatch.setattr(mc, "CORPUS_ROOT", tmp_path, raising=False)
    monkeypatch.setattr(sys, "argv", ["mine-chats.py", "seedproj", *argv])
    _seed_corpus(tmp_path)
    return mc.main()


class TestMineChatsMain:
    def test_main_mines_transcripts(self, tmp_path, monkeypatch, capsys):
        """The shipped break: main() reached return 0 without invoking the
        mining loop — here the loop must run (durable takeaways reported)."""
        rc = _run_main(monkeypatch, tmp_path, "--dry-run")
        assert rc == 0
        out = capsys.readouterr().out
        assert "Mining 1 chat transcript(s)" in out
        # dry-run: no page, but the mining loop demonstrably ran
        assert "1 durable takeaway" in out

    def test_main_writes_insight_page(self, tmp_path, monkeypatch, capsys):
        rc = _run_main(monkeypatch, tmp_path)
        assert rc == 0
        insights = list((tmp_path / "evidence" / "insights").glob("insight-*.md"))
        assert insights, "main() must write the insight page (the loop must run)"
        assert "Durable takeaways" in insights[0].read_text()
        out = capsys.readouterr().out
        assert "transient-filtered" in out

    def test_main_propose_reports_staging(self, tmp_path, monkeypatch, capsys):
        """--propose reaches the staging path and reports the count. The
        heuristic classifier yields kind=durable|maybe; only pattern/anti-
        pattern KINDS stage (LLM mode). Direct staging of pattern-kind
        takeaways is covered in test_mine_inbox (propose_candidates)."""
        rc = _run_main(monkeypatch, tmp_path, "--propose")
        assert rc == 0
        out = capsys.readouterr().out
        # the loop ran with --propose and reported a stage count (0 for
        # heuristic kinds — the filter, not a silent no-op)
        assert "Pattern candidates staged: 0" in out
        inbox = tmp_path / "patterns" / "_inbox"
        assert inbox.exists() or "--propose" in out

    def test_main_no_chats_exits_clean(self, tmp_path, monkeypatch, capsys):
        monkeypatch.setattr(mc, "CORPUS_ROOT", tmp_path, raising=False)
        monkeypatch.setattr(sys, "argv", ["mine-chats.py", "seedproj"])
        (tmp_path / "evidence").mkdir()  # no chats dir
        rc = mc.main()
        assert rc == 2  # capture hint, not a silent success
        assert "No chats captured" in capsys.readouterr().err


class TestMinePromotionsMain:
    """The same break class, other mine verbs (#150 audit): mine promotions'
    main() must reach clustering from argv — driven with --min-projects
    high enough that a tiny seed yields no clusters (no writes)."""

    def test_main_reaches_clustering(self, tmp_path, monkeypatch, capsys):
        mp = _load("mine_promotions_main",
                   Path(__file__).parent.parent / "scripts/cmd/mine-promotions.py")
        monkeypatch.setattr(mp, "CORPUS_ROOT", tmp_path, raising=False)
        monkeypatch.setattr(mp, "VAULT_ROOT", tmp_path, raising=False)
        (tmp_path / "evidence").mkdir(exist_ok=True)
        monkeypatch.setattr(sys, "argv",
                            ["mine-promotions.py", "--min-projects", "99", "--dry-run"])
        rc = mp.main()
        assert rc in (0, None)
        out = capsys.readouterr().out
        assert "Found 0 experience events" in out
        assert "Mining promotions" in out


if __name__ == "__main__":
    import unittest
    unittest.main()