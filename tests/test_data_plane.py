"""#160 data-plane hygiene: source staleness tiers (S1), expired lifecycle
(S2), promotion-queue bootstrap (S3), questions loop with domain routing (S4).

Run: python3 -m pytest tests/test_data_plane.py -v
"""
import sys
import importlib.util
from datetime import date, timedelta
from pathlib import Path

import pytest

_SCRIPTS = (Path(__file__).resolve().parent.parent / "scripts").resolve()
for _rel in ("cmd", "lib", ""):
    _d = _SCRIPTS / _rel if _rel else _SCRIPTS
    if str(_d) not in sys.path:
        sys.path.insert(0, str(_d))


def _load(name, rel="cmd"):
    # rel may carry the module file name (hyphenated scripts): 'cmd/ingest.py'
    file = rel if "/" in rel else f"{rel}/{name}.py"
    spec = importlib.util.spec_from_file_location(name, _SCRIPTS / file)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


class TestSourceStalenessTiers:
    def setup_method(self):
        self.ing = _load("ing_dp", "cmd/ingest.py")

    def test_kind_by_path(self):
        assert self.ing.source_kind(Path("/x/evidence/raw/p/git/pr-5.md")) == "pr-record"
        assert self.ing.source_kind(Path("/x/evidence/raw/p/git/issue-2.md")) == "pr-record"
        assert self.ing.source_kind(Path("/x/evidence/raw/p/git/commit-abc.md")) == "commit"
        assert self.ing.source_kind(Path("/x/evidence/raw/p/chats/d-chat-x.md")) == "chat-session"
        assert self.ing.source_kind(Path("/x/evidence/raw/p/docs-readme.md")) == "default"

    def test_tier_stamps(self, tmp_path, monkeypatch):
        monkeypatch.setattr(self.ing, "VAULT_ROOT", tmp_path)
        for path, tier in ((tmp_path / "raw" / "p" / "git" / "pr-1.md", 30),
                           (tmp_path / "raw" / "p" / "chats" / "x.md", 45),
                           (tmp_path / "raw" / "p" / "readme.md", 180)):
            line = self.ing.source_staleness_stamps(path)
            days = (date.fromisoformat(line.split("review_after: ")[1]) - date.today()).days
            assert abs(days - tier) <= 1, (path, line, tier)


class TestSourceExpiryLifecycle:
    def _review(self, tmp_path, monkeypatch):
        import fabric_config
        monkeypatch.setattr(fabric_config, "CORPUS_ROOT", tmp_path, raising=False)
        rv = _load("rv_dp", "cmd/review.py")
        monkeypatch.setattr(rv, "CORPUS_ROOT", tmp_path)
        return rv, tmp_path

    def _record(self, tmp_path, raw_rel, sha="a" * 64, status="ingested"):
        raw = tmp_path / raw_rel
        raw.parent.mkdir(parents=True, exist_ok=True)
        raw.write_text("raw content")
        rec = tmp_path / "evidence" / "sources" / "src-p-x-md.md"
        rec.parent.mkdir(parents=True, exist_ok=True)
        rec.write_text(f"---\ntype: source\nsource_path: {raw_rel}\nsha256: {sha}\n"
                       f"review_after: 2999-01-01\nstatus: {status}\n---\n\n# src\n")
        return rec, raw

    def test_fresh_rolls_tier(self, tmp_path, monkeypatch):
        import wf_common
        rv, tmp = self._review(tmp_path, monkeypatch)
        import wf_common as _wf
        rec, raw = self._record(tmp, "evidence/raw/p/x.md")
        rec.write_text(rec.read_text().replace("a" * 64, _wf.sha256_file(raw)))
        outcome, _ = rv.expire_or_reverify_source(rec)
        assert outcome == "refreshed"
        text = rec.read_text()
        assert "stale_after:" not in text
        assert f"review_after: {(date.today() + timedelta(days=180)).isoformat()}" in text

    def test_gone_expires(self, tmp_path, monkeypatch):
        import wf_common
        rv, tmp = self._review(tmp_path, monkeypatch)
        rec, raw = self._record(tmp, "evidence/raw/p/x.md")
        orig_sha = wf_common.sha256_file(raw)
        rec.read_text()
        raw.unlink()  # upstream vanished
        # rewrite recorded sha to the real one (fresh before deletion)
        rec.write_text(rec.read_text().replace("a" * 64, orig_sha))
        outcome, _ = rv.expire_or_reverify_source(rec)
        assert outcome == "expired"
        assert "status: expired" in rec.read_text()
        assert "stale_after:" in rec.read_text()

    def test_drifted_stamps_stale(self, tmp_path, monkeypatch):
        import wf_common
        rv, tmp = self._review(tmp_path, monkeypatch)
        rec, raw = self._record(tmp, "evidence/raw/p/x.md", sha="b" * 64)
        outcome, _ = rv.expire_or_reverify_source(rec)
        assert outcome == "drifted"
        assert f"stale_after: {date.today().isoformat()}" in rec.read_text()
        assert "status: ingested" in rec.read_text()  # not expired — drift is fixable

    def test_dry_run_writes_nothing(self, tmp_path, monkeypatch):
        import wf_common
        rv, tmp = self._review(tmp_path, monkeypatch)
        rec, raw = self._record(tmp, "evidence/raw/p/x.md", sha="z" * 64)
        outcome, _ = rv.expire_or_reverify_source(rec, dry_run=True)
        assert outcome == "drifted"
        assert "stale_after:" not in rec.read_text()

    def test_verify_sources_cli(self, tmp_path, monkeypatch):
        import wf_common
        rv, tmp = self._review(tmp_path, monkeypatch)
        rec, raw = self._record(tmp, "evidence/raw/p/x.md", sha="b" * 64)
        monkeypatch.setattr(sys, "argv", ["review.py", "--verify-sources"])
        buf = io.StringIO() if (io := __import__("io")) else None
        import contextlib
        with contextlib.redirect_stdout(buf):
            rc = rv.main()
        assert rc == 0
        assert "drifted" in buf.getvalue()


class TestPromotionQueueBootstrap:
    def test_scaffold_idempotent(self, tmp_path, monkeypatch):
        sy = _load("sy_dp", "cmd/sync.py")
        import fabric_config
        monkeypatch.setattr(sy, "VAULT_ROOT", tmp_path, raising=False)
        (tmp_path / "registry").mkdir(parents=True)
        sy.scaffold_promotion_queue()
        q = tmp_path / "registry" / "promotion-queue.md"
        first = q.read_text()
        sy.scaffold_promotion_queue()
        assert q.read_text() == first
        assert "type: registry" in first


class TestQuestionsLoop:
    def _fabric(self, tmp_path):
        (tmp_path / "domains" / "godot" / "concepts").mkdir(parents=True)
        (tmp_path / "domains" / "ontology.md").write_text("## Domains\n- **godot** — x\n")
        (tmp_path / "registry" / "question-proposals").mkdir(parents=True)
        concept = tmp_path / "domains" / "godot" / "concepts" / "concept-mesh.md"
        concept.write_text("---\ntype: concept\nid: concept-mesh\ndomain: [godot]\n"
                           "claims:\n  - \"[[claim-a]]\"\n---\n\n## Open questions\n\n"
                           "- Does the mesher hold the mesh across chunk boundaries?\n")
        return tmp_path, concept

    def test_harvest_inherits_domain_binding(self, tmp_path):
        hq = _load("hq_dp", "cmd/harvest-questions.py")
        tmp, concept = self._fabric(tmp_path)
        hq.CORPUS_ROOT = tmp
        hq.PROPOSALS_DIR = tmp / "registry" / "question-proposals"
        n, _ = hq.harvest_concept(concept)
        props = list(hq.PROPOSALS_DIR.glob("question-*.md"))
        assert n == 1 and props
        import yaml
        assert yaml.safe_load(props[0].read_text().split("---")[1]).get("domain") == ["godot"]

    def test_heading_case_insensitive(self, tmp_path):
        hq = _load("hq_dp2", "cmd/harvest-questions.py")
        tmp, concept = self._fabric(tmp_path)
        concept.write_text(concept.read_text().replace("## Open questions", "## OPEN QUESTIONS"))
        hq.CORPUS_ROOT = tmp
        hq.PROPOSALS_DIR = tmp / "registry" / "question-proposals"
        n, _ = hq.harvest_concept(concept)
        assert n == 1

    def test_promote_routes_to_domain_home(self, tmp_path):
        hq = _load("hq_dp3", "cmd/harvest-questions.py")
        pq = _load("pq_dp3", "cmd/promote-questions.py")
        tmp, concept = self._fabric(tmp_path)
        hq.CORPUS_ROOT = tmp
        hq.PROPOSALS_DIR = tmp / "registry" / "question-proposals"
        pq.CORPUS_ROOT = tmp
        pq.PROPOSALS_DIR = hq.PROPOSALS_DIR
        pq.QUESTIONS_DIR = tmp / "questions"
        hq.harvest_concept(concept)
        prop = next(hq.PROPOSALS_DIR.glob("question-*.md"))
        assert pq.apply_question(prop)
        assert (tmp / "domains" / "godot" / "questions" / prop.name).exists()
        assert "status: open" in (tmp / "domains" / "godot" / "questions" / prop.name).read_text()
