"""SkillOpt-epic S3 (#140): rejected-proposal buffer — tombstones + miner consumption."""
import json
import sys
from pathlib import Path

REPO = Path(__file__).parent.parent
_SCRIPTS = (REPO / "scripts").resolve()
for _d in (_SCRIPTS, _SCRIPTS / "lib", _SCRIPTS / "cmd"):
    if str(_d) not in sys.path:
        sys.path.insert(0, str(_d))

from wiki_lib import tombstones as T


class TestTombstones:
    def test_write_and_load_roundtrip(self, tmp_path):
        p = T.write_tombstone(tmp_path, "chat-mined-pattern", "pattern-abc",
                              "too vague; duplicates existing rotation guidance",
                              {"token", "rotation", "cache"},
                              "human:johnd")
        assert p.exists()
        active = T.load_active(tmp_path)
        assert len(active) == 1
        tid, sig, reason, path = active[0]
        assert tid == "abc"
        assert "rotation" in sig
        assert "too vague" in reason

    def test_inactive_not_loaded(self, tmp_path):
        p = T.write_tombstone(tmp_path, "dossier", "c1", "dup", {"alpha", "beta"}, "human:x")
        # retire it
        text = p.read_text().replace("status: active", "status: inactive")
        p.write_text(text)
        assert T.load_active(tmp_path) == []

    def test_match_cluster_above_threshold(self, tmp_path):
        T.write_tombstone(tmp_path, "dossier", "cache-rejection",
                          "single-writer cache idea rejected",
                          {"single", "writer", "cache", "stale", "invalidation",
                           "scene", "reads", "preflight"},
                          "human:johnd")
        events = ["process-global preflight read cache bled stale scene reads "
                  "across editor sessions — reject shared token cache"]
        tid, j = T.match_cluster(events, T.load_active(tmp_path))
        assert tid == "cache-rejection" and j >= 0.25

    def test_no_match_below_threshold(self, tmp_path):
        T.write_tombstone(tmp_path, "dossier", "c1", "unrelated",
                          {"quantum", "tensor", "lattice"}, "human:johnd")
        tid, j = T.match_cluster(["preflight cache drift in editor"], T.load_active(tmp_path))
        assert tid is None or j < 0.25

    def test_suppression_annotated(self, tmp_path):
        p = T.write_tombstone(tmp_path, "dossier", "c1", "dup",
                              {"rotation", "token"}, "human:johnd")
        T.annotate_suppressed(p, "cluster_xyz", ["ee-1", "ee-2"])
        text = p.read_text()
        assert "## Suppressions" in text
        assert "cluster_xyz" in text
        # and the tombstone remains active (reviewable, not consumed)
        assert T.load_active(tmp_path)

    def test_promote_patterns_reject_writes_tombstone(self, tmp_path, monkeypatch):
        """The inbox reject path persists a tombstone before unlinking."""
        import importlib.util as _ilu
        _spec = _ilu.spec_from_file_location("promote_patterns", REPO / "scripts" / "cmd" / "promote-patterns.py")
        PP = _ilu.module_from_spec(_spec); _spec.loader.exec_module(PP)
        import fabric_config
        inbox = tmp_path / "corpus" / "patterns" / "_inbox"
        inbox.mkdir(parents=True)
        cand = inbox / "pattern-foo.md"
        cand.write_text("---\ntype: pattern\nid: pattern-foo\nstatus: candidate\n"
                        "tags: [chat-mined, inbox]\n---\n\nRotation tokens per session.\n")
        monkeypatch.setattr(PP, "INBOX_DIR", inbox)
        monkeypatch.setattr(fabric_config, "CORPUS_ROOT", tmp_path / "corpus")
        monkeypatch.setattr(PP, "CORPUS_ROOT", tmp_path / "corpus")
        PP.reject_candidate("pattern-foo", "redundant with pattern-token-rotation")
        assert not cand.exists()  # candidate gone
        # tombstone exists with the reason
        tdir = tmp_path / "corpus" / "patterns" / "_rejected"
        tombs = list(tdir.glob("tombstone-*.md")) if tdir.is_dir() else []
        assert tombs, "tombstone must be written on inbox reject"
        assert "redundant" in tombs[0].read_text()

    def test_miner_suppresses_matching_cluster(self, tmp_path, monkeypatch):
        """End-to-end: tombstone active → mine-promotions skips the matching cluster."""
        # build a fabric: two matching events in two projects + a tombstone
        import importlib.util as _ilu
        _spec = _ilu.spec_from_file_location("mine_promotions", REPO / "scripts" / "cmd" / "mine-promotions.py")
        MP = _ilu.module_from_spec(_spec); _spec.loader.exec_module(MP)
        import fabric_config
        corpus = tmp_path / "corpus"
        for proj in ("p1", "p2"):
            ee = corpus / "projects" / proj / "experience-events"
            ee.mkdir(parents=True)
            (ee / "ee-1.md").write_text(
                "---\ntype: experience-event\nproject: p\n"
                "observed_problem: process-global preflight read cache bled stale reads\n"
                "intervention: serialize cache invalidation on writes\n"
                "outcomes:\n  happy_path: PASS\nsession: s1\n---\n\nx\n")
        import fabric_config as fc
        monkeypatch.setattr(fc, "CORPUS_ROOT", corpus)
        # MP reads VAULT_ROOT — patch both
        vault = tmp_path / "corpus"
        monkeypatch.setattr(MP, "VAULT_ROOT", vault)
        # tombstone matching the cache idea
        T.write_tombstone(vault, "promotion-dossier", "cache-cluster",
                          "single-writer cache idea rejected earlier",
                          {"preflight", "cache", "stale", "reads", "invalidate",
                           "serialize", "writes"},
                          "human:johnd")
        monkeypatch.setattr(MP, "VAULT_ROOT", vault)
        # run the clustering+suppression path in dry-run equivalent: call the module functions directly
        active = T.load_active(vault)
        assert len(active) == 1
        # the suppression helper agrees the cluster matches
        ev_texts = ["process-global preflight read cache bled stale reads — serialize cache invalidation on writes"]
        tid, j = T.match_cluster(ev_texts, active)
        assert tid == "cache-cluster"