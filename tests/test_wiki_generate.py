"""Living-wiki S2 (#144): the wiki-generation bookkeeper — durable queue,
claim reconciliation, citation validation, MCP tool wiring."""
import json
import importlib.util
import sys
from pathlib import Path

REPO = Path(__file__).parent.parent
_SCRIPTS = (REPO / "scripts").resolve()
for _d in (_SCRIPTS / "cmd", _SCRIPTS / "lib", _SCRIPTS):
    if str(_d) not in sys.path:
        sys.path.insert(0, str(_d))

import wiki_generate as WG


def _fabric(tmp):
    """Temp corpus with one concept (4 claims) + its claims."""
    import fabric_config
    corpus = tmp / "corpus"
    claims_dir = corpus / "evidence" / "claims"
    claims_dir.mkdir(parents=True)
    concept = corpus / "concepts"
    concept.mkdir(parents=True)
    claim_ids = [f"claim-p-doc-md-{i:03d}" for i in range(4)]
    for i, cid in enumerate(claim_ids):
        (claims_dir / f"{cid}.md").write_text(
            f"---\ntype: claim\nid: {cid}\nstatement: \"Claim {i} text.\"\n---\n\nb\n")
    (concept / "concept-token-rotation.md").write_text(
        "---\ntype: concept\ntitle: \"Token Rotation\"\n"
        "claims:\n" + "".join(f'  - "[[{c}]]"\n' for c in claim_ids) +
        "---\n\n# Token Rotation\n\nbody\n")
    # claim statements for citations
    return corpus


class TestLifecycle:
    def test_begin_builds_outline_and_checkpoints(self, tmp_path, monkeypatch):
        monkeypatch.setattr(WG, "CORPUS_ROOT", tmp_path / "corpus")
        _fabric(tmp := tmp_path)
        monkeypatch.setattr(WG, "CORPUS_ROOT", tmp_path / "corpus", raising=False)
        import fabric_config
        monkeypatch.setattr(fabric_config, "CORPUS_ROOT", tmp_path / "corpus", raising=False)
        rc = WG.cmd_begin(_args(project="p", task="t", min_claims=2))
        assert rc == 0
        runs = list((tmp_path / "corpus" / "evidence" / "traces" / "wiki-runs").glob("run-*/.run.json"))
        assert len(runs) == 1
        r = _json(runs[0])
        assert r["total"] == 1 and r["pages"][0]["claims"]

    def test_begin_resumes_open_run(self, tmp_path, monkeypatch, capsys):
        monkeypatch.setattr(WG, "CORPUS_ROOT", tmp_path / "corpus", raising=False)
        import fabric_config
        monkeypatch.setattr(fabric_config, "CORPUS_ROOT", tmp_path / "corpus", raising=False)
        _fabric(tmp_path)
        WG.cmd_begin(_args(project="p", task="t", min_claims=2))
        capsys.readouterr()
        WG.cmd_begin(_args(project="p", task="t", min_claims=2))
        out = capsys.readouterr().out
        assert "Resuming" in out

    def test_next_emits_pending_job(self, tmp_path, monkeypatch):
        _seed(tmp_path, monkeypatch, begun=True)
        import io, contextlib
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            WG.cmd_next(_args())
        job = json.loads(buf.getvalue())
        assert job["claims"] and job["citation_rule"].startswith("every assigned")

    def test_submit_rejects_zero_citations(self, tmp_path, monkeypatch, capsys):
        _seed(tmp_path, monkeypatch, begun=True)
        bad = tmp_path / "bad.md"
        bad.write_text("# Page\n\nprose with no citations\n")
        import contextlib, io
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            rc = WG.cmd_submit(_args(page="token-rotation", file=str(bad)))
        assert rc == 1
        assert "REJECTED" in err.getvalue()

    def test_submit_accepts_cited_page_durable(self, tmp_path, monkeypatch):
        run_dir, run = _seed(tmp_path, monkeypatch, begun=True)
        claims = run["pages"][0]["claims"]
        good = tmp_path / "good.md"
        body = "# Page\n\n" + " ".join(f"[[{c}]]" for c in claims)
        good.write_text(body)
        rc = WG.cmd_submit(_args(page="token-rotation", file=str(good)))
        assert rc == 0
        _, run2 = WG._open_run()
        page = run2["pages"][0]
        assert page["status"] == "done" and page["verified"]["citations"] == "ok"
        staged = tmp_path / "wiki" / "staged" / run_dir.name / "token-rotation.md"
        assert staged.exists()

    def test_resubmit_skips_done_page(self, tmp_path, monkeypatch, capsys):
        run_dir, run = _seed(tmp_path, monkeypatch, begun=True, done_first=True)
        import contextlib, io
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            WG.cmd_submit(_args(page="token-rotation", file=str(tmp_path / "x.md")))
        assert "already complete" in out.getvalue()

    def test_finish_refuses_when_pending(self, tmp_path, monkeypatch, capsys):
        _seed(tmp_path, monkeypatch, begun=True)
        import contextlib, io
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            rc = WG.cmd_finish(_args())
        assert rc == 1 and "REFUSED" in err.getvalue()

    def test_finish_ok_when_all_durable(self, tmp_path, monkeypatch, capsys):
        run_dir, run = _seed(tmp_path, monkeypatch, begun=True, done_all=True)
        import contextlib, io
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            rc = WG.cmd_finish(_args())
        assert rc == 0 and "finished" in out.getvalue()

    def test_reconcile_deltas(self):
        claims = ["claim-a", "claim-b", "claim-c"]
        final, applied, errors = WG.reconcile(claims, {"retract": ["claim-b"], "add": ["claim-d"]})
        assert "claim-b" not in final and "claim-d" in final
        assert applied["retracted"] == ["claim-b"] and not errors

    def test_retract_unassigned_rejected(self):
        final, applied, errors = WG.reconcile(["claim-a"], {"retract": ["claim-zzz"]})
        assert errors and final is None


# ---- helpers ----

def _args(**kw):
    import argparse
    return argparse.Namespace(**kw)


def _json(p):
    return json.loads(Path(p).read_text())


def _seed(tmp_path, monkeypatch, begun=False, done_first=False, done_all=False):
    import fabric_config
    corpus = _fabric(tmp_path)
    monkeypatch.setattr(WG, "CORPUS_ROOT", corpus, raising=False)
    monkeypatch.setattr(fabric_config, "CORPUS_ROOT", corpus, raising=False)
    monkeypatch.setattr(WG, "_wiki_root", lambda: tmp_path / "wiki", raising=False)
    if begun:
        WG.cmd_begin(_args(project="p", task="t", min_claims=2))
        run_dir, run = WG._open_run()
        if done_all:
            for p in run["pages"]:
                p["status"] = "done"
            WG._checkpoint(run_dir, run)
        elif done_first:
            run["pages"][0]["status"] = "done"
            WG._checkpoint(run_dir, run)
        return run_dir, run
    return None, None


def test_inspect_page_claims(tmp_path, monkeypatch, capsys):
    run_dir, run = _seed(tmp_path, monkeypatch, begun=True)
    import contextlib, io
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        WG.cmd_inspect(_args(page=run["pages"][0]["page"]))
    d = json.loads(out.getvalue())
    assert d["claims"]
