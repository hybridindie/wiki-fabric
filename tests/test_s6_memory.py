"""#177 S6 — the memory bridge: remember verb (friction-free intake),
idempotence, expiry sweep, mining reads standing notes, schema contract.
"""

import os
import sys
from datetime import date, timedelta
from pathlib import Path
from unittest import mock

import pytest

_REPO = Path(__file__).resolve().parent.parent
for _p in (str(_REPO / "scripts" / "cmd"), str(_REPO / "scripts" / "lib")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

os.environ.setdefault("WIKI_FABRIC_DIR", "/tmp/definitely-not-a-fabric-s6")


def _mk_fabric(tmp_path):
    corpus = tmp_path / "corpus"
    (corpus / "evidence" / "memory").mkdir(parents=True)
    (corpus / "projects" / "proj").mkdir(parents=True)
    (tmp_path / "fabric.yaml").write_text("repos:\n  proj:\n    path: ../proj\n")
    os.environ["WIKI_FABRIC_DIR"] = str(tmp_path)
    import fabric_config
    import importlib
    importlib.reload(fabric_config)
    return corpus


def _rem(tmp_path):
    import importlib.util as ilu
    spec = ilu.spec_from_file_location(f"rem_{id(tmp_path) % 99999}",
                                       _REPO / "scripts" / "cmd" / "remember.py")
    mod = ilu.module_from_spec(spec)
    sys.modules[f"rem_{id(tmp_path) % 99999}"] = mod
    spec.loader.exec_module(mod)
    return mod


def _mine(tmp_path):
    import importlib.util as ilu
    spec = ilu.spec_from_file_location(f"mine_s6_{id(tmp_path) % 99999}",
                                       _REPO / "scripts" / "cmd" / "mine-promotions.py")
    mod = ilu.module_from_spec(spec)
    sys.modules[f"mine_s6_{id(tmp_path) % 99999}"] = mod
    spec.loader.exec_module(mod)
    return mod


class TestRemember:
    def test_write_note(self, tmp_path):
        corpus = _mk_fabric(tmp_path)
        rem = _rem(tmp_path)
        dest, created = rem.write_note("proj", "always run gdlint before commit",
                                       kind="feedback")
        assert created and "mn-proj-feedback" in dest.name
        s = dest.read_text()
        assert "type: memory-note" in s
        assert "kind: feedback" in s
        assert "expires:" in s  # 45d for feedback
        assert (date.today() + timedelta(days=45)).isoformat() in s

    def test_idempotent(self, tmp_path):
        corpus = _mk_fabric(tmp_path)
        rem = _rem(tmp_path)
        d1, c1 = rem.write_note("proj", "the same note twice")
        d2, c2 = rem.write_note("proj", "the same note twice")
        assert c1 and not c2 and d1 == d2

    def test_unknown_kind_defaults_project(self, tmp_path):
        corpus = _mk_fabric(tmp_path)
        rem = _rem(tmp_path)
        dest, _ = rem.write_note("proj", "note with odd kind x", kind="odd")
        assert "kind: project" in dest.read_text()

    def test_dry_run_writes_nothing(self, tmp_path):
        corpus = _mk_fabric(tmp_path)
        rem = _rem(tmp_path)
        dest, _ = rem.write_note("proj", "a dry run note", dry_run=True)
        assert not dest.exists()
        assert list((corpus / "evidence" / "memory").glob("*.md")) == []


class TestExpiry:
    def _seed(self, corpus, expires, stem="mn-proj-project-x-abc123"):
        p = corpus / "evidence" / "memory" / f"{stem}.md"
        p.write_text(f"""---
type: memory-note
id: {stem}
title: "x"
project: proj
kind: project
note: "x note"
lineage: "proj"
expires: {expires}
created: 2026-10-01
---

# x
""")
        return p

    def test_expired_notes_deleted(self, tmp_path):
        corpus = _mk_fabric(tmp_path)
        old = self._seed(corpus, (date.today() - timedelta(days=1)).isoformat())
        fresh = self._seed(corpus, (date.today() + timedelta(days=5)).isoformat(),
                           "mn-proj-project-fresh-def456")
        rem = _rem(tmp_path)
        expired, kept = rem.expire_notes()
        assert (expired, kept) == (1, 1)
        assert not old.exists() and fresh.exists()

    def test_missing_expires_is_already_stale(self, tmp_path):
        corpus = _mk_fabric(tmp_path)
        p = corpus / "evidence" / "memory" / "mn-proj-project-nostamp-aaa.md"
        p.write_text("---\ntype: memory-note\nproject: proj\n---\n\nx\n")
        rem = _rem(tmp_path)
        expired, _ = rem.expire_notes()
        assert expired == 1

    def test_project_scoped_expiry(self, tmp_path):
        corpus = _mk_fabric(tmp_path)
        self._seed(corpus, "2026-01-01")  # proj
        other = corpus / "evidence" / "memory" / "mn-other-project-z-zz.md"
        other.write_text("---\ntype: memory-note\nproject: other\nexpires: 2026-01-01\n---\n\nz\n")
        rem = _rem(tmp_path)
        expired, _ = rem.expire_notes(project="proj")
        assert expired == 1 and other.exists()


class TestMiningInput:
    def test_mining_reads_standing_notes(self, tmp_path):
        corpus = _mk_fabric(tmp_path)
        rem = _rem(tmp_path)
        rem.write_note("proj", "shared insight across the loop")
        # give it a partner event in another project so a cluster can form
        mine = _mine(tmp_path)
        notes = mine.extract_memory_notes()
        assert len(notes) == 1
        e = notes[0]
        assert e["_memory_note"] is True
        assert e["observed_problem"] == "shared insight across the loop"

    def test_expired_notes_not_mining_input(self, tmp_path):
        corpus = _mk_fabric(tmp_path)
        self._seed_expired(corpus)
        mine = _mine(tmp_path)
        assert mine.extract_memory_notes() == []

    def _seed_expired(self, corpus):
        (corpus / "evidence" / "memory" / "mn-proj-project-dead-aa.md").write_text(
            "---\ntype: memory-note\nproject: proj\nnote: dead\nexpires: 2026-01-01\n---\n\nx\n")

    def test_project_prefix_canonical(self, tmp_path):
        corpus = _mk_fabric(tmp_path)
        rem = _rem(tmp_path)
        dest, _ = rem.write_note("my_proj", "underscore folds")
        assert "mn-my-proj" in dest.name


class TestLintContract:
    def test_memory_note_is_valid_type(self):
        from lint import VALID_TYPES
        assert "memory-note" in VALID_TYPES

    def test_layout_segment_declared(self):
        import layout
        assert layout.memory().name == "memory"

    def test_policy_plane(self):
        # import through the PACKAGE (sync_lib.policy) — the sync_lib dir
        # on sys.path registered a SECOND 'policy' module identity (the
        # #178-suite flake: same code, two module objects, the from-import
        # bindings then disagree)
        from sync_lib import policy as policy
        # memory plane is EVIDENCE (auto-mergeable, unlike atoms)
        assert any("evidence/memory" in x for x in policy.EVIDENCE_PATHS)