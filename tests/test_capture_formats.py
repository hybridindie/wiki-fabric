"""Unit tests for capture-chat harness readers (#113): codex + gemini formats.

Run: python3 -m pytest tests/test_capture_formats.py -v
"""

import json
import shutil
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


cc = _load("capture_chat_f", Path(__file__).parent.parent / "scripts/cmd/capture-chat.py")
FIXTURES = Path(__file__).parent / "fixtures" / "capture"


class TestCodexReader:
    def test_fixture_session_parses(self):
        root = "/tmp/proj"
        turns, files, sid, cwd, last_ms = cc._read_codex_session(FIXTURES / "codex-session.jsonl", root)
        assert sid == "ses-codex-fixture-1"
        assert cwd == "/tmp/proj"
        roles = [r for r, _ in turns]
        assert roles == ["user", "assistant", "assistant"]
        assert turns[0][1] == "Fix the retry loop in worker.py"
        assert "exponential backoff" in turns[-1][1]
        # read+edit file paths extracted; bash never parsed
        assert "/tmp/proj/worker.py" in files
        assert len(files) == 2
        assert last_ms is not None

    def test_capture_writes_markdown_with_frontmatter(self, tmp_path):
        raw_dir = tmp_path / "raw"
        raw_dir.mkdir()
        home = tmp_path / "home"
        sessions = home / ".codex" / "sessions" / "2026" / "09"
        sessions.mkdir(parents=True)
        shutil.copy(FIXTURES / "codex-session.jsonl", sessions / "s.jsonl")
        with mock.patch.object(cc.Path, "home", lambda: tmp_path / "home"):
            written = cc.capture_codex("proj", Path("/tmp/proj"), raw_dir,
                                       since_ms=0, limit=5, min_turns=1, dry_run=False)
        assert len(written) == 1
        text = written[0].read_text()
        assert "kind: chat-session" in text
        assert "harness: codex" in text
        assert 'session: "ses-codex-fixture-1"' in text
        assert "files_touched:" in text and "worker.py" in text
        assert "Fix the retry loop" in text

    def test_no_sessions_returns_empty(self, tmp_path):
        with mock.patch.object(cc.Path, "home", lambda: tmp_path / "missing-home"):
            assert cc.capture_codex("proj", Path("/tmp/proj"), tmp_path / "raw",
                                    0, 5, 1, False) == []

    def test_window_filter(self, tmp_path):
        sessions = tmp_path / "home" / ".codex" / "sessions"
        sessions.mkdir(parents=True)
        shutil.copy(FIXTURES / "codex-session.jsonl", sessions / "s.jsonl")
        with mock.patch.object(cc.Path, "home", lambda: tmp_path / "home"):
            # fixture timestamps are 2026-09-27T10:00Z — a since_ms of "now" excludes it
            import time
            written = cc.capture_codex("proj", Path("/tmp/proj"), tmp_path / "raw",
                                       since_ms=int(time.time() * 1000), limit=5,
                                       min_turns=1, dry_run=False)
        assert written == []


class TestGeminiReader:
    def test_fixture_session_parses(self):
        record = json.loads((FIXTURES / "gemini-session.jsonl").read_text())
        assert record["sessionId"].startswith("a1b2c3d4")
        msgs = record["messages"]
        user = [m for m in msgs if m["type"] == "user"]
        gemini = [m for m in msgs if m["type"] == "gemini"]
        assert len(user) == 1 and len(gemini) == 2
        touched = record["memoryScratchpad"]["touchedPaths"]
        assert "/tmp/proj/token.ts" in touched

    def test_capture_writes_markdown_with_frontmatter(self, tmp_path):
        home = tmp_path / "home"
        chats = home / ".gemini" / "tmp" / "hash123" / "chats"
        chats.mkdir(parents=True)
        shutil.copy(FIXTURES / "gemini-session.jsonl", chats / "session-1.jsonl")
        with mock.patch.object(cc.Path, "home", lambda: home):
            written = cc.capture_gemini("proj", Path("/tmp/proj"), tmp_path / "raw",
                                        since_ms=0, limit=5, min_turns=1, dry_run=False)
        assert len(written) == 1
        text = written[0].read_text()
        assert "kind: chat-session" in text
        assert "harness: gemini" in text
        assert 'session: "a1b2c3d4-e5f6-7890-abcd-ef1234567890"' in text
        # tool-call paths + scratchpad touchedPaths both feed files_touched
        assert "auth.ts" in text
        assert "token.ts" in text
        assert "Investigate the flaky auth test" in text

    def test_tool_call_paths_extracted(self, tmp_path):
        home = tmp_path / "home"
        chats = home / ".gemini" / "tmp" / "h" / "chats"
        chats.mkdir(parents=True)
        shutil.copy(FIXTURES / "gemini-session.jsonl", chats / "session-1.jsonl")
        with mock.patch.object(cc.Path, "home", lambda: home):
            written = cc.capture_gemini("proj", Path("/tmp/proj"), tmp_path / "raw",
                                        0, 5, 1, False)
        text = written[0].read_text()
        # both tool args and scratchpad paths, deduped
        assert text.count("auth.ts") >= 1
        assert "token.ts" in text


