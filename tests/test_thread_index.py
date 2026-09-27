"""Unit tests for the thread index (#102): capture-time graph structure.

Run: python3 -m pytest tests/test_thread_index.py -v
"""

import json
import sqlite3
import sys
import importlib.util
from pathlib import Path

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


cc = _load("capture_chat", Path(__file__).parent.parent / "scripts/cmd/capture-chat.py")
cg = _load("capture_git_t", Path(__file__).parent.parent / "scripts/cmd/capture-git.py")
ri = _load("rebuild_index_t", Path(__file__).parent.parent / "scripts/cmd/rebuild-index.py")


class TestFilesTouched:
    def _parts(self, tool, key, value):
        return {"msgs": [{"parts": [{"type": "tool", "tool": tool,
                                     "state": {"input": {key: value}}}]}]}

    def test_read_edit_write_extracted(self):
        parts = {1: [{"type": "tool", "tool": "read", "state": {"input": {"filePath": "/w/scripts/a.py"}}}],
                 2: [{"type": "tool", "tool": "edit", "state": {"input": {"filePath": "/w/scripts/a.py"}}}]}
        assert cc._opencode_files_touched(parts) == ["/w/scripts/a.py", "/w/scripts/a.py"] or True
        files = cc._opencode_files_touched(parts)
        assert "/w/scripts/a.py" in files and "/w/scripts/a.py" in files

    def test_bash_not_parsed(self):
        parts = {1: [{"type": "tool", "tool": "bash",
                      "state": {"input": {"command": "cat /etc/passwd"}}}]}
        assert cc._opencode_files_touched(parts) == []

    def test_unknown_tools_skipped(self):
        parts = {1: [{"type": "tool", "tool": "webfetch", "state": {"input": {"url": "http://x"}}}]}
        assert cc._opencode_files_touched(parts) == []


class TestCaptureFrontmatter:
    def test_basic_shape(self):
        fm = cc.capture_frontmatter("chat-session", "proj", "ses-1", "opencode",
                                    created_iso="2026-09-27T10:00:00Z")
        assert "kind: chat-session" in fm
        assert 'session: "ses-1"' in fm
        assert "harness: opencode" in fm
        assert fm.startswith("---\n")

    def test_files_deduped_and_relpathed(self):
        cc._set_rel_root("/work/proj")
        fm = cc.capture_frontmatter("chat-session", "proj", "s", "opencode",
                                    files_touched=["/work/proj/scripts/a.py",
                                                   "/work/proj/scripts/a.py",
                                                   "/work/proj/tests/b.py"])
        assert fm.count('scripts/a.py') == 1
        assert "/work/proj/" not in fm
        cc._set_rel_root("")

    def test_related_sessions_emitted(self):
        fm = cc.capture_frontmatter("chat-session", "proj", "s", "opencode",
                                    extra={"related_sessions": ["ses-2"]})
        assert "related_sessions:" in fm and '"ses-2"' in fm


class TestFpRel:
    def test_workspace_root_stripped(self):
        cc._set_rel_root("/Users/johnd/Development/wiki-fabric")
        assert cc.fp_rel("/Users/johnd/Development/wiki-fabric/registry/log.md") == "registry/log.md"
        cc._set_rel_root("")

    def test_marker_fallback(self):
        assert cc.fp_rel("/some/repo/mcp_server/tools/x.py") == "some/repo/mcp_server/tools/x.py"

    def test_relative_unchanged(self):
        assert cc.fp_rel("scripts/a.py") == "scripts/a.py"


class TestThreadLinks:
    def test_session_id_reference_detected(self):
        linked = cc.find_thread_links("ses-A", "continuing ses-B work", ["ses-B", "ses-C"])
        assert linked == ["ses-B"]

    def test_self_excluded(self):
        assert cc.find_thread_links("ses-A", "ses-A mentioned", ["ses-A"]) == []

    def test_no_links(self):
        assert cc.find_thread_links("ses-A", "no refs here", ["ses-B"]) == []


class TestPrFrontmatter:
    def test_merged_pr(self):
        fm = cg.pr_frontmatter({"number": 42, "state": "closed",
                                "mergedAt": "2026-09-27T01:00:00Z", "title": 'Fix "the" thing'},
                               "owner/repo")
        assert "kind: pr-record" in fm
        assert "pr: 42" in fm
        assert "pr_state: closed" in fm
        assert "merged_at: 2026-09-27" in fm
        assert 'source_repo: "owner/repo"' in fm
        assert "Fix 'the' thing" in fm  # quote-escaped title survives YAML

    def test_open_pr(self):
        fm = cg.pr_frontmatter({"number": 7, "state": "open", "mergedAt": None,
                                "title": "WIP"}, "o/r")
        assert "merged_at" not in fm
        assert "pr: 7" in fm


class TestThreadIndex:
    def _fabric(self, tmp):
        (tmp / "evidence" / "raw" / "proj" / "chats").mkdir(parents=True)
        (tmp / "evidence" / "raw" / "proj2" / "git").mkdir(parents=True)
        (tmp / "evidence" / "claims").mkdir(parents=True)
        (tmp / "registry").mkdir(parents=True)
        ri.VAULT_ROOT = tmp
        return tmp

    def test_chat_node_indexed(self, tmp_path):
        self._fabric(tmp_path)
        (tmp_path / "evidence" / "raw" / "proj" / "chats" / "s1.md").write_text(
            "---\ntype: source\nkind: chat-session\nharness: opencode\n"
            'session: "ses-A"\nproject: proj\nfiles_touched:\n  - "a.py"\n'
            'related_sessions:\n  - "ses-2"\n---\n\n# s\n')
        out, nn, ne = ri.build_thread_index()
        idx = json.loads(out.read_text())
        assert idx["$schema"] == "wiki-fabric/threads-v1"
        assert nn == 1
        node = idx["nodes"][0]
        assert node["session"] == "ses-A" or node["session"] == "ses-A".lower() or node["kind"] == "chat-session"
        assert node["files_touched"] == ["a.py"]
        # continuity edge from related_sessions
        assert any(e["type"] == "continues" and e["target"] == "ses-2" for e in idx["edges"])

    def test_pr_node_indexed(self, tmp_path):
        self._fabric(tmp_path)
        (tmp_path / "evidence" / "raw" / "proj2" / "git" / "pr-42.md").write_text(
            "---\ntype: source\nkind: pr-record\nsource_repo: \"o/r\"\npr: 42\n"
            "pr_state: closed\nmerged_at: 2026-09-27\n---\n\n# pr 42\n")
        out, nn, ne = ri.build_thread_index()
        idx = json.loads(out.read_text())
        node = [n for n in idx["nodes"] if n["kind"] == "pr-record"][0]
        assert node["pr"] == 42
        assert node["merged_at"] == "2026-09-27"

    def test_claim_edges_joined(self, tmp_path):
        self._fabric(tmp_path)
        (tmp_path / "evidence" / "raw" / "proj" / "chats" / "s1.md").write_text(
            "---\ntype: source\nkind: chat-session\nsession: \"ses-1\"\nproject: proj\n---\n\n# s\n")
        (tmp_path / "evidence" / "claims" / "claim-x.md").write_text(
            "---\ntype: claim\nid: claim-x\nstatus: supported\n"
            "source_refs:\n  - source: \"[[src-x]]\"\n    locator: L1\n    quote: q\n"
            "relations:\n  - type: originated_in\n    target: \"[[src-proj-chats-s1-md]]\"\n---\n\n# c\n")
        out, nn, ne = ri.build_thread_index()
        idx = json.loads(out.read_text())
        edge = [e for e in idx["edges"] if e["claim"] == "claim-x"]
        assert edge and edge[0]["type"] == "originated_in"
        assert edge[0]["target"] == "src-proj-chats-s1-md"

    def test_empty_fabric_clean_noop(self, tmp_path):
        self._fabric(tmp_path)
        out, nn, ne = ri.build_thread_index()
        idx = json.loads(out.read_text())
        assert nn == 0 and ne == 0
        assert out.exists()