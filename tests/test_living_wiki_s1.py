"""Living-wiki S1 (#143): exporter claim joins + evidence-version freshness."""
import importlib.util
import sys
from pathlib import Path
from unittest import mock

import pytest

REPO = Path(__file__).parent.parent
_SCRIPTS = (REPO / "scripts").resolve()
for _rel in ("cmd", "lib", "eval", "harness", "wiki_lib"):
    p = _SCRIPTS / _rel
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


_REPO_SCRIPTS = str(REPO / "scripts")
for _d in (_REPO_SCRIPTS, _REPO_SCRIPTS + "/lib", _REPO_SCRIPTS + "/cmd"):
    if _d not in sys.path:
        sys.path.insert(0, _d)
import wiki_lib.generators as gen


def _fabric(tmp):
    """Temp corpus: one source (recorded sha256 of raw A), one claim citing it."""
    import hashlib
    corpus = tmp / "corpus"
    raw = corpus / "evidence" / "raw" / "proj"
    raw.mkdir(parents=True)
    (raw / "doc.md").write_text("line1\nline2\n")
    digest = hashlib.sha256((raw / "doc.md").read_bytes()).hexdigest()
    src = corpus / "evidence" / "sources"
    src.mkdir(parents=True)
    (src / "src-proj-doc-md.md").write_text(
        f"---\ntype: source\nsource_path: evidence/raw/proj/doc.md\nsha256: {digest}\n---\n\ns\n")
    claims = corpus / "evidence" / "claims"
    claims.mkdir(parents=True)
    (claims / "claim-proj-doc-md-000.md").write_text(
        "---\ntype: claim\nid: claim-proj-doc-md-000\nstatement: \"S\"\n"
        'source_refs:\n  - source: "[[src-proj-doc-md]]"\n'
        '    locator: "L1"\n    quote: "doc line"\n'
        "last_verified: 2026-09-28\n---\n\nS\n")
    return corpus, digest


from unittest import mock


class TestEvidenceTier:
    def test_current_when_hash_matches(self, tmp_path, monkeypatch):
        import fabric_config
        corpus, _ = _fabric(tmp_path)
        monkeypatch.setattr(gen.fabric_config, "CORPUS_ROOT", corpus, raising=False)
        monkeypatch.setattr(gen, "_src_cache", {})
        p = corpus / "evidence" / "claims" / "claim-proj-doc-md-000.md"
        tier, label, _ = gen._claim_evidence_tier(p)
        assert tier == 1 and label is None

    def test_drifted_when_hash_changes(self, tmp_path, monkeypatch):
        import fabric_config
        corpus, digest = _fabric(tmp_path)
        monkeypatch.setattr(gen.fabric_config, "CORPUS_ROOT", corpus, raising=False)
        monkeypatch.setattr(gen, "_src_cache", {})
        # tamper: recorded hash no longer matches raw
        src = corpus / "evidence" / "sources" / "src-proj-doc-md.md"
        src.write_text(src.read_text().replace(
            [l for l in src.read_text().splitlines() if l.startswith("sha256:")][0],
            "sha256: " + "0" * 64))
        p = corpus / "evidence" / "claims" / "claim-proj-doc-md-000.md"
        tier, label, _ = gen._claim_evidence_tier(p)
        assert tier == 2 and label == "evidence drifted"

    def test_calendar_stale_outranks_drift(self, tmp_path, monkeypatch):
        import fabric_config
        corpus, _ = _fabric(tmp_path)
        monkeypatch.setattr(gen.fabric_config, "CORPUS_ROOT", corpus, raising=False)
        monkeypatch.setattr(gen, "_src_cache", {})
        src = corpus / "evidence" / "sources" / "src-proj-doc-md.md"
        src.write_text(src.read_text().replace(
            [l for l in src.read_text().splitlines() if l.startswith("sha256:")][0],
            "sha256: " + "0" * 64))
        p = corpus / "evidence" / "claims" / "claim-proj-doc-md-000.md"
        p.write_text(p.read_text().replace(
            "last_verified: 2026-09-28",
            "review_after: 2026-01-01\nlast_verified: 2026-09-28"))
        tier, label, _ = gen._claim_evidence_tier(p)
        assert tier == 3  # overdue calendar wins

    def test_missing_source_record_is_not_drift(self, tmp_path, monkeypatch):
        import fabric_config
        corpus, _ = _fabric(tmp_path)
        monkeypatch.setattr(gen.fabric_config, "CORPUS_ROOT", corpus, raising=False)
        monkeypatch.setattr(gen, "_src_cache", {})
        (corpus / "evidence" / "sources" / "src-proj-doc-md.md").unlink()
        p = corpus / "evidence" / "claims" / "claim-proj-doc-md-000.md"
        tier, _, _ = gen._claim_evidence_tier(p)
        assert tier == 1


class TestProjectArticleJoins:
    def test_project_glob_matches_slugged_claims(self, tmp_path, monkeypatch):
        """#143: project pages must render claims — the claim→project glob
        matches claim-<project>-<upstream>-<doc>-N files."""
        corpus, _ = _fabric(tmp_path)
        monkeypatch.setattr(gen.fabric_config, "CORPUS_ROOT", corpus, raising=False)
        cfg = {"repos": {"proj": {"path": str(tmp_path / "proj-repo")}}}
        art, n = gen._generate_project_article("proj", cfg, dry_run=True, mode="mechanical")
        assert n >= 1
        assert art is not None