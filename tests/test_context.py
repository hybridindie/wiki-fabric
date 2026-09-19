"""Unit tests for context.py — task-aware context manifest compilation.

Run: python3 -m pytest tests/test_context.py -v
"""

import sys
import importlib.util
import json
import subprocess
from pathlib import Path

REPO = Path(__file__).parent.parent


def _load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


ctx = _load_module("context", REPO / "scripts" / "context.py")


class _FakePage:
    def __init__(self, posix, fm, body):
        p = Path(posix)
        self.rel = p
        self.posix = posix
        self.stem = p.stem.lower()
        self.fm = fm
        self.body = body
        self.type = fm.get("type", "")
        scope = fm.get("scope") or (
            "domain" if posix.startswith("domains/")
            else "project" if posix.startswith("projects/")
            else "global"
        )
        self.scope = scope


def _page(posix, fm, body):
    p = Path(posix)
    return {
        "path": p,
        "rel": p,
        "posix": posix,
        "stem": p.stem.lower(),
        "fm": fm,
        "body": body,
        "type": fm.get("type", ""),
        "scope": fm.get("scope") or (
            "domain" if posix.startswith("domains/")
            else "project" if posix.startswith("projects/")
            else "global"
        ),
    }


class TestSelection:
    def test_superseded_excluded(self):
        pages = [_page("patterns/pattern-old.md",
                       {"type": "pattern", "status": "superseded"}, "token rotation content")]
        selected, excluded = ctx.select_context(pages, "token rotation", [], None, __import__("datetime").date.today())
        assert not selected
        assert any(e["reason"] == "superseded" for e in excluded)

    def test_deprecated_excluded(self):
        pages = [_page("patterns/pattern-d.md",
                       {"type": "pattern", "status": "deprecated"}, "token rotation content")]
        selected, excluded = ctx.select_context(pages, "token rotation", [], None, __import__("datetime").date.today())
        assert not selected
        assert any(e["reason"] == "deprecated" for e in excluded)

    def test_stale_pattern_excluded_with_reason(self):
        import datetime
        pages = [_page("patterns/pattern-stale.md",
                       {"type": "pattern", "status": "recommended", "review_after": "2026-01-01"},
                       "token rotation content")]
        selected, excluded = ctx.select_context(pages, "token rotation", [], None, datetime.date(2026, 9, 13))
        assert not selected
        assert any("stale" in e["reason"] and "overdue" in e["reason"] for e in excluded)

    def test_stale_decision_kept_but_warned(self):
        import datetime
        # decisions are never staleness-excluded (project constraints are binding)
        pages = [_page("projects/p/decisions/d.md",
                       {"type": "decision", "project": "p", "review_after": "2026-01-01"},
                       "token rotation content")]
        selected, excluded = ctx.select_context(pages, "token rotation", [], None, datetime.date(2026, 9, 13))
        assert selected and selected[0].get("warning")

    def test_project_decision_selected_with_reason(self):
        import datetime
        pages = [_page("projects/auth/decisions/d.md",
                       {"type": "decision", "project": "auth"}, "rotating refresh tokens for oauth")]
        selected, _ = ctx.select_context(pages, "Add token rotation to the auth service", [], None, datetime.date.today())
        assert any(s["priority"] == "P1-project" and "task text match" in s["reason"] for s in selected)

    def test_project_pin_matches_namespace(self):
        import datetime
        pages = [_page("projects/auth/decisions/d.md",
                       {"type": "decision", "project": "auth"}, "unrelated body")]
        selected, _ = ctx.select_context(pages, "some task", [], "auth", datetime.date.today())
        assert any("project match: auth" in s["reason"] for s in selected)

    def test_domain_match(self):
        import datetime
        pages = [_page("domains/oauth/concepts/c.md",
                       {"type": "concept", "scope": "domain"}, "token rotation best practice")]
        selected, _ = ctx.select_context(pages, "OAuth token rotation", [], None, datetime.date.today())
        assert any(s["priority"] == "P2-domain" for s in selected)

    def test_global_pattern_match(self):
        import datetime
        pages = [_page("patterns/pattern-serial-writes.md",
                       {"type": "pattern", "status": "recommended"}, "serialize writes on single writer systems")]
        selected, _ = ctx.select_context(pages, "writes serialize", [], None, datetime.date.today())
        assert any(s["priority"] == "P3-global" for s in selected)

    def test_precedence_order_project_before_domain_before_global(self):
        import datetime
        pages = [
            _page("patterns/p-x.md", {"type": "pattern", "status": "recommended"}, "token rotation applies"),
            _page("domains/d/concepts/c.md", {"type": "concept", "scope": "domain"}, "token rotation concept"),
            _page("projects/auth/decisions/d.md", {"type": "decision", "project": "auth"}, "token rotation decision"),
        ]
        selected, _ = ctx.select_context(pages, "token rotation", [], "auth", datetime.date.today())
        priorities = [s["priority"] for s in selected]
        assert priorities == sorted(priorities, key=lambda p: {"P1-project": 0, "P2-domain": 1, "P3-global": 2}[p])

    def test_claims_require_strong_task_match(self):
        import datetime
        # claims are now direct task evidence when they match the task; an
        # unrelated claim must not be selected
        pages = [_page("evidence/claims/claim-x.md",
                       {"type": "claim", "id": "claim-x", "status": "supported"}, "billing webhook retry backoff policy")]
        selected, _ = ctx.select_context(pages, "token rotation oauth", [], None, datetime.date.today())
        assert not any(s["type"] == "claim" for s in selected)

    def test_matching_claim_selected_as_task_evidence(self):
        import datetime
        pages = [_page("evidence/claims/claim-sse.md",
                       {"type": "claim", "id": "claim-sse", "status": "supported"},
                       "EventSourceResponse sends an empty body for non-generator endpoints")]
        selected, _ = ctx.select_context(pages, "Fix empty body in EventSourceResponse", [], None, datetime.date.today())
        assert any(s["type"] == "claim" and s["priority"] == "P1-project" for s in selected)

    def test_max_respected(self):
        import datetime
        pages = [_page(f"patterns/p-{i}.md", {"type": "pattern", "status": "recommended"},
                       f"token rotation body {i} with many words") for i in range(5)]
        selected, excluded = ctx.select_context(pages, "token rotation", [], None, datetime.date.today(), max_items=2)
        assert len(selected) == 2
        assert any(e["reason"].startswith("beyond --max") for e in excluded)


class TestOutputs:
    def test_json_manifest_shape(self, tmp_path):
        (tmp_path / "patterns").mkdir()
        (tmp_path / "patterns" / "pattern-x.md").write_text(
            "---\ntype: pattern\nid: pattern-x\nstatus: recommended\n---\n\nRotate tokens on refresh.\n"
        )
        env_root = tmp_path
        # context.py derives VAULT_ROOT from its own parent; run with cwd trick via subprocess env
        src = (REPO / "scripts" / "context.py").read_text()
        (tmp_path / "scripts").mkdir()
        (tmp_path / "scripts" / "context.py").write_text(src)
        # context.py imports fabric_config + wf_common from its own dir
        for dep in ("fabric_config.py", "wf_common.py"):
            (tmp_path / "scripts" / dep).write_text(
                (REPO / "scripts" / dep).read_text())
        out = subprocess.run(
            [sys.executable, str(tmp_path / "scripts" / "context.py"),
             "--task", "token rotation", "--format", "json"],
            capture_output=True, text=True,
        )
        data = json.loads(out.stdout)
        assert set(data) >= {"task", "selected", "excluded", "precedence", "compiled"}
        assert data["precedence"] == ["project", "domain", "global"]
        assert any(s["stem"] == "pattern-x" and "match" in s["reason"] for s in data["selected"])

    def test_markdown_has_precedence_section(self, tmp_path):
        out = subprocess.run(
            [sys.executable, str(REPO / "scripts" / "context.py"),
             "--task", "token rotation"],
            capture_output=True, text=True,
        )
        assert "## Precedence" in out.stdout
        assert "project decisions override" in out.stdout

    def test_zero_tokens_no_llm_call(self):
        # The script must not import any LLM client
        src = (REPO / "scripts" / "context.py").read_text()
        assert "openai" not in src and "anthropic" not in src