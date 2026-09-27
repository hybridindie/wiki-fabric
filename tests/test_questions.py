"""Unit tests for harvest-questions.py / promote-questions.py (#88).

Run: python3 -m pytest tests/test_questions.py -v
"""

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


harvest = _load("harvest_questions", Path(__file__).parent.parent / "scripts/cmd/harvest-questions.py")
promote = _load("promote_questions", Path(__file__).parent.parent / "scripts/cmd/promote-questions.py")


def _make_corpus(tmp):
    """Corpus shape: concepts/ with an Open Questions section; claims dir."""
    corpus = tmp / "corpus"
    (corpus / "concepts").mkdir(parents=True)
    (corpus / "evidence" / "claims").mkdir(parents=True)
    (corpus / "registry" / "question-proposals").mkdir(parents=True)
    harvest.CONCEPTS_DIR = corpus / "concepts"
    harvest.PROPOSALS_DIR = corpus / "registry" / "question-proposals"
    harvest.QUESTIONS_DIR = corpus / "questions"
    harvest.CORPUS_ROOT = corpus
    promote.PROPOSALS_DIR = harvest.PROPOSALS_DIR
    promote.QUESTIONS_DIR = harvest.QUESTIONS_DIR
    return corpus


CONCEPT = """---
type: concept
title: Test Concept
id: concept-test
domain: [test]
claims:
  - "[[claim-test-0]]"
created: 2026-09-26
---

# Concept: Test Concept

## Definition

Something.

## Supporting Claims (1)

| Claim | Statement | Status | Confidence |
|-------|-----------|--------|------------|
| [[claim-test-0]] | A claim | supported | medium |

## Applicability

- when testing

## Open Questions

- Does the gate apply to derived pages?
- {ignored}

## Status Distribution

- supported: 1
"""

CLAIM_MEDIUM = """---
type: claim
id: claim-test-0
statement: "A claim"
status: supported
confidence: medium
source_refs:
  - source: "[[src-x]]"
    locator: L1
    quote: q
relations: []
---

# claim-test-0

A claim
"""


class TestHarvest:
    def test_harvest_proposes_questions(self, tmp_path):
        corpus = _make_corpus(tmp_path)
        (corpus / "concepts" / "concept-test.md").write_text(CONCEPT)
        (corpus / "evidence" / "claims" / "claim-test-0.md").write_text(CLAIM_MEDIUM)
        proposed, skipped = harvest.harvest_concept(corpus / "concepts" / "concept-test.md")
        assert proposed == 1, "placeholder {…} excluded, real question proposed"
        assert skipped == 0
        pages = list(harvest.PROPOSALS_DIR.glob("question-*.md"))
        assert len(pages) == 1
        fm, body = promote.parse_frontmatter(pages[0])
        assert fm["type"] == "question"
        assert fm["status"] == "proposed"
        assert fm["priority"] == "P1"  # medium-confidence claim → P1
        assert "concept-test" in str(fm["related"])

    def test_harvest_is_idempotent(self, tmp_path):
        corpus = _make_corpus(tmp_path)
        (corpus / "concepts" / "concept-test.md").write_text(CONCEPT)
        (corpus / "evidence" / "claims" / "claim-test-0.md").write_text(CLAIM_MEDIUM)
        p1, _ = harvest.harvest_concept(corpus / "concepts" / "concept-test.md")
        p2, s2 = harvest.harvest_concept(corpus / "concepts" / "concept-test.md")
        assert p1 == 1 and p2 == 0 and s2 == 1, "re-harvest skips known questions"

    def test_high_confidence_claims_priority_p2(self, tmp_path):
        corpus = _make_corpus(tmp_path)
        (corpus / "concepts" / "concept-test.md").write_text(CONCEPT)
        claim = CLAIM_MEDIUM.replace("confidence: medium", "confidence: high")
        (corpus / "evidence" / "claims" / "claim-test-0.md").write_text(claim_high) if False else None
        (corpus / "evidence" / "claims" / "claim-test-0.md").write_text(claim_high := claim)
        proposed, _ = harvest.harvest_concept(corpus / "concepts" / "concept-test.md")
        pages = list(harvest.PROPOSALS_DIR.glob("question-*.md"))
        assert proposed == 1
        import re
        assert "priority: P2" in pages[0].read_text()

    def test_concept_without_open_questions_noop(self, tmp_path):
        corpus = _make_corpus(tmp_path)
        (corpus / "concepts" / "concept-test.md").write_text(
            CONCEPT.replace("- Does the gate apply to derived pages?\n- {ignored}", "_None identified_"))
        proposed, skipped = harvest.harvest_concept(corpus / "concepts" / "concept-test.md")
        assert (proposed, skipped) == (0, 0)


class TestPromoteQuestions:
    def _staged(self, corpus):
        (corpus / "concepts" / "concept-test.md").write_text(CONCEPT)
        (corpus / "evidence" / "claims" / "claim-test-0.md").write_text(CLAIM_MEDIUM)
        harvest.harvest_concept(corpus / "concepts" / "concept-test.md")
        return list(harvest.PROPOSALS_DIR.glob("question-*.md"))[0]

    def test_list_pending(self, tmp_path):
        corpus = _make_corpus(tmp_path)
        self._staged(corpus)
        pending = promote.list_pending()
        assert len(pending) == 1
        assert pending[0][1]["status"] == "proposed"

    def test_apply_moves_to_canonical_and_flips_status(self, tmp_path):
        corpus = _make_corpus(tmp_path)
        staged = self._staged(corpus)
        assert promote.apply_question(staged)
        canonical = corpus / "questions" / staged.name
        assert canonical.exists()
        assert not staged.exists()  # staging page consumed
        text = canonical.read_text()
        assert "status: open" in text
        assert promote.list_pending() == []
        assert len(promote.list_open_questions()) == 1

    def test_reject_requires_reason(self, tmp_path):
        corpus = _make_corpus(tmp_path)
        staged = self._staged(corpus)
        assert not promote.reject_question(staged.stem, "")
        assert staged.exists()  # not deleted without a reason
        assert promote.reject_question(staged.stem, "out of scope")
        assert not staged.exists()

    def test_dry_run_writes_nothing(self, tmp_path):
        corpus = _make_corpus(tmp_path)
        staged = self._staged(corpus)
        assert promote.apply_question(staged, dry_run=True)
        assert staged.exists()  # untouched
        assert not (corpus / "questions" / staged.name).exists()