"""Unit tests for context.py — task-aware context manifest compilation.

Run: python3 -m pytest tests/test_context.py -v
"""

import os
import sys
import importlib.util
import json
import subprocess
from pathlib import Path
from unittest import mock

REPO = Path(__file__).parent.parent


def _load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


ctx = _load_module("context", REPO / "scripts" / "cmd/context.py")


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
        (tmp_path / "corpus" / "patterns").mkdir(parents=True)
        (tmp_path / "corpus" / "patterns" / "pattern-x.md").write_text(
            "---\ntype: pattern\nid: pattern-x\nstatus: recommended\n---\n\nRotate tokens on refresh.\n"
        )
        env_root = tmp_path
        # context.py derives VAULT_ROOT from fabric_config; run isolated via
        # WIKI_FABRIC_DIR pointing at the temp fabric (which has corpus/).
        # Mirror the real scripts/ subdir layout so context.py's bootstrap
        # (which prepends scripts/, cmd/, lib/, ... to sys.path) resolves deps.
        import shutil as _sh
        _sh.copytree(REPO / "scripts", tmp_path / "scripts", dirs_exist_ok=True)
        # create corpus/ for CORPUS_ROOT resolution
        (tmp_path / "corpus").mkdir(exist_ok=True)
        out = subprocess.run(
            [sys.executable, str(tmp_path / "scripts" / "cmd/context.py"),
             "--task", "token rotation", "--format", "json"],
            capture_output=True, text=True,
            env={**os.environ, "WIKI_FABRIC_DIR": str(tmp_path)},
        )
        data = json.loads(out.stdout)
        assert set(data) >= {"task", "selected", "excluded", "precedence", "compiled"}
        assert data["precedence"] == ["project", "domain", "global"]
        assert any(s["stem"] == "pattern-x" and "match" in s["reason"] for s in data["selected"])

    def test_json_manifest_carries_schema_version(self, tmp_path):
        (tmp_path / "corpus" / "patterns").mkdir(parents=True)
        (tmp_path / "corpus" / "patterns" / "pattern-x.md").write_text(
            "---\ntype: pattern\nid: pattern-x\nstatus: recommended\n---\n\nRotate tokens on refresh.\n"
        )
        import shutil as _sh
        _sh.copytree(REPO / "scripts", tmp_path / "scripts", dirs_exist_ok=True)
        out = subprocess.run(
            [sys.executable, str(tmp_path / "scripts" / "cmd/context.py"),
             "--task", "token rotation", "--format", "json"],
            capture_output=True, text=True,
            env={**os.environ, "WIKI_FABRIC_DIR": str(tmp_path)},
        )
        assert json.loads(out.stdout)["$schema"] == "wiki-fabric/context-manifest-v1"

    def test_json_manifest_v1_shape_is_additive_only(self, tmp_path):
        """#23 contract: v1 fields are never removed or renamed — only added.
        This test pins the documented v1 field inventory (machine-contract.md).
        A failure here means a breaking change: bump the schema to -v2 instead
        of mutating v1."""
        fabric = tmp_path
        import shutil as _sh
        (fabric / "corpus" / "patterns").mkdir(parents=True)
        (fabric / "corpus" / "patterns" / "pattern-x.md").write_text(
            "---\ntype: pattern\nid: pattern-x\nstatus: recommended\n---\n\nRotate tokens on refresh.\n"
        )
        (fabric / "corpus" / "patterns" / "pattern-stale.md").write_text(
            "---\ntype: pattern\nid: pattern-stale\nstatus: superseded\n---\n\nold\n"
        )
        _sh.copytree(REPO / "scripts", fabric / "scripts", dirs_exist_ok=True)
        out = subprocess.run(
            [sys.executable, str(fabric / "scripts" / "cmd/context.py"),
             "--task", "token rotation", "--format", "json"],
            capture_output=True, text=True,
            env={**os.environ, "WIKI_FABRIC_DIR": str(fabric)},
        )
        data = json.loads(out.stdout)
        # documented v1 top-level inventory (machine-contract.md)
        required_top = {"$schema", "task", "paths", "project", "compiled",
                        "integrations", "selected", "excluded", "precedence"}
        missing = required_top - set(data)
        assert not missing, f"v1 breaking change — fields removed: {sorted(missing)}"
        assert set(data["integrations"]) >= {"graphify", "embeddings"}
        assert data["precedence"] == ["project", "domain", "global"]
        # selected item v1 inventory
        required_sel = {"id", "stem", "path", "type", "scope", "reason", "priority", "trust_tier"}
        for s in data["selected"]:
            miss = required_sel - set(s)
            assert not miss, f"v1 breaking change in selected item: {sorted(miss)}"
        # excluded item v1 inventory
        required_exc = {"stem", "path", "reason"}
        for e in data["excluded"]:
            miss = required_exc - set(e)
            assert not miss, f"v1 breaking change in excluded item: {sorted(miss)}"
        # documented optional fields, contractual-when-present
        optional_sel = {"warning", "stale_after", "title"}
        for s in data["selected"]:
            extra = set(s) - required_sel - optional_sel
            # new fields are allowed (additive), but if you add one, document it
            assert isinstance(extra, set)  # informational; additive is legal

    def test_markdown_has_precedence_section(self, tmp_path):
        out = subprocess.run(
            [sys.executable, str(REPO / "scripts" / "cmd/context.py"),
             "--task", "token rotation"],
            capture_output=True, text=True,
        )
        assert "## Precedence" in out.stdout
        assert "project decisions override" in out.stdout

    def test_zero_tokens_no_llm_call(self):
        # The script must not import any LLM client
        src = (REPO / "scripts" / "cmd/context.py").read_text()
        assert "openai" not in src and "anthropic" not in src


class TestReceipts:
    """--write-receipt persists the manifest as a receipt-v1 artifact:
    content-derived id (idempotent), namespace-partitioned, byte-stable,
    stdout untouched (path goes to stderr)."""

    def _fabric(self, tmp_path):
        import shutil as _sh
        (tmp_path / "corpus" / "patterns").mkdir(parents=True)
        (tmp_path / "corpus" / "patterns" / "pattern-x.md").write_text(
            "---\ntype: pattern\nid: pattern-x\nstatus: recommended\n---\n\nRotate tokens on refresh.\n"
        )
        _sh.copytree(REPO / "scripts", tmp_path / "scripts", dirs_exist_ok=True)
        return tmp_path

    def _run(self, fabric, *extra):
        return subprocess.run(
            [sys.executable, str(fabric / "scripts" / "cmd/context.py"),
             "--task", "token rotation", *extra],
            capture_output=True, text=True,
            env={**os.environ, "WIKI_FABRIC_DIR": str(fabric)},
        )

    def test_receipt_written_with_envelope(self, tmp_path):
        fabric = self._fabric(tmp_path)
        out = self._run(fabric, "--format", "json", "--write-receipt")
        assert out.returncode == 0
        receipts = list((fabric / "corpus" / "registry" / "receipts").glob("*.json"))
        assert len(receipts) == 1
        data = json.loads(receipts[0].read_text())
        assert data["$schema"] == "wiki-fabric/receipt-v1"
        assert data["receipt_id"] == receipts[0].stem
        assert data["namespace"] == "registry"
        assert data["manifest"] == "wiki-fabric/context-manifest-v1"
        assert "revision" in data  # corpus git sha, or null outside a repo
        assert {s["stem"] for s in data["selected"]} == {"pattern-x"}

    def test_receipt_path_on_stderr_stdout_untouched(self, tmp_path):
        fabric = self._fabric(tmp_path)
        plain = self._run(fabric, "--format", "json")
        with_r = self._run(fabric, "--format", "json", "--write-receipt")
        # stdout byte-identical with and without the flag
        assert plain.stdout == with_r.stdout
        assert "receipt" in with_r.stderr
        assert "receipt" not in plain.stderr

    def test_receipt_id_deterministic_idempotent(self, tmp_path):
        fabric = self._fabric(tmp_path)
        self._run(fabric, "--format", "json", "--write-receipt")
        self._run(fabric, "--format", "json", "--write-receipt")
        receipts = list((fabric / "corpus" / "registry" / "receipts").glob("*.json"))
        assert len(receipts) == 1, "same corpus+task must overwrite in place, not accumulate"

    def test_receipt_byte_identical_across_runs(self, tmp_path):
        fabric = self._fabric(tmp_path)
        self._run(fabric, "--format", "json", "--write-receipt")
        first = list((fabric / "corpus" / "registry" / "receipts").glob("*.json"))[0].read_bytes()
        self._run(fabric, "--format", "json", "--write-receipt")
        second = list((fabric / "corpus" / "registry" / "receipts").glob("*.json"))[0].read_bytes()
        assert first == second

    def test_receipt_partitioned_by_project_namespace(self, tmp_path):
        import shutil as _sh
        fabric = self._fabric(tmp_path)
        proj = fabric / "corpus" / "projects" / "auth"
        proj.mkdir(parents=True)
        (proj / "decisions").mkdir()
        (proj / "decisions" / "decision-rotation.md").write_text(
            "---\ntype: decision\nid: decision-rotation\nproject: auth\n---\n\nRotate tokens for oauth.\n"
        )
        out = subprocess.run(
            [sys.executable, str(fabric / "scripts" / "cmd/context.py"),
             "--task", "token rotation", "--project", "auth",
             "--format", "json", "--write-receipt"],
            capture_output=True, text=True,
            env={**os.environ, "WIKI_FABRIC_DIR": str(fabric)},
        )
        assert out.returncode == 0
        proj_receipts = list((proj / "receipts").glob("*.json"))
        assert len(proj_receipts) == 1, "pinned project receipt must live under projects/<p>/receipts/"
        assert not (fabric / "corpus" / "registry" / "receipts").exists()
        data = json.loads(proj_receipts[0].read_text())
        assert data["namespace"] == "projects/auth"

    def test_receipt_id_changes_when_manifest_changes(self, tmp_path):
        fabric = self._fabric(tmp_path)
        self._run(fabric, "--format", "json", "--write-receipt")
        first = list((fabric / "corpus" / "registry" / "receipts").glob("*.json"))[0].stem
        # a different task changes the selection => different payload => different id
        subprocess.run(
            [sys.executable, str(fabric / "scripts" / "cmd/context.py"),
             "--task", "unrelated billing webhook", "--format", "json", "--write-receipt"],
            capture_output=True, text=True,
            env={**os.environ, "WIKI_FABRIC_DIR": str(fabric)},
        )
        receipts = list((fabric / "corpus" / "registry" / "receipts").glob("*.json"))
        assert len(receipts) == 2, "different manifest payload must yield a different receipt id"

    def test_receipt_lint_rejects_bad_envelope(self, tmp_path):
        import importlib.util as _ilu
        fabric = self._fabric(tmp_path)
        self._run(fabric, "--format", "json", "--write-receipt")
        rpath = list((fabric / "corpus" / "registry" / "receipts").glob("*.json"))[0]
        spec = _ilu.spec_from_file_location('lint_mod', str(REPO / "scripts" / "cmd/lint.py"))
        lint = _ilu.module_from_spec(spec); spec.loader.exec_module(lint)

        def lint_errors():
            out = subprocess.run(
                [sys.executable, str(REPO / "scripts" / "cmd/lint.py"),
                 "--format", "json", str(fabric / "corpus")],
                capture_output=True, text=True,
            )
            report = json.loads(out.stdout)
            return [e["message"] for e in report["errors"] if e["code"] == "RECEIPT"]

        # good receipt: clean
        assert lint_errors() == []
        # bad $schema: flagged
        data = json.loads(rpath.read_text())
        data["$schema"] = "nope"
        rpath.write_text(json.dumps(data))
        assert any("$schema" in e for e in lint_errors())
        # missing required field: flagged
        data["$schema"] = "wiki-fabric/receipt-v1"
        del data["task"]
        rpath.write_text(json.dumps(data))
        assert any("'task'" in e for e in lint_errors())
        # filename != receipt_id: flagged
        data["task"] = "t"
        rpath2 = rpath.with_name("wrong-name.json")
        rpath2.write_text(json.dumps(data))
        rpath.unlink()
        assert any("receipt_id" in e for e in lint_errors())


class TestHumanLayerExcluded:
    """The generated wiki/syntheses prose is the human layer; the machine must
    consume only atoms (claims/patterns/decisions/concepts/...), never the
    paraphrased prose — otherwise the manifest re-feeds paraphrase + bloat."""

    def test_corpus_skips_wiki_and_syntheses(self, tmp_path):
        corpus = tmp_path / "corpus"
        (corpus / "patterns").mkdir(parents=True)
        (corpus / "patterns" / "pattern-x.md").write_text(
            "---\ntype: pattern\nstatus: recommended\n---\n\nrotate tokens on refresh\n")
        (corpus / "wiki" / "topics").mkdir(parents=True)
        (corpus / "wiki" / "topics" / "token-rotation.md").write_text(
            "---\ntype: wiki-article\n---\n\nToken rotation is a paraphrase of many claims.\n")
        (corpus / "syntheses").mkdir()
        (corpus / "syntheses" / "syn-1.md").write_text(
            "---\ntype: synthesis\n---\n\nA synthesis restates findings.\n")

        import fabric_config as fc
        with mock.patch.object(fc, "CORPUS_ROOT", corpus), \
             mock.patch.object(fc, "FABRIC_ROOT", corpus), \
             mock.patch.object(ctx, "CORPUS_ROOT", corpus), \
             mock.patch.object(ctx, "VAULT_ROOT", corpus):
            pages = ctx.load_corpus()
        posixs = [p["posix"] for p in pages]
        assert any("pattern-x" in p for p in posixs)
        assert not any("wiki" in p for p in posixs), "wiki prose leaked into machine corpus"
        assert not any("syntheses" in p for p in posixs), "synthesis prose leaked into machine corpus"


class TestQueryExcludesHumanLayer:
    """query.py's retrieval is another machine surface; it must also skip the
    generated wiki/syntheses prose so answers quote atoms, not paraphrase."""

    def test_load_pages_skips_wiki_and_syntheses(self, tmp_path):
        corpus = tmp_path / "corpus"
        (corpus / "evidence" / "claims").mkdir(parents=True)
        (corpus / "evidence" / "claims" / "claim-auth.md").write_text(
            "---\ntype: claim\nstatement: \"tokens rotate on refresh\"\n---\n\nbody\n")
        (corpus / "wiki" / "topics").mkdir(parents=True)
        (corpus / "wiki" / "topics" / "t.md").write_text(
            "---\ntype: wiki-article\n---\n\nparaphrase prose\n")
        (corpus / "syntheses").mkdir()
        (corpus / "syntheses" / "s.md").write_text("---\ntype: synthesis\n---\n\nparaphrase\n")

        import fabric_config as fc
        import importlib.util as _ilu
        qspec = _ilu.spec_from_file_location('query_mod', str(REPO / "scripts" / "cmd/query.py"))
        qmod = _ilu.module_from_spec(qspec); qspec.loader.exec_module(qmod)
        with mock.patch.object(fc, "CORPUS_ROOT", corpus), \
             mock.patch.object(fc, "FABRIC_ROOT", corpus), \
             mock.patch.object(qmod, "VAULT_ROOT", corpus):
            pages = qmod.load_pages()
        # query.py returns bodies loaded; filter by relative path
        rels = [str(p["rel"]) for p in pages]
        assert any("claim-auth" in r for r in rels)
        assert not any("wiki/" in r for r in rels), "wiki prose leaked into query retrieval"
        assert not any("syntheses/" in r for r in rels), "synthesis prose leaked into query retrieval"


class TestCitationGraph:
    """export-wiki emits the wiki's MACHINE value as registry/wiki-graph.json:
    topic/project -> claim edges + staleness tiers + claim provenance. Models
    consume these edges instead of re-reading the prose."""

    def test_emits_topic_claim_edges_and_provenance(self, tmp_path):
        import importlib.util as _ilu
        spec = _ilu.spec_from_file_location('export_wiki', str(REPO / "scripts" / "cmd/export-wiki.py"))
        ew = _ilu.module_from_spec(spec); spec.loader.exec_module(ew)
        claims_dir = tmp_path / "evidence" / "claims"
        claims_dir.mkdir(parents=True)
        (claims_dir / "claim-tok.md").write_text(
            "---\ntype: claim\nid: claim-tok\nstatement: \"t\"\n"
            "resource: \"[[src-auth]]\"\nreview_after: 2027-01-01\n---\n\nx\n")

        import fabric_config as fc
        with mock.patch.object(fc, "CORPUS_ROOT", tmp_path), \
             mock.patch.object(fc, "FABRIC_ROOT", tmp_path), \
             mock.patch.object(ew, "CORPUS_ROOT", tmp_path), \
             mock.patch.object(ew, "FABRIC_ROOT", tmp_path):
            topics = [{"slug": "token-rotation", "title": "Token Rotation",
                       "domain": "auth", "claims": ["claim-tok"]}]
            out = ew.emit_citation_graph(topics, ["proj-a"], dry_run=False)

        data = json.loads(Path(out).read_text())
        assert data["type"] == "wiki-graph"
        assert data["topics"][0]["claims"][0]["tier"] == "current"
        assert data["claim_sources"]["claim-tok"] == "src-auth"

    def test_dry_run_does_not_write(self, tmp_path):
        import importlib.util as _ilu
        spec = _ilu.spec_from_file_location('export_wiki', str(REPO / "scripts" / "cmd/export-wiki.py"))
        ew = _ilu.module_from_spec(spec); spec.loader.exec_module(ew)
        (tmp_path / "evidence" / "claims").mkdir(parents=True)
        import fabric_config as fc
        with mock.patch.object(fc, "CORPUS_ROOT", tmp_path), \
             mock.patch.object(fc, "FABRIC_ROOT", tmp_path), \
             mock.patch.object(ew, "CORPUS_ROOT", tmp_path), \
             mock.patch.object(ew, "FABRIC_ROOT", tmp_path):
            out = ew.emit_citation_graph([], [], dry_run=True)
        assert out == tmp_path / "registry" / "wiki-graph.json"
        assert not (tmp_path / "registry" / "wiki-graph.json").exists()


class TestMermaidRepair:
    """LangChain-OpenWiki-style diagram guarantee: a broken mermaid fence degrades
    to a text fence with a repair comment instead of shipping broken."""

    def _mod(self):
        import importlib.util as _ilu
        spec = _ilu.spec_from_file_location('export_wiki_repair', str(REPO / "scripts" / "cmd/export-wiki.py"))
        m = _ilu.module_from_spec(spec); spec.loader.exec_module(m)
        return m

    def test_valid_flowchart_and_sequence(self):
        m = self._mod()
        assert m._mermaid_valid("flowchart TD\n  A --> B\n  B --> C")
        assert m._mermaid_valid("sequenceDiagram\n  A->>B: hi\n  B-->>A: ok")

    def test_unbalanced_braces_invalid(self):
        m = self._mod()
        assert not m._mermaid_valid("flowchart TD\n  A --> B{\"x\"\n  B --> C")

    def test_repair_degrades_broken_fence(self):
        m = self._mod()
        art = "# X\n\n```mermaid\nflowchart TD\n  A --> B{\"oops\"\n```\n\nTail.\n"
        fixed, n = m._validate_and_repair_diagrams(art)
        assert n == 1
        assert "```text" in fixed
        assert m.MERMAID_REPAIR_COMMENT in fixed
        assert "```mermaid" not in fixed


class TestEnrichPage:
    """Every generated wiki page gets the same OpenWiki-style anatomy: provenance
    stamp, SUMMARY lead, Key Takeaways, and Sources backtrace."""

    def test_enrich_adds_anatomy(self, tmp_path):
        import importlib.util as _ilu
        spec = _ilu.spec_from_file_location('export_wiki_enrich', str(REPO / "scripts" / "cmd/export-wiki.py"))
        ew = _ilu.module_from_spec(spec); spec.loader.exec_module(ew)
        claims = tmp_path / "evidence" / "claims"
        claims.mkdir(parents=True)
        (claims / "claim-tok-rotation.md").write_text(
            "---\ntype: claim\nid: claim-tok-rotation\nstatement: \"tokens rotate on refresh\"\n"
            "resource: \"[[src-auth]]\"\nreview_after: 2027-01-01\n---\n\nx\n")
        page = tmp_path / "wiki" / "topics" / "token-rotation.md"
        page.parent.mkdir(parents=True)
        page.write_text(
            "---\ntype: wiki-article\ntitle: \"Token Rotation\"\n---\n\n"
            "# Token Rotation\n\nThe tokens rotate on refresh.\n\n"
            "## Evidence\n\n- [1] claim-tok-rotation — tokens rotate\n"
            "---\n[1] claim-tok-rotation\n")

        import fabric_config as fc
        with mock.patch.object(fc, "CORPUS_ROOT", tmp_path), \
             mock.patch.object(fc, "FABRIC_ROOT", tmp_path), \
             mock.patch.object(ew, "CORPUS_ROOT", tmp_path), \
             mock.patch.object(ew, "FABRIC_ROOT", tmp_path):
            ew._enrich_page(page, fc.get_config(), "mechanical")

        txt = page.read_text()
        assert "generated: { by:" in txt
        assert txt.count("SUMMARY:") == 1
        assert "## Key Takeaways" in txt
        assert "## Sources" in txt
        assert "[[src-auth]]" in txt  # source backtrace resolves


class TestVisualizer:
    """The human exploration surface for the generated wiki is Obsidian's native
    Graph view, which renders the [[wikilinks]] between pages. no separate HTML
    viewer is shipped."""

    def test_no_html_visualizer_emitted(self, tmp_path):
        import importlib.util as _ilu
        spec = _ilu.spec_from_file_location('export_wiki_viz', str(REPO / "scripts" / "cmd/export-wiki.py"))
        ew = _ilu.module_from_spec(spec); spec.loader.exec_module(ew)
        # the module must not ship a browser visualizer anymore
        src = Path(spec.origin).read_text()
        assert "view.html" not in src
        assert "_visualizer" not in src

class TestWikiRepair:
    """export-wiki repairs the human layer: reconcile stale output, synthesize
    concepts only when missing, rebuild the machine catalog."""

    def _mod(self):
        import importlib.util as _ilu
        spec = _ilu.spec_from_file_location('export_wiki_repair', str(REPO / "scripts" / "cmd/export-wiki.py"))
        m = _ilu.module_from_spec(spec); spec.loader.exec_module(m)
        return m

    def test_reconcile_counts_stale_without_deleting_on_dry_run(self, tmp_path):
        m = self._mod()
        (tmp_path / "vault" / "wiki" / "topics").mkdir(parents=True)
        (tmp_path / "vault" / "wiki" / "topics" / "stale-one.md").write_text("x")
        (tmp_path / "vault" / "wiki" / "topics" / "stale-two.md").write_text("x")
        import fabric_config as fc
        with mock.patch.object(fc, "get_vault_path", return_value=(tmp_path / "vault")), \
             mock.patch.object(m, "get_vault_path", return_value=(tmp_path / "vault")), \
             mock.patch.object(m, "_wiki_root", return_value=(tmp_path / "vault" / "wiki")):
            n = m._reconcile_wiki_dir("topics", dry_run=True)
        assert n == 2
        assert (tmp_path / "vault" / "wiki" / "topics" / "stale-one.md").exists()

    def test_reconcile_deletes_on_real_run(self, tmp_path):
        m = self._mod()
        (tmp_path / "vault" / "wiki" / "topics").mkdir(parents=True)
        (tmp_path / "vault" / "wiki" / "topics" / "stale.md").write_text("x")
        import fabric_config as fc
        with mock.patch.object(fc, "get_vault_path", return_value=(tmp_path / "vault")), \
             mock.patch.object(m, "get_vault_path", return_value=(tmp_path / "vault")), \
             mock.patch.object(m, "_wiki_root", return_value=(tmp_path / "vault" / "wiki")):
            n = m._reconcile_wiki_dir("topics", dry_run=False)
        assert n == 1
        assert not (tmp_path / "vault" / "wiki" / "topics" / "stale.md").exists()

    def test_concepts_exist_when_populated(self, tmp_path):
        m = self._mod()
        import fabric_config as fc
        # missing -> False
        with mock.patch.object(fc, "CORPUS_ROOT", tmp_path), \
             mock.patch.object(m, "CORPUS_ROOT", tmp_path):
            assert not m._concepts_exist()
        # populated -> True
        (tmp_path / "concepts").mkdir()
        (tmp_path / "concepts" / "concept-a.md").write_text("---\ntype: concept\n---\n")
        with mock.patch.object(fc, "CORPUS_ROOT", tmp_path), \
             mock.patch.object(m, "CORPUS_ROOT", tmp_path):
            assert m._concepts_exist()

    def test_rebuild_catalog_writes_reconciled(self, tmp_path):
        m = self._mod()
        (tmp_path / "registry").mkdir(parents=True)
        (tmp_path / "evidence" / "claims").mkdir(parents=True)
        (tmp_path / "evidence" / "claims" / "claim-a.md").write_text(
            "---\ntype: claim\nstatus: supported\n---\n\nx\n")
        import fabric_config as fc
        with mock.patch.object(fc, "CORPUS_ROOT", tmp_path), \
             mock.patch.object(fc, "FABRIC_ROOT", tmp_path), \
             mock.patch.object(m, "CORPUS_ROOT", tmp_path):
            ok = m._rebuild_catalog(dry_run=False)
        assert ok
        cat = json.loads((tmp_path / "registry" / "catalog.json").read_text())
        assert cat["total"] == 1
        assert cat["pages"][0]["type"] == "claim"


class TestWikiNetwork:
    """The wiki is a real network: pages carry Related wikilinks (human) and
    wiki-graph.json emits nodes[] + edges[] (machine). Edges are grounded in
    shared sources/claims — never invented."""

    def _mod(self):
        import importlib.util as _ilu
        spec = _ilu.spec_from_file_location('export_wiki_net', str(REPO / "scripts" / "cmd/export-wiki.py"))
        m = _ilu.module_from_spec(spec); spec.loader.exec_module(m)
        return m

    def test_compute_wiki_edges_topic_topic_via_shared_source(self, tmp_path):
        m = self._mod()
        claims = tmp_path / "evidence" / "claims"
        claims.mkdir(parents=True)
        # claims; t1 and t2 BOTH cite src-s1 and src-s2 => share 2 sources (>= min)
        for stem, src in [("a", "s1"), ("b", "s1"), ("c", "s2"), ("d", "s2")]:
            (claims / f"claim-{stem}.md").write_text(
                f"---\ntype: claim\nid: claim-{stem}\nstatement: \"{stem}\"\n"
                f"resource: \"[[src-{src}]]\"\n---\n\nx\n")
        import fabric_config as fc
        with mock.patch.object(fc, "CORPUS_ROOT", tmp_path), \
             mock.patch.object(fc, "FABRIC_ROOT", tmp_path), \
             mock.patch.object(m, "CORPUS_ROOT", tmp_path):
            topics = [
                {"slug": "t1", "title": "One", "domain": "d", "claims": ["claim-a", "claim-c"]},
                {"slug": "t2", "title": "Two", "domain": "d", "claims": ["claim-b", "claim-d"]},
            ]
            # t1 cites s1+s2; t2 cites s1+s2 -> shared sources = {s1,s2} (2)
            edges, index = m._compute_wiki_edges(topics, ["proj1"])
        t1 = [e["target"] for e in edges["t1"]]
        assert "t2" in t1
        assert index["t1"]["type"] == "topic"
        assert index["proj1"]["type"] == "project"

    def test_graph_emits_nodes_and_cross_edges(self, tmp_path):
        m = self._mod()
        claims = tmp_path / "evidence" / "claims"
        claims.mkdir(parents=True)
        # claim stem must match project prefix for the project edge
        (claims / "claim-proj-x-a.md").write_text(
            "---\ntype: claim\nid: claim-proj-x-a\nstatement: \"x\"\n"
            "resource: \"[[src-a]]\"\nreview_after: 2027-01-01\n---\n\nx\n")
        import fabric_config as fc
        with mock.patch.object(fc, "CORPUS_ROOT", tmp_path), \
             mock.patch.object(fc, "FABRIC_ROOT", tmp_path), \
             mock.patch.object(m, "CORPUS_ROOT", tmp_path):
            out = m.emit_citation_graph(
                [{"slug": "t", "title": "T", "domain": "d", "claims": ["claim-proj-x-a"]}],
                ["proj-x"], dry_run=False)
        data = json.loads(Path(out).read_text())
        assert "nodes" in data and "edges" in data
        types = {n["type"] for n in data["nodes"]}
        assert types >= {"topic", "claim", "source", "project"}
        # topic cites claim; claim traces to source; topic<->project via shared claim
        rels = {(e["source"], e["relation"], e["target"]) for e in data["edges"]}
        assert ("topic:t", "cites", "claim:claim-proj-x-a") in rels
        assert ("topic:t", "claim", "project:proj-x") in rels


class TestEnrichedAnatomy:
    """OpenWiki-style page anatomy: SUMMARY from prose (not headings), aliases in
    frontmatter, no duplicate Related, deterministic Definition fallback."""

    def _mod(self):
        import importlib.util as _ilu
        spec = _ilu.spec_from_file_location('export_wiki_anat', str(REPO / "scripts" / "cmd/export-wiki.py"))
        m = _ilu.module_from_spec(spec); spec.loader.exec_module(m)
        return m

    def test_summary_from_prose_not_heading(self, tmp_path):
        m = self._mod()
        page = tmp_path / "page.md"
        page.write_text(
            "---\ntype: wiki-article\ntitle: \"X\"\n---\n\n"
            "# X\n\n## Definition\n\nThis is the real opening prose.\n\nMore text.\n")
        import fabric_config as fc
        with mock.patch.object(fc, "get_config", return_value={"owner": "o", "llm": {"model": "m", "compiler_model": "c"}}):
            m._enrich_page(page, fc.get_config(), "mechanical")
        txt = page.read_text()
        assert "SUMMARY: This is the real opening prose." in txt
        assert "SUMMARY: Definition" not in txt

    def test_aliases_added_to_frontmatter(self, tmp_path):
        m = self._mod()
        page = tmp_path / "page.md"
        page.write_text("---\ntype: wiki-article\ntitle: \"Some Topic\"\n---\n\nbody\n")
        import fabric_config as fc
        with mock.patch.object(fc, "get_config", return_value={"owner": "o", "llm": {"model": "m", "compiler_model": "c"}}):
            m._enrich_page(page, fc.get_config(), "mechanical")
        txt = page.read_text()
        assert "aliases:" in txt
        assert '"Some Topic"' in txt
        assert '"some-topic"' in txt

    def test_no_duplicate_related(self, tmp_path):
        m = self._mod()
        claims = tmp_path / "evidence" / "claims"
        claims.mkdir(parents=True)
        (claims / "claim-a.md").write_text(
            "---\ntype: claim\nid: claim-a\nstatement: \"a\"\nresource: \"[[src-s1]]\"\n---\n\nx\n")
        page = tmp_path / "page.md"
        # LLM already emitted a Related section
        page.write_text("---\ntype: wiki-article\ntitle: \"T\"\n---\n\nbody\n\n## Related\n- [[other]]\n")
        import fabric_config as fc
        with mock.patch.object(fc, "CORPUS_ROOT", tmp_path), \
             mock.patch.object(fc, "FABRIC_ROOT", tmp_path), \
             mock.patch.object(m, "CORPUS_ROOT", tmp_path), \
             mock.patch.object(fc, "get_config", return_value={"owner": "o", "llm": {"model": "m", "compiler_model": "c"}}):
            m._enrich_page(page, fc.get_config(), "mechanical", related_links=[{"target": "z", "kind": "claim", "weight": 1}])
        txt = page.read_text()
        assert txt.count("## Related") == 1

    def test_aliases_resolve_in_wikilink(self, tmp_path):
        # aliases allow [[some-topic]] to resolve to the Some Topic page
        m = self._mod()
        page = tmp_path / "Some-Topic.md"
        page.write_text("---\ntype: wiki-article\ntitle: \"Some Topic\"\n---\n\nbody\n")
        import fabric_config as fc
        with mock.patch.object(fc, "get_config", return_value={"owner": "o", "llm": {"model": "m", "compiler_model": "c"}}):
            m._enrich_page(page, tmp if False else fc.get_config(), "mechanical")
        assert "some-topic" in page.read_text().lower()


class TestDomainHubs:
    """Domain hub pages: navigational grouping of topics by domain with a
    mermaid cluster, written to vault/wiki/domains/."""

    def _mod(self):
        import importlib.util as _ilu
        spec = _ilu.spec_from_file_location('export_wiki_hub', str(REPO / "scripts" / "cmd/export-wiki.py"))
        m = _ilu.module_from_spec(spec); spec.loader.exec_module(m)
        return m

    def test_generates_domain_hubs_grouped(self, tmp_path):
        m = self._mod()
        # seed two topic pages so the hub can read SUMMARYs
        wiki = tmp_path / "vault" / "wiki"
        (wiki / "topics").mkdir(parents=True)
        (wiki / "topics" / "tok.md").write_text(
            "---\ntype: wiki-article\ntitle: \"Token\"\n---\n\nSUMMARY: Rotate tokens.\n\n# Token\n\nbody\n")
        (wiki / "topics" / "mesh.md").write_text(
            "---\ntype: wiki-article\ntitle: \"Mesh\"\n---\n\nSUMMARY: Build voxel mesh.\n\n# Mesh\n\nbody\n")
        import fabric_config as fc
        with mock.patch.object(fc, "CORPUS_ROOT", tmp_path), \
             mock.patch.object(fc, "FABRIC_ROOT", tmp_path), \
             mock.patch.object(fc, "get_vault_path", return_value=(tmp_path / "vault")), \
             mock.patch.object(m, "CORPUS_ROOT", tmp_path), \
             mock.patch.object(m, "get_vault_path", return_value=(tmp_path / "vault")), \
             mock.patch.object(m, "_wiki_root", return_value=wiki):
            topics = [
                {"slug": "tok", "title": "Token", "domain": "agent-systems", "claims": ["c1"]},
                {"slug": "mesh", "title": "Mesh", "domain": "godot-systems", "claims": ["c2"]},
            ]
            hubs = m._generate_domain_hubs(topics, dry_run=False)
        assert len(hubs) == 2
        agent = (wiki / "domains" / "agent-systems.md")
        godot = (wiki / "domains" / "godot-systems.md")
        assert agent.exists() and godot.exists()
        agent_txt = agent.read_text()
        assert "[[tok]]" in agent_txt
        assert "Rotate tokens." in agent_txt  # SUMMARY pulled in
        assert "mermaid" in agent_txt and "flowchart TD" in agent_txt
        # godot hub must NOT contain the agent-systems topic
        assert "[[tok]]" not in godot.read_text()


class TestMermaidValidation:
    """Mermaid validation must accept sequence/state arrows (->>, -->, =>) that a
    protocol/lifecycle diagram genuinely uses, and still catch broken fences."""

    def _mod(self):
        import importlib.util as _ilu
        spec = _ilu.spec_from_file_location('export_wiki_mermaid', str(REPO / "scripts" / "cmd/export-wiki.py"))
        m = _ilu.module_from_spec(spec); spec.loader.exec_module(m)
        return m

    def test_sequence_diagram_valid(self):
        m = self._mod()
        assert m._mermaid_valid("sequenceDiagram\n    A->>B: hi\n    B-->>A: ok")
        assert m._mermaid_valid("sequenceDiagram\n    E->>S: dial\n    Note over S: listens\n    S->>E: cmd")

    def test_state_and_flow_valid(self):
        m = self._mod()
        assert m._mermaid_valid("stateDiagram-v2\n    [*] --> Pending\n    Pending --> Done")
        assert m._mermaid_valid("flowchart TD\n    A --> B")

    def test_unbalanced_still_caught(self):
        m = self._mod()
        assert not m._mermaid_valid("flowchart TD\n    A --> B{\"unbalanced")
